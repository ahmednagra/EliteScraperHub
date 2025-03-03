word = "For Loop"
x = ""
for i in word:
    x += i
    print(x)  
primes = [2, 3, 5, 7]
for prime in primes:
    print(f"prime loop: ",prime)

for i in range(0, 50, 7):
    print(f"for loop with 5 rangr: ",i)    

fruits = ['apple', 'banana', 'cherry']
for i, fruit in enumerate(fruits):
    print(f"For loop with enumerate:  ",i, fruit)
 
   
word = "While Loop"
x = ""
for i in word:
    x += i
    print(x)      

count = 0
while True:
    print(f"while with brak loop: ",count)
    count += 1
    if count >= 3:
        break    

for x in range(10):
    # Check if x is even
    if x % 2 == 0:
        continue
    print(f"while with continue loop odd numbers: ",x)    
    
word = "If Else Loop"
x = ""
for i in word:
    x += i
    print(x)    
    
    
x = 10
if x > 5:
    print("x is greater than 5")
else:
    print("x is less than or equal to 5")

# Prints out 1,2,3,4
for i in range(1, 10):
    if(i%5==0):
        break
    print(f"if else loop with range of 5 : ", i)
else:
    print("this is not printed because for loop is terminated because of break but not due to fail in condition")
    
    
word = "Match Case stat"
x = ""
for i in word:
    x += i
    print(x)      
    

# Importing the required modules
from enum import Enum

# Defining an enum class
class Color(Enum):
    RED = 1
    GREEN = 2
    BLUE = 3

# Initializing the color variable
color = Color.GREEN

# Using the match-case statement
match color:
    case Color.RED:
        print("The color is red")
    case Color.GREEN:
        print("The color is green")
    case Color.BLUE:
        print("The color is blue")
       