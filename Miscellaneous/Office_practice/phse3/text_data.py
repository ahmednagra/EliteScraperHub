with open('file.txt', 'r') as f:
    line = f.read()
    print(line)
print('insert some line into text file')

with open('file.txt', 'a') as file:
    file.write('Pakistan \n is situated in \n contenent asia.\n')
