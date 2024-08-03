import json
import logging
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()


webdriver_path = os.getenv("WEBDRIVER_PATH")


service = Service(webdriver_path)
options = Options()
options.add_argument("--headless")
driver = webdriver.Chrome(service=service, options=options)

driver.get('https://www.yelp.com/')

wait = WebDriverWait(driver, 4)  # Increased wait time
wait.until(EC.visibility_of_all_elements_located((By.XPATH, '//nav[@aria-label="Business categories"]')))
logging.info("Header section is loaded")

categories = []

sub_category_elements = driver.find_elements(By.XPATH, '//ul[@class="header-dropdown-col__09f24__yr1XA y-css-1iy1dwt"]//a[@role="menuitem"]/div/div/div[2]/span[@class = "y-css-15epot"]')
logger.info(f"Found {len(sub_category_elements)} sub-category elements.")
time.sleep(1)

for sub_category_element in sub_category_elements:
    sub_category_name = driver.execute_script("return arguments[0].textContent;", sub_category_element).strip()
    logging.info(sub_category_name)
    if sub_category_name:
        categories.append(sub_category_name)
    else:
        logger.warning("Found an empty sub-category name.")

driver.quit()
output = {"Categories": categories}
logging.info(json.dumps(output, indent=4))

with open(os.getenv("CATEGORY_JSON_PATH_yelp"), 'w') as json_file:
    json.dump(output, json_file, indent=4)
