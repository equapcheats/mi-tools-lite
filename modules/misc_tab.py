
import customtkinter as ctk

class MiscTab(ctk.CTkFrame):
    def __init__(self, master, adb_manager):
        super().__init__(master)
        self.adb_manager = adb_manager

        self.grid_columnconfigure(0, weight=1)
        
        self.header = ctk.CTkLabel(self, text="Miscellaneous Tools", font=("Roboto Medium", 18))
        self.header.pack(pady=20)
        
        # Animation scales
        self.anim_frame = ctk.CTkFrame(self)
        self.anim_frame.pack(fill="x", padx=20, pady=10)
        
        self.lbl_anim = ctk.CTkLabel(self.anim_frame, text="System Animation Speed", font=("Roboto", 14, "bold"))
        self.lbl_anim.pack(anchor="w", padx=10, pady=(10, 5))
        
        self.lbl_desc = ctk.CTkLabel(self.anim_frame, text="Adjust animation scale (0.1x to 10.0x). Lower is faster.", text_color="gray")
        self.lbl_desc.pack(anchor="w", padx=10, pady=(0, 5))

        # Slider Section
        self.slider_frame = ctk.CTkFrame(self.anim_frame, fg_color="transparent")
        self.slider_frame.pack(fill="x", padx=10, pady=10)

        self.slider_val = ctk.DoubleVar(value=1.0)
        
        self.lbl_val = ctk.CTkLabel(self.slider_frame, text="1.0x", width=40)
        self.lbl_val.pack(side="right", padx=5)

        self.slider = ctk.CTkSlider(self.slider_frame, from_=0.1, to=10.0, number_of_steps=99, variable=self.slider_val, command=self.update_slider_label)
        self.slider.pack(side="left", fill="x", expand=True, padx=5)
        
        # Buttons
        self.btn_apply = ctk.CTkButton(self.anim_frame, text="Apply Speed Tweak", command=self.apply_speed_tweak)
        self.btn_apply.pack(padx=10, pady=10, anchor="w", side="left")

        self.btn_reset = ctk.CTkButton(self.anim_frame, text="Reset (1.0x)", command=self.reset_speed_tweak, fg_color="gray")
        self.btn_reset.pack(padx=10, pady=10, anchor="w", side="left")

        self.status_label = ctk.CTkLabel(self, text="", text_color="green")
        self.status_label.pack(pady=10)

    def update_slider_label(self, value):
        self.lbl_val.configure(text=f"{value:.1f}x")

    def apply_speed_tweak(self):
        if not self.adb_manager.connected_device:
            self.status_label.configure(text="No device connected.", text_color="red")
            return
            
        val = f"{self.slider_val.get():.2f}"
        
        cmds = [
            ["shell", "settings", "put", "global", "animator_duration_scale", val],
            ["shell", "settings", "put", "global", "transition_animation_scale", val],
            ["shell", "settings", "put", "global", "window_animation_scale", val]
        ]
        
        for cmd in cmds:
            self.adb_manager.run_command(["-s", self.adb_manager.connected_device] + cmd)
            
        self.status_label.configure(text=f"Animation speed set to {val}x", text_color="#2CC985")

    def reset_speed_tweak(self):
        self.slider_val.set(1.0)
        self.update_slider_label(1.0)
        self.apply_speed_tweak()
