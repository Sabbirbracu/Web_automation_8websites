import csv
import time
import subprocess
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import urllib.parse
import sys

webdriver_path = '/Users/sabbirahmad/Desktop/chromedriver'

def generate_jameda_url(category, location):
    base_url = 'https://www.jameda.de'
    return f"{base_url}/{category}"

category = 'allgemeinmediziner'
location = 'Berlin'
source = 'https://www.jameda.de/'
source_name = "Jameda.de"
url = generate_jameda_url(category, location)

chrome_options = Options()
chrome_options.add_argument("--headless")  
service = Service(webdriver_path)
driver = webdriver.Chrome(service=service, options=chrome_options)

driver.get(url)

wait = WebDriverWait(driver, 4)
try:
    wait.until(EC.presence_of_element_located((By.XPATH, '//ul[@class="list-unstyled search-list"]')))
    print("Main content loaded.")
except Exception as e:
    print(f"Error waiting for main content to load: {e}")
    driver.quit()
    sys.exit()
def is_pagination_visible(driver):
    try:
        pagination = driver.find_element(By.XPATH, '//ul[@class="pagination pagination-lg"]')
        return pagination.is_displayed()
    except:
        return False

def is_pagination_button_interactable(driver):
    try:
        pagination_button = driver.find_element(By.XPATH, "//ul[@class='pagination pagination-lg']//a[contains(@aria-label, 'next')]")
        return pagination_button.is_enabled()
    except:
        return False

def extract_business_links_and_names(driver, business_dict):
    try:
        
        business_elements = driver.find_elements(By.XPATH, "//ul[@class='list-unstyled search-list']/li/div/div/div/div[1]/div[1]/div/div[@class='media-body']")
        print("Found the business elements")

        for business in business_elements:
            try:
                link_element = business.find_element(By.XPATH, './h3/a')
                name =  business.find_element(By.XPATH, './h3/a/span').text
                link = link_element.get_attribute('href')
                print(name)
                if name in business_dict:
                    name +="@"
                    business_dict[name] = link
                else:
                    business_dict[name] = link
            except Exception as e:
                print(f"Error extracting name and link: {e}")
                continue

        print(f"Extracted {len(business_dict)} business names and links so far.")
    except Exception as e:
        print(f"Error extracting business data: {e}")

def main(driver):
    all_business_data = {}
    try:
        print("Finding the cookies")
        wait = WebDriverWait(driver, 2)
        accept_button = wait.until(EC.element_to_be_clickable((By.ID, 'onetrust-accept-btn-handler')))
        accept_button.click()
        time.sleep(0.7)
        print("Cookies pop-up accepted.")
    except Exception as e:
        print(f"Error accepting cookies: {e}")
        
    while True:
        extract_business_links_and_names(driver, all_business_data)
        print(f"So far total unique items: {len(all_business_data)}")

        if is_pagination_visible(driver) and is_pagination_button_interactable(driver):
            print("Pagination button found and interactable. Clicking it.")
            try:
                pagination_button = driver.find_element(By.XPATH, "//a[contains(@class, 'next')]")
                pagination_button.click()
                time.sleep(1) 
            except Exception as e:
                print(f"Error clicking pagination button: {e}")
                break
        else:
            print("Pagination button not found or not interactable. Stopping pagination.")
            break

    all_business_data_list = list(all_business_data.items())
    print(f"Total unique business items extracted: {len(all_business_data_list)}")
    
    csv_file_path = f"/Users/sabbirahmad/Jameda.de/{category}.csv"
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
        subprocess.run([python_executable, '/Users/sabbirahmad/Jameda.de/details.py', csv_file_path, source_name, source, category], check=True)
        print(f"new_details.py executed successfully with {csv_file_path}")
    except subprocess.CalledProcessError as e:
        print(f"Error calling new_details.py: {e}")

main(driver)
