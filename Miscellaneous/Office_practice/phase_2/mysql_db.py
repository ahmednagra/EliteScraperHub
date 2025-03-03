import mysql.connector

# Connect to MySQL server
mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="office_db"
)

# Check if the database exists
cursor = mydb.cursor()
cursor.execute("SHOW DATABASES")
databases = cursor.fetchall()
# db_exists = False
# for database in databases:
#     if 'office_db' in database:
#         db_exists = True
#         print(f'databse already exists')
#         break

# # Create the database if it doesn't exist
# if not db_exists:
#     cursor.execute("CREATE DATABASE office_db")
cursor.execute("CREATE DATABASE IF NOT EXISTS office_db")

# define table name
table_name = 'staff'

cursor.execute(
    f"CREATE TABLE IF NOT EXISTS {table_name} ( id INT NOT NULL AUTO_INCREMENT PRIMARY KEY, FIRST_NAME CHAR(20) NOT NULL,LAST_NAME CHAR(20),AGE INT,SEX CHAR(1))")
print(f'Table {table_name} Created ')
mydb.commit()

# insert data into staff table
table_data = "INSERT INTO staff (FIRST_NAME, LAST_NAME, AGE, SEX ) VALUES (%s, %s,%s, %s)"
values = ("Muhammad", "Usama", "27", "male")
cursor.execute(table_data, values)
mydb.commit()
# print the number of rows affected by the query
print(cursor.rowcount, "record inserted.")

# reding table from db
cursor.execute("SELECT * FROM staff")
data = cursor.fetchall()
# iterate over the data and print it out
for row in data:
    print(row)

 # update the data
sql = "UPDATE staff SET LAST_NAME = 'Shah' WHERE id = 2"
cursor.execute(sql)
mydb.commit()
# print the number of rows affected
print(cursor.rowcount, "record(s) updated")

# delete value against id
query = "DELETE FROM staff WHERE id = '4'"
cursor.execute(query)
mydb.commit()

print(cursor.rowcount, "record(s) Deleted")

# Closing the connection
cursor.close()
mydb.close()
