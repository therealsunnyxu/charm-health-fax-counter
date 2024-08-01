import pandas as pd
import tkinter as tk
from tkintertable import *
from fax_counter.utilities import ChromiumUtilities


class NoDragColumnHeader(ColumnHeader):
    def handle_left_release(self, event):
        """When mouse released implement resize or col move"""

        self.delete("dragrect")
        if self.atdivider == 1:
            # col = self.table.get_col_clicked(event)
            x = int(self.canvasx(event.x))
            col = self.table.currentcol
            x1, y1, x2, y2 = self.table.getCellCoords(0, col)
            newwidth = x - x1
            if newwidth < 5:
                newwidth = 5
            self.table.resizeColumn(col, newwidth)
            self.table.delete("resizeline")
            self.delete("resizeline")
            self.delete("resizesymbol")
            self.atdivider = 0
            return
        self.delete("resizesymbol")
        # move column
        return

    def handle_mouse_drag(self, event):
        """Handle column drag, will be either to resize or select cols"""

        x = int(self.canvasx(event.x))
        if self.atdivider == 1:
            self.table.delete("resizeline")
            self.delete("resizeline")
            self.table.create_line(
                x,
                0,
                x,
                self.table.rowheight * self.table.rows,
                width=2,
                fill="gray",
                tag="resizeline",
            )
            self.create_line(
                x, 0, x, self.height, width=2, fill="gray", tag="resizeline"
            )
            return
        else:
            self.handle_left_shift_click(event)
            return

    def handle_left_shift_click(self, event):
        """Handle shift click, for selecting multiple cols"""

        colover = self.table.get_col_clicked(event)
        if colover == None:
            return
        if colover >= self.table.cols or self.table.currentcol > self.table.cols:
            return
        else:
            self.table.endcol = colover
        # draw the selected columns
        print(self.table.endcol, self.table.currentcol)
        if self.table.endcol != self.table.currentcol:
            if self.table.endcol < self.table.currentcol:
                collist = range(self.table.endcol, self.table.currentcol + 1)
            else:
                collist = range(self.table.currentcol, self.table.endcol + 1)
            for c in self.table.multiplecollist:
                self.drawRect(c, delete=0)
                self.table.drawSelectedCol(c, delete=0)
            self.table.multiplecollist = collist
        else:
            self.table.multiplecollist = []
            self.table.multiplecollist.append(colover)
            for c in self.table.multiplecollist:
                self.drawRect(c, delete=0)
                self.table.drawSelectedCol(c, delete=0)
        return


class CoolTableCanvas(TableCanvas):
    def show(self, callback=None):
        """Adds column header and scrollbars and combines them with
        the current table adding all to the master frame provided in constructor.
        Table is then redrawn."""

        # Add the table and header to the frame
        self.tablerowheader = RowHeader(
            self.parentframe, self, width=self.rowheaderwidth
        )
        self.tablecolheader = NoDragColumnHeader(self.parentframe, self)
        self.Yscrollbar = AutoScrollbar(
            self.parentframe, orient=VERTICAL, command=self.set_yviews
        )
        self.Yscrollbar.grid(row=1, column=2, rowspan=1, sticky="news", pady=0, ipady=0)
        self.Xscrollbar = AutoScrollbar(
            self.parentframe, orient=HORIZONTAL, command=self.set_xviews
        )
        self.Xscrollbar.grid(row=2, column=1, columnspan=1, sticky="news")
        self["xscrollcommand"] = self.Xscrollbar.set
        self["yscrollcommand"] = self.Yscrollbar.set
        self.tablecolheader["xscrollcommand"] = self.Xscrollbar.set
        self.tablerowheader["yscrollcommand"] = self.Yscrollbar.set
        self.parentframe.rowconfigure(1, weight=1)
        self.parentframe.columnconfigure(1, weight=1)

        self.tablecolheader.grid(
            row=0, column=1, rowspan=1, sticky="news", pady=0, ipady=0
        )
        self.tablerowheader.grid(
            row=1, column=0, rowspan=1, sticky="news", pady=0, ipady=0
        )
        self.grid(row=1, column=1, rowspan=1, sticky="news", pady=0, ipady=0)

        self.adjustColumnWidths()
        self.redrawTable(callback=callback)
        self.parentframe.bind("<Configure>", self.redrawVisible)
        self.tablecolheader.xview("moveto", 0)
        self.xview("moveto", 0)
        return

    def updateModel(self, model):
        """Call this method to update the table model"""

        self.model = model
        self.rows = self.model.getRowCount()
        self.cols = self.model.getColumnCount()
        self.tablewidth = (self.cellwidth) * self.cols
        self.tablecolheader = NoDragColumnHeader(self.parentframe, self)
        self.tablerowheader = RowHeader(self.parentframe, self)
        self.createTableFrame()
        return

    def handle_left_click(self, event):
        """Respond to a single press"""

        # which row and column is the click inside?
        self.clearSelected()
        self.allrows = False
        rowclicked = self.get_row_clicked(event)
        colclicked = self.get_col_clicked(event)
        self.focus_set()
        if self.mode == "formula":
            self.handleFormulaClick(rowclicked, colclicked)
            return
        if hasattr(self, "cellentry"):
            self.cellentry.destroy()
        # ensure popup menus are removed if present
        if hasattr(self, "rightmenu"):
            self.rightmenu.destroy()
        if hasattr(self.tablecolheader, "rightmenu"):
            self.tablecolheader.rightmenu.destroy()

        self.startrow = rowclicked
        self.endrow = rowclicked
        self.startcol = colclicked
        self.endcol = colclicked
        # reset multiple selection list
        self.multiplerowlist = []
        self.multiplerowlist.append(rowclicked)

        self.setSelectedRow(rowclicked)
        self.setSelectedCol(colclicked)

        if rowclicked is None or colclicked is None:
            return
        if rowclicked is not None and colclicked is not None:
            self.drawSelectedRect(self.currentrow, self.currentcol)
            self.drawSelectedRow()
            self.tablerowheader.drawSelectedRows(rowclicked)
        if self.read_only is True:
            return
        if 0 <= rowclicked < self.rows and 0 <= colclicked < self.cols:
            coltype = self.model.getColumnType(colclicked)
            if coltype == "text" or coltype == "number":
                self.drawCellEntry(rowclicked, colclicked)
        return


class SpreadsheetWindow:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SpreadsheetWindow, cls).__new__(cls)
            cls._instance.init()
        return cls._instance

    def init(self):
        self.filename = "files/example.xlsx"  # Replace with your Excel file name
        self.df = ChromiumUtilities.import_spreadsheet(self.filename)
        self.data = ChromiumUtilities.df_to_dict(self.df)

        self.window = tk.Tk()
        self.window.title("Excel Data")

        self.instruction_frame = tk.Frame(self.window)
        self.instruction_frame.pack(fill="x")

        self.instruction = tk.Label(
            self.instruction_frame,
            text="Select a range of data to use, or select just the headers to use all rows.",
        )
        self.instruction.pack(side="left")

        self.button = tk.Button(
            self.instruction_frame,
            text="Get Data from Selection",
            command=self.select_data,
        )
        self.button.pack(side="right")

        self.selection_frame = tk.Frame(self.window)
        self.selection_frame.pack(fill="x")

        self.rows_selected = 0
        self.columns_selected = 0
        self.headers_selected = []
        self.startrow = 0
        self.startcol = 0
        self.endrow = 0
        self.endcol = 0

        self.rows_label = tk.Label(self.selection_frame, text="Rows Selected: 0")
        self.rows_label.pack(side="left")

        self.columns_label = tk.Label(self.selection_frame, text="Columns Selected: 0")
        self.columns_label.pack(side="left")

        self.headers_label = tk.Label(self.selection_frame, text="Headers Selected: []")
        self.headers_label.pack(side="left")

        self.confirm_button = tk.Button(
            self.selection_frame,
            text="Confirm and Use Data",
            command=self.confirm_and_use_data,
        )
        self.confirm_button.pack(side="right")
        self.confirm_button.config(state="disabled")

        self.frame = tk.Frame(self.window)
        self.frame.pack(fill="both", expand=True)

        self.table = CoolTableCanvas(self.frame, data=self.data, read_only=True)
        self.table.thefont = ("Arial", 10)
        self.table.rowheight = 20
        self.table.drawTooltip = lambda x, y: None
        self.table.show()

        screen_width = self.window.winfo_screenwidth()
        table_width = len(self.data.keys()) * 120  # assume 100 pixels per column
        self.window.geometry(f"{min(table_width, int(screen_width/2))}x600")

        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)

    def select_data(self):
        if hasattr(self.table, "multiplerowlist"):
            self.rows_selected = len(self.table.multiplerowlist)
            self.columns_selected = abs(self.table.endcol - self.table.startcol) + 1
            self.startrow = self.table.startrow
            self.startcol = min(self.table.startcol, self.table.endcol)
            self.endrow = self.table.endrow
            self.endcol = max(self.table.startcol, self.table.endcol)
            row = self.table.multiplerowlist[0]
            self.headers_selected = [
                self.table.model.data[str(row)][str(col)]
                for col in range(self.startcol, self.endcol + 1)
            ]
            self.update_selection_labels()
            self.confirm_button.config(state="normal")
        else:
            print("No data selected")

    def update_selection_labels(self):
        self.rows_label["text"] = f"Rows Selected: {self.rows_selected}"
        self.columns_label["text"] = f"Columns Selected: {self.columns_selected}"
        self.headers_label["text"] = f"Headers Selected: {self.headers_selected}"

    def get_data_selection(self, as_df=False):
        startrow = min(self.startrow, self.endrow)
        endrow = max(self.startrow, self.endrow)
        startcol = min(self.startcol, self.endcol)
        endcol = max(self.startcol, self.endcol)

        data_subset = {}
        for row in range(startrow, endrow + 1):
            row_str = str(row)
            data_subset[row_str] = {}
            for col in range(startcol, endcol + 1):
                col_str = str(col)
                data_subset[row_str][col_str] = self.data[row_str][col_str]
        if as_df:
            data_subset = pd.DataFrame.from_dict(data_subset, orient="index")
        return data_subset

    def get_all_data_under_header(self, as_df=False):
        startrow = min(self.startrow, self.endrow)
        startcol = min(self.startcol, self.endcol)
        endcol = max(self.startcol, self.endcol)
        endrow = max(map(int, self.data.keys()))  # get the last row

        data_subset = {}
        for row in range(startrow, endrow + 1):
            row_str = str(row)
            data_subset[row_str] = {}
            for col in range(startcol, endcol + 1):
                col_str = str(col)
                data_subset[row_str][col_str] = self.data[row_str][col_str]
        if as_df:
            data_subset = pd.DataFrame.from_dict(data_subset, orient="index")
        return data_subset

    def confirm_and_use_data(self):
        if self.rows_selected > 1:
            data_subset = self.get_data_selection(as_df=True)
        else:
            data_subset = self.get_all_data_under_header(as_df=True)
        self.window.destroy()
        return data_subset

    def on_closing(self):
        self.window.destroy()
        return {}

    def mainloop(self):
        self.window.mainloop()
