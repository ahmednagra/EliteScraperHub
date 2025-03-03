import re

birth_info = 'Death Record July 2006 (age 61)'
match = re.search(r'\(age (\d+)\)', birth_info)

if match:
    age = int(match.group(1))  # Extracts the age as an integer
    print(f"Extracted age: {age}")