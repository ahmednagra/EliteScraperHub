list = ['cat', 'bat', 'rat', 'elephant', 'cat']
print(f"simplw List:", list)
print(f"list cat count: ", list.count('cat'))
print(f"list elephant index : ", list.index('elephant'))
print(f"list elephant index : ", list.index('elephant'))

print(f"Reverse list: ", list.reverse())

print(f"lion add in list : ", list.append('lion'))
print(f"lion append in the List:", list)

print(f"last element remove from list : ", list.pop())
print(f"last element popped:", list)

print(f"cat element remove from list : ", list.remove('cat'))
print(f"cat element removed:", list)

list.sort()
print(f"afetr Sort List:", list)


print(f"count A's in list: ", list.count('a'))

print(f"Length list: ", len(list))

print(f"smallest Value in list : ", min(list))

print(f"Largest Value in list : ", max(list))

for i, lst in enumerate(list):
    print(f"enumerate of list:", i, lst)


# zip function ['cat', 'bat', 'rat', 'elephant', 'cat']
new_list = [' ball', ' milk', ' height', ' hide']
zip_list = []
for l, n in zip(list, new_list):
    zip_list.append(l + n)
print(f"Zip Function :", zip_list)
