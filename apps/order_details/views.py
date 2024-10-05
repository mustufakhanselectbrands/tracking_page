from django.conf import settings
from rest_framework.decorators import api_view
from django.http import JsonResponse
from rest_framework import status
import requests
from rest_framework.views import APIView, View
from django.shortcuts import render, redirect
from cryptography.fernet import Fernet
from ftm_selectbrands.settings import FERNET_KEY
from apps.order_details.image_id import get_image_src_by_sku 
import pandas as pd


# Load the Excel file once at the start
df_images = pd.read_excel("Image_Ids.xlsx")

# Function to get authentication token
def get_auth_token():
    url = settings.BASE_URL + "getApiToken"
    email = settings.USER_EMAIL
    password = settings.PASSWORD
    payload = {
        "email": email,
        "password": password
    }
    response = requests.post(url, data=payload)
    response.raise_for_status()
    data = response.json()
    api_token = data['data']["api_token"]
    jwt = data['data']["jwt_token"]
    if api_token and jwt:
        return api_token, jwt
    return None, None

def get_image_url(sku):
    try:
        # Print the sku being searched
        print(f"Searching for sku: {sku}")

        # Check if sku exists in the DataFrame
        if sku not in df_images['sku'].values:
            print(f"sku {sku} not found in sku column")
            return None

        # Match the sku with the 'sku' to get the corresponding image URL
        image_url = df_images[df_images['sku'] == sku]['image url'].values[0]
        print(f"Found image URL: {image_url} for sku: {sku}")
        return image_url
    except IndexError:
        print(f"No image URL found for sku: {sku}")
        return None
    except KeyError as e:
        print(f"KeyError: {e}")
        return None

# View for rendering order fetch page
class Orders(View):
    def get(self, request):
        context = {
            'error': request.GET.get('error', False)
        }
        return render(request, 'fetch_order.html', context)

# APIView for handling order details retrieval
class OrderDetails(APIView):
    def post(self, request):
        data = request.data
        ref_no = data.get('ref_no', None)
        order_type = data.get('order_type', None)
        
        try:
            if not ref_no:
                return JsonResponse({"message": "Missing reference number", "status": status.HTTP_400_BAD_REQUEST})
            
            filter = None
            if order_type == 'ref_id':
                filter = f'reference_code={ref_no if ref_no.startswith("K-") else "K-" + ref_no}'
            elif order_type == 'order_id':
                filter = f'order_id={ref_no}'
            elif order_type == 'invoice_id':
                filter = f'invoice_id={ref_no}'
            
            if not filter:
                return JsonResponse({"message": "Invalid order type", "status": status.HTTP_400_BAD_REQUEST})

            token, jwt = get_auth_token()
            if not token or not jwt:
                return JsonResponse({"message": "Authentication failed", "status": status.HTTP_401_UNAUTHORIZED})

            url = settings.BASE_URL + f"orders/V2/getOrderDetails?" + filter
            headers = {
                "x-api-key": token,
                "Authorization": f"Bearer {jwt}"
            }

            response = requests.get(url, headers=headers)
            response.raise_for_status()
            order_data = response.json()

            if not order_data.get('data'):
                return JsonResponse({"message": "Order details not found", "status": status.HTTP_404_NOT_FOUND})

            fernet = Fernet(FERNET_KEY)
            enc_ref_no = fernet.encrypt(order_data['data'][0]['reference_code'].encode()).decode()
            res_data = {
                'ref_no': enc_ref_no,
                'headers': headers
            }

            # Extract order items
            order_items = pd.json_normalize(order_data['data'][0]['order_items'])
            extracted_items_list = order_items[['sku', 'productName']].to_dict(orient='records')

            return JsonResponse({
                "data": {
                    "valid": True,
                    "res_data": res_data,
                    "order_items": extracted_items_list
                },
                "message": "Order details validated",
                "status": status.HTTP_200_OK
            })

        except requests.exceptions.RequestException as err:
            return JsonResponse({"message": f"Request failed: {err}", "status": status.HTTP_500_INTERNAL_SERVER_ERROR})

        except Exception as err:
            return JsonResponse({"message": f"Something went wrong: {err}", "status": status.HTTP_500_INTERNAL_SERVER_ERROR})

# View for rendering order tracking details page
class OrderTrackingDetails(View):
    def get(self, request):
        ref_no = request.GET.get("ref_no")
        if not ref_no:
            return redirect("/order_details?error=True")

        token, jwt = get_auth_token()
        if not token or not jwt:
            return redirect("/order_details?error=True")
        
        try:
            # Decrypt the reference number using Fernet encryption
            fernet = Fernet(FERNET_KEY)
            dec_ref_no = fernet.decrypt(ref_no.encode()).decode()
            
            # Construct the API URL and headers for fetching order details
            url = settings.BASE_URL + f"orders/V2/getOrderDetails?reference_code={dec_ref_no}"
            headers = {
                "x-api-key": token,
                "Authorization": f"Bearer {jwt}"
            }

            # Make a GET request to fetch order details
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            tracking_data = response.json()
            
            context = []

            # Define desired statuses mapping
            desired_statuses = {
                "Pickup Awaited": 0,
                "Picked Up": 1,
                "In Transit": 2,
                "Pickup Scheduled": 3,
                "Reached At Destination": 4,
                "Out For Delivery": 5,
                "Delivered": 6,
                "Cancelled": 8
            }

            # Process each order's tracking details
            for order in tracking_data.get("data", []):
                tracking_details = {
                    "cancelled": False,
                    "currentShippingStatus": order.get("currentShippingStatus", "--"),
                    "courier": order.get("courier", "--"),
                    "order_date": order.get("order_date", "--"),
                    "reference_code": order.get("reference_code", "--"),
                    "customer_name": order.get("customer_name", "--"),
                    "customer_mobile_num": order.get("customer_mobile_num", "--"),
                    "invoiceAmount": order.get("invoiceAmount", "--"),
                    "suborder_id": order.get('suborder_id'),
                    "suborder_details": [],  # Initialize an empty list for shipping history
                    "latest_details": {},
                    "latest_status": None,
                    "sku": "--",
                    "product_name": "--",
                    "image_src": None  # Initialize image_src
                }
                
                # Extract shipping history for the current order
                shipping = order.get('shipping_history', [])
                if shipping:
                    # Filter and include relevant fields (status, time, location)
                    filtered_shipping = [{
                        "status": item["status"],
                        "time": item["time"],  # Ensure time field is included
                        "location": item["location"]
                    } for item in shipping if item["status"] in desired_statuses]
                    tracking_details["suborder_details"] = filtered_shipping
                    tracking_details["latest_details"] = shipping[0]
                    tracking_details["latest_status"] = desired_statuses.get(shipping[-1]["status"], 7)
                
                # Extract order items data
                order_items = order.get('order_items', [])
                if order_items:
                    # Choose the first item (assuming there could be multiple, you can adjust as needed)
                    first_item = order_items[0]
                    tracking_details["sku"] = first_item.get("sku", "--")
                    tracking_details["product_name"] = first_item.get("productName", "--")
                    tracking_details["suborder_id"] = first_item.get("suborder_id","--")
                    tracking_details["image_src"] = get_image_url(tracking_details["sku"])

                elif not shipping and order.get('orderStatus') == 'Cancelled':
                    tracking_details["cancelled"] = True
                    tracking_details["latest_status"] = 8

                context.append(tracking_details)

        except requests.exceptions.RequestException as err:
            return redirect("/order_details?error=True")

        except Exception as err:
            return redirect("/order_details?error=True")
        
        return render(request, 'order_tracking_details.html', {"context": context})
