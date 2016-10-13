from jinja2 import Environment, FileSystemLoader
import datetime
from transaction_analyzer import TransactionData
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import json

def currency_filter(value):
    return "${:,.0f}".format(value)

def percentage_filter(value):
    return "{:.0%}".format(value)

def years_to_fi_filter(savings_rate):
    """Calculates total # working years to reach FI given savings rate.
       Assumes 4% withdrawal rate and 5% return on savings during saving years."""
    income = 1
    year = 0
    net_worth = 0

    while net_worth * .04  < income * (1 - savings_rate):
        net_worth = net_worth * 1.05 + income * savings_rate
        year += 1

    return year




if __name__ == '__main__':
    env = Environment(loader=FileSystemLoader('templates'))

    env.filters['currency_filter'] = currency_filter
    env.filters['percentage_filter'] = percentage_filter
    env.filters['years_to_fi_filter'] = years_to_fi_filter

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

    template_context["last_month_after_tax_income"] = last_month_transactions.after_tax_income()
    template_context["last_month_spending"] = last_month_transactions.spending()
    template_context["last_month_savings_rate"] = last_month_transactions.savings_rate()

    html  =  template.render(template_context)

    email_info = json.load(open('emails.json'))
    sender = email_info["sender"]
    receivers = email_info["receivers"]

    for receiver in receivers:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = "Mint Financial Independence Report"
        msg['From'] = sender
        msg['To'] = receiver
        msg.attach(MIMEText(html, 'html'))

        s = smtplib.SMTP_SSL(host = 'smtp.gmail.com', port = 465)
        email_login_info = json.load(open('email_user_pass.json'))
        s.login(user = email_login_info['username'], password = email_login_info['password'])

        s.sendmail(sender, receiver, msg.as_string())

        s.quit()
