from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from bs4 import BeautifulSoup
import getpass
import os
import time
import configparser
import argparse

#TO DO: check if chromedriver exists in path, otherwise check current directory. if it doesn't exist in either location, fail.

parser = argparse.ArgumentParser()
parser.add_argument('--interactive', '-i', action='store_true', help='Assume Role interactively')
parser.add_argument('--alias', help='AWS SSO Account Alias')
parser.add_argument('--region', default='us-east-1', help='AWS Region')
parser.add_argument('--output', default='json', help='Output text type. Typically json or text')
parser.add_argument('--account', help="Account number")
parser.add_argument('--role', help="Role to assume")
parser.add_argument('--username', help="Username")
parser.add_argument('--list', action='store_true', help="List accounts and roles that can be assumed")
args = parser.parse_args()

def check_element(element_id, driver):
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

    config = configparser.ConfigParser()
    config.read(awscredsfile)
    with open(awscredsfile, 'r+') as configfile:
        config.remove_section('sso')
        config['sso'] = aws_creds
        config.write(configfile)

def main(args):
    # How long should we wait to check for fields?
    wait = 15
    aws_alias = args.alias
    username = args.username
    region = args.region
    output = args.output
    account = args.account
    role = args.role
    # Prompt for information that wasn't passed as an argument or if interactive is true
    if args.interactive or not aws_alias:
        aws_alias = input(f'AWS SSO alias [{aws_alias}]: ')
    if args.interactive or not username:
        username = input(f'Username [{username}]: ')

    password = getpass.getpass()

    if args.interactive or not region:
        region = input(f'Region [{region}]: ')
    if args.interactive or not output:
        output = input(f'Output [{output}]: ')

    #driver = webdriver.Chrome('')  # Optional argument, if not specified will search path.
    options = webdriver.ChromeOptions()
    options.add_argument('headless')
    #options.binary_location = 
    driver = webdriver.Chrome('/usr/lib/chromium-browser/chromedriver', chrome_options=options)
    driver.get(f"https://{aws_alias}.awsapps.com/start#/")

    #Check for username and password fields before sending keys
    login_box = check_element('wdc_username', driver)
    password_box = check_element('wdc_password', driver)
    login_box.send_keys(username)
    password_box.send_keys(password)

    signin_button = check_element('wdc_login_button', driver)
    signin_button.click()
    
    # Wait for SSO Applications to load before sending to bs4
    try:
        signin_button = WebDriverWait(driver, wait).until(
        lambda x: x.find_element_by_tag_name('portal-application')
        )
    except TimeoutException:
        print("Timeout waiting for portal applications")
        driver.quit()

    time.sleep(1)
    soup = BeautifulSoup(driver.page_source, 'lxml')

    # Search through all badges for any named AWS Account
    for i in (soup.find_all('portal-application')):
        if i.text.find('AWS Account'):
            awsappid = i['id']
        else:
            print("There doesn't appear to be any AWS Accounts!")
            driver.quit()

    aws_account = check_element(awsappid, driver)
    aws_account.click()

    #Wait for the AWS Accounts to load
    try:
        WebDriverWait(driver, wait).until(
            lambda x: x.find_element_by_tag_name('portal-instance')
        )
    except TimeoutException:
        print("Timeout waiting for the AWS Accounts to load")
        driver.quit()
    
    time.sleep(1)

    soup = BeautifulSoup(driver.page_source, 'lxml')

    count = 0
    accountid = []
    for i in (soup.find_all('portal-instance')):
        print(f"{count}: {i.text.strip()}")
        accountid.append(i['id'])
        count += 1

    if args.interactive == True:
        get_accountid = int(input("Enter account: "))
    aws_account_role = check_element(accountid[get_accountid], driver)

    aws_account_role.click()
    time.sleep(3)

    soup = BeautifulSoup(driver.page_source, 'lxml')

    count = 0
    roles = []
    for j in (soup.find_all('portal-profile')):
        print(f"{count}: {j.find('span', {'class': 'profileName'}).text}")
        roles.append(j)
        count += 1

    # Prompt for which role to be assumed here
    get_role = int(input("Get role: "))

    try:
        aws_roles = WebDriverWait(driver, wait).until(
            lambda x: x.find_elements_by_link_text('Command line or programmatic access')
        )
    except TimeoutException:
        print("Timeout waiting for account roles")
        driver.quit()

    aws_roles[get_role].click()

    try:
        aws_access_key_id = WebDriverWait(driver, wait).until(
            lambda x: x.find_element_by_id('accessKeyId')
        )
        aws_secret_access_key = WebDriverWait(driver, wait).until(
            lambda x: x.find_element_by_id('secretAccessKey')
        )
        aws_session_token = WebDriverWait(driver, wait).until(
            lambda x: x.find_element_by_id('sessionToken')
        )
    except TimeoutException:
        print("Timeout waiting for credentials")
        driver.quit()

    soup = BeautifulSoup(driver.page_source, 'lxml')
    codelines = soup.find_all('div', {'class': 'code-line'})

    #Generate dict to pass to credentials file
    aws_creds_dict = {'region': region, 'output': output}
    for i in codelines[-3:]:
        aws_creds_dict[i.getText().split('=')[0].strip()] = i.getText().split('=')[1].strip()

    write_aws_creds(aws_creds_dict)

    driver.quit()

main(args)