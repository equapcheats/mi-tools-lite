
import subprocess
import threading
import time

class ADBManager:
    def __init__(self, update_callback=None):
        self.update_callback = update_callback
        self.connected_device = None


    def run_command(self, args):
        """Runs an ADB command and returns output, error."""
        try:

            cmd = ["adb"] + args
            process = subprocess.run(cmd, capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW if subprocess.os.name == 'nt' else 0)
            return process.stdout.strip(), process.stderr.strip()
        except FileNotFoundError:
            return None, "ADB executable not found. Please ensure Android Platform Tools are installed and in PATH."
        except Exception as e:
            return None, str(e)

    def scan_devices(self, callback):
        def _scan():
            output, error = self.run_command(["devices"])
            devices = []
            if output:
                lines = output.split('\n')[1:] # Skip header
                for line in lines:
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 2 and parts[1] == 'device':
                            devices.append(parts[0])
            if callback:
                callback(devices, error)

        threading.Thread(target=_scan, daemon=True).start()

    def connect_device(self, device_serial, callback):
        self.connected_device = device_serial
        # Connection logic is minimal for USB, mainly just verifying it's reachable.
        # But let's simulate a connection check or handshake.
        def _connect():
            # Basic ping: check if serial is still in `adb devices`
            out, err = self.run_command(["devices"])
            success = False
            msg = "Connection failed."
            if out and device_serial in out:
                success = True
                msg = f"Connected to {device_serial}"
            else:
                self.connected_device = None
            
            if callback:
                callback(success, msg)
                
        threading.Thread(target=_connect, daemon=True).start()


    def get_info(self):
        """Fetches consolidated device info."""
        if not self.connected_device: return None
        
        info = {}

        # Battery
        try:
            out, _ = self.run_command(["-s", self.connected_device, "shell", "dumpsys", "battery"])
            if out:
                for line in out.splitlines():
                    if "level:" in line:
                        info['battery_level'] = line.split(":", 1)[1].strip() + "%"
                    elif "voltage:" in line:
                        try:
                            v = int(line.split(":", 1)[1].strip())
                            info['battery_voltage'] = f"{v} mV ({v/1000:.3f} V)"
                        except ValueError:
                            pass
                    elif "temperature:" in line:
                        try:
                            t = int(line.split(":", 1)[1].strip())
                            info['battery_temp'] = f"{t} ({t/10:.1f} °C)"
                        except ValueError:
                            pass
        except Exception:
            pass

        # CPU Cores
        try:
            out, _ = self.run_command(["-s", self.connected_device, "shell", "cat", "/proc/cpuinfo"])
            if out:
                lines = out.splitlines()
                count = sum(1 for line in lines if line.strip().startswith("processor"))
                info['cpu_cores'] = count
        except Exception:
            pass

        # Memory
        try:
            out, _ = self.run_command(["-s", self.connected_device, "shell", "cat", "/proc/meminfo"])
            if out:
                for line in out.splitlines():
                    parts = line.split()
                    if not parts: continue
                    key = parts[0].strip(':')
                    if key in ['MemTotal', 'MemFree', 'MemAvailable']:
                        try:
                            kb = int(parts[1])
                            info[key] = f"{kb/1024:.0f} MB"
                        except ValueError:
                            pass
        except Exception:
            pass
        
        # Region
        try:
            out, _ = self.run_command(["-s", self.connected_device, "shell", "getprop", "ro.product.mod_device"])
            if out:
                info['miui_mod_device'] = out.strip()
                info['region'] = "Global" if "global" in out.lower() else "China/Other"
        except Exception:
            pass

        return info



    def _get_variants(self, pkg):
        """Returns a list of package variants to try (e.g. com.miui.X and com.xiaomi.X)."""
        variants = [pkg]
        if pkg.startswith("com.miui."):
            variants.append(pkg.replace("com.miui.", "com.xiaomi."))
        elif pkg.startswith("com.xiaomi."):
            variants.append(pkg.replace("com.xiaomi.", "com.miui."))
        return variants

    def uninstall_package(self, package_name, callback):
        if not self.connected_device:
            if callback: callback(False, "No device connected.")
            return

        def _uninstall():
            variants = self._get_variants(package_name)
            messages = []
            any_success = False

            for pkg in variants:
                out, err = self.run_command(["-s", self.connected_device, "shell", "pm", "uninstall", "--user", "0", pkg])
                if out and "Success" in out:
                    messages.append(f"{pkg}: Success")
                    any_success = True
                # We iterate silently for failures/not installed on variants
            
            if any_success:
                 callback(True, " | ".join(messages))
            else:
                 callback(False, f"Failed to uninstall {package_name} (and variants)")

        threading.Thread(target=_uninstall, daemon=True).start()



    def install_existing_package(self, package_name, callback):
        # Redirect to robust method which handles variants and install-existing + enable
        self.restore_package_robust(package_name, callback)

        

    def get_packages(self, mode):
        if not self.connected_device: return []
        
        cmd = ["-s", self.connected_device, "shell", "pm", "list", "packages"]
        
        if mode == "system":
            cmd.append("-s")
        elif mode == "user":
            cmd.append("-3")
        elif mode == "disabled":
            cmd.extend(["-d", "--user", "0"])
        elif mode == "uninstalled":
            # This is tricky. -u shows ALL (installed + uninstalled).
            # We want ONLY uninstalled.
            # Strategy: Get all system (-u -s) and subtract currently installed system (-s).
            # Or just return raw list if requested.
            # User request: "System-Apps, die per --user 0 entfernt wurden"
            pass 

        out, _ = self.run_command(cmd)
        if not out: return []
        
        packages = []
        for line in out.splitlines():
            if line.startswith("package:"):
                packages.append(line.split(":")[1].strip())
        
        if mode == "uninstalled":
            # Logic: Get ALL system apps (incl uninstalled)
            cmd_all = ["-s", self.connected_device, "shell", "pm", "list", "packages", "-u", "-s", "--user", "0"]
            out_all, _ = self.run_command(cmd_all)
            all_pkgs = set()
            if out_all:
                for line in out_all.splitlines():
                    if line.startswith("package:"):
                        all_pkgs.add(line.split(":")[1].strip())
            
            # Get currently installed system apps
            cmd_inst = ["-s", self.connected_device, "shell", "pm", "list", "packages", "-s", "--user", "0"]
            out_inst, _ = self.run_command(cmd_inst)
            inst_pkgs = set()
            if out_inst:
                for line in out_inst.splitlines():
                    if line.startswith("package:"):
                        inst_pkgs.add(line.split(":")[1].strip())
            
            # Difference
            packages = list(all_pkgs - inst_pkgs)

        return sorted(packages)



    def restore_package_robust(self, package_name, callback):
        if not self.connected_device:
            if callback: callback(False, "No device connected.")
            return

        def _run():
            variants = self._get_variants(package_name)
            messages = []
            any_success = False

            for pkg in variants:
                # 1. Install Existing
                out1, _ = self.run_command(["-s", self.connected_device, "shell", "pm", "install-existing", "--user", "0", pkg])
                # 2. Enable
                out2, _ = self.run_command(["-s", self.connected_device, "shell", "pm", "enable", pkg])
                
                if (out1 and "installed" in out1.lower()) or (out2 and ("new state" in out2.lower() or "enabled" in out2.lower())):
                     messages.append(f"{pkg}: Restored")
                     any_success = True
            
            if any_success:
                 callback(True, " | ".join(messages))
            else:
                 callback(True, f"Restore command attempts finished for {package_name}")

        threading.Thread(target=_run, daemon=True).start()

    def text_action(self, cmd_args, package_name, callback, success_kw=""):

        if not self.connected_device:
            if callback: callback(False, "No device connected.")
            return

        def _run():
            variants = self._get_variants(package_name)
            messages = []
            any_success = False

            for pkg in variants:
                out, err = self.run_command(["-s", self.connected_device, "shell"] + cmd_args + [pkg])
                if out and (success_kw.lower() in out.lower() or not out.strip()): # Sometimes silence is success
                    messages.append(f"{pkg}: Success")
                    any_success = True
                elif not out and not err:
                     messages.append(f"{pkg}: Success")
                     any_success = True

            if any_success:
                 callback(True, " | ".join(messages))
            else:
                 callback(False, f"Action failed for {package_name} (and variants)")
        
        threading.Thread(target=_run, daemon=True).start()


    def enable_package(self, pkg, callback):
        # pm enable com.example
        self.text_action(["pm", "enable"], pkg, callback, success_kw="state")

    def disable_package(self, pkg, callback):
        # pm disable-user --user 0 com.example
        self.text_action(["pm", "disable-user", "--user", "0"], pkg, callback, success_kw="state")

    def uninstall_full(self, pkg, callback):
        # pm uninstall com.example
        self.text_action(["pm", "uninstall"], pkg, callback, success_kw="Success")


    # --- File Manager Methods ---

    def list_files(self, path):
        """Lists files in a directory. Returns list of dicts: {name, type, size, date}."""
        if not self.connected_device: return []
        
        # Use ls -pl to get details and type indicator
        # -p appends / to directories
        # -l gives long format (permissions, owner, group, size, date, name)
        # We try to parse this.
        cmd = ["-s", self.connected_device, "shell", "ls", "-pl", path]
        out, err = self.run_command(cmd)

        entries = []
        if out:
            lines = out.splitlines()
            for line in lines:
                parts = line.split()
                if len(parts) < 7: continue # Skip total or malformed lines
                
                # permissions links owner group size date time name...
                # drwxrwx--x 3 root sdcard_rw 4096 2023-01-01 12:00 Folder/
                
                # Check if it looks like a file line
                if parts[0][0] not in '-dcb': continue
                
                # Size is usually at index 4 (0-based)
                try:
                    size = parts[4]
                except IndexError:
                    size = "0"
                
                # Date/Time is usually 5, 6
                try:
                    date_str = f"{parts[5]} {parts[6]}"
                except IndexError:
                    date_str = ""

                # Name starts at 7
                name_start_index = 7
                if len(parts) > name_start_index:
                    name = " ".join(parts[name_start_index:])
                else:
                    continue # No name?

                is_dir = name.endswith('/')
                if is_dir:
                    name = name[:-1]
                    file_type = 'dir'
                else:
                    file_type = 'file'
                
                # Format size
                try:
                    size_bytes = int(size)
                    if size_bytes > 1024*1024*1024:
                        size_str = f"{size_bytes/(1024*1024*1024):.2f} GB"
                    elif size_bytes > 1024*1024:
                        size_str = f"{size_bytes/(1024*1024):.2f} MB"
                    elif size_bytes > 1024:
                        size_str = f"{size_bytes/1024:.2f} KB"
                    else:
                        size_str = f"{size_bytes} B"
                except ValueError:
                    size_str = size

                entries.append({
                    'name': name,
                    'type': file_type,
                    'size': size_str,
                    'date': date_str,
                    'permissions': parts[0],
                    'raw_line': line
                })
        
        # Fallback if list is empty (parsing failed or empty dir)
        # If parsing failed but dir not empty, we might want 'ls -1p' as fallback?
        # For now, if empty, we assume empty or error.
        
        # Sort: Dirs first, then alphabetical
        return sorted(entries, key=lambda x: (x['type'] != 'dir', x['name'].lower()))

    def search_files(self, path, query, callback):
        """Searches for files matching query in path."""
        def _search():
            cmd = ["-s", self.connected_device, "shell", "find", path, "-name", f"*{query}*"]
            out, err = self.run_command(cmd)
            results = []
            if out:
                for line in out.splitlines():
                    clean_line = line.strip()
                    if clean_line:
                        results.append({'name': clean_line, 'type': 'file'}) # Assume file for consistency
            
            callback(results)
        
        threading.Thread(target=_search, daemon=True).start()

    def pull_file(self, remote_path, local_path, callback):
        def _run():
            cmd = ["-s", self.connected_device, "pull", remote_path, local_path]
            # remove NO_WINDOW flag for pull to potentially show progress? No, subprocess captures it.
            # ADB prints progress to stderr usually. 
            process = subprocess.run(["adb"] + cmd, capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW if subprocess.os.name == 'nt' else 0)
            
            if process.returncode == 0:
                callback(True, f"Pulled {remote_path} to {local_path}")
            else:
                callback(False, f"Failed: {process.stderr}")

        threading.Thread(target=_run, daemon=True).start()

    def push_file(self, local_path, remote_path, callback):
        def _run():
            cmd = ["-s", self.connected_device, "push", local_path, remote_path]
            process = subprocess.run(["adb"] + cmd, capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW if subprocess.os.name == 'nt' else 0)
            
            if process.returncode == 0:
                callback(True, f"Pushed {local_path} to {remote_path}")
            else:
                callback(False, f"Failed: {process.stderr}")

        threading.Thread(target=_run, daemon=True).start()

    def delete_file(self, path, callback):
        def _run():
            cmd = ["-s", self.connected_device, "shell", "rm", "-rf", path]
            out, err = self.run_command(cmd)
            if not err:
                callback(True, f"Deleted {path}")
            else:
                callback(False, f"Delete failed: {err}")
        threading.Thread(target=_run, daemon=True).start()

    def rename_file(self, old_path, new_path, callback):
        def _run():
            cmd = ["-s", self.connected_device, "shell", "mv", old_path, new_path]
            out, err = self.run_command(cmd)
            if not err:
                 callback(True, f"Renamed to {new_path}")
            else:
                 callback(False, f"Rename failed: {err}")
        threading.Thread(target=_run, daemon=True).start()

    def create_directory(self, path, callback):
        def _run():
            cmd = ["-s", self.connected_device, "shell", "mkdir", "-p", path]
            out, err = self.run_command(cmd)
            if not err:
                callback(True, f"Created folder {path}")
            else:
                callback(False, f"Failed to create folder: {err}")
        threading.Thread(target=_run, daemon=True).start()
