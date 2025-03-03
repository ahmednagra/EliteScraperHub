
from datetime import datetime as dt
from datetime import timedelta
from dateutil.relativedelta import relativedelta
from itertools import zip_longest
word = "Conversion date into multiple format"
x = ""
for i in word:
    x += i
    print(x)

today = dt.today()
print('today with datetime library', today)
print('Current date & time with ctime func:', today.ctime())

print('')
print('Converting Dates to Strings with strftime() function')

# We have used the following character strings to format the date:

# %a: Returns the first three characters of the weekday, e.g. Wed.
# %A: Returns the full name of the weekday, e.g. Wednesday.
# %b: Returns the first three characters of the month name. In our example, it returned "Sep".
# %B: Returns the full name of the month, e.g. September.
# %c: Returns the local date and time version.
# %d: Returns day of the month, from 1 to 31. In our example, it returned "15".
# %f: Returns microsecond from 000000 to 999999.
# %H: Returns the hour. In our example, it returned "00".
# %m: Returns the month as a number, from 01 to 12.
# %M: Returns the minute, from 00 to 59. In our example, it returned "00".
# %p: Returns AM/PM for time.
# %S: Returns the second, from 00 to 59. In our example, it returned "00".
# %U: Returns the week number of the year, from 00 to 53,
#     with Sunday counted as the first day of each week
# %W: Returns the week number of the year, from 00 to 53,
#      with Monday being counted as the first day of the week.
# %x: Returns the local version of date.
# %X: Returns the local version of time.
# %Y: Returns the year in four-digit format. In our example, it returned "2022".
# %y: Returns the year in two-digit format, that is,
#     without the century. For example, "18" instead of "2018".
# %Z: Returns the timezone.
# %z: Returns UTC offset.

date_time = dt.today()
print(date_time.strftime(" %b/ %d/ %Y %H:%M:%S:%p"))
print(date_time.strftime("'%d-%b-%Y' %H:%M:%S"))
print(date_time.strftime("%A, %B %d, %Y, Time %H:%M:%S:%p"))

print("")
print("Converting Strings to Dates with strptime")
string = "02/04/2023 14:35:32:PM"
print("date string =", string)
print("type of date_string =", type(string))
# Considering date is in dd/mm/yyyy format
date_object = print("convert string into date",
                    dt.strptime(string, "%d/%m/%Y %H:%M:%S:%p"))
# Considering date is in mm/dd/yyyy format
date = print("convert string into date", dt.strptime(
    string, "%m/%d/%Y %H:%M:%S:%p"))


word = "Add 2 dates"
x = ""
for i in word:
    x += i
    print(x)

# Add 1 day
print('Add 1 day: ', dt.now() + timedelta(days=1))
# Add 2 years
print('Add 2 years: ', dt.now() + timedelta(days=730))
# Pass multiple parameters (1 day and 5 minutes)
print('Pass multiple parameters (1 day and 5 minutes): ',
      dt.now() + timedelta(days=1, minutes=5))

# Pass multiple parameters (Subtract 1 day and 5 minutes)
print('Pass multiple parameters (1 day and 5 minutes): ',
      dt.now() - timedelta(days=1, minutes=5))
# Pass multiple parameters (Subtract 365 day and minutes)
print('Pass multiple parameters (1 year , 5 months and 10 minutes): ',
      dt.now() - timedelta(days=515, minutes=10))
print("")
print("Adding/Subtracting Days from a given Date ")
# dates in string format
str_d1 = '2023/10/20'
str_d2 = '2013/2/20'
# convert string to date format
d1 = dt.strptime(str_d1, "%Y/%m/%d")
print('First Date is   : ', d1)
d2 = dt.strptime(str_d2, "%Y/%m/%d")
print('Seccond Date is : ', d2)
# subtract dates
subtract = d2 - d1
print(f'After Subtracting Difference is {subtract.days} days')
# Adding date to month 25
d3 = d1 + relativedelta(years=2, month=10)

print(f'After Adding new date is : {d3} ')


word = "zip Func"
x = ""
for i in word:
    x += i
    print(x)

fruits = ["apples", "oranges", "bananas", "melons"]
prices = [20, 10, 5, 15]
quantities = [5, 7, 3, 4]

for fruit, price, quantity in zip(fruits, prices, quantities):
    print(
        f"Zip FUnction output====== You bought {quantity} {fruit} for ${price*quantity}")

print('')
print('Zip Longest Function')
L1 = [1, 2, 3, 4, 5]
L2 = ['a', 'b', 'c', 'd']

zipL_L1L2 = zip_longest(L1, L2)
print('Zip longest Func output : ', list(zipL_L1L2))
