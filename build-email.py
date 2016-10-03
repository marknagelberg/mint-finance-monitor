from jinja2 import Environment, FileSystemLoader
import datetime
from transaction_analyzer import TransactionData

env = Environment(loader=FileSystemLoader('templates'))
template = env.get_template('email.html')

template_context = {}

all_time_transactions = TransactionData("transactions.csv")
template_context["all_time_after_tax_income"] = all_time_transactions.after_tax_income()
template_context["all_time_spending"] = all_time_transactions.spending()
template_context["all_time_savings_rate"] = all_time_transactions.savings_rate()

last_month_transactions = TransactionData("transactions.csv")
current_time = datetime.datetime.now()
last_month = current_time.month - 1
last_month_year = current_time.year
if last_month == 0:
    last_month = 12
    last_month_year = last_month_year - 1

last_month_transactions.filter_dates(begin_datetime = datetime.date(day = 1, month = last_month, year = last_month_year))

last_month_transactions = TransactionData("transactions.csv")
template_context["last_month_after_tax_income"] = last_month_transactions.after_tax_income()
template_context["last_month_spending"] = last_month_transactions.spending()
template_context["last_month_savings_rate"] = last_month_transactions.savings_rate()

print template.render(template_context)
