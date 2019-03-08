AWS SSO CLI Scraper
Warning: This is my first python script. Use with caution.

This script uses Selenium to scrape the AWS SSO site for CLI credentials.

Example output:

$ python ascs.py -i
AWS SSO alias [None]: d-XXXXXXXXXX
Username [None]: jpecora716
Region [us-east-1]: 
Output [json]: 
Password: 
0: 123456789012 (Account 1)
1: 123456789013 (Account 2)
2: 123456789014 (Account 3)
3: 123456789015 (Account 4)
4: 123456789016 (Account 5)
Enter account: 3
0: Role_1
1: Role_2
Enter role: 1
Credentials have been written to the [sso] profile
Run the following command next time: ./ascs.py --alias d-XXXXXXXXXX --username jpecora716 --account 'Account 4' --role 'Role_2' --region us-east-1 --output json
