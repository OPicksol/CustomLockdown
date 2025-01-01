import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import subprocess
import re
from PIL import Image, ImageTk, UnidentifiedImageError
from datetime import datetime

# --- Constants ---
CONFIG_FILE = "config.txt"
LOG_FILE = "Log.txt"
DEFAULT_PASSWORD = "password"
MAIN_SCRIPT = "LockTestpy.py"
CONFIG_IMG_DIR = "ConfigImg"
MAX_IMAGE_WIDTH = 200  # Define a maximum width for images
GIF_UPDATE_DELAY = 100  # Milliseconds for GIF frame update

# --- Logging ---
def log_message(message, level="INFO"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] [{level}] {message}\n"
    try:
        with open(LOG_FILE, 'a') as logfile:
            logfile.write(log_line)
    except Exception as e:
        print(f"Error writing to log file: {e}")

# --- Configuration ---
def save_config(config_data):
    try:
        with open(CONFIG_FILE, 'w') as config_file:
            for key, value in config_data.items():
                config_file.write(f"{key}={value}\n")
        log_message(f"Saved configuration: {config_data}")
    except IOError as e:
        log_message(f"Error saving configuration file: {e}", level="ERROR")
        messagebox.showerror("Error", f"Failed to save configuration: {e}")

def load_config():
    default_config = {
        "password": DEFAULT_PASSWORD,
        "log_level": "INFO",
        "timer": "",
        "timer_position": "top_right",
        "theme": "Light",
        "mode": "fullscreen",
        "bg_color": "#000000",
        "screensaver_image_path": "",
        "popup_text_file": "",
        "popup_interval": "0.5",
        "popup_duration": "5",
        "popup_video_size": "5",
        "show_skip_button": "True",
        "show_password": "True",
        "show_popup_bg": "True"
    }
    if not os.path.exists(CONFIG_FILE):
        return default_config

    config_dict = {}
    try:
        with open(CONFIG_FILE, 'r') as config_file:
            for line in config_file:
                if '=' in line:
                    key, value = line.strip().split('=', 1)
                    config_dict[key] = value
        log_message(f"Loaded configuration: {config_dict}")
        return config_dict
    except IOError as e:
        log_message(f"Error loading configuration file: {e}", level="ERROR")
        messagebox.showerror("Error", f"Failed to load configuration: {e}")
        return default_config

# --- Script Execution ---
def start_main_script():
    try:
        configurator_dir = os.path.dirname(os.path.abspath(__file__))
        subprocess.Popen(['python', MAIN_SCRIPT], cwd=configurator_dir)
        log_message("LockTestpy.py started successfully.")
    except FileNotFoundError:
        log_message(f"Error: {MAIN_SCRIPT} not found.", level="ERROR")
        messagebox.showerror("Error", f"{MAIN_SCRIPT} not found in the same directory.")
    except Exception as e:
        log_message(f"Failed to start {MAIN_SCRIPT}: {e}", level="ERROR")
        messagebox.showerror("Error", f"Failed to start {MAIN_SCRIPT}: {e}")

# --- Validation ---
def is_hex_color(color_code):
    return re.match(r'^#([0-9a-fA-F]{3}){1,2}$', color_code) is not None

# --- Image Handling ---
def load_all_images():
    images = {}
    if not os.path.exists(CONFIG_IMG_DIR):
        return images

    for file in os.listdir(CONFIG_IMG_DIR):
        try:
            filepath = os.path.join(CONFIG_IMG_DIR, file)
            if file.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
                image = Image.open(filepath)
                image.thumbnail((MAX_IMAGE_WIDTH, 500))  # Initial resize with max width
                photo_image = ImageTk.PhotoImage(image)
                images[file.split('.')[0].lower()] = photo_image
                log_message(f"Loaded image: {file}")
            elif file.lower().endswith('.gif'):
                gif_frames = []
                gif_image = Image.open(filepath)
                try:
                    for i in range(gif_image.n_frames):
                        gif_image.seek(i)
                        frame = gif_image.copy().convert('RGB')
                        frame.thumbnail((MAX_IMAGE_WIDTH, 500))
                        gif_frames.append(ImageTk.PhotoImage(frame))
                    images[file.split('.')[0].lower()] = gif_frames
                    log_message(f"Loaded animated GIF: {file} with {len(gif_frames)} frames")
                except EOFError:
                    log_message(f"Incomplete GIF file: {file}", level="WARNING")
        except FileNotFoundError:
            log_message(f"Image file not found: {file}", level="WARNING")
        except UnidentifiedImageError:
            log_message(f"Cannot open image file (unsupported format): {file}", level="WARNING")
        except Exception as e:
            log_message(f"Error loading image {file}: {e}", level="ERROR")
    return images

def get_image(images, name):
    return images.get(name.lower())

def play_gif(label, frames, index=0):
    if frames:
        label.config(image=frames[index])
        label.image = frames[index]
        label.after(GIF_UPDATE_DELAY, play_gif, label, frames, (index + 1) % len(frames))

# --- File Browsing ---
def browse_file(title, filetypes, variable):
    filepath = filedialog.askopenfilename(title=title, filetypes=filetypes)
    if filepath:
        variable.set(filepath)

# --- Main Application ---
def main():
    config = load_config()

    window = tk.Tk()
    window.title("Configurator")

    images = load_all_images()

    style = ttk.Style(window)
    style.theme_use('clam')

    tab_control = ttk.Notebook(window)

    def browse_videos():
        zip_path = filedialog.askopenfilename(
            title="Select a ZIP file containing videos",
            filetypes=[("ZIP files", "*.zip")]
        )
        if zip_path:
            messagebox.showinfo("Info", "Video extraction logic would go here.")
            log_message(f"User selected video ZIP file: {zip_path}")

    def update_color_preview(new_color):
        color_preview.config(bg=new_color if is_hex_color(new_color) else '')

    def update_password_checkbox_state():
        show_password_checkbox.config(state='normal' if timer_entry.get() else 'disabled')
        if not timer_entry.get():
            show_password_var.set(False)

    def save_settings():
        password = password_entry.get() or DEFAULT_PASSWORD
        log_level = log_level_var.get()
        timer = timer_entry.get()
        timer_position = timer_position_var.get()
        theme = theme_var.get()
        mode = mode_var.get()
        bg_color = bg_color_var.get()
        show_popup_bg = show_popup_bg_var.get()
        screensaver_image_path = screensaver_image_path_var.get()
        popup_text_file = popup_text_file_var.get()
        popup_interval = popup_interval_var.get()
        popup_duration = popup_duration_var.get()
        popup_video_size = popup_video_size_var.get()
        show_skip_button = show_skip_button_var.get()
        show_password = show_password_var.get()

        # Input validation
        if timer and not timer.isdigit():
            messagebox.showerror("Validation Error", "Timer must be a positive integer.")
            return
        if not is_hex_color(bg_color):
            messagebox.showerror("Validation Error", "Invalid background color format. Use #RRGGBB or #RGB.")
            return
        try:
            float(popup_interval)
            float(popup_duration)
            video_size = int(popup_video_size)
            if not 1 <= video_size <= 10:
                raise ValueError
        except ValueError:
            messagebox.showerror("Validation Error", "Invalid numeric input for pop-up settings.")
            return

        if not timer and show_password:
            messagebox.showerror("Validation Error", "You must set a timer to enable showing the password.")
            return

        config_data = {
            "password": password, "log_level": log_level, "timer": timer,
            "timer_position": timer_position, "theme": theme, "mode": mode,
            "bg_color": bg_color, "screensaver_image_path": screensaver_image_path,
            "popup_text_file": popup_text_file, "popup_interval": popup_interval,
            "popup_duration": popup_duration, "popup_video_size": popup_video_size,
            "show_skip_button": show_skip_button, "show_password": show_password,
            "show_popup_bg": show_popup_bg
        }
        save_config(config_data)
        messagebox.showinfo("Success", "Settings saved successfully.")

    def validate_before_start():
        if not timer_entry.get() and show_password_var.get():
            messagebox.showerror("Validation Error", "You cannot show the password without setting a timer.")
            return False
        return True

    def start_program():
        if validate_before_start():
            save_settings()
            start_main_script()
            window.quit()

    # --- Helper function for placing images ---
    def place_image(tab, image_data, row, column, columnspan=1, rowspan=1, sticky="nsew"):
        if image_data:
            label = ttk.Label(tab)
            if isinstance(image_data, list):
                play_gif(label, image_data)
            else:
                label.config(image=image_data)
                label.image = image_data
            label.grid(row=row, column=column, columnspan=columnspan, rowspan=rowspan, sticky=sticky, padx=5, pady=5)
            return label
        return None

    # --- General Tab ---
    general_tab = ttk.Frame(tab_control)
    tab_control.add(general_tab, text="General")

    place_image(general_tab, get_image(images, "Page1TopLeft"), row=0, column=0, sticky="nw")

    ttk.Label(general_tab, text="New Password:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
    password_entry = ttk.Entry(general_tab, show="*")
    password_entry.insert(0, config.get("password", DEFAULT_PASSWORD))
    password_entry.grid(row=2, column=0, sticky="ew", padx=5, pady=5)

    ttk.Label(general_tab, text="Log Level:").grid(row=3, column=0, sticky="w", padx=5, pady=5)
    log_level_var = tk.StringVar(value=config.get("log_level", "INFO"))
    log_levels = ["INFO", "DEBUG", "WARNING", "ERROR"]
    for i, level in enumerate(log_levels):
        ttk.Radiobutton(general_tab, text=level, variable=log_level_var, value=level).grid(row=4 + i, column=0, sticky="w", padx=15)

    show_skip_button_var = tk.BooleanVar(value=config.get("show_skip_button", "True") == "True")
    show_skip_button_checkbox = ttk.Checkbutton(general_tab, text="Show Skip Button", variable=show_skip_button_var)
    show_skip_button_checkbox.grid(row=4 + len(log_levels), column=0, sticky="w", padx=5, pady=5)

    show_password_var = tk.BooleanVar(value=config.get("show_password", "True") == "True")
    show_password_checkbox = ttk.Checkbutton(general_tab, text="Show Password", variable=show_password_var)
    show_password_checkbox.grid(row=5 + len(log_levels), column=0, sticky="w", padx=5, pady=5)

    general_tab.grid_columnconfigure(0, weight=1)

    # --- Timer Tab ---
    timer_tab = ttk.Frame(tab_control)
    tab_control.add(timer_tab, text="Timer")

    place_image(timer_tab, get_image(images, "TimerTabImage"), row=0, column=1, sticky="ne")

    ttk.Label(timer_tab, text="Countdown Timer (seconds):").grid(row=0, column=0, sticky="w", padx=5, pady=5)
    timer_entry = ttk.Entry(timer_tab)
    timer_entry.insert(0, config.get("timer", ""))
    timer_entry.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
    timer_entry.bind("<KeyRelease>", lambda event: update_password_checkbox_state())

    ttk.Label(timer_tab, text="Timer Position:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
    timer_position_var = tk.StringVar(value=config.get("timer_position", "top_right"))
    timer_positions = ["top_left", "top_right", "bottom_left", "bottom_right"]
    for i, position in enumerate(timer_positions):
        ttk.Radiobutton(timer_tab, text=position.replace("_", " ").capitalize(), variable=timer_position_var, value=position).grid(row=3 + i, column=0, sticky="w", padx=15)

    timer_tab.grid_columnconfigure(0, weight=1)
    timer_tab.grid_columnconfigure(1, weight=0)

    # --- Appearance Tab ---
    appearance_tab = ttk.Frame(tab_control)
    tab_control.add(appearance_tab, text="Appearance")

    place_image(appearance_tab, get_image(images, "AppearanceTopRight"), row=0, column=1, sticky="ne")

    ttk.Label(appearance_tab, text="Theme:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
    theme_var = tk.StringVar(value=config.get("theme", "Light"))
    themes = ["Light", "Dark"]
    for i, theme in enumerate(themes):
        ttk.Radiobutton(appearance_tab, text=theme, variable=theme_var, value=theme).grid(row=1 + i, column=0, sticky="w", padx=15)

    ttk.Label(appearance_tab, text="Background Color:").grid(row=3, column=0, sticky="w", padx=5, pady=5)
    bg_color_var = tk.StringVar(value=config.get("bg_color", "#000000"))
    bg_color_var.trace_add("write", lambda name, index, mode, sv=bg_color_var: update_color_preview(sv.get()))
    bg_color_entry = ttk.Entry(appearance_tab, textvariable=bg_color_var)
    bg_color_entry.grid(row=4, column=0, sticky="ew", padx=5, pady=5)
    color_preview = tk.Canvas(appearance_tab, width=20, height=20, bg=config.get("bg_color", "#000000"))
    color_preview.grid(row=4, column=1, sticky="w", padx=5, pady=5)

    appearance_tab.grid_columnconfigure(0, weight=1)
    appearance_tab.grid_columnconfigure(1, weight=0)

    # --- Mode Tab ---
    mode_tab = ttk.Frame(tab_control)
    tab_control.add(mode_tab, text="Mode")

    place_image(mode_tab, get_image(images, "ModeBottomLeft"), row=1, column=0, sticky="sw")

    ttk.Label(mode_tab, text="Select Mode:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
    mode_var = tk.StringVar(value=config.get("mode", "fullscreen"))
    modes = [("Fullscreen (single video)", "fullscreen"), ("Pop-Up Mode (floating videos)", "windowed")]
    for i, (mode_text, mode_value) in enumerate(modes):
        ttk.Radiobutton(mode_tab, text=mode_text, variable=mode_var, value=mode_value).grid(row=1 + i, column=1, sticky="nw", padx=15)

    ttk.Label(mode_tab, text="Pop-Up Video Size (1-10):").grid(row=3, column=0, sticky="w", padx=5, pady=5)
    popup_video_size_var = tk.StringVar(value=config.get("popup_video_size", "5"))
    popup_video_size_slider = tk.Scale(mode_tab, from_=1, to=10, orient=tk.HORIZONTAL, variable=popup_video_size_var)
    popup_video_size_slider.grid(row=3, column=1, sticky="ew", padx=5, pady=5)

    show_popup_bg_var = tk.BooleanVar(value=config.get("show_popup_bg", "True") == "True")
    show_popup_bg_checkbox = ttk.Checkbutton(mode_tab, text="Use Pop-Up Background", variable=show_popup_bg_var)
    show_popup_bg_checkbox.grid(row=4, column=1, sticky="w", padx=15)

    mode_tab.grid_columnconfigure(0, weight=1)
    mode_tab.grid_columnconfigure(1, weight=1)

    # --- Screen Saver Tab ---
    screensaver_tab = ttk.Frame(tab_control)
    tab_control.add(screensaver_tab, text="Screen Saver")

    place_image(screensaver_tab, get_image(images, "ScreenSaverTopLeft"), row=0, column=0, sticky="nw")

    ttk.Label(screensaver_tab, text="Pause Video with 'F1' Key").grid(row=1, column=0, sticky="w", padx=5, pady=5)

    ttk.Label(screensaver_tab, text="Select Screen Saver Image:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
    screensaver_image_path_var = tk.StringVar(value=config.get("screensaver_image_path", ""))
    ttk.Entry(screensaver_tab, textvariable=screensaver_image_path_var, state="readonly").grid(row=3, column=0, sticky="ew", padx=5, pady=5)
    ttk.Button(screensaver_tab, text="Browse", command=lambda: browse_file("Select an image", [("Image files", "*.jpg;*.jpeg;*.png;*.bmp")], screensaver_image_path_var)).grid(row=3, column=1, sticky="w", padx=5, pady=5)

    screensaver_tab.grid_columnconfigure(0, weight=1)
    screensaver_tab.grid_columnconfigure(1, weight=0)

    # --- Pop-Up Tab ---
    popup_tab = ttk.Frame(tab_control)
    tab_control.add(popup_tab, text="Pop-Up")

    place_image(popup_tab, get_image(images, "PopupBottomRight"), row=1, column=1, sticky="se")

    ttk.Label(popup_tab, text="Upload Text File for Pop-Ups:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
    popup_text_file_var = tk.StringVar(value=config.get("popup_text_file", ""))
    ttk.Entry(popup_tab, textvariable=popup_text_file_var, state="readonly").grid(row=1, column=0, sticky="ew", padx=5, pady=5)
    ttk.Button(popup_tab, text="Browse", command=lambda: browse_file("Select a text file", [("Text files", "*.txt")], popup_text_file_var)).grid(row=1, column=1, sticky="w", padx=5, pady=5)

    ttk.Label(popup_tab, text="Pop-Up Interval (seconds):").grid(row=2, column=0, sticky="w", padx=5, pady=5)
    popup_interval_var = tk.StringVar(value=config.get("popup_interval", "0.5"))
    ttk.Entry(popup_tab, textvariable=popup_interval_var).grid(row=3, column=0, sticky="ew", padx=5, pady=5)

    ttk.Label(popup_tab, text="Pop-Up Duration (seconds):").grid(row=4, column=0, sticky="w", padx=5, pady=5)
    popup_duration_var = tk.StringVar(value=config.get("popup_duration", "5"))
    ttk.Entry(popup_tab, textvariable=popup_duration_var).grid(row=5, column=0, sticky="ew", padx=5, pady=5)

    popup_tab.grid_columnconfigure(0, weight=1)
    popup_tab.grid_columnconfigure(1, weight=0)

    # --- Video Import Tab ---
    video_import_tab = ttk.Frame(tab_control)
    tab_control.add(video_import_tab, text="Video Import")

    place_image(video_import_tab, get_image(images, "VideoImportTopRight"), row=0, column=1, sticky="ne")

    ttk.Button(video_import_tab, text="Browse ZIP", command=browse_videos).grid(row=0, column=0, sticky="ew", padx=5, pady=5)

    video_import_tab.grid_columnconfigure(0, weight=1)
    video_import_tab.grid_columnconfigure(1, weight=0)

    tab_control.pack(expand=1, fill="both")

    button_frame = ttk.Frame(window)
    button_frame.pack(pady=10)
    ttk.Button(button_frame, text="Save Settings", command=save_settings).pack(side="left", padx=10)
    ttk.Button(button_frame, text="Start Program", command=start_program).pack(side="left", padx=10)

    update_password_checkbox_state()
    window.mainloop()

if __name__ == "__main__":
    main()