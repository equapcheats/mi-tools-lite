
import customtkinter as ctk
import threading

class PowerTab(ctk.CTkFrame):
    def __init__(self, master, adb_manager):
        super().__init__(master)
        self.adb_manager = adb_manager

        self.grid_columnconfigure(0, weight=1)
        
        # Header
        self.header = ctk.CTkLabel(self, text="Power & Performance", font=("Roboto Medium", 18))
        self.header.pack(pady=20)

        # 1. Battery Saver Section
        self.saver_frame = ctk.CTkFrame(self)
        self.saver_frame.pack(fill="x", padx=20, pady=10)
        
        self.lbl_saver = ctk.CTkLabel(self.saver_frame, text="Android Battery Saver", font=("Roboto", 14, "bold"))
        self.lbl_saver.pack(anchor="w", padx=10, pady=(10, 5))
        
        self.btn_saver_on = ctk.CTkButton(self.saver_frame, text="Enable Saver", command=lambda: self.set_low_power("1"), fg_color="#2CC985", hover_color="#229966")
        self.btn_saver_on.pack(side="left", padx=10, pady=10)

        self.btn_saver_off = ctk.CTkButton(self.saver_frame, text="Disable Saver", command=lambda: self.set_low_power("0"), fg_color="#C92C2C", hover_color="#992222")
        self.btn_saver_off.pack(side="left", padx=10, pady=10)

        self.btn_check_saver = ctk.CTkButton(self.saver_frame, text="Check Status", command=self.check_low_power, width=100)
        self.btn_check_saver.pack(side="right", padx=10, pady=10)
        
        self.lbl_saver_status = ctk.CTkLabel(self.saver_frame, text="Status: Unknown", text_color="gray")
        self.lbl_saver_status.pack(side="right", padx=10, pady=10)

        # 2. Doze Section
        self.doze_frame = ctk.CTkFrame(self)
        self.doze_frame.pack(fill="x", padx=20, pady=10)

        self.lbl_doze = ctk.CTkLabel(self.doze_frame, text="Doze / Deep Sleep", font=("Roboto", 14, "bold"))
        self.lbl_doze.pack(anchor="w", padx=10, pady=(10, 5))

        self.btn_force_idle = ctk.CTkButton(self.doze_frame, text="Force Idle (Deep Sleep)", command=self.force_idle)
        self.btn_force_idle.pack(side="left", padx=10, pady=10)

        self.btn_unforce = ctk.CTkButton(self.doze_frame, text="Unforce / Wake Up", command=self.unforce_idle)
        self.btn_unforce.pack(side="left", padx=10, pady=10)

        # 3. Performance / Game Booster
        self.boost_frame = ctk.CTkFrame(self)
        self.boost_frame.pack(fill="x", padx=20, pady=10)

        self.lbl_boost = ctk.CTkLabel(self.boost_frame, text="Performance & Game Booster", font=("Roboto", 14, "bold"))
        self.lbl_boost.pack(anchor="w", padx=10, pady=(10, 5))

        self.btn_boost_on = ctk.CTkButton(self.boost_frame, text="Enable Game Booster", command=self.enable_boost, fg_color="#3B8ED0", hover_color="#36719F")
        self.btn_boost_on.pack(side="left", padx=10, pady=10)

        self.btn_boost_off = ctk.CTkButton(self.boost_frame, text="Disable Game Booster", command=self.disable_boost, fg_color="gray")
        self.btn_boost_off.pack(side="left", padx=10, pady=10)

        # Status Bar
        self.status_label = ctk.CTkLabel(self, text="", text_color="green")
        self.status_label.pack(pady=10)

    def run_cmd(self, cmd_args, success_msg):
        if not self.adb_manager.connected_device:
            self.status_label.configure(text="No device connected.", text_color="red")
            return

        def _run():
            out, err = self.adb_manager.run_command(["-s", self.adb_manager.connected_device] + cmd_args)
            # Most settings/dumpsys commands don't return text on success
            if not err:
                self.status_label.configure(text=success_msg, text_color="#2CC985")
            else:
                self.status_label.configure(text=f"Error: {err}", text_color="red")
        
        threading.Thread(target=_run, daemon=True).start()

    def set_low_power(self, val):
        self.run_cmd(["shell", "settings", "put", "global", "low_power", val], 
                     f"Battery Saver Set to {val}")

    def check_low_power(self):
        if not self.adb_manager.connected_device:
            self.lbl_saver_status.configure(text="No device")
            return

        def _check():
            out, _ = self.adb_manager.run_command(["-s", self.adb_manager.connected_device, "shell", "settings", "get", "global", "low_power"])
            if out:
                val = out.strip()
                status = "ON" if val == "1" else "OFF"
                col = "green" if val == "1" else "gray"
                self.lbl_saver_status.configure(text=f"Status: {status}", text_color=col)
        
        threading.Thread(target=_check, daemon=True).start()

    def force_idle(self):
        self.run_cmd(["shell", "dumpsys", "deviceidle", "force-idle"], "Device Forced to Idle/Doze")

    def unforce_idle(self):
        self.run_cmd(["shell", "dumpsys", "deviceidle", "unforce"], "Device Unforced from Idle")

    def enable_boost(self):
        # 1. Low Power OFF
        # 2. Game Booster ON
        if not self.adb_manager.connected_device: return

        def _run():
            # Disable Saver
            self.adb_manager.run_command(["-s", self.adb_manager.connected_device, "shell", "settings", "put", "global", "low_power", "0"])
            # Enable Booster
            self.adb_manager.run_command(["-s", self.adb_manager.connected_device, "shell", "settings", "put", "system", "game_booster", "1"])
            
            self.status_label.configure(text="Performance Mode Enabled (Saver Off + Game Booster On)", text_color="#3B8ED0")

        threading.Thread(target=_run, daemon=True).start()

    def disable_boost(self):
         self.run_cmd(["shell", "settings", "put", "system", "game_booster", "0"], "Game Booster Disabled")
