import requests

# Function to get image src by SKU
def get_image_src_by_sku(sku):

    # Define your credentials and parameters
    store_name = "kyari-co"
    api_version = "2023-07"
    api_key = "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"

    shop_url = f"https://{store_name}.myshopify.com/admin/api/{api_version}"
    products_url = f"{shop_url}/products.json"
    
    # Initialize since_id for pagination
    since_id = 0
    
    while True:
        params = {"limit": 250, "since_id": since_id}
        response = requests.get(products_url, headers={"X-Shopify-Access-Token": api_key}, params=params, verify=False)
        
        if response.status_code == 200:
            products_data = response.json()["products"]
            if not products_data:
                break
            
            for product in products_data:
                for variant in product["variants"]:
                    if variant["sku"] == sku:
                        image_id = variant["image_id"]
                        for image in product["images"]:
                            if image["id"] == image_id:
                                return image["src"]
            
            # Update since_id for next pagination
            since_id = max(product["id"] for product in products_data)
        else:
            print("Failed to fetch products:", response.status_code, response.text)
            break
    
    return "SKU not found"

# Example usage
# manual_sku = input("Enter SKU: ")
# image_src = get_image_src_by_sku(manual_sku)
# print(f"Image URL for SKU {manual_sku}: {image_src}")
