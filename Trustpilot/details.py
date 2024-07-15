import re
import csv
import logging
import time
import sys
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import requests
from selenium.common.exceptions import StaleElementReferenceException
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
sys.stdout.reconfigure(encoding='utf-8')


# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

# Path to your webdriver executable
webdriver_path = os.getenv("WEBDRIVER_PATH")

if len(sys.argv) < 5:
    logger.error("CSV file path not provided.")
    sys.exit(1)
csv_input_file_path = sys.argv[1]
source = sys.argv[3]
category = sys.argv[4]
source_name = sys.argv[2]

chrome_options = Options()
chrome_options.add_argument("--headless")  
service = Service(webdriver_path)
driver = webdriver.Chrome(service=service, options=chrome_options)

with open(csv_input_file_path, mode='r') as file:
    csv_reader = csv.reader(file)
    next(csv_reader)  
    links = list(csv_reader)

wait = WebDriverWait(driver, 4)

def is_pagination_visible(driver):
    try:
        pagination = driver.find_element(By.XPATH, '//div[@class="styles_pagination__6VmQv"]/nav[@aria-label="Pagination"]/a[@name="pagination-button-next"]')
        return pagination.is_displayed() and pagination.is_enabled()
    except:
        return False

def is_pagination_button_interactable(driver):
    try:
        pagination_button = driver.find_element(By.XPATH, '//div[@class="styles_pagination__6VmQv"]/nav[@aria-label="Pagination"]/a[@name="pagination-button-next"]')
        if pagination_button.get_attribute("aria-disabled") == "true":
            logger.info("Pagination is end")
            return False
        elif pagination_button.get_attribute("data-pagination-button-next-link") == "true":
            logger.info("Next page is available")
            return True
        else:
            return False
    except:
        return False

def extract_reviews_with_bs(driver,company_name, company_link, phone_num, email, location, avg_rating, Source_Name, source, category):
    reviews_data = []
    try:
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        review_elements = soup.find_all('div', class_='styles_cardWrapper__LcCPA styles_show__HUXRb styles_reviewCard__9HxJJ')
        
        for review in review_elements:
            try:
                reviewer_name = review.find('div', class_='styles_consumerDetailsWrapper__p2wdr').find('a', {'name': 'consumer-profile'}).span.text.strip()
                logger.info(f"Reviewer name: {reviewer_name}")
            except AttributeError as e:
                reviewer_name = "N/A"
                logger.error(f"Reviewer name not found: {e}")

            try:
                # country code
                reviewer_cc = review.find('div', class_='typography_body-m__xgxZ_ typography_appearance-subtle__8_H2l styles_detailsIcon__Fo_ua').span.text.strip()
                logger.info(f"Reviewer cc: {reviewer_cc}")
            except AttributeError as e:
                reviewer_cc = "N/A"
                logger.error(f"Reviewer cc not found: {e}")

            try:
                review_date = review.find('div', class_='typography_body-m__xgxZ_ typography_appearance-subtle__8_H2l styles_datesWrapper__RCEKH').time.text.strip()
                logger.info(f"Review date: {review_date}")
            except AttributeError as e:
                review_date = "N/A"
                logger.error(f"Review date not found: {e}")

            try:
                review_star_elem = review.find('div', class_='star-rating_starRating__4rrcf star-rating_medium__iN6Ty').img['alt']
                review_star = review_star_elem.split()[1]
                logger.info(f"Review star rating: {review_star}")
            except AttributeError as e:
                review_star = "N/A"
                logger.error(f"Review star not found: {e}")

            try:
                review_description = review.find('div', class_='styles_reviewContent__0Q2Tg').p.text.strip()
                logger.info("Got the review description")
            except AttributeError as e:
                review_description = "N/A"
                logger.info("Review Description Not Found")

            city= ""
            reviews_data.append((company_name, company_link, reviewer_name, reviewer_cc, review_date, review_star, review_description, phone_num, email, location, avg_rating, Source_Name, source, category, city))
        
        logger.info(f"Extracted {len(reviews_data)} reviews.")
        
        if len(reviews_data) == 0:
            reviewer_name = "N/A"
            review_date = ""
            review_star = "N/A"
            reviewer_cc = "N/A"
            review_description = "N/A"
            city= ""
            reviews_data.append((company_name, company_link, reviewer_name, reviewer_cc, review_date, review_star, review_description, phone_num, email, location, avg_rating,Source_Name, source, category, city))
    except Exception as e:
        logger.error(f"Error finding review elements: {e}")
    
    return reviews_data

