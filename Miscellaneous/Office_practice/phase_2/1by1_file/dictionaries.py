import random
capital_city = {"Nepal": "Kathmandu", "Italy": "Rome", "England": "London"}

unique_values = set(capital_city.values())
print(f"Dictionary Capital Cities: ", capital_city)
print('unique values from dic', unique_values)


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
