import csv
import logging
import time
import sys
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, ElementNotInteractableException, StaleElementReferenceException
import os


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()
webdriver_path = os.getenv(WEBDRIVER)


if len(sys.argv) < 5:
    logger.error("CSV file path not provided.")
    sys.exit(1)
csv_input_file_path = sys.argv[1]
source_name = sys.argv[2]
source = sys.argv[3]
category = sys.argv[4]


chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=1920x1080")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--remote-debugging-port=9222")
service = Service(webdriver_path)
driver = webdriver.Chrome(service=service, options=chrome_options)


def read_csv(file_path):
    with open(file_path, mode='r') as file:
        csv_reader = csv.reader(file)
        next(csv_reader)  
        return list(csv_reader)


wait = WebDriverWait(driver, 2)

def get_location(driver):
    try:
        location_element = driver.find_element(By.XPATH, '//div[@class="RcCsl fVHpi w4vB1d NOE9ve M0S7ae AG25L "]/button[contains(@aria-label,"Address")]')
        driver.execute_script("arguments[0].scrollIntoView();", location_element)
        location = location_element.find_element(By.XPATH, './/div[@class="Io6YTe fontBodyMedium kR99db "]').text
        return location if location else "N/A"
    except NoSuchElementException:
        return "N/A"

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

def extract_reviews(driver, company_name, company_link, phone_num, avg_rating, source_name, source, category):
    reviews_data = []
    try:
        wait = WebDriverWait(driver, 2)
        
     
        wait.until(EC.presence_of_all_elements_located((By.XPATH, '//div[@class="jftiEf fontBodyMedium "]')))

        
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        review_elements = soup.find_all('div', class_='jftiEf fontBodyMedium')

        for review in review_elements:
            try:
                review_star_elem = review.find('span', class_='kvMYJc')
                review_star = review_star_elem['aria-label'].split()[0] if review_star_elem else "N/A"
                logger.info(f"Review Star is {review_star}")
                if int(review_star) < 4:
                    reviewer_name_elem = review.find('div', class_='d4r55')
                    reviewer_name = reviewer_name_elem.text if reviewer_name_elem else "N/A"
                    logger.info(f"Reviewer name is {reviewer_name}")
                    
                    review_date_elem = review.find('span', class_='rsqaWe')
                    review_date = review_date_elem.text if review_date_elem else "N/A"
                    logger.info(f"Review date is {review_date}")
                    
                    review_description_elem = review.find('span', class_='wiI7pd')
                    review_description = review_description_elem.text if review_description_elem else "N/A"
                    logger.info(f"Review description: {review_description}")

                    reviews_data.append((company_name, company_link, reviewer_name, review_date, review_star, review_description, phone_num, avg_rating, source_name, source, category))
                else:
                    return reviews_data

            except AttributeError as e:
                logger.error(f"Error finding sub-elements in review: {e}")
            except Exception as e:
                logger.error(f"Unexpected error during sub-element extraction: {e}")

        logger.info(f"Extracted {len(reviews_data)} reviews.")
    except TimeoutException as e:
        logger.error(f"Timeout while waiting for review elements: {e}")
    except Exception as e:
        logger.error(f"Unexpected error during review extraction: {e}")
    
    return reviews_data


def click_reviews_button(driver, max_retries=3, wait_time=1):
    retries = 0
    while retries < max_retries:
        try:
            
            reviews_button = WebDriverWait(driver, wait_time).until(
                EC.element_to_be_clickable((By.XPATH, '//div[@class="RWPxGd"]/button[contains(@aria-label,"Reviews")]'))
            )
            driver.execute_script("arguments[0].scrollIntoView();", reviews_button)
            # time.sleep(2)  
            driver.execute_script("arguments[0].click();", reviews_button)
            logger.info("Clicked on the reviews button.")
            return True
        except (NoSuchElementException, TimeoutException, ElementNotInteractableException) as e:
            logger.error(f"Error clicking the reviews button on attempt {retries + 1}: {e}")
            retries += 1
            time.sleep(wait_time)
        except Exception as e:
            logger.error(f"Unexpected error on attempt {retries + 1}: {e}")
            retries += 1
            time.sleep(wait_time)
    return False


def scroll_to_end(driver):
    retry_count = 0
    max_retries = 8
    num = 0

    while retry_count < max_retries:
        try:
            scrollable_div = driver.find_element(By.XPATH, '//div[@class="m6QErb XiKgde "]')
            last_height = driver.execute_script("return arguments[0].scrollHeight", scrollable_div)
            
            while True:
                driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", scrollable_div)
                num += 1
                driver.find_element(By.XPATH, '//div[@class="m6QErb DxyBCb kA9KIf dS8AEf XiKgde "]').send_keys(Keys.PAGE_DOWN)
                logger.info("Scrolling ....")
                time.sleep(0.7)
                driver.find_element(By.XPATH, '//div[@class="m6QErb DxyBCb kA9KIf dS8AEf XiKgde "]').send_keys(Keys.PAGE_DOWN)
                logger.info("Scrolling ....")
                time.sleep(.7)
                driver.find_element(By.XPATH, '//div[@class="m6QErb DxyBCb kA9KIf dS8AEf XiKgde "]').send_keys(Keys.PAGE_DOWN)
                logger.info("Scrolling ....")
                time.sleep(0.7)
                driver.find_element(By.XPATH, '//div[@class="m6QErb DxyBCb kA9KIf dS8AEf XiKgde "]').send_keys(Keys.PAGE_DOWN)
                logger.info("Scrolling ....")
                time.sleep(0.7)
                driver.find_element(By.XPATH, '//div[@class="m6QErb DxyBCb kA9KIf dS8AEf XiKgde "]').send_keys(Keys.PAGE_DOWN)
                logger.info("Scrolling ....")
                time.sleep(.7)
                driver.find_element(By.XPATH, '//div[@class="m6QErb DxyBCb kA9KIf dS8AEf XiKgde "]').send_keys(Keys.PAGE_DOWN)
                logger.info("Scrolling ....")
                time.sleep(.7)
                driver.find_element(By.XPATH, '//div[@class="m6QErb DxyBCb kA9KIf dS8AEf XiKgde "]').send_keys(Keys.PAGE_DOWN)
                logger.info("Scrolling ....")
                time.sleep(.7)
                driver.find_element(By.XPATH, '//div[@class="m6QErb DxyBCb kA9KIf dS8AEf XiKgde "]').send_keys(Keys.PAGE_DOWN)
                logger.info("Scrolling ....")
                time.sleep(.7)
                driver.find_element(By.XPATH, '//div[@class="m6QErb DxyBCb kA9KIf dS8AEf XiKgde "]').send_keys(Keys.PAGE_DOWN)
                logger.info("Scrolling ....")
                time.sleep(.7)
                driver.find_element(By.XPATH, '//div[@class="m6QErb DxyBCb kA9KIf dS8AEf XiKgde "]').send_keys(Keys.PAGE_DOWN)
                logger.info("Scrolling ....")
                time.sleep(.7)
                driver.find_element(By.XPATH, '//div[@class="m6QErb DxyBCb kA9KIf dS8AEf XiKgde "]').send_keys(Keys.PAGE_DOWN)
                logger.info("Scrolling ....")
                time.sleep(.7)
                driver.find_element(By.XPATH, '//div[@class="m6QErb DxyBCb kA9KIf dS8AEf XiKgde "]').send_keys(Keys.PAGE_DOWN)
                logger.info("Scrolling ....")
                time.sleep(.7)
                driver.find_element(By.XPATH, '//div[@class="m6QErb DxyBCb kA9KIf dS8AEf XiKgde "]').send_keys(Keys.PAGE_DOWN)
                logger.info("Scrolling ....")
                time.sleep(.7)
                driver.find_element(By.XPATH, '//div[@class="m6QErb DxyBCb kA9KIf dS8AEf XiKgde "]').send_keys(Keys.PAGE_DOWN)
                logger.info("Scrolling ....")
                time.sleep(.7)
                driver.find_element(By.XPATH, '//div[@class="m6QErb DxyBCb kA9KIf dS8AEf XiKgde "]').send_keys(Keys.PAGE_DOWN)
                logger.info("Scrolling ....")
                time.sleep(.7)
                driver.find_element(By.XPATH, '//div[@class="m6QErb DxyBCb kA9KIf dS8AEf XiKgde "]').send_keys(Keys.PAGE_DOWN)
                logger.info("Scrolling ....")
                time.sleep(.7)
                driver.find_element(By.XPATH, '//div[@class="m6QErb DxyBCb kA9KIf dS8AEf XiKgde "]').send_keys(Keys.PAGE_DOWN)
                logger.info("Scrolling ....")
                time.sleep(2)
            
                new_height = driver.execute_script("return arguments[0].scrollHeight", scrollable_div)

                logger.info(f"Scrolled {num} times and sleeping.")
                time.sleep(2)

                review_elements = wait.until(EC.presence_of_all_elements_located((By.XPATH, '//div[@class="jftiEf fontBodyMedium "]')))
                for review in review_elements:
                    try:
                        review_star_elem = review.find_element(By.XPATH, './/span[@class="kvMYJc"]').get_attribute('aria-label')
                        review_star = review_star_elem.split()[0] if review_star_elem else "N/A"
                        logger.info(f"Review Star is {review_star}")
                        if int(review_star) > 3:
                            logger.info("Comes greater than 3 star review, Break the scrolling loop")
                            return 
                    except (NoSuchElementException, TimeoutException, ElementNotInteractableException, Exception) as e:
                        logger.error(f"did not get into the review star element: {e}")
                 
                if new_height == last_height:
                    logger.info("Reached the end of the results.")
                    break
                last_height = new_height

            logger.info("Successfully scrolled to end.")
            return True                                         
        except NoSuchElementException:
            retry_count += 1
            logger.error(f"Scroll container not found. Retrying {retry_count}/{max_retries}...")
            time.sleep(.7)                                      
            continue

        except Exception as e:
            retry_count += 1
            logger.error(f"Error scrolling: Retrying {retry_count}/{max_retries}...")
            time.sleep(.7)
            

    if retry_count == max_retries:
        logger.error("Failed to find the scrollable container after maximum retries.")
        return False  
    return False  


def click_lowest_rating(driver, max_retries=3, delay=2):
    retries = 0
    while retries < max_retries:
        try:
            
            sort_button = WebDriverWait(driver, 2).until(
                EC.presence_of_element_located((By.XPATH, '//button[@aria-label="Sort reviews"]'))
            )
            sort_button.click()
            logger.info("Clicked the sort button.")
            
            
            lowest_rating_option = WebDriverWait(driver, 2).until(
                EC.presence_of_element_located((By.XPATH, '//div[@id="action-menu"]//div[@role="menuitemradio" and .//div[text()="Lowest rating"]]'))
            )
            lowest_rating_option.click()
            logger.info("Selected the 'Lowest rating' option.")
            return True
        except (NoSuchElementException, TimeoutException, ElementNotInteractableException, Exception) as e:
            logger.error(f"Error selecting 'Lowest rating' option on attempt {retries + 1} ...")
            retries += 1
            time.sleep(delay)  
        except StaleElementReferenceException:
            logger.warning("StaleElementReferenceException encountered. Retrying...")
            retries += 1
            time.sleep(delay) 
            

    return False


def process_company_link(driver, name, link, source_name, source, category):
    driver.get(link)
    try:
        wait = WebDriverWait(driver, 1)
        wait.until(EC.presence_of_element_located((By.XPATH, '//div[@class="m6QErb WNBkOb XiKgde " and @role="main"]')))
        logger.info("Reviews section loaded.")
        time.sleep(0.7)

        location = get_location(driver)
        logger.info(f"Location is {location}")
        if location != "N/A":
            splited_loc = (location.split(","))
            if len(splited_loc) == 3:
                city = splited_loc[1]
            elif len(splited_loc) > 3:
                city = splited_loc[2]
        logger.info(f"City is {city}")

        phone_num = get_phone_number(driver)
        logger.info(f"Phone number is {phone_num}")

        avg_rating = get_average_rating(driver)
        logger.info(f"Average rating is {avg_rating}")

        if phone_num == "N/A":
            return

        clicked = click_reviews_button(driver)

        if not clicked:
            logger.error("Failed to click the reviews button.")
            return


        clicked_lowest = click_lowest_rating(driver)
        if not clicked_lowest:
            logger.error("Failed to click the 'Lowest rating' option.")
            return
        
        scroll_to_end(driver)

        reviews_data = extract_reviews(driver, name, link, phone_num, avg_rating, source_name, source, category)
        for review_data in reviews_data:
            print(review_data)
        logging.info(f"Total review scrapped {len(reviews_data)}")
        
        logger.info(f"Processed link: {link}")

    except TimeoutException:
        logger.error("Timed out waiting for the reviews section to load.")
    except Exception as e:
        logger.error(f"Error processing link {link}: {e}")


def main():
    company_links = read_csv(csv_input_file_path)
    for row in company_links:
        name, link = row[0], row[1]
        logger.info(f"Oppening link of {name}")
        process_company_link(driver, name, link, source_name, source, category)

    driver.quit()

if __name__ == "__main__":
    main()
