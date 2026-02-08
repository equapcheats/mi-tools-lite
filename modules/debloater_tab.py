
import customtkinter as ctk

class DebloaterTab(ctk.CTkFrame):
    def __init__(self, master, adb_manager, bloatware_list):
        super().__init__(master)
        self.adb_manager = adb_manager
        self.bloatware_list = bloatware_list

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # Header
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(fill="x", padx=20, pady=5)

        self.label_info = ctk.CTkLabel(self.header_frame, text="Select MIUI Packages to Remove", font=("Roboto Medium", 16))
        self.label_info.pack(side="left", pady=10)

        self.select_all_var = ctk.BooleanVar(value=False)
        self.chk_select_all = ctk.CTkCheckBox(self.header_frame, text="Select All", variable=self.select_all_var, command=self.toggle_select_all)
        self.chk_select_all.pack(side="right", pady=10, padx=10)

        # List
        self.scrollable_list = ctk.CTkScrollableFrame(self, label_text="Packages")
        self.scrollable_list.pack(fill="both", expand=True, padx=20, pady=10)

        self.check_vars = {}
        
        # bloatware_list is now a dict {category: [(pkg, desc), ...]}
        for category, items in self.bloatware_list.items():
            # Category Header
            cat_label = ctk.CTkLabel(self.scrollable_list, text=category, font=("Roboto", 14, "bold"), text_color="#3B8ED0")
            cat_label.pack(anchor="w", padx=5, pady=(15, 5))
            
            for pkg, desc in items:
                var = ctk.BooleanVar(value=False)
                # Text: "com.pkg (Description)"
                text = f"{pkg} ({desc})" if desc else pkg
                chk = ctk.CTkCheckBox(self.scrollable_list, text=text, variable=var, font=("Roboto", 12))
                chk.pack(anchor="w", padx=15, pady=2)
                self.check_vars[pkg] = var


        # Actions
        self.action_frame = ctk.CTkFrame(self)
        self.action_frame.pack(fill="x", padx=20, pady=20)

        self.status_label = ctk.CTkLabel(self.action_frame, text="Status: Waiting for connection...", anchor="w")
        self.status_label.pack(side="left", padx=20, pady=10, fill="x", expand=True)


        self.btn_uninstall = ctk.CTkButton(self.action_frame, text="Uninstall Selected", command=self.run_uninstall, state="disabled", fg_color="#C92C2C", hover_color="#992222")
        self.btn_uninstall.pack(side="right", padx=10, pady=10)

        self.btn_reinstall = ctk.CTkButton(self.action_frame, text="Re-enable Selected", command=self.run_reinstall, state="disabled", fg_color="#3B8ED0", hover_color="#36719F")
        self.btn_reinstall.pack(side="right", padx=10, pady=10)



    def on_device_connected(self):
        self.status_label.configure(text="Ready.")
        self.btn_uninstall.configure(state="normal")
        self.btn_reinstall.configure(state="normal")
        self.check_uninstalled_status()

    def check_uninstalled_status(self):
        self.status_label.configure(text="Checking installed status...")
        import threading
        threading.Thread(target=self._check_status_thread, daemon=True).start()

    def _check_status_thread(self):
        # Fetch uninstalled system packages
        uninstalled = self.adb_manager.get_packages("uninstalled")
        
        matched_count = 0
        for pkg, var in self.check_vars.items():
            # Check packages and variants
            variants = self.adb_manager._get_variants(pkg)
            is_uninstalled = False
            for v in variants:
                if v in uninstalled:
                    is_uninstalled = True
                    break
            
            if is_uninstalled:
                self.after(0, lambda v=var: v.set(True))
                matched_count += 1
        
        self.after(0, lambda: self.status_label.configure(text=f"Ready. Found {matched_count} uninstalled apps."))




    def toggle_select_all(self):
        state = self.select_all_var.get()
        for var in self.check_vars.values():
            var.set(state)

    def run_reinstall(self):

        if not self.adb_manager.connected_device:
            self.status_label.configure(text="Error: No device connected.")
            return

        selected = [pkg for pkg, var in self.check_vars.items() if var.get()]
        if not selected:
            self.status_label.configure(text="No packages selected.")
            return

        self.btn_reinstall.configure(state="disabled")
        self.btn_uninstall.configure(state="disabled")
        self.status_label.configure(text="Re-enabling...")
        
        self.work_queue = list(selected)
        self.work_total = len(selected)
        self.work_success = 0
        self.process_next_work(action="install")

    def run_uninstall(self):
        if not self.adb_manager.connected_device:
            self.status_label.configure(text="Error: No device connected.")
            return

        selected = [pkg for pkg, var in self.check_vars.items() if var.get()]
        if not selected:
            self.status_label.configure(text="No packages selected.")
            return

        self.btn_uninstall.configure(state="disabled")
        self.btn_reinstall.configure(state="disabled")
        self.status_label.configure(text="Uninstalling...")
        
        self.work_queue = list(selected)
        self.work_total = len(selected)
        self.work_success = 0
        self.process_next_work(action="uninstall")

    def process_next_work(self, action):
        if not self.work_queue:
            self.status_label.configure(text=f"Finished: {self.work_success}/{self.work_total} processed.")
            self.btn_uninstall.configure(state="normal")
            self.btn_reinstall.configure(state="normal")
            # Auto-refresh status to reflect changes
            self.check_uninstalled_status()
            return

        pkg = self.work_queue.pop(0)
        self.status_label.configure(text=f"{'Uninstalling' if action == 'uninstall' else 'Re-enabling'} {pkg}...")
        
        def on_done(success, msg):
            if success: self.work_success += 1
            self.after(500, lambda: self.process_next_work(action))


        if action == "uninstall":
            self.adb_manager.uninstall_package(pkg, lambda s, m: self.after(0, lambda: on_done(s, m)))
        else:
            self.adb_manager.restore_package_robust(pkg, lambda s, m: self.after(0, lambda: on_done(s, m)))


