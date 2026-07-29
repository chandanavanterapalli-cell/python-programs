# Interest Calculator

principal = 1000
interest_per_day = 1

days = int(input("Enter number of days: "))

interest = interest_per_day * days
total_amount = principal + interest

print("Principal Amount :", principal)
print("Interest         :", interest)
print("Total Amount     :", total_amount)