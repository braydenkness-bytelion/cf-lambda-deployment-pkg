import json
import boto3
import mail_notif
import slack_notif
import sec_scraper
import os

class Company:
    def __init__(self, name, link):
        self.name = name
        self.link = link

client = boto3.client('lambda')
distribution_mode = os.environ.get('MODE').upper()
debug_email = os.environ.get('DEBUG_EMAIL')

def lambda_handler(event, context):
    cols = ['date_scraped', 'date_filed', 'link', 'submission_type', 'filer_cik',
    'filer_ccc', 'file_number', 'override_internet_flag', 'name_of_issuer',
    'nature_of_amendment', 'legal_status_form', 'jurisdiction_organization',
    'date_incorporation', 'street1', 'street2', 'city', 'state_or_country',
    'zip_code', 'issuer_website', 'commission_cik', 'company_name',
    'commission_file_number', 'crd_number', 'compensation_amount',
    'financial_interest', 'security_offered_type', 'security_offered_other_desc',
    'no_of_security_offered', 'price', 'price_determination_method',
    'offering_amount', 'maximum_offering_amount', 'over_subscription_allocation_type',
    'deadline_date', 'current_employees', 'total_asset_most_recent_fiscal_year',
    'total_asset_prior_fiscal_year', 'cash_equi_most_recent_fiscal_year',
    'cash_equi_prior_fiscal_year', 'act_received_most_recent_fiscal_year',
    'act_received_prior_fiscal_year', 'short_term_debt_most_recent_fiscal_year',
    'short_term_debt_prior_fiscal_year', 'long_term_debt_most_recent_fiscal_year',
    'long_term_debt_prior_fiscal_year', 'revenue_most_recent_fiscal_year',
    'revenue_prior_fiscal_year', 'cost_goods_sold_most_recent_fiscal_year',
    'cost_goods_sold_prior_fiscal_year', 'tax_paid_most_recent_fiscal_year',
    'tax_paid_prior_fiscal_year', 'net_income_most_recent_fiscal_year',
    'created_at', 'updated_at', 'net_income_prior_fiscal_year']

    data = sec_scraper.scrape(cols)
    print(data)

    response = client.invoke(
        FunctionName='arn:aws:lambda:us-east-1:164558671925:function:cf-rds-access',
        InvocationType='RequestResponse',
        Payload=json.dumps(data))

    responseJson = json.load(response['Payload'])

    # Get Users from Database
    users = responseJson['users']

    # Get Filings from Database
    filings = responseJson['filings']

    # Send Email to User Distribution List
    if distribution_mode == 'DEBUG':
        # Debugging Mode
        mail_notif.send('Debug User', debug_email, filings)
    else:
        # Production Mode -- Default
        for user in users:
            mail_notif.send(user['name'], user['email'], filings)

    # TODO: Send Slack Notification

    return {
        'statusCode': 200,
        'body': responseJson
    }
