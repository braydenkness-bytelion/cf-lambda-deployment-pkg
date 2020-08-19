from jinja2 import Environment, FileSystemLoader
import smtplib
from email.message import EmailMessage
from datetime import datetime, timedelta
import os
import states
import re

def format_currency(value):
    if value == None:
        return "N/A"
    else:
        return "${:,.2f}".format(value);

def format_number(value):
    if value == None:
        return "N/A"
    else:
        return "{:,.0f}".format(value)

def format_url(value):
    if value == None:
        return ''
    else:
        domain = re.sub('^http[s]?://', '', re.sub('www\.', '', value))
        return 'www.' + domain

def send(name, email, companies):
    # Load Environment Variables
    _email = os.environ.get('CF_EMAIL')
    _password = os.environ.get('CF_PASS')
    _url = os.environ.get('CF_URL')
    _company = os.environ.get('CF_COMP')
    _subject = os.environ.get('CF_SUBJ')

    # Get Filing Date
    today = datetime.today()
    if today.weekday() == 0: # Monday
        # Get Fridays Date
        filing_date = today - timedelta(days = 3)
    else:
        # Get Yesterday
        filing_date = today - timedelta(days = 1)

    # Get Template
    templateLoader = FileSystemLoader(searchpath="./templates/")
    templateEnv = Environment(loader=templateLoader)

    # Format Currency | 123456 => $123,456.00
    templateEnv.filters['format_currency'] = format_currency
    templateEnv.filters['format_number'] = format_number
    templateEnv.filters['get_state_name'] = states.get_name
    templateEnv.filters['format_url'] = format_url

    template = templateEnv.get_template('index.html')
    email_body = template.render(receiver = name, sender = _company,
        filings = companies, date = filing_date.strftime('%A, %B %-d, %Y'))

    # Format Subject
    date_string = filing_date.strftime('%B %-d, %Y')
    full_subject = '{} | {}'.format(_subject, date_string)

    # Generate and Send Email
    msg = EmailMessage()
    msg['From'] = '{} <{}>'.format(_company, _email)
    msg['To'] = email
    msg['Subject'] = full_subject
    msg.set_content("Uh Oh... HTML Did Not Load Correctly.")
    msg.add_alternative(email_body, subtype='html')

    # Send Email
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(_email, _password)
        smtp.send_message(msg)
