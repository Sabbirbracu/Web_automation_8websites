import csv
import time
import subprocess
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import urllib.parse
import sys
import logging
import os

# Path to your webdriver executable
webdriver_path = os.getenv("WEBDRIVER_PATH")

# Function to generate the YellowPages search URL
def generate_yellowpages_url(category, location):
    base_url = 'https://www.yellowpages.com/search'
    params = {
        'search_terms': category,
        'geo_location_terms': location
    }
    return f"{base_url}?{urllib.parse.urlencode(params)}"
    
json_file_path = os.getenv("CATEGORY_JSON_PATH_yellowpage")

# Read categories from JSON file
with open(json_file_path, 'r') as json_file:
    data = json.load(json_file)
    categories = data.get("Categories", [])

# Initialize Chrome web driver with existing user profile
chrome_options = Options()
chrome_options.add_argument("--headless")  # Optional: Run Chrome in headless mode, i.e., without a UI
service = Service(webdriver_path)

# Function to check if pagination element is present and visible
def is_pagination_visible(driver):
    try:
        pagination = driver.find_element(By.XPATH, '//div[@class="pagination"]')
        return pagination.is_displayed()
    except:
        return False

# Function to check if pagination button is interactable
def is_pagination_button_interactable(driver):
    try:
        pagination_button = driver.find_element(By.XPATH, "//a[contains(@class, 'next')]")
        return pagination_button.is_enabled()
    except:
        return False

# Function to extract business links and names from the current page
def extract_business_links_and_names(driver, business_dict):
    try:
        # Find all the business elements
        business_elements = driver.find_elements(By.XPATH, "//div[@class='result']")

        logging.info("Found the business elements")
        for business in business_elements:
            try:
                # Locate the link element
                link_element = business.find_element(By.XPATH, './/h2[@class="n"]/a')
                name = (link_element.text).strip()
                link = link_element.get_attribute('href')

                # Add the name and link to the dictionary if the name is not already present
                if name not in business_dict:
                    business_dict[name] = link
            except Exception as e:
                logging.info(f"Error extracting name and link: {e}")
                continue

        logging.info(f"Extracted {len(business_dict)} unique business names and links so far.")
    except Exception as e:
        logging.info(f"Error extracting business data: {e}")

# Main script to handle pagination and data extraction
def main(category, location):
    source = 'https://www.yellowpages.com'
    source_name = "YellowPage"

    # Generate the URL dynamically
    url = generate_yellowpages_url(category, location)

    driver = webdriver.Chrome(service=service, options=chrome_options)

    # Open the YellowPages search page
    driver.get(url)

    # Wait for the main content to load
    wait = WebDriverWait(driver,3)
    try:
        wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="main-content"]')))
        print("Main content loaded.")
    except Exception as e:
        print(f"Error waiting for main content to load: {e}")
        driver.quit()
        return

    all_business_data = {}
    while True:
        extract_business_links_and_names(driver, all_business_data)
        print(f"So far total unique items: {len(all_business_data)}")

        if is_pagination_visible(driver) and is_pagination_button_interactable(driver):
            print("Pagination button found and interactable. Clicking it.")
            try:
                pagination_button = driver.find_element(By.XPATH, "//a[contains(@class, 'next')]")
                pagination_button.click()
                time.sleep(1)  # Wait for the next page to load
            except Exception as e:
                print(f"Error clicking pagination button: {e}")
                break
        else:
            print("Pagination button not found or not interactable. Stopping pagination.")
            break

    # Convert the dictionary to a list of tuples
    all_business_data_list = list(all_business_data.items())
    print(f"Total unique business items extracted: {len(all_business_data_list)}")
    
    csv_file_path = os.getenv("CSV_FILE_PATH_yellowpage")  # Assuming this returns a valid path as a string
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
            writer.writerow(['Business Name', 'Business Link'])  # Write the header
            for name, link in all_business_data_list:
                writer.writerow([name, link])
        print(f"Links and names successfully saved to {csv_file_path}")
    except Exception as e:
        print(f"Error saving links and names to CSV: {e}")

    # Close the web driver
    driver.quit()
    
    # Use the full path to Python executable
    python_executable = sys.executable  # This gets the currently running Python executable

    # Call details.py with the CSV file path
    try:
        subprocess.run([python_executable, os.getenv("DETAIL_PATH_yellowpage"), csv_file_path, source_name, source, category], check=True)
        print(f"new_details.py executed successfully with {csv_file_path}")
    except subprocess.CalledProcessError as e:
        print(f"Error calling new_details.py: {e}")

# Set the search location
location = 'Germany'

# Iterate over categories and run the main function for each category
for category in categories:
    main(category, location)
