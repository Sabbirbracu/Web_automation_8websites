import csv
import logging
import time
import sys
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, ElementNotInteractableException, StaleElementReferenceException

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

# Path to your WebDriver executable
webdriver_path = '/Users/sabbirahmad/Desktop/chromedriver'

# Get the CSV file path from the command-line arguments
if len(sys.argv) < 5:
    logger.error("CSV file path not provided.")
    sys.exit(1)
csv_input_file_path = sys.argv[1]
source_name = sys.argv[2]
source = sys.argv[3]
category = sys.argv[4]

# Extract the table name from the CSV file name
table_name = "Scrapped_Data"

# Initialize Chrome WebDriver
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=1920x1080")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--remote-debugging-port=9222")
service = Service(webdriver_path)
driver = webdriver.Chrome(service=service, options=chrome_options)

# Function to read links from CSV
def read_csv(file_path):
    with open(file_path, mode='r') as file:
        csv_reader = csv.reader(file)
        next(csv_reader)  # Skip header row
        return list(csv_reader)

# Initialize WebDriverWait
wait = WebDriverWait(driver, 4)

def get_phone_number(driver):
    try:
        phone_element = driver.find_element(By.XPATH, '//div[@class="RcCsl fVHpi w4vB1d NOE9ve M0S7ae AG25L "]/button[contains(@aria-label,"Phone")]')
        driver.execute_script("arguments[0].scrollIntoView();", phone_element)
        phone_num = phone_element.find_element(By.XPATH, './/div[@class="Io6YTe fontBodyMedium kR99db "]').text
        return phone_num if phone_num else "N/A"
    except NoSuchElementException:
        return "N/A"

def get_average_rating(driver):
    try:
        rating_element = driver.find_element(By.XPATH, '//div[@class="skqShb "]//div[@class="F7nice "]/span[1]/span[1]')
        driver.execute_script("arguments[0].scrollIntoView();", rating_element)
        avg_rating = rating_element.text
        return avg_rating if avg_rating else "N/A"
    except NoSuchElementException:
        return "N/A"

# Function to extract review information from the current page
def extract_reviews(driver, company_name, company_link, phone_num, avg_rating, source_name, source, category):
    reviews_data = []
    retries = 5
    while retries > 0:
        try:
            review_elements = wait.until(EC.presence_of_all_elements_located((By.XPATH, '//div[@class="jftiEf fontBodyMedium "]')))
            for review in review_elements:
                try:
                    reviewer_name = review.find_element(By.XPATH, './/div[@class="d4r55 "]').text if review.find_element(By.XPATH, './/div[@class="d4r55 "]') else "N/A"
                    logger.info(f"Reviewer name is {reviewer_name}")
                    review_date = review.find_element(By.XPATH, './/span[@class="rsqaWe"]').text if review.find_element(By.XPATH, './/span[@class="rsqaWe"]') else "N/A"
                    logger.info(f"Review date is {review_date}")

                    review_star_elem = review.find_element(By.XPATH, './/span[@class="kvMYJc"]').get_attribute('aria-label')
                    review_star = review_star_elem.split()[0] if review_star_elem else "N/A"

                    review_description = review.find_element(By.XPATH, './/span[@class="wiI7pd"]').text if review.find_element(By.XPATH, './/span[@class="wiI7pd"]') else "N/A"

                    reviews_data.append((company_name, company_link, reviewer_name, review_date, review_star, review_description, phone_num, avg_rating, source_name, source, category))
                except StaleElementReferenceException:
                    logger.warning("Stale element reference, re-finding element.")
                    retries -= 1
                    break
                except NoSuchElementException as e:
                    logger.error(f"Error finding sub-elements in review: {e}")
                except Exception as e:
                    logger.error(f"Unexpected error during sub-element extraction: {e}")
            else:
                break  # Break the outer loop if no stale element exception occurs

            logger.info(f"Extracted {len(reviews_data)} reviews.")
        except TimeoutException as e:
            logger.error(f"Timeout while waiting for review elements: {e}")
        except Exception as e:
            logger.error(f"Unexpected error during review extraction: {e}")
        retries -= 1
    return reviews_data

def click_reviews_button(driver):
    try:
        # Wait for the reviews button to be clickable
        reviews_button = WebDriverWait(driver, 4).until(
            EC.element_to_be_clickable((By.XPATH, '//div[@class="RWPxGd"]/button[2]'))
        )
        driver.execute_script("arguments[0].scrollIntoView();", reviews_button)
        driver.execute_script("arguments[0].click();", reviews_button)
        logger.info("Clicked on the reviews button.")
        return True
    except (NoSuchElementException, TimeoutException, ElementNotInteractableException, Exception) as e:
        logger.error(f"Error clicking the reviews button: {e}")
        return False

# Function to process each company link
def process_company_link(driver, name, link, source_name, source, category):
    driver.get(link)
    try:
        wait.until(EC.presence_of_element_located((By.XPATH, '//div[@class="m6QErb WNBkOb XiKgde " and @role="main"]')))
        logger.info("Reviews section loaded.")
        
        time.sleep(1)
        phone_num = get_phone_number(driver)
        logger.info(f"Phone number is {phone_num}")

        avg_rating = get_average_rating(driver)
        logger.info(f"Average rating is {avg_rating}")

        # Attempt to click the reviews button
        clicked = click_reviews_button(driver)
        if not clicked:
            logger.error("Failed to click the reviews button.")
            return

        try:
            review_section = wait.until(EC.presence_of_element_located((By.XPATH, '//div[@class="m6QErb XiKgde "]')))
            logger.info("Review section loaded.")
        except TimeoutException:
            logger.error("Reviews did not load in time.")
            return

        reviews_data = extract_reviews(driver, name, link, phone_num, avg_rating, source_name, source, category)
        
        for review_data in reviews_data:
            print(review_data)

        logger.info(f"Processed link: {link}")

    except TimeoutException:
        logger.error("Timed out waiting for the reviews section to load.")
    except Exception as e:
        logger.error(f"Error processing link {link}: {e}")

# Main function
def main():
    company_links = read_csv(csv_input_file_path)
    for row in company_links:
        name, link = row[0], row[1]
        process_company_link(driver, name, link, source_name, source, category)

    driver.quit()

if __name__ == "__main__":
    main()
