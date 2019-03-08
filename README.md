AWS SSO CLI Scraper<br>
Warning: This is my first python script. Use with caution.<br>
<br>
This script uses Selenium to scrape the AWS SSO site for CLI credentials.<br>
<br>
Example output:<br>
<br>
$ python ascs.py -i<br>
AWS SSO alias [None]: d-XXXXXXXXXX<br>
Username [None]: jpecora716<br>
Region [us-east-1]:<br>
Output [json]:<br>
Password:<br>
0: 123456789012 (Account 1)<br>
1: 123456789013 (Account 2)<br>
2: 123456789014 (Account 3)<br>
3: 123456789015 (Account 4)<br>
4: 123456789016 (Account 5)<br>
Enter account: 3<br>
0: Role_1<br>
1: Role_2<br>
Enter role: 1<br>
Credentials have been written to the [sso] profile<br>
Run the following command next time: ./ascs.py --alias d-XXXXXXXXXX --username jpecora716 --account 'Account 4' --role 'Role_2' --region us-east-1 --output json<br>
