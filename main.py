def add_expense():
    category = input("Enter category: ")
    amount = input("Enter amount: ")

    with open("expenses.txt", "a") as file:
        file.write(f"{category},{amount}\n")

    print("Expense added!")


def view_expenses():
    with open("expenses.txt", "r") as file:
        expenses = file.readlines()

    if not expenses:
        print("No expenses found.")
        return

    print("\nExpenses:")
    for expense in expenses:
        category, amount = expense.strip().split(",")
        print(f"{category}: ${amount}")


def show_total():
    total = 0

    with open("expenses.txt", "r") as file:
        expenses = file.readlines()

    for expense in expenses:
        category, amount = expense.strip().split(",")
        total += float(amount)

    print(f"\nTotal Expenses: ${total:.2f}")


while True:
    print("\nExpense Tracker")
    print("1. Add Expense")
    print("2. View Expenses")
    print("3. Show Total")
    print("4. Exit")

    choice = input("Choose an option: ")

    if choice == "1":
        add_expense()
    elif choice == "2":
        view_expenses()
    elif choice == "3":
        show_total()
    elif choice == "4":
        print("Goodbye!")
        break
    else:
        print("Invalid option.")