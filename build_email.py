from jinja2 import Environment, FileSystemLoader
import datetime
from transaction_analyzer import TransactionData
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import json
import pandas as pd
import csv
import numpy as np

month_mapper = {1: "January",
                2: "February",
                3: "March",
                4: "April",
                5: "May",
                6: "June",
                7: "July",
                8: "August",
                9: "September",
                10: "October",
                11: "November",
                12: "December"}

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

    annual_savings_trend = []
    for year in all_time_transactions.years_covered():
        annual_transaction = TransactionData("transactions.csv")
        annual_transaction.filter_dates(year = year)
        annual_savings_trend.append((year, annual_transaction.savings_rate()))

    template_context["annual_savings_trend"] = annual_savings_trend

    last_month_transactions = TransactionData("transactions.csv")
    current_time = datetime.datetime.now()
    last_month = current_time.month - 1
    last_month_year = current_time.year
    if last_month == 0:
        last_month = 12
        last_month_year = last_month_year - 1


    last_month_transactions.filter_dates(year = last_month_year, month = last_month)

    template_context["last_month_name"] = month_mapper[last_month]

    template_context["last_month_after_tax_income"] = last_month_transactions.after_tax_income()
    template_context["last_month_spending"] = last_month_transactions.spending()
    template_context["last_month_savings_rate"] = last_month_transactions.savings_rate()
    template_context["last_month_net_worth_required_for_fi"] = template_context["last_month_spending"] * 12 * 25


    top_10_last_month_spending_categories = []
    for idx, value in last_month_transactions.top_n_spending_categories(n=10).iteritems():
        top_10_last_month_spending_categories.append((idx, value))

    template_context["top_10_last_month_spending_categories"] = top_10_last_month_spending_categories

    #Hard code the year you began working
    template_context["year_work_began"] = 2011

    net_worth_data = pd.read_csv('trends.csv')
    current_net_worth = net_worth_data[-1:]["Net"].str.replace("$","").str.replace(",","").astype(float)
    current_net_worth =  current_net_worth.values[0]

    template_context["current_net_worth"] = current_net_worth

    template_context["current_safe_withdrawal_amount"] = current_net_worth * .04

    annual_spending_trend = []
    for year in all_time_transactions.years_covered():
        annual_transaction = TransactionData("transactions.csv")
        annual_transaction.filter_dates(year = year)
        annual_spending_trend.append((year, annual_transaction.spending()))
    template_context["annual_spending_trend"] = annual_spending_trend

    average_annual_spending = np.mean([x[1] for x in annual_spending_trend])
    template_context["average_annual_spending"] = average_annual_spending
    template_context["all_time_net_worth_required_for_fi"] = average_annual_spending * 25


    top_10_all_time_spending_categories = []
    for idx, value in all_time_transactions.top_n_spending_categories(n=10).iteritems():
        top_10_all_time_spending_categories.append((idx, value))

    template_context["top_10_all_time_spending_categories"] = top_10_all_time_spending_categories

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
