word = "Strings Method"
x = ""
for i in word:
    x += i
    print(x) 
    
txt = "hello, welcome to office."
txt2 = "At Gujranwala"
print(f"simplr string :", txt)
# - Converts the first character to upper case
string = txt.capitalize()
print(f"capitalize string:",  string)

# Converts the first character of each word to upper case
upper_string = txt.title()
print(f"upper case string:",  upper_string)

True_upper_case = upper_string.islower()
print(f"upper case string:",  True_upper_case)

# Converts a string into lower case
lower_string = txt.lower()
print(f"lower case string:",  lower_string)

# Returns True if all characters in the string are lower case
True_lower_case = lower_string.islower()
print(f"lower case string:",  True_lower_case)

# Swaps cases, lower case becomes upper case and vice versa
swap_string = txt.swapcase()
print(f"letter swap from uperr to lower $ lower to upper:",  swap_string)

#  Returns the number of times a specified value occurs in a string
Count_string = txt.count('w')
print(f"W Count in string:",  Count_string)

# Returns True if all characters in the string are alphanumeric
alpha_string = txt.isnumeric()
print(f"alphanumeric or not string:",  alpha_string)

# Returns True if all characters in the string are in the alphabet
alphabet_string = txt.isalpha()
print(f"alphabet or not string:",  alphabet_string)

# Splits the string at the specified separator, and returns a list
split_string = txt.split()
print(f"spli String and covert into list :",  split_string)

# String Concatenate
text = txt[0:23] + txt2
print(f"slice and Concatenate string :", text)
    
    
    
    
    
    
word = "List Method"
x = ""
for i in word:
    x += i
    print(x)      
    
list = ['cat', 'bat', 'rat', 'elephant', 'cat']
print(f"simplw List:", list)
print(f"list cat count: ", list.count('cat'))
print(f"list elephant index : ", list.index('elephant'))
print(f"list elephant index : ", list.index('elephant'))

print(f"Reverse list: ", list.reverse())

print(f"lion add in list : ", list.append('lion'))
print(f"lion append in the List:", list)

print(f"last element remove from list : ", list.pop())
print(f"last element popped:", list)

print(f"cat element remove from list : ", list.remove('cat'))
print(f"cat element removed:", list)

list.sort()
print(f"afetr Sort List:", list)


print(f"count A's in list: ", list.count('a'))

print(f"Length list: ", len(list))

print(f"smallest Value in list : ", min(list))

print(f"Largest Value in list : ", max(list))

for i, lst in enumerate(list):
    print(f"enumerate of list:", i, lst)


# zip function ['cat', 'bat', 'rat', 'elephant', 'cat']
new_list = [' ball', ' milk', ' height', ' hide']
zip_list = []
for l, n in zip(list, new_list):
    zip_list.append(l + n)
print(f"Zip Function :", zip_list)



word = "List Comprehension Method"
x = ""
for i in word:
    x += i
    print(x)  
list = " The difference is that set comprehensions"
list2 = ['cat', 'bat', 'rat', 'elephant', 'cat']
vowels = {i for i in list if i in 'aeiou'}
print(f"vowels by list comprehension method:", vowels)

comp_list = [i for i in list2 if 'a' in i]
print('')
print(f"if word a found in list show names: ", comp_list)


even_numbers = [i for i in range(30) if i % 2 == 0]
print(f"even numbers", even_numbers)

tables = [lambda x=x: x*10 for x in range(1, 11)]
for table in tables:
    print(table())


word = "Dictionaries Method"
x = ""
for i in word:
    x += i
    print(x) 

import random
capital_city = {"Nepal": "Kathmandu", "Italy": "Rome", "England": "London"}
print(f"Capital Cities: ", capital_city)

print(f"Nepal Capital Sity Name is : ", capital_city.get('Nepal'))

print(f"item method that fetch whole dic : ", capital_city.items())

print(f"VALUES method : ", capital_city.values())

print(f"keys method fetch keys in dic : ", capital_city.keys())

print(f"Pop Method : ", capital_city.pop('Nepal'))

print(f"after use pop method Capital Cities: ", capital_city)

print(f"Insert pak: isl: ", capital_city.update({"pakistan": "islamabad"}))

print(f"update method : ", capital_city)

capital_city.clear()
print(f"after using clear method : ", capital_city)    
    
word = "Dict Comprehension"
x = ""
for i in word:
    x += i
    print(x)     
# dic comprehension
customers = ["Alex", "Bob", "Carol", "Dave", "Flow", "Katie", "Nate"]
discount_dict_cus = {customer: random.randint(
    1, 100) for customer in customers}
print(discount_dict_cus)

days = ["Sunday", "Monday", "Tuesday",
        "Wednesday", "Thursday", "Friday", "Saturday"]
print(f"days dic : ", days)
temp_C = [30.5, 32.6, 31.8, 33.4, 29.8, 30.2, 29.9]
print(f"Temperature Dict :", temp_C)
weekly_temp = {day: temp for (day, temp) in zip(days, temp_C)}
print(f"Weekekly temp Dic :", weekly_temp)
    

word = "Sets Methods"
x = ""
for i in word:
    x += i
    print(x)     
set = {1, 3, 4, 5, 7}
print(f"simple Set :", set)
set.add('paksitan')
print(f"add value Set :", set)
print(f"copy Set :", set.copy())
print(f"pop method first value Set :", set.pop())

set.remove(5)
print(f"remove 5 value Set :", set)
    
word = "Tuples Methods"
x = ""
for i in word:
    x += i
    print(x)  
lang = ('java', 'c++', 'python')
year = (1995, 1983, 1991)
tup = lang + year
print(f"Languages tuple: ", lang)
print(f"Languages tuple 2nd value: ", lang[1])
print(f"tuples Concatenate: ", tup)
print(f"len func of tuples: ", len(tup))
print(f"repitation of tuple 4 time: ", (tup) * 4)
print(f"slicing language [1:]: ", lang[1:])
print(f"Type of language: ", type(lang))
print(f"Small value from Language: ", min(lang))
print(f"largest value from Language: ", max(lang))
print(f"Tuple Language: ", tuple(lang))
        