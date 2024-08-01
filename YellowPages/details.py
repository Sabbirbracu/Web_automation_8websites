
import csv
import logging
import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json
import sys  # Add this import to get command-line arguments

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

# Path to your webdriver executable
webdriver_path = '/Users/sabbirahmad/Desktop/chromedriver'

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
chrome_options.add_argument("--headless")  
service = Service(webdriver_path)
driver = webdriver.Chrome(service=service, options=chrome_options)

# Open the input CSV file and read links
with open(csv_input_file_path, mode='r') as file:
    csv_reader = csv.reader(file)
    next(csv_reader)  # Skip header row
    links = list(csv_reader)

# Initialize WebDriverWait
wait = WebDriverWait(driver, 3)

# Function to extract review information from the current page
def extract_reviews(driver, company_name, company_link, phone_num, avg_rating, source_name, source, category):
    reviews_data = []
    try:
        # time.sleep(5)
        review_elements = driver.find_elements(By.XPATH, '//div[@id="reviews-container"]/article[@class="clearfix"]/div[@class="entry clearfix"]')
        for review in review_elements:
            try:
                reviewer_name = review.find_element(By.XPATH, './/div[@class="review-info"]//a[@class="author"]').text
                logging.info(f"reviewer name is {reviewer_name}")
            except Exception as e:
                try:
                     reviewer_name = review.find_element(By.XPATH, './/div[@class="review-info"]//div[@class="author"]')
                     logging.info(f"reviewer name is {reviewer_name}")
                except:
                    reviewer_name = "N/A"
                    logger.error(f"Reviewer name not found: Reviewer name = {reviewer_name}")

            try:
                review_date = review.find_element(By.XPATH, './/div[@class="review-info"]/div[@class="review-dates"]//span').text
                logging.info(f"review date is {review_date}")
            except Exception as e:
                review_date = "N/A"
                logger.error(f"Review date not found: {e}")

            rating_map = {
                "one": 1,
                "two": 2,
                "three": 3,
                "four": 4,
                "five": 5,
                "four half": 4.5,
                "three half": 3.5,
                "two half": 2.5,
                "one half": 1.5
            }

            try:
                # Locate the review star container
                review_star_container = review.find_element(By.XPATH, './/div[@class="result-ratings overall"]/div[contains(@class, "rating-indicator")]')
                
                # Extract the class attribute
                rating_class = review_star_container.get_attribute("class")
                
                # Split the class names and find the rating word
                rating_word = rating_class.split()
                if len(rating_word) >2:
                    rating_words = rating_word[1] + rating_word[2]
                else:
                    rating_words = rating_word[1]
                
                # Convert the rating word to a number using the rating_map
                review_star = rating_map.get(rating_words, "N/A")
                logging.info(f'Review star rating is {review_star}')
            except Exception as e:
                review_star = "N/A"
                logger.error(f"Review star not found: {e}")

            try:
                review_description = review.find_element(By.XPATH, './/div[@class="review-response"]/p').text
                logger.info(f"The review is:--- {review_description}")
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
            reviews_data.append((company_name, company_link, reviewer_name, review_date, review_star, review_description, phone_num, avg_rating, source_name, source, category))
    except Exception as e:
        logger.error(f"Error finding review elements: {e}")
    return reviews_data

# Function to handle pagination
def handle_pagination(driver, restaurant_name, restaurant_link, phone_num, avg_rating, source_name, source, category):
    all_reviews = []
    while True:
        reviews = extract_reviews(driver, restaurant_name, restaurant_link, phone_num, avg_rating, source_name, source, category)
        all_reviews.extend(reviews)
        try:
            if driver.find_element(By.XPATH, '//div[@class="pagination"]/span[@class="next"]/a'):
                next_button = driver.find_element(By.XPATH, '//div[@class="pagination"]/span[@class="next"]/a')
                logging.info("found the next button")
                next_button.click()
                time.sleep(4)  # Adjust the sleep time as necessary
        except Exception as e:
            logger.info("No more pages found.")
            break
    return all_reviews

# Iterate over links and extract review data
for name, link in links:
    logger.info(f"Opening link for: {name}")
    driver.get(link)
    try:
        # Check if the page is not available
        if "You may need permission to access this page" in driver.page_source:
            logger.error("Permission needed to access this page. Stopping execution.")
            break

        # Wait for the reviews to load
        wait.until(EC.presence_of_element_located((By.XPATH, '//div[@id= "reviews-container"]')))
        logger.info("Reviews section loaded.")
        
        # Initialize phone_num to handle cases where it may not be found
        phone_num = "N/A"
        try:
            phone_num_element = driver.find_element(By.XPATH, '//div[@id="listing-card"]/section[@class="inner-section"]/a[@class="phone dockable"]/span[@class="full"]')
            phone_num = phone_num_element.text[:50]  # Ensure within VARCHAR(50)
            logging.info(f"Got the phone number and the phone number is {phone_num}")
        except Exception as e:
            logger.error(f"Phone number not found: {e}")

        # Extract the average rating
        avg_rating = "N/A"
        try:
            avg_rating_element = driver.find_element(By.XPATH, '//a[@title="Star Ratings"]')
            avg_rating = avg_rating_element.get_attribute("rate")
            if avg_rating is None:  # If the rate attribute is not found, fallback to extracting from data-analytics
                data_analytics = avg_rating_element.get_attribute("data-analytics")
                avg_rating = json.loads(data_analytics).get("rate", "N/A")
            logging.info(f'Average rating is {avg_rating}')
        except Exception as e:
            logger.error(f"Average rating not found: {e}")

        # Scroll down twice to load more reviews
        driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.PAGE_DOWN)
        time.sleep(1)
        driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.PAGE_DOWN)
        time.sleep(1)

        # Handle pagination and extract review data
        reviews = handle_pagination(driver, name, link, phone_num, avg_rating, source_name, source, category)
        
        # Print the review data
        for review in reviews:
            print(review)

    except Exception as e:
        logger.error(f"Error processing link {link}: {e}")
        continue

driver.quit()
