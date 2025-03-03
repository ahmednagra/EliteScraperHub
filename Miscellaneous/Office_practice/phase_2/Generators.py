# # def generator_name(arg):
# #     # statements
# #     yield something
# #  yield  keyword is used to produce a value from the generator.
# When the generator function is called, it does not execute the function
# body immediately. Instead, it returns a generator object that can be
# iterated over to produce the values

print("generator with while loop")
def number_sequence(n):
    """A generator function that generates a sequence of numbers from 0 to n-1."""
    i = 0
    while i < n:
        yield i
        i += 1
# Create a generator object that generates a sequence of numbers from 0 to 9
seq = number_sequence(10)
# Iterate over the generator object and print each value
for num in seq:
    print(num)

print("generator with for loop")
# create the generator object
squares_generator = (i * 2 for i in range(8))

# iterate over the generator and print the values
for i in squares_generator:
    print(i)