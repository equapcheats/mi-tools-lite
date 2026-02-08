import customtkinter as ctk
import threading
import tkinter.filedialog
import tkinter.messagebox
import tkinter as tk
import os
import subprocess

class FileRow(ctk.CTkFrame):
    def __init__(self, master, item, selected=False, on_click=None, on_right_click=None, on_double_click=None):
        super().__init__(master, fg_color="transparent", corner_radius=0)
        self.item = item
        self.selected = selected
        self.on_click = on_click
        self.on_right_click = on_right_click
        self.on_double_click = on_double_click

        # Layout
        self.grid_columnconfigure(1, weight=1) # Name
        self.grid_columnconfigure(2, weight=0) # Date
        self.grid_columnconfigure(3, weight=0) # Size

        # Checkbox (simulated with a label or button, or actual checkbox)
        # Using a label for selection indicator is cleaner than a bulky checkbox sometimes, 
        # but checkbox is better for multi-select usability.
        self.checkbox = ctk.CTkCheckBox(self, text="", width=24, command=self._on_check_toggle)
        self.checkbox.grid(row=0, column=0, padx=(5, 5), pady=2, sticky="w")
        if selected:
            self.checkbox.select()

        # Icon
        icon = "📁" if item['type'] == 'dir' else "📄"
        self.lbl_icon = ctk.CTkLabel(self, text=icon, width=30, anchor="center")
        self.lbl_icon.grid(row=0, column=0, padx=(30, 0), sticky="w") # Offset from checkbox

        # Name
        self.lbl_name = ctk.CTkLabel(self, text=item['name'], anchor="w")
        self.lbl_name.grid(row=0, column=1, padx=5, sticky="ew")

        # Date
        self.lbl_date = ctk.CTkLabel(self, text=item.get('date', ''), width=120, anchor="e", text_color="gray")
        self.lbl_date.grid(row=0, column=2, padx=5, sticky="e")

        # Size
        self.lbl_size = ctk.CTkLabel(self, text=item.get('size', ''), width=80, anchor="e", text_color="gray")
        self.lbl_size.grid(row=0, column=3, padx=5, sticky="e")

        # Bindings
        for w in [self, self.lbl_icon, self.lbl_name, self.lbl_date, self.lbl_size]:
            w.bind("<Button-1>", self._on_click_event)
            w.bind("<Button-3>", self._on_right_click_event)
            if self.item['type'] == 'dir':
                w.bind("<Double-Button-1>", self._on_double_click_event)
        
        # Hover effect
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)

    def _on_enter(self, event):
        if not self.selected:
            self.configure(fg_color=("gray85", "gray25"))

    def _on_leave(self, event):
        if not self.selected:
            self.configure(fg_color="transparent")

    def _on_check_toggle(self):
        self.selected = bool(self.checkbox.get())
        if self.on_click:
            self.on_click(self.item, self.selected)
        self.update_appearance()

    def _on_click_event(self, event):
        # Toggle selection on click, or single select? 
        # Standard: Click selects (and deselects others usually), Ctrl+Click toggles.
        # For simplicity: Click toggles this row's selection state physically, but 
        # typically in file managers, single click selects only ONE.
        # Let's implement: Click = select only this (deselect others). Ctrl+Click = toggle.
        
        # Checking for Ctrl key is hard in pure tkinter bind without event parsing.
        # We'll just generic click -> inform parent.
        state = 0
        if isinstance(event.state, int): # Sometimes it's a string in some wrappers, but usually int
             # 0x0004 is Control on Windows
             if event.state & 0x0004:
                 state = 1 # Ctrl
             elif event.state & 0x0001:
                 state = 2 # Shift (ignored for now)
        
        if self.on_click:
             self.on_click(self.item, modifier=state)

    def _on_right_click_event(self, event):
        if self.on_right_click:
            self.on_right_click(event, self.item)

    def _on_double_click_event(self, event):
        if self.on_double_click:
            self.on_double_click(self.item)

    def set_selected(self, selected):
        self.selected = selected
        if selected:
            self.checkbox.select()
            self.configure(fg_color=("gray75", "#3A3A4A"))
        else:
            self.checkbox.deselect()
            self.configure(fg_color="transparent")
    
    def update_appearance(self):
        self.set_selected(self.selected)


