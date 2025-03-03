import mysql.connector
import csv

from itertools import islice


class TennisClass:
    def __init__(self):
        self.cnx = mysql.connector.connect(
            user='root', host='localhost', port='4306')
        print('sql Connection', self.cnx)
        self.cursor = self.cnx.cursor()

        # check if database exists, create if not
        self.cursor.execute("CREATE DATABASE IF NOT EXISTS tennis_data")
        self.cnx.database = "tennis_data"

    def create_table(self):
        with open('Tennis Data.csv', 'r') as f:
            reader = csv.reader(f)
            headers = next(reader)
            create_table_query = f"CREATE TABLE IF NOT EXISTS matches (id INT AUTO_INCREMENT PRIMARY KEY)"

            for header in headers:
                column_name = header.replace(
                    ' ', '').lower().replace('%', 'percent')
                create_table_query += f", {column_name} TEXT"

            create_table_query += ", date_created DATETIME DEFAULT CURRENT_TIMESTAMP, DATETIME NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP)"
            print('create_table_query:   ', create_table_query)
            self.cursor.execute(create_table_query)

    def insert_data(self):
        table_name = 'matches'
        # Open the CSV file
        with open('Tennis Data.csv', 'r') as f:
            reader = csv.reader(f)
            headers = next(reader)
            headers = [header.replace(' ', '').lower().replace(
                '%', 'Percent') for header in headers]
            # read the first 1000 rows
            rows = list(islice(reader, 1000))
            for row in rows:
                # add new records or update existing ones
                values = tuple(val for val in row)
                insert_query = f"INSERT INTO {table_name} ({', '.join(headers)}) VALUES ({', '.join(['%s']*len(headers))})"
                self.cursor.execute(insert_query, values)
                self.cnx.commit()
            return self.cursor.rowcount

    def close_connection(self):
        self.cursor.close()
        self.cnx.close()


if __name__ == '__main__':
    data = TennisClass()
    data.create_table()
    num_rows = data.insert_data()
    print(f"{num_rows} rows inserted.")
    data.close_connection()
