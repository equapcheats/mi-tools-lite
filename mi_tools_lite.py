
import customtkinter as ctk
from modules.connection_tab import ConnectionTab
from modules.debloater_tab import DebloaterTab
from modules.misc_tab import MiscTab
from modules.reboot_tab import RebootTab
from modules.packages_tab import PackagesTab
from modules.power_tab import PowerTab
from modules.inspector_tab import InspectorTab
from modules.task_manager_tab import TaskManagerTab
from modules.adb_manager import ADBManager
from modules.constants import MIUI_ADS_AND_TRACKING

# Configuration
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class MiToolsLiteApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Mi Tools Lite - Modular 2.6")
        self.geometry("1100x800")
        
        # ADB Manager
        self.adb_manager = ADBManager()
        self.bloatware_list = MIUI_ADS_AND_TRACKING

        # Layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Header
        self.header_frame = ctk.CTkFrame(self, corner_radius=0)
        self.header_frame.grid(row=0, column=0, sticky="ew")
        
        self.label_title = ctk.CTkLabel(self.header_frame, text="Mi Tools Lite", font=("Roboto Medium", 24))
        self.label_title.pack(padx=20, pady=20)

        # Tab View
        self.tab_view = ctk.CTkTabview(self, command=self.on_tab_change)
        self.tab_view.grid(row=1, column=0, padx=20, pady=20, sticky="nsew")

        # Tabs
        self.tab_connect = self.tab_view.add("Connection & Info")
        self.tab_debloat = self.tab_view.add("Debloater")
        self.tab_task = self.tab_view.add("Task Manager") # New
        self.tab_packages = self.tab_view.add("Package Manager")
        self.tab_power = self.tab_view.add("Power & Performance")
        self.tab_inspector = self.tab_view.add("Inspector")
        self.tab_misc = self.tab_view.add("Tweaks")
        self.tab_reboot = self.tab_view.add("Reboot")
        self.tab_other = self.tab_view.add("Other")

        # Initialize Debloater Tab
        self.debloater = DebloaterTab(self.tab_debloat, self.adb_manager, self.bloatware_list)
        self.debloater.pack(fill="both", expand=True)

        # Initialize Connection Tab
        self.connection = ConnectionTab(self.tab_connect, self.adb_manager, on_connect_callback=self.on_connected)
        self.connection.pack(fill="both", expand=True)

        # Initialize Task Manager Tab
        self.task_manager = TaskManagerTab(self.tab_task, self.adb_manager)
        self.task_manager.pack(fill="both", expand=True)
        
        # Initialize Packages Tab
        self.packages = PackagesTab(self.tab_packages, self.adb_manager)
        self.packages.pack(fill="both", expand=True)

        # Initialize Power Tab
        self.power = PowerTab(self.tab_power, self.adb_manager)
        self.power.pack(fill="both", expand=True)
        
        # Initialize Inspector Tab
        self.inspector = InspectorTab(self.tab_inspector, self.adb_manager)
        self.inspector.pack(fill="both", expand=True)

        # Initialize Misc Tab
        self.misc = MiscTab(self.tab_misc, self.adb_manager)
        self.misc.pack(fill="both", expand=True)

        # Initialize Reboot Tab
        self.reboot = RebootTab(self.tab_reboot, self.adb_manager)
        self.reboot.pack(fill="both", expand=True)

        # Other
        self.label_other = ctk.CTkLabel(self.tab_other, text="More features coming soon...", font=("Roboto", 16))
        self.label_other.pack(pady=40)

    def on_connected(self):
        # Notify other tabs that connection is active
        self.debloater.on_device_connected()
        self.packages.status_label.configure(text="Connected. Refresh to load packages.")
        self.misc.status_label.configure(text="Connected.", text_color="#2CC985")
        self.reboot.status_label.configure(text="Connected.", text_color="#2CC985")
        self.power.status_label.configure(text="Connected.", text_color="#2CC985")
        self.power.check_low_power() # Auto check status
        self.task_manager.status_label.configure(text="Connected. Load processes to start.")

    def on_tab_change(self):
        current_tab = self.tab_view.get()
        if current_tab == "Connection & Info":
            self.connection.start_monitoring()
        else:
            self.connection.stop_monitoring()

if __name__ == "__main__":
    app = MiToolsLiteApp()
    app.mainloop()
