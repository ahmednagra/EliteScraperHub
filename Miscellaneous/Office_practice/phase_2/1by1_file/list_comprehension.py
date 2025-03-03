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
