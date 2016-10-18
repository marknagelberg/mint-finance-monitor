import pandas as pd
import numpy as np
import csv

class TransactionData():
    exclude_from_calculations = ["Transfer", "Credit Card Payment"]
    remove_from_expenses_and_income = ["Business Expense", "Reimbursement", "Reimbursable", "Work Expense"]

    def __init__(self, transaction_data_filename):
        self.data = pd.read_csv(transaction_data_filename)
        self.data["Date"] = pd.to_datetime(self.data["Date"])
        self.data = self.data[~self.data["Category"].isin(TransactionData.exclude_from_calculations)]

    def after_tax_income(self):
        grouped = self.data.groupby("Transaction Type")
        total_credits =  grouped["Amount"].sum()['credit']
        return total_credits - self.subtract_from_expenses_and_income()

    def spending(self):
        grouped = self.data.groupby("Transaction Type")
        total_debits = grouped["Amount"].sum()['debit']
        return total_debits - self.subtract_from_expenses_and_income()

    def savings_rate(self):
        return 1 - (self.spending() / self.after_tax_income())

    def subtract_from_expenses_and_income(self):
        categories_to_remove = self.data[self.data["Category"].isin(TransactionData.remove_from_expenses_and_income)]["Amount"].sum()
        labels_to_remove = self.data[self.data["Labels"].isin(TransactionData.remove_from_expenses_and_income)]["Amount"].sum()
        return categories_to_remove + labels_to_remove

    def years_covered(self):
        years = [date.year for date in self.data["Date"]]
        years = list(set(years))
        years.sort()
        return years

    def filter_dates(self, begin_datetime = None, end_datetime = None, year = None, month = None):
        if begin_datetime:
            self.data = self.data[self.data["Date"] >= begin_datetime]
        if end_datetime:
            self.data = self.data[self.data["Date"] <= end_datetime]
        if year:
            self.data = self.data[self.data["Date"].dt.year == year]
        if month:
            self.data = self.data[self.data["Date"].dt.month == month]

if __name__ == "__main__":
    a = TransactionData("transactions.csv")
    print a.average_annual_spending()
