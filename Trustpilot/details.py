import csv
import logging
import time
import mysql.connector
import sys
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from mysql.connector import errorcode
from bs4 import BeautifulSoup
import requests
from selenium.common.exceptions import StaleElementReferenceException

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

# PLease input the databse configuration here

# mysql_config = {
#     'user': 'root',
#     'password': 'EasyMove2024',
#     'host': 'localhost',
#     'database': 'Scrapping',
#     'connect_timeout': 60,
#     'connection_timeout': 60
# }

webdriver_path = '/Users/sabbirahmad/Desktop/chromedriver'

if len(sys.argv) < 5:
    logger.error("CSV file path not provided.")
    sys.exit(1)
csv_input_file_path = sys.argv[1]
source = sys.argv[3]
category = sys.argv[4]
source_name = sys.argv[2]

table_name = "Scrapped_Dkyyk"
chrome_options = Options()
chrome_options.add_argument("--headless")  
service = Service(webdriver_path)
driver = webdriver.Chrome(service=service, options=chrome_options)

with open(csv_input_file_path, mode='r') as file:
    csv_reader = csv.reader(file)
    next(csv_reader)  
    links = list(csv_reader)

wait = WebDriverWait(driver, 4)

def create_table(cursor, table_name):
    create_table_query = f"""
    CREATE TABLE IF NOT EXISTS `{table_name}` (
        id INT AUTO_INCREMENT PRIMARY KEY,
        Company_name VARCHAR(255),
        Company_link VARCHAR(1000),
        reviewer_name VARCHAR(255),
        review_date VARCHAR(50),
        review_star VARCHAR(50),
        review_description TEXT,
        phone_num VARCHAR(50),
        avg_rating VARCHAR(50),
        Source_Name VARCHAR(50),
        Source_Website VARCHAR(255),
        Company_category VARCHAR(100)
    );
    """
    try:
        cursor.execute(create_table_query)
        logger.info(f"Table `{table_name}` ensured to exist.")
    except mysql.connector.Error as err:
        logger.error(f"Error creating table: {err}")

def review_exists(cursor, table_name, reviewer_name, review_date):
    query = f"""
    SELECT COUNT(*) FROM `{table_name}` WHERE reviewer_name = %s AND review_date = %s;
    """
    try:
        cursor.execute(query, (reviewer_name, review_date))
        result = cursor.fetchone()
        return result[0] > 0
    except mysql.connector.Error as err:
        if err.errno in [errorcode.CR_SERVER_LOST, errorcode.CR_SERVER_GONE_ERROR]:
            logger.error(f"Lost connection to MySQL server. Attempting to reconnect: {err}")
            reconnect_mysql(connection, cursor)
            cursor.execute(query, (reviewer_name, review_date))
            result = cursor.fetchone()
            return result[0] > 0
        else:
            logger.error(f"Error checking review existence: {err}")
            return False

def insert_review_data(cursor, table_name, data):
    insert_query = f"""
    INSERT INTO `{table_name}` (Company_name, Company_link, reviewer_name, review_date, review_star, review_description, phone_num, avg_rating,Source_Name, Source_Website, Company_category)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
    """
    try:
        cursor.execute(insert_query, data)
    except mysql.connector.Error as err:
        if err.errno in [errorcode.CR_SERVER_LOST, errorcode.CR_SERVER_GONE_ERROR]:
            logger.error(f"Lost connection to MySQL server. Attempting to reconnect: {err}")
            reconnect_mysql(connection, cursor)
            cursor.execute(insert_query, data)
        else:
            logger.error(f"Error inserting data: {err}")

def reconnect_mysql(connection, cursor):
    try:
        connection.ping(reconnect=True, attempts=3, delay=5)
        logger.info("Reconnected to MySQL server.")
    except mysql.connector.Error as err:
        logger.error(f"Failed to reconnect to MySQL server: {err}")
        sys.exit(1)

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

