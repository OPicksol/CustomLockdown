# Customizable Lockdown Videoplayer

## Features

Password Protection: Requires a password to exit the video playback, ensuring only authorized users can regain control.

Countdown Timer: Optionally set a timer after which the application will automatically exit.

Customizable Appearance:
- Themes: Choose between light and dark themes.
- Background Color: Set a custom background color for windowed mode.
- Multiple Playback Modes:
  - Fullscreen: Immersive, uninterrupted video playback.
  - Pop-Up Mode: Displays floating videos for a dynamic visual experience.
- Screen Saver Integration: Pause video playback with the F1 key and display a custom image. Press F1 again to resume.
- Dynamic Pop-Up Messages: Display timed text pop-ups from a text file in windowed mode.
- Adjustable Playback: Control video speed and volume.
- Skip Button (Optional): Allow users to skip to the next video.
- Show Password Option: Optionally display the password on the screen when the timer is active.
- Configurable Pop-Up Settings: Adjust the interval, duration, and size of pop-up videos.
- Log File: Keeps a record of the application's activity for troubleshooting.

## Getting Started
These instructions will guide you through setting up and running the Secure Video Player on a Windows machine.

## Prerequisites
- Internet Connection: Required for the bootstrapper to download Python and necessary dependencies.
- Administrator Privileges: Running the Bootstrapper.bat as an administrator is recommended to install Python system-wide.

## Instructions
Run the Bootstrapper:
- Locate the Bootstrapper.bat file in File Explorer.
- Right-click on Bootstrapper.bat and select "Run as administrator".

## Configuration
Configure the Application: The configurator.py application will open automatically after the bootstrapper finishes. Here you can customize the Secure Video Player's settings:

- General Tab:
  - New Password: Set the password required to exit the player.
  - Log Level: Control the verbosity of the log file.
  - Show Skip Button: Enable or disable the "Skip Video" button.
  - Show Password: Display the password on screen when the timer is active.

- Timer Tab:
  - Countdown Timer (seconds): Set a timer in seconds after which the application will exit. Leave blank to disable the timer.
  - Timer Position: Choose where the timer is displayed on the screen.

- Appearance Tab:
  - Theme: Select between "Light" and "Dark" themes.
  - Background Color: Set the background color for windowed mode (using hex codes like #000000 for black).

- Mode Tab:
  - Select Mode: Choose between "Fullscreen" (plays one video at a time) and "Pop-Up Mode" (displays floating videos).
  - Pop-Up Video Size (1-10): Adjust the size of the pop-up videos in windowed mode.
  - Use Pop-Up Background: Toggle the background for pop-up windows.

- Screen Saver Tab:
  - Pause Video with 'F1' Key: Information about using the F1 key.
  - Select Screen Saver Image: Choose an image to display when the screen saver is active.

- Pop-Up Tab:
  - Upload Text File for Pop-Ups: Select a .txt file where each line is a pop-up message (only for windowed mode).
  - Pop-Up Interval (seconds): Set how often text pop-ups appear.
  - Pop-Up Duration (seconds): Set how long text pop-ups are displayed.

- Video Import Tab:
  - Browse ZIP: (Placeholder for future functionality) Allows browsing and selecting a ZIP file containing videos.

- Save Settings: Click the "Save Settings" button to apply your configurations.
- Start Program: Click the "Start Program" button to launch the Secure Video Player with your configured settings.

## Contributing
Contributions are welcome! If you'd like to contribute to the development of the Secure Video Player, please follow these steps:
- Fork the repository on GitHub.
- Create a new branch for your feature or bug fix.
- Make your changes and commit them with clear, concise messages.
- Test your changes thoroughly.
- Submit a pull request to the main branch of the original repository.

## License
This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments
Thanks to the developers of the Python libraries used in this project: tkinter, Pillow, python-vlc, pynput, pywin32, and pyautogui.

## Contact
For questions or feedback, please feel free to open an issue on the GitHub repository
