import smtplib, os
from dotenv import load_dotenv
load_dotenv()

server = smtplib.SMTP('smtp.gmail.com', 587)
server.ehlo()
server.starttls()
server.ehlo()
server.login(os.getenv('EMAIL_FROM'), os.getenv('EMAIL_PASSWORD'))
server.sendmail(os.getenv('EMAIL_FROM'), os.getenv('EMAIL_TO'), 'Subject: Test\n\nTest email')
server.quit()
print('Sent!')
