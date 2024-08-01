import csv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import sys
import subprocess
import urllib.parse
import os

# Path to your webdriver executable
webdriver_path = '/Users/sabbirahmad/Desktop/chromedriver'

# Function to generate the Yelp search URL
def generate_yelp_url(category, location):
    base_url = 'https://www.yelp.com/search'
    params = {
        'find_desc': category,
        'find_loc': location
    }
    return f"{base_url}?{urllib.parse.urlencode(params)}"

# Set the search category and location
category = 'School'
location = 'Germany'
source = 'https://www.yelp.com'
source_name = "Yelp"

# Generate the URL dynamically
url = generate_yelp_url(category, location)

# Initialize Chrome web driver
chrome_options = Options()
# chrome_options.add_argument("--headless")  # Run Chrome in headless mode, i.e., without a UI
service = Service(webdriver_path)
driver = webdriver.Chrome(service=service, options=chrome_options)

# Open the Yelp search page
driver.get(url)

# Wait for the main content to load
wait = WebDriverWait(driver, 20)
try:
    wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="main-content"]')))
    print("Main content loaded.")
except Exception as e:
    print(f"Error waiting for main content to load: {e}")
    driver.quit()
    exit()

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

# Function to extract restaurant links and names from the current page
def extract_restaurant_links_and_names(driver, business_dict):
    try:
        # Find all the business elements
        business_elements = driver.find_elements(By.XPATH,
            "//div[contains(@class, 'container__09f24__FeTO6') and contains(@class, 'hoverable__09f24___UXLO') and "
            "contains(@class, 'y-css-xvvvfw') or contains(@class,'y-css-way87j')]")

        print("Found the business elements")

        for business in business_elements:
            try:
                # Locate the link element
                link_element = business.find_element(By.XPATH, './/h3[@class="y-css-hcgwj4"]/a[@class="y-css-12ly5yx"]')
                name = (link_element.text).strip()
                link = link_element.get_attribute('href')

                # Add the name and link to the dictionary if the name is not already present
                if name not in business_dict:
                    business_dict[name] = link
            except Exception as e:
                print(f"Error extracting name and link: {e}")
                continue

        print(f"Extracted {len(business_dict)} unique restaurant names and links so far.")
    except Exception as e:
        print(f"Error extracting restaurant data: {e}")

# Main script to handle pagination and data extraction
def main(driver):
    all_business_data = {}
    while True:
        extract_restaurant_links_and_names(driver, all_business_data)
        print(f"So far total unique items: {len(all_business_data)}")

        if is_pagination_visible(driver) and is_pagination_button_interactable(driver):
            print("Pagination button found and interactable. Clicking it.")
            try:
                # Check and close the cookie consent banner if present
                try:
                    accept_cookies_button = driver.find_element(By.ID, 'onetrust-accept-btn-handler')
                    if accept_cookies_button.is_displayed():
                        accept_cookies_button.click()
                        time.sleep(2)  # Wait for the banner to disappear
                        print("Closed cookie consent banner.")
                except:
                    pass

                pagination_button = driver.find_element(By.XPATH, "//*/li/div[@aria-label='Pagination navigation']//button")
                driver.execute_script("arguments[0].scrollIntoView();", pagination_button)  # Scroll to the button
                driver.execute_script("arguments[0].click();", pagination_button)  # Click the button using JavaScript
                time.sleep(10)  # Wait for the next page to load
            except Exception as e:
                print(f"Error clicking pagination button: {e}")
                break
        else:
            print("Pagination button not found or not interactable. Stopping pagination.")
            break

    # Convert the dictionary to a list of tuples
    all_business_data_list = list(all_business_data.items())
    print(f"Total unique restaurant items extracted: {len(all_business_data_list)}")
    
    # Save the links and names to a CSV file
    csv_file_path = f"/Users/sabbirahmad/Yelp Data scrapping./{category.replace(' ', '_')}.csv"
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
        subprocess.run([python_executable, '/Users/sabbirahmad/Yelp Data scrapping./details.py', csv_file_path, source_name, source, category], check=True)
        print(f"details.py executed successfully with {csv_file_path}")
    except subprocess.CalledProcessError as e:
        print(f"Error calling details.py: {e}")

# Run the main function
main(driver)
