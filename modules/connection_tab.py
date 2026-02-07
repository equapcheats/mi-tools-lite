
import customtkinter as ctk

class ConnectionTab(ctk.CTkFrame):

    def __init__(self, master, adb_manager, on_connect_callback=None):
        super().__init__(master)
        self.adb_manager = adb_manager
        self.on_connect_callback = on_connect_callback
        self.is_monitoring = False


        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1) # Two columns for info
        
        # Connection Section
        self.conn_frame = ctk.CTkFrame(self)
        self.conn_frame.grid(row=0, column=0, columnspan=2, padx=20, pady=20, sticky="ew")

        self.label_device = ctk.CTkLabel(self.conn_frame, text="Select Device:", font=("Roboto", 14))
        self.label_device.pack(side="left", padx=10, pady=10)

        self.device_var = ctk.StringVar(value="Searching...")
        self.device_menu = ctk.CTkOptionMenu(self.conn_frame, variable=self.device_var, values=["Searching..."])
        self.device_menu.pack(side="left", padx=10, pady=10, expand=True, fill="x")

        self.btn_refresh = ctk.CTkButton(self.conn_frame, text="↻", width=40, command=self.refresh_devices)
        self.btn_refresh.pack(side="left", padx=5, pady=10)

        self.btn_connect = ctk.CTkButton(self.conn_frame, text="Connect", command=self.connect_device)
        self.btn_connect.pack(side="left", padx=10, pady=10)

        self.status_label = ctk.CTkLabel(self, text="Status: Ready", anchor="w")
        self.status_label.grid(row=1, column=0, columnspan=2, padx=20, pady=(0, 10), sticky="ew")

        # Device Info Section
        self.info_frame = ctk.CTkFrame(self)
        self.info_frame.grid(row=2, column=0, columnspan=2, padx=20, pady=10, sticky="nsew")
        self.grid_rowconfigure(2, weight=1)
        
        self.info_frame.grid_columnconfigure(0, weight=1)
        self.info_frame.grid_columnconfigure(1, weight=1)

        self.create_info_label(0, 0, "Battery Level:", "battery_level")
        self.create_info_label(0, 1, "Voltage:", "battery_voltage")
        self.create_info_label(1, 0, "Temperature:", "battery_temp")
        self.create_info_label(1, 1, "CPU Cores:", "cpu_cores")
        self.create_info_label(2, 0, "RAM Total:", "MemTotal")
        self.create_info_label(2, 1, "RAM Available:", "MemAvailable")
        self.create_info_label(3, 0, "Region:", "region")
        self.create_info_label(3, 1, "Model Code:", "miui_mod_device")
        
        self.info_labels = {}

        # Initial Scan
        self.refresh_devices()

    def create_info_label(self, row, col, title, key):
        frame = ctk.CTkFrame(self.info_frame, fg_color="transparent")
        frame.grid(row=row, column=col, padx=10, pady=10, sticky="ew")
        
        lbl_title = ctk.CTkLabel(frame, text=title, font=("Roboto", 12, "bold"))
        lbl_title.pack(anchor="w")
        
        lbl_val = ctk.CTkLabel(frame, text="--", font=("Roboto", 12))
        lbl_val.pack(anchor="w")
        
        # We'll store the value label to update it later using the key
        if not hasattr(self, 'value_labels'):
            self.value_labels = {}
        self.value_labels[key] = lbl_val

    def refresh_devices(self):
        self.status_label.configure(text="Scanning...")
        self.btn_refresh.configure(state="disabled")
        
        self.adb_manager.scan_devices(lambda d, e: self.after(0, lambda: self._update_device_list(d, e)))

    def _update_device_list(self, devices, error):
        self.btn_refresh.configure(state="normal")
        if error and "ADB executable not found" in error:
            self.status_label.configure(text="Error: ADB not found.")
            self.device_menu.configure(values=["ADB Not Found"])
            self.device_var.set("ADB Not Found")
        elif devices:
            self.device_menu.configure(values=devices)
            self.device_var.set(devices[0])
            self.status_label.configure(text=f"Found {len(devices)} device(s).")
        else:
            self.device_menu.configure(values=["No devices found"])
            self.device_var.set("No devices found")
            self.status_label.configure(text="No devices found.")

    def connect_device(self):
        target = self.device_var.get()
        if target in ["No devices found", "Searching...", "ADB Not Found"]:
            return

        self.btn_connect.configure(text="Connecting...", state="disabled")
        self.status_label.configure(text=f"Connecting to {target}...")
        
        self.adb_manager.connect_device(target, lambda s, m: self.after(0, lambda: self._handle_connect_result(s, m)))

    def _handle_connect_result(self, success, msg):
        self.status_label.configure(text=msg)
        if success:
            self.btn_connect.configure(text="Connected", fg_color="#2CC985", hover_color="#229966", state="disabled")

            self.update_device_info()
            self.start_monitoring()
            if self.on_connect_callback:
                self.on_connect_callback()

        else:
            self.btn_connect.configure(text="Connect", state="normal", fg_color="#3B8ED0", hover_color="#36719F")

    def update_device_info(self):
        # Run in thread to avoid UI freeze
        import threading
        def _fetch():
            info = self.adb_manager.get_info()
            self.after(0, lambda: self._display_info(info))
        threading.Thread(target=_fetch, daemon=True).start()

    def _display_info(self, info):
        if not info: return
        for key, lbl in self.value_labels.items():
            val = info.get(key, "N/A")

            lbl.configure(text=str(val))

    def start_monitoring(self):
        self.is_monitoring = True
        self._monitor_loop()

    def stop_monitoring(self):
        self.is_monitoring = False

    def _monitor_loop(self):
        if not self.is_monitoring:
            return
        
        # Only fetch if connected
        if self.adb_manager.connected_device:
            self.update_device_info()
            
        # Schedule next update in 1 second (1000ms)
        self.after(1000, self._monitor_loop)

