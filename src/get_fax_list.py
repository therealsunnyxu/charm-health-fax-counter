"""
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options 
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv
import os
import time
import string

# Load the .env file
load_dotenv("src\.env")

username = os.getenv("APP_USERNAME")
password = os.getenv("APP_PASSWORD")

chrome_options = Options()
chrome_options.add_experimental_option("detach", True)
# Create a new instance of the Chrome driver
driver = webdriver.Chrome(options=chrome_options)

# Navigate to the webpage
driver.get("https://accounts.charmtracker.com/signin?hide_signup=true&hide_secure=true&hide_gsignup=true&servicename=charmhealth&serviceurl=https%3A%2F%2Fehr2.charmtracker.com%2Fehr%2Fmain.do")

# Find the input element using its ID and type "example" into it
input_element = driver.find_element(By.ID, "login_id")
input_element.send_keys(username)

# Find the button element using its ID and click on it
button_element = driver.find_element(By.ID, "nextbtn")
button_element.click()

time.sleep(1)

# Find the password input element using its ID and type "example" into it
password_element = driver.find_element(By.ID, "password")
password_element.send_keys(password)
# Find the button element with the ID "nextbtn" and click on it again
button_element = driver.find_element(By.ID, "nextbtn")
button_element.click()

time.sleep(5)

# Assuming 'driver' is an instance of WebDriver
element = driver.find_element(By.CLASS_NAME, "messages-menu-icon")
for _ in range(3):
    element = element.find_element(By.XPATH, "..")

element.click()

time.sleep(3)

received_element = driver.find_element(By.ID, "FAX_RECEIVED")
received_element.click()

time.sleep(3)

current_faxes_list = driver.find_element(By.ID, "messagesListDiv").find_element(By.TAG_NAME, "table").find_element(By.TAG_NAME, "tbody").find_elements(By.TAG_NAME, "tr")

fax_row_items = []
for faxes in current_faxes_list:
    fax_row = []
    fax_elements = faxes.find_elements(By.TAG_NAME, "td")
    fax_elements[1].click()
    fax_row = [div.text.translate(str.maketrans('', '', string.punctuation)) for div in fax_elements[2:5]]
    fax_row.append("")
    file_tab = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "FAXDetails")))
    file_link = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "dateDiv")))
    try:
        fax_row[-1] = file_link.get_attribute("onclick").replace("showPDF(\'","").replace("\');","")
    except:
        file_link = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "dateDiv")))
        fax_row[-1] = file_link.get_attribute("onclick")

    print(fax_row)


"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options 
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import selenium.common.exceptions
from dotenv import load_dotenv
import os
import time
import string
import pandas as pd
import numpy as np

def execute_with_retry(function_chain, max_loops=50):
    attempts = 0

    while attempts < max_loops:
        try:
            return function_chain()
        except selenium.common.exceptions.StaleElementReferenceException:
            attempts += 1
            #print(f"Attempt {attempts}/{max_loops} failed with StaleElementReferenceException. Retrying...")
        except selenium.common.exceptions.TimeoutException:
            attempts += 1
        except Exception as e:
            break

    return None

load_dotenv("src\.env")
facility_id = os.getenv("FACILITY_ID")

chrome_options = Options()
chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")

driver = webdriver.Chrome(options=chrome_options)

# Interact with the existing session
driver.get("https://ehr2.charmtracker.com/ehr/messagesAction.do?ACTION=FETCH_ALL_MESSAGES&FACILITY_ID=" + facility_id)

received_element = driver.find_element(By.ID, "FAX_RECEIVED")
received_element.click()

time.sleep(3)

fax_row_items = []

def long_fax_counter():
    try:
        while True:
            # Get the faxes on the current page
            try:
                current_faxes_list = execute_with_retry(lambda: driver.find_element(By.ID, "messagesListDiv").find_element(By.TAG_NAME, "table").find_element(By.TAG_NAME, "tbody").find_elements(By.TAG_NAME, "tr"))
                len_list, counter = len(current_faxes_list), 0
                while counter < len_list:
                    fax_row = []
                    fax = current_faxes_list[counter]
                    fax_elements = execute_with_retry(lambda: fax.find_elements(By.TAG_NAME, "td"), max_loops=2)
                    if fax_elements:
                        execute_with_retry(lambda: fax_elements[1].click(), max_loops=2)
                        for i in range(2,5):
                            div = execute_with_retry(lambda: fax_elements[i], max_loops=2)
                            div_text = execute_with_retry(lambda: div.text, max_loops=2)
                            sanitized_text = ""
                            if div_text:
                                sanitized_text = div_text.translate(str.maketrans('', '', string.punctuation))
                            fax_row.append(sanitized_text)
                        file_link = execute_with_retry(lambda: WebDriverWait(driver, 1).until(EC.presence_of_element_located((By.ID, "dateDiv"))), max_loops=10)
                        file_name = execute_with_retry(lambda: file_link.get_attribute("onclick"))
                        correct_file_name = ""
                        if file_name:
                            correct_file_name = file_name.replace("showPDF(\'","").replace("\');","")
                        fax_row.append(correct_file_name)
                        counter += 1
                        fax_row_items.append(fax_row)
                    else:
                        #print("Oopsie")
                        current_faxes_list = execute_with_retry(lambda: driver.find_element(By.ID, "messagesListDiv").find_element(By.TAG_NAME, "table").find_element(By.TAG_NAME, "tbody").find_elements(By.TAG_NAME, "tr"))
                        continue
                #for faxes in current_faxes_list:
                    #fax_row = []
                    #fax_elements = execute_with_retry(lambda: faxes.find_elements(By.TAG_NAME, "td"))
                    #print(len(fax_elements))
                    #execute_with_retry(lambda: fax_elements[1].click())
                
                time.sleep(0.5)
            except IndexError:
                print("No more faxes")
                break
            except Exception as e:
                print("Something went wrong: ", e)
                break

            time.sleep(0.5)
            # attempt to click on the next button until there's no more next buttons
            try:
                file_tab = execute_with_retry(lambda: WebDriverWait(driver, 1).until(EC.presence_of_element_located((By.ID, "FAXDetails"))), max_loops=2)
                if file_tab != None:
                    close_button = execute_with_retry(lambda: file_tab.find_element(By.CLASS_NAME, "v1-pgcls-icon"), max_loops=1)
                    execute_with_retry(lambda: close_button.click(), max_loops=1)
                next_button = execute_with_retry(lambda: WebDriverWait(driver, 1).until(EC.element_to_be_clickable((By.ID, "nextButtonEnable"))))
                next_button_disabled = execute_with_retry(lambda: WebDriverWait(driver, 1).until(EC.presence_of_element_located((By.ID, "nextButtonDisable"))))
                end_of_faxes = execute_with_retry(lambda: next_button_disabled.value_of_css_property('display'))
                if end_of_faxes != 'block':
                    execute_with_retry(lambda: next_button.click())
                else:
                    raise selenium.common.exceptions.TimeoutException()
            except selenium.common.exceptions.TimeoutException as e:
                print("No more faxes to look at.")
                break
            except Exception as e:
                print("Something went wrong:", e)
                break
    except KeyboardInterrupt:
        pass
    finally:
        np_file_list = np.array(fax_row_items)
        columns = ['Patient Name', 'File Name in Chart', 'Date (M DD YYYY HHMM P)', 'File Name in Internal System']
        df_file_list = pd.DataFrame(np_file_list, columns=columns)
        df_file_list.to_csv('faxes.csv')
    
long_fax_counter()