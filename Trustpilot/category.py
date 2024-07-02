import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

# Path to your webdriver executable
webdriver_path = '/Users/sabbirahmad/Desktop/chromedriver'

# Set up the web driver (Make sure you have downloaded the appropriate web driver for your browser)
service = Service(webdriver_path)
options = Options()
driver = webdriver.Chrome(service=service, options=options)

# Open the Trustpilot categories page
driver.get('https://www.trustpilot.com/categories')

# List to store sub-categories
categories = []

# Locate all sub-categories on the page
sub_category_elements = driver.find_elements(By.XPATH, '//li[@class="styles_linkItem__KtBm6"]/a')

for sub_category_element in sub_category_elements:
    sub_category_name = sub_category_element.text
    categories.append(sub_category_name)

# Close the web driver
driver.quit()

# Format the output as {"Categories": []}
output = {"Categories": categories}

# Print the categories dictionary
print(json.dumps(output, indent=4))

# Optionally, save to a JSON file
with open('/Users/sabbirahmad/Trustpilot/categories.json', 'w') as json_file:
    json.dump(output, json_file, indent=4)
