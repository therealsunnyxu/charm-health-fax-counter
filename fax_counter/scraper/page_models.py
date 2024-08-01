from selenium import webdriver
import selenium.common.exceptions as selenium_exceptions
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from fax_counter.utilities import ChromiumUtilities
from fax_counter.scraper.frame_models import *
from typing import Union
import time

# Define the URLs as constants
HOME_PAGE_URL = "https://ehr2.charmtracker.com"
FAXES_PAGE_URL = (
    "https://ehr2.charmtracker.com/ehr/messagesAction.do?ACTION=FETCH_ALL_MESSAGES"
)
FAX_FILE_URL = (
    "https://ehr2.charmtracker.com/ehr/physician/fax.do?ACTION=SHOW_PDF&FILE_ID="
)

# create login page class then have it


class BasePageModel:
    def __init__(self, driver: Union[webdriver.Chrome, webdriver.Edge], wait=1):
        self.driver = driver
        self.wait = WebDriverWait(driver, wait)


class HomePageModel(BasePageModel):
    messages_menu_icon_locator = (By.CLASS_NAME, "messages-menu-icon")
    lock_session_frame_locator = (By.ID, "LockSession")

    def __init__(self, driver, wait=1):
        super().__init__(driver, wait)

    def is_page_locked(self, check_freq_seconds=1):
        lock_frame_visible = False
        while lock_frame_visible == False:
            try:
                self.wait.until(
                    EC.visibility_of_element_located(self.lock_session_frame_locator)
                )
                lock_frame_visible = True
                time.sleep(check_freq_seconds)
            except selenium_exceptions.StaleElementReferenceException:
                continue
            except selenium_exceptions.TimeoutException:
                return True
        return lock_frame_visible

    def is_page_unlocked(self, check_freq_seconds=1):
        lock_frame_visible = True
        while lock_frame_visible == True:
            try:
                self.wait.until_not(
                    EC.visibility_of_element_located(self.lock_session_frame_locator)
                )
                lock_frame_visible = False
                time.sleep(check_freq_seconds)
            except selenium_exceptions.StaleElementReferenceException:
                continue
            except selenium_exceptions.TimeoutException:
                return False
        return lock_frame_visible

    def wait_until_page_locked(self, check_freq_seconds=1):
        lock_frame_visible = False
        while lock_frame_visible == False:
            try:
                self.wait.until(
                    EC.visibility_of_element_located(self.lock_session_frame_locator)
                )
                lock_frame_visible = True
                time.sleep(check_freq_seconds)
            except selenium_exceptions.StaleElementReferenceException:
                continue
            except selenium_exceptions.TimeoutException:
                continue
        return lock_frame_visible

    def wait_until_page_unlocked(self, check_freq_seconds=1):
        lock_frame_visible = True
        while lock_frame_visible == True:
            try:
                self.wait.until_not(
                    EC.visibility_of_element_located(self.lock_session_frame_locator)
                )
                lock_frame_visible = False
                time.sleep(check_freq_seconds)
            except selenium_exceptions.StaleElementReferenceException:
                continue
            except selenium_exceptions.TimeoutException:
                continue
        return lock_frame_visible

    def navigate_to_main_menu(self):
        self.driver.get(HOME_PAGE_URL)

    def navigate_to_messages_page(self):
        self.navigate_to_main_menu()
        self.wait.until(
            EC.element_to_be_clickable((self.messages_menu_icon_locator))
        ).click()
        self.wait.until(EC.url_contains(FAXES_PAGE_URL))
        return MessagesPageModel(self.driver)


class MessagesPageModel(BasePageModel):
    fax_received_locator = (By.ID, "FAX_RECEIVED")
    fax_sent_locator = (By.ID, "FAX_SENT")

    def navigate_to_faxes_page(self, mode):
        menu_element: WebElement = None
        if mode == "RECEIVED":
            menu_element = self._find_element_with_retry(self.fax_received_locator)
        elif mode == "SENT":
            menu_element = self._find_element_with_retry(self.fax_sent_locator)
        menu_element.click()
        return FaxesPageModel(self.driver, mode)

    def _find_element_with_retry(self, locator):
        return ChromiumUtilities.retry_sel_cmd(
            lambda: self.driver.find_element(*locator)
        )


class FaxesPageModel(BasePageModel):
    def __init__(self, driver, mode: str):
        BasePageModel.__init__(self, driver)
        self.current_mode = mode.upper()

    def get_prev_page(self):
        button_locator = (By.ID, "previousButtonEnable")
        button_clicked = ChromiumUtilities.retry_sel_click(self.wait, button_locator)
        if button_clicked == False:
            return None
        time.sleep(0.1)
        return FaxTableFrameModel(self.driver)

    def get_next_page(self):
        button_locator = (By.ID, "nextButtonEnable")
        button_clicked = ChromiumUtilities.retry_sel_click(
            self.wait, button_locator, max_retries=10
        )
        if button_clicked == False:
            return None
        time.sleep(0.1)
        return FaxTableFrameModel(self.driver)

    def get_current_page(self):
        return FaxTableFrameModel(self.driver)