def handle_pagination(driver, company_name, company_link, phone_num, email, location, avg_rating, Source_Name, source, category):
    all_reviews = []

    try:
        all_review_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//a[@class="link_internal__7XN06 button_button__T34Lr button_l__mm_bi button_appearance-secondary__VUFHU link_button___108l styles_link__0RbL4 styles_loadMoreLanguages__wonXg"]')))
        all_review_button.click()
        logger.info("Clicked all reviews button")
        time.sleep(2)
    except Exception as e:
        logger.info("All reviews button not found or not clickable: {}".format(e))

    while True:
        reviews = extract_reviews_with_bs(driver, company_name, company_link, phone_num, email, location, avg_rating, Source_Name, source, category)
        all_reviews.extend(reviews)

        try:
            if is_pagination_visible(driver) and is_pagination_button_interactable(driver):
                logger.info("Pagination button found and interactable. Clicking it.")
                try:
                    pagination_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[@name='pagination-button-next']")))
                    
                    driver.execute_script("arguments[0].scrollIntoView(true);", pagination_button)
                    
                    try:
                        driver.execute_script("arguments[0].click();", pagination_button)
                        logger.info("Clicked the pagination button")
                        time.sleep(2)
                    except StaleElementReferenceException as e:
                        logger.error("Pagination button became stale. Re-finding the element.")
                        pagination_button = driver.find_element(By.XPATH, "//a[@name='pagination-button-next']")
                        driver.execute_script("arguments[0].click();", pagination_button)
                        logger.info("Clicked the pagination button after re-finding")
                        time.sleep(2)
                except Exception as e:
                    logger.error("Pagination button not clicked. Exception: {}".format(e))
                    driver.save_screenshot('pagination_error.png')
                    break
            else:
                logger.info("No more pages to paginate.")
                break
        except Exception as e:
            logger.info("No more pages found or an error occurred: {}".format(e))
            break

    return all_reviews

# Define a function to validate email format
def is_valid_email(email):
    # Basic email regex pattern
    pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(pattern, email) is not None

# Define a function to validate phone number format
def is_valid_phone(phone):
    # Pattern to match numbers and + character only
    pattern = r'^\+?[\d\s\-/]+$'
    return re.match(pattern, phone) is not None

for name, link in links:
    logger.info(f"Opening link for: {name}")

    if name == "Lizenzexperte.de":
        logger.info(f"skipping for: {name}")
        continue
    else:
        # update link to fetch all reviews
        link_with_param = link + "?languages=all&stars=1&stars=2&stars=3"
        driver.get(link_with_param)

        try:
            wait.until(EC.presence_of_element_located((By.XPATH, '//section[@class="styles_reviewsContainer__3_GQw"]')))
            logger.info("Reviews section loaded.")

            # IDs of the checkboxes to check
            # checkbox_ids = [
            #     'star-filter-page-filter-one',
            #     'star-filter-page-filter-two',
            #     'star-filter-page-filter-three'
            # ]

            # try:
            #     # checkbox = driver.find_element(By.XPATH, '//input[@type="checkbox"]')
            #     # logger.info(f"Checkbox: {checkbox}")
            #     for checkbox_id in checkbox_ids:
            #         checkbox = driver.find_element(By.ID, checkbox_id)
            #         if not checkbox.is_selected() and checkbox.is_enabled():
            #             checkbox.click()
            #         else:
            #             logger.info(f"Checkbox with ID {checkbox_id} is either already selected or disabled.")
            # except Exception as e:
            #     logger.error(f"Error in checkbox logic: {e}")
            
            email = ""
            try:
                email = driver.find_element(By.XPATH, '//address//a[starts-with(@href, "mailto:")]').text
                if is_valid_email(email):
                    logger.info(f"Email found: {email}")
                else:
                    email = ""
                    logger.info("Invalid email format.")
            except Exception as e:
                logger.info(f"Email not found:")

            phone_num = "N/A"
            try:
                phone_num = driver.find_element(By.XPATH, '//a[starts-with(@href, "tel:")]').text
                if is_valid_phone(phone_num):
                    logger.info(f"Phone number found: {phone_num}")
                else:
                    phone_num = "N/A"
                    logger.info(f"Invalid phone number format for category-: {category} and company link-: {link}")
                    logger.info("skiping this company")
                    logger.info("")
                    continue
            except Exception as e:
                logger.info(f"Phone number not found for category-: {category} and company link-: {link}") 
                logger.info("skiping this company")
                logger.info("")
                continue

            location = "Germany"
            try:
                li_elements = driver.find_elements(By.XPATH, '//address/ul/li/ul/li')
                # Extract the text content of each li element
                locations = [li.text for li in li_elements]

                # Join the list elements into a single string separated by commas
                location_string = ', '.join(locations)

                location = "Germany" if len(location_string) == 0 else location_string
                logger.info(f"Location found: {location}")
            except Exception as e:
                logger.info("Location not found.")

            avg_rating = "N/A"
            try:
                avg_rating_element = driver.find_element(By.XPATH, '//span[@class="typography_heading-m__T_L_X typography_appearance-default__AAY17"]')
                avg_rating = avg_rating_element.text.strip()
                logger.info(f'Average rating is {avg_rating}')
            except Exception as e:
                if driver.find_element(By.XPATH, '//p[@class="typography_body-l__KUYFJ typography_appearance-default__AAY17"]').text.strip() == "0 total":
                    avg_rating = "0"
                else:
                    logger.error(f"Average rating not found: {e}")

            reviews = handle_pagination(driver, name, link, phone_num, email, location, avg_rating, source_name, source, category)

            response = requests.post(os.getenv("ENDPOINT"),json=reviews)

            if response.status_code == 201:
                response_data = response.json()
                print("Data created successfully:")
                print("******",response_data.get('success', False))
            else:
                print(f"Error {response.status_code}: {response.text}")

            # for review in reviews:
            #     logger.info("**************")
            #     logger.info(review)
            #     logger.info("**************")

        except Exception as e:
            logger.error(f"Error processing link {link}: {e}")
            continue

driver.quit()
