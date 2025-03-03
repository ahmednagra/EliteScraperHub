
import csv


class ProductClass:
    def __init__(self):
        # self.file_name = 'products.csv'
        self.products = self.read_csv_file()
        self.chosen_category = {}
        self.categories = self.display_categories()
        self.select_products_by_filter = self.filter_products_by_category()
        self.all_filters = self.filters()
        self.prodycts_by_task = self.display_tasks()
        self.chosen_id = self.take_id()

    # read csv file

    def read_csv_file(self):
        with open('products.csv', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            return [row for row in reader]

    def display_categories(self):
        categories = sorted(set(product['category']
                            for product in self.products))
        print("Categories:")
        for index, category in enumerate(categories, start=1):
            print(f"{index}. {category}")
        max_cat = len(categories)
        print('Total Categories are : ', max_cat)

    # choose a category
        while True:
            try:
                chosen_category = int(
                    input(f" Enter a category Number 1 and {max_cat}: "))
                if chosen_category < 1 or chosen_category > max_cat:
                    raise ValueError
                break
            except ValueError:
                print(f'Invalid input, please choose between 1 and {max_cat}')
        self.chosen_category = list(categories)[chosen_category - 1]
        print(f"User Select the  category: {self.chosen_category}")
        return self

    def filter_products_by_category(self):
        self.filtered_products = []
        for product in self.products:
            if product['category'] == self.chosen_category:
                self.filtered_products.append(product)
        print('filtered_products', len(self.filtered_products))
        return self.filtered_products

    def filters(self):
        given_filters = ['rating', 'color', 'size', 'price_range']
        print('Available filters:')
        for i, filter in enumerate(given_filters, start=1):
            print(f"{i}. {filter}")

        while True:
            try:
                chosen_filter = int(input('Choose a filter name (1-4): '))
                if chosen_filter not in range(1, 5):
                    raise ValueError
                break
            except ValueError:
                print('Invalid filter ID, please choose between 1 and 4')
        print('Selected filter ID:', chosen_filter)
        chosen_filter_name = given_filters[chosen_filter - 1]
        print('Selected filter:', chosen_filter_name)
        # self.filter_product = []
        if chosen_filter_name == 'rating':
            self.filtered_products.sort(
                key=lambda x: int(x['rating']), reverse=True)
        elif chosen_filter_name == 'color':
            self.filtered_products.sort(key=lambda x: x['color'])
        elif chosen_filter_name == 'size':
            self.filtered_products.sort(
                key=lambda x: x['size'], reverse=True)
        elif chosen_filter_name == 'price_range':
            self.filtered_products.sort(
                key=lambda x: float(x['price']), reverse=True)
        print('till code ok. products found : ',
              len(self.filtered_products))
        return self.filtered_products

    def display_tasks(self):
        self.product_id = []
        print('Choose a task:')
        print('1. Show max price 10 items')
        print('2. Show min price 10 items')
        print('3. Show top rated 10 items')
        print('4. Show latest 10 items')

        while True:
            try:
                chosen_task = int(
                    input("Enter the task id (1-4): "))
                if chosen_task not in range(1, 5):
                    raise ValueError
                break
            except ValueError:
                print('Invalid Task ID, please choose between 1 and 4')
        print('Task Choosed by the user is : ', chosen_task)

        print('No\t\tid\t\t\t\t\ttitle')
        if chosen_task == 1:
            print("Max Price Items:")
            for i, product in enumerate(sorted(self.filtered_products, key=lambda x: x['price'], reverse=True)[:10], start=1):
                print(f"{i}\t{product['product_id']}\t\t{product['title']}")
                self.product_id.append(product['product_id'])
        elif chosen_task == 2:
            print("min price items")
            for i, product in enumerate(sorted(self.filtered_products, key=lambda x: x['price'])[:10], start=1):
                print(f"{i}\t {product['product_id']}\t\t{product['title']}")
                self.product_id.append(product['product_id'])
        elif chosen_task == 3:
            print("top rated items")
            for i, product in enumerate(sorted(self.filtered_products, key=lambda x: float(x['rating']), reverse=True)[:10], start=1):
                print(f"{i}\t {product['product_id']}\t\t{product['title']}")
                self.product_id.append(product['product_id'])
        elif chosen_task == 4:
            print("latest items")
            for i, product in enumerate(sorted(self.filtered_products, key=lambda x: x['arrival_date'], reverse=True)[:10], start=1):
                print(f"{i}\t  {product['product_id']}\t\t{product['title']}")
                self.product_id.append(product['product_id'])
        print('len product id', len(self.filtered_products))
        return self

    def take_id(self):
        max_id = len(self.product_id)
        print('max Id length', max_id)

        while True:
            try:
                chosen_id = int(
                    input("Enter the Product id (1-10): "))
                if chosen_id not in range(1, 11):
                    raise ValueError
                break
            except ValueError:
                print('Invalid Product ID, please choose between 1 and 10')
        self.chosen_id = self.product_id[chosen_id - 1]
        print('Selected id from user is:', self.chosen_id)
    #     return self

    # # Find the product with the ID

    # def id_detail(self):
        for product in self.products:
            if product['product_id'] == self.chosen_id:
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


def main():
    product = ProductClass()
    product.read_csv_file()
    product.display_categories()
    product.filter_products_by_category()
    product.filters()
    product.display_tasks()
    product.take_id()


if __name__ == '__main__':

    main()
