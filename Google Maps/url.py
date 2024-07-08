# Call details.py with the CSV file path
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
webdriver_path = os.getenv("WEBDRIVER_PATH")
category = 'Burger'
location = 'Berlin'
source = 'https://www.google.com/maps'
source_name = "Google"
csv_file_path = os.getenv("CSV_FILE_PATH_for_google")
python_executable = sys.executable  # This gets the currently running Python executable
try:
    subprocess.run([python_executable, os.getenv("DETAIL_PATH_for_google") , csv_file_path, source_name, source, category], check=True)
    print(f"details.py executed successfully with {csv_file_path}")
except subprocess.CalledProcessError as e:
    print(f"Error calling details.py: {e}")
