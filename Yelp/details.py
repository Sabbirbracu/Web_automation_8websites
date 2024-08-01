import csv
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import sys
import os
import mysql.connector
from mysql.connector import errorcode

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

# Path to your webdriver executable
webdriver_path = os.getenv("WEBDRIVER_PATH")

# Get the CSV file path from the command-line arguments
if len(sys.argv) < 5:
    logger.error("CSV file path not provided.")
    sys.exit(1)
csv_input_file_path = sys.argv[1]
source = sys.argv[3]
category = sys.argv[4]
source_name = sys.argv[2]


# Initialize Chrome web driver
chrome_options = Options()
# chrome_options.add_argument("--headless")  # Uncomment to run Chrome in headless mode
service = Service(webdriver_path)
driver = webdriver.Chrome(service=service, options=chrome_options)

# Open the input CSV file and read links
with open(csv_input_file_path, mode='r') as file:
    csv_reader = csv.reader(file)
    next(csv_reader)  # Skip header row
    links = list(csv_reader)

# Initialize WebDriverWait
wait = WebDriverWait(driver, 4)


# Function to extract review information from the current page
def extract_reviews(driver, company_name, company_link, phone_num, avg_rating, source_name, source, category):
    reviews_data = []
    try:
        # time.sleep(5)
        review_elements = driver.find_elements(By.XPATH, '//div[@class=" y-css-1iy1dwt"]/ul[@class=" list__09f24__ynIEd"]/li[@class=" y-css-1jp2syp"]/div[@class=" y-css-1iy1dwt"]')
        # logging.info("Got the review elements")
        for review in review_elements:
            try:
                reviewer_name = review.find_element(By.XPATH, './/div[@class="user-passport-info y-css-1iy1dwt"]/span[@class=" y-css-w3ea6v"]/a[@class="y-css-12ly5yx"]').text
                logging.info("Got the reviewer name")
    
            except Exception as e:
                reviewer_name = "N/A"
                logger.error(f"Reviewer name not found: {e}")

            try:
                review_date = review.find_element(By.XPATH, './/div[@class=" y-css-19pbem2"]/div/div[2]/span[contains(@class, " y-css-wfbtsu")]').text
                logging.info("Got the review date")
            except Exception as e:
                review_date = "N/A"
                logger.error(f"Review date not found: {e}")

            try:
                review_star = review.find_element(By.XPATH, './/div[@class=" y-css-19pbem2"]/div/div[1]/span/div[@class="y-css-9tnml4"]').get_attribute('aria-label')
                logging.info("Got the review star")
            except Exception as e:
                review_star = "N/A"
                logger.error(f"Review star not found: {e}")

            try:
                review_description = review.find_element(By.XPATH, './/p[@class= "comment__09f24__D0cxf y-css-h9c2fl"]/span[@class=" raw__09f24__T4Ezm"]').text
                logging.info("Got the review description")
            except Exception as e:
                review_description = "N/A"
                logger.error(f"Review description not found: {e}")

            reviews_data.append((company_name, company_link, reviewer_name, review_date, review_star, review_description, phone_num, avg_rating, source_name, source, category))
        logger.info(f"Extracted {len(reviews_data)} reviews.")

        if len(reviews_data) == 0:
            reviewer_name = "N/A"
            review_date = "N/A"
            review_star = "N/A"
            review_description = "N/A"
            reviews_data.append((company_name, company_link, reviewer_name, review_date, review_star, review_description, phone_num, avg_rating,source_name, source, category))
    except Exception as e:
        logger.error(f"Error finding review elements: {e}")
    return reviews_data


# Function to handle pagination
def handle_pagination(driver, company_name, company_link, phone_num, avg_rating, source_name, source, category):
    all_reviews = []
    while True:
        reviews = extract_reviews(driver, company_name, company_link, phone_num, avg_rating, source_name, source, category)
        all_reviews.extend(reviews)
        try:
            next_button = driver.find_element(By.XPATH, '//div[@class="pagination-links__09f24__bmFj8 y-css-lbeyaq"]/div[@class="navigation-button-container__09f24__SvcBh y-css-1iy1dwt"]/span/a[@aria-label="Next"]')
            next_button.click()
            time.sleep(1)  # Adjust the sleep time as necessary
        except Exception as e:
            logger.info("No more pages found.")
            break
    return all_reviews

for name, link in links:
    logger.info(f"Opening link for: {name}")
    driver.get(link)
    try:
        # Check if the page is not available
        if "You may need permission to access this page" in driver.page_source:
            logger.error("Permission needed to access this page. Stopping execution.")
            break

        # Wait for the reviews to load
        wait.until(EC.presence_of_element_located((By.XPATH, '//ul[contains(@class, "list__09f24__ynIEd")]')))
        logger.info("Reviews section loaded.")
        
        # Initialize phone_num to handle cases where it may not be found
        phone_num = "N/A"
        try:
            phone_num_element = driver.find_element(By.XPATH, '//p[text()="Phone number"]/following-sibling::p[contains(@class, "y-css-1o34y7f") and @data-font-weight="semibold"]')
            phone_num = phone_num_element.text[:50]  # Ensure within VARCHAR(50)
            logging.info("got the Phone Number")
        except Exception as e:
            phone_num = "N/A"
            logger.error(f"Phone number not found: {e}")

        # Extract the average rating
        avg_rating = "N/A"
        try:
            avg_rating_element = driver.find_element(By.XPATH, '//span[contains(@class, "y-css-1o34y7f") or  contains(@class, "y-css-kw85nd") and @data-font-weight="semibold"]')
            avg_rating = avg_rating_element.text
            logging.info("Got the Avg Rattings")
        except Exception as e:
            avg_rating = "N/A"
            logger.error(f"Average rating not found: {e}")

        # Scroll down twice to load more reviews
        driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.PAGE_DOWN)
        time.sleep(1)
        driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.PAGE_DOWN)
        time.sleep(1)

        # Handle pagination and extract review data
        reviews = handle_pagination(driver, name, link, phone_num, avg_rating, source_name, source, category)
        
        # Insert review data into MySQL
        for review in reviews:
            logger.info(review)

    except Exception:
        logger.error(f"Error processing link")
        continue
driver.quit()
