import customtkinter as ctk
import sqlite3
import threading
import webbrowser
import time
import datetime
import pygame
import json
import os
import numpy as np
from plyer import notification
from dateutil.relativedelta import relativedelta
from tkinter import messagebox
import sys
import tempfile

# Configure CustomTkinter
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class FocusSessionApp:
    def resource_path(self, relative_path):
        """Get absolute path to resource, works for dev and PyInstaller"""
        try:
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path)

    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("Infinity FocusPro")
        self.root.geometry("1200x776")
        self.center_window()

        # set window icon
        try:
            # For Windows
            # self.root.iconbitmap('focuspro.ico') 
            # OR for cross-platform compatibility:
            self.root.wm_iconbitmap(self.resource_path('focuspro.ico'))

        except Exception as e:
            print(f"Could not load icon: {e}")

        self.root.configure(fg_color="#0a0a0a")
        
        # Initialize pygame for sound
        pygame.mixer.init()
        
        # Variables
        self.session_active = False
        self.session_paused = False
        self.timer_thread = None
        self.current_session_id = None
        self.session_duration = 25  # minutes
        self.remaining_time = 0
        self.daily_goal = 8  # hours
        self.selected_task = "Maths"
        self.last_progress = 0
        self.task_categories = ["Maths", "Physics", "ICT", "General"]
        
        # Database setup
        self.setup_database()
        
        # Setup UI
        self.setup_ui()
        
        # Load today's progress
        self.update_daily_progress()
        
        # Load settings
        self.load_settings()

        # Start the update checker
        self.root.after(1000, self.check_for_updates)

    def center_window(self):
        self.root.update_idletasks()
        width = 1200
        height = 770
        
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        
        self.root.geometry(f"+{x}+{y}")


    def get_graph_data(self, range_selection):
        """Get data for graph based on range selection"""
        today = datetime.date.today()
        
        if range_selection == "this_week":
            start_date = today - datetime.timedelta(days=today.weekday())
            end_date = today
        elif range_selection == "last_week":
            start_date = today - datetime.timedelta(days=today.weekday() + 7)
            end_date = today - datetime.timedelta(days=today.weekday() + 1)
        elif range_selection == "this_month":
            start_date = today.replace(day=1)
            end_date = today
        elif range_selection == "last_month":
            if today.month == 1:
                start_date = datetime.date(today.year - 1, 12, 1)
                end_date = datetime.date(today.year, 1, 1) - datetime.timedelta(days=1)
            else:
                start_date = datetime.date(today.year, today.month - 1, 1)
                end_date = today.replace(day=1) - datetime.timedelta(days=1)
        else:
            start_date = today - datetime.timedelta(days=7)
            end_date = today
            
        # Get data from database
        self.cursor.execute('''
            SELECT date, SUM(completed) as total_minutes
            FROM sessions 
            WHERE date >= ? AND date <= ?
            GROUP BY date
            ORDER BY date
        ''', (start_date.isoformat(), end_date.isoformat()))
        
        results = self.cursor.fetchall()
        
        # Fill in missing dates with 0
        data = []
        current_date = start_date
        result_dict = {date: minutes for date, minutes in results}
        
        while current_date <= end_date:
            date_str = current_date.isoformat()
            minutes = result_dict.get(date_str, 0)
            data.append((date_str, minutes))
            current_date += datetime.timedelta(days=1)
            
        return data

    def check_for_updates(self):
        """Check for database changes periodically"""
        if not self.session_active:  # Only check when not in a session
            today_minutes = self.get_today_total_minutes()
            current_progress = min(today_minutes / (self.daily_goal * 60), 1.0)
            
            # Update UI if progress changed
            if current_progress != self.last_progress:
                self.update_daily_progress()
                self.last_progress = current_progress
        
        # Check again after 5 seconds
        self.root.after(5000, self.check_for_updates)
        
    def setup_database(self):
        """Initialize SQLite database"""
        self.conn = sqlite3.connect('focus_sessions.db', check_same_thread=False)
        self.cursor = self.conn.cursor()
        
        # Create tables
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                task_category TEXT NOT NULL,
                duration INTEGER NOT NULL,
                completed INTEGER NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        ''')
        
        self.conn.commit()
        
    def setup_ui(self):
        """Setup the main UI with Vercel-inspired design"""
        # Main container
        main_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Create a header frame for the title and top analytics button
        header_frame = ctk.CTkFrame(main_frame, fg_color="transparent", height=50)
        header_frame.pack(fill="x", pady=(0, 20))
        
        # FocusPro title in top left
        ctk.CTkLabel(
            header_frame,
            text="FocusPro",
            font=ctk.CTkFont(size=30, weight="bold"),
            text_color="#efefef"
        ).pack(side="left", padx=10)
        
        # Analytics button in top right
        ctk.CTkButton(
            header_frame,
            text="Analytics",
            command=self.open_browser_analysis,
            width=100,
            height=42,
            font=ctk.CTkFont(size=15),
            fg_color="#ccc",
            hover_color="#eee",
            text_color="#1d1d1d",
            corner_radius=6
        ).pack(side="right", padx=10)
        
        # Top section (Focus Sessions and Daily Progress)
        top_content_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        top_content_frame.pack(fill="x", pady=(0, 20))
        
        # Focus Sessions Section
        self.setup_focus_section(top_content_frame)
        
        # Daily Progress Section
        self.setup_daily_progress_section(top_content_frame)
        
        # Bottom Graph Section (with its own analytics button)
        self.setup_graph_section(main_frame)
        
    def setup_focus_section(self, parent):
        """Setup focus session section with modern design"""
        focus_frame = ctk.CTkFrame(parent, corner_radius=12, fg_color="#171717", border_width=1, border_color="#333333")
        focus_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        # Title
        title_label = ctk.CTkLabel(focus_frame, text="Focus Sessions", 
                                 font=ctk.CTkFont(size=20, weight="bold"),
                                 text_color="#ffffff")
        title_label.pack(pady=(20, 15))
        
        # Task selector
        task_frame = ctk.CTkFrame(focus_frame, fg_color="transparent")
        task_frame.pack(pady=8)
        
        ctk.CTkLabel(task_frame, text="Task Category:", 
                    font=ctk.CTkFont(size=14), text_color="#a1a1aa").pack(side="left", padx=(0, 10))
        
        self.task_dropdown = ctk.CTkComboBox(
            task_frame, 
            values=self.task_categories,
            command=self.on_task_change, 
            width=180,
            fg_color="#262626",
            button_color="#2e2e2e",
            button_hover_color="#403f3f",
            border_color="#2e2e2e",
            dropdown_fg_color="#2b2b2b",
            dropdown_text_color="#efefef",
            dropdown_hover_color="#403f3f"
        )
        self.task_dropdown.set("Maths")
        self.task_dropdown.pack(side="left")
        
        # Duration selector
        duration_frame = ctk.CTkFrame(focus_frame, fg_color="transparent")
        duration_frame.pack(pady=12)
        
        ctk.CTkLabel(duration_frame, text="Duration (minutes):", 
                    font=ctk.CTkFont(size=14), text_color="#a1a1aa").pack(side="left", padx=(0, 10))
        
        # Duration input box
        self.duration_entry = ctk.CTkEntry(
            duration_frame,
            width=60,
            placeholder_text="25",
            fg_color="#262626",
            border_color="#3f3f46",
            text_color="#ffffff",
            validate="key",
            validatecommand=(self.root.register(self.validate_duration_input), '%P')
        )
        self.duration_entry.insert(0, "25")
        self.duration_entry.pack(side="left", padx=(0, 10))
        self.duration_entry.bind("<Return>", lambda e: self.update_slider_from_entry())
        
        # Duration slider
        self.duration_slider = ctk.CTkSlider(
            duration_frame, 
            from_=1, 
            to=240, 
            number_of_steps=239, 
            command=self.update_entry_from_slider,
            button_color="#3b82f6",
            progress_color="#3b82f6",
            fg_color="#262626"
        )
        self.duration_slider.set(25)
        self.duration_slider.pack(side="left", padx=(0, 10))
        
        # Circular progress
        self.setup_circular_progress(focus_frame)
        
        # Control buttons
        self.setup_control_buttons(focus_frame)

        self.duration_label = ctk.CTkLabel(
            duration_frame, 
            text="25 min", 
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#efefef"
        )
        self.duration_label.pack(side="left")

    def validate_duration_input(self, new_value):
        """Validate duration input (1-240 minutes)"""
        if new_value == "":
            return True
        try:
            value = int(new_value)
            return 1 <= value <= 240
        except ValueError:
            return False

    def update_entry_from_slider(self, value):
        """Update entry when slider moves"""
        minutes = int(float(value))
        self.duration_entry.delete(0, "end")
        self.duration_entry.insert(0, str(minutes))
        self.on_duration_change(value)  # Update other components

    def update_slider_from_entry(self):
        """Update slider when entry changes"""
        try:
            minutes = int(self.duration_entry.get())
            if 1 <= minutes <= 240:
                self.duration_slider.set(minutes)
                self.on_duration_change(minutes)  # Update other components
            else:
                messagebox.showerror("Error", "Duration must be 1-240 minutes")
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid number")

    def on_duration_change(self, value):
        """Handle duration changes from either input"""
        minutes = int(float(value))
        self.duration_label.configure(text=f"{minutes} min")
        self.session_duration = minutes
        if not self.session_active:
            self.remaining_time = minutes * 60
            self.draw_progress_circle(0)
        
    def setup_circular_progress(self, parent):
        """Setup modern circular progress indicator"""
        progress_frame = ctk.CTkFrame(parent, fg_color="transparent")
        progress_frame.pack(pady=20)
        
        # Create circular progress canvas
        self.progress_canvas = ctk.CTkCanvas(
            progress_frame, 
            width=220, 
            height=220, 
            bg="#171717",
            highlightthickness=0,
            bd=0
        )
        self.progress_canvas.pack()
        
        # Status label
        self.status_label = ctk.CTkLabel(
            progress_frame, 
            text="Ready to start", 
            font=ctk.CTkFont(size=14),
            text_color="#a1a1aa"
        )
        self.status_label.pack(pady=(15, 0))
        
        # Draw initial circle
        self.draw_progress_circle(0)
        
    def setup_control_buttons(self, parent):
        """Setup beautiful control buttons"""
        button_frame = ctk.CTkFrame(parent, fg_color="transparent")
        button_frame.pack(pady=20)
        
        # Start/Pause button
        self.start_pause_btn = ctk.CTkButton(
            button_frame, 
            text="Start", 
            command=self.toggle_session,
            width=120,
            height=42,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color="#262626",
            hover_color="#21d153",
            text_color="#efefef",
            corner_radius=8,
            border_color="#3f3f46",
            border_width=1
        )
        self.start_pause_btn.pack(side="left", padx=8)
        
        # Reset button
        self.reset_btn = ctk.CTkButton(
            button_frame, 
            text="Reset", 
            command=self.reset_session,
            width=100,
            height=42,
            font=ctk.CTkFont(size=15),
            fg_color="#262626",
            hover_color="#3f3f46",
            text_color="#ffffff",
            corner_radius=8,
            border_color="#3f3f46",
            border_width=1
        )
        self.reset_btn.pack(side="left", padx=8)
        
        # Stop button
        self.stop_btn = ctk.CTkButton(
            button_frame, 
            text="Stop", 
            command=self.stop_session,
            width=100,
            height=42,
            font=ctk.CTkFont(size=15),
            fg_color="#262626",
            hover_color="#e3102c",
            text_color="#efefef",
            corner_radius=8,
            border_color="#3f3f46",
            border_width=1
        )
        self.stop_btn.pack(side="left", padx=8)
        
    def setup_daily_progress_section(self, parent):
        """Setup daily progress section with modern design"""
        daily_frame = ctk.CTkFrame(
            parent, 
            corner_radius=12, 
            fg_color="#171717",
            border_width=1,
            border_color="#333333"
        )
        daily_frame.pack(side="right", fill="both", expand=True, padx=(10, 0))
        
        # Title
        title_label = ctk.CTkLabel(
            daily_frame, 
            text="Daily Progress", 
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#ffffff"
        )
        title_label.pack(pady=(20, 15))
        
        # Progress ring
        ring_frame = ctk.CTkFrame(daily_frame, fg_color="transparent")
        ring_frame.pack(pady=20)
        
        self.daily_canvas = ctk.CTkCanvas(
            ring_frame, 
            width=200, 
            height=200, 
            bg="#171717",
            highlightthickness=0,
            bd=0
        )
        self.daily_canvas.pack()
        
        # Progress percentage
        self.daily_progress_label = ctk.CTkLabel(
            ring_frame, 
            text="0%", 
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color="#ffffff"
        )
        
        # Daily stats
        stats_frame = ctk.CTkFrame(daily_frame, fg_color="transparent")
        stats_frame.pack(pady=12)
        
        # Today's time
        self.today_time_label = ctk.CTkLabel(
            stats_frame, 
            text="Today: 0h 0m", 
            font=ctk.CTkFont(size=14),
            text_color="#a1a1aa"
        )
        self.today_time_label.pack(pady=4)
        
        # Streak
        self.streak_label = ctk.CTkLabel(
            stats_frame, 
            text="Streak: 0 days", 
            font=ctk.CTkFont(size=14),
            text_color="#a1a1aa"
        )
        self.streak_label.pack(pady=4)
        
        # Goal setting
        goal_frame = ctk.CTkFrame(daily_frame, fg_color="transparent")
        goal_frame.pack(pady=12)
        
        ctk.CTkLabel(
            goal_frame, 
            text="Daily Goal (hours):", 
            font=ctk.CTkFont(size=14),
            text_color="#a1a1aa"
        ).pack(side="left", padx=(0, 10))
        
        self.goal_entry = ctk.CTkEntry(
            goal_frame, 
            width=70, 
            placeholder_text="8",
            fg_color="#262626",
            border_color="#3f3f46",
            text_color="#ffffff"
        )
        self.goal_entry.pack(side="left", padx=(0, 10))
        self.goal_entry.insert(0, str(self.daily_goal))
        
        update_goal_btn = ctk.CTkButton(
            goal_frame, 
            text="Update", 
            command=self.update_daily_goal,
            width=80,
            height=34,
            font=ctk.CTkFont(size=14),
            fg_color="#262626",
            hover_color="#a354d1",
            corner_radius=6,
            text_color="#efefef",
            border_color="#3f3f46",
            border_width=1
        )
        update_goal_btn.pack(side="left")
        
    def setup_graph_section(self, parent):
        graph_frame = ctk.CTkFrame(
            parent, 
            corner_radius=12, 
            fg_color="#0a0a0a",
            border_width=1,
            border_color="#0a0a0a"
        )
        graph_frame.pack(fill="both", expand=True)
        
        ctk.CTkLabel(
            graph_frame,
            text="©2025 Infinity Minds • FocusPro",
            pady=(10),
            text_color="#525252"
        ).pack()

    def open_browser_analysis(self):
        """Generate HTML file and open in browser"""
        try:
            html_content = self.generate_html_with_data()
            temp_path = os.path.join(tempfile.gettempdir(), "analytics.html")
            with open(temp_path, "w") as f:
                f.write(html_content)

            webbrowser.open(f"file://{temp_path}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open analyzer: {str(e)}")

    def get_filtered_graph_data(self, filter_type, start_date=None, end_date=None):
        """Get filtered data based on the selected filter type"""
        today = datetime.date.today()
        
        if filter_type == "week":
            # Current week (Monday to Sunday)
            start_date = today - datetime.timedelta(days=today.weekday())
            end_date = start_date + datetime.timedelta(days=6)
        elif filter_type == "month":
            # Current month
            start_date = today.replace(day=1)
            end_date = (today.replace(day=28) + datetime.timedelta(days=4))  # Ensure we get to end of month
            end_date = end_date - datetime.timedelta(days=end_date.day - 1)
        elif filter_type == "year":
            # Current year
            start_date = today.replace(month=1, day=1)
            end_date = today.replace(month=12, day=31)
        elif filter_type == "custom" and start_date and end_date:
            # Custom range (dates provided)
            pass
        else:
            # Default to showing all data
            self.cursor.execute("SELECT MIN(date) FROM sessions")
            min_date = self.cursor.fetchone()[0]
            start_date = datetime.date.fromisoformat(min_date) if min_date else today
            end_date = today
        
        # Get data from database
        self.cursor.execute('''
            SELECT date, task_category, SUM(completed) as total_minutes
            FROM sessions
            WHERE date >= ? AND date <= ?
            GROUP BY date, task_category
            ORDER BY date
        ''', (start_date.isoformat(), end_date.isoformat()))
        
        results = self.cursor.fetchall()
        
        return [{
            'date': row[0],
            'category': row[1],
            'minutes': row[2] if row[2] else 0
        } for row in results], start_date, end_date

    # Update the generate_html_with_data method
    def generate_html_with_data(self):
        """Generate complete HTML with embedded JSON data and area chart"""
        # Get all data (we'll filter in JavaScript)
        self.cursor.execute('''
            SELECT date, task_category, SUM(completed) as total_minutes
            FROM sessions
            GROUP BY date, task_category
            ORDER BY date
        ''')
        
        results = self.cursor.fetchall()
        
        # Convert to JS format
        js_data = []
        for row in results:
            date_obj = datetime.datetime.strptime(row[0], "%Y-%m-%d")
            js_data.append({
                'date': row[0],  # Keep as YYYY-MM-DD for filtering
                'display_date': date_obj.strftime("%Y-%m-%d"),  # For default display
                'hours': round(row[2] / 60, 2) if row[2] else 0,
                'category': row[1]
            })
        
        # Get date range for default view (last 7 days)
        end_date = datetime.date.today()
        start_date = end_date - datetime.timedelta(days=6)
        
        # Read template HTML
        html_path = self.resource_path("graph.html")
        if not os.path.exists(html_path):
            raise FileNotFoundError(f"Missing graph.html at {html_path}")
        with open(html_path, "r") as f:
            html_template = f.read()

        
        # Inject data and configuration
        return html_template.replace(
            '/*DATA_PLACEHOLDER*/', 
            f"""
            const allGraphData = {json.dumps(js_data)};
            const dailyGoal = {self.daily_goal};
            const defaultStartDate = "{start_date.isoformat()}";
            const defaultEndDate = "{end_date.isoformat()}";
            """
        )                                                            

    def get_all_graph_data(self):
        """Fetch all graph data from database"""
        conn = sqlite3.connect('focus_sessions.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT date, task_category, SUM(completed) as total_minutes
            FROM sessions
            GROUP BY date, task_category
            ORDER BY date
        ''')
        
        results = cursor.fetchall()
        conn.close()
        
        return [{
            'date': row[0],
            'category': row[1],
            'minutes': row[2]
        } for row in results]
        
    def draw_progress_circle(self, progress):
        """Draw modern gradient circular progress indicator"""
        self.progress_canvas.delete("all")
        
        # Dimensions
        width, height = 220, 220
        center_x, center_y = width//2, height//2
        radius = 90
        line_width = 14
        
        # Background circle (subtle)
        self.progress_canvas.create_oval(
            center_x - radius, center_y - radius,
            center_x + radius, center_y + radius,
            outline="#262626", width=line_width
        )
        
        # Modern gradient progress arc
        if progress > 0:
            start_angle = 90
            extent = -360 * progress
            
            # Create segments for smooth gradient (optimized for performance)
            segments = 72  # 5 degree steps
            for i in range(0, int(abs(extent)), int(360/segments)):
                angle = start_angle - i
                segment_progress = i/abs(extent) if extent != 0 else 0
                color = self.get_gradient_color(segment_progress)
                
                # Draw arc segment
                self.progress_canvas.create_arc(
                    center_x - radius, center_y - radius,
                    center_x + radius, center_y + radius,
                    start=angle, extent=-360/segments,
                    outline=color, width=line_width,
                    style="arc"
                )
        
        # Center text with time display
        mins = self.remaining_time // 60
        secs = self.remaining_time % 60
        self.progress_canvas.create_text(
            center_x, center_y,
            text=f"{mins:02d}:{secs:02d}",
            font=("Segoe UI", 28, "bold"),
            fill="#ffffff"
        )
        
        # Task name below time
        self.progress_canvas.create_text(
            center_x, center_y + 40,
            text=self.selected_task[:12],
            font=("Segoe UI", 12),
            fill="#a1a1aa"
        )
        
    def draw_daily_progress_ring(self, progress):
        """Draw modern daily progress ring"""
        self.daily_canvas.delete("all")
        
        # Dimensions
        width, height = 200, 200
        center_x, center_y = width//2, height//2
        radius = 80
        line_width = 10
        
        # Background circle
        self.daily_canvas.create_oval(
            center_x - radius, center_y - radius,
            center_x + radius, center_y + radius,
            outline="#262626", width=line_width
        )
        
        # Progress arc with gradient
        if progress > 0:
            start_angle = 90
            extent = -360 * progress
            
            segments = 72  # 5 degree steps
            for i in range(0, int(abs(extent)), int(360/segments)):
                angle = start_angle - i
                segment_progress = i/abs(extent) if extent != 0 else 0
                color = self.get_daily_gradient_color(segment_progress, progress)
                
                # Draw arc segment
                self.daily_canvas.create_arc(
                    center_x - radius, center_y - radius,
                    center_x + radius, center_y + radius,
                    start=angle, extent=-360/segments,
                    outline=color, width=line_width,
                    style="arc"
                )

        # Center text with time display
        percentage = int(progress * 100)
        self.daily_canvas.create_text(
            center_x, center_y,
            text=f"{percentage}%",
            font=("Segoe UI", 28, "bold"),
            fill="#ffffff"
        )
        
        # Task name below time
        self.daily_canvas.create_text(
            center_x, center_y + 40,
            text="Completed",
            font=("Segoe UI", 12),
            fill="#a1a1aa"
        )
    
    def get_gradient_color(self, ratio):
        """Generate blue to purple gradient"""
        # Blue (#3b82f6) to purple (#8b5cf6)
        r = int(59 + (139-59)*ratio)
        g = int(130 + (92-130)*ratio)
        b = int(246 + (246-246)*ratio)
        return f'#{r:02x}{g:02x}{b:02x}'
    
    def get_daily_gradient_color(self, segment_progress, overall_progress):
        """Generate gradient from blue to green (for daily progress)"""
        if overall_progress < 1.0:
            # Blue (#3b82f6) to teal (#14b8a6)
            r = int(59 + (20-59)*segment_progress)
            g = int(130 + (184-130)*segment_progress)
            b = int(246 + (166-246)*segment_progress)
        else:
            # Green (#22c55e)
            r, g, b = 34, 197, 94
        return f'#{r:02x}{g:02x}{b:02x}'

    def on_task_change(self, task):
        """Handle task category change"""
        self.selected_task = task
        
    def on_duration_change(self, value):
        """Handle duration change"""
        self.session_duration = int(float(value))
        self.duration_label.configure(text=f"{self.session_duration} min")
        
        if not self.session_active:
            self.remaining_time = self.session_duration * 60
            self.update_timer_display()
            
    def on_range_change(self, value):
        """Handle graph range change"""
        pass  # Handled by web view now
        
    def toggle_session(self):
        """Start or pause session"""
        if not self.session_active:
            self.start_session()
        else:
            if self.session_paused:
                self.resume_session()
            else:
                self.pause_session()
                
    def start_session(self):
        """Start a new focus session"""
        self.session_active = True
        self.session_paused = False
        self.remaining_time = self.session_duration * 60
        self.selected_task = self.task_dropdown.get()
        
        # Save session to database
        self.save_session_start()
        
        # Update UI
        self.start_pause_btn.configure(text="Pause")
        self.status_label.configure(text="Focus session active")
        
        # Start timer thread
        self.timer_thread = threading.Thread(target=self.run_timer, daemon=True)
        self.timer_thread.start()
        
    def pause_session(self):
        """Pause current session"""
        self.session_paused = True
        self.start_pause_btn.configure(text="Resume")
        self.status_label.configure(text="Session paused")
        
        # Update session in database
        self.update_session_progress()
        
    def resume_session(self):
        """Resume paused session"""
        self.session_paused = False
        self.start_pause_btn.configure(text="Pause")
        self.status_label.configure(text="Focus session active")
        
    def reset_session(self):
        """Reset current session"""
        self.session_active = False
        self.session_paused = False
        self.remaining_time = self.session_duration * 60
        
        # Update UI
        self.start_pause_btn.configure(text="Start")
        self.status_label.configure(text="Ready to start")
        self.update_timer_display()
        self.draw_progress_circle(0)
        
    def stop_session(self):
        """Stop and save current session"""
        if self.session_active:
            self.session_active = False
            self.session_paused = False
            
            # Save final session data
            self.save_session_end()
            
            # Update UI
            self.start_pause_btn.configure(text="Start")
            self.status_label.configure(text="Session completed")
            
            # Update daily progress
            self.update_daily_progress()

            # Session completed
            if self.session_active and self.remaining_time <= 0:
                self.root.after(0, self.session_completed)
            
            # reset
            self.reset_session()
            
    def run_timer(self):
        """Main timer loop"""
        while self.session_active and self.remaining_time > 0:
            if not self.session_paused:
                self.remaining_time -= 1
                
                # Update UI
                self.root.after(0, self.update_timer_display)
                
                # Auto-save progress every 30 seconds
                if self.remaining_time % 30 == 0:
                    self.update_session_progress()
                    
            time.sleep(1)
            
        # Session completed
        if self.session_active and self.remaining_time <= 0:
            self.root.after(0, self.session_completed)
            
    def session_completed(self):
        """Handle session completion"""
        self.session_active = False
        self.session_paused = False
        
        # Save session
        self.save_session_end()
        
        # Update UI
        self.start_pause_btn.configure(text="Start")
        self.status_label.configure(text="Session completed!")
        self.draw_progress_circle(1.0)

        #Reset
        self.reset_session()
        
        # Show notification
        self.show_notification("Focus Session Complete!", 
                             f"Great job! You completed a {self.session_duration} minute session.")
        
        # Play notification sound
        self.play_notification_sound()
        
        # Update daily progress
        self.update_daily_progress()
        
        # Check if daily goal reached
        today_minutes = self.get_today_total_minutes()
        if today_minutes >= self.daily_goal * 60:
            self.show_notification("Daily Goal Achieved!", 
                                 f"Congratulations! You've reached your daily goal of {self.daily_goal} hours!")
            
    def update_timer_display(self):
        """Update timer display"""
        minutes = self.remaining_time // 60
        seconds = self.remaining_time % 60
        time_str = f"{minutes:02d}:{seconds:02d}"
        
        # Update progress circle
        total_seconds = self.session_duration * 60
        progress = 1.0 - (self.remaining_time / total_seconds)
        self.draw_progress_circle(progress)
        
    def save_session_start(self):
        """Save session start to database"""
        date_str = datetime.date.today().isoformat()
        start_time = datetime.datetime.now().isoformat()
        
        self.cursor.execute('''
            INSERT INTO sessions (date, task_category, duration, completed, start_time)
            VALUES (?, ?, ?, ?, ?)
        ''', (date_str, self.selected_task, self.session_duration, 0, start_time))
        
        self.current_session_id = self.cursor.lastrowid
        self.conn.commit()

    
        
    def update_session_progress(self):
        """Update session progress in database"""
        if self.current_session_id:
            completed_seconds = (self.session_duration * 60) - self.remaining_time
            completed_minutes = completed_seconds // 60
            
            self.cursor.execute('''
                UPDATE sessions SET completed = ? WHERE id = ?
            ''', (completed_minutes, self.current_session_id))
            self.conn.commit()
            
    def save_session_end(self):
        """Save session end to database"""
        if self.current_session_id:
            completed_seconds = (self.session_duration * 60) - self.remaining_time
            completed_minutes = completed_seconds // 60
            end_time = datetime.datetime.now().isoformat()
            
            self.cursor.execute('''
                UPDATE sessions SET completed = ?, end_time = ? WHERE id = ?
            ''', (completed_minutes, end_time, self.current_session_id))
            self.conn.commit()
            
    def get_today_total_minutes(self):
        """Get total minutes for today with connection refresh"""
        try:
            # Refresh connection to see external changes
            self.conn.commit()
            today = datetime.date.today().isoformat()
            self.cursor.execute('''
                SELECT SUM(completed) FROM sessions WHERE date = ?
            ''', (today,))
            result = self.cursor.fetchone()
            return result[0] if result[0] else 0
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return 0
        
    def update_daily_progress(self):
        """Update daily progress display"""
        today_minutes = self.get_today_total_minutes()
        daily_goal_minutes = self.daily_goal * 60
        
        # Calculate progress
        progress = min(today_minutes / daily_goal_minutes, 1.0) if daily_goal_minutes > 0 else 0
        
        # Update UI
        hours = today_minutes // 60
        minutes = today_minutes % 60
        self.today_time_label.configure(text=f"Today: {hours}h {minutes}m")
        
        percentage = int(progress * 100)
        self.daily_progress_label.configure(text=f"{percentage}%")
        
        # Update progress ring
        self.draw_daily_progress_ring(progress)
        
        # Update streak
        streak = self.calculate_streak()
        self.streak_label.configure(text=f"Streak: {streak} days")
        
    def calculate_streak(self):
        """Calculate current streak"""
        # Get last 30 days of data
        end_date = datetime.date.today()
        start_date = end_date - datetime.timedelta(days=30)
        
        self.cursor.execute('''
            SELECT date, SUM(completed) as total_minutes
            FROM sessions 
            WHERE date >= ? AND date <= ?
            GROUP BY date
            ORDER BY date DESC
        ''', (start_date.isoformat(), end_date.isoformat()))
        
        results = self.cursor.fetchall()
        daily_goal_minutes = self.daily_goal * 60
        
        streak = 0
        for date_str, total_minutes in results:
            if total_minutes >= daily_goal_minutes:
                streak += 1
            else:
                break
                
        return streak
        
    def update_graph(self):
        """Update progress graph"""
        pass  # Handled by web view now
        
    def show_notification(self, title, message):
        """Show system notification"""
        try:
            notification.notify(
                title=title,
                message=message,
                app_name="Focus Session Pro",
                timeout=5
            )
        except Exception as e:
            print(f"Notification error: {e}")
            
    def play_notification_sound(self):
        """Play notification sound"""
        try:
            # Initialize mixer if not already done
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            
            # Load and play the sound file
            sound = pygame.mixer.Sound(self.resource_path('focuspro.wav'))
            sound.play()
        
        except Exception as e:
            print(f"Error playing sound: {e}")
            # Fallback to built-in sound
            self.play_default_notification_sound()

    def play_default_notification_sound(self):
        """Fallback sound (beep)"""
        try:
            import winsound
            winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
        except:
            print("No fallback sound available")

            
    def update_daily_goal(self):
        """Update daily goal"""
        try:
            new_goal = int(self.goal_entry.get())
            if new_goal > 0:
                self.daily_goal = new_goal
                self.save_settings()
                self.update_daily_progress()
                messagebox.showinfo("Success", f"Daily goal updated to {new_goal} hours")
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid number")
            
    def save_settings(self):
        """Save settings to database"""
        self.cursor.execute('''
            INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)
        ''', ('daily_goal', str(self.daily_goal)))
        self.conn.commit()
        
    def load_settings(self):
        """Load settings from database"""
        self.cursor.execute('SELECT value FROM settings WHERE key = ?', ('daily_goal',))
        result = self.cursor.fetchone()
        if result:
            self.daily_goal = int(result[0])
            self.goal_entry.delete(0, 'end')
            self.goal_entry.insert(0, str(self.daily_goal))
            
    def on_closing(self):
        """Handle application closing"""
        if self.session_active:
            self.update_session_progress()
        self.conn.close()
        self.root.destroy()
        
    def run(self):
        """Start the application"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()


if __name__ == "__main__":
    # Create application instance
    app = FocusSessionApp()
    
    # Run the application
    app.run()