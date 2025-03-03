import json

with open('data.json', 'r') as f:
    data = json.load(f)
print(data)

print('insert data into json file')
data = {"name": "John", "age": 30},
{"name": "Jane", "age": 25},
{"name": "Bob", "age": 40}

# encode data as a JSON string
json_data = json.dumps(data)
with open("data.json", "w") as outfile:
    outfile.write(json_data)
