# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
import logging

from itemadapter import ItemAdapter

import mysql.connector


class HomesPropertiesPipeline:
    def process_item(self, item, spider):
        return item


class MysqlPipeline:
    def __init__(self):
        self.conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password=''
        )
        self.cur = self.conn.cursor()
        self.valid_fields = {}  # for storing the db table fields name
        self.conn.database = 'properties'

    def process_item(self, item, spider):
        tables = []
        if spider.name == 'homes_rent':
            tables.append('rent_properties')

        elif spider.name == 'homes_sale' or spider.name == 'homes_sold':
            tables.extend(['hometable', 'homes_properties'])
        else:
            raise ValueError("Invalid spider name")

        self.create_homeproperties_if_not_exists('homes_properties')

        for table_name in tables:
            # Fetch valid fields if not already fetched
            if table_name not in self.valid_fields:
                self.valid_fields[table_name] = self.get_table_columns(table_name)

            # Get the item fields and values
            fields = item.fields.keys()
            values = [item.get(field) for field in fields]

            # Retrieve the valid fields for the current table
            table_fields = self.valid_fields[table_name]

            # Filter valid fields and values for the current table
            valid_fields = [field for field in fields if field in table_fields]
            valid_values = [f"`{item.get(field)}`" if item.get(field) is not None else 'NULL' for field in valid_fields]

            placeholders = ', '.join(['%s' if value is not None else 'NULL' for value in valid_values])

            query = f"INSERT INTO `{table_name}` ({', '.join(valid_fields)}) VALUES ({placeholders})"

            # Check if the record already exists
            existing_query = f"SELECT * FROM {table_name} WHERE URL = %s"
            self.cur.execute(existing_query, (item['URL'],))
            existing_record = self.cur.fetchone()

            # If the record exists, skip insertion
            if existing_record:
                logging.info('already record found')
                continue

            # Execute the query and insert the values into the table
            self.cur.execute(query, tuple(valid_values))
            self.conn.commit()

        return item

    def close_spider(self, spider):
        print('from pipeline clode spider ')
        # Close the database connection when the spider is closed
        self.conn.close()

    def get_table_columns(self, table_name):
        # Retrieve the column names from the table schema
        query = f"SHOW COLUMNS FROM {table_name}"
        self.cur.execute(query)
        columns = [column[0] for column in self.cur.fetchall()]
        return columns

    def create_table_if_not_exists(self, table_name):
        query = f"CREATE TABLE IF NOT EXISTS {table_name} (...)"  # Define the table schema here
        self.cur.execute(query)
        self.conn.commit()

    # def process_item(self, item, spider):
    #     table_name = 'rent_properties'
    #
    #     Address = item['Address']
    #     Street = item['Street']
    #     City = item['City']
    #     State = item['State']
    #     Zip_Code = item['Zipcode']
    #     Latitude = item['Latitude']
    #     Longitude = item['Longitude']
    #     Beds = item['Beds']
    #     Baths = item['Baths']
    #     Area = item['Sqft']
    #     Property_Type = item['Property_Type']
    #     Price = item['Price']
    #     Price_Text = item['Property_Tax']
    #     Zestimate = item['Zestimate']
    #     Zestimate_Percentage = item['Zestimate_Percentage']
    #     Rent_Zestimate = item['Rent_Zestimate']
    #     Year_Built = item['Year_Built']
    #     Availability_Date = item['Availability_Date']
    #     Broker = item['Broker_Company']
    #     Image = item['Primary_Image']
    #     URL = item['URL']
    #
    #     # SQL statement to insert item data into the table
    #     query = f"""
    #             INSERT INTO {table_name} (Address, Street, City, State, Zip_Code, Latitude, Longitude, Beds, Baths, Area, Property_Type,
    #             Price, Price_Text, Zestimate, Zestimate_Percentage, Rent_Zestimate, Year_Built, Availability_Date, Broker, Image, URL)
    #             VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    #         """
    #
    #     # Values to be inserted into the table
    #     values = (
    #         Address, Street, City, State, Zip_Code, Latitude, Longitude, Beds, Baths, Area, Property_Type,
    #         Price, Price_Text, Zestimate, Zestimate_Percentage, Rent_Zestimate, Year_Built, Availability_Date, Broker,
    #         Image, URL
    #     )
    #
    #     # Execute the query and commit the changes
    #     self.cur.execute(query, values)
    #     self.conn.commit()
    #
    #     return item

    # def create_table_if_not_exists(self, table_name):
    #     self.cur.execute(f"CREATE TABLE IF NOT EXISTS {table_name} ("
    #                      "Address VARCHAR(255), "
    #                      "Street VARCHAR(255), "
    #                      "City VARCHAR(255), "
    #                      "State VARCHAR(255), "
    #                      "Zip_Code VARCHAR(255), "
    #                      "Latitude VARCHAR(255), "
    #                      "Longitude VARCHAR(255), "
    #                      "Beds VARCHAR(255), "
    #                      "Baths VARCHAR(255), "
    #                      "Area VARCHAR(255), "
    #                      "Property_Type VARCHAR(255), "
    #                      "Price FLOAT, "
    #                      "Price_Text VARCHAR(255), "
    #                      "Zestimate VARCHAR(255), "
    #                      "Zestimate_Percentage VARCHAR(255), "
    #                      "Rent_Zestimate VARCHAR(255), "
    #                      "Year_Built VARCHAR(255), "
    #                      "Availability_Date VARCHAR(255), "
    #                      "Broker VARCHAR(255), "
    #                      "Image VARCHAR(255), "
    #                      "URL VARCHAR(255)"
    #                      ")")

    def create_homeproperties_if_not_exists(self, table_name):
        query = f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                id INT AUTO_INCREMENT PRIMARY KEY,
                SearchTerm TEXT,
                Price TEXT,
                Address TEXT,
                Street TEXT,
                City TEXT,
                State TEXT,
                Zipcode TEXT,
                Baths TEXT,
                Beds TEXT,
                Sqft TEXT,
                MLS TEXT,
                Annual_Tax TEXT,
                Listing_Agent TEXT,
                Listing_Office TEXT,
                URL TEXT,
                Status TEXT,
                Sold_Date TEXT,
                Property_Type TEXT, 
                Agent_Email TEXT,
                Agent_Phone TEXT,
                Availability_Date TEXT,
                Image TEXT,
                Lot_Size_Acres TEXT,
                Other_Images TEXT,             
                Year_Built TEXT                
            )
        """
        self.cur.execute(query)
        self.conn.commit()
