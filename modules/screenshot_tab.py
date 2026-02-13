import customtkinter as ctk
from modules.ui_theme import CARD_BG, CARD_BORDER, TEXT_MUTED, SUCCESS, DANGER
import threading
import os
from datetime import datetime

try:
    from PIL import Image, ImageTk
except ImportError:
    Image = None
    ImageTk = None


class ScreenshotTab(ctk.CTkScrollableFrame):
    def __init__(self, master, adb_manager):
        super().__init__(master, fg_color="transparent")
        self.adb_manager = adb_manager
        self.current_screenshot_path = None
        self.screenshot_image = None
        
        self.columnconfigure(0, weight=1)

        # Header
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(fill="x", padx=20, pady=(10, 4))

        self.header_title = ctk.CTkLabel(self.header_frame, text="Screenshot", font=("Roboto Medium", 20))
        self.header_title.pack(anchor="w")

        self.header_sub = ctk.CTkLabel(self.header_frame, text="Capture device screen and preview on PC", font=("Roboto", 12), text_color=TEXT_MUTED)
        self.header_sub.pack(anchor="w", pady=(2, 0))

        # Controls Frame
        self.controls_frame = ctk.CTkFrame(self, corner_radius=14, fg_color=CARD_BG, border_width=1, border_color=CARD_BORDER)
        self.controls_frame.pack(fill="x", padx=20, pady=(6, 10))
        
        self.controls_inner = ctk.CTkFrame(self.controls_frame, fg_color="transparent")
        self.controls_inner.pack(fill="x", padx=12, pady=10)
        
        # Capture button
        self.btn_capture = ctk.CTkButton(
            self.controls_inner, 
            text="📸 Capture Screenshot", 
            command=self.capture_screenshot,
            font=("Roboto Medium", 14),
            height=40,
            fg_color="#3B8ED0"
        )
        self.btn_capture.pack(side="left", padx=5, expand=True, fill="x")
        
        # Status label
        self.status_label = ctk.CTkLabel(
            self.controls_inner, 
            text="Ready", 
            text_color=TEXT_MUTED,
            font=("Roboto", 11),
            width=200
        )
        self.status_label.pack(side="left", padx=10)

        # Preview Frame
        self.preview_frame = ctk.CTkFrame(self, corner_radius=14, fg_color=CARD_BG, border_width=1, border_color=CARD_BORDER)
        self.preview_frame.pack(fill="both", expand=True, padx=20, pady=(0, 10))
        
        # Preview header
        self.preview_header = ctk.CTkLabel(self.preview_frame, text="Screenshot Preview", font=("Roboto Medium", 14), text_color=TEXT_MUTED)
        self.preview_header.pack(anchor="w", padx=12, pady=(10, 8))
        
        # Image label
        self.image_label = ctk.CTkLabel(self.preview_frame, text="No screenshot captured yet", fg_color="transparent", text_color=TEXT_MUTED)
        self.image_label.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        
        # Action buttons frame
        self.action_frame = ctk.CTkFrame(self, corner_radius=14, fg_color=CARD_BG, border_width=1, border_color=CARD_BORDER)
        self.action_frame.pack(fill="x", padx=20, pady=(0, 10))
        
        self.action_inner = ctk.CTkFrame(self.action_frame, fg_color="transparent")
        self.action_inner.pack(fill="x", padx=12, pady=10)
        
        # Open file button
        self.btn_open = ctk.CTkButton(
            self.action_inner, 
            text="📂 Open File", 
            command=self.open_file,
            state="disabled"
        )
        self.btn_open.pack(side="left", padx=5, expand=True, fill="x")
        
        # Save as button
        self.btn_save_as = ctk.CTkButton(
            self.action_inner, 
            text="💾 Save As", 
            command=self.save_as,
            state="disabled"
        )
        self.btn_save_as.pack(side="left", padx=5, expand=True, fill="x")
        
        # Info frame
        self.info_frame = ctk.CTkFrame(self, corner_radius=14, fg_color=CARD_BG, border_width=1, border_color=CARD_BORDER)
        self.info_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        self.info_label = ctk.CTkLabel(
            self.info_frame, 
            text="Info: Screenshots are saved to Documents/MiTools by default\nClick 'Capture Screenshot' to get started",
            font=("Roboto", 11),
            text_color=TEXT_MUTED,
            justify="left"
        )
        self.info_label.pack(anchor="w", padx=12, pady=10)

    def capture_screenshot(self):
        if not self.adb_manager.connected_device:
            self.status_label.configure(text="❌ No device connected", text_color=DANGER)
            return
        
        self.status_label.configure(text="⏳ Capturing...", text_color=TEXT_MUTED)
        self.btn_capture.configure(state="disabled")
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        save_dir = os.path.expanduser("~/Documents/MiTools")
        os.makedirs(save_dir, exist_ok=True)
        save_path = os.path.join(save_dir, f"screenshot_{timestamp}.png")
        
        def on_screenshot_complete(success, message, path):
            self.btn_capture.configure(state="normal")
            
            if success:
                self.current_screenshot_path = path
                self.status_label.configure(text=f"✅ {message}", text_color=SUCCESS)
                self.display_screenshot(path)
                self.update_action_buttons(True)
                self.info_label.configure(text=f"Info: Screenshot saved to\n{path}")
            else:
                self.status_label.configure(text=f"❌ {message}", text_color=DANGER)
                self.current_screenshot_path = None
                self.update_action_buttons(False)
        
        self.adb_manager.take_screenshot(save_path, on_screenshot_complete)

    def display_screenshot(self, image_path):
        """Display screenshot preview in the UI."""
        try:
            if Image is None:
                self.image_label.configure(text="PIL not installed. Install Pillow to see preview.")
                return
            
            # Load and resize image for preview
            img = Image.open(image_path)
            
            # Get preview frame dimensions
            max_width = 800
            max_height = 600
            
            img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
            
            # Convert to PhotoImage
            photo = ImageTk.PhotoImage(img)
            
            self.screenshot_image = photo  # Keep reference
            self.image_label.configure(image=photo, text="")
        except Exception as e:
            self.image_label.configure(text=f"Error loading preview: {str(e)}")

    def update_action_buttons(self, enabled):
        """Enable/disable action buttons based on screenshot availability."""
        state = "normal" if enabled else "disabled"
        self.btn_open.configure(state=state)
        self.btn_save_as.configure(state=state)

    def open_file(self):
        """Open the screenshot file with default application."""
        if not self.current_screenshot_path:
            return
        
        try:
            import subprocess
            import sys
            
            if sys.platform == "win32":
                os.startfile(self.current_screenshot_path)
            elif sys.platform == "darwin":
                subprocess.run(["open", self.current_screenshot_path])
            else:
                subprocess.run(["xdg-open", self.current_screenshot_path])
            
            self.status_label.configure(text="📂 Opening file...", text_color=TEXT_MUTED)
        except Exception as e:
            self.status_label.configure(text=f"❌ Error opening file: {str(e)}", text_color=DANGER)

    def save_as(self):
        """Save screenshot to a custom location."""
        if not self.current_screenshot_path:
            return
        
        try:
            import tkinter.filedialog as filedialog
            import shutil
            
            file_path = filedialog.asksaveasfilename(
                defaultextension=".png",
                filetypes=[("PNG files", "*.png"), ("All files", "*.*")],
                initialfile=os.path.basename(self.current_screenshot_path)
            )
            
            if file_path:
                shutil.copy(self.current_screenshot_path, file_path)
                self.status_label.configure(text=f"✅ Saved to {os.path.basename(file_path)}", text_color=SUCCESS)
        except Exception as e:
            self.status_label.configure(text=f"❌ Error saving: {str(e)}", text_color=DANGER)

    def on_device_connected(self):
        """Called when device connects."""
        self.status_label.configure(text="✅ Device connected", text_color=SUCCESS)

    def on_device_disconnected(self):
        """Called when device disconnects."""
        self.status_label.configure(text="❌ Device disconnected", text_color=DANGER)
        self.btn_capture.configure(state="disabled")
