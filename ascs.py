from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from bs4 import BeautifulSoup
from re import findall
import getpass
import os
import time
import configparser
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--interactive', '-i', action='store_true', help='Assume Role interactively')
parser.add_argument('--alias', help='AWS SSO Account Alias')
parser.add_argument('--username', help="Username")
parser.add_argument('--region', default='us-east-1', help='AWS Region')
parser.add_argument('--output', default='json', help='Output text type. Typically json or text')
parser.add_argument('--account', help="Account number")
parser.add_argument('--role', help="Role to assume")
parser.add_argument('--list', action='store_true', help="List accounts and roles that can be assumed")
args = parser.parse_args()

def find_chromedriver():
    pass

def check_element_id(element_id, driver):
    wait = 15
    try:
        element = WebDriverWait(driver, wait).until(
            lambda x: x.find_element_by_id(element_id)
        )
        time.sleep(1)
        return element
    except TimeoutException:
        print(f"Timeout waiting for {element} field")
        driver.quit()

def write_aws_creds(aws_creds):
    awsdir = os.path.expanduser('~/.aws')
    awscredsfile = awsdir + '/credentials'
    if not os.path.isdir(awsdir):
        os.mkdir(awsdir, 0o700)
    if not os.path.isfile(awscredsfile):
        open(awscredsfile, 'a').close()

    config = configparser.ConfigParser()
    config.read(awscredsfile)
    with open(awscredsfile, 'r+') as configfile:
        config.remove_section('sso')
        config['sso'] = aws_creds
        config.write(configfile)
    print("Credentials have been written to the [sso] profile")

def main(args):
    # Max time in seconds to wait for javascript to populate
    wait = 15
    aws_alias = args.alias
    username = args.username
    region = args.region
    output = args.output
    account = args.account
    role = args.role
    # Prompt for information that wasn't passed as an arg or if interactive is true
    if args.interactive or not aws_alias:
        aws_alias = input(f'AWS SSO alias [{aws_alias}]: ') or aws_alias
    if args.interactive or not username:
        username = input(f'Username [{username}]: ') or username
    if args.interactive or not region:
        region = input(f'Region [{region}]: ') or region
    if args.interactive or not output:
        output = input(f'Output [{output}]: ') or output

    password = getpass.getpass()

    options = webdriver.ChromeOptions()
    options.add_argument('headless')
    driver = webdriver.Chrome('/usr/lib/chromium-browser/chromedriver', chrome_options=options)
    driver.get(f"https://{aws_alias}.awsapps.com/start#/")

    #Check for username and password fields before sending keys
    sel_login_box = check_element_id('wdc_username', driver)
    sel_password_box = check_element_id('wdc_password', driver)
    sel_login_box.send_keys(username)
    sel_password_box.send_keys(password)

    sel_signin_button = check_element_id('wdc_login_button', driver)
    sel_signin_button.click()
    
    # Wait for SSO Applications to load before sending to bs4
    try:
        sel_signin_button = WebDriverWait(driver, wait).until(
        lambda x: x.find_element_by_tag_name('portal-application')
        )
    except TimeoutException:
        print("Timeout waiting for portal applications")
        driver.quit()

    # Improve this...
    time.sleep(3)
    soup = BeautifulSoup(driver.page_source, 'lxml')

    # Search through all badges for any named AWS Account
    for i in (soup.find_all('portal-application')):
        if i.text.find('AWS Account'):
            sel_awsappid = i['id']
        else:
            print("There doesn't appear to be any AWS Accounts!")
            driver.quit()
            exit()

    sel_aws_account = check_element_id(sel_awsappid, driver)
    sel_aws_account.click()

    #Wait for the AWS Accounts to load
    try:
        WebDriverWait(driver, wait).until(
            lambda x: x.find_element_by_tag_name('portal-instance')
        )
    except TimeoutException:
        print("Timeout waiting for the AWS Accounts to load")
        driver.quit()
    
    # Improve this...
    time.sleep(3)

    soup = BeautifulSoup(driver.page_source, 'lxml')

    sel_accountids = []
    accountinfo = []
    accountnames = []
    for i in (soup.find_all('portal-instance')):
        sel_accountids.append(i['id'])
        # Remove account number before adding to accountnames
        find_accountname = findall("\(.*\)", i.text.strip())
        accountnames.append(find_accountname[0][1:-1])
        # Get the account number and name to loop through if
        # in interactive or account not passed as argv
        accountinfo.append(i.text.strip())

    if args.interactive == True or not account:
        count = 0
        for i in (accountinfo):
            print(f"{count}: {i}")
            count += 1
        get_accountid = int(input(f"Enter account: "))
        account = accountnames[get_accountid]
    elif account in accountnames:
        get_accountid = accountnames.index(account)
    else:
        print(f"{account} not found in {accountnames}")
        driver.quit()
        exit()
    
    sel_aws_account_role = check_element_id(sel_accountids[get_accountid], driver)

    sel_aws_account_role.click()
    # Can this be sped up with check_element_id?
    time.sleep(3)

    soup = BeautifulSoup(driver.page_source, 'lxml')

    roles = []
    rolenames = []
    for j in (soup.find_all('portal-profile')):
        rolenames.append(j.find('span', {'class': 'profileName'}).text.strip())
        roles.append(j)

    # Prompt for which role to be assumed here
    # This is shit. Fix all of this and accounts above for proper error checking
    if args.interactive == True or not role:
        count = 0
        for i in (rolenames):
            print(f"{count}: {i}")
            count += 1
        get_role = int(input("Enter role: "))
        role = rolenames[get_role]
    elif role in rolenames:
        get_role = rolenames.index(role)
    else:
        print(f"{role} not found in {rolenames}")
        driver.quit()
        exit()

    try:
        sel_aws_roles = WebDriverWait(driver, wait).until(
            lambda x: x.find_elements_by_link_text('Command line or programmatic access')
        )
    except TimeoutException:
        print("Timeout waiting for account roles")
        driver.quit()

    sel_aws_roles[get_role].click()

    # Check for aws credentials before scraping them - this might be overkill
    try:
        sel_aws_access_key_id = WebDriverWait(driver, wait).until(
            lambda x: x.find_element_by_id('accessKeyId')
        )
        sel_aws_secret_access_key = WebDriverWait(driver, wait).until(
            lambda x: x.find_element_by_id('secretAccessKey')
        )
        sel_aws_session_token = WebDriverWait(driver, wait).until(
            lambda x: x.find_element_by_id('sessionToken')
        )
    except TimeoutException:
        print("Timeout waiting for credentials")
        driver.quit()
        exit()

    soup = BeautifulSoup(driver.page_source, 'lxml')
    codelines = soup.find_all('div', {'class': 'code-line'})

    #Generate dict to pass to credentials file
    aws_creds_dict = {'region': region, 'output': output}
    for i in codelines[-3:]:
        # Convert string to raw to prevent python from interpreting special characters
        raw_string = r'{}'.format(i.getText().split('=')[1].strip())
        aws_creds_dict[i.getText().split('=')[0].strip()] = raw_string

    write_aws_creds(aws_creds_dict)

    driver.quit()
    if (args.interactive):
        print(f"Run the following command next time: ./ascs.py --alias {aws_alias}"
        f" --username {username} --account '{account}'" 
        f" --role '{role}' --region {region} --output {output}")
    exit()

main(args)