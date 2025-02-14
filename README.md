# Web Automation for 8 Websites  
*(Google Maps, Trustpilot, YellowPages, Yelp, Jameda.de)*  

## 📌 About This Repository  
This repository contains Python-based web scraping automation scripts designed to extract business data from multiple websites, including **Google Maps, Trustpilot, YellowPages, Yelp, and Jameda.de**.  

The automation is built using **Selenium** (with Chromedriver) for handling page navigation and **BeautifulSoup** to speed up the scraping process.  

## 🚀 Features  
✅ **Automated Search & Scraping**: The script starts by performing a category-based search on the target websites.  
✅ **Multi-Step Workflow**:  
1. **Category Selection**: Uses `categorie.json` to determine the categories for the search.  
2. **URL Scraping**: The script navigates through search results and collects URLs (`urls.py`).  
3. **Detail Extraction**: Each URL is visited, and business details are scraped (`details.py`).  
✅ **Seamless Page Handling**: Selenium efficiently navigates through paginated results.  
✅ **Data Optimization**: BeautifulSoup is used for faster parsing and extraction.  

## 🛠️ Tech Stack  
- **Python** 🐍  
- **Selenium** (for browser automation)  
- **Chromedriver** (for controlling Chrome)  
- **BeautifulSoup** (for HTML parsing)  
- **JSON** (to manage categories and store results)  

## 📂 Project Structure  
```plaintext
Web_automation_8websites/
│── categorie.json    # Categories for search  
│── urls.py           # Scrapes URLs from search results  
│── details.py        # Extracts business details  
│── requirements.txt  # Required dependencies  
│── README.md         # Project documentation  
│── /data             # Stores scraped results (if applicable)
```

## 🏁 How It Works  
1️⃣ **Define Categories**: Modify `categorie.json` to add/remove search categories.  
2️⃣ **Run `urls.py`**: Scrapes URLs from search results across multiple pages.  
3️⃣ **Run `details.py`**: Visits each URL and extracts business details.  
4️⃣ **Data Collection**: The extracted data can be stored in JSON, CSV, or a database.  

## 📌 Usage  
```bash
pip install -r requirements.txt  # Install dependencies
python urls.py                    # Start URL scraping
python details.py                  # Extract business details
```
## 📢 Note  
- Ensure **Chromedriver** is installed and matches your Chrome version.  
- Adjust Selenium wait times for optimal performance based on website speed.  
- Some websites may require **proxy rotation** or **CAPTCHA handling** for large-scale scraping.  

## 📜 License  
This project is intended for **educational purposes**. Ensure compliance with website **terms of service** before scraping.  
