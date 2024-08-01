import json
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
# Setup logging

# Load environment variables from .env file
load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

# Path to your webdriver executable
webdriver_path = os.getenv("WEBDRIVER_PATH")
# Set up the web driver
service = Service(webdriver_path)
options = Options()
driver = webdriver.Chrome(service=service, options=options)

# Open the Yellow Pages page
driver.get('https://www.yellowpages.com/new-germany-mn/barbers')

# Wait until the elements are present
wait = WebDriverWait(driver, 4)
wait.until(EC.presence_of_all_elements_located((By.XPATH, '//div[@class="show-browse-menu"]//div[@class="category-links"]/a')))

# List to store sub-categories
categories = []

# Locate all sub-categories on the page
sub_category_elements = driver.find_elements(By.XPATH, '//div[@class="show-browse-menu"]//div[@class="category-links"]/a')

# Log the number of elements found
logger.info(f"Found {len(sub_category_elements)} sub-category elements.")

for sub_category_element in sub_category_elements:
    sub_category_name = sub_category_element.get_attribute('textContent').strip()  # Using JavaScript to get the text
    if sub_category_name:  # Only append non-empty names
        categories.append(sub_category_name)
    else:
        logger.warning("Found an empty sub-category name.")

# Close the web driver
driver.quit()

# Format the output as {"Categories": []}
output = {"Categories": categories}

# Print the categories dictionary
print(json.dumps(output, indent=4))

# Optionally, save to a JSON file
with open('CATEGORY_JSON_PATH_yellowpage', 'w') as json_file:
    json.dump(output, json_file, indent=4)
