
import customtkinter as ctk
from modules.connection_tab import ConnectionTab
from modules.debloater_tab import DebloaterTab
from modules.misc_tab import MiscTab
from modules.reboot_tab import RebootTab
from modules.packages_tab import PackagesTab
from modules.power_tab import PowerTab
from modules.inspector_tab import InspectorTab
from modules.task_manager_tab import TaskManagerTab
from modules.file_transfer_tab import FileTransferTab
from modules.screenshot_tab import ScreenshotTab
from modules.adb_manager import ADBManager
from modules.constants import MIUI_ADS_AND_TRACKING

# Configuration
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

# UI Theme
APP_BG = "#0F1115"
TOPBAR_BG = "#0B0F17"
SIDEBAR_BG = "#111827"
SIDEBAR_ACTIVE = "#1F2937"
SIDEBAR_HOVER = "#1F2937"
TEXT_MUTED = "#9CA3AF"
TEXT_OK = "#2CC985"

class MiToolsLiteApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Mi Tools Lite - Modular 2.6")
        self.geometry("1200x820")
        self.configure(fg_color=APP_BG)
        
        # ADB Manager
        self.adb_manager = ADBManager()
        self.bloatware_list = MIUI_ADS_AND_TRACKING

        # Layout
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Top Bar
        self.header_frame = ctk.CTkFrame(self, corner_radius=0, fg_color=TOPBAR_BG)
        self.header_frame.grid(row=0, column=0, columnspan=2, sticky="ew")
        self.header_frame.grid_columnconfigure(0, weight=1)
        self.header_frame.grid_columnconfigure(1, weight=0)

        self.label_title = ctk.CTkLabel(self.header_frame, text="Mi Tools Lite", font=("Roboto Medium", 24))
        self.label_title.grid(row=0, column=0, padx=22, pady=(16, 2), sticky="w")

        self.label_subtitle = ctk.CTkLabel(self.header_frame, text="Device toolbox for Xiaomi/MIUI", font=("Roboto", 12), text_color=TEXT_MUTED)
        self.label_subtitle.grid(row=1, column=0, padx=22, pady=(0, 16), sticky="w")

        self.header_status = ctk.CTkLabel(self.header_frame, text="Not connected", font=("Roboto", 12), text_color=TEXT_MUTED)
        self.header_status.grid(row=0, column=1, rowspan=2, padx=22, pady=16, sticky="e")

        # Sidebar
        self.sidebar_frame = ctk.CTkFrame(self, corner_radius=0, fg_color=SIDEBAR_BG)
        self.sidebar_frame.grid(row=1, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(2, weight=1)
        self.sidebar_frame.grid_columnconfigure(0, weight=1)

        self.sidebar_title = ctk.CTkLabel(self.sidebar_frame, text="Navigation", font=("Roboto Medium", 13), text_color=TEXT_MUTED)
        self.sidebar_title.grid(row=0, column=0, padx=18, pady=(18, 8), sticky="w")

        self.nav_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        self.nav_frame.grid(row=1, column=0, padx=12, pady=8, sticky="nsew")

        # Content
        self.content_frame = ctk.CTkFrame(self, corner_radius=0, fg_color=APP_BG)
        self.content_frame.grid(row=1, column=1, padx=20, pady=20, sticky="nsew")
        self.content_frame.grid_rowconfigure(0, weight=1)
        self.content_frame.grid_columnconfigure(0, weight=1)

        self.page_container = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.page_container.grid(row=0, column=0, sticky="nsew")
        self.page_container.grid_rowconfigure(0, weight=1)
        self.page_container.grid_columnconfigure(0, weight=1)

        # Pages
        self.tab_connect = ctk.CTkFrame(self.page_container, fg_color="transparent")
        self.tab_debloat = ctk.CTkFrame(self.page_container, fg_color="transparent")
        self.tab_file_transfer = ctk.CTkFrame(self.page_container, fg_color="transparent")
        self.tab_task = ctk.CTkFrame(self.page_container, fg_color="transparent")
        self.tab_packages = ctk.CTkFrame(self.page_container, fg_color="transparent")
        self.tab_power = ctk.CTkFrame(self.page_container, fg_color="transparent")
        self.tab_inspector = ctk.CTkFrame(self.page_container, fg_color="transparent")
        self.tab_misc = ctk.CTkFrame(self.page_container, fg_color="transparent")
        self.tab_reboot = ctk.CTkFrame(self.page_container, fg_color="transparent")
        self.tab_screenshot = ctk.CTkFrame(self.page_container, fg_color="transparent")
        self.tab_other = ctk.CTkFrame(self.page_container, fg_color="transparent")

        for frame in [
            self.tab_connect,
            self.tab_debloat,
            self.tab_file_transfer,
            self.tab_task,
            self.tab_packages,
            self.tab_power,
            self.tab_inspector,
            self.tab_misc,
            self.tab_reboot,
            self.tab_screenshot,
            self.tab_other,
        ]:
            frame.grid(row=0, column=0, sticky="nsew")

        # Initialize Debloater Tab
        self.debloater = DebloaterTab(self.tab_debloat, self.adb_manager, self.bloatware_list)
        self.debloater.pack(fill="both", expand=True)

        # Initialize File Transfer Tab
        self.file_transfer = FileTransferTab(self.tab_file_transfer, self.adb_manager)
        self.file_transfer.pack(fill="both", expand=True)

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

        # Initialize Screenshot Tab
        self.screenshot = ScreenshotTab(self.tab_screenshot, self.adb_manager)
        self.screenshot.pack(fill="both", expand=True)

        # Other
        self.label_other = ctk.CTkLabel(self.tab_other, text="More features coming soon...", font=("Roboto", 16), text_color=TEXT_MUTED)
        self.label_other.pack(pady=40)

        # Navigation Buttons
        self.nav_buttons = {}
        nav_items = [
            ("connection", "Connection & Info", "🔌"),
            ("debloater", "Debloater", "🧹"),
            ("file_transfer", "File Transfer", "📁"),
            ("task_manager", "Task Manager", "🧾"),
            ("packages", "Package Manager", "📦"),
            ("power", "Power & Performance", "⚡"),
            ("inspector", "Inspector", "🔍"),
            ("screenshot", "Screenshot", "📸"),
            ("tweaks", "Tweaks", "🛠"),
            ("reboot", "Reboot", "🔄"),
            ("other", "Other", "✨"),
        ]

        for index, (key, label, icon) in enumerate(nav_items):
            btn = ctk.CTkButton(
                self.nav_frame,
                text=f"{icon} {label}",
                anchor="w",
                fg_color="transparent",
                hover_color=SIDEBAR_HOVER,
                text_color="#E5E7EB",
                height=36,
                command=lambda k=key: self.show_tab(k),
            )
            btn.grid(row=index, column=0, padx=6, pady=4, sticky="ew")
            self.nav_buttons[key] = btn

        self.pages = {
            "connection": self.tab_connect,
            "debloater": self.tab_debloat,
            "file_transfer": self.tab_file_transfer,
            "task_manager": self.tab_task,
            "packages": self.tab_packages,
            "power": self.tab_power,
            "inspector": self.tab_inspector,
            "screenshot": self.tab_screenshot,
            "tweaks": self.tab_misc,
            "reboot": self.tab_reboot,
            "other": self.tab_other,
        }

        self.active_tab = None
        self.show_tab("connection")

    def on_connected(self):
        # Notify other tabs that connection is active
        self.debloater.on_device_connected()
        self.file_transfer.on_device_connected()
        self.packages.status_label.configure(text="Connected. Refresh to load packages.")
        self.misc.status_label.configure(text="Connected.", text_color="#2CC985")
        self.reboot.status_label.configure(text="Connected.", text_color="#2CC985")
        self.power.status_label.configure(text="Connected.", text_color="#2CC985")
        self.power.check_low_power() # Auto check status
        self.task_manager.status_label.configure(text="Connected. Load processes to start.")
        self.screenshot.on_device_connected()
        self.header_status.configure(text="Connected", text_color=TEXT_OK)

    def show_tab(self, tab_key):
        if self.active_tab == tab_key:
            return

        if self.active_tab == "connection":
            self.connection.stop_monitoring()

        target = self.pages.get(tab_key)
        if not target:
            return

        target.tkraise()
        self.active_tab = tab_key
        self._update_nav_buttons()

        if tab_key == "connection":
            self.connection.start_monitoring()

        if tab_key == "debloater" and self.adb_manager.connected_device:
            self.debloater.check_uninstalled_status()

    def _update_nav_buttons(self):
        for key, button in self.nav_buttons.items():
            if key == self.active_tab:
                button.configure(fg_color=SIDEBAR_ACTIVE)
            else:
                button.configure(fg_color="transparent")

    def on_close(self):
        try:
             # Stop any threads or monitoring if possible
             self.connection.stop_monitoring()
             
             import subprocess
             # Execute taskkill /f /im adb.exe
             subprocess.run(["taskkill", "/f", "/im", "adb.exe"], creationflags=subprocess.CREATE_NO_WINDOW if subprocess.os.name == 'nt' else 0)
        except:
            pass
        self.destroy()

if __name__ == "__main__":
    app = MiToolsLiteApp()
    app.protocol("WM_DELETE_WINDOW", app.on_close)
    app.mainloop()
