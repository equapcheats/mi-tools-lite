
import customtkinter as ctk
import threading
import tkinter.filedialog
import os

class FileTransferTab(ctk.CTkFrame):
    def __init__(self, master, adb_manager):
        super().__init__(master)
        self.adb_manager = adb_manager
        
        self.current_path = "/sdcard/"
        self.file_list = []
        
        # Grid layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # 1. Header
        self.header_frame = ctk.CTkFrame(self)
        self.header_frame.grid(row=0, column=0, padx=20, pady=10, sticky="ew")
        
        self.label_title = ctk.CTkLabel(self.header_frame, text="File Transfer", font=("Roboto Medium", 18))
        self.label_title.pack(side="left", padx=10, pady=10)

        # 2. Controls / Navbar
        self.nav_frame = ctk.CTkFrame(self)
        self.nav_frame.grid(row=1, column=0, padx=20, pady=5, sticky="ew")

        self.btn_up = ctk.CTkButton(self.nav_frame, text="⬆ Up", width=50, command=self.go_up)
        self.btn_up.pack(side="left", padx=5, pady=5)
        
        self.btn_refresh = ctk.CTkButton(self.nav_frame, text="↻", width=40, command=self.refresh_files)
        self.btn_refresh.pack(side="left", padx=5, pady=5)

        self.entry_path = ctk.CTkEntry(self.nav_frame, placeholder_text="/path/to/dir")
        self.entry_path.pack(side="left", fill="x", expand=True, padx=5, pady=5)
        self.entry_path.bind("<Return>", self.on_path_entry)

        self.btn_search = ctk.CTkButton(self.nav_frame, text="Search", width=80, command=self.toggle_search)
        self.btn_search.pack(side="right", padx=5)

        # 3. File List
        self.list_frame = ctk.CTkScrollableFrame(self, label_text="Files")
        self.list_frame.grid(row=2, column=0, padx=20, pady=5, sticky="nsew")

        # 4. Actions
        self.action_frame = ctk.CTkFrame(self)
        self.action_frame.grid(row=3, column=0, padx=20, pady=20, sticky="ew")

        self.status_label = ctk.CTkLabel(self.action_frame, text="Ready", anchor="w")
        self.status_label.pack(side="left", padx=10, fill="x", expand=True)

        self.btn_upload = ctk.CTkButton(self.action_frame, text="Upload File", command=self.upload_file)
        self.btn_upload.pack(side="right", padx=5, pady=10)
        
        self.btn_rename = ctk.CTkButton(self.action_frame, text="Rename", state="disabled", command=self.rename_selected, fg_color="#E0A800", hover_color="#B08800")
        self.btn_rename.pack(side="right", padx=5, pady=10)

        self.btn_delete = ctk.CTkButton(self.action_frame, text="Delete", state="disabled", command=self.delete_selected, fg_color="#D32F2F", hover_color="#B71C1C")
        self.btn_delete.pack(side="right", padx=5, pady=10)

        self.btn_download = ctk.CTkButton(self.action_frame, text="Download Selected", state="disabled", command=self.download_selected)
        self.btn_download.pack(side="right", padx=5, pady=10)

        # State
        self.selected_item = None # {'name': '...', 'type': 'dir/file'}
        self.item_widgets = {}

    def on_device_connected(self):
        self.status_label.configure(text="Connected.")
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
            self.status_label.configure(text="No device connected.")
            return

        self.entry_path.delete(0, 'end')
        self.entry_path.insert(0, self.current_path)
        self.status_label.configure(text=f"Loading {self.current_path}...")

        def _fetch():
            files = self.adb_manager.list_files(self.current_path)
            self.after(0, lambda: self.display_files(files))

        threading.Thread(target=_fetch, daemon=True).start()

    def display_files(self, files):
        self.file_list = files
        for w in self.list_frame.winfo_children():
            w.destroy()
        
        self.item_widgets = {}
        self.selected_item = None
        self.btn_download.configure(state="disabled", text="Download / Open")
        self.btn_delete.configure(state="disabled")
        self.btn_rename.configure(state="disabled")

        if not files:
            ctk.CTkLabel(self.list_frame, text="(Empty or Access Denied)").pack(pady=10)
            self.status_label.configure(text="Ready.")
            return

        for item in files:
            f = ctk.CTkFrame(self.list_frame, fg_color="transparent")
            f.pack(fill="x", padx=2, pady=1)

            # Icon
            icon = "📁" if item['type'] == 'dir' else "📄"
            fg = "white" if item['type'] == 'file' else "#3B8ED0"
            
            # Display text with size if available
            display_text = f"{icon}  {item['name']}"
            if 'size' in item:
                 display_text += f"   ({item['size']})"

            btn = ctk.CTkButton(f, text=display_text, anchor="w", fg_color="transparent", 
                                text_color=fg, hover_color="#444",
                                command=lambda i=item: self.on_item_click(i))
            btn.pack(fill="x")
            self.item_widgets[item['name']] = btn

        self.status_label.configure(text=f"Loaded {len(files)} items.")

    def on_item_click(self, item):
        # Deselect old
        if self.selected_item and self.selected_item['name'] in self.item_widgets:
             self.item_widgets[self.selected_item['name']].configure(fg_color="transparent")

        self.selected_item = item
        
        # Highlight new
        if item['name'] in self.item_widgets:
             self.item_widgets[item['name']].configure(fg_color="#3A3A4A")

        self.btn_delete.configure(state="normal")
        self.btn_rename.configure(state="normal")
        
        if item['type'] == 'dir':
            self.btn_download.configure(text="Open Folder", state="normal", command=self.enter_selected_folder)
        else:
            self.btn_download.configure(text="Download File", state="normal", command=self.download_selected)
    
    def enter_selected_folder(self):
        if self.selected_item and self.selected_item['type'] == 'dir':
            self.current_path += self.selected_item['name'] + "/"
            self.refresh_files()

    def download_selected(self):
        if not self.selected_item: return
        
        remote_file = self.current_path + self.selected_item['name']
        
        # Ask where to save
        local_path = tkinter.filedialog.asksaveasfilename(initialfile=self.selected_item['name'])
        if not local_path: return

        self.status_label.configure(text=f"Downloading {self.selected_item['name']}...")
        
        def cb(success, msg):
             self.after(0, lambda: self.status_label.configure(text=msg))

        self.adb_manager.pull_file(remote_file, local_path, cb)

    def upload_file(self):
        files = tkinter.filedialog.askopenfilenames()
        if not files: return
        
        self.status_label.configure(text="Starting upload...")
        
        def _upload_thread():
            count = 0
            total = len(files)
            for f in files:
                fname = os.path.basename(f)
                remote = self.current_path + fname
                
                # We use a blocking call to run_command for push to ensure sequential execution in this thread
                # But ADBManager.push_file spawns a thread. We will use run_command directly here or
                # just wait a bit. 
                # Better: ADBManager.push_file is designed for single async calls.
                # Let's direct call adb push here since we are already in a background thread.
                
                self.after(0, lambda n=fname: self.status_label.configure(text=f"Uploading {n}..."))
                
                cmd = ["-s", self.adb_manager.connected_device, "push", f, remote]
                # We need to subprocess directly as we are in a thread and want to block THIS thread
                import subprocess
                try:
                    subprocess.run(["adb"] + cmd, capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW if subprocess.os.name == 'nt' else 0)
                    count += 1
                except Exception as e:
                    print(f"Upload failed: {e}")

            self.after(0, lambda: self.status_label.configure(text=f"Uploaded {count}/{total} files."))
            self.after(1000, self.refresh_files)

        threading.Thread(target=_upload_thread, daemon=True).start()

    def delete_selected(self):
        if not self.selected_item: return
        
        # Check if item name is full path (from search) or relative (from list)
        is_search_result = self.selected_item['name'].startswith('/')
        path = self.selected_item['name'] if is_search_result else self.current_path + self.selected_item['name']
        display_name = os.path.basename(path)

        import tkinter.messagebox
        if not tkinter.messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete {display_name}?"):
            return

        self.status_label.configure(text=f"Deleting {display_name}...")
        
        def cb(success, msg):
             self.after(0, lambda: self.status_label.configure(text=msg))
             self.after(500, self.refresh_files)

        self.adb_manager.delete_file(path, cb)

    def rename_selected(self):
        if not self.selected_item: return
        
        is_search_result = self.selected_item['name'].startswith('/')
        old_path = self.selected_item['name'] if is_search_result else self.current_path + self.selected_item['name']
        old_name = os.path.basename(old_path)
        parent_dir = os.path.dirname(old_path)

        dialog = ctk.CTkInputDialog(text=f"Rename '{old_name}' to:", title="Rename")
        new_name = dialog.get_input()
        
        if new_name and new_name != old_name:
             new_path = os.path.join(parent_dir, new_name).replace("\\", "/")
             
             self.status_label.configure(text=f"Renaming to {new_name}...")
             
             def cb(success, msg):
                  self.after(0, lambda: self.status_label.configure(text=msg))
                  self.after(500, self.refresh_files)

             self.adb_manager.rename_file(old_path, new_path, cb)

    def toggle_search(self):
        dialog = ctk.CTkInputDialog(text="Search file name in current folder tree:", title="Search")
        query = dialog.get_input()
        if query:
            self.status_label.configure(text=f"Searching for '{query}'...")
            
            def _cb(results):
                self.after(0, lambda: self.display_search_results(results))
            
            self.adb_manager.search_files(self.current_path, query, _cb)

    def display_search_results(self, files):
        # Special display for search results (absolute paths)
        for w in self.list_frame.winfo_children():
            w.destroy()
        
        self.item_widgets = {}
        self.selected_item = None
        self.btn_download.configure(state="disabled")
        self.btn_delete.configure(state="disabled")
        self.btn_rename.configure(state="disabled")

        if not files:
            ctk.CTkLabel(self.list_frame, text="No matches found.").pack(pady=10)
            self.status_label.configure(text="Ready.")
            return

        for item in files:
            f = ctk.CTkFrame(self.list_frame, fg_color="transparent")
            f.pack(fill="x", padx=2, pady=1)

            btn = ctk.CTkButton(f, text=f"🔍 {item['name']}", anchor="w", fg_color="transparent", 
                                hover_color="#444",
                                command=lambda i=item: self.on_search_item_click(i))
            btn.pack(fill="x")
            self.item_widgets[item['name']] = btn
        
        self.status_label.configure(text=f"Found {len(files)} matches.")

    def on_search_item_click(self, item):
         # Search results are absolute paths.
         self.selected_item = item # name is full path
         if item['name'] in self.item_widgets:
             for k, v in self.item_widgets.items(): v.configure(fg_color="transparent")
             self.item_widgets[item['name']].configure(fg_color="#3A3A4A")

         self.btn_download.configure(text="Download File", state="normal", command=self.download_search_result)
         self.btn_delete.configure(state="normal")
         self.btn_rename.configure(state="normal")
    
    def download_search_result(self):
        if not self.selected_item: return
        # Ensure we just get the filename for the local save dialog
        local = tkinter.filedialog.asksaveasfilename(initialfile=os.path.basename(self.selected_item['name']))
        if local:
             self.adb_manager.pull_file(self.selected_item['name'], local, lambda s,m: self.after(0, lambda: self.status_label.configure(text=m)))
