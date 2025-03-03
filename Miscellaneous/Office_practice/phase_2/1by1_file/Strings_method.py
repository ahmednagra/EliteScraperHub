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
