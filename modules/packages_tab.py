
import customtkinter as ctk

class PackagesTab(ctk.CTkFrame):
    def __init__(self, master, adb_manager):
        super().__init__(master)
        self.adb_manager = adb_manager

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # Filters / Mode Selection
        self.filter_frame = ctk.CTkFrame(self)
        self.filter_frame.grid(row=0, column=0, padx=20, pady=10, sticky="ew")

        self.modes = {
            "System Apps": "system",
            "User Apps (3rd Party)": "user",
            "Disabled Apps": "disabled",
            "Uninstalled System Apps": "uninstalled"
        }
        
        self.mode_var = ctk.StringVar(value="System Apps")
        
        self.label_mode = ctk.CTkLabel(self.filter_frame, text="Filter:", font=("Roboto", 14))
        self.label_mode.pack(side="left", padx=10, pady=10)

        self.mode_menu = ctk.CTkOptionMenu(self.filter_frame, variable=self.mode_var, values=list(self.modes.keys()), command=self.load_packages)
        self.mode_menu.pack(side="left", padx=10, pady=10, fill="x", expand=True)

        self.btn_refresh = ctk.CTkButton(self.filter_frame, text="Refresh", width=80, command=self.load_packages)
        self.btn_refresh.pack(side="left", padx=10, pady=10)

        # Search
        self.search_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.search_frame.grid(row=1, column=0, padx=20, pady=(0, 10), sticky="ew")

        self.entry_search = ctk.CTkEntry(self.search_frame, placeholder_text="Search package...")
        self.entry_search.pack(fill="x", expand=True)
        self.entry_search.bind("<KeyRelease>", self.filter_list)

        # List Area
        self.list_frame = ctk.CTkScrollableFrame(self, label_text="Packages List")
        self.list_frame.grid(row=2, column=0, padx=20, pady=10, sticky="nsew")

        # Action Buttons
        self.action_frame = ctk.CTkFrame(self)
        self.action_frame.grid(row=3, column=0, padx=20, pady=20, sticky="ew")

        self.status_label = ctk.CTkLabel(self.action_frame, text="Ready", anchor="w")
        self.status_label.pack(side="left", padx=20, pady=10, fill="x", expand=True)

        # Dynamic Buttons (will be packed based on mode)
        self.btns = []

        self.all_packages = [] # Full list for current mode
        self.check_vars = {}
        
        # Initial Load? Wait for connection.

    def load_packages(self, _=None):
        if not self.adb_manager.connected_device:
            self.status_label.configure(text="No device connected.")
            return

        mode_key = self.mode_var.get()
        mode = self.modes[mode_key]
        
        self.status_label.configure(text=f"Loading {mode_key}...")
        self.update_idletasks() # Force UI update
        
        # Fetch in thread
        import threading
        threading.Thread(target=self._fetch_packages, args=(mode,), daemon=True).start()

    def _fetch_packages(self, mode):
        pkgs = self.adb_manager.get_packages(mode)
        self.all_packages = pkgs
        
        # Update UI in main thread
        self.after(0, lambda: self._display_list(pkgs))
        self.after(0, self.update_actions)

    def _display_list(self, packages):
        # Clear existing
        for widget in self.list_frame.winfo_children():
            widget.destroy()
        self.check_vars = {}

        if not packages:
            ctk.CTkLabel(self.list_frame, text="No packages found.").pack(pady=20)
            self.status_label.configure(text="No packages found.")
            return

        for pkg in packages:
            var = ctk.BooleanVar(value=False)
            chk = ctk.CTkCheckBox(self.list_frame, text=pkg, variable=var)
            chk.pack(anchor="w", padx=10, pady=2)
            self.check_vars[pkg] = var
            
        self.status_label.configure(text=f"Loaded {len(packages)} packages.")
        self.filter_list() # Apply search if any

    def filter_list(self, event=None):
        query = self.entry_search.get().lower()
        
        # Hide/Show widgets based on query
        # Since tkinter pack/unpack is heavy, creating/destroying might be better or pack_forget.
        # Simple optimization: Iterate check_vars keys and widgets?
        # CheckBox widget text is the package name.
        
        # Re-drawing list from all_packages is cleaner but slower if lists are huge.
        # Let's try re-draw loop.
        
        # Note: self.list_frame.winfo_children() are the checkboxes.
        # But we need their text.
        
        # Actually simplest way for this 'Lite' tool:
        # Just loop through existing widgets and pack_forget if not match, pack if match.
        
        for widget in self.list_frame.winfo_children():
             if isinstance(widget, ctk.CTkCheckBox):
                text = widget.cget("text").lower()
                if query in text:
                    widget.pack(anchor="w", padx=10, pady=2)
                else:
                    widget.pack_forget()

    def update_actions(self):
        # Clear old buttons
        for btn in self.btns:
            btn.destroy()
        self.btns = []

        mode_key = self.mode_var.get()
        mode = self.modes[mode_key]

        # Define actions per mode
        actions = []
        if mode == "system":
            # Actions: Disable, Uninstall (User 0)
            actions.append(("Disable", self.action_disable, "#F0ad4e", "#d08d2e")) # Orange
            actions.append(("Uninstall (User 0)", self.action_uninstall_user0, "#C92C2C", "#992222")) # Red
        elif mode == "user":
            # Actions: Uninstall (User 0), Uninstall (Full)
            # actions.append(("Uninstall (User 0)", self.action_uninstall_user0, "#C92C2C", "#992222"))
            actions.append(("Uninstall (Full)", self.action_uninstall_full, "#C92C2C", "#992222"))
        elif mode == "disabled":
            # Actions: Enable, Uninstall (User 0)
            actions.append(("Enable", self.action_enable, "#2CC985", "#229966")) # Green
            actions.append(("Uninstall (User 0)", self.action_uninstall_user0, "#C92C2C", "#992222"))
        elif mode == "uninstalled":
            # Actions: Restore (Install Existing)
            actions.append(("Restore / Re-install", self.action_restore, "#2CC985", "#229966"))

        # Create Buttons
        for text, cmd, col, hov in actions:
            btn = ctk.CTkButton(self.action_frame, text=text, command=cmd, fg_color=col, hover_color=hov)
            btn.pack(side="right", padx=5, pady=10)
            self.btns.append(btn)

    def get_selected(self):
        return [pkg for pkg, var in self.check_vars.items() if var.get()]

    def process_queue(self, queue, action_func, action_name):
        if not queue:
            self.status_label.configure(text=f"{action_name} complete.")
            self.load_packages() # Refresh list
            return

        pkg = queue.pop(0)
        self.status_label.configure(text=f"{action_name}: {pkg}...")
        
        def on_done(success, msg):
             # Maybe log status
             self.after(200, lambda: self.process_queue(queue, action_func, action_name))

        # action_func signature: (pkg, callback)
        action_func(pkg, lambda s, m: self.after(0, lambda: on_done(s, m)))

    # Action Handlers
    def action_enable(self):
        selected = self.get_selected()
        if not selected: return
        self.process_queue(list(selected), self.adb_manager.enable_package, "Enabling")

    def action_disable(self):
        selected = self.get_selected()
        if not selected: return
        self.process_queue(list(selected), self.adb_manager.disable_package, "Disabling")

    def action_uninstall_user0(self):
        selected = self.get_selected()
        if not selected: return
        self.process_queue(list(selected), self.adb_manager.uninstall_package, "Uninstalling (User 0)")

    def action_uninstall_full(self):
        selected = self.get_selected()
        if not selected: return
        self.process_queue(list(selected), self.adb_manager.uninstall_full, "Uninstalling Fully")


    def action_restore(self):
        selected = self.get_selected()
        if not selected: return
        self.process_queue(list(selected), self.adb_manager.restore_package_robust, "Restoring")

