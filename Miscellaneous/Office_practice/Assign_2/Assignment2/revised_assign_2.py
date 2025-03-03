<<<<<<< HEAD
import csv

import mysql.connector


class TennisClass:
    def __init__(self):
        self.headers, self.matches = self.read_csv_file()
        self.db_connection = mysql.connector.connect(
            user='root', host='localhost', port='3306')
        self.cursor = self.db_connection.cursor()
        self.db_fields = [header.replace(' ', '_')
                          .replace('%', 'Percent') for header in self.headers]

        # check if database exists, create if not
        self.cursor.execute(
            "CREATE DATABASE IF NOT EXISTS tennis_data_revised")
        self.db_connection.database = "tennis_data_revised"

    def read_csv_file(self):
        with open('Tennis Data.csv', "r") as csvfile:
            matches = csv.DictReader(csvfile)
            headers = matches.fieldnames

            return (headers, list(matches))

    def create_table(self):
        create_table_query = f"CREATE TABLE IF NOT EXISTS matches\
             (id INT AUTO_INCREMENT PRIMARY KEY"

        for header in self.db_fields:
            create_table_query += f", {header} VARCHAR(150)"

        create_table_query += ", date_created DATETIME DEFAULT \
              CURRENT_TIMESTAMP,\
            date_modified DATETIME DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,\
                  UNIQUE(Match_ID))"

        self.cursor.execute(create_table_query)

        print('Table created According to Csv Filename Fields')

    def insert_records(self):
        for match in self.matches:
            values = [match.get(col) for col in self.headers]
            insert_query = f"INSERT INTO matches ({', '.join(self.db_fields)})\
                  VALUES ({', '.join(['%s']*len(self.db_fields))}) \
                    ON DUPLICATE KEY UPDATE \
                          {', '.join([f'{record}=VALUES({record})' for record in self.db_fields])} "

            self.cursor.execute(insert_query, values)

        self.db_connection.commit()

    def show_events(self):
        events = sorted(set(match['Event'] for match in self.matches))
        # for index, event in enumerate(events, start=1):
        #     print(f"{index}. {event}")

        # all events automatically write in csvs
        for selected_event in events:
            file_name = list(selected_event + ".csv")

        self.create_events_file(file_name, selected_event)

    def create_events_file(self, file_name, selected_event):
        # list show str error so join the list into string single , elements
        file_name = ''.join(file_name)

        with open(file_name, 'w', newline='') as csv_file:
            fieldnames = self.matches[0].keys()
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()

            for match in self.matches:
                if match['Event'] == selected_event:
                    writer.writerow(match)

        print(f"Successfully wrote {selected_event} data to {file_name}")


def main():
    tennis = TennisClass()
    tennis.create_table()
    tennis.insert_records()
    tennis.show_events()
    tennis.create_events_file


if __name__ == '__main__':
    main()
=======
import csv

import mysql.connector


class TennisClass:
    def __init__(self):
        self.headers, self.matches = self.read_csv_file()
        self.db_connection = mysql.connector.connect(
            user='root', host='localhost', port='3306')
        self.cursor = self.db_connection.cursor()
        self.db_fields = [header.replace(' ', '_')
                          .replace('%', 'Percent') for header in self.headers]

        # check if database exists, create if not
        self.cursor.execute(
            "CREATE DATABASE IF NOT EXISTS tennis_data_revised")
        self.db_connection.database = "tennis_data_revised"

    def read_csv_file(self):
        with open('Tennis Data.csv', "r") as csvfile:
            matches = csv.DictReader(csvfile)
            headers = matches.fieldnames

            return (headers, list(matches))

    def create_table(self):
        create_table_query = f"CREATE TABLE IF NOT EXISTS matches\
             (id INT AUTO_INCREMENT PRIMARY KEY"

        for header in self.db_fields:
            create_table_query += f", {header} VARCHAR(150)"

        create_table_query += ", date_created DATETIME DEFAULT \
              CURRENT_TIMESTAMP,\
            date_modified DATETIME DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,\
                  UNIQUE(Match_ID))"

        self.cursor.execute(create_table_query)

        print('Table created According to Csv Filename Fields')

    def insert_records(self):
        for match in self.matches:
            values = [match.get(col) for col in self.headers]
            insert_query = f"INSERT INTO matches ({', '.join(self.db_fields)})\
                  VALUES ({', '.join(['%s']*len(self.db_fields))}) \
                    ON DUPLICATE KEY UPDATE \
                          {', '.join([f'{record}=VALUES({record})' for record in self.db_fields])} "

            self.cursor.execute(insert_query, values)

        self.db_connection.commit()

    def show_events(self):
        events = sorted(set(match['Event'] for match in self.matches))
        # for index, event in enumerate(events, start=1):
        #     print(f"{index}. {event}")

        # all events automatically write in csvs
        for selected_event in events:
            file_name = list(selected_event + ".csv")

        self.create_events_file(file_name, selected_event)

    def create_events_file(self, file_name, selected_event):
        # list show str error so join the list into string single , elements
        file_name = ''.join(file_name)

        with open(file_name, 'w', newline='') as csv_file:
            fieldnames = self.matches[0].keys()
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()

            for match in self.matches:
                if match['Event'] == selected_event:
                    writer.writerow(match)

        print(f"Successfully wrote {selected_event} data to {file_name}")


def main():
    tennis = TennisClass()
    tennis.create_table()
    tennis.insert_records()
    tennis.show_events()
    tennis.create_events_file


if __name__ == '__main__':
    main()
>>>>>>> 54fa324ad56a0cea14827c1468020459030b7b98
