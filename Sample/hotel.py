import random

# Sangi Manki Hotel Menu
menu = {
    "Biryani": 120,
    "Parotta": 50,
    "Chicken 65": 100,
    "Soda": 30
}

success_dialogues = [
    "Saamy! sooru poduthu! 😂",
    "Saptachu pa.. Ippo thanpa kannu bright ah Thariethu😎",
]

fail_dialogues = [
    "Dai ennakunay varuviegalada! 😤",
    "Kaasu illa pa 🙃"
]

# Function to buy item
def buy_item(item, money):
    if item not in menu:
        print("Vadivelu: 'unga mathila valurathu romba kastam da!' 🤔")
        return
    
    price = menu[item]
    print(f"\nYou ordered {item} - Rs.{price}")
    print(f"You have Rs.{money}")

    if money >= price:
        print("Vadivelu:", random.choice(success_dialogues))
    else:
        shortage = price - money
        print("Vadivelu:", random.choice(fail_dialogues))


# Main Program
print("🍽️ Welcome to Sangi mangi Hotel 🍽️")
print("Today's Menu:", ", ".join([f"{k} (Rs.{v})" for k, v in menu.items()]))
money = int(input("Enter the amount you have: Rs."))
item = input("Enter the item you want to buy: ")
buy_item(item,money)
