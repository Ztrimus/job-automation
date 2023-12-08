import os
import re
import sys
import time

from zlm import AutoApplyModel
from multiprocessing import Process
from playwright.sync_api import Playwright, sync_playwright

SLEEP_TIME = 2

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

def old_click(page, s):
    page.click(s)
    page.wait_for_load_state('load')

@measure_execution_time
def download_resume(job_llm, job_details, user_data):
    job_llm.resume_builder(job_details, user_data)

@measure_execution_time
def download_cv(job_llm, job_details, user_data):
    job_llm.cover_letter_generator(job_details, user_data)

@measure_execution_time
def auto_apply(job_content: str):
    job_llm = AutoApplyModel(os.environ['OPENAI_API_KEY'], os.path.abspath('./'))
    user_data = job_llm.user_data_extraction('src/zlm/demo_data/user_profile.json')
    job_details = job_llm.job_details_extraction(job_content)
    
    p_resume = Process(target = download_resume, args=(job_llm, job_details, user_data))
    p_cv = Process(target = download_cv, args=(job_llm, job_details, user_data))
    
    p_resume.start()
    p_cv.start()

@measure_execution_time
def autofill(webpage: any):
    webpage.get_by_role("button", name="Apply to job").click()
    webpage.get_by_role("button", name="Let's get started").click()
    webpage.get_by_role("button", name="Save and continue").click()
    webpage.get_by_role("group", name="Are you currently eligible to work in the United States without ASU sponsorship?").get_by_label("Yes").check()
    webpage.get_by_role("group", name="Are you eligible for Federal Work Study?").get_by_label("Yes").check()
    webpage.get_by_role("listbox", name="How did you find out about this job? Choose...").locator("span").first.click()
    webpage.get_by_role("option", name="Searching ASU Website").get_by_text("Searching ASU Website").click()
    webpage.get_by_role("button", name="Save and continue").click()
    webpage.get_by_role("link", name="requiredRésumé/CV Add résumé/CV").click()
    webpage.frame_locator("iframe[title=\"Add résumé\\/CV\"]").get_by_role("button", name="Upload a file from Saved résumés/CVs").click()
    webpage.frame_locator("iframe[title=\"Add résumé\\/CV\"]").get_by_label("Resume_Saurabh_Zinjad+.pdf").check()
    webpage.frame_locator("iframe[title=\"Add résumé\\/CV\"]").get_by_role("button", name="Add file").click()
    webpage.get_by_role("link", name="requiredCover Letter Add cover letter").click()
    webpage.frame_locator("iframe[title=\"Add Cover Letter\"]").get_by_role("button", name="Upload a file from Saved cover letters").click()
    webpage.frame_locator("iframe[title=\"Add Cover Letter\"]").get_by_label("Cover_letter_Saurabh_Zinjad+.pdf").check()
    webpage.frame_locator("iframe[title=\"Add Cover Letter\"]").get_by_role("button", name="Add file").click()
    webpage.get_by_role("button", name="Save and continue").click()
    webpage.get_by_role("link", name="Add file").click()
    webpage.frame_locator("iframe[title=\"Add documents for Supporting Documentation\"]").get_by_role("button", name="Upload files from Saved Files").click()
    webpage.frame_locator("iframe[title=\"Add documents for Supporting Documentation\"]").get_by_label("ASU-SOP.pdf").check()
    webpage.frame_locator("iframe[title=\"Add documents for Supporting Documentation\"]").get_by_label("LOR turuk maam.pdf").check()
    webpage.frame_locator("iframe[title=\"Add documents for Supporting Documentation\"]").get_by_label("LOR-Dinesh-Sir.pdf").check()
    webpage.frame_locator("iframe[title=\"Add documents for Supporting Documentation\"]").get_by_label("LOR-Bansod-Sir.pdf").check()
    webpage.frame_locator("iframe[title=\"Add documents for Supporting Documentation\"]").get_by_role("button", name="Add file").click()
    webpage.get_by_role("button", name="Save and continue").click()
    time.sleep(SLEEP_TIME)
    webpage.get_by_role("button", name="Save and continue").click()
    time.sleep(SLEEP_TIME)
    webpage.get_by_role("button", name="Save and continue").click()
    time.sleep(SLEEP_TIME)
    webpage.get_by_role("button", name="Save and continue").click()
    time.sleep(SLEEP_TIME)
    webpage.get_by_role("button", name="Send my application").click()
    time.sleep(SLEEP_TIME)
    webpage.get_by_role("link", name="Job search").click()
    webpage.get_by_role("button", name="Search").click()

    # =========================================================

if __name__ == '__main__':
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False)
        try:
            context = browser.new_context()

            # login
            page = context.new_page()
            page.goto('https://weblogin.asu.edu/cas/login?service=https%3A%2F%2Fweblogin.asu.edu%2Fcgi-bin%2Fcas-login%3Fcallapp%3Dhttps%253A%252F%252Fwebapp4.asu.edu%252Fmyasu%252F%253Finit%253Dfalse')

            page.fill('input[name=username]', 'szinjad')
            page.fill('input[name=password]', os.environ['ASURITE_PWD'])
            page.click('input[type=submit]')
            page.wait_for_load_state('load')
            
            page.get_by_role("link", name="Campus Services").click()
            page.get_by_role("link", name="Student Employment - Job Search").click()
            page.get_by_role("button", name="Search On-Campus Jobs").click()
            page.get_by_role("button", name="Search").click()
            time.sleep(SLEEP_TIME)
            page.query_selector('#Job_0').click()
            # check already applied
            # while page.get_by_role("button", name="View your applications"):
            #     page.get_by_role("link", name="Next Job").click()
            
            web_content = re.sub(r'\s+', ' ', page.text_content('.jobDetailsLiner.mainDetails')).strip()

            p_apply = Process(target = auto_apply, args=(web_content,))
            p_autofill = Process(target = autofill, args=(page,))
            p_apply.start()
            p_autofill.start()

        except Exception as e:
            print(e)

        finally:
            context.close()
            browser.close()