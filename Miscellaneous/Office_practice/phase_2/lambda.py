# Example 2: Sorting a list of tuples based on second element
students = [("Alice", 20), ("Bob", 19), ("Charlie", 21), ("David", 18)]
students.sort(key=lambda x: x[1])  # Sorting based on second element of each tuple
print(f"lambda function sort the tuple based value : ",students)  
# Output: [("David", 18), ("Bob", 19), ("Alice", 20), ("Charlie", 21)]

# Example 3: Filtering a list of numbers
numbers = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
even_numbers = list(filter(lambda x: x % 2 == 0, numbers))  # Filtering only even numbers
print(f"lambda function filter even list  : ", even_numbers) 
# Output: [2, 4, 6, 8, 10]

# Example 4: Mapping a list of numbers to their squares
numbers = [1, 2, 3, 4, 5]
squares = list(map(lambda x: x ** 2, numbers))  # Mapping each number to its square
print(f"map lambda , list to its square: ",squares) 
# Output: [1, 4, 9, 16, 25]