
import customtkinter as ctk
import threading
import subprocess

class TaskManagerTab(ctk.CTkFrame):
    def __init__(self, master, adb_manager):
        super().__init__(master)
        self.adb_manager = adb_manager

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1) # Search list area

        # 1. Header & Controls
        self.header_frame = ctk.CTkFrame(self)
        self.header_frame.grid(row=0, column=0, padx=20, pady=10, sticky="ew")

        self.label_header = ctk.CTkLabel(self.header_frame, text="Task Manager & Process Killer", font=("Roboto Medium", 18))
        self.label_header.pack(pady=10)

        # Process List Controls
        self.controls_frame = ctk.CTkFrame(self)
        self.controls_frame.grid(row=1, column=0, padx=20, pady=5, sticky="ew")

        self.btn_refresh = ctk.CTkButton(self.controls_frame, text="Refresh Processes", command=self.refresh_processes)
        self.btn_refresh.pack(side="left", padx=10, pady=10)

        self.btn_foreground = ctk.CTkButton(self.controls_frame, text="Find Foreground App", command=self.find_foreground, fg_color="#3B8ED0", hover_color="#36719F")
        self.btn_foreground.pack(side="left", padx=10, pady=10)

        self.entry_search = ctk.CTkEntry(self.controls_frame, placeholder_text="Search package name...")
        self.entry_search.pack(side="left", fill="x", expand=True, padx=10)
        self.entry_search.bind("<KeyRelease>", self.filter_list)

        # 2. Process List
        self.list_frame = ctk.CTkScrollableFrame(self, label_text="Running Processes")
        self.list_frame.grid(row=2, column=0, padx=20, pady=10, sticky="nsew")

        # 3. Actions for Selected Process
        self.action_frame = ctk.CTkFrame(self)
        self.action_frame.grid(row=3, column=0, padx=20, pady=20, sticky="ew")

        self.lbl_selected = ctk.CTkLabel(self.action_frame, text="Selected: None", font=("Roboto", 12, "bold"))
        self.lbl_selected.pack(side="top", pady=5, fill="x")

        # Action Buttons
        self.btn_force_stop = ctk.CTkButton(self.action_frame, text="Force Stop (Safe)", command=lambda: self.kill_action("force-stop"), fg_color="#F0ad4e", hover_color="#d08d2e")
        self.btn_force_stop.pack(side="left", padx=10, pady=10, expand=True)

        self.btn_kill = ctk.CTkButton(self.action_frame, text="Kill Process (Hard)", command=lambda: self.kill_action("kill"), fg_color="#C92C2C", hover_color="#992222")
        self.btn_kill.pack(side="left", padx=10, pady=10, expand=True)
        
        self.btn_crash = ctk.CTkButton(self.action_frame, text="Crash (SIGSEGV)", command=lambda: self.kill_action("crash"), fg_color="gray", hover_color="#555")
        self.btn_crash.pack(side="left", padx=10, pady=10, expand=True)

        self.status_label = ctk.CTkLabel(self, text="Ready", text_color="gray")
        self.status_label.grid(row=4, column=0, pady=10)

        # Data
        self.current_processes = [] # List of tuples/dicts: (pid, pkg, name)
        self.selected_pkg = None
        self.selected_pid = None

        self.process_widgets = {}
        self.pending_auto_select = None


    def refresh_processes(self):
        if not self.adb_manager.connected_device:
            self.status_label.configure(text="No device connected.", text_color="red")
            return
            
        self.status_label.configure(text="Fetching process list...", text_color="#3B8ED0")
        
        def _fetch():
            # Command: adb shell ps -A | grep u0_
            # We want to filter for user apps primarily usually starting with u0_
            out, _ = self.adb_manager.run_command(["-s", self.adb_manager.connected_device, "shell", "ps", "-A"])
            
            # Simple manual grep for u0_ if the grep command on device fails or is tricky
            lines = out.splitlines()
            parsed = []
            
            for line in lines:
                if "u0_" in line: # Basic filter for user space apps
                    parts = line.split()
                    # USER PID ... NAME
                    # u0_a157 2461 ... com.miui.home
                    if len(parts) >= 9:
                        user = parts[0]
                        pid = parts[1]
                        name = parts[-1] # Last element usually package name
                        parsed.append({'pid': pid, 'user': user, 'name': name})
            
            # Sort by name
            parsed.sort(key=lambda x: x['name'])
            
            self.after(0, lambda: self.display_processes(parsed))

        threading.Thread(target=_fetch, daemon=True).start()

    def display_processes(self, processes):
        self.current_processes = processes
        for w in self.list_frame.winfo_children():
            w.destroy()
        self.process_widgets = {}
        
        if not processes:
            ctk.CTkLabel(self.list_frame, text="No user processes found running.").pack(pady=20)
            self.status_label.configure(text="No processes found.")
            return

        for p in processes:
            # Row widget
            f = ctk.CTkFrame(self.list_frame, fg_color="transparent")
            f.pack(fill="x", padx=5, pady=2)
            
            # Clickable button or label? Button is easier
            text = f"[{p['pid']}] {p['name']}"
            btn = ctk.CTkButton(f, text=text, anchor="w", fg_color="transparent", border_width=1, text_color=("black", "white"),
                                command=lambda proc=p: self.select_process(proc))
            btn.pack(fill="x")

            btn.pack(fill="x")
            self.process_widgets[p['pid']] = btn
            

            btn.pack(fill="x")
            self.process_widgets[p['pid']] = btn
            
        self.status_label.configure(text=f"Loaded {len(processes)} processes.", text_color="green")
        self.filter_list()
        
        # Auto-select if pending
        if self.pending_auto_select:
            for p in processes:
                # Try exact match first
                if p['name'] == self.pending_auto_select:
                    self.select_process(p)
                    self.pending_auto_select = None
                    break
            
            # If still pending (no exact match), maybe try to select the first one visible?
            # For now, let's just clear it to avoid stuck state
            self.pending_auto_select = None


    def filter_list(self, event=None):
        query = self.entry_search.get().strip().lower()
        
        for p in self.current_processes:
            btn = self.process_widgets.get(p['pid'])
            if not btn: continue
            
            if query in p['name'].lower() or query in p['pid']:
                btn.pack(fill="x", padx=5, pady=2)
                btn.master.pack(fill="x", padx=5, pady=2) # Repack parent frame
            else:
                btn.master.pack_forget() # Hide parent frame


    def select_process(self, proc):
        self.selected_pkg = proc['name']
        self.selected_pid = proc['pid']
        self.lbl_selected.configure(text=f"Selected: {proc['name']} (PID: {proc['pid']})")
        
        # Reset colors of other buttons? (Optional optimization omitted for Lite version)

    def find_foreground(self):
        if not self.adb_manager.connected_device: return
        
        def _run():
            # Try mCurrentFocus first
            out, _ = self.adb_manager.run_command(["-s", self.adb_manager.connected_device, "shell", "dumpsys", "window", "|", "grep", "mCurrentFocus"])
            # Format: mCurrentFocus=Window{... u0 com.example/com.example.Activity}
            if not out:
                 out, _ = self.adb_manager.run_command(["-s", self.adb_manager.connected_device, "shell", "dumpsys", "activity", "activities", "|", "grep", "mResumedActivity"])

            if out:
                # Extract package name loosely
                import re
                match = re.search(r'u0 ([\w\.]+)', out) # basic regex for pkg
                if not match:
                    match = re.search(r' ([\w\.]+)/', out)
                

                if match:
                    pkg = match.group(1)
                    self.after(0, lambda: self.entry_search.delete(0, 'end'))
                    self.after(0, lambda: self.entry_search.insert(0, pkg))
                    
                    # Store pending selection and refresh
                    self.pending_auto_select = pkg
                    self.after(0, lambda: self.status_label.configure(text=f"Foreground: {pkg}. Refreshing..."))
                    self.after(100, self.refresh_processes)
                else:
                    self.after(0, lambda: self.status_label.configure(text=f"Could not parse foreground app: {out[:50]}..."))
            else:
                 self.after(0, lambda: self.status_label.configure(text="No foreground info found."))


        threading.Thread(target=_run, daemon=True).start()

    def kill_action(self, action_type):
        if not self.selected_pkg:
            self.status_label.configure(text="No process selected.", text_color="red")
            return
            
        pkg = self.selected_pkg
        pid = self.selected_pid
        
        self.status_label.configure(text=f"Executing {action_type} on {pkg}...", text_color="yellow")

        def _run():
            if action_type == "force-stop":
                # am force-stop pkg
                self.adb_manager.run_command(["-s", self.adb_manager.connected_device, "shell", "am", "force-stop", pkg])
                
            elif action_type == "kill":
                # am kill pkg (background kill) or kill -9 PID (hard kill)
                # Let's do kill -9 if we have PID, it's surer for "Task Manager" feel.
                if pid:
                    self.adb_manager.run_command(["-s", self.adb_manager.connected_device, "shell", "kill", "-9", pid])
                else:
                    self.adb_manager.run_command(["-s", self.adb_manager.connected_device, "shell", "am", "kill", pkg])

            elif action_type == "crash":
                # kill -11 PID
                if pid:
                    self.adb_manager.run_command(["-s", self.adb_manager.connected_device, "shell", "kill", "-11", pid])
                else:
                     self.after(0, lambda: self.status_label.configure(text="Need PID for crash.", text_color="red"))
                     return

            # Refresh after short delay
            import time
            time.sleep(1)
            self.refresh_processes()
            self.after(0, lambda: self.status_label.configure(text=f"Executed {action_type}.", text_color="green"))

        threading.Thread(target=_run, daemon=True).start()