def extract_reviews_with_bs(driver,company_name, company_link, phone_num, avg_rating, Source_Name, source, category, cursor, table_name):
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
                review_date = review.find('div', class_='typography_body-m__xgxZ_ typography_appearance-subtle__8_H2l styles_datesWrapper__RCEKH').time.text.strip()
                logger.info(f"Review date: {review_date}")
            except AttributeError as e:
                review_date = "N/A"
                logger.error(f"Review date not found: {e}")

            if review_exists(cursor, table_name, reviewer_name, review_date):
                logger.info(f"Review by {reviewer_name} on {review_date} already exists. Skipping.")
                continue

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

            reviews_data.append((company_name, company_link, reviewer_name, review_date, review_star, review_description, phone_num, avg_rating, Source_Name, source, category))
        
        logger.info(f"Extracted {len(reviews_data)} reviews.")
        
        if len(reviews_data) == 0:
            reviewer_name = "N/A"
            review_date = "N/A"
            review_star = "N/A"
            review_description = "N/A"
            reviews_data.append((company_name, company_link, reviewer_name, review_date, review_star, review_description, phone_num, avg_rating,Source_Name, source, category))
    except Exception as e:
        logger.error(f"Error finding review elements: {e}")
    
    return reviews_data

def handle_pagination(driver, company_name, company_link, phone_num, avg_rating, Source_Name, source, category, cursor, table_name):
    all_reviews = []

    try:
        all_review_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//a[@class="link_internal__7XN06 button_button__T34Lr button_l__mm_bi button_appearance-secondary__VUFHU link_button___108l styles_link__0RbL4 styles_loadMoreLanguages__wonXg"]')))
        all_review_button.click()
        logger.info("Clicked all reviews button")
        time.sleep(2)
    except Exception as e:
        logger.info("All reviews button not found or not clickable: {}".format(e))

    while True:
        reviews = extract_reviews_with_bs(driver, company_name, company_link, phone_num, avg_rating, Source_Name, source, category, cursor, table_name)
        all_reviews.extend(reviews)

        try:
            if is_pagination_visible(driver) and is_pagination_button_interactable(driver):
                logger.info("Pagination button found and interactable. Clicking it.")
                try:
                    pagination_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[@name='pagination-button-next']")))
                    
                    # Scroll to the pagination button to ensure it's in view
                    driver.execute_script("arguments[0].scrollIntoView(true);", pagination_button)

                    # Attempt to click using JavaScript
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
                    # Optionally save a screenshot for debugging
                    driver.save_screenshot('pagination_error.png')
                    break
            else:
                logger.info("No more pages to paginate.")
                break
        except Exception as e:
            logger.info("No more pages found or an error occurred: {}".format(e))
            break

    return all_reviews

connection = None
cursor = None

try:
    connection = mysql.connector.connect(**mysql_config)
    cursor = connection.cursor()
    logger.info("Connected to MySQL database.")

    create_table(cursor, table_name)

    for name, link in links:
        logger.info(f"Opening link for: {name}")

        driver.get(link)
        try:
            wait.until(EC.presence_of_element_located((By.XPATH, '//section[@class="styles_reviewsContainer__3_GQw"]')))
            logger.info("Reviews section loaded.")

            phone_num = "N/A"
            try:
                phone_num = driver.find_element(By.XPATH, '//address/ul/li[2]/a').text
                logger.info(f"Phone number found: {phone_num}")
            except Exception as e:
                logger.info("Phone number not found.")

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

            reviews = handle_pagination(driver, name, link, phone_num, avg_rating, source_name, source, category, cursor, table_name)

            for review in reviews:
                insert_review_data(cursor, table_name, review)
            
            connection.commit()

        except Exception as e:
            logger.error(f"Error processing link {link}: {e}")
            continue

except mysql.connector.Error as err:
    if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
        logger.error("Something is wrong with your user name or password.")
    elif err.errno == errorcode.ER_BAD_DB_ERROR:
        logger.error("Database does not exist.")
    else:
        logger.error(err)
finally:
    if cursor:
        cursor.close()
    if connection:
        connection.close()
    logger.info("MySQL connection closed.")
    driver.quit()
