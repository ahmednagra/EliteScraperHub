import csv

# read csv file
with open('products.csv', newline='') as csvfile:
    reader = csv.DictReader(csvfile)
    products = [row for row in reader]
    print('product dicit', len(products))

# # 1:: Display all (unique) categories to user and allow him to choose category. The chosen category should be used in next steps to work with the products of this chosen category
categories = set(product['category'] for product in products)
# Display all categories
print('Categories:')
for i, category in enumerate(categories):
    print(f"{i+1}. {category}")
# choose a category
chosen_category = input('Enter a category by number: ')
chosen_category = list(categories)[int(chosen_category)-1]
print(f"\nYou have chosen category: {chosen_category}")


# Filter products by chosen category
filtered_products = []
for product in products:
    if product['category'] == chosen_category:
        filtered_products.append(product)
        # print('product from selected category', product)
print('filtered_products', len(filtered_products))

# Display all filters: rating, color, size, price_range and allow user to choose
given_filters = ['rating', 'color', 'size', 'price_range']
print('Available filters:')
for filter in given_filters:
    print(filter)
chosen_filter = input('Choose a filter: ')
chosen_filter = given_filters[int(chosen_filter)-1]
print('chosen_filter by the user is : ', chosen_filter)

# Sort the filtered products by the chosen filter
if chosen_filter == 'rating':
    filtered_products.sort(key=lambda x: int(x['rating']), reverse=True)
elif chosen_filter == 'color':
    filtered_products.sort(key=lambda x: x['color'])
elif chosen_filter == 'size':
    filtered_products.sort(key=lambda x: x['size'], reverse=True)
elif chosen_filter == 'price_range':
    filtered_products.sort(key=lambda x: float(x['price']), reverse=True)

# Give the following menu to user to choose task:
print('Choose a task:')
print('1. Show max price 10 items')
print('2. Show min price 10 items')
print('3. Show top rated 10 items')
print('4. Show latest 10 items')
chosen_task = int(input("Enter the number of task you want to choose: "))
print('chosen_task', chosen_task)


# Show 10 items in table id title
product_ids = []
print('No\t\tid\t\t\t\t\ttitle')
if chosen_task == 1:
    print(f"Max Price Items:")
    for i, product in enumerate(filtered_products[-10:], start=1):
        print(f"{i}\t{product['product_id']}\t\t{product['title']}")
        product_ids.append(product['product_id'])
elif chosen_task == 2:
    print("min price items")
    for i, product in enumerate(filtered_products[:10], start=1):
        print(f"{i}\t {product['product_id']}\t\t{product['title']}")
elif chosen_task == 3:
    print("top rated items")
    for i, product in enumerate(sorted(filtered_products, key=lambda x: float(x['rating']), reverse=True)[:10], start=1):
        print(f"{i}\t {product['product_id']}\t\t{product['title']}")
elif chosen_task == 4:
    print("latest items")
    for i, product in enumerate(sorted(filtered_products, key=lambda x: x['arrival_date'], reverse=True)[:10], start=1):
        print(f"{i}\t  {product['product_id']}\t\t{product['title']}")

choosen_id = input('Choose an No: ')
choosen_id = product_ids[int(choosen_id)-1]
print('Selected id from user is: ', choosen_id)

# Find the product with the matching ID
for product in products:
    if product['product_id'] == choosen_id:
        # Display the product information
        print('Arrival Date: ', product['arrival_date'])
        print('Title: ', product['title'])
        print('Category: ', product['category'])
        print('Color: ', product['color'])
        print('Rating: ', product['rating'])
        print('Size: ', product['size'])
        print('Price: ', product['price'])
        print('Material Info: ', product['material_info'])
        break
