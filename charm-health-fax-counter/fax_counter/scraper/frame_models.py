from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import pandas as pd
from fax_counter.utilities import *
from typing import Union
from typing import List


class FaxTableFrameModel:
    def __init__(self, driver: Union[webdriver.Chrome, webdriver.Edge], wait=5):
        self.wait = WebDriverWait(driver, wait)

        self.driver = driver

        self.patient_col_index = None
        self.title_col_index = None
        self.date_col_index = None
        self.set_column_indices()

        self.df = self.create_dataframe()

    def set_column_indices(self):
        tr_children_count = self.driver.execute_script(
            "return document.evaluate("
            "'count(//div[@id=\"tableHeader\"]/table/thead/tr/*)', "
            "document, null, XPathResult.NUMBER_TYPE, null).numberValue;"
        )

        headers = []
        for i in range(1, tr_children_count + 1):
            th = self.driver.execute_script(
                "evaluation = document.evaluate("
                f"'//div[@id=\"tableHeader\"]/table/thead/tr/th[position()={i}]', "
                "document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;"
                "if (evaluation) {"
                "return evaluation.textContent;"
                '}; return "";'
            )
            text = ""
            if th:
                text = th
            headers.append(text)

        for i, th in enumerate(headers):
            if "Patient" in th:
                self.patient_col_index = i
            elif "Title" in th or "Subject" in th:
                self.title_col_index = i
            elif "Date" in th:
                self.date_col_index = i

    def get_messages_list_div(self):
        return self.wait.until(
            EC.presence_of_element_located((By.ID, "messagesListDiv"))
        )

    def create_dataframe(self):
        table_rows = self.get_row_ids()
        data = []
        for row_id in table_rows:
            row_data = self.get_row_data(row_id)
            data.append(row_data)
        return pd.DataFrame(data, columns=["Patient", "Title", "Date", "URL", "Pages"])

    def get_row_data(self, row_id: str):
        indices = [self.patient_col_index, self.title_col_index, self.date_col_index]
        xpath = f'//tr[@id="{row_id}"]/*'
        script_result: List[str] = self.driver.execute_script(
            f"indices = {indices};"
            f"tdpath = '{xpath}';"
            "snapshot = document.evaluate(tdpath, document, null, XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null);"
            "data = [];"
            "for (let i = 0, length = indices.length; i < length; ++i) {"
            "   curr_element = snapshot.snapshotItem(indices[i]);"
            "   text = '';"
            "   if (curr_element) {"
            "       text = curr_element.textContent;"
            "   };"
            "   data.push(text);"
            "};"
            "return data;"
        )
        for x in range(len(indices) - 1):
            script_result[x] = DataUtilities.sanitize(script_result[x])
        script_result.append("")
        script_result.append("")
        return script_result

    def get_row_ids(self):
        xpath = '//div[@id="messagesListDiv"]/table/tbody/*'
        script_result = self.driver.execute_script(
            f"var trpath = '{xpath}';"
            "var snapshot = document.evaluate(trpath, document, null, XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null);"
            "var ids = [];"
            "for (let i = 0, length = snapshot.snapshotLength; i < length; ++i) {"
            "   ids.push(snapshot.snapshotItem(i).id);};"
            "return ids;"
        )
        return script_result


class FaxDetailsFrameModel:
    def __init__(self, driver: webdriver.Chrome, wait=1):
        self.wait = WebDriverWait(driver, wait)
        self.driver = driver

    def get_file_name(self):
        file_link_existence = self.wait.until(
            EC.text_to_be_present_in_element_attribute(
                (By.ID, "dateDiv"), "onclick", "showPDF"
            )
        )
        if not file_link_existence:
            return

        def get_onclick_value():
            return self.wait.until(EC.presence_of_element_located((By.ID, "dateDiv")))

        file_link = ChromiumUtilities.retry_sel_cmd(get_onclick_value())
        return file_link