class FileTransferTab(ctk.CTkFrame):
    def __init__(self, master, adb_manager):
        super().__init__(master)
        self.adb_manager = adb_manager
        
        self.current_path = "/sdcard/"
        self.file_items = [] # raw data
        self.row_widgets = [] # FileRow instances
        self.selected_items = set() # Set of names
        
        # Layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1) # List area grows

        # 1. Header & Navigation
        self._setup_header()

        # 2. Column Headers
        self._setup_column_headers()
        
        # 3. File List
        self.list_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.list_frame.grid(row=2, column=0, padx=10, pady=(0, 10), sticky="nsew")
        
        # 4. Footer / Actions
        self._setup_footer()

        # Context Menu
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="Open", command=self.on_open_context)
        self.context_menu.add_command(label="Download", command=self.download_selected)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Rename", command=self.rename_selected)
        self.context_menu.add_command(label="Delete", command=self.delete_selected)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Properties", command=self.show_properties)

        self.last_right_clicked_item = None

    def _setup_header(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        
        # Refresh
        self.btn_refresh = ctk.CTkButton(header, text="↻", width=30, command=self.refresh_files)
        self.btn_refresh.pack(side="left", padx=(0, 5))

        # Up
        self.btn_up = ctk.CTkButton(header, text="⬆", width=30, command=self.go_up)
        self.btn_up.pack(side="left", padx=5)

        # Home
        self.btn_home = ctk.CTkButton(header, text="🏠", width=30, command=self.go_home)
        self.btn_home.pack(side="left", padx=5)

        # Path Entry
        self.entry_path = ctk.CTkEntry(header, placeholder_text="/path/to/dir")
        self.entry_path.pack(side="left", fill="x", expand=True, padx=10)
        self.entry_path.bind("<Return>", self.on_path_entry)
        
        # New Folder
        self.btn_new_folder = ctk.CTkButton(header, text="+ Folder", width=80, command=self.create_folder, fg_color="#2aa198")
        self.btn_new_folder.pack(side="right", padx=5)

        # Search
        self.btn_search = ctk.CTkButton(header, text="Search", width=80, command=self.toggle_search)
        self.btn_search.pack(side="right", padx=5)

    def _setup_column_headers(self):
        cols = ctk.CTkFrame(self, height=30, fg_color=("gray90", "gray20"))
        cols.grid(row=1, column=0, padx=10, pady=(0,0), sticky="ew")
        cols.grid_columnconfigure(1, weight=1)

        # Select All Checkbox logic
        self.chk_select_all = ctk.CTkCheckBox(cols, text="", width=24, command=self.toggle_select_all)
        self.chk_select_all.grid(row=0, column=0, padx=(15, 5), pady=5, sticky="w") # Align with items

        ctk.CTkLabel(cols, text="Name", anchor="w", font=("Roboto", 12, "bold")).grid(row=0, column=1, padx=35, sticky="ew")
        ctk.CTkLabel(cols, text="Date", width=120, anchor="e", font=("Roboto", 12, "bold")).grid(row=0, column=2, padx=5, sticky="e")
        ctk.CTkLabel(cols, text="Size", width=80, anchor="e", font=("Roboto", 12, "bold")).grid(row=0, column=3, padx=15, sticky="e")

    def _setup_footer(self):
        footer = ctk.CTkFrame(self, height=50)
        footer.grid(row=3, column=0, padx=10, pady=10, sticky="ew")
        
        self.lbl_status = ctk.CTkLabel(footer, text="Ready", anchor="w")
        self.lbl_status.pack(side="left", padx=10, fill="x", expand=True)
        
        # Actions
        self.btn_upload = ctk.CTkButton(footer, text="Upload", command=self.upload_file, width=80)
        self.btn_upload.pack(side="right", padx=5, pady=5)

        self.btn_download = ctk.CTkButton(footer, text="Download", command=self.download_selected, width=80)
        self.btn_download.pack(side="right", padx=5, pady=5)
        
        self.btn_rename = ctk.CTkButton(footer, text="Rename", command=self.rename_selected, width=80, fg_color="#E0A800", hover_color="#B08800")
        self.btn_rename.pack(side="right", padx=5, pady=5)

        self.btn_delete = ctk.CTkButton(footer, text="Delete", command=self.delete_selected, width=80, fg_color="#D32F2F", hover_color="#B71C1C")
        self.btn_delete.pack(side="right", padx=5, pady=5)

    # --- Events ---

    def on_device_connected(self):
        self.refresh_files()

    def go_home(self):
        self.current_path = "/sdcard/"
        self.refresh_files()

    def go_up(self):
        if self.current_path == "/": return
        parent = os.path.dirname(self.current_path.rstrip("/"))
        if not parent.endswith("/"): parent += "/"
        if not parent: parent = "/"
        self.current_path = parent
        self.refresh_files()

    def on_path_entry(self, event=None):
        new_path = self.entry_path.get().strip()
        if not new_path.endswith("/"): new_path += "/"
        self.current_path = new_path
        self.refresh_files()

    def refresh_files(self):
        if not self.adb_manager.connected_device:
            self.lbl_status.configure(text="No device connected.")
            return

        self.entry_path.delete(0, 'end')
        self.entry_path.insert(0, self.current_path)
        self.lbl_status.configure(text=f"Loading {self.current_path}...")
        
        # Clear list
        for w in self.row_widgets:
            w.destroy()
        self.row_widgets = []
        self.selected_items.clear()
        self.chk_select_all.deselect()

        def _fetch():
            files = self.adb_manager.list_files(self.current_path)
            self.after(0, lambda: self.display_files(files))

        threading.Thread(target=_fetch, daemon=True).start()

    def display_files(self, files):
        self.file_items = files
        
        if not files:
            ctk.CTkLabel(self.list_frame, text="(Empty folder)").pack(pady=20)
            self.lbl_status.configure(text=f"Loaded 0 items.")
            return

        # Create rows
        for item in files:
            row = FileRow(
                self.list_frame, 
                item, 
                selected=False,
                on_click=self.on_row_click,
                on_right_click=self.on_row_right_click,
                on_double_click=self.on_row_double_click
            )
            row.pack(fill="x", pady=1)
            self.row_widgets.append(row)
        
        self.lbl_status.configure(text=f"Loaded {len(files)} items.")

    # --- Interaction ---

    def on_row_click(self, item, modifier=0):
        # Modifier: 0=None, 1=Ctrl, 2=Shift (not impl)
        # However, FileRow click event might come from checkbox toggle too.
        # But if it comes from row click:
        name = item['name']
        
        if modifier == 1: # Ctrl: toggle this one, keep others
            if name in self.selected_items:
                self.selected_items.remove(name)
            else:
                self.selected_items.add(name)
        else: # Simple click: Select ONLY this one (unless it was a checkbox click?)
            # Refine: If user clicks Checkbox, modifier is irrelevant, we just toggle.
            # But the row widget click handler logic needs to be distinct. 
            # Let's simplify: Click on row body -> Select Single. Ctrl+Click -> Toggle. 
            # Click on Checkbox -> Toggle (handled by checkbox command).
            
            # The FileRow calls on_click with modifier. 
            # If modifier is 0, we clear others and select this one.
            self.selected_items.clear()
            self.selected_items.add(name)

        self._update_selection_visuals()

    def on_row_double_click(self, item):
        if item['type'] == 'dir':
            self.current_path += item['name'] + "/"
            self.refresh_files()

    def on_row_right_click(self, event, item):
        # Select this item if not selected, unless multiple are selected
        if item['name'] not in self.selected_items:
            self.selected_items.clear()
            self.selected_items.add(item['name'])
            self._update_selection_visuals()
        
        self.last_right_clicked_item = item
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()

    def toggle_select_all(self):
        state = self.chk_select_all.get()
        self.selected_items.clear()
        if state:
            for item in self.file_items:
                self.selected_items.add(item['name'])
        
        self._update_selection_visuals()

    def _update_selection_visuals(self):
        count = len(self.selected_items)
        self.lbl_status.configure(text=f"{count} items selected.")
        
        for row in self.row_widgets:
            is_sel = row.item['name'] in self.selected_items
            row.set_selected(is_sel)
        
        # Update buttons state
        state = "normal" if count > 0 else "disabled"
        self.btn_download.configure(state=state)
        self.btn_delete.configure(state=state)
        self.btn_rename.configure(state="normal" if count == 1 else "disabled") # Rename only 1 at a time usually

    # --- Actions ---

    def create_folder(self):
        dialog = ctk.CTkInputDialog(text="Folder Name:", title="New Folder")
        name = dialog.get_input()
        if name:
            path = self.current_path + name
            
            def cb(success, msg):
                self.after(0, lambda: self.lbl_status.configure(text=msg))
                if success:
                    self.after(500, self.refresh_files)
            
            self.adb_manager.create_directory(path, cb)

    def delete_selected(self):
        if not self.selected_items: return
        
        count = len(self.selected_items)
        if not tkinter.messagebox.askyesno("Confirm Delete", f"Delete {count} items? This cannot be undone."):
            return

        # Prepare paths
        paths = [self.current_path + name for name in self.selected_items]
        
        self.lbl_status.configure(text="Deleting...")

        def _run():
            # ADB `rm` can take multiple args? Yes usually.
            # But simpler to just loop or join. `rm -rf path1 path2 ...` works.
            # However adb shell argument limits exist.
            # Safer to delete one by one or in chunks.
            
            for p in paths:
                # We use internal blocking delete for now or enhance ADBManager to take list.
                # Let's call ADBManager.delete_file for each (it spawns thread, so this spawns N threads... bad).
                # Better: call adb command directly here or make ADBManager.delete_many.
                # For now, let's just use ADBManager.run_command directly in this thread.
                
                cmd = ["-s", self.adb_manager.connected_device, "shell", "rm", "-rf", p]
                self.adb_manager.run_command(cmd)
            
            self.after(0, self.refresh_files)

        threading.Thread(target=_run, daemon=True).start()

    def rename_selected(self):
        if len(self.selected_items) != 1: return
        name = list(self.selected_items)[0]
        
        dialog = ctk.CTkInputDialog(text=f"Rename '{name}' to:", title="Rename")
        new_name = dialog.get_input()
        if new_name and new_name != name:
             old_path = self.current_path + name
             new_path = self.current_path + new_name
             
             self.adb_manager.rename_file(old_path, new_path, lambda s, m: (
                 self.after(0, lambda: self.lbl_status.configure(text=m)),
                 self.after(500, self.refresh_files)
             ))

    def download_selected(self):
        if not self.selected_items: return
        
        # If multiple, ask for Folder. If single, ask for File (saveto).
        count = len(self.selected_items)
        
        if count == 1:
            item_name = list(self.selected_items)[0]
            # Check if dir
            is_dir = next((i['type'] == 'dir' for i in self.file_items if i['name'] == item_name), False)
            
            if is_dir:
                 local_dir = tkinter.filedialog.askdirectory()
                 if not local_dir: return
                 remote = self.current_path + item_name
                 # adb pull /sdcard/Folder C:/Local/
                 # result: C:/Local/Folder
                 self.adb_manager.pull_file(remote, local_dir, lambda s,m: self.lbl_status.configure(text=m))
            else:
                 local_path = tkinter.filedialog.asksaveasfilename(initialfile=item_name)
                 if not local_path: return
                 remote = self.current_path + item_name
                 self.adb_manager.pull_file(remote, local_path, lambda s,m: self.lbl_status.configure(text=m))
        else:
            # Multiple
            local_dir = tkinter.filedialog.askdirectory()
            if not local_dir: return
            
            self.lbl_status.configure(text="Downloading multiple files...")
            
            def _run():
                for name in self.selected_items:
                    remote = self.current_path + name
                    # adb pull remote local_dir
                    self.adb_manager.run_command(["-s", self.adb_manager.connected_device, "pull", remote, local_dir])
                
                self.after(0, lambda: self.lbl_status.configure(text="Download complete."))

            threading.Thread(target=_run, daemon=True).start()

    def upload_file(self):
        # We allow uploading multiple files
        files = tkinter.filedialog.askopenfilenames()
        if not files: return
        
        self.lbl_status.configure(text="Starting upload...")
        
        def _run():
            count = 0
            for f in files:
                fname = os.path.basename(f)
                remote = self.current_path + fname
                self.after(0, lambda n=fname: self.lbl_status.configure(text=f"Uploading {n}..."))
                
                cmd = ["-s", self.adb_manager.connected_device, "push", f, remote]
                subprocess.run(["adb"] + cmd, capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW if subprocess.os.name == 'nt' else 0)
                count += 1
            
            self.after(0, lambda: self.lbl_status.configure(text=f"Uploaded {count} files."))
            self.after(1000, self.refresh_files)

        threading.Thread(target=_run, daemon=True).start()

    def on_open_context(self):
        # Trigger default action (enter folder or download)
        if len(self.selected_items) == 1:
            name = list(self.selected_items)[0]
            # find item
            item = next((i for i in self.file_items if i['name'] == name), None)
            if item and item['type'] == 'dir':
                self.on_row_double_click(item)
            else:
                self.download_selected()

    def show_properties(self):
        if not self.selected_items: return
        msg = ""
        for name in self.selected_items:
            item = next((i for i in self.file_items if i['name'] == name), None)
            if item:
                msg += f"Name: {item['name']}\nType: {item['type']}\nSize: {item.get('size','?')}\nDate: {item.get('date','?')}\nPerms: {item.get('permissions','?')}\n\n"
        
        tkinter.messagebox.showinfo("Properties", msg)

    def toggle_search(self):
        dialog = ctk.CTkInputDialog(text="File name to search:", title="Recursive Search")
        query = dialog.get_input()
        if not query: return
        
        self.lbl_status.configure(text=f"Searching for '{query}'...")
        # Search is robust in ADBManager but returns absolute paths.
        # We should display them. The List can handle it if we adapt it.
        # Ideally, we open a "Search Results" view or just replace the list content temporarily.
        
        def cb(results):
             self.after(0, lambda: self._show_search_results(results))
        
        self.adb_manager.search_files(self.current_path, query, cb)

    def _show_search_results(self, results):
        self.lbl_status.configure(text=f"Found {len(results)} matches.")
        
        # Clear list
        for w in self.row_widgets: w.destroy()
        self.row_widgets = []
        self.selected_items.clear()
        
        self.file_items = results # Replace current view model
        # results have 'name' as full path.
        
        for item in results:
             # Create row but display full name
             row = FileRow(
                self.list_frame, 
                item, 
                selected=False,
                on_click=self.on_row_click,
                on_right_click=self.on_row_right_click
                # Double click on search result? -> Maybe go to that folder? 
                # Or just download. Let's make it download or open folder.
             )
             row.pack(fill="x", pady=1)
             self.row_widgets.append(row)
