import os
import json
import shutil
import subprocess
from selenium import webdriver
from selenium.webdriver.edge.options import Options
from fax_counter.utilities import ChromiumUtilities
import tempfile


class EdgeDriverManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EdgeDriverManager, cls).__new__(cls)
            cls._instance.driver = None  # Initialize driver to None
        return cls._instance

    def _init_driver(self):
        # Create a temporary directory for downloads
        self.download_dir = os.path.join(os.getcwd(), "files", "cache")
        os.makedirs(self.download_dir, exist_ok=True)

        # Print the temporary directory path for debugging purposes
        print(f"Temporary download directory: {self.download_dir}")

        # Specify the path to your Edge profile
        self.edge_profile_path = ChromiumUtilities.get_edge_user_dir()

        # Create Edge options object
        self.edge_options = Options()

        # Set the user data directory to load the default user profile
        self.edge_options.add_argument(f"user-data-dir={self.edge_profile_path}")

        # Define the temporary preferences
        self.temp_prefs = {
            "download.default_directory": self.download_dir,
            "download.prompt_for_download": False,
            "plugins.always_open_pdf_externally": True,  # Disable the built-in PDF viewer
            "download.directory_upgrade": True,
        }

        # Backup the original preferences and apply the temporary ones
        self.backup_prefs_file_path = self._manage_edge_prefs()
        self.edge_options.add_experimental_option("prefs", self.temp_prefs)
        # Initialize the WebDriver with the specified options
        self.driver = webdriver.Edge(options=self.edge_options)

    def _manage_edge_prefs(self):
        # Path to Edge's preferences file
        prefs_file_path = os.path.join(self.edge_profile_path, "Default", "Preferences")

        # Backup the original preferences
        backup_prefs_file_path = prefs_file_path + ".backup"
        shutil.copyfile(prefs_file_path, backup_prefs_file_path)

        return backup_prefs_file_path

    def _restore_original_prefs(self):
        prefs_file_path = os.path.join(self.edge_profile_path, "Default", "Preferences")
        if os.path.exists(self.backup_prefs_file_path):
            shutil.copyfile(self.backup_prefs_file_path, prefs_file_path)
            os.remove(self.backup_prefs_file_path)  # Clean up the backup file

    def start(self):
        """Initialize or restart the WebDriver."""
        if self.driver:
            print("Driver already running. Restarting...")
            self.stop()

        self.force_quit_edge()
        self._init_driver()
        print("WebDriver started.")

    def stop(self):
        """Stop the WebDriver and clean up resources."""
        if self.driver:
            print("Stopping WebDriver.")
            # Restore the original preferences
            self._restore_original_prefs()

            # Close the browser
            self.driver.quit()
            self.driver = None  # Reset driver to None

            self.edge_profile_path = None
            self.backup_prefs_file_path = None
            print("WebDriver stopped and resources cleaned up.")

    def get_driver(self):
        """Get the current WebDriver instance."""
        if not self.driver:
            raise Exception(
                "WebDriver is not running. Please call 'start' to initialize it."
            )
        return self.driver

    @staticmethod
    def force_quit_edge():
        """Kill all Edge processes to ensure cleanup."""
        try:
            if os.name == "nt":  # For Windows
                subprocess.call(["taskkill", "/F", "/IM", "msedge.exe"])
            else:  # For Unix-like systems
                subprocess.call(["pkill", "-f", "msedge"])
            print("All Edge processes have been terminated.")
        except Exception as e:
            print(f"Error terminating Edge processes: {e}")
