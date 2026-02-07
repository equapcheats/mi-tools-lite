
import customtkinter as ctk
import threading

class InspectorTab(ctk.CTkFrame):
    def __init__(self, master, adb_manager):
        super().__init__(master)
        self.adb_manager = adb_manager

        self.grid_columnconfigure(0, weight=1)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(4, weight=1) # Output area expands


        self.header = ctk.CTkLabel(self, text="System & App Inspector", font=("Roboto Medium", 18))
        self.header.grid(row=0, column=0, pady=10)

        # 1. Target Package Input
        self.target_frame = ctk.CTkFrame(self)
        self.target_frame.grid(row=1, column=0, padx=20, pady=5, sticky="ew")
        
        self.lbl_pkg = ctk.CTkLabel(self.target_frame, text="Target Package:", width=100)
        self.lbl_pkg.pack(side="left", padx=5)
        
        self.entry_pkg = ctk.CTkEntry(self.target_frame, placeholder_text="com.example.app")
        self.entry_pkg.pack(side="left", fill="x", expand=True, padx=5)

        # App Specific Buttons
        self.btn_why_dead = ctk.CTkButton(self.target_frame, text="Why is it dead?", command=self.diagnose_app, width=120, fg_color="#C92C2C", hover_color="#992222")
        self.btn_why_dead.pack(side="right", padx=5, pady=5)

        self.btn_notif = ctk.CTkButton(self.target_frame, text="Notif. Channels", command=self.check_notifs, width=120)
        self.btn_notif.pack(side="right", padx=5, pady=5)
        
        self.btn_perms = ctk.CTkButton(self.target_frame, text="Perm. Flags", command=self.check_perms, width=100)
        self.btn_perms.pack(side="right", padx=5, pady=5)

        # 2. General Inspections Grid
        self.ops_frame = ctk.CTkFrame(self)
        self.ops_frame.grid(row=2, column=0, padx=20, pady=10, sticky="ew")

        # Row 1
        self.btn_doze = ctk.CTkButton(self.ops_frame, text="Doze/Idle State", command=lambda: self.run_dump(["deviceidle"], "Doze Status"))
        self.btn_doze.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

        self.btn_bg_exec = ctk.CTkButton(self.ops_frame, text="Bg Execution Limits", command=lambda: self.run_dump(["activity", "bg-execution"], "Bg Execution"))
        self.btn_bg_exec.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        self.btn_netpol = ctk.CTkButton(self.ops_frame, text="Network Policy", command=lambda: self.run_dump(["netpolicy"], "Network Policy"))
        self.btn_netpol.grid(row=0, column=2, padx=5, pady=5, sticky="ew")

        self.btn_services = ctk.CTkButton(self.ops_frame, text="Running Services", command=lambda: self.run_dump(["activity", "services"], "Services"))
        self.btn_services.grid(row=0, column=3, padx=5, pady=5, sticky="ew")

        # Row 2
        self.btn_joyose = ctk.CTkButton(self.ops_frame, text="Joyose Status", command=lambda: self.run_dump(["package", "com.xiaomi.joyose"], "Joyose Internals"))
        self.btn_joyose.grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        
        self.btn_thermal = ctk.CTkButton(self.ops_frame, text="Thermal Zones", command=lambda: self.run_dump(["thermalservice"], "Thermal Status"))
        self.btn_thermal.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        self.btn_game = ctk.CTkButton(self.ops_frame, text="Game Mode API", command=lambda: self.run_dump(["game"], "Game API Status"))
        self.btn_game.grid(row=1, column=2, padx=5, pady=5, sticky="ew")

        self.btn_fast_reboot = ctk.CTkButton(self.ops_frame, text="Fast Reboot (Userspace)", command=self.fast_reboot, fg_color="#E0a800", hover_color="#c69500", text_color="black")
        self.btn_fast_reboot.grid(row=1, column=3, padx=5, pady=5, sticky="ew")
        
        # Configure columns to stretch
        for i in range(4):
            self.ops_frame.grid_columnconfigure(i, weight=1)


        # 3. Manual Shell Command
        self.shell_frame = ctk.CTkFrame(self)
        self.shell_frame.grid(row=3, column=0, padx=20, pady=5, sticky="ew")

        self.lbl_shell = ctk.CTkLabel(self.shell_frame, text="ADB Shell Command:", width=120)
        self.lbl_shell.pack(side="left", padx=5)

        self.entry_shell = ctk.CTkEntry(self.shell_frame, placeholder_text="e.g. pm list users")
        self.entry_shell.pack(side="left", fill="x", expand=True, padx=5)
        self.entry_shell.bind("<Return>", lambda e: self.run_custom_shell())

        self.btn_run_shell = ctk.CTkButton(self.shell_frame, text="Run Command", command=self.run_custom_shell, width=100)
        self.btn_run_shell.pack(side="right", padx=5, pady=5)

        # 4. Output Viewer
        self.txt_output = ctk.CTkTextbox(self, font=("Consolas", 12))
        self.txt_output.grid(row=4, column=0, padx=20, pady=10, sticky="nsew")
        self.txt_output.insert("1.0", "Select a function to view internal diagnostics...")

    def run_custom_shell(self):
        cmd_str = self.entry_shell.get().strip()
        if not cmd_str: return
        
        if not self.adb_manager.connected_device:
            self.log("Error: No device connected.")
            return

        self.log(f"> adb shell {cmd_str}")
        
        def _run():
            # Split command string into args (simple split by space, ideally shlex but this is simple)
            import shlex
            try:
                args = shlex.split(cmd_str)
            except:
                args = cmd_str.split()
                
            out, err = self.adb_manager.run_command(["-s", self.adb_manager.connected_device, "shell"] + args)
            content = out + "\n" + err
            self.after(0, lambda: self.log(content, append=True))
            
        threading.Thread(target=_run, daemon=True).start()


    def fast_reboot(self):
        if not self.adb_manager.connected_device: return
        self.log("Executing Fast Reboot (stop; start)...")
        # Need root usually or specific permissions, but 'stop' 'start' works on some envs or just kills shell.
        # It restarts the Android runtime (zygote).
        def _run():
            self.adb_manager.run_command(["-s", self.adb_manager.connected_device, "shell", "stop"])
            import time
            time.sleep(1)
            self.adb_manager.run_command(["-s", self.adb_manager.connected_device, "shell", "start"])
            self.log("Fast Reboot command sent. Device interface should restart.")
        threading.Thread(target=_run, daemon=True).start()

    def run_dump(self, args, title):
        if not self.adb_manager.connected_device:
            self.log("Error: No device connected.")
            return

        self.log(f"Fetching {title}...\n(adb shell dumpsys {' '.join(args)})")

        def _run():
            out, err = self.adb_manager.run_command(["-s", self.adb_manager.connected_device, "shell", "dumpsys"] + args)
            content = out + "\n" + err
            self.after(0, lambda: self.log(content, append=False))
        
        threading.Thread(target=_run, daemon=True).start()

    def diagnose_app(self):
        pkg = self.entry_pkg.get().strip()
        if not pkg:
            self.log("Please enter a package name first.")
            return
            
        self.log(f"Diagnosing {pkg} (Why is it dead?)...")
        
        def _run():
            # 1. Activity Package dump
            out1, _ = self.adb_manager.run_command(["-s", self.adb_manager.connected_device, "shell", "dumpsys", "activity", "package", pkg])
            
            # 2. OOM dump (grep for pkg?) - keeping it simple, full oom dump might be big
            out2, _ = self.adb_manager.run_command(["-s", self.adb_manager.connected_device, "shell", "dumpsys", "oom"])
            
            summary =  f"--- APP STATE ({pkg}) ---\n"
            summary += out1 if out1 else "No activity info found.\n"
            
            summary += f"\n--- MEMORY / OOM STATS ---\n"
            # Filter OOM for package if possible
            if pkg in out2:
                lines = [line for line in out2.splitlines() if pkg in line]
                summary += "\n".join(lines)
            else:
                summary += "App not found in active OOM list (likely stopped/killed)."

            self.after(0, lambda: self.log(summary, append=False))

        threading.Thread(target=_run, daemon=True).start()

    def check_notifs(self):
        pkg = self.entry_pkg.get().strip()
        if not pkg: return
        self.run_dump(["notification", pkg], f"Notification Channels: {pkg}")

    def check_perms(self):
        pkg = self.entry_pkg.get().strip()
        if not pkg: return
        self.run_dump(["package", pkg], f"Package & Permissions: {pkg}")

    def log(self, text, append=True):
        self.txt_output.configure(state="normal")
        if not append:
            self.txt_output.delete("1.0", "end")
        self.txt_output.insert("end", text + "\n")
        self.txt_output.configure(state="disabled")
        self.txt_output.see("end")
