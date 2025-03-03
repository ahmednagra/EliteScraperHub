# Token	Matches
#   ^	    Start of a string
#   $	    End of a string
#   .	    Any character (except \n)
#    |  	Characters on either side of the symbol
#    \  	Escapes special characters
#   Char	The character given
#   *	    Any number of previous characters
#   ?	    1 previous character
#    +  	1 or more previous characters
#   {Digit}	        Exact number
#   {Digit-Digit)	Between range
#   \d  	Any digit
#   \s	    Any whitespace character
#    \w	    Any word character
#   \b	    Word boundary character
#   \D  	Inverse of \d
#   \S	    Inverse of \s
#   \W	    Inverse of \w

# main function
# re.findall()
# re.split()
# re.sub()
# re.search()
# match.group()


# Program to extract numbers from a string

import re

string = 'hello 12 hi 89. Howdy 34'
pattern = '\d+'
result = re.findall(pattern, string)
print('find all function : ', result)

string = 'Twelve:12 Eighty nine:89.'
pattern = '\d+'
result = re.split(pattern, string)
print('split function', result)

# Program to remove all whitespaces
# multiline string
string = 'abc 12\
de 23 \n f45 6'
# matches all whitespace characters
pattern = '\s+'
replace = ''
new_string = re.sub(r'\s+', replace, string, 1)
print('sub func for removing white spaces : ', new_string)

string = "Python is fun"
# check if 'Python' is at the beginning
match = re.search('\APython', string)
if match:
    print("search function: pattern found inside the string")
else:
    print("pattern not found")
