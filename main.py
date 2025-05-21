import tkinter as tk
from tkinter import (
    ttk,
    messagebox,
    filedialog,
)
import time
import json
import os
import datetime
import threading
import psutil
from win32gui import GetForegroundWindow, GetWindowText

# --- NEW IMPORTS ---
import subprocess
import re
import win32process  # Added for getting process ID

# --- END NEW IMPORTS ---
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class ProductivityTracker:
    def __init__(self, root):
        self.root = root
        self.root.title("Personal Productivity Tracker")
        self.root.geometry("800x650")
        self.root.minsize(800, 650)

        self.data_file = "productivity_data.json"
        if not os.path.exists(self.data_file):
            with open(self.data_file, "w") as f:
                json.dump({"sessions": []}, f)

        self.load_data()

        self.tracking = False
        self.start_time = None
        self.current_app = ""
        self.app_times = {}
        self.tracking_thread = None
        self.public_monitor = None
        self.public_monitor_showing = False
        self.focus_mode = False
        self.remote_device_ip_var = tk.StringVar(value="")

        self.color_themes = {
            "Blue": {
                "bg": "#e6f2ff",
                "fg": "#003366",
                "accent": "#3399ff",
                "chart": "skyblue",
                "progress_bg": "#d0e8ff",
                "fg_on_accent": "#FFFFFF",
            },
            "Green": {
                "bg": "#e6ffe6",
                "fg": "#006600",
                "accent": "#33cc33",
                "chart": "lightgreen",
                "progress_bg": "#d0ffd0",
                "fg_on_accent": "#FFFFFF",
            },
            "Purple": {
                "bg": "#f2e6ff",
                "fg": "#330066",
                "accent": "#9933ff",
                "chart": "plum",
                "progress_bg": "#ead8ff",
                "fg_on_accent": "#FFFFFF",
            },
            "Dark": {
                "bg": "#333333",
                "fg": "#ffffff",
                "accent": "#0099cc",
                "chart": "steelblue",
                "progress_bg": "#555555",
                "fg_on_accent": "#FFFFFF",
            },
        }
        self.create_ui()

    def load_data(self):
        try:
            with open(self.data_file, "r") as f:
                self.data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.data = {"sessions": []}
            self.save_data()

    def save_data(self):
        with open(self.data_file, "w") as f:
            json.dump(self.data, f, indent=4)

    def create_ui(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill="both", padx=10, pady=10)

        self.tracking_frame = ttk.Frame(self.notebook)
        self.stats_frame = ttk.Frame(self.notebook)
        self.settings_frame = ttk.Frame(self.notebook)
        self.network_devices_frame = ttk.Frame(self.notebook)

        self.notebook.add(self.tracking_frame, text="Tracking")
        self.notebook.add(self.stats_frame, text="Statistics")
        self.notebook.add(self.network_devices_frame, text="Network Devices")
        self.notebook.add(self.settings_frame, text="Settings")

        self.setup_tracking_tab()
        self.setup_stats_tab()
        self.setup_settings_tab()
        self.setup_network_devices_tab()

    def setup_tracking_tab(self):
        status_frame = ttk.LabelFrame(self.tracking_frame, text="Tracking Status")
        status_frame.pack(fill="x", padx=10, pady=10)
        self.status_label = ttk.Label(
            status_frame, text="Not tracking", font=("Arial", 12)
        )
        self.status_label.pack(pady=10)
        self.time_label = ttk.Label(
            status_frame, text="Elapsed time: 00:00:00", font=("Arial", 12)
        )
        self.time_label.pack(pady=5)
        self.current_app_label = ttk.Label(
            status_frame, text="Current application: None", font=("Arial", 12)
        )
        self.current_app_label.pack(pady=5)
        button_frame = ttk.Frame(self.tracking_frame)
        button_frame.pack(fill="x", padx=10, pady=10)
        self.start_button = ttk.Button(
            button_frame, text="Start Tracking (Local)", command=self.start_tracking
        )
        self.start_button.pack(side="left", padx=5)
        self.stop_button = ttk.Button(
            button_frame,
            text="Stop Tracking",
            command=self.stop_tracking,
            state="disabled",
        )
        self.stop_button.pack(side="left", padx=5)
        self.public_monitor_btn = ttk.Button(
            button_frame, text="Show Public Monitor", command=self.toggle_public_monitor
        )
        self.public_monitor_btn.pack(side="left", padx=5)
        self.session_frame = ttk.LabelFrame(self.tracking_frame, text="Current Session")
        self.session_frame.pack(fill="both", expand=True, padx=10, pady=10)
        columns = ("Application", "Time Spent")
        self.session_tree = ttk.Treeview(
            self.session_frame, columns=columns, show="headings"
        )
        for col in columns:
            self.session_tree.heading(col, text=col)
            self.session_tree.column(col, width=100, anchor="w")
        self.session_tree.column("Time Spent", anchor="e")
        self.session_tree.pack(fill="both", expand=True, padx=5, pady=5)

    def setup_stats_tab(self):
        date_frame = ttk.Frame(self.stats_frame)
        date_frame.pack(fill="x", padx=10, pady=10)
        ttk.Label(date_frame, text="View Statistics:").pack(side="left", padx=5)
        self.stats_option = tk.StringVar(value="Today")
        options = ["Today", "Yesterday", "This Week", "This Month", "All Time"]
        stats_dropdown = ttk.Combobox(
            date_frame, textvariable=self.stats_option, values=options, state="readonly"
        )
        stats_dropdown.pack(side="left", padx=5)
        stats_dropdown.bind("<<ComboboxSelected>>", self.update_stats)
        ttk.Button(date_frame, text="Refresh", command=self.update_stats).pack(
            side="left", padx=5
        )
        self.stats_display_frame = ttk.Frame(self.stats_frame)
        self.stats_display_frame.pack(fill="both", expand=True, padx=10, pady=10)
        self.update_stats()

    def setup_settings_tab(self):
        settings_inner_frame = ttk.Frame(self.settings_frame)
        settings_inner_frame.pack(fill="both", expand=True, padx=20, pady=20)
        notification_frame = ttk.LabelFrame(settings_inner_frame, text="Notifications")
        notification_frame.pack(fill="x", padx=10, pady=10)
        self.notify_var = tk.BooleanVar(value=True)
        notify_check = ttk.Checkbutton(
            notification_frame,
            text="Show notifications about productivity",
            variable=self.notify_var,
        )
        notify_check.pack(anchor="w", padx=10, pady=5)
        idle_frame = ttk.LabelFrame(
            settings_inner_frame, text="Idle Detection (Not Implemented)"
        )
        idle_frame.pack(fill="x", padx=10, pady=10)
        ttk.Label(idle_frame, text="Consider inactive after (minutes):").pack(
            anchor="w", padx=10, pady=5
        )
        self.idle_time = tk.StringVar(value="5")
        idle_entry = ttk.Entry(
            idle_frame, textvariable=self.idle_time, width=5, state="disabled"
        )
        idle_entry.pack(anchor="w", padx=10, pady=5)
        remote_device_frame = ttk.LabelFrame(
            settings_inner_frame, text="Remote Device Monitoring (Conceptual)"
        )
        remote_device_frame.pack(fill="x", padx=10, pady=10)
        ttk.Label(
            remote_device_frame, text="Target Device IP Address (for future use):"
        ).pack(anchor="w", padx=10, pady=(5, 0))
        remote_ip_entry = ttk.Entry(
            remote_device_frame, textvariable=self.remote_device_ip_var, width=30
        )
        remote_ip_entry.pack(anchor="w", padx=10, pady=(0, 5))
        ttk.Label(
            remote_device_frame,
            text="Note: Current tracking (win32gui) is LOCAL-ONLY.\nTrue remote application tracking requires an agent on the remote device\nand network communication. This field is a placeholder.",
            justify="left",
            font=("Arial", 8),
        ).pack(anchor="w", padx=10, pady=(0, 5))
        monitor_frame = ttk.LabelFrame(
            settings_inner_frame, text="Public Monitor Settings"
        )
        monitor_frame.pack(fill="x", padx=10, pady=10)
        ttk.Label(monitor_frame, text="Opacity:").pack(anchor="w", padx=10, pady=5)
        self.opacity_var = tk.DoubleVar(value=0.8)
        opacity_scale = ttk.Scale(
            monitor_frame,
            from_=0.2,
            to=1.0,
            variable=self.opacity_var,
            orient="horizontal",
        )
        opacity_scale.pack(fill="x", padx=10, pady=5)
        opacity_scale.bind("<ButtonRelease-1>", self.update_monitor_opacity)
        ttk.Label(monitor_frame, text="Size:").pack(anchor="w", padx=10, pady=5)
        self.size_var = tk.StringVar(value="Medium")
        size_options = ["Small", "Medium", "Large"]
        size_dropdown = ttk.Combobox(
            monitor_frame,
            textvariable=self.size_var,
            values=size_options,
            state="readonly",
        )
        size_dropdown.pack(anchor="w", padx=10, pady=5)
        size_dropdown.bind("<<ComboboxSelected>>", self.update_monitor_size)
        self.always_on_top_var = tk.BooleanVar(value=True)
        always_on_top_check = ttk.Checkbutton(
            monitor_frame,
            text="Keep monitor window always on top",
            variable=self.always_on_top_var,
        )
        always_on_top_check.pack(anchor="w", padx=10, pady=5)
        always_on_top_check.bind("<ButtonRelease-1>", self.update_monitor_topmost)
        ttk.Label(monitor_frame, text="Color Theme:").pack(anchor="w", padx=10, pady=5)
        self.theme_var = tk.StringVar(value="Blue")
        theme_options = list(self.color_themes.keys())
        theme_dropdown = ttk.Combobox(
            monitor_frame,
            textvariable=self.theme_var,
            values=theme_options,
            state="readonly",
        )
        theme_dropdown.pack(anchor="w", padx=10, pady=5)
        theme_dropdown.bind("<<ComboboxSelected>>", self.update_monitor_theme)
        ttk.Label(monitor_frame, text="Daily Productivity Goal (hours):").pack(
            anchor="w", padx=10, pady=5
        )
        self.goal_var = tk.StringVar(value="8")
        goal_entry = ttk.Entry(monitor_frame, textvariable=self.goal_var, width=5)
        goal_entry.pack(anchor="w", padx=10, pady=5)
        goal_entry.bind(
            "<Return>",
            lambda e: (
                self.update_public_monitor() if self.public_monitor_showing else None
            ),
        )
        ttk.Label(
            monitor_frame, text="Focus Mode Apps (comma separated keywords):"
        ).pack(anchor="w", padx=10, pady=5)
        self.focus_apps_var = tk.StringVar(
            value="Word,Excel,PowerPoint,Visual Studio Code,PyCharm,Photoshop"
        )
        focus_entry = ttk.Entry(
            monitor_frame, textvariable=self.focus_apps_var, width=40
        )
        focus_entry.pack(anchor="w", padx=10, pady=5)
        data_frame = ttk.LabelFrame(settings_inner_frame, text="Data Management")
        data_frame.pack(fill="x", padx=10, pady=10)
        ttk.Button(data_frame, text="Export Data", command=self.export_data).pack(
            anchor="w", padx=10, pady=5
        )
        ttk.Button(data_frame, text="Clear All Data", command=self.clear_data).pack(
            anchor="w", padx=10, pady=5
        )
        about_frame = ttk.LabelFrame(settings_inner_frame, text="About")
        about_frame.pack(fill="x", padx=10, pady=10)
        ttk.Label(about_frame, text="Personal Productivity Tracker v1.1").pack(
            anchor="w", padx=10, pady=5
        )
        ttk.Label(
            about_frame, text="A tool to help you monitor your own computer usage"
        ).pack(anchor="w", padx=10, pady=5)

    def setup_network_devices_tab(self):
        main_net_frame = ttk.Frame(self.network_devices_frame)
        main_net_frame.pack(expand=True, fill="both", padx=10, pady=10)

        desc_label = ttk.Label(
            main_net_frame,
            text="This section displays devices found in your computer's ARP cache. "
            "These are typically devices your computer has recently communicated with on the local network. "
            "The list is based on the 'arp -a' command output.",
            wraplength=750,
            justify="left",
        )
        desc_label.pack(pady=(0, 10), fill="x")

        control_frame = ttk.Frame(main_net_frame)
        control_frame.pack(fill="x", pady=(0, 10))

        self.scan_button = ttk.Button(
            control_frame,
            text="Show ARP Cache (arp -a)",
            command=self.scan_network_devices,
        )
        self.scan_button.pack(side="left")

        self.network_status_label = ttk.Label(control_frame, text="")
        self.network_status_label.pack(side="left", padx=10)

        results_frame = ttk.LabelFrame(main_net_frame, text="ARP Cache Entries")
        results_frame.pack(fill="both", expand=True)

        columns = ("Interface", "IP Address", "MAC Address", "Type")
        self.arp_tree = ttk.Treeview(results_frame, columns=columns, show="headings")
        for col in columns:
            self.arp_tree.heading(col, text=col)
            if col == "IP Address" or col == "MAC Address":
                self.arp_tree.column(col, width=150, anchor="w", minwidth=120)
            elif col == "Interface":
                self.arp_tree.column(col, width=180, anchor="w", minwidth=150)
            else:  # Type
                self.arp_tree.column(col, width=100, anchor="w", minwidth=80)

        arp_scrollbar_y = ttk.Scrollbar(
            results_frame, orient="vertical", command=self.arp_tree.yview
        )
        self.arp_tree.configure(yscrollcommand=arp_scrollbar_y.set)
        arp_scrollbar_x = ttk.Scrollbar(
            results_frame, orient="horizontal", command=self.arp_tree.xview
        )
        self.arp_tree.configure(xscrollcommand=arp_scrollbar_x.set)

        arp_scrollbar_y.pack(side="right", fill="y")
        arp_scrollbar_x.pack(side="bottom", fill="x")
        self.arp_tree.pack(fill="both", expand=True, padx=5, pady=5)

    def scan_network_devices(self):
        self.network_status_label.config(text="Loading ARP cache...")
        self.scan_button.config(state="disabled")
        for item in self.arp_tree.get_children():
            self.arp_tree.delete(item)
        self.root.update_idletasks()

        try:
            process = subprocess.run(
                ["arp", "-a"],
                capture_output=True,
                text=True,
                check=False,
                encoding="utf-8",
                errors="replace",
            )

            if process.returncode != 0 and process.stderr:
                if not process.stdout.strip():
                    self.network_status_label.config(
                        text=f"Error running arp -a: {process.stderr.strip()}"
                    )
                    messagebox.showerror(
                        "ARP Error",
                        f"Failed to execute arp -a.\nError: {process.stderr.strip()}",
                    )
                    return

            arp_output = process.stdout
            if not arp_output.strip():
                self.network_status_label.config(text="No output from arp -a command.")
                return

            parsed_data = self._parse_arp_output(arp_output)

            if not parsed_data:
                self.network_status_label.config(
                    text="No devices found in ARP cache or parsing failed."
                )
            else:
                for entry in parsed_data:
                    self.arp_tree.insert(
                        "",
                        "end",
                        values=(
                            entry["interface"],
                            entry["ip"],
                            entry["mac"],
                            entry["type"],
                        ),
                    )
                self.network_status_label.config(
                    text=f"Scan complete. Found {len(parsed_data)} entries."
                )

        except FileNotFoundError:
            self.network_status_label.config(text="Error: 'arp' command not found.")
            messagebox.showerror(
                "Command Error",
                "'arp' command not found. Please ensure it is in your system's PATH.",
            )
        except Exception as e:
            self.network_status_label.config(
                text=f"An unexpected error occurred: {str(e)}"
            )
            messagebox.showerror(
                "Error", f"An unexpected error occurred during scan: {str(e)}"
            )
        finally:
            if hasattr(self, "scan_button") and self.scan_button.winfo_exists():
                self.scan_button.config(state="normal")

    def _parse_arp_output(self, arp_output_str):
        entries = []
        current_interface = "Unknown"
        interface_re = re.compile(r"Interface:\s*([\d\.]+)\s*---.*", re.IGNORECASE)
        lines = arp_output_str.splitlines()

        for line in lines:
            line = line.strip()
            if not line:
                continue
            match_interface = interface_re.match(line)
            if match_interface:
                current_interface = match_interface.group(1)
                continue
            if (
                "internet address" in line.lower()
                and "physical address" in line.lower()
            ):
                continue
            parts = re.split(r"\s{2,}", line)
            if len(parts) < 2:
                parts = re.split(r"\s+", line)

            if len(parts) >= 3:
                ip_address, mac_address, entry_type = parts[0], parts[1], parts[2]
                if re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", ip_address):
                    entries.append(
                        {
                            "interface": current_interface,
                            "ip": ip_address,
                            "mac": mac_address,
                            "type": entry_type,
                        }
                    )
            elif len(parts) == 2:
                ip_address, second_part = parts[0], parts[1]
                if re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", ip_address):
                    if (
                        re.match(
                            r"^([0-9A-Fa-f]{2}-){5}[0-9A-Fa-f]{2}$",
                            second_part,
                            re.IGNORECASE,
                        )
                        or second_part.lower() == "(incomplete)"
                    ):
                        entries.append(
                            {
                                "interface": current_interface,
                                "ip": ip_address,
                                "mac": second_part,
                                "type": "(missing)",
                            }
                        )
                    else:
                        entries.append(
                            {
                                "interface": current_interface,
                                "ip": ip_address,
                                "mac": "(missing)",
                                "type": second_part,
                            }
                        )
        return entries

    def start_tracking(self):
        remote_ip = self.remote_device_ip_var.get()
        if remote_ip:
            messagebox.showinfo(
                "Remote Tracking Note",
                f"Remote IP '{remote_ip}' is set, but current tracking is LOCAL only.\nActual remote tracking is not yet implemented.",
            )
        self.tracking = True
        self.start_time = time.time()
        self.app_times = {}
        self.status_label.config(text="Currently tracking (Local)")
        self.start_button.config(state="disabled")
        self.stop_button.config(state="normal")
        self.tracking_thread = threading.Thread(target=self.track_activity, daemon=True)
        self._last_app_name_for_timing_thread = ""
        self._last_update_ts_thread = time.time()
        self.tracking_thread.start()
        if self.public_monitor_showing:
            self.update_public_monitor()

    def track_activity(self):
        last_heavy_update_time = time.time()
        while self.tracking:
            current_ts = time.time()
            interval_duration = current_ts - self._last_update_ts_thread
            try:
                window = GetForegroundWindow()
                raw_title = GetWindowText(window)
                current_raw_app_name = ""

                # --- MODIFIED LOGIC FOR UNKNOWN/EMPTY WINDOW TITLES ---
                if (
                    not raw_title
                    or not raw_title.strip()
                    or raw_title.strip().lower() == "unknown"
                ):
                    current_raw_app_name = (
                        "Unknown"  # Initial placeholder before trying PID
                    )
                    try:
                        # win32process.GetWindowThreadProcessId returns (threadId, processId)
                        _, pid = win32process.GetWindowThreadProcessId(window)
                        if pid > 0:
                            process = psutil.Process(pid)
                            p_name = process.name()  # e.g., "chrome.exe"
                            if p_name:
                                current_raw_app_name = p_name  # Use process name
                            else:
                                current_raw_app_name = f"Unnamed Process (PID: {pid})"
                        else:
                            current_raw_app_name = "Unknown (System Window/No PID)"
                    except psutil.NoSuchProcess:
                        current_raw_app_name = "Unknown (Process Ended)"
                    except psutil.AccessDenied:
                        current_raw_app_name = "Unknown (Access Denied to Process Info)"
                    except Exception:  # Catch other win32 or psutil errors
                        current_raw_app_name = "Unknown (Error Getting Process Info)"
                else:
                    current_raw_app_name = (
                        raw_title  # Use the window title if it's valid
                    )

                if (
                    not current_raw_app_name or not current_raw_app_name.strip()
                ):  # Final fallback
                    current_raw_app_name = "Unknown Application (Final Fallback)"
                # --- END MODIFIED LOGIC ---

                app_name_for_display = (
                    current_raw_app_name[:47] + "..."
                    if len(current_raw_app_name) > 50
                    else current_raw_app_name
                )

                if self.current_app != app_name_for_display:
                    self.current_app = app_name_for_display
                    if self.root.winfo_exists():
                        self.root.after(
                            0,
                            lambda app=self.current_app: self.current_app_label.config(
                                text=f"Current application: {app}"
                            ),
                        )
                    if (
                        self.public_monitor_showing
                        and self.public_monitor
                        and self.public_monitor.winfo_exists()
                        and hasattr(self, "public_app_label")
                    ):
                        self.root.after(
                            0,
                            lambda app=self.current_app: self.public_app_label.config(
                                text=f"Current: {app[:30]}"
                            ),
                        )

                # Use current_raw_app_name for time aggregation
                if self._last_app_name_for_timing_thread:
                    self.app_times[self._last_app_name_for_timing_thread] = (
                        self.app_times.get(self._last_app_name_for_timing_thread, 0)
                        + interval_duration
                    )
                self._last_app_name_for_timing_thread = current_raw_app_name
                self._last_update_ts_thread = current_ts

                elapsed_total_seconds = current_ts - self.start_time
                hours, remainder = divmod(int(elapsed_total_seconds), 3600)
                minutes, seconds = divmod(remainder, 60)
                time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

                if self.root.winfo_exists():
                    self.root.after(
                        0,
                        lambda s=time_str: self.time_label.config(
                            text=f"Elapsed time: {s}"
                        ),
                    )
                if (
                    self.public_monitor_showing
                    and self.public_monitor
                    and self.public_monitor.winfo_exists()
                    and hasattr(self, "public_time_label")
                ):
                    self.root.after(
                        0,
                        lambda s=time_str: self.public_time_label.config(
                            text=f"Time: {s}"
                        ),
                    )

                if (
                    current_ts - last_heavy_update_time > 5.0
                ):  # Update tree and monitor less frequently
                    if self.root.winfo_exists():
                        self.root.after(0, self.update_session_tree)
                    if self.public_monitor_showing:
                        self.root.after(0, self.update_public_monitor)
                    last_heavy_update_time = current_ts

                time.sleep(1)  # Check every second
            except Exception as e:
                print(f"Error in tracking thread: {e}")
                if self.root.winfo_exists():  # Check if root window still exists
                    self.root.after(
                        0,
                        lambda: (
                            self.current_app_label.config(
                                text="Current application: Error reading window"
                            )
                            if self.current_app_label.winfo_exists()
                            else None
                        ),
                    )
                time.sleep(1)

    def update_session_tree(self):
        if not hasattr(self, "session_tree") or not self.session_tree.winfo_exists():
            return
        for item in self.session_tree.get_children():
            self.session_tree.delete(item)

        current_app_times_copy = self.app_times.copy()

        # Aggregate by display name for session tree (raw names are stored)
        display_app_times = {}
        for raw_name, seconds in current_app_times_copy.items():
            # Truncate raw_name for display if it's too long
            display_name = raw_name[:47] + "..." if len(raw_name) > 50 else raw_name
            display_app_times[display_name] = (
                display_app_times.get(display_name, 0) + seconds
            )

        sorted_apps = sorted(
            display_app_times.items(), key=lambda x: x[1], reverse=True
        )
        for app, seconds in sorted_apps:
            hours, remainder = divmod(int(seconds), 3600)
            minutes, sec = divmod(remainder, 60)
            time_str = f"{hours:02d}:{minutes:02d}:{sec:02d}"
            if self.session_tree.winfo_exists():
                self.session_tree.insert("", "end", values=(app, time_str))

    def stop_tracking(self):
        if not self.tracking:
            return

        # Ensure the last tracked application's time is recorded
        if (
            hasattr(self, "_last_app_name_for_timing_thread")
            and self._last_app_name_for_timing_thread
            and hasattr(self, "_last_update_ts_thread")
        ):
            final_interval_duration = time.time() - self._last_update_ts_thread
            self.app_times[self._last_app_name_for_timing_thread] = (
                self.app_times.get(self._last_app_name_for_timing_thread, 0)
                + final_interval_duration
            )

        self.tracking = False
        if self.tracking_thread and self.tracking_thread.is_alive():
            try:
                self.tracking_thread.join(timeout=1.5)
            except RuntimeError:
                pass  # Thread might already be finished
        self.tracking_thread = None

        end_time = time.time()
        duration = end_time - self.start_time if self.start_time else 0
        session_date = (
            datetime.datetime.fromtimestamp(self.start_time).strftime("%Y-%m-%d")
            if self.start_time
            else datetime.datetime.now().strftime("%Y-%m-%d")
        )
        session_start_time_str = (
            datetime.datetime.fromtimestamp(self.start_time).strftime("%H:%M:%S")
            if self.start_time
            else "N/A"
        )

        session = {
            "date": session_date,
            "start_time": session_start_time_str,
            "end_time": datetime.datetime.fromtimestamp(end_time).strftime("%H:%M:%S"),
            "duration": duration,
            "applications": self.app_times.copy(),  # Store raw names and times
        }
        self.data["sessions"].append(session)
        self.save_data()

        self.status_label.config(text="Not tracking")
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")
        self.current_app_label.config(text="Current application: None")
        self.time_label.config(text="Elapsed time: 00:00:00")

        messagebox.showinfo(
            "Tracking Stopped",
            f"Tracked for {int(duration // 3600)}h {int((duration % 3600) // 60)}m {int(duration % 60)}s",
        )
        self.update_stats()
        if self.public_monitor_showing:
            self.update_public_monitor()

    def update_stats(self, event=None):
        if (
            not hasattr(self, "stats_display_frame")
            or not self.stats_display_frame.winfo_exists()
        ):
            return
        for widget in self.stats_display_frame.winfo_children():
            if isinstance(
                widget, FigureCanvasTkAgg
            ):  # Ensure Matplotlib figures are closed
                plt.close(widget.figure)
            widget.destroy()

        option = self.stats_option.get()
        now = datetime.datetime.now()
        today_str = now.strftime("%Y-%m-%d")
        yesterday_str = (now - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        week_start_dt = now - datetime.timedelta(days=now.weekday())
        week_start_str = week_start_dt.strftime("%Y-%m-%d")
        month_start_str = now.strftime("%Y-%m-01")

        filtered_sessions = []
        if option == "Today":
            filtered_sessions = [
                s for s in self.data["sessions"] if s.get("date") == today_str
            ]
        elif option == "Yesterday":
            filtered_sessions = [
                s for s in self.data["sessions"] if s.get("date") == yesterday_str
            ]
        elif option == "This Week":
            filtered_sessions = [
                s
                for s in self.data["sessions"]
                if s.get("date") and s.get("date") >= week_start_str
            ]
        elif option == "This Month":
            filtered_sessions = [
                s
                for s in self.data["sessions"]
                if s.get("date") and s.get("date") >= month_start_str
            ]
        else:  # All Time
            filtered_sessions = self.data["sessions"]

        if not filtered_sessions:
            ttk.Label(
                self.stats_display_frame, text=f"No data available for {option}."
            ).pack(pady=20)
            return

        combined_apps_raw = {}  # Store raw names from sessions
        total_duration_seconds = 0
        for session in filtered_sessions:
            total_duration_seconds += session.get("duration", 0)
            for app_raw_name, time_spent in session.get("applications", {}).items():
                combined_apps_raw[app_raw_name] = (
                    combined_apps_raw.get(app_raw_name, 0) + time_spent
                )

        hours, rem = divmod(int(total_duration_seconds), 3600)
        mins, secs = divmod(rem, 60)
        total_time_str = f"{hours:02d}:{mins:02d}:{secs:02d}"

        ttk.Label(
            self.stats_display_frame,
            text=f"Total time tracked: {total_time_str}",
            font=("Arial", 12, "bold"),
        ).pack(pady=10)

        stats_content = ttk.Frame(self.stats_display_frame)
        stats_content.pack(fill="both", expand=True)

        table_frame = ttk.Frame(stats_content)
        table_frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        columns = ("Application", "Time Spent", "Percentage")
        app_tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        for col in columns:
            app_tree.heading(col, text=col)
            app_tree.column(col, width=120, anchor="w")
        app_tree.column(
            "Application", width=200, minwidth=150
        )  # Wider for longer names
        app_tree.column("Time Spent", anchor="e", width=100)
        app_tree.column("Percentage", anchor="e", width=80)

        scrollbar = ttk.Scrollbar(
            table_frame, orient="vertical", command=app_tree.yview
        )
        app_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        app_tree.pack(side="left", fill="both", expand=True)

        # For display in stats, use truncated names if necessary
        combined_apps_display = {}
        for raw_name, seconds_spent in combined_apps_raw.items():
            display_name = (
                raw_name[:60] + "..." if len(raw_name) > 63 else raw_name
            )  # Slightly longer truncation for stats
            combined_apps_display[display_name] = (
                combined_apps_display.get(display_name, 0) + seconds_spent
            )

        sorted_combined_apps_display = sorted(
            combined_apps_display.items(), key=lambda x: x[1], reverse=True
        )

        for app_display_name, seconds_spent in sorted_combined_apps_display:
            h_app, rem_app = divmod(int(seconds_spent), 3600)
            m_app, s_app = divmod(rem_app, 60)
            app_time_str = f"{h_app:02d}:{m_app:02d}:{s_app:02d}"
            percentage = (
                (seconds_spent / total_duration_seconds) * 100
                if total_duration_seconds > 0
                else 0
            )
            app_tree.insert(
                "", "end", values=(app_display_name, app_time_str, f"{percentage:.1f}%")
            )

        chart_frame = ttk.Frame(stats_content)
        chart_frame.pack(side="right", fill="both", expand=True, padx=5, pady=5)

        fig, ax = plt.subplots(figsize=(5, 4))
        plt.subplots_adjust(
            left=0.1, right=0.9, top=0.9, bottom=0.2
        )  # Adjust as needed

        top_n_apps = 5
        # Use sorted_combined_apps_display for chart data
        chart_data_source = sorted_combined_apps_display[:top_n_apps]
        other_apps_time = sum(
            time_val for _, time_val in sorted_combined_apps_display[top_n_apps:]
        )
        if other_apps_time > 0:
            chart_data_source.append(("Other", other_apps_time))

        labels = [app_name for app_name, _ in chart_data_source]
        sizes = [time_val for _, time_val in chart_data_source]

        if not labels:  # No data to plot
            plt.close(fig)  # Close the figure if no data
            ttk.Label(chart_frame, text="Not enough data for chart.").pack()
            return

        ax.pie(sizes, labels=labels, autopct="%1.1f%%", startangle=90, pctdistance=0.85)
        ax.axis("equal")
        ax.set_title("Top Applications Usage")

        canvas = FigureCanvasTkAgg(fig, master=chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    def export_data(self):
        try:
            export_file_path = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                title="Export Productivity Data",
            )
            if not export_file_path:
                return
            with open(export_file_path, "w") as f:
                json.dump(self.data, f, indent=4)
            messagebox.showinfo(
                "Export Successful", f"Data exported to {export_file_path}"
            )
        except Exception as e:
            messagebox.showerror("Export Failed", f"Failed to export data: {e}")

    def clear_data(self):
        if messagebox.askyesno(
            "Clear Data",
            "Are you sure you want to delete all tracking data? This cannot be undone.",
        ):
            self.data = {"sessions": []}
            self.save_data()
            messagebox.showinfo("Data Cleared", "All tracking data has been deleted.")
            self.update_stats()  # Refresh stats tab
            if self.public_monitor_showing:
                self.update_public_monitor()  # Refresh public monitor if showing

    def toggle_public_monitor(self):
        if not self.public_monitor_showing:
            self.create_public_monitor()
            if (
                hasattr(self, "public_monitor_btn")
                and self.public_monitor_btn.winfo_exists()
            ):
                self.public_monitor_btn.config(text="Hide Public Monitor")
        else:
            self.close_public_monitor()

    def create_public_monitor(self):
        if (
            self.public_monitor_showing
            and self.public_monitor
            and self.public_monitor.winfo_exists()
        ):
            self.public_monitor.lift()
            return
        self.public_monitor = tk.Toplevel(self.root)
        self.public_monitor.title("Monitor")
        size_map = {"Small": "220x200", "Medium": "300x260", "Large": "380x320"}
        self.public_monitor.geometry(size_map.get(self.size_var.get(), "300x260"))
        theme_name = self.theme_var.get()
        theme = self.color_themes.get(theme_name, self.color_themes["Blue"])
        self.public_monitor.configure(bg=theme["bg"])
        self.public_monitor.attributes("-alpha", self.opacity_var.get())
        if self.always_on_top_var.get():
            self.public_monitor.attributes("-topmost", True)
        main_frame = tk.Frame(self.public_monitor, bg=theme["bg"])
        main_frame.pack(fill="both", expand=True, padx=5, pady=5)
        header_frame = tk.Frame(main_frame, bg=theme["bg"])
        header_frame.pack(fill="x")
        tk.Label(
            header_frame,
            text="STATUS",
            bg=theme["bg"],
            fg=theme["fg"],
            font=("Arial", 9, "bold"),
        ).pack(side="left", padx=2)
        controls_frame = tk.Frame(header_frame, bg=theme["bg"])
        controls_frame.pack(side="right")
        self.focus_btn = tk.Button(
            controls_frame,
            text="F",
            width=2,
            relief=tk.FLAT,
            bg=theme["bg"],
            fg=theme["fg"],
            activebackground=theme["accent"],
            command=self.toggle_focus_mode,
            font=("Arial", 8, "bold"),
        )
        self.focus_btn.pack(side="left", padx=(0, 1))
        tk.Button(
            controls_frame,
            text="×",
            width=2,
            relief=tk.FLAT,
            bg=theme["bg"],
            fg=theme["fg"],
            activebackground="red",
            activeforeground="white",
            command=self.close_public_monitor,
            font=("Arial", 8, "bold"),
        ).pack(side="left")
        content_frame = tk.Frame(main_frame, bg=theme["bg"])
        content_frame.pack(fill="both", expand=True, pady=5)
        status_frame = tk.Frame(content_frame, bg=theme["bg"])
        status_frame.pack(fill="x")
        self.public_status_label = tk.Label(
            status_frame,
            text="NOT TRACKING",
            font=("Arial", 10, "bold"),
            bg=theme["bg"],
            fg=theme["fg"],
        )
        self.public_status_label.pack(side="left")
        self.status_indicator_canvas = tk.Canvas(
            status_frame, width=12, height=12, bg=theme["bg"], highlightthickness=0
        )
        self.status_indicator_canvas.pack(side="left", padx=3, pady=2)
        self.status_dot = self.status_indicator_canvas.create_oval(
            1, 1, 11, 11, fill="red", outline=""
        )
        self.public_time_label = tk.Label(
            content_frame,
            text="Time: --:--:--",
            font=("Arial", 9),
            bg=theme["bg"],
            fg=theme["fg"],
        )
        self.public_time_label.pack(anchor="w")
        self.public_app_label = tk.Label(
            content_frame,
            text="Current: None",
            font=("Arial", 9),
            bg=theme["bg"],
            fg=theme["fg"],
        )
        self.public_app_label.pack(anchor="w")
        self.focus_indicator = tk.Label(
            content_frame,
            text="",
            font=("Arial", 8, "italic"),
            bg=theme["bg"],
            fg=theme["accent"],
        )
        self.focus_indicator.pack(anchor="w")
        self.mini_chart_frame = tk.Frame(content_frame, bg=theme["bg"])
        self.mini_chart_frame.pack(fill="both", expand=True, pady=(5, 0))
        goal_frame = tk.Frame(main_frame, bg=theme["bg"])
        goal_frame.pack(fill="x", pady=(5, 0))
        tk.Label(
            goal_frame,
            text="Daily Goal:",
            bg=theme["bg"],
            fg=theme["fg"],
            font=("Arial", 8),
        ).pack(anchor="w")
        progress_container = tk.Frame(goal_frame, bg=theme["bg"], height=18)
        progress_container.pack(fill="x", pady=(0, 3))
        self.progress_canvas = tk.Canvas(
            progress_container,
            height=15,
            bg=theme.get("progress_bg", "#f0f0f0"),
            highlightthickness=1,
            highlightbackground=theme["fg"],
        )
        self.progress_canvas.pack(fill="x", expand=True)
        self.progress_bar_rect = self.progress_canvas.create_rectangle(
            0, 0, 0, 15, fill=theme["accent"], outline=""
        )
        self.progress_bar_text_id = self.progress_canvas.create_text(
            5, 8, anchor="w", text="0%", fill=theme["fg"], font=("Arial", 7)
        )
        self.public_monitor.protocol("WM_DELETE_WINDOW", self.close_public_monitor)
        self.public_monitor_showing = True
        self.update_public_monitor()

    def close_public_monitor(self):
        if self.public_monitor and self.public_monitor.winfo_exists():
            if (
                hasattr(self, "mini_chart_frame")
                and self.mini_chart_frame.winfo_exists()
            ):
                for widget in self.mini_chart_frame.winfo_children():
                    if isinstance(widget, FigureCanvasTkAgg):
                        plt.close(widget.figure)  # Close matplotlib figure
            self.public_monitor.destroy()
        self.public_monitor = None
        self.public_monitor_showing = False
        if (
            hasattr(self, "public_monitor_btn")
            and self.public_monitor_btn.winfo_exists()
        ):
            self.public_monitor_btn.config(text="Show Public Monitor")

    def update_public_monitor(self):
        if (
            not self.public_monitor_showing
            or not self.public_monitor
            or not self.public_monitor.winfo_exists()
        ):
            return
        theme_name = self.theme_var.get()
        theme = self.color_themes.get(theme_name, self.color_themes["Blue"])
        status_text = "TRACKING" if self.tracking else "NOT TRACKING"
        status_color = theme["accent"] if self.tracking else "red"
        if (
            hasattr(self, "public_status_label")
            and self.public_status_label.winfo_exists()
        ):
            self.public_status_label.config(text=status_text)
        if (
            hasattr(self, "status_indicator_canvas")
            and self.status_indicator_canvas.winfo_exists()
        ):
            self.status_indicator_canvas.itemconfig(self.status_dot, fill=status_color)
        if not self.tracking:  # Update labels if not tracking
            if (
                hasattr(self, "public_time_label")
                and self.public_time_label.winfo_exists()
            ):
                self.public_time_label.config(text="Time: --:--:--")
            if (
                hasattr(self, "public_app_label")
                and self.public_app_label.winfo_exists()
            ):
                self.public_app_label.config(text="Current: None")

        self.toggle_focus_mode(update_only=True)  # Update focus indicator
        self._update_public_monitor_mini_chart(theme)
        if self.root.winfo_exists():  # Ensure root exists for `after` call
            self.root.after(
                50, lambda t=theme: self._update_public_monitor_progress_bar(t)
            )

    def update_monitor_opacity(self, event=None):
        if (
            self.public_monitor_showing
            and self.public_monitor
            and self.public_monitor.winfo_exists()
        ):
            self.public_monitor.attributes("-alpha", self.opacity_var.get())

    def update_monitor_size(self, event=None):
        if (
            self.public_monitor_showing
            and self.public_monitor
            and self.public_monitor.winfo_exists()
        ):
            current_focus = self.focus_mode
            self.close_public_monitor()
            self.create_public_monitor()
            if current_focus:  # Re-apply focus mode if it was on
                self.toggle_focus_mode(force_on=True)

    def update_monitor_topmost(self, event=None):
        if (
            self.public_monitor_showing
            and self.public_monitor
            and self.public_monitor.winfo_exists()
        ):
            self.public_monitor.attributes("-topmost", self.always_on_top_var.get())

    def update_monitor_theme(self, event=None):
        if (
            self.public_monitor_showing
            and self.public_monitor
            and self.public_monitor.winfo_exists()
        ):
            current_focus = self.focus_mode
            self.close_public_monitor()
            self.create_public_monitor()
            if current_focus:  # Re-apply focus mode
                self.toggle_focus_mode(force_on=True)

    def toggle_focus_mode(
        self, event=None, force_on=None, force_off=None, update_only=False
    ):
        if not update_only:
            if force_on is not None:
                self.focus_mode = force_on
            elif force_off is True:
                self.focus_mode = False
            else:
                self.focus_mode = not self.focus_mode

        if (
            self.public_monitor_showing
            and self.public_monitor
            and self.public_monitor.winfo_exists()
            and hasattr(self, "focus_indicator")  # Check if widgets exist
            and hasattr(self, "focus_btn")
        ):
            theme = self.color_themes.get(
                self.theme_var.get(), self.color_themes["Blue"]
            )
            fg_on_accent = theme.get(
                "fg_on_accent", theme["bg"]
            )  # Fallback for fg_on_accent

            if self.focus_mode:
                if self.focus_indicator.winfo_exists():
                    self.focus_indicator.config(text="FOCUS ON", fg=theme["accent"])
                if self.focus_btn.winfo_exists():
                    self.focus_btn.config(
                        relief=tk.SUNKEN, bg=theme["accent"], fg=fg_on_accent
                    )
            else:
                if self.focus_indicator.winfo_exists():
                    self.focus_indicator.config(text="")  # Clear text
                if self.focus_btn.winfo_exists():
                    self.focus_btn.config(
                        relief=tk.FLAT, bg=theme["bg"], fg=theme["fg"]
                    )

        # Always update progress bar as focus mode affects productive time calculation
        if (
            self.public_monitor_showing
            and self.public_monitor
            and self.public_monitor.winfo_exists()
        ):
            self._update_public_monitor_progress_bar(
                self.color_themes.get(self.theme_var.get())
            )

    def _update_public_monitor_mini_chart(self, theme):
        if (
            not hasattr(self, "mini_chart_frame")
            or not self.mini_chart_frame.winfo_exists()
        ):
            return
        for widget in self.mini_chart_frame.winfo_children():
            if isinstance(widget, FigureCanvasTkAgg):
                plt.close(widget.figure)  # Close matplotlib figure
            widget.destroy()

        source_data_raw = {}  # Use raw names for aggregation before display
        chart_title = "App Usage"

        # Aggregate data based on tracking status or today's sessions
        current_app_times_copy = self.app_times.copy()  # Use a copy
        if self.tracking and current_app_times_copy:
            source_data_raw = current_app_times_copy
            chart_title = "Current Session Apps"
        else:
            today_str = datetime.datetime.now().strftime("%Y-%m-%d")
            today_sessions_data_raw = {}
            for s in self.data["sessions"]:
                if s.get("date") == today_str:
                    for app_raw, time_val in s.get("applications", {}).items():
                        today_sessions_data_raw[app_raw] = (
                            today_sessions_data_raw.get(app_raw, 0) + time_val
                        )
            if today_sessions_data_raw:
                source_data_raw = today_sessions_data_raw
                chart_title = "Today's Top Apps"
            else:
                tk.Label(
                    self.mini_chart_frame,
                    text="No app data yet.",
                    bg=theme["bg"],
                    fg=theme["fg"],
                    font=("Arial", 8),
                ).pack(pady=5)
                return

        if not source_data_raw:
            tk.Label(
                self.mini_chart_frame,
                text="No app data.",
                bg=theme["bg"],
                fg=theme["fg"],
                font=("Arial", 8),
            ).pack(pady=5)
            return

        # Process raw names for display in mini-chart
        apps_data_for_chart_display = {}
        for raw_name, seconds in source_data_raw.items():
            # Heuristic for cleaner display names in mini-chart
            name_parts = raw_name.split(" - ")
            display_name = name_parts[-1] if len(name_parts) > 0 else raw_name
            # If it's a process name like "chrome.exe", keep it.
            # If it's "Unknown (...)", keep it.
            # If it was "Window Title - Process.exe", display_name becomes "Process.exe"

            # Further simplification for common cases if needed, e.g. generic "Unknown"
            if "unknown" in display_name.lower() and len(name_parts) > 1:
                # Try to get a more specific part if "Unknown" is the last part of a multi-part title
                display_name = name_parts[-2] if len(name_parts) > 1 else name_parts[0]

            # Truncate display name for chart labels
            display_name_truncated = (
                display_name[:12] + "..." if len(display_name) > 15 else display_name
            )
            apps_data_for_chart_display[display_name_truncated] = (
                apps_data_for_chart_display.get(display_name_truncated, 0) + seconds
            )

        sorted_apps_display = sorted(
            apps_data_for_chart_display.items(), key=lambda x: x[1], reverse=True
        )

        top_n = 3
        chart_apps_display = sorted_apps_display[:top_n]

        if not chart_apps_display:
            tk.Label(
                self.mini_chart_frame,
                text="Not enough data.",
                bg=theme["bg"],
                fg=theme["fg"],
                font=("Arial", 8),
            ).pack(pady=5)
            return

        labels = [app_name for app_name, _ in chart_apps_display]
        sizes = [time_val for _, time_val in chart_apps_display]

        try:
            fig, ax = plt.subplots(
                figsize=(2.8, 1.8), dpi=65
            )  # Small figure for monitor
            fig.patch.set_facecolor(theme["bg"])
            ax.set_facecolor(theme["bg"])

            ax.barh(labels, sizes, color=theme["chart"], height=0.6)

            ax.tick_params(axis="x", colors=theme["fg"], labelsize=6)
            ax.tick_params(axis="y", colors=theme["fg"], labelsize=7)
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)
            ax.spines["bottom"].set_color(theme["fg"])
            ax.spines["left"].set_color(theme["fg"])

            ax.invert_yaxis()  # Top item first
            ax.set_xlabel("Time (sec)", color=theme["fg"], fontsize=7)

            plt.tight_layout(pad=0.2)  # Adjust padding

            canvas = FigureCanvasTkAgg(fig, master=self.mini_chart_frame)
            canvas_widget = canvas.get_tk_widget()
            canvas_widget.configure(bg=theme["bg"])
            canvas_widget.pack(fill="both", expand=True)
            canvas.draw()
        except Exception as e:
            print(f"Error creating mini chart: {e}")
            if self.mini_chart_frame.winfo_exists():
                tk.Label(
                    self.mini_chart_frame,
                    text="Chart error.",
                    bg=theme["bg"],
                    fg=theme["fg"],
                ).pack()

    def _get_productive_time_today(self):
        today_str = datetime.datetime.now().strftime("%Y-%m-%d")
        total_seconds_for_goal = 0

        focus_keywords = [
            kw.strip().lower()
            for kw in self.focus_apps_var.get().split(",")
            if kw.strip()  # Ensure keyword is not empty
        ]

        # Aggregate all time spent today, using raw application names
        todays_aggregated_app_times_raw = {}

        # Include current session if tracking
        if self.tracking:
            current_app_times_copy = self.app_times.copy()
            for app_raw_name, time_spent in current_app_times_copy.items():
                todays_aggregated_app_times_raw[app_raw_name] = (
                    todays_aggregated_app_times_raw.get(app_raw_name, 0) + time_spent
                )

        # Include saved sessions for today
        for session in self.data["sessions"]:
            if session.get("date") == today_str:
                # If tracking, ensure we don't double-count the current session's start if it was saved and restarted
                # This logic assumes a new tracking session replaces the old self.app_times
                is_current_session_already_partially_counted = False
                if self.tracking and self.start_time:
                    session_start_dt = datetime.datetime.strptime(
                        session.get("start_time", "00:00:00"), "%H:%M:%S"
                    ).time()
                    current_tracking_start_dt = datetime.datetime.fromtimestamp(
                        self.start_time
                    ).time()
                    if (
                        session.get("date")
                        == datetime.datetime.fromtimestamp(self.start_time).strftime(
                            "%Y-%m-%d"
                        )
                        and session_start_dt == current_tracking_start_dt
                    ):
                        is_current_session_already_partially_counted = True

                if not (
                    self.tracking
                    and is_current_session_already_partially_counted
                    and session.get("applications") == self.app_times
                ):

                    for app_raw_name, time_spent in session.get(
                        "applications", {}
                    ).items():
                        todays_aggregated_app_times_raw[app_raw_name] = (
                            todays_aggregated_app_times_raw.get(app_raw_name, 0)
                            + time_spent
                        )

        for app_raw_name, time_spent in todays_aggregated_app_times_raw.items():
            app_lower = app_raw_name.lower()
            if (
                self.focus_mode and focus_keywords
            ):  # If focus mode is on AND keywords are defined
                if any(keyword in app_lower for keyword in focus_keywords):
                    total_seconds_for_goal += time_spent
            else:  # If focus mode is off, or no keywords, all time is productive for goal
                total_seconds_for_goal += time_spent

        return total_seconds_for_goal

    def _update_public_monitor_progress_bar(self, theme):
        if (
            not hasattr(self, "progress_canvas")
            or not self.progress_canvas.winfo_exists()
        ):
            return
        if theme is None:  # Fallback theme if not provided
            theme = self.color_themes.get(
                self.theme_var.get(), self.color_themes["Blue"]
            )

        try:
            goal_hours_str = self.goal_var.get()
            goal_hours = float(goal_hours_str) if goal_hours_str.strip() else 8.0
            if goal_hours <= 0:
                goal_hours = 8.0  # Default to 8 if invalid
        except ValueError:
            goal_hours = 8.0  # Default if conversion fails

        goal_seconds = goal_hours * 3600
        productive_seconds_today = self._get_productive_time_today()

        progress_percentage = (
            min((productive_seconds_today / goal_seconds) * 100, 100.0)  # Cap at 100%
            if goal_seconds > 0
            else 0.0
        )

        self.progress_canvas.update_idletasks()  # Ensure dimensions are up-to-date
        canvas_width = self.progress_canvas.winfo_width()

        # Retry mechanism if canvas width is not yet determined (common on first draw)
        if canvas_width <= 1:  # Canvas not ready
            retries = getattr(self, "_progress_bar_retries", 0)
            if retries < 10:  # Limit retries
                self._progress_bar_retries = retries + 1
                if self.root.winfo_exists():
                    self.root.after(
                        100, lambda t=theme: self._update_public_monitor_progress_bar(t)
                    )
            else:  # Max retries reached
                if hasattr(self, "_progress_bar_retries"):
                    del self._progress_bar_retries
            return
        if hasattr(self, "_progress_bar_retries"):  # Clear retries if successful
            del self._progress_bar_retries

        bar_width = (progress_percentage / 100.0) * canvas_width
        self.progress_canvas.coords(self.progress_bar_rect, 0, 0, bar_width, 15)
        self.progress_canvas.itemconfig(self.progress_bar_rect, fill=theme["accent"])

        current_hours_display = productive_seconds_today / 3600.0
        text_on_bar = f"{current_hours_display:.1f}h / {goal_hours:.1f}h ({progress_percentage:.0f}%)"
        text_x_position = canvas_width / 2

        # Determine text color based on contrast with bar
        # Create temporary text to get its bounding box for intelligent color choice
        temp_text_id = self.progress_canvas.create_text(
            text_x_position, 8, text=text_on_bar, anchor="center", font=("Arial", 7)
        )
        text_bbox = self.progress_canvas.bbox(temp_text_id)
        self.progress_canvas.delete(temp_text_id)  # Delete temporary text

        # Delete old persistent text item before creating new one to avoid overlap
        if (
            hasattr(self, "progress_bar_text_id")
            and self.progress_canvas.winfo_exists()
        ):
            try:  # It might have been deleted if progress_canvas was reconfigured
                self.progress_canvas.delete(self.progress_bar_text_id)
            except tk.TclError:
                pass  # Item already deleted

        text_color = theme["fg"]  # Default text color
        if text_bbox and bar_width > text_bbox[0] + (text_bbox[2] - text_bbox[0]) / 2:
            # If more than half of the text is on the colored bar, use contrast color
            text_color = theme.get(
                "fg_on_accent", theme["bg"]
            )  # Fallback for fg_on_accent

        self.progress_bar_text_id = self.progress_canvas.create_text(
            text_x_position,
            8,  # Vertically centered
            text=text_on_bar,
            anchor="center",
            fill=text_color,
            font=("Arial", 7),
        )
        self.progress_canvas.config(  # Update background colors
            bg=theme.get("progress_bg", "#f0f0f0"), highlightbackground=theme["fg"]
        )


if __name__ == "__main__":
    root = tk.Tk()
    app = ProductivityTracker(root)

    def on_closing():
        try:
            if app.tracking:
                app.stop_tracking()
            if app.public_monitor_showing:
                app.close_public_monitor()
            plt.close("all")  # Close all matplotlib figures
        except Exception as e:
            print(f"Error during closing: {e}")
        finally:
            if root.winfo_exists():  # Check if root still exists before destroying
                root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()
