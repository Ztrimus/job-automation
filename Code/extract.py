'''
-----------------------------------------------------------------------
Author: Saurabh Zinjad
Developer Email: zinjadsaurabh1997@gmail.com
File: extract.py
Creation Time: Oct 31st 2023 1:53 pm
Copyright (c) 2023 Saurabh Zinjad. All rights reserved | GitHub: Ztrimus
-----------------------------------------------------------------------
'''

import requests
from bs4 import BeautifulSoup

def get_text_from_webpage(url):
    # Send a GET request to the URL
    response = requests.get(url)

    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        # Parse the HTML content
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract text content (modify this based on the structure of the webpage)
        text_content = soup.get_text(separator='\n', strip=True)

        return text_content
    else:
        print(f"Failed to retrieve the webpage. Status code: {response.status_code}")
        return None

# Example usage
url = "https://www.linkedin.com/jobs/search/?currentJobId=3709577773&distance=25&geoId=103644278&keywords=Computer%20Science%20Summer%20Intern&origin=JOBS_HOME_SEARCH_CARDS"
webpage_text = get_text_from_webpage(url)

if webpage_text:
    print(webpage_text)
