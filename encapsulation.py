class Account:
    def __init__(self,balance):
        self.balance=balance
    def get_balance(self):
        return self.balance
acc=Account(5000)
print(acc.get_balance())