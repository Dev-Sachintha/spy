# Personal Productivity Tracker
[Personal Productivity Tracker Screenshot]

![Screenshot (573)](https://github.com/user-attachments/assets/2a0e62b4-f358-463a-9f2d-14298bca47cf)
![Screenshot (579)](https://github.com/user-attachments/assets/c0f46d23-a4a7-4c54-bc15-826eaa2e1ef8)
![Screenshot (578)](https://github.com/user-attachments/assets/8ca6585b-95f7-465f-b41e-1cc9dc2306a0)
![Screenshot (577)](https://github.com/user-attachments/assets/410e112e-3f4b-45db-bf70-51c7eaf59919)
![Screenshot (576)](https://github.com/user-attachments/assets/5aa6e255-5a1f-47c0-bf15-200afc47e7f3)
![Screenshot (575)](https://github.com/user-attachments/assets/a4d6aa7e-0a30-4ab1-912c-42c0baf299aa)
![Screenshot (574)](https://github.com/user-attachments/assets/e587be32-1954-4871-9b8a-f79c43b2b459)



A desktop application built with Python and Tkinter to help you track your application usage, monitor productivity, and gain insights into your computer habits.

## Features

*   **Application Time Tracking:**
    *   Monitors the active window and records time spent on each application.
    *   Attempts to identify applications by window title or process name (e.g., `chrome.exe`) for unknown/empty titles.
    *   Tracks time in sessions, which are saved locally.
*   **Statistics Dashboard:**
    *   View aggregated application usage data for "Today," "Yesterday," "This Week," "This Month," or "All Time."
    *   Displays data in a table with application name, time spent, and percentage.
    *   Includes a pie chart visualizing the top applications.
*   **Public Monitor Overlay:**
    *   A small, customizable, always-on-top (optional) window providing real-time feedback.
    *   Displays current tracking status, elapsed session time, and the currently active application.
    *   Features a mini bar chart of top app usage for the current session or today.
    *   Includes a daily productivity goal progress bar.
    *   **Focus Mode:** Filters the daily goal progress to only count time spent on user-defined "productive" applications.
    *   Customizable:
        *   Opacity
        *   Size (Small, Medium, Large)
        *   Color Themes (Blue, Green, Purple, Dark)
        *   Always-on-top toggle
*   **Network Devices Tab:**
    *   Displays entries from your computer's ARP cache (`arp -a` command).
    *   Lists recently communicated-with devices on your local network (IP, MAC, Interface, Type).
*   **Settings & Configuration:**
    *   Set a daily productivity goal (in hours).
    *   Define keywords for "Focus Mode" applications (comma-separated).
    *   Manage Public Monitor appearance.
    *   Export all tracking data to a JSON file.
    *   Clear all stored tracking data.
*   **Data Storage:**
    *   All tracking data is stored locally in `productivity_data.json`.

## Prerequisites

*   **Python:** Version 3.7+ recommended.
*   **pip:** Python package installer.
*   **Operating System:** Currently **Windows only** due to the use of `win32gui` and `win32process` for foreground window and process information.
*   The `arp` command must be available in your system's PATH for the "Network Devices" tab to function.

## Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/personal-productivity-tracker.git
    cd personal-productivity-tracker
    ```

2.  **Create and activate a virtual environment (recommended):**
    ```bash
    python -m venv venv
    # On Windows
    venv\Scripts\activate
    # On macOS/Linux
    # source venv/bin/activate
    ```

3.  **Install dependencies:**
    A `requirements.txt` file should be included. Create one with the following content:
    ```
    psutil
    matplotlib
    Pillow # Matplotlib TkAgg backend might need this
    pywin32 # For win32gui, win32process
    ```
    Then install:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

1.  Run the application:
    ```bash
    python productivity_tracker.py
    ```
    (Or `python __main__.py` if you structure it as a package)

2.  **Tracking Tab:**
    *   Click "Start Tracking (Local)" to begin monitoring your application usage.
    *   The status, elapsed time, and current application will be updated.
    *   A list of applications and time spent in the current session will populate the tree view.
    *   Click "Stop Tracking" to end the current session. Data will be saved.
    *   Click "Show Public Monitor" to toggle the overlay window.

3.  **Statistics Tab:**
    *   Select a time range (Today, Yesterday, etc.) from the dropdown.
    *   Click "Refresh" to update the stats if needed (auto-updates on selection change).
    *   View application usage in the table and pie chart.

4.  **Network Devices Tab:**
    *   Click "Show ARP Cache (arp -a)" to populate the list with devices from your local ARP cache.
    *   *Note: This reflects devices your computer has recently communicated with and is not a full network scan.*

5.  **Settings Tab:**
    *   Adjust Public Monitor settings (opacity, size, theme, always-on-top).
    *   Set your "Daily Productivity Goal" in hours.
    *   Define "Focus Mode Apps" using comma-separated keywords (e.g., `Word,Excel,Code,Photoshop`). These keywords are case-insensitive and will be matched against the application name or window title.
    *   "Export Data" to save your `productivity_data.json` to a custom location.
    *   "Clear All Data" to reset your tracking history (confirmation required).

## Data Storage

*   All session data is stored in a JSON file named `productivity_data.json` in the same directory as the script.
*   Each session records the date, start time, end time, duration, and a dictionary of applications with the time spent on each (in seconds).

## Known Limitations / Future Ideas

*   **Windows Only:** Core tracking functionality relies on Windows-specific libraries. Porting to macOS/Linux would require different libraries for active window/process detection (e.g., `pyobjc-framework-Quartz` for macOS, X11 utilities for Linux).
*   **Idle Detection:** The "Idle Detection" feature in settings is currently a placeholder and not implemented.
*   **Remote Tracking:** The "Remote Device Monitoring" IP field is conceptual. True remote tracking would require an agent on the target device.
*   **Application Bundling:** The application is run via a Python script. It could be bundled into an executable using tools like PyInstaller or cx_Freeze for easier distribution.
*   **More Granular "Unknown" App Detection:** While process names are used for some unknowns, further heuristics could be developed.
*   **Background Process:** Run as a background service for continuous tracking without the main UI always open.
*   **Advanced Analytics:** More detailed reports, trend analysis, and customizable categories for productive/unproductive apps.

## Contributing

Contributions are welcome! If you have ideas for improvements or bug fixes, please follow these steps:

1.  Fork the repository.
2.  Create a new branch (`git checkout -b feature/your-feature-name` or `bugfix/issue-description`).
3.  Make your changes and commit them (`git commit -m 'Add some feature'`).
4.  Push to the branch (`git push origin feature/your-feature-name`).
5.  Open a Pull Request.

Please ensure your code adheres to existing style and provide a clear description of your changes.

## License

This project is licensed under the [MIT License](LICENSE).
*(You'll need to create a `LICENSE` file with the MIT License text or your chosen license).*

## Acknowledgements

*   The `psutil` library for system and process utilities.
*   The `pywin32` library for Windows API access.
*   `Matplotlib` for charting.
