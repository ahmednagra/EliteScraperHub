import glob
import os
import requests
from woocommerce import API
from wordpress import API as wordapi

import openai


def get_key_values_from_file():
    """
    Get the Google sheet keys and Search URLs keys  from input text file
    """
    file_path = 'input/config.txt'
    with open(file_path, mode='r', encoding='utf-8') as input_file:
        data = {}

        for row in input_file.readlines():
            if not row.strip():
                continue

            try:
                key, value = row.strip().split('==')
                data.setdefault(key.strip(), value.strip())
            except ValueError:
                pass

        return data


config = get_key_values_from_file()
auth = requests.auth.HTTPBasicAuth(config.get('user_name', ''), config.get('password', ''))

wcapi = API(
    url=config.get('url', ''),
    consumer_key=config.get('consumer_key', ''),
    consumer_secret=config.get('consumer_secret', ''),
    wp_api=True,
    version="wc/v3",
    timeout=300
)

wpapi = wordapi(
    url=config.get('url', ''),
    api="wp-json",
    version="wp/v2",
    wp_user=config.get('user_name', ''),
    wp_pass=config.get('password', ''),
    wp_auth=True,
    consumer_key=config.get('consumer_key', ''),
    consumer_secret=config.get('consumer_secret', ''),
    headers={
        'User-Agent': "MyWordPressApp/1.0",
        'Accept': 'application/json',
    },
    timeout=300
)


def image_upload(image_path):
    """
       Uploads an image to the WooCommerce media endpoint.

       Args:
           image_path (str): The local path of the image.

       Returns:
           tuple: A tuple containing image ID, image URL, and image slug.
       """
    # user_name = "MateefyShopsUS"
    # password = "CHahdoElinoChourouka16!!@@"
    media_endpoint = f"{config.get('url', '')}/wp-json/wp/v2/media"

    # Get previous media items
    previous_media = wpapi.get('media').json()

    image_name = os.path.basename(image_path).replace(' ', '_').replace('-', '_')
    images_list = [x.get('title', {}).get('rendered', '') for x in previous_media]

    # Check if the image exists in previous media
    media = [x for x in previous_media if
             os.path.splitext(x.get('title', {}).get('rendered', ''))[0] == os.path.splitext(image_name)[0]]

    if media:
        source_url = media[0].get('source_url', '')
        # img_id = media[0].get('id', '')
        img_id = None
        print(f"Image '{image_name}' found in previous media. Source URL: {source_url}")
        # if image already exist mean last time the original will removed and this time image is attached with any
        # other post so no need to remove
        return source_url, img_id
    else:
        print(f"Image '{image_name}' not found in previous media. Uploading image.")
        # Continue with image upload logic
        headers = {
            "Content-Disposition": f'attachment; filename="{os.path.basename(image_path)}"',
        }
        files = {
            # "file": (os.path.basename(image_path), open(image_path, "rb"), "image/jpeg"),
            "file": (image_name, open(image_path, "rb"), "image/jpeg"),
        }

        res = requests.post(media_endpoint, auth=auth, headers=headers, files=files)

        if res.status_code == 201:
            print("Image uploaded successfully.")
            data = res.json()
            print("Media ID:", data["id"])
            img_id = data.get('id', 0)
            img_url = data.get('source_url', '')
            img_slug = data.get('slug', '')

            print("Media URL:", data["guid"]["rendered"])
            # return img_id, img_url, img_slug
            return img_url, img_id
        else:
            print(f"Failed to upload image. Status code: {res.status_code}")
            print("Response:", res.text)
            # return None, None, None
            return None, None


def create_category(id, name):
    # create category and subcategory
    data = {"name": name,
            # "description": config.get('category_description', ''),
            "parent": id,
            "image": {"src": ""}}

    res = wcapi.post("products/categories", data)
    if res.status_code == 201:
        data = res.json()
        id = data.get('id', '')
        print(f"Category {data.get('id')} Successfully created.")
        return id

    else:
        print(f"Error: {res.status_code} - {res.text}")
        return None


def get_categories():
    """
    Gets all categories from WooCommerce.

    Args:
        wcapi: The WooCommerce API object.

    Returns:
        tuple: A tuple containing parent_cat_id and subcat_id.
    """
    # Call the get_categories function
    response = wcapi.get("products/categories", params={"per_page": 100, "page": 1})

    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        categories_response = response.json()

        # Create a list to store category information
        all_categories = categories_response

        # Check if there are more pages
        while "Link" in response.headers and "rel=\"next\"" in response.headers["Link"]:
            # Extract the next page URL from the Link header
            next_page_url = response.links["next"]["url"]

            # Make the next page request
            response = wcapi.get(next_page_url)
            if response.status_code == 200:
                categories_response = response.json()
                all_categories.extend(categories_response)
            else:
                print(f"Error: {response.status_code} - {response.text}")
                return None, None

        # Access category information by calling the category name
        category_name_to_find = config.get('sub_category', '')
        parent_cat_id, subcat_id = None, None

        for category in all_categories:
            if category['name'].lower() == category_name_to_find.lower():
                subcat_id = category.get('id', 0)
                parent_cat_id = category.get('parent', 0)

        if parent_cat_id is None and subcat_id is None:
            id = 0
            name = config.get('category', '')
            parent_cat_id = create_category(id, name)
            subcategory_name = config.get('sub_category', '')
            subcat_id = create_category(parent_cat_id, subcategory_name)

        return parent_cat_id, subcat_id

    else:
        print(f"Error: {response.status_code} - {response.text}")
        return None, None


def delete_images(img_ids):
    for img_id in img_ids:
        # endpoint_url = f'media/{img_id}?Force=True'
        endpoint = f"{config.get('url', '')}/wp-json/wp/v2/media/{img_id}"
        res = requests.delete(endpoint, auth=auth, params='force=true')

        if res.status_code == 200:
            print(f"Image with ID {img_id} deleted successfully.")
        else:
            print(
                f"Failed to delete image with ID {img_id}. Status code: {res.status_code}, Response: {res.text}")


# folders and their image now uploading
def product_upload(previous_products):
    """
        Uploads a product to WooCommerce.

        Args:
            folder (str): The path of the folder containing product images.
            parent_cat_id (int): The parent category ID.
            subcat_id (int): The subcategory ID.

        Returns:
            None
        """
    folders = glob.glob(f"{config.get('designs_path', '')}/*")
    for folder in folders[:3]:
        folder_name = os.path.basename(folder)

        if folder_name in [x.get('name') for x in previous_products]:
            print(folder_name, 'Product already Published')
            continue

        images = [f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))]

        image_list = [
            {
                "src": image_name,
                "name": image_name.replace(' ', '_').replace('-', '_'),
                "alt": image_name
            }
            for image_name in images
        ]

        # Upload images and get remote URLs
        remote_image_urls = []
        for image_data in image_list:
            image = image_data['src']
            image_path = folder + f'/{image}'
            img_url, img_id = image_upload(image_path)

            if img_url:
                # remote_image_urls.append(img_url, img_id)
                remote_image_urls.append((img_url, img_id))

        post_product = {
            "name": folder_name,
            "type": "simple",
            "regular_price": "0.00",
            "description": "Dem description, Demo description",
            "short_description": "Short Description, Short Description",
            "categories": [
                {"id": parent_cat_id},
                {"id": subcat_id}
            ],
            "images": [{"src": remote_url[0], "name": image_data["name"], "alt": image_data["alt"]} for
                       remote_url, image_data in zip(remote_image_urls, image_list)],

            "meta_data": [
                {"key": "rank_math_focus_keyword", "value": config.get('focus_keyword', '')}
            ],
        }

        # Make a POST request to create the product
        response = wcapi.post("products", data=post_product)

        if response.status_code == 201:
            uploaded_imgs_id = [x[1] for x in remote_image_urls]
            if uploaded_imgs_id:
                delete_images(uploaded_imgs_id)
            print(f"Product '{folder_name}' created successfully!")

        else:
            print(f"Error creating product '{folder_name}': {response.status_code} - {response.text}")


def products_duplication(previous_products):
    duplicate_id = config.get('product_id_to_duplicate', '')

    for product in previous_products:
        if duplicate_id == product.get('id'):
            product_id = product.get('id', 0)
            product_name = product.get('name', '')
            product_type = product.get('type')
            regular_price = product.get('regular_price')
            description = product.get('description')
            short_description = product.get('short_description')
            parent_cat_id = product.get('categories')[0].get('id', 0)
            subcat_id = product.get('categories')[1].get('id', 0)

            post_product = {
                "name": f"{product_name} Duplicate",
                "type": product_type,
                "regular_price": regular_price,
                "description": description,
                "short_description": short_description,
                "categories": [
                    {"id": parent_cat_id},
                    {"id": subcat_id}
                ],
                "images": [{"src": product.get('images')[0].get('src', ''),
                            "alt": product.get('images')[0].get('alt', ''),
                            "name": product.get('images')[0].get('name', '')
                            }],
                "meta_data": [
                    {"key": "rank_math_focus_keyword", "value": config.get('focus_keyword', '')}
                ],
            }

            # Make a POST request to create the product
            response = wcapi.post("products", data=post_product)

            if response.status_code == 201:
                print(f"Product '{f'{product_name} Duplicate'}' created successfully!")
            else:
                print(
                    f"Error creating product '{f'{product_name} Duplicate'}': {response.status_code} - {response.text}")

    # If you want to indicate the end of the function after duplicating all eligible products
    print("Duplicating products completed.")


def get_all_products():
    response = wcapi.get("products", params={"per_page": 100, "page": 1})

    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        products_response = response.json()

        # Create a list to store product information
        all_products = products_response

        # Check if there are more pages
        while "Link" in response.headers and "rel=\"next\"" in response.headers["Link"]:
            # Extract the next page URL from the Link header
            next_page_url = response.links["next"]["url"]

            # Make the next page request
            response = wcapi.get(next_page_url)
            if response.status_code == 200:
                products_response = response.json()
                all_products.extend(products_response)
            else:
                print(f"Error: {response.status_code} - {response.text}")
                return None

        return all_products

    else:
        print(f"Error: {response.status_code} - {response.text}")
        return []

parent_cat_id, subcat_id = get_categories()

previous_products = get_all_products()

product_uploads = product_upload(previous_products)

duplicate_products = products_duplication(previous_products)
