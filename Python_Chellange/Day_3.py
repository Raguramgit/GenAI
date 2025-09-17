import streamlit as st

def add(x, y):
    return x + y

def subtract(x, y):
    return x - y

def multiply(x, y):
    return x * y

def divide(x, y):
    if y == 0:
        return "Error: Division by zero"
    return x / y

def main():
    st.title("🧮 Simple Calculator")
    st.write("Select an operation and enter numbers:")

    # Dropdown for operation selection
    operation = st.selectbox("Choose operation", ["Add", "Subtract", "Multiply", "Divide"])

    # Number inputs
    num1 = st.number_input("Enter first number", value=0.0, format="%.2f")
    num2 = st.number_input("Enter second number", value=0.0, format="%.2f")

    # Calculate button
    if st.button("Calculate"):
        if operation == "Add":
            result = add(num1, num2)
        elif operation == "Subtract":
            result = subtract(num1, num2)
        elif operation == "Multiply":
            result = multiply(num1, num2)
        elif operation == "Divide":
            result = divide(num1, num2)
        else:
            result = "Invalid Operation"

        st.success(f"Result: {result}")

if __name__ == "__main__":
    main()
