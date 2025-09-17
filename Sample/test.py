# List operations in Python
''' fruit = ["apple", "banana", "cherry"]
print(fruit)
fruit.append("orange")
print(fruit)
print(fruit[3])
fruit[1] = "blackcurrant"
print(fruit)
fruit.remove("blackcurrant")
print(fruit)
print(len(fruit)) '''

# Tuple operations in Python
''' colors = ("red", "green", "blue")
print(colors)
print(colors[-1])
print(colors[1:3])
print(len(colors))
type(colors) '''

# Set operations in Python
''' animals = {"cat", "dog", "rabbit"}
print(animals)
animals.add("hamster")
print(animals) '''
# Dictionary operations in Python
''' person = {"name": "Raguram", "age": 32, "city": "Chennai"} 
print(person)
print(person["name"])
person["age"] = 33
print(person) '''

# Control flow in Python
''' amount = int(input("Enter the amount: "))
if amount == 300:
    print("You can buy a cake")
elif amount > 300:
    print("You can buy a cake+gift")
elif amount < 300 and amount >=200:
    print("You can buy a gift")
else:
    print("You cannot buy anything") '''
# Nested if-else 
''' amount = int(input("Enter the amount: "))
if amount >= 300:
    type = str(input("You can buy a cake or gift: "))
    if type == "cake":
        print("You can buy a cake")
    else:
        print("You can buy a gift")
else:
    print("You cannot buy anything") '''

# Looping in Python
''' for i in range(1,5):
    print(i)
while i < 10:
    print(i)
    i +=1 '''

# Functions in Python
''' a = 1
b = 2 
def add(a, b):
    c = a + b
    return c
print(add(a, b)) '''

# Error handling in Python
''' try:
    a = int (input("Enter a number :"))
    b = int (input("Enter another number :"))
    c = a / b
    print(c)
except Exception as r:
    raise r

else:
    print("No error occured")
finally:
    print("Execution completed") '''

#File Handling in Python
#Reading and Writing Files
#Opening a File
file = open("note.txt", "r")
#Reading the File
content = file.read()
print(content)
# writing to a file write mode
file = open("note.txt" , "w")
file.write("I am learning python file handling.")
file.close()
# writing to a file append mode
file = open("note.txt" , "a")
file.write("I am learning python file handling.")
file.write("\nI need to practice more.")
file.write("\nI will become good in python file handling.")
file.close()
# using with statement to open a file
with open("note.txt", "r") as file:
    content = file.read()
    print(content)
    file.close()
    #import os
#os.remove("note.txt")

# Mastering File Handling in Python using OS and Importing Custom Modules
''' import os
os.getcwd()
os.listdir()
#os.mkdir("Code")
from Code.package import add, sub
print(add(5, 3))
print(sub(5, 3)) '''