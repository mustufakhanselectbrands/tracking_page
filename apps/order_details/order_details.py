import requests

BASE_URL_EASYECOM = "https://api.easyecom.io"
AUTH_EMAIL_EASYECOM = "dhruv.pahuja@selectbrands.in"
AUTH_PASS_EASYECOM = "Analyst@123#"

def authenticate_easyecom():
    url = f"{BASE_URL_EASYECOM}/getApiToken"
    payload = {
        "email": AUTH_EMAIL_EASYECOM,
        "password": AUTH_PASS_EASYECOM,
        "location_key": "en11797218225"
    }

    response = requests.post(url, data=payload)
    data = response.json()["data"]
    return data["api_token"], data["jwt_token"]

def get_tracking_details(api_token, jwt_token, order_id):
    url = f"{BASE_URL_EASYECOM}/orders/V2/getAllOrders?reference_code={order_id}"

    headers = {
        "x-api-key": api_token,
        "Authorization": f"Bearer {jwt_token}"
    }

    response = requests.get(url, headers=headers)
    return response.json()

def extract_suborders_and_titles(orders_data):
    suborders_with_titles = []
    
    if "data" not in orders_data or "orders" not in orders_data["data"]:
        print("No data or orders found in the API response")
        return suborders_with_titles
    
    orders = orders_data["data"]["orders"]
    
    for order in orders:
        order_id = order.get("reference_code")
        if not order_id:
            print("Order ID not found in order data")
            continue
        
        if "suborders" in order:
            for suborder in order["suborders"]:
                suborder_id = suborder.get("suborder_id")
                title = suborder.get("productName", "")
                suborders_with_titles.append({"order_id": order_id, "suborder_id": suborder_id, "title": title})
        else:
            print(f"Order {order_id} does not have 'suborders'")
    
    return suborders_with_titles

def main(order_id):
    api_token, jwt_token = authenticate_easyecom()
    orders_data = get_tracking_details(api_token, jwt_token, order_id)
    
    suborders_with_titles = extract_suborders_and_titles(orders_data)

    print(suborders_with_titles)

    return suborders_with_titles


# main("K-145998")

# suborder_ids = []
# for sku_data 
# print([ single_sku["title"] for single_sku in sku_data if single_sku["suborder_id"] == suborder_id ][0])