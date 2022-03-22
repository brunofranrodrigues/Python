import time
import yaml
from selenium import webdriver
from selenium.webdriver.common.by import By
# Function for open yaml file and loader
def read_config(path):
    with open(path, "r") as stream:
        return yaml.FullLoader(stream).get_data()

# Read yaml file and load email and password
config = read_config("/home/sysadmin/PycharmProjects/SMAX-URL/loginDetails.yml")
user = config['smax_user']['email']
passwd = config['smax_user']['password']
browser = webdriver.Chrome("/home/sysadmin/PycharmProjects/SMAX-URL/chromedriver")
#URL
browser.get("https://smax-qa.compassouol.com/saw/ess?TENANTID=372102201")
# 5 seconds
time.sleep(5)
username = browser.find_element(By.ID, 'username')
# Send user
username.send_keys(user)
# click next button
browser.find_element(By.ID, 'next').click()
# 5 seconds
time.sleep(5)
password = browser.find_element(By.ID, 'password')
# Send password
password.send_keys(passwd)
# click submit button
browser.find_element(By.ID, 'submit').click()