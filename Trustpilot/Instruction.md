
# Web Scraping Script Setup and Execution

## Required Packages and Libraries

To run the web scraping script(Details.py), you need to install the following packages and libraries:

1. `csv`
2. `logging`
3. `time`
4. `sys`
5. `os`
6. `selenium`
7. `beautifulsoup4`
8. `requests`

## Installation Steps

1. **Install Python**: Ensure you have Python installed. You can download it from [python.org](https://www.python.org/downloads/).

2. **Install Required Packages**: Use `pip` to install the necessary packages. Run the following commands in your terminal:

    ```sh
    pip install selenium
    pip install beautifulsoup4
    pip install requests
    ```

## Script Setup

1. **Download the ChromeDriver**: Download the ChromeDriver that matches your version of Chrome from [ChromeDriver Downloads](https://sites.google.com/a/chromium.org/chromedriver/downloads).

2. **Update WebDriver Path**: Update the `webdriver_path` variable in the script to point to the location of the ChromeDriver on your machine:

    ```python
    webdriver_path = '/path/to/chromedriver'  # Update this path
    ```

3. **Update CSV Input File Path**: Ensure that the CSV input file path provided as the first command-line argument is correct.

## Running the Script

1. **Save the Script**: Save the script as `details.py`.

2. **Run the Script**: Open your terminal and run the script with the necessary arguments. For example:

    ```sh
    python details.py <path_to_csv_file> <source_name> <source_website> <company_category>
    ```

    Replace `<path_to_csv_file>`, `<source_name>`, `<source_website>`, and `<company_category>` with the actual values.

---

## URL.PY
This is the helping script. In urls.py it will scrape the search result and then save as csv and then will run details.py.
But if you already have csv file and want to run details.py you can just run url.py with providing the web driver path, csv file path and details.py path.
And aditionaly you have to change manually thte source name, category.

