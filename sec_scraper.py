import requests
import copy
from bs4 import BeautifulSoup
import re
from datetime import datetime
from datetime import timedelta

# Helper -- String to PostgreSQL Date Object
def format_date(date):
    return "to_date('{}', 'YYYY-MM-DD')".format(date.strftime("%Y-%m-%d"))

# Main Scrape Function
def scrape(original_columns):

    all_data = []

    # Establish variables
    var_names = ["submissionType","filerCik","filerCcc","fileNumber","overrideInternetFlag",\
            "nameOfIssuer","natureOfAmendment","legalStatusForm","jurisdictionOrganization","dateIncorporation","com:street1",\
            "com:street2","com:city","com:stateOrCountry","com:zipCode","issuerWebsite","commissionCik","companyName",\
            "commissionFileNumber","crdNumber","compensationAmount","financialInterest","securityOfferedType","securityOfferedOtherDesc",\
            "noOfSecurityOffered","price","priceDeterminationMethod","offeringAmount","maximumOfferingAmount",\
            "overSubscriptionAllocationType","deadlineDate","currentEmployees","totalAssetMostRecentFiscalYear",\
            "totalAssetPriorFiscalYear","cashEquiMostRecentFiscalYear","cashEquiPriorFiscalYear","actReceivedMostRecentFiscalYear",\
            "actReceivedPriorFiscalYear","shortTermDebtMostRecentFiscalYear","shortTermDebtPriorFiscalYear",\
            "longTermDebtMostRecentFiscalYear","longTermDebtPriorFiscalYear","revenueMostRecentFiscalYear","revenuePriorFiscalYear",\
            "costGoodsSoldMostRecentFiscalYear","costGoodsSoldPriorFiscalYear","taxPaidMostRecentFiscalYear","taxPaidPriorFiscalYear",\
            "netIncomeMostRecentFiscalYear","netIncomePriorFiscalYear"]

    top = "Date Scraped,Date Filed,Link,Type of Offering,Filer CIK,Filer CCC,File Number,Notify via Filing Website only?,Name of Issuer,Describe the Nature of the Amendment,Form,Jurisdiction of Incorporation/ Organization,Date of Incorporation/ Organization,Address 1,Address 2,City,State/Country,Mailing Zip/Postal Code,Website of Issuer,CIK,Company Name,Commission File Number,CRD Number,Amount of compensation to be paid to the intermediary whether as a dollar amount of a percentage of the offering amount or a good faith estimate if the exact amount is not available at the time of the filing for conducting the offers including the amount of referral and any other fees associated with the offering:,Any other financial interest in the issuer held by the intermediary or any arrangement for the intermediary to acquire such an interest:,Type of Security Offered:,Specify,Target Number of Securities to be Offered:, Price,Price (or Method for determining price),Target offering Amount,Maximum Offering Amount (if different from Target Offering Amount) - Oversubscriptions Accepted:,If yes disclose how oversubscriptions will be allocated:,Deadline to reach the Target Offering Amount:,Current Number of Employees,Total Assets Most Recent Fiscal Year-end,Total Assets Prior Fiscal Year-end,Cash and Cash equivalents Most Recent Fiscal Year-end,Cash and Cash Equivalents Prior Fiscal Year-end,Accounts Receivable Most Recent Fiscal Year-end,Accounts Receivable Prior Fiscal Year-end,Short-term Debt Most Recent Fiscal Year-end,Short-term Debt Prior Fiscal Year-end,Long-term Debt Most Recent Fiscal Year-end,Long-term Debt Prior Fiscal Year-end,Revenue/Sales Most Recent Fiscal Year-end,Revenue/Sales Prior Fiscal Year-end,Cost of Goods Sold Most Recent Fiscal Year-end,Cost of Goods Sold Prior Fiscal Year-end,Taxes Paid Most Recent Fiscal Year-end,Taxes Paid Prior Fiscal Year-end,Net Income Most Recent Fiscal Year-end,Net Income Prior Fiscal Year-end"

    search = ["C","C/A"]
    today = datetime.today()

    # Handle Monday's
    if today.weekday() == 0:
        # Get Fridays Date
        yesterday = today - timedelta(days = 3)
    else:
        # Get Yesterday
        yesterday = today - timedelta(days = 1)

    links = []

    # Collect yesterday links
    rss = requests.get("https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=C&&count=100&output=atom").content
    sec_soup = BeautifulSoup(rss,"lxml")
    entries = sec_soup.find_all("entry")
    for entry in entries:
        date = str(entry.find("summary")).split()[3]
        date = datetime.strptime(date, "%Y-%m-%d")
        if(entry.find("category")["term"] in search) and (date.date() == yesterday.date()):
            links.append(entry.find("link")["href"])

    # Reconstruct links
    for num in range(len(links)):
        link = links[num]
        link = link.split("/")
        link[-1] = "primary_doc.xml"
        link = "/".join(link)
        links[num] = link

    # Get data
    input = ""
    for link in links:

        cols = copy.deepcopy(original_columns)
        print('Cols: {}'.format(cols))
        print('OG Cols: {}'.format(original_columns))

        # Data Dictionary
        data_dict = {}

        xml = requests.get(link).content
        xml_soup = BeautifulSoup(xml,"xml")

        # Get html link
        html_link = link.split("/")
        html_link[-1] = "xslC_X01/primary_doc.xml"
        html_link = "/".join(html_link)

        # Append extra data
        data_dict[cols.pop(0)] = format_date(today)
        data_dict[cols.pop(0)] = format_date(yesterday)
        data_dict[cols.pop(0)] = "'{}'".format(html_link)
        print('Link: {}\n\n'.format(html_link))

        # Run through data
        for i in var_names:
            key = cols.pop(0)
            while key == 'created_at' or key == 'updated_at':
                data_dict[key] = format_date(today)
                key = cols.pop(0)

            try:
                data = xml_soup.find(i).string
                print(i + " done!")
            except:
                data = None
                print(i + " not found...")

            # Write data
            try:
                if data != None:
                    # Add to data Dictionary
                    final_entry = re.sub("\n","",re.sub(",", "", re.sub("'", "", data)))
                    data_dict[key] = "'{}'".format(final_entry)
            except:
                print("ERROR: Invalid xml. Skipping previous data field.")

        print("")
        all_data.append(data_dict)

    # Return list of dictionaries
    return all_data
