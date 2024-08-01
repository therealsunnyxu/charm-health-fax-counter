import tkinter as tk
from fax_counter.ui.ui_frames import ImportFrame, ExportFrame
from fax_counter.ui.ui_frames import LoadingFrame
import pandas as pd


class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()

        self.import_frame = ImportFrame(self)
        self.export_frame = ExportFrame(self)
        self.loading_frame = LoadingFrame(self)

        self.import_frame.pack(fill="both", expand=True)
        self.export_frame.pack_forget()
        self.loading_frame.pack_forget()

        self.import_frame.submit_button.config(command=self.show_export_frame)

    def show_export_frame(self):
        self.import_frame.pack_forget()
        self.export_frame.pack(fill="both", expand=True)
        self.export_frame.submit_button.config(command=self.destroy)

    def show_loading_frame(self):
        self.import_frame.pack_forget()
        self.export_frame.pack_forget()
        self.loading_frame.pack(fill="both", expand=True)

    def hide_loading_frame(self):
        self.loading_frame.stop_progress()
        self.loading_frame.pack_forget()
