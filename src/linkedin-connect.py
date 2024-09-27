'''
-----------------------------------------------------------------------
File: src/linkedin-connect.py
Creation Time: Sep 26th 2024, 3:22 pm
Author: Saurabh Zinjad
Developer Email: saurabhzinjad@gmail.com
Copyright (c) 2023-2024 Saurabh Zinjad. All rights reserved | https://github.com/Ztrimus
-----------------------------------------------------------------------
'''

import os
import time
import itertools
from screeninfo import get_monitors
from playwright.sync_api import sync_playwright, Page
from typing import List, Dict

# Constants
SLEEP_TIME = 0.5
MAX_SCROLL_ATTEMPTS = 10

def measure_execution_time(func):
    def wrapper(*args, **kwargs):
        print(f"Start Function {func.__name__}")
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        print(f"END: Function {func.__name__} took {execution_time:.4f} seconds to execute")
        return result
    return wrapper

@measure_execution_time
def login(page):
    page.goto('https://www.linkedin.com')
    page.click('a.nav__button-secondary')
    page.fill('#username', os.environ['LINKEDIN_EMAIL'])
    page.fill('#password', os.environ['LINKEDIN_PASSWORD'])
    page.click('button[type="submit"]')
    # page.wait_for_load_state('networkidle')

def scroll_to_bottom(page):
    prev_height = page.evaluate('document.body.scrollHeight')
    for _ in range(MAX_SCROLL_ATTEMPTS):
        page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
        time.sleep(SLEEP_TIME)
        new_height = page.evaluate('document.body.scrollHeight')
        if new_height == prev_height:
            break
        prev_height = new_height

import json
import os

def get_visited_linkedin_profiles() -> set:
    file_path = 'src/visited-linkedin-profiles.json'
    if not os.path.exists(file_path):
        return set()
    
    with open(file_path, 'r', encoding='utf-8') as f:
        try:
            data = json.load(f)
            return set(data.get("visited_profiles", []))
        except json.JSONDecodeError:
            return set()

def set_visited_linkedin_profile(profile_url: str) -> None:
    file_path = 'src/visited-linkedin-profiles.json'
    visited_profiles = get_visited_linkedin_profiles()
    visited_profiles.add(profile_url)
    
    data = {"visited_profiles": list(visited_profiles)}
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

def connect_with_note(page):
    note = "Hi, I'm interested in connecting with you to expand my professional network. Looking forward to potential collaborations!"
    page.fill('textarea[name="message"]', note)
    page.click('button[aria-label="Send now"]')

def send_without_note(page, profile_url: str = ''):
    # Wait for the "Send without a note" option to appear
        send_without_note = page.get_by_role("button", name="Send without a note").first
        if send_without_note:
            send_without_note.click()
            print(f"Successfully sent connection request to {profile_url}")
            set_visited_linkedin_profile(profile_url)
            return True
        else:
            print(f"'Send without a note' option not found for {profile_url}")
            return False

def connect_with_profile(page: Page, profile_url: str, timeout: int = 10000):
    try:
        page.goto(profile_url)

        # Check for the main "Connect" button
        connect_button = page.query_selector('button[aria-label^="Invite"][class*="artdeco-button--primary"][class*="pvs-profile-actions__action"]')
        
        if connect_button:
            connect_button.click()
        else:
            # If main "Connect" button not found, try the "More" button
            more_button = page.query_selector('button[aria-label="More actions"]')
            
            if more_button:
                page.evaluate("(button) => button.click()", more_button)
                page.wait_for_selector('.artdeco-dropdown__content--is-open', state='visible', timeout=timeout)
                connect_option = page.query_selector('div.artdeco-dropdown__content--is-open div[aria-label^="Invite"][role="button"]')

                if connect_option:
                    connect_option.click()
                else:
                    print(f"Couldn't find Connect option for {profile_url}")
                    return False
            else:
                print(f"Couldn't find Connect or More button for {profile_url}")
                return False

        # Wait for the "Send without a note" option to appear
        send_without_note(page, profile_url)

    except Exception as e:
        print(f"An error occurred while connecting with {profile_url}: {str(e)}")
        return False

def process_person(page, card):
    button_text = card.locator('button span').first.inner_text().lower()
    profile_link = card.locator('a.app-aware-link[href^="https://www.linkedin.com/in/"]').first
    profile_url = profile_link.get_attribute('href').split('?')[0] if profile_link else None
    visited_profiles = get_visited_linkedin_profiles()

    if profile_url not in visited_profiles:
        if button_text == "connect":
            card.locator('button').click()
            send_without_note(page, profile_url)
        elif button_text == "pending":
            return
        elif button_text in ["message", "follow"]:
            if profile_url:
                connect_with_profile(page, profile_url)
            page.go_back()
        set_visited_linkedin_profile(profile_url)

def generate_parameter_combinations(params):
    # Get all possible values for each parameter
    param_values = [
        [(key, value) for value in values.values()]
        for key, values in params.items()
    ]

    # Generate all combinations
    combinations = itertools.product(*param_values)

    # Format each combination as a URL parameter string
    formatted_combinations = [
        "&".join(f"{key}={value}" for key, value in combo)
        for combo in combinations
    ]

    return formatted_combinations

def process_company(page, company: str, params: Dict[str, str]):
    base_url = f"https://www.linkedin.com/company/{company}/people/"

    query_combinations = generate_parameter_combinations(params)

    for query_params in query_combinations:
        url = f"{base_url}?{query_params}"
        
        page.goto(url)
        scroll_to_bottom(page)
        
        people_cards = page.locator('.org-people-profile-card')
        for i in range(people_cards.count()):
            process_person(page, people_cards.nth(i))

def  get_company_params():
    # TODO: Currently considering all 3 params, also write for single or double params i.e. facetGeoRegion=103644278&facetCurrentFunction=12
    company_params= {
        "facetGeoRegion": {'USA': '103644278', 'India': '102713980'},
        "facetSchool": {'PICT': '2445691', 'ASU': '4292'},
        "facetCurrentFunction": {'Engineering': '8', 'HR': '12', 'Project Management': '20', 'IT': '13', 'Research': '24'}
    }

    return company_params

def get_company_list():
    company_list = ["doordash", "uber", "lyft"]  # Add more companies as needed

    return company_list

@measure_execution_time
def main():
    company_list = get_company_list()
    params = get_company_params()

    with sync_playwright() as p:
        # Get the screen size of the primary monitor
        monitor = get_monitors()[0]
        width = monitor.width
        height = monitor.height
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(viewport={'width': width, 'height': height}, color_scheme='dark')
        page = context.new_page()
        
        try:
            login(page)
            for company in company_list:
                process_company(page, company, params)
        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            context.close()
            browser.close()

if __name__ == "__main__":
    main()