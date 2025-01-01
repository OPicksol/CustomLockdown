import os
import random
import tkinter as tk
from tkinter import messagebox, font, ttk
from PIL import Image, ImageTk
import vlc
import pyautogui
import sys
import logging

LOG_FILE = "Log.txt"
CONFIG_FILE = "config.txt"
DEFAULT_PASSWORD = "password"
DEFAULT_VIDEO_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "videos")
CUSTOM_VIDEO_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "custom_videos")

logging.basicConfig(filename=LOG_FILE, level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

def log_message(message, level=logging.INFO):
    logging.log(level, message)

def load_config():
    config = {}
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as config_file:
                config = dict(line.strip().split('=', 1) for line in config_file if '=' in line)
            log_message(f"Loaded configuration: {config}")
        except Exception as e:
            log_message(f"Error loading configuration: {e}", level=logging.ERROR)
    return config

class LockApp:
    def __init__(self, master, config):
        self.master = master
        self.config = config
        self.correct_password = config.get("password", DEFAULT_PASSWORD)
        self.use_default_videos = config.get("use_default_videos", "True") == "True"
        self.timer_duration = int(config.get("timer", 0)) if config.get("timer") else 0
        self.timer_position = config.get("timer_position", "top_right")
        self.theme_name = config.get("theme", "Light")
        self.mode = config.get("mode", "fullscreen")
        self.bg_color = config.get("bg_color", "#000000")
        self.screensaver_image_path = config.get("screensaver_image_path", "")
        self.popup_text_file = config.get("popup_text_file", "")
        self.popup_interval = float(config.get("popup_interval", 0.5))
        self.popup_duration = float(config.get("popup_duration", 5))
        self.popup_video_size_percent = int(config.get("popup_video_size", 5)) / 20
        self.show_skip_button = config.get("show_skip_button", "True") == "True"
        self.show_password = config.get("show_password", "True") == "True"
        self.video_folder = DEFAULT_VIDEO_FOLDER if self.use_default_videos else CUSTOM_VIDEO_FOLDER
        self.popups = []
        self.popup_windows = []
        self.popup_job = None
        self.text_popup_job = None
        self.timer_running = False
        self.time_left = self.timer_duration
        self.timer_label = None
        self.player = None
        self.instance = None
        self.screensaver_label = None
        self.screensaver_image = None
        self.current_videos = []
        self.is_screensaver_active = False
        self.fullscreen_controls_visible = True  # Initially visible in fullscreen
        self.controls_hide_timer = None
        self.show_popup_bg = config.get("show_popup_bg", "True") == "True"
        self.popup_background_window = None  # For popup mode background
        self.fullscreen_controls_visible_forced = False # Flag for forced visibility
        self._playback_before_screensaver = False

        log_message(f"Loaded password: {self.correct_password}")

        self.setup_ui()
        if self.mode == "fullscreen":
            self.master.after(100, self.hide_fullscreen_controls)
        self.lock_input()
        self.load_videos()
        self.start_video_playback()
        if self.timer_duration > 0:
            self.start_timer()
        if self.mode == "windowed" and self.popup_text_file:
            self.create_popup_background()
            self.load_popups()
            self.schedule_popups()

        self.master.focus_force()

    def create_popup_background(self):
        if self.mode == "windowed":
            self.popup_background_window = tk.Toplevel(self.master)
            self.popup_background_window.title("Pop-up Background")
            self.popup_background_window.config(bg=self.bg_color)
            self.popup_background_window.attributes('-fullscreen', True)
            self.popup_background_window.attributes('-topmost', False) # Ensure other popups are on top
            self.popup_background_window.overrideredirect(True) # Remove window decorations

            # Make sure the background window doesn't get focus
            self.popup_background_window.bind("<FocusIn>", lambda event: self.master.focus_force())

    def setup_ui(self):
        self.master.title("Video Player")
        self.master.attributes('-topmost', True)

        if self.mode == "fullscreen":
            self.master.wm_attributes('-fullscreen', True)
            self.master.config(bg='black')
        else:
            self.master.overrideredirect(True)
            self.master.config(bg=self.bg_color)

        # Themed styling
        self.style = ttk.Style(self.master)
        if self.theme_name == "Dark":
            self.style.theme_use('clam')
            self.style.configure('TButton', background='#333', foreground='white', padding=5)
            self.style.configure('TScale', background='#333', foreground='white')
            self.style.configure('TLabel', background='black', foreground='white')
            self.style.configure('TEntry', fieldbackground='white', foreground='black')
        else:
            self.style.theme_use('vista')
            self.style.configure('TButton', padding=5)
            self.style.configure('TLabel', background='black', foreground='black')

        if self.mode == "fullscreen":
           self.style.configure('Fullscreen.TFrame', background=self.bg_color)
        elif self.mode != "fullscreen":
           self.style.configure('TLabel', background=self.bg_color)

        self.style.configure('Transparent.TFrame', background='')

        self.video_frame = tk.Frame(self.master, bg='black')
        self.video_frame.pack(fill="both", expand=True)

        # Navigation frame
        self.nav_frame = ttk.Frame(self.master, style='Transparent.TFrame')
        if self.mode == "fullscreen":
            self.nav_frame.config(style="Fullscreen.TFrame")
        self.nav_frame.pack(side="bottom", fill="x")

        self.control_frame = ttk.Frame(self.nav_frame, padding=5, style='Transparent.TFrame')
        if self.mode == "fullscreen":
            self.control_frame.config(style="Fullscreen.TFrame")
        self.control_frame.pack(side="bottom", fill="x")

        self.nav_controls = ttk.Frame(self.nav_frame, padding=5, style='Transparent.TFrame')
        if self.mode == "fullscreen":
            self.nav_controls.config(style="Fullscreen.TFrame")
        self.nav_controls.pack(side="top", fill="x")

        if self.show_password:
            ttk.Label(self.control_frame, text="Password:").pack(side="left", padx=5)
            self.password_entry = ttk.Entry(self.control_frame, show="*")
            self.password_entry.pack(side="left", padx=5)
            self.password_button = ttk.Button(self.control_frame, text="Enter", command=self.verify_password)
            self.password_button.pack(side="left", padx=5)
            self.password_entry.bind("<Return>", lambda event: self.verify_password())

        if self.show_skip_button:
            self.skip_button = ttk.Button(self.nav_controls, text="Skip Video", command=self.play_next_video)
            self.skip_button.pack(side="left", padx=5)

        ttk.Label(self.nav_controls, text="Speed:").pack(side="left", padx=5)
        self.playback_speed_var = tk.DoubleVar(value=1.0)
        self.playback_speed_scale = ttk.Scale(self.nav_controls, from_=0.5, to=2.0, orient=tk.HORIZONTAL,
                                             variable=self.playback_speed_var, command=self.update_playback_speed)
        self.playback_speed_scale.pack(side="left", padx=5)

        ttk.Label(self.nav_controls, text="Volume:").pack(side="left", padx=5)
        self.volume_var = tk.IntVar(value=100)
        self.volume_scale = ttk.Scale(self.nav_controls, from_=0, to=100, orient=tk.HORIZONTAL,
                                       variable=self.volume_var, command=self.update_volume)
        self.volume_scale.pack(side="left", padx=5)

        self.timer_label = ttk.Label(self.master, text="")

        # Transparent area around the timer to show controls
        self.timer_hitbox = tk.Frame(self.master, bg="", highlightthickness=0)  # Invisible frame
        self.timer_hitbox.bind("<Enter>", self.show_fullscreen_controls)

        self.position_timer_label()

        self.master.bind("<Key>", self.on_key_press)
        self.master.bind("<F1>", self.toggle_screensaver)

        if self.mode == "fullscreen":
            self.video_frame.bind("<Motion>", self.show_fullscreen_controls)
            self.nav_frame.bind("<Enter>", self.on_controls_enter)
            self.nav_frame.bind("<Leave>", self.hide_fullscreen_controls_on_leave)
            self.control_frame.bind("<Enter>", self.on_controls_enter)
            self.control_frame.bind("<Leave>", self.hide_fullscreen_controls_on_leave)
            self.nav_controls.bind("<Enter>", self.on_controls_enter)
            self.nav_controls.bind("<Leave>", self.hide_fullscreen_controls_on_leave)
            self.master.after(100, self.hide_fullscreen_controls)

    def position_timer_label(self):
        if self.timer_label:
            position_config = {
                "top_left": {"anchor": "nw", "padx": 10, "pady": 10},
                "top_right": {"anchor": "ne", "padx": 10, "pady": 10},
                "bottom_left": {"anchor": "sw", "padx": 10, "pady": 10},
                "bottom_right": {"anchor": "se", "padx": 10, "pady": 10},
            }.get(self.timer_position, {"anchor": "ne", "padx": 10, "pady": 10})

            screen_width = self.master.winfo_screenwidth()
            screen_height = self.master.winfo_screenheight()

            relx = position_config["padx"] / screen_width if "left" in self.timer_position else 1 - (position_config["padx"] / screen_width)
            rely = position_config["pady"] / screen_height if "top" in self.timer_position else 1 - (position_config["pady"] / screen_height)

            self.timer_label.place(relx=relx, rely=rely, anchor=position_config["anchor"])
            self.timer_label.lift()

            # Position the transparent hitbox around the timer
            timer_x = self.timer_label.winfo_rootx() - 10  # Add some padding
            timer_y = self.timer_label.winfo_rooty() - 10
            timer_width = self.timer_label.winfo_width() + 20
            timer_height = self.timer_label.winfo_height() + 20
            self.timer_hitbox.place(x=timer_x, y=timer_y, width=timer_width, height=timer_height)
            self.timer_hitbox.lift(self.timer_label) # Ensure hitbox is above the video

    def on_controls_enter(self, event=None):
        if self.mode == "fullscreen":
            if self.controls_hide_timer:
                self.master.after_cancel(self.controls_hide_timer)

    def hide_fullscreen_controls_on_leave(self, event=None):
        if self.mode == "fullscreen" and self.fullscreen_controls_visible and not self.fullscreen_controls_visible_forced:
            self.controls_hide_timer = self.master.after(2000, self.hide_fullscreen_controls) # Adjust time as needed

    def show_fullscreen_controls(self, event=None):
        if self.mode == "fullscreen":
            self.fullscreen_controls_visible = True
            self.nav_frame.pack(side="bottom", fill="x")
            if self.controls_hide_timer:
                self.master.after_cancel(self.controls_hide_timer)

    def hide_fullscreen_controls(self):
        if self.mode == "fullscreen":
            self.fullscreen_controls_visible = False
            self.nav_frame.pack_forget()
            self.fullscreen_controls_visible_forced = False

    def load_videos(self):
        if not os.path.exists(self.video_folder):
            log_message(f"Video folder '{self.video_folder}' does not exist.", level=logging.ERROR)
            messagebox.showerror("Error", f"Video folder '{self.video_folder}' does not exist.")
            return

        self.current_videos = [
            os.path.join(self.video_folder, f)
            for f in os.listdir(self.video_folder)
            if f.endswith(('.mp4', '.avi', '.mkv'))
        ]
        if not self.current_videos:
            log_message(f"No videos found in '{self.video_folder}'.", level=logging.WARNING)
            messagebox.showerror("Error", "No videos found in the videos folder.")

    def load_popups(self):
        try:
            with open(self.popup_text_file, 'r') as file:
                self.popups = [line.strip() for line in file]
        except Exception as e:
            log_message(f"Error loading popup text file: {e}", level=logging.ERROR)

    def schedule_popups(self):
        if self.mode == "windowed" and self.popups:
            self.schedule_text_popup()
            self.schedule_video_popup()

    def schedule_text_popup(self):
        if self.mode == "windowed" and self.popups:
            self.show_text_popup()
            self.text_popup_job = self.master.after(random.randint(100, 500), self.schedule_text_popup)

    def schedule_video_popup(self):
        if self.mode == "windowed" and self.current_videos:
            self.show_video_popup()
            self.popup_job = self.master.after(int(self.popup_interval * 1000), self.schedule_video_popup)

    def show_text_popup(self):
        if self.mode == "windowed" and self.popups:
            popup_text = random.choice(self.popups)
            all_fonts = font.families()
            random_font_family = random.choice(all_fonts)
            popup_font = font.Font(family=random_font_family, size=random.randint(30, 60), weight="bold")
            r, g, b = [random.randint(50, 200) for _ in range(3)]
            desaturated_color = '#%02x%02x%02x' % (r, g, b)

            text_popup = tk.Toplevel(self.master, bg=self.bg_color if self.show_popup_bg else '')
            text_popup.overrideredirect(True)
            text_popup.attributes('-topmost', True)

            screen_width = self.master.winfo_screenwidth()
            screen_height = self.master.winfo_screenheight()
            text_label = ttk.Label(text_popup, text=popup_text, font=popup_font, foreground=desaturated_color, background=self.bg_color if self.show_popup_bg else '')
            text_label.pack(expand=True, fill='both')

            text_popup_width = text_label.winfo_reqwidth()
            text_popup_height = text_label.winfo_reqheight()
            x = random.randint(0, screen_width - text_popup_width)
            y = random.randint(0, screen_height - text_popup_height)
            text_popup.geometry(f"{text_popup_width}x{text_popup_height}+{x}+{y}")

            self.popup_windows.append(text_popup)
            self.master.after(200, lambda w=text_popup: self.hide_popup(w))

    def show_video_popup(self):
        if self.mode == "windowed" and self.current_videos:
            popup_window = tk.Toplevel(self.master, bg=self.bg_color if self.show_popup_bg else 'black')
            popup_window.overrideredirect(True)
            popup_window.attributes('-topmost', True)

            screen_width = self.master.winfo_screenwidth()
            screen_height = self.master.winfo_screenheight()
            width = int(screen_width * self.popup_video_size_percent)
            height = int(screen_height * self.popup_video_size_percent)
            x = random.randint(0, screen_width - width)
            y = random.randint(0, screen_height - height)
            popup_window.geometry(f"{width}x{height}+{x}+{y}")

            popup_video_frame = tk.Frame(popup_window, bg='black')
            popup_video_frame.pack(fill="both", expand=True)

            try:
                instance = vlc.Instance("--no-xlib", "--quiet")
                player = instance.media_player_new()
                video = random.choice(self.current_videos)
                media = instance.media_new_path(video)
                player.set_media(media)
                player.set_hwnd(popup_video_frame.winfo_id())

                # Get video duration in milliseconds
                media.parse()
                duration = media.get_duration()

                # Loop the video
                def video_ended(event):
                    player.play()
                player.event_manager().event_attach(vlc.EventType.MediaPlayerEndReached, video_ended)
                player.play()
                if duration > self.popup_duration * 1000:
                    start_time = random.randint(0, int(duration - (self.popup_duration * 1000)))
                    player.set_time(start_time)
                popup_window.player = player
                log_message(f"Pop-up video started: {os.path.basename(video)}{' at random time' if duration > self.popup_duration * 1000 else ''}.")
                self.popup_windows.append(popup_window)
                self.master.after(int(self.popup_duration * 1000), lambda w=popup_window: self.hide_popup(w))
            except Exception as e:
                log_message(f"Error creating pop-up video: {e}", level=logging.ERROR)

    def hide_popup(self, window):
        if window in self.popup_windows:
            if hasattr(window, 'player'):
                try:
                    window.player.stop()
                    window.player.event_manager().event_detach(vlc.EventType.MediaPlayerEndReached)
                except Exception as e:
                    log_message(f"Error stopping pop-up video: {e}", level=logging.ERROR)
            try:
                window.destroy()
            except Exception as e:
                log_message(f"Error destroying pop-up window: {e}", level=logging.ERROR)
            self.popup_windows.remove(window)

    def lock_input(self):
        pyautogui.FAILSAFE = False
        pyautogui.moveTo(0, 0)

    def unlock_input(self):
        pyautogui.FAILSAFE = True

    def start_video_playback(self):
        if not self.current_videos:
            return

        self.instance = vlc.Instance("--no-xlib", "--quiet")
        self.player = self.instance.media_player_new()
        self.player.set_hwnd(self.video_frame.winfo_id())
        self.play_next_video()

        if self.mode == "fullscreen":
            self.player.set_fullscreen(True)
            self.master.after(1000, self.loop_videos)

    def loop_videos(self):
        if self.mode == "fullscreen" and not self.player.is_playing():
            self.play_next_video()
        if self.mode == "fullscreen":
            self.master.after(1000, self.loop_videos)

    def play_next_video(self):
        if self.current_videos:
            video = random.choice(self.current_videos)
            media = self.instance.media_new(video)
            self.player.set_media(media)
            self.player.play()
            log_message(f"Now playing: {os.path.basename(video)}")
        else:
            log_message("No videos available to play.", level=logging.WARNING)

    def update_playback_speed(self, speed):
        if self.player:
            self.player.set_rate(float(speed))

    def update_volume(self, volume):
        if self.player:
            self.player.audio_set_volume(int(volume))

    def start_timer(self):
        self.timer_running = True
        self.time_left = self.timer_duration
        self.update_timer_display()
        self.master.after(1000, self.update_timer)

    def update_timer(self):
        if self.timer_running:
            self.time_left -= 1
            self.update_timer_display()
            if self.time_left <= 0:
                log_message("Timer ended.")
                self.unlock_input()
                self.master.quit()
            else:
                self.master.after(1000, self.update_timer)

    def update_timer_display(self):
        if self.timer_label:
            minutes, seconds = divmod(self.time_left, 60)
            self.timer_label.config(text=f"{minutes:02}:{seconds:02}")
            self.position_timer_label()

    def verify_password(self):
        if self.password_entry.get() == self.correct_password:
            log_message("Correct password entered.")
            self.unlock_input()
            self.master.quit()
        else:
            log_message("Incorrect password attempt.", level=logging.WARNING)
            messagebox.showerror("Incorrect Password", "The password you entered is incorrect.")
            self.password_entry.delete(0, tk.END)

    def on_key_press(self, event):
        log_message(f"Key pressed: {event.keysym}, Keycode: {event.keycode}", level=logging.DEBUG)
        if event.keysym == "Escape":
            log_message("Escape key pressed.")
            self.unlock_input()
            self.master.quit()
        elif self.show_password and event.widget != self.password_entry:
            return "break"
        elif not self.show_password:
            return "break"
        elif self.mode == "fullscreen" and event.keysym in ['Backquote', 'Tab']: # Corrected key symbols
            self.show_fullscreen_controls()
            self.fullscreen_controls_visible_forced = True
            if self.controls_hide_timer:
                self.master.after_cancel(self.controls_hide_timer)
            self.controls_hide_timer = self.master.after(5000, self.hide_fullscreen_controls)

    def toggle_screensaver(self, event=None):
        if self.mode == "windowed":
            return  # Disable screensaver in popup mode
        log_message(f"Toggle Screensaver called. Current state: {'Active' if self.is_screensaver_active else 'Inactive'}", level=logging.DEBUG)
        if self.player:
            if self.is_screensaver_active:
                self.hide_screensaver()
                if self.mode == "fullscreen" and self._playback_before_screensaver:
                    self.player.play()
                elif self.mode != "fullscreen" and self._playback_before_screensaver:
                    self.player.play()
                self.is_screensaver_active = False
                log_message("Screensaver deactivated.")
            else:
                if self.player.is_playing():
                    self._playback_before_screensaver = True
                    self.player.pause()
                else:
                    self._playback_before_screensaver = False
                if self.screensaver_image_path:
                    try:
                        self.screensaver_image = ImageTk.PhotoImage(Image.open(self.screensaver_image_path))
                        self.screensaver_label = tk.Label(self.master, image=self.screensaver_image, bg='black')
                        self.screensaver_label.place(relx=0.5, rely=0.5, anchor="center")
                        for popup in self.popup_windows:
                            if isinstance(popup, tk.Toplevel) and popup.winfo_exists():
                                popup.withdraw()
                        self.is_screensaver_active = True
                        log_message("Screensaver activated.")
                    except Exception as e:
                        log_message(f"Error loading screensaver image: {e}", level=logging.ERROR)

    def hide_screensaver(self, event=None):
        log_message("Hide Screensaver called.", level=logging.DEBUG)
        if self.screensaver_label:
            self.screensaver_label.place_forget()
            self.screensaver_label = None
            for popup in self.popup_windows:
                if isinstance(popup, tk.Toplevel) and popup.winfo_exists():
                    popup.deiconify()
            self.video_frame.lift()
            if self.mode == "fullscreen":
                # Reapply style with background color
                self.style.configure('Fullscreen.TFrame', background=self.bg_color)
                self.nav_frame.config(style='Fullscreen.TFrame')
                self.control_frame.config(style='Fullscreen.TFrame')
                self.nav_controls.config(style='Fullscreen.TFrame')
                if self.player:
                    self.player.set_fullscreen(True)  # Reapply video fullscreen
            self.show_fullscreen_controls()

def main():
    config = load_config()

    answer = messagebox.askyesno(
        "Warning",
        "This program will play videos continuously until you type the correct password, press the ESC key, or the timer runs out. Do you want to continue?"
    )
    if not answer:
        log_message("User chose not to continue.")
        return

    root = tk.Tk()
    app = LockApp(root, config)
    root.mainloop()

if __name__ == "__main__":
    main()