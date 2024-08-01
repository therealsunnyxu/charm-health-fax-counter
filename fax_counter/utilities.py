import pandas as pd
import string
from datetime import datetime
import os
import selenium.common.exceptions
import string
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from typing import List
import shutil


class NameUtilities:
    @staticmethod
    def find_last_name_matches(file_name: str, name_list: pd.DataFrame) -> list:
        # find last names as exact match by indexing using pd.Index
        last_names = name_list["LastName"].unique()
        last_name_index = pd.Index(last_names)
        words = str(file_name).split()
        last_name_matches = last_name_index.get_indexer(words)
        last_name_matches_list = last_name_matches[last_name_matches != -1]
        return last_name_matches_list

    @staticmethod
    def find_all_first_names(name_list: pd.DataFrame, last_name: str) -> pd.Series:
        return name_list[name_list["LastName"] == last_name]["FirstName"].unique()

    @staticmethod
    def find_first_name_matches(
        file_name: str, name_list: pd.DataFrame, last_name_match: str
    ) -> list:
        # find first names names as exact match by indexing using pd.Index
        first_names = NameUtilities.find_all_first_names(name_list, last_name_match)
        first_name_index = pd.Index(first_names)
        words = str(file_name).split()
        first_name_matches = first_name_index.get_indexer(words)
        first_name_matches_list = first_name_matches[first_name_matches != -1]
        return first_name_matches_list

    @staticmethod
    def find_potential_initials(last_name_index_in_words: int, words: list) -> list:
        # Find potential initials adjacent to the last name
        potential_initials = []
        for i in range(
            max(0, last_name_index_in_words - 1),
            min(len(words), last_name_index_in_words + 2),
        ):
            word = words[i]
            if len(word) == 1:
                potential_initials.append(word)
        return potential_initials

    @staticmethod
    def find_first_name_from_initials(
        first_names: pd.Series, potential_initials: list
    ) -> list:
        # Find the first matching first name from patients who have the last name
        first_name_initials = first_names.apply(lambda x: x[0])
        first_match = first_names[first_name_initials.isin(potential_initials)].tolist()
        return first_match

    @staticmethod
    def capitalize_name(name: str) -> str:
        name = str(name)
        if not name or len(name) <= 0:
            return ""
        if len(name) == 1:
            return name.upper
        return name[0].upper() + name[1:]

    @staticmethod
    def capitalize_full_name(full_name: str) -> str:
        names = full_name.split()
        return " ".join([NameUtilities.capitalize_name(name) for name in names])

    @staticmethod
    def get_adjacent_words(word_list: List[str], index: int, distance: int):
        if not (0 <= index < len(word_list)):
            return [], []

        left_start = max(index - distance, 0)
        left_end = index
        right_start = index + 1
        right_end = min(index + 1 + distance, len(word_list))

        left_items = word_list[left_start:left_end]
        right_items = word_list[right_start:right_end]

        return left_items, right_items

    @staticmethod
    def get_index_of_word_from_list(word_list: List[str], word: str):
        try:
            index = word_list.index(word)
            return index
        except ValueError:
            return -1  # Return -1 or any other value to indicate the word was not found

    @staticmethod
    def get_indices_of_word_from_list(word_list: List[str], word: str):
        words_series = pd.Series(word_list)
        return words_series[words_series == word].index.tolist()

    @staticmethod
    def find_indices_of_last_name_matches(
        file_name: str, name_list: pd.DataFrame
    ) -> list:
        # find last names as exact match by indexing using pd.Index
        last_names = name_list["LastName"].unique()
        last_name_index = pd.Index(last_names)
        words = str(file_name).split()
        last_name_matches = last_name_index.get_indexer(words)
        return last_name_matches

    @staticmethod
    def get_positive_and_adjacent_negative_indices(
        word_list: List[str],
    ) -> tuple[List[int]]:
        n = len(word_list)
        positive_indices = []
        adjacent_negative_indices = []

        for i in range(n):
            if word_list[i] > 0:
                positive_indices.append(i)
            elif word_list[i] == -1:
                # check if adjacent to a positive number
                if (i > 0 and word_list[i - 1] > 0) or (
                    i < n - 1 and word_list[i + 1] > 0
                ):
                    adjacent_negative_indices.append(i)

        return positive_indices, adjacent_negative_indices

    @staticmethod
    def get_patient_name_from_file_name(
        file_name: str, last_name_index: pd.Index, first_names_group: pd.DataFrame
    ) -> set[str]:
        file_name_lower = str(file_name).lower()
        words = str(file_name_lower).split()
        last_name_matches = last_name_index.get_indexer(words)

        last_name_indices, adjacent_word_indices = (
            NameUtilities.get_positive_and_adjacent_negative_indices(last_name_matches)
        )
        found_last_names = [str(words[i]) for i in last_name_indices]
        adjacent_words = [str(words[i]) for i in adjacent_word_indices]
        initials = [i for i in found_last_names + adjacent_words if len(i) == 1]
        # Check if corresponding first names are in the file names
        specific_persons = set()
        for last_name in found_last_names:
            # Get the possible first names for this last name from the DataFrame
            possible_first_names = first_names_group[
                first_names_group["LastName"] == last_name
            ]["FirstName"].values

            found_person = False

            # Check if any of these first names are in the list of adjacent words
            for first_name in possible_first_names:
                if first_name in adjacent_words + found_last_names:
                    specific_persons.add(
                        NameUtilities.capitalize_full_name(
                            " ".join(((first_name, last_name)))
                        )
                    )
                    found_person = True
                    break

            if not found_person:
                # Check if any of the initials match the first initials of the possible first names
                for first_name in possible_first_names:
                    if first_name[0] in initials:
                        specific_persons.add(
                            NameUtilities.capitalize_full_name(
                                " ".join(((first_name, last_name)))
                            )
                        )
                        break

            if not found_person:
                # Check if there is only one first name associated with the last name
                if len(possible_first_names) == 1 and len(found_last_names) == 1:
                    specific_persons.add(
                        NameUtilities.capitalize_full_name(
                            " ".join(((possible_first_names[0], last_name)))
                        )
                    )
                else:
                    # Print just the last name if no first name or initial match is found
                    specific_persons.add(NameUtilities.capitalize_name(last_name))

        if len(specific_persons) > 1:
            specific_persons = set(
                [person for person in specific_persons if len(str(person).split()) > 1]
            )

        return specific_persons


class DataUtilities:
    @staticmethod
    def sanitize(file_name: str):
        return (
            file_name.translate(
                str.maketrans(string.punctuation, " " * len(string.punctuation))
            )
            .replace("[0-9]+", "")
            .strip()
        )

    @staticmethod
    def convert_time_to_excel_format(time_str, old_format="%b %d, %Y %I:%M %p"):
        time_obj = datetime.strptime(time_str, old_format)
        return time_obj.strftime("%m/%d/%Y %I:%M %p")

    @staticmethod
    def import_spreadsheet(file_name):
        if not file_name or len(file_name) <= 0:
            raise IOError("No file name given!")

        if not os.path.exists(file_name):
            raise IOError("File does not exist or is corrupted!")

        file_ext = str(file_name).split(".")[-1]
        match file_ext:
            case "csv":
                return pd.read_csv(file_name)
            case "tsv":
                return pd.read_csv(sep="\t")
            case str(x) if "xls" in x:
                return pd.read_excel(file_name, engine="openpyxl", header=None)
            case _:
                raise IOError(
                    "Wrong file type! File must be a .csv or a Microsoft Excel file extension starting with .xls"
                )

    @staticmethod
    def df_to_dict(df: pd.DataFrame):
        # Convert DataFrame to dictionary of dictionaries
        data = {}
        for i, row in df.iterrows():
            data[str(i)] = {}
            for j, value in row.items():
                data[str(i)][str(j)] = value

        return data

    @staticmethod
    def backup_file(file_path: str) -> bool:
        try:
            backup_name_path = file_path + ".backup"
            if os.path.exists(file_path):
                shutil.copy(file_path, backup_name_path)
                return True
            return False
        except IOError:
            return False
        except Exception:
            return False


class ChromiumUtilities:
    @staticmethod
    def get_chrome_user_dir():
        return os.path.join(os.getenv("LOCALAPPDATA"), "Google", "Chrome", "User Data")

    @staticmethod
    def get_chrome_path():
        # Define the paths for both Program Files and Program Files (x86)
        program_files = os.getenv("ProgramFiles")
        program_files_x86 = os.getenv("ProgramFiles(x86)")

        # Define the expected paths for chrome.exe in both directories
        chrome_path_program_files = os.path.join(
            program_files, "Google", "Chrome", "Application", "chrome.exe"
        )
        chrome_path_program_files_x86 = os.path.join(
            program_files_x86, "Google", "Chrome", "Application", "chrome.exe"
        )

        # Check if chrome.exe exists in Program Files
        if os.path.exists(chrome_path_program_files):
            return chrome_path_program_files
        # If not found, check in Program Files (x86)
        elif os.path.exists(chrome_path_program_files_x86):
            return chrome_path_program_files_x86
        else:
            return None  # Chrome not found in either location

    @staticmethod
    def get_edge_user_dir():
        return os.path.join(os.getenv("LOCALAPPDATA"), "Microsoft", "Edge", "User Data")

    @staticmethod
    def get_edge_path():
        # Define the paths for both Program Files and Program Files (x86)
        program_files_x86 = os.getenv("ProgramFiles(x86)")

        edge_path_program_files_x86 = os.path.join(
            program_files_x86, "Microsoft", "Edge", "Application", "msedge.exe"
        )
        if os.path.exists(edge_path_program_files_x86):
            return edge_path_program_files_x86
        else:
            return None  # Chrome not found in either location

    @staticmethod
    def retry_sel_cmd(func, max_retries=5):
        attempts = 0

        while attempts < max_retries:
            try:
                return func()
            except selenium.common.exceptions.StaleElementReferenceException:
                attempts += 1
            except selenium.common.exceptions.TimeoutException:
                attempts += 1
            except Exception as e:
                break

        return None

    @staticmethod
    def retry_sel_click(
        wait_class: WebDriverWait, locator: tuple[By, str], max_retries=5
    ):
        attempts = 0

        button = None
        while attempts < max_retries and button == None:
            try:
                button = wait_class.until(EC.visibility_of_element_located(locator))
                button = wait_class.until(EC.element_to_be_clickable(locator))
            except selenium.common.exceptions.StaleElementReferenceException:
                attempts += 1
            except selenium.common.exceptions.TimeoutException:
                attempts += 1
            except Exception as e:
                return False

        if button is not None:
            button.click()
            return True

        return False


class ReportUtilities:
    @staticmethod
    def combine_reports(list_dfs: List[pd.DataFrame]):
        return pd.concat(list_dfs)

    @staticmethod
    def calculate_cost_per_patient(
        raw_report: pd.DataFrame,
        cost: float = 0.25,
        date_col: str = "Date",
        name_col: str = "Patient",
        page_col: str = "Pages",
        cost_col: str = "Cost",
    ):
        cloned_report = raw_report.copy()
        cloned_report[date_col] = pd.to_datetime(
            cloned_report[date_col], format="%b %d, %Y %I:%M %p"
        )
        cloned_report = cloned_report[[name_col, date_col, page_col]]
        cloned_report = (
            cloned_report[[name_col, page_col]][name_col].value_counts().reset_index()
        )
        cloned_report[cost_col] = cloned_report["count"].apply(lambda x: x * cost)

        return cloned_report

    @staticmethod
    def filter_report_by_date(
        report_df: pd.DataFrame,
        start_date: datetime,
        end_date: datetime,
        date_col: str = "Date",
    ):
        return report_df[
            (report_df[date_col].dt.date >= start_date)
            & (report_df[date_col].dt.date <= end_date)
        ]
