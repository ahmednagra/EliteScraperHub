
import csv
import mysql.connector
from itertools import islice


class TennisClass:
    def __init__(self):
        self.headers, self.reader = self.read_csv_file()

        self.cnx = mysql.connector.connect(
            user='root', host='localhost', port='4306')
        print('sql Connection', self.cnx)
        self.cursor = self.cnx.cursor()

        # check if database exists, create if not
        self.cursor.execute("CREATE DATABASE IF NOT EXISTS tennis_data")
        self.cnx.database = "tennis_data"

    def read_csv_file(self):

        with open('Tennis Data.csv', "r") as csvfile:
            reader = csv.DictReader(csvfile)
            headers = next(reader)

            return (headers, (list[reader]))

    def create_table(self):
        table_name = 'matches'
        # code for mysql table
        with open('Tennis Data.csv', 'r') as f:
            reader = csv.reader(f)
            headers = next(reader)
            create_table_query = f"CREATE TABLE IF NOT EXISTS matches (id INT AUTO_INCREMENT PRIMARY KEY"

            for header in headers:
                column_name = header.replace(
                    ' ', '').lower().replace('%', 'Percent')
                print('column names:', column_name)
                create_table_query += f", `{column_name}` TEXT"
                # print(create_table_query)
            create_table_query += ", date_created DATETIME DEFAULT CURRENT_TIMESTAMP,date_modified DATETIME DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP)"
            self.cursor.execute(create_table_query)

    def insert_records(self):
        table_name = 'matches'
        # Open the CSV file
        with open('Tennis Data.csv', 'r') as f:
            reader = csv.reader(f)
            headers = next(reader)
            headers = [header.replace(' ', '').lower().replace(
                '%', 'Percent') for header in headers]
            # match Id compare
            match_id_index = headers.index('matchid')
            # add first 1000 values
         # add new records or update existing ones
            for row in islice(reader, 1200):
                values = tuple(val for val in row)
                match_id = values[match_id_index]

                # Check if the record already exists
                self.cursor.execute(
                    f"SELECT * FROM {table_name} WHERE matchid = %s", (match_id,))
                existing_record = self.cursor.fetchone()
                if existing_record:
                    # Check if the existing record needs to be updated
                    update_query = f"UPDATE {table_name} SET {', '.join(f'{header} = %s' for header in headers)} WHERE matchid = %s"
                    if existing_record[1:] != values:
                        self.cursor.execute(update_query, values + (match_id,))
                    else:
                        continue  # Record already up-to-date
                else:
                    insert_query = f"INSERT INTO {table_name} ({', '.join(headers)}) VALUES ({', '.join(['%s']*len(headers))})"
                    self.cursor.execute(insert_query, values)
                print('existing_record', existing_record)
                self.cnx.commit()

    def show_events(self):
        events = sorted(set(match['Event']
                            for match in self.matches_data))
        print("Events:")
        for index, event in enumerate(events, start=1):
            print(f"{index}. {event}")
        self.max_evt = len(events)
        print('Total Events are : ', self.max_evt)

        # all events automatically write in csvs
        for selected_event in events:
            file_name = f"{selected_event}.csv"

            with open(file_name, 'w', newline='') as csv_file:
                fieldnames = self.matches_data[0].keys()
                writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
                writer.writeheader()

                for match in self.matches_data:
                    if match['Event'] == selected_event:
                        writer.writerow(match)

            print(f"Successfully wrote {selected_event} data to {file_name}")

    def show_events1_1(self):
        events = sorted(set(match['Event']
                            for match in self.matches_data))
        print("Events:")
        for index, event in enumerate(events, start=1):
            print(f"{index}. {event}")
        self.max_evt = len(events)
        print('Total Events are : ', self.max_evt)

        while True:
            try:
                event_number = int(
                    input(f"Enter the event number to export data 1- {len(events)} : "))
                if event_number not in range(1, len(events) + 1):
                    raise ValueError
                break
            except ValueError:
                print('Invalid event number')

        selected_event = events[event_number - 1]
        file_name = f"{selected_event}.csv"

        with open(file_name, 'w', newline='') as csv_file:
            fieldnames = self.matches_data[0].keys()
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()

            for match in self.matches_data:
                if match['Event'] == selected_event:
                    writer.writerow(match)

        print(f"Successfully wrote {selected_event} data to {file_name}")


def main():
    data = TennisClass()
    data.read_csv_file()
    data.create_table()
    data.insert_records()
    data.show_events()
    data.show_events1_1()


if __name__ == '__main__':
    main()
