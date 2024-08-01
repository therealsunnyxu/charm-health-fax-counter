import tkinter as tk
from tkinter import ttk
from fax_counter.scraper.page_models import HomePageModel
from fax_counter.scraper.edge_driver_manager import EdgeDriverManager
from fax_counter.scraper.fax_scraper import FaxScraper
from fax_counter.utilities import ReportUtilities
from fax_counter.ui.main_window import MainWindow
from fax_counter.name_corrector import NameCorrector
import pandas as pd
import os
import time
from threading import Thread, Event
import queue
import datetime


class App:
    def __init__(self):
        self.app = MainWindow()
        self.import_frame = self.app.import_frame
        self.export_frame = self.app.export_frame
        self.loading_frame = self.app.loading_frame
        self.import_done = tk.BooleanVar()
        self.scraping_done = tk.BooleanVar()
        self.export_done = tk.BooleanVar()
        self.app.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.work_queue: queue.Queue[bool] = queue.Queue()
        self.update_message_queue: queue.Queue[str] = queue.Queue()
        self.stop_event = Event()
        self.scraper_thread = Thread(
            target=self.scrape_faxes,
            args=(
                self.work_queue,
                self.update_message_queue,
            ),
            daemon=True,
        )
        self.dataframes = {}

    def import_data(self):
        self.app.title("Import Names Spreadsheet")

        def on_import_submit():
            if self.import_frame.submit_file():
                self.import_done.set(True)

        self.import_frame.submit_button.config(command=on_import_submit)
        self.import_frame.instruction.config(
            text="Press Browse to import a spreadsheet of first and last names, then press Submit."
        )

        self.app.update()
        self.app.wait_variable(self.import_done)

    def procedure(self):
        # Custom procedure that can be overridden
        self.app.title("Scraping Faxes")
        self.app.show_loading_frame()
        self.update_loading_message("Starting the scraping process...")

        self.scraper_thread.start()
        self.check_work_queue()
        self.app.wait_variable(self.scraping_done)

        local_files_path = os.path.join(os.getcwd(), "files")
        sent_path = os.path.join(local_files_path, "sent.csv")
        sent_df = pd.read_csv(sent_path)
        received_path = os.path.join(local_files_path, "received.csv")
        received_df = pd.read_csv(received_path)
        combined_df = ReportUtilities.combine_reports([sent_df, received_df])
        cost_report = ReportUtilities.calculate_cost_per_patient(combined_df)
        today = datetime.datetime.strftime(datetime.datetime.today(), "%m-%d-%Y")
        self.dataframes = {
            f"Sent Faxes as of {today}.csv": sent_df,
            f"Received Faxes as of {today}.csv": received_df,
            f"Combined Sent and Received Faxes as of {today}.csv": combined_df,
            f"Fax Cost Report as of {today}.xlsx": cost_report,
        }

        self.loading_frame.progress.destroy()
        prog = tk.IntVar()
        self.loading_frame.progress = ttk.Progressbar(
            self.loading_frame, mode="determinate", variable=prog
        )
        self.loading_frame.progress.pack(fill="x", pady=10)

        self.update_loading_message("Finished! Continuing to export menu...")

        self.loading_frame.start_progress()
        for i in range(99):
            prog.set(i)
            time.sleep(0.01)
            self.app.update()
        prog.set(99.9)
        self.app.update()
        time.sleep(0.1)
        self.loading_frame.stop_progress()

        self.app.hide_loading_frame()

    def update_loading_message(self, message):
        self.loading_frame.update_message(message)
        self.app.update()

    def export_data(self, dataframes):
        self.app.title("Export Scraped Data")

        def on_export_submit():
            if self.export_frame.submit_file():
                self.export_done.set(True)

        self.export_frame.add_dfs(dataframes)
        self.export_frame.submit_button.config(command=on_export_submit)
        self.export_frame.instruction.config(
            text="Press Browse to choose a directory to save the output files, then press Export."
        )

        self.app.update()
        self.app.wait_variable(self.export_done)

    def run(self):
        try:
            self.import_data()
            self.procedure()
            self.app.show_export_frame()
            self.export_data(self.dataframes)
        except tk.TclError:
            print("Forcibly closing the program.")

    def on_closing(self):
        print("Attempting to stop program...")
        self.stop_event.set()
        if self.scraper_thread.is_alive():
            self.scraper_thread.join(1)
        try:
            self.app.destroy()
        except tk.TclError:
            print("Forcibly closing the program.")

        self.scraping_done.set(True)
        self.import_done.set(True)
        self.export_done.set(True)
        EdgeDriverManager.force_quit_edge()

    def check_work_queue(self):
        try:
            message = self.work_queue.get_nowait()
            self.scraping_done.set(message)
            self.app.after(100, self.check_work_queue)
            self.loading_frame.progress.stop()
        except queue.Empty:
            pass

        try:
            update_message = self.update_message_queue.get_nowait()
            if update_message:
                self.update_loading_message(update_message)
        except queue.Empty:
            pass

        if not self.scraping_done.get():
            self.app.after(100, self.check_work_queue)
            self.loading_frame.progress.start(10)

    def scrape_faxes(
        self, work_queue: queue.Queue[bool], update_message_queue: queue.Queue[str]
    ):
        fax_scraper = FaxScraper()
        try:
            fax_scraper.start()
            name_df = self.import_frame.df
            name_df = NameCorrector.correct_names(name_df)

            print("Microsoft Edge started...")
            local_files_path = os.path.join(os.getcwd(), "files")
            home_page: HomePageModel = fax_scraper.navigate_to_home_page()
            lock_screen_visible = home_page.is_page_locked()
            if lock_screen_visible:
                update_message_queue.put(
                    "Lock screen detected. Please login to the session."
                )
                lock_screen_visible = home_page.wait_until_page_unlocked()
                update_message_queue.put("Session unlocked. Continuing program...")

            update_message_queue.put("Scraping sent faxes...")
            faxes_page = fax_scraper.navigate_to_sent_faxes_page()
            fax_scraper.log_faxes_and_save(faxes_page, local_files_path, "sent.csv")
            time.sleep(1)

            update_message_queue.put("Scraping received faxes...")
            faxes_page = fax_scraper.navigate_to_received_faxes_page()
            fax_scraper.log_faxes_and_save(faxes_page, local_files_path, "received.csv")
            time.sleep(1)

            update_message_queue.put("Categorizing faxes...")
            sent_path = os.path.join(local_files_path, "sent.csv")
            sent_df = pd.read_csv(sent_path)
            sent_df = fax_scraper.get_name_and_page_counts(sent_df, name_df)

            received_path = os.path.join(local_files_path, "received.csv")
            received_df = pd.read_csv(received_path)
            received_df = fax_scraper.get_name_and_page_counts(received_df, name_df)

            update_message_queue.put("Preparing data for export...")
            sent_df.to_csv(sent_path, index=False)
            # update_message_queue.put("Saved sent faxes to:", sent_path)
            received_df.to_csv(received_path, index=False)
            # update_message_queue.put("Saved received faxes to:", received_path)

        except Exception:
            if self.stop_event.is_set():
                fax_scraper.stop()
        finally:
            fax_scraper.stop()
            pass

        work_queue.put(True)
        pass


# Example usage:
if __name__ == "__main__":
    app = App()
    export_dir = os.path.join(os.getcwd(), "files")
    sent_path = os.path.join(export_dir, "sent.csv")
    received_path = os.path.join(export_dir, "received.csv")

    app.run()
    app.on_closing()
    # quit()
