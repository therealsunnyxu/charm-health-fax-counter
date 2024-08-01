from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from fax_counter.scraper.page_models import *  # Correct imports
from fax_counter.scraper.edge_driver_manager import EdgeDriverManager
from fax_counter.scraper.frame_models import *
from fax_counter.utilities import *
from fax_counter.scraper.page_models import *
import time
import os
import pandas as pd
import PyPDF4

HOME_PAGE_URL = "https://ehr2.charmtracker.com"
FAXES_PAGE_URL = (
    "https://ehr2.charmtracker.com/ehr/messagesAction.do?ACTION=FETCH_ALL_MESSAGES"
)
FAX_FILE_URL = (
    "https://ehr2.charmtracker.com/ehr/physician/fax.do?ACTION=SHOW_PDF&FILE_ID="
)


class FaxScraper:
    _instance = None

    def __init__(self):
        self.edge_driver_manager = EdgeDriverManager()
        self.driver = None

    def start(self):
        self.edge_driver_manager.start()
        self.driver = self.edge_driver_manager.get_driver()

    def stop(self):
        self.edge_driver_manager.stop()

    def navigate_to_home_page(self):
        home_page = HomePageModel(self.driver)
        self.driver.get(HOME_PAGE_URL)
        return home_page

    def navigate_to_received_faxes_page(self) -> FaxesPageModel:
        # Navigate to MessagesPage
        messages_page = self.navigate_to_home_page().navigate_to_messages_page()
        if FAXES_PAGE_URL not in self.driver.current_url:
            raise Exception("Failed to navigate to MessagesPage.")

        # Navigate to Received Faxes Page
        faxes_page = messages_page.navigate_to_faxes_page("RECEIVED")
        if FAXES_PAGE_URL not in self.driver.current_url:
            raise Exception("Failed to navigate to Received Faxes page.")
        if not isinstance(faxes_page, FaxesPageModel):
            raise Exception("Navigation did not return a FaxesPage instance.")
        return faxes_page

    def navigate_to_sent_faxes_page(self) -> FaxesPageModel:
        # Navigate to MessagesPage
        messages_page = self.navigate_to_home_page().navigate_to_messages_page()
        if FAXES_PAGE_URL not in self.driver.current_url:
            raise Exception("Failed to navigate to MessagesPage.")

        # Navigate to Sent Faxes Page
        faxes_page = messages_page.navigate_to_faxes_page("SENT")
        if FAXES_PAGE_URL not in self.driver.current_url:
            raise Exception("Failed to navigate to Sent Faxes page.")
        if not isinstance(faxes_page, FaxesPageModel):
            raise Exception("Navigation did not return a FaxesPage instance.")
        return faxes_page

    def scrape_faxes_data(self, faxes_page: FaxesPageModel) -> pd.DataFrame:
        # Verify the current page is a FaxTableFrame and contains data
        dfs = []
        next_page_exists = True
        time.sleep(5)
        current_page = faxes_page.get_current_page()
        while next_page_exists:
            row_ids = current_page.get_row_ids()
            file_names = []
            for row_id in row_ids:
                row = faxes_page.wait.until(
                    EC.presence_of_element_located((By.ID, row_id))
                )
                row_date: WebElement = row.find_elements(By.TAG_NAME, "td")[
                    current_page.date_col_index
                ]
                if row_date is None:
                    raise Exception("Row should have a date field.")
                row_date.click()

                file_name_func = lambda: (
                    faxes_page.wait.until(
                        EC.presence_of_element_located((By.ID, "dateDiv"))
                    )
                    .get_attribute("onclick")
                    .replace("showPDF('", "")
                    .replace("');", "")
                )

                file_name = ChromiumUtilities.retry_sel_cmd(file_name_func)
                text = ""
                if file_name:
                    text = FAX_FILE_URL + file_name
                else:
                    print(
                        "Could not retrieve fax details from message with id:", row_id
                    )
                file_names.append(text)

            current_page.df["URL"] = pd.Series(file_names)
            dfs.append(current_page.df)

            next_page = faxes_page.get_next_page()
            if next_page is None:
                next_page_exists = False
            else:
                current_page = next_page

        big_df = pd.concat(dfs, ignore_index=True)
        print(len(big_df), "faxes scraped.")
        return big_df

    def temp_download_pdfs(self, df: pd.DataFrame):
        print("Saving faxes to disk...")
        for url in df["URL"]:
            if not url:
                continue

            file_name = self.get_abbreviated_file_name(url)
            pdf_path = os.path.join(self.edge_driver_manager.download_dir, file_name)

            if not os.path.exists(pdf_path):
                time.sleep(0.1)
                self.driver.get(url)

    def get_abbreviated_file_name(self, long_file_name: str) -> str:
        return (
            str(long_file_name).replace(FAX_FILE_URL, "").split("!->")[0]
            if FAX_FILE_URL in str(long_file_name)
            else str(long_file_name)
        )

    def read_length_of_pdf(self, pdf_url: str) -> int:
        file_name = self.get_abbreviated_file_name(pdf_url)
        full_file_name = os.path.join(self.edge_driver_manager.download_dir, file_name)

        num_pages = 0
        try:
            with open(full_file_name, "rb") as file:
                reader = PyPDF4.PdfFileReader(file)
                num_pages = reader.getNumPages()
        except Exception as e:
            print("Skipping", file_name, "because:", e)
        return num_pages

    def get_page_counts(self, df: pd.DataFrame) -> pd.DataFrame:
        df_copy = df.copy()

        for index, row in df_copy.iterrows():
            file_name = row["URL"]
            page_index = df_copy.columns.get_loc("Pages")
            df_copy.iloc[index, page_index] = self.read_length_of_pdf(file_name)

        return df_copy

    def get_patient_names_from_file_names(
        self, df: pd.DataFrame, name_list: pd.DataFrame
    ) -> pd.DataFrame:
        df_copy: pd.DataFrame = df.copy()
        name_list_lower = name_list.copy()
        for col in name_list_lower.columns:
            name_list_lower[col] = name_list_lower[col].map(lambda x: str(x).lower())
        last_names = name_list_lower["LastName"].unique()
        last_name_index = pd.Index(last_names)

        sorted_names: pd.DataFrame = name_list_lower.sort_values(
            by="LastName", axis="rows"
        )
        first_names_group = (
            sorted_names.groupby(["LastName", "FirstName"], as_index=False)
            .size()
            .reset_index()[["LastName", "FirstName"]]
        )

        for index, row in df_copy[
            df_copy["Patient"].isnull() | df_copy["Patient"].str.endswith("yeehaw")
        ].iterrows():
            file_name = row["Title"]
            name_index = df_copy.columns.get_loc("Patient")
            patient_name = NameUtilities.get_patient_name_from_file_name(
                file_name, last_name_index, first_names_group
            )
            patient_name_string = "/".join([patient for patient in patient_name])
            df_copy.iloc[index, name_index] = patient_name_string  # patient_name

        return df_copy

    def log_faxes_and_save(
        self, faxes_page: FaxesPageModel, output_dir: str, output_file_name: str
    ) -> pd.DataFrame:
        output_df = self.scrape_faxes_data(faxes_page)
        self.temp_download_pdfs(output_df)
        output_path = os.path.join(output_dir, output_file_name)
        DataUtilities.backup_file(output_path)
        output_df.to_csv(output_path, index=False)
        return output_df

    def get_name_and_page_counts(
        self, input_df: pd.DataFrame, name_df: pd.DataFrame
    ) -> pd.DataFrame:
        print("Counting pages...")
        temp_df = self.get_page_counts(input_df)
        print("Assigning patient names based on file name...")
        temp_df = self.get_patient_names_from_file_names(temp_df, name_df)
        return temp_df


# Example usage
if __name__ == "__main__":
    fax_logger = FaxScraper()
    fax_logger.start()
    print("Microsoft Edge started...")
    local_files_path = os.path.join(os.getcwd(), "files")
    try:
        print("Scraping sent faxes...")
        faxes_page = fax_logger.navigate_to_sent_faxes_page()
        fax_logger.log_faxes_and_save(faxes_page, local_files_path, "sent.csv")
        time.sleep(1)

        print("Scraping received faxes...")
        faxes_page = fax_logger.navigate_to_received_faxes_page()
        fax_logger.log_faxes_and_save(faxes_page, local_files_path, "received.csv")
        time.sleep(1)

        print("Finished scraping faxes. Starting categorization...")
        name_df = pd.read_csv(
            os.path.join(local_files_path, "PatientsDetails_11Jun2024.csv")
        )
        sent_path = os.path.join(local_files_path, "sent.csv")
        sent_df = pd.read_csv(sent_path)
        sent_df = fax_logger.get_name_and_page_counts(sent_df, name_df)

        received_path = os.path.join(local_files_path, "received.csv")
        received_df = pd.read_csv(received_path)
        received_df = fax_logger.get_name_and_page_counts(received_df, name_df)

        print("Saving data to disk...")
        sent_df.to_csv(sent_path, index=False)
        print("Saved sent faxes to:", sent_path)
        received_df.to_csv(received_path, index=False)
        print("Saved received faxes to:", received_path)

    finally:
        fax_logger.stop()
        pass
