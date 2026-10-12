# Bank Management System

import json
from pathlib import Path
from datetime import datetime

database = "bank_data.json"
data = { 
    "customers":[] ,
    "admin": [] ,
    "transaction":[],
    }

if Path(database).exists():
    with open(database,"r") as f:
        content = f.read()

        if content :
            data = json.load(f)
        
def save():
    with open(database, "w") as f:
        json.dump(data, f, indent=4)





class Customer :

    def create_account(self):
        customer_id = int(input("Customer_id : "))
        name = input("Name : ")
        acc_no = input("Account No. : ")
        balance = int(input("Balance : "))
        status = "pending"
        password = input("Password : ")

        for customer in data['customers']:
            if customer_id == customer['Customer ID'] :
                print("Customer already exist !!")
                return

        for customer in data['customers']:
            if acc_no == customer['Account No.'] :
                print("Customer already exist !!")
                return

        if balance <= 0 :
            print("Invalid balance")
            return
        

        details = {
            "Customer ID": customer_id ,
            "Name": name , 
            "Account No.": acc_no ,
            "Balance": balance ,
            "Status": status ,
            "Password": password ,
        }
        data['customers'].append(details)
        save()
        print(f"Successfully created an account of {name}")

    def view_profile(self):
        cust_id = int(input("Customer ID : "))
        for customer in data['customers']:
            if cust_id == customer['Customer ID'] :
                print(f"Name : {customer['Name']}")
                print(f"Balance : {customer['Balance']}")
                print(f"Account No. : {customer['Account No.']}")
                print(f"Status : {customer['Status']}")
                return
        print("Customer not Found !!")

    def withdraw(self):
        cust_id = int(input("Customer ID : "))
        withdrawal_amount = int(input("Enter the amount you want to withdraw : "))

        if withdrawal_amount <= 0 :
            print("Invalid amount")
            return

        for customer in data['customers']:
            if cust_id == customer['Customer ID'] :
                if customer["Status"].lower() != "active":
                    print("Account is inactive")

                if withdrawal_amount <= customer['Balance'] :
                    initial_balance = customer['Balance']
                    customer['Balance']-= withdrawal_amount

                    print(f"Initial balnce = Rs.{initial_balance}")
                    print(f"Amount withdrawn = Rs.{withdrawal_amount}")
                    print(f"Remaining balance = Rs.{customer['Balance']}")
                    
                    data["transaction"].append({

                        "Transaction ID": len(data["transaction"]) + 1,
                        "Type": "Withdrawal",
                        "Customer ID": cust_id,
                        "Amount": withdrawal_amount,
                        "Date": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                                                })
                    save()
                else:
                    print("Insufficient balance .....")
        print("Customer not Found !!")

    def deposit(self):
        cust_id = int(input("Customer ID : "))
        deposit_amount = int(input("Enter the amount you want to deposit : "))

        if deposit_amount <= 0 :
            print("Invalid amount")
            return
        
        for customer in data['customers']:
            if cust_id == customer['Customer ID'] :
                if customer["Status"].lower() != "active":
                    print("Account is inactive")
                    return
                initial_balance = customer['Balance']
                customer['Balance']+= deposit_amount

                print(f"Initial balance = Rs.{initial_balance}")
                print(f"Amount withdrawn = Rs.{deposit_amount}")
                print(f"Remaining balance = Rs.{customer['Balance']}")

                data["transaction"].append({

                            "Transaction ID": len(data["transaction"]) + 1,
                            "Type": "Deposit",
                            "Customer ID": cust_id,
                            "Amount": deposit_amount,
                            "Date": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                        })
                save()
        print("Customer not Found !!")

    def transfer_money(self):
        sender_id = int(input("Enter the sender's id : "))
        receiver_id = int(input("Enter the receiver's id : "))

        amount = int(input("Enter amount to be transfered : "))

        if amount <= 0 :
            print("Invalid amount.")
            return

        if sender_id == receiver_id :
            print("Sender and receiver cannot be the same .")
            return

        sender = None
        receiver = None

        for customer in data['customers']:
            if sender_id == customer['Customer ID']:
                sender = customer

        for customer in data['customers']:
            if receiver_id == customer['Customer ID']:
                receiver = customer
            
        if sender is None :
            print("Sender not Found")
            return

        if receiver is None :
            print("Receiver not Found")
            return

        if sender['Balance'] < amount :
            print("Insufficient Balance")
            return
        
        if sender.get("Status", "active").lower() != "active":
            print("Sender account is not active.")
            return

        if receiver.get("Status", "active").lower() != "active":
            print("Receiver account is not active.")
            return

        sender['Balance'] -= amount
        receiver['Balance'] += amount
       
        data["transaction"].append({

                    "Transaction ID": len(data["transaction"]) + 1,
                    "Type": "Transfer",
                    "Sender ID": sender_id,
                    "Receiver ID": receiver_id,
                    "Amount": amount,
                    "Date": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                                    })
        save()
        print("Money transferred sucessfully............")
        print("Sender's remaining balance:", sender["Balance"])

    def view_transcation_history(self):
        cust_id = int(input("Customer ID: "))
        found = False

        for transaction in data["transaction"]:
            if (
                transaction.get("Customer ID") == cust_id
                or transaction.get("Sender ID") == cust_id
                or transaction.get("Receiver ID") == cust_id
            ):
                print("-" * 35)
                for key, value in transaction.items():
                    print(f"{key}: {value}")
                found = True

        if not found:
            print("No transactions found.")

    def change_password(self):
        cust_id = int(input("Customer ID : "))
        new_password = input("Enter a new password : ")

        for customer in data['customers']:
            if customer['Customer ID'] == cust_id :
                customer['Password'] = new_password
                save()
                print("Password changed successfully ")
                return
        print("Customer not found !!")

    def exit(self):
        print("Thanks for using our services !!\nHave a nice day ")

class Admin :

    def view_dashboard(self):
        total_customers = len(data['customers'])

        active_customers = 0
        pending_customers = 0

        for customer in data['customers']:
            if customer['Status'].lower() == "active":
                active_customers+=1
            if customer['Status'].lower() == "pending":
                pending_customers+=1

        print("-------------------\n")
        print(f"Total customers = {total_customers}")
        print(f"Active customers = {active_customers}")
        print(f"Pending customers = {pending_customers}")
        print("-------------------\n")


    def view_all_accounts(self):

        if not data['customers']:
            print("No customer registered .")
            return
        
        for customer in data['customers']:
            print("Customer ID:", customer["Customer ID"])
            print("Name:", customer["Name"])
            print("Account No.:", customer["Account No."])
            print("Status:", customer["Status"])
        

    def search_customer(self):
        cust_id = int(input("Customer ID : "))
        for customer in data['customers']:
            if customer['Customer ID'] == cust_id :

                print("\nCustomer found!")
                print("Name:", customer["Name"])
                print("Account No.:", customer["Account No."])
                print("Balance:", customer["Balance"])
                print("Status:", customer["Status"])
                return
        print("Customer not found !!")

    def view_all_transactions(self):
        transactions = data.get("transaction", [])

        if not transactions:
            print("No transactions found.")
            return

        for transaction in transactions:
            print("-" * 35)
            for key, value in transaction.items():
                print(f"{key}: {value}")

    def approve_account(self):
        acc_no = int(input("Account No. : "))

        for customer in data['customers']:
            if customer['Account No.'] == acc_no :

                if customer['Status'].lower() == "pending":
                    customer['Status'] = "approve"
                    save()
                    print("Account approved successfully")
                else:
                    print("Account is not pending.")
                return
        print("Account not found")

    def update_account_status(self):
        acc_no = input("Enter account number: ")

        for customer in data["customers"]:
            if customer["Account No."] == acc_no:
                print("1. Activate")
                print("2. Freeze")
                choice = input("Choose an option: ")

                if choice == "1":
                    customer["Status"] = "active"
                elif choice == "2":
                    customer["Status"] = "frozen"
                else:
                    print("Invalid choice.")
                    return

                save()
                print("Account status updated.")
                return

        print("Account not found.")

    def logout(self):
        print("Admin logged out successfully.")

cust = Customer()
adm = Admin()

while True :
    print("---------------------- WELCOME TO CODING BANK OF INDIA ----------------------\n\n")
    print("1.Create Account")
    print("2.View profile")
    print("3.Withdraw money")
    print("4.Deposit money")
    print("5.Transfer money")
    print("6.View transcation history")
    print("7.Change password")
    print("8.View dashboard")
    print("9.View all accounts")
    print("10.Search customer")
    print("11.Freeze account")
    print("12.View all transcations")
    print("13.Approve account")
    print("14.Activate account")
    print("15.Logout")
    print("16.Exit")

    choice = int(input("Enter the choice = "))

    if choice == 1 :
        cust.create_account()
    elif choice == 2:
        cust.view_profile()
    elif choice == 3 :
        cust.withdraw()
    elif choice == 4:
        cust.deposit()
    elif choice == 5 :
        cust.transfer_money()
    elif choice == 6:
        cust.view_transcation_history()
    elif choice == 7:
        cust.change_password()
    elif choice == 8:
        adm.view_dashboard()
    elif choice == 9 :
        adm.view_all_accounts()
    elif choice == 10 :
        adm.search_customer()
    elif choice == 11 :
        adm.view_all_transactions()
    elif choice == 12 :
        adm.approve_account()
    elif choice == 13 :
        adm.update_account_status()
    elif choice == 14 :
        adm.logout()
        break
    elif choice == 15 :
        cust.exit()
        break
        
        
