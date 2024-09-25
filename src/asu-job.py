import os
import re
import time

from zlm import AutoApplyModel
from playwright.sync_api import sync_playwright

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
def auto_apply(job_content: str):
    job_llm = AutoApplyModel(api_key="os", provider="openai", downloads_dir=os.path.abspath('./output'))
    user_data = job_llm.user_data_extraction(user_data_path='src/user-profile.json')
    job_details, jd_path = job_llm.job_details_extraction(job_site_content=job_content)

    resume_path, resume_details = job_llm.resume_builder(job_details, user_data)
    # resume_path = "/Users/saurabh/Documents/Resume/Resume-Saurabh-Zinjad.pdf"
    cover_letter, cv_path = job_llm.cover_letter_generator(job_details, user_data)

    return cv_path, resume_path

def get_visited_ids() -> set:
    with open('src/visited_job_ids.txt', 'r', encoding='utf-8') as f:
        content = f.read()
        content = content.strip(',')
        if content == '':
            return set()
        else:
            return set(content.split(','))

def set_visited_id(id: str) -> set:
    with open('src/visited_job_ids.txt', 'a', encoding='utf-8') as f:
        f.write(f'{id},')

if __name__ == '__main__':
    applied_job = 0
    visited_ids = get_visited_ids()
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False)
        try:
            context = browser.new_context(viewport={'width': 1920, 'height': 1080}, color_scheme='dark')

            # login
            webpage = context.new_page()
            webpage.goto('https://weblogin.asu.edu/cas/login')

            webpage.fill('input[name=username]', 'szinjad')
            webpage.fill('input[name=password]', os.environ['ASURITE_PWD'])
            webpage.click('input[type=submit]')
            webpage.wait_for_load_state('load')

            webpage.goto('https://students.asu.edu/employment/search')
            webpage.get_by_role("link", name="Search on-campus jobs").click()
            is_remove_cv = False

            webpage.get_by_role("button", name="Yes, this is my device").click()
            

            # remove overloaded resume and cv
            if is_remove_cv:
                webpage.get_by_role("link", name="Candidate Zone").locator("span").click()
                webpage.query_selector(f'#jobProfile').click()
                webpage.query_selector(f'#czMyFilesTab').click()

                while webpage.get_by_role("link", name="Remove").first.is_visible():
                    webpage.get_by_role("link", name="Remove").first.click()
                    webpage.locator(f'.deleteFileDialog').locator(".primaryButton").first.click()
                
                webpage.get_by_role("link", name="Job search").locator("span").click()

            webpage.fill('input[name=keyWordSearch]', 'Python')
            # webpage.fill('input[name=keyWordSearch]', 'Engineering')
            # webpage.fill('input[name=keyWordSearch]', 'Grader')
            webpage.get_by_role("button", name="Search").click()
            time.sleep(SLEEP_TIME)

            while True:
                try:
                    list_locator = webpage.locator('li.job.baseColorPalette.ng-scope')
                    count = list_locator.count()

                    job_id  = ''
                    is_link_clicked = False
                    for i in range(count):
                        job_id = list_locator.nth(i).locator('p.jobProperty.position3').last.text_content()
                        if job_id not in visited_ids:
                                webpage.query_selector(f'#Job_{i}').click()
                                is_link_clicked = True
                                time.sleep(SLEEP_TIME)
                                break
                    
                    if not is_link_clicked:
                        webpage.locator('.showMoreJobs').last.click()
                        continue

                    while webpage.get_by_role("button", name="View your applications").is_visible():
                        job_id = webpage.locator('p[class="answer ng-scope position3InJobDetails"]').last.text_content()
                        if job_id.strip() != '':
                            set_visited_id(job_id)
                            visited_ids.add(job_id)
                        webpage.get_by_role("link", name="Next Job").last.click()
                        time.sleep(SLEEP_TIME)
                    
                    # page_next = webpage.get_by_role("link", name="Next Job")
                    time.sleep(SLEEP_TIME)
                    web_content = re.sub(r'\s+', ' ', webpage.text_content('.jobDetailsLiner.mainDetails')).strip()
                    print(f"\n========================\n {applied_job+1} : {web_content[:75]}\n========================\n")

                    cv_path, resume_path = auto_apply(web_content)

                    webpage.get_by_role("button", name="Apply to job").click()
                    webpage.get_by_role("button", name="Let's get started").click()
                    webpage.get_by_role("button", name="Save and continue").click()
                    webpage.get_by_role("group", name="Are you currently eligible to work in the United States without ASU sponsorship?").get_by_label("Yes").check()
                    webpage.get_by_role("group", name="Are you eligible for Federal Work Study?").get_by_label("No").check()
                    webpage.get_by_role("listbox", name="How did you find out about this job? Choose...").locator("span").first.click()
                    webpage.get_by_role("option", name="Searching ASU Website").get_by_text("Searching ASU Website").click()
                    webpage.get_by_role("button", name="Save and continue").click()

                    webpage.get_by_role("link", name="requiredRésumé/CV Add résumé/CV").click()
                    webpage.frame_locator("#profileBuilder").get_by_label("Browse to upload a file from local storage").set_input_files(resume_path)
                    time.sleep(SLEEP_TIME)
                    
                    webpage.get_by_role("link", name="requiredCover Letter Add cover letter").click()
                    webpage.frame_locator("#profileBuilder").get_by_label("Browse to upload a file from local storage").set_input_files(cv_path)
                    time.sleep(SLEEP_TIME)

                    webpage.get_by_role("button", name="Save and continue").click()
                    webpage.get_by_role("link", name="Add file").click()
                    webpage.frame_locator("iframe[title=\"Add documents for Supporting Documentation\"]").get_by_role("button", name="Upload files from Saved Files").click()
                    webpage.frame_locator("iframe[title=\"Add documents for Supporting Documentation\"]").get_by_label("LOR turuk maam.pdf").check()
                    webpage.frame_locator("iframe[title=\"Add documents for Supporting Documentation\"]").get_by_label("LOR-Dinesh-Sir.pdf").check()
                    webpage.frame_locator("iframe[title=\"Add documents for Supporting Documentation\"]").get_by_label("LOR-Bansod-Sir.pdf").check()
                    webpage.frame_locator("iframe[title=\"Add documents for Supporting Documentation\"]").get_by_label("Server-side Development with NodeJS, Express.pdf").check()
                    webpage.frame_locator("iframe[title=\"Add documents for Supporting Documentation\"]").get_by_label("Omdena Certificate_Dryad_Saurabh Zinjad.pdf").check()
                    webpage.frame_locator("iframe[title=\"Add documents for Supporting Documentation\"]").get_by_label("Microsoft Azure Fundmentals Certificate.pdf").check()
                    webpage.frame_locator("iframe[title=\"Add documents for Supporting Documentation\"]").get_by_label("Front-End Web UI Frameworks and Tools.pdf").check()
                    webpage.frame_locator("iframe[title=\"Add documents for Supporting Documentation\"]").get_by_label("Certificate-MLOps-for-AI-Engineers-and-Data-Scientists.png").check()
                    webpage.frame_locator("iframe[title=\"Add documents for Supporting Documentation\"]").get_by_label("Deep Learning Specializations.pdf").check()
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
                    # page_next.click()
                    webpage.get_by_role("link", name="Job search").click()
                    webpage.get_by_role("button", name="Search").click()
                    time.sleep(SLEEP_TIME)
                    applied_job += 1
                    if job_id.strip() != '':
                        set_visited_id(job_id)
                        visited_ids.add(job_id)
                    
                except Exception as e:
                    print(e)
                    break

        except Exception as e:
            print(e)

        finally:
            context.close()
            browser.close()