import csv
import time
import subprocess
import urllib.parse
import sys
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

# Path to your webdriver executable
webdriver_path = '/Users/sabbirahmad/Desktop/chromedriver'

# Function to generate the Google Maps search URL
def generate_google_maps_url(category, location):
    base_url = 'https://www.google.com/maps/search/'
    query = f"{category} in {location}"
    return f"{base_url}{urllib.parse.quote(query)}/?hl=en"  # Append hl=en to ensure English results

# Set the search category and location
category = 'Burger'
location = 'Germany'
source = 'https://www.google.com/maps'
source_name = "Google Maps"

# Generate the URL dynamically
url = generate_google_maps_url(category, location)

# Initialize Chrome web driver with existing user profile
chrome_options = Options()
chrome_options.add_argument("user-data-dir=/Users/sabbirahmad/Library/Application Support/Google/Chrome/Default")  # Change to your Chrome profile path
chrome_options.add_argument("--headless")  # Optional: Run Chrome in headless mode, i.e., without a UI
chrome_options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")
chrome_options.add_argument("--window-size=1920,1080")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--disable-software-rasterizer")
chrome_options.add_argument("--lang=en")

# Set logging preferences
chrome_options.set_capability('goog:loggingPrefs', {'browser': 'ALL'})

service = Service(webdriver_path)
driver = webdriver.Chrome(service=service, options=chrome_options)

# Open the Google Maps search page
driver.get(url)

# Wait for the main content to load
wait = WebDriverWait(driver, 4)
try:
    wait.until(EC.presence_of_element_located((By.XPATH, '//div[@class="m6QErb DxyBCb kA9KIf dS8AEf XiKgde ecceSd"]')))
    print("Main content loaded.")
    time.sleep(1)
except Exception as e:
    print(f"Error waiting for main content to load: {e}")
    driver.quit()
    sys.exit()

# Function to scroll until the end of results
def scroll_to_end(driver):
    num = 0
    scrollable_div = driver.find_element(By.XPATH, '//div[@class="m6QErb DxyBCb kA9KIf dS8AEf XiKgde ecceSd"]')
    while True:
        driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", scrollable_div)
        num += 1
        print(f"Scrolled {num} times and it's sleeping.")
        time.sleep(1.7)  # Give time for new elements to load
        try:
            # Check if the end of the results is reached
            driver.find_element(By.XPATH, '//span[@class="HlvSq"]')
            print("Reached the end of the results.")
            break
        except:
            continue

# Function to extract business links and names from the current page
def extract_business_links_and_names(driver, business_dict):
    try:
        # Find all the business elements
        business_elements = driver.find_elements(By.XPATH, "//div[contains(@class,'Nv2PK')]")
        print("Found the business elements")
        time.sleep(1)

        for business in business_elements:
            try:
                # Locate the link element
                link_element = business.find_element(By.XPATH, './/a[@class="hfpxzc"]')
                link = link_element.get_attribute('href')
                name = link_element.get_attribute('aria-label')
                logging.info(f"The name is {name}")
                # Add the name and link to the dictionary if the name is not already present
                if name and link not in business_dict:
                    business_dict[name] = link
            except Exception as e:
                print(f"Error extracting name and link: {e}")
                continue

        print(f"Extracted {len(business_dict)} unique business names and links so far.")
    except Exception as e:
        print(f"Error extracting business data: {e}")

# Main script to handle scrolling and data extraction
def main(driver):
    all_business_data = {}
    
    # Scroll to the end of the results
    scroll_to_end(driver)
    
    # Extract all business names and links
    extract_business_links_and_names(driver, all_business_data)
    print(f"So far total unique items: {len(all_business_data)}")

    # Convert the dictionary to a list of tuples
    all_business_data_list = list(all_business_data.items())
    print(f"Total unique business items extracted: {len(all_business_data_list)}")

    # Save the links and names to a CSV file
    csv_file_path = f"/Users/sabbirahmad/google maps/{category.replace(' ', '_')} in {location}.csv"
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
        subprocess.run([python_executable, '/Users/sabbirahmad/google maps/details.py', csv_file_path, source_name, source, category], check=True)
        print(f"details.py executed successfully with {csv_file_path}")
    except subprocess.CalledProcessError as e:
        print(f"Error calling details.py: {e}")

    # Log JavaScript errors
    logs = driver.get_log("browser")
    for log in logs:
        logging.info(log)

# Run the main function
main(driver)

