
import customtkinter as ctk

class RebootTab(ctk.CTkFrame):
    def __init__(self, master, adb_manager):
        super().__init__(master)
        self.adb_manager = adb_manager

        self.grid_columnconfigure(0, weight=1)
        
        self.header = ctk.CTkLabel(self, text="Reboot Options", font=("Roboto Medium", 18))
        self.header.pack(pady=20)
        
        self.options_frame = ctk.CTkScrollableFrame(self)
        self.options_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Helper to create buttons
        def create_btn(text, cmd_arg, desc):
            frame = ctk.CTkFrame(self.options_frame, fg_color="transparent")
            frame.pack(fill="x", pady=5)
            
            btn = ctk.CTkButton(frame, text=text, command=lambda: self.reboot(cmd_arg), width=180)
            btn.pack(side="left", padx=10)
            
            lbl = ctk.CTkLabel(frame, text=desc, text_color="gray", anchor="w")
            lbl.pack(side="left", padx=10, fill="x", expand=True)

        create_btn("Normal Reboot", [], "Standard system restart.")
        create_btn("Reboot Recovery", ["recovery"], "Boot into Stock Recovery or TWRP.")
        create_btn("Reboot Bootloader", ["bootloader"], "Boot into Fastboot mode.")
        create_btn("Reboot EDL", ["edl"], "Emergency Download Mode (Requires auth/older devices).")
        create_btn("Reboot Fastboot", ["fastboot"], "Alias for bootloader (works on many Xiaomis).")

        self.status_label = ctk.CTkLabel(self, text="", text_color="green")
        self.status_label.pack(pady=10)

    def reboot(self, mode_args):
        if not self.adb_manager.connected_device:
            self.status_label.configure(text="No device connected.", text_color="red")
            return
            
        cmd = ["-s", self.adb_manager.connected_device, "reboot"] + mode_args
        self.status_label.configure(text=f"Executing reboot {' '.join(mode_args)}...", text_color="yellow")
        
        # Execute in thread? Reboot is usually fast to return, but device goes offline.
        self.adb_manager.run_command(cmd)
        
        self.status_label.configure(text=f"Reboot command sent.", text_color="#2CC985")
