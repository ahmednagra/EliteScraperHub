
print("first esample")
# put unsafe operation in try block
try:
     print("code start")
     # unsafe operation perform
     print(1 / 0)
  
# if error occur the it goes in except block
except:
     print("an error occurs")
  
# final code in finally block
finally:
     print("End of code ")


print("Seccond esample")
# try for unsafe code
try:
    amount = 3699
    if amount < 2999:
          
        # raise the ValueError
        raise ValueError("please add money in your account")
    else:
        print("You are eligible to purchase DSA Self Paced course")
              
# if false then raise the value error
except ValueError as e:
        print(e)     
        

print("3rd esample")
try: 
    a = [1, 2, 3] 
    print (a[3]) 
except LookupError: 
    print ("Index out of bound error.")
else: 
    print ("Success")