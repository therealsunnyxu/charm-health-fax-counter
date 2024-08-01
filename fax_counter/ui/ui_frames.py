import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from tkcalendar import DateEntry
from fax_counter.utilities import *
import pandas as pd
import os
from typing import Union


class BaseBrowseFrame(tk.Frame):
    def __init__(self, parent: Union[tk.Tk, tk.Toplevel]):
        super().__init__(parent)
        self.parent = parent

        self.file_label = tk.Label(self, text="File Name:")
        self.file_label.grid(row=0, column=0, padx=(16, 8), pady=(16, 8), sticky="w")

        self.file_entry = tk.Entry(self)
        self.file_entry.grid(
            row=0, column=1, padx=(8, 8), pady=(16, 8), columnspan=3, sticky="ew"
        )

        self.browse_button = tk.Button(self, text="Browse", command=self.browse_file)
        self.browse_button.grid(
            row=0, column=4, padx=(16, 16), pady=(16, 8), columnspan=2, sticky="ew"
        )

        self.instruction = tk.Label(self, text="", wraplength=400)
        self.instruction.grid(
            row=1, column=0, padx=(16, 8), pady=(8, 16), columnspan=4, sticky="ew"
        )

        self.submit_button = tk.Button(
            self, text="", state="disabled", command=self.submit_file
        )
        self.submit_button.grid(row=1, column=4, padx=(16, 8), pady=(8, 16))

        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=1)
        self.grid_columnconfigure(3, weight=1)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=0)
        self.pack(fill="both", expand=True)

        self.parent.update_idletasks()
        self.parent.minsize(self.winfo_reqwidth(), self.winfo_reqheight())

    def browse_file(self):
        raise NotImplementedError("Subclass must implement abstract method")

    def submit_file(self) -> bool:
        raise NotImplementedError("Subclass must implement abstract method")


class ImportFrame(BaseBrowseFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.instruction.config(
            text="Press Browse to import a spreadsheet of first and last names, then press Submit."
        )
        self.submit_button.config(text="Submit")
        self.df = None

    def browse_file(self):
        file_name = filedialog.askopenfilename()
        self.file_entry.delete(0, tk.END)
        self.file_entry.insert(0, file_name)
        self.submit_button.config(state="normal")  # enable submit button

    def submit_file(self) -> bool:
        try:
            self.df = DataUtilities.import_spreadsheet(self.file_entry.get())
            columns_lower = [str(column).lower() for column in self.df.columns]
            if (
                "firstname" not in columns_lower and "first name" not in columns_lower
            ) or ("lastname" not in columns_lower and "last name" not in columns_lower):
                raise IOError(
                    "The spreadsheet is missing first name and last name columns!"
                )
            messagebox.showinfo("Success", "File successfully imported!")
            return True
        except IOError as e:
            messagebox.showerror("Error", str(e))
            return False


class ExportFrame(BaseBrowseFrame):
    def __init__(self, parent):
        super().__init__(parent)

        self.file_label.grid(row=3, column=0, padx=(16, 8), pady=(16, 8), sticky="w")
        self.file_entry.grid(
            row=3, column=1, padx=(8, 8), pady=(16, 8), columnspan=3, sticky="ew"
        )
        self.browse_button.grid(
            row=3, column=4, padx=(16, 16), pady=(16, 8), columnspan=2, sticky="ew"
        )
        self.instruction.grid(
            row=4, column=0, padx=(16, 8), pady=(8, 16), columnspan=4, sticky="ew"
        )
        self.submit_button.grid(row=4, column=4, padx=(16, 8), pady=(8, 16))

        self.date_frame = FilterDateFrame(self)
        self.date_frame.grid(
            row=0, column=0, padx=(16, 8), pady=(8, 16), columnspan=5, sticky="ew"
        )
        self.grid_rowconfigure(2, weight=0)
        self.grid_rowconfigure(3, weight=0)
        self.grid_rowconfigure(4, weight=0)

        self.separator = ttk.Separator(self, orient="horizontal")
        self.separator.grid(
            row=1, column=0, columnspan=5, padx=(16, 8), pady=(8, 8), sticky="ew"
        )

        self.instruction2 = tk.Label(
            self,
            text="After filtering the dates, choose a location to save the reports.",
        )
        self.instruction2.grid(
            row=2, column=0, padx=(16, 8), pady=(8, 8), columnspan=5, sticky="ew"
        )

        self.export_dfs: dict[str, pd.DataFrame] = {}
        self.export_dir = ""
        self.instruction.config(
            text="Press Browse to choose a directory to save the output files, then press Export."
        )
        self.submit_button.config(text="Export")

    def add_df(self, df: pd.DataFrame, file_name: str):
        self.export_dfs[file_name] = df

    def add_dfs(self, dict_of_dfs: dict[str, pd.DataFrame]):
        for index, key in dict_of_dfs.items():
            self.add_df(key, index)

    def browse_file(self):
        directory = filedialog.askdirectory()
        self.file_entry.delete(0, tk.END)
        self.file_entry.insert(0, directory)
        if directory:
            self.submit_button.config(state="normal")  # enable submit button

    def submit_file(self) -> bool:
        try:
            for key, df in self.export_dfs.items():
                new_key = key if key.endswith(".csv") or ".xls" in key else f"{key}.csv"
                self.export_dir = self.file_entry.get()
                if ".xls" in new_key:
                    df.to_excel(os.path.join(self.export_dir, new_key), index=False)
                else:
                    df.to_csv(os.path.join(self.export_dir, new_key), index=False)
            messagebox.showinfo("Success", "Files successfully exported!")
            return True
        except IOError as e:
            messagebox.showerror("Error", str(e))
            return False


class LoadingFrame(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.label = tk.Label(self, text="Loading...")
        self.label.pack(pady=10)
        self.progress = ttk.Progressbar(self, mode="indeterminate")
        self.progress.pack(fill="x", pady=10)

    def update_message(self, message):
        self.label.config(text=message)

    def start_progress(self):
        self.progress.start()

    def stop_progress(self):
        self.progress.stop()


class DatePickerFrame(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        # Create a date entry field which automatically comes with a button to open a calendar frame
        self.date_picker: tk.Entry = DateEntry(
            self, date_pattern="MM/DD/YYYY", locale="en_US"
        )

        # Bind validation to every key press
        self.date_picker.bind("<KeyRelease>", self._auto_validate_date)
        self.date_picker.pack(pady=10, fill="x")

    def _auto_validate_date(self, event):
        # Get the contents of the date entry and the input character
        date_str = self.date_picker.get()
        len_date_str = len(date_str)
        input_char = str(event.char)

        if len(input_char) == 0:
            # The input character is not a character
            return
        if not input_char.isnumeric():
            # The input character is not a number
            # Delete the input
            self.date_picker.delete(len_date_str - 1, len_date_str + 2)
            return

        # Check the length of the date string and add slashes accordingly
        match len_date_str:
            case 2:
                # User filled out MM in date
                self.date_picker.insert(3, "/")
            case 5:
                # User filled out YYYY in date
                self.date_picker.insert(6, "/")
            case _:
                pass


class FilterDateFrame(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.instruction_label = ttk.Label(
            self,
            text="Filter the final report to include only the faxes between the start and end dates, inclusive.\n\n"
            "Type in the dates in each box using MM/DD/YYYY format, or press on the up carat to choose a date.\n",
        )
        self.instruction_label.grid(
            row=0, column=0, columnspan=2, padx=(16, 16), pady=(8, 8), sticky="ew"
        )
        self.separator = ttk.Separator(self, orient="horizontal")
        self.separator.grid(row=1, column=0, columnspan=2, sticky="ew")

        self.start_label = ttk.Label(self, text="Start Date:")
        self.start_label.grid(row=2, column=0, padx=(16, 16), pady=(8, 0), sticky="ew")
        self.end_label = ttk.Label(
            self,
            text="End Date:",
        )
        self.end_label.grid(row=2, column=1, padx=(16, 16), pady=(8, 0), sticky="ew")

        self.start_date_frame = DatePickerFrame(self)
        self.start_date_frame.grid(
            row=3, column=0, padx=(16, 16), pady=(0, 8), sticky="ew"
        )

        self.end_date_frame = DatePickerFrame(self)
        self.end_date_frame.grid(
            row=3, column=1, padx=(16, 16), pady=(0, 8), sticky="ew"
        )
