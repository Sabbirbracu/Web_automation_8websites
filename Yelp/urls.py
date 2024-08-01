import csv
import json
import subprocess
import sys
import time
import urllib.parse
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os

logger = logging.getLogger()

# Path to your webdriver executable
webdriver_path = os.getenv("WEBDRIVER_PATH")

# Function to generate the Yelp search URL
def generate_yelp_url(category, location):
    base_url = 'https://www.yelp.com/search'
    params = {
        'find_desc': category,
        'find_loc': location
    }
    return f"{base_url}?{urllib.parse.urlencode(params)}"

# Function to check if pagination element is present and visible
def is_pagination_visible(driver):
    try:
        pagination = driver.find_element(By.XPATH, '//div[@aria-label="Pagination navigation"]')
        return pagination.is_displayed()
    except:
        return False

# Function to check if pagination button is interactable
def is_pagination_button_interactable(driver):
    try:
        pagination_button = driver.find_element(By.XPATH, "//*/li/div[@aria-label='Pagination navigation']//button")
        return pagination_button.is_enabled()
    except:
        return False

# Function to extract business links and names from the current page
def extract_business_links_and_names(driver, business_dict):
    try:
        business_elements = driver.find_elements(By.XPATH,
            "//div[contains(@class, 'container__09f24__FeTO6') and contains(@class, 'hoverable__09f24___UXLO') and "
            "contains(@class, 'y-css-xvvvfw') or contains(@class,'y-css-way87j')]")
        
        for business in business_elements:
            try:
                link_element = business.find_element(By.XPATH, './/h3[@class="y-css-hcgwj4"]/a[@class="y-css-12ly5yx"]')
                name = (link_element.text).strip()
                link = link_element.get_attribute('href')
                
                if name not in business_dict:
                    business_dict[name] = link
            except Exception as e:
                print(f"Error extracting name and link: {e}")
                continue
        
        print(f"Extracted {len(business_dict)} unique business names and links so far.")
    except Exception as e:
        print(f"Error extracting business data: {e}")

# Main script to handle pagination and data extraction
def main(driver, category, location, source, source_name):
    url = generate_yelp_url(category, location)
    driver.get(url)
    
    wait = WebDriverWait(driver, 4)
    try:
        wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="main-content"]')))
        print("Main content loaded.")
    except Exception as e:
        print(f"Error waiting for main content to load: {e}")
        driver.quit()
        exit()
    
    all_business_data = {}
    while True:
        extract_business_links_and_names(driver, all_business_data)
        print(f"So far total unique items: {len(all_business_data)}")
        
        if is_pagination_visible(driver) and is_pagination_button_interactable(driver):
            print("Pagination button found and interactable. Clicking it.")
            try:
                try:
                    accept_cookies_button = driver.find_element(By.ID, 'onetrust-accept-btn-handler')
                    if accept_cookies_button.is_displayed():
                        accept_cookies_button.click()
                        time.sleep(2)
                        print("Closed cookie consent banner.")
                except:
                    pass
                
                pagination_button = driver.find_element(By.XPATH, "//*/li/div[@aria-label='Pagination navigation']//button")
                driver.execute_script("arguments[0].scrollIntoView();", pagination_button)
                driver.execute_script("arguments[0].click();", pagination_button)
                time.sleep(1)
            except Exception as e:
                print(f"Error clicking pagination button: {e}")
                break
        else:
            print("Pagination button not found or not interactable. Stopping pagination.")
            break
    
    all_business_data_list = list(all_business_data.items())
    print(f"Total unique business items extracted: {len(all_business_data_list)}")
    
    csv_file_path = os.getenv("CSV_FILE_PATH_yelp")  # Assuming this returns a valid path as a string
    file_name = "example sub category"

    # Replace spaces with underscores in file_name
    sub_category_sanitized = file_name.replace(' ', '_')

    # Join the paths
    full_path = os.path.join(csv_file_path, f"{sub_category_sanitized}.csv")
    
    # Save the links and names to a CSV file
    csv_file_path = full_path
    
    try:
        with open(csv_file_path, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['Business Name', 'Business Link'])
            for name, link in all_business_data_list:
                writer.writerow([name, link])
        print(f"Links and names successfully saved to {csv_file_path}")
    except Exception as e:
        print(f"Error saving links and names to CSV: {e}")
    
    driver.quit()
    
    python_executable = sys.executable
    try:
        subprocess.run([python_executable, os.getenv("DETAIL_PATH_yelp"), csv_file_path, source_name, source, category], check=True)
        print(f"details.py executed successfully with {csv_file_path}")
    except subprocess.CalledProcessError as e:
        print(f"Error calling details.py: {e}")

# Load categories from the category.json file and process each one

json_file_path = os.getenv("CATEGORY_JSON_PATH_yelp")

# Read categories from JSON file
with open(json_file_path, 'r') as json_file:
    data = json.load(json_file)
    categories = data.get("Categories", [])

location = 'Germany'
source = 'https://www.yelp.com'
source_name = "Yelp"

chrome_options = Options()
chrome_options.add_argument("--headless")  # Run Chrome in headless mode
service = Service(webdriver_path)
driver = webdriver.Chrome(service=service, options=chrome_options)

for category in categories:
    print(f"Processing category: {category}")
    main(driver, category, location, source, source_name)
