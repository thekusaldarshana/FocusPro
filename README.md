# Remeinium FocusPro

![Remeinium FocusPro Logo](focuspro.ico) 

A productivity-focused desktop application for managing focus sessions with analytics.

## Features

- 🕒 Customizable focus timer (1-240 minutes)
- 📊 Session analytics and progress tracking
- 🎯 Daily goals and streak monitoring
- 📈 Interactive data visualization
- 🔔 Custom notification sounds
- 🎨 Dark mode UI with modern design

## Installation

### For Users

1. Download the latest `Remeinium FocusPro.exe` from Releases
2. Double-click to run (no installation required)
3. For best experience, create a desktop shortcut

### For Developers

#### Prerequisites
- Python 3.9+
- pip

#### Setup
```bash
git clone https://github.com/thekusaldarshana/FocusPro.git
cd Remeinium-FocusPro
pip install -r requirements.txt
```

#### Running
```bash
python FocusPro.py
```

#### Building Executable
```bash
pyinstaller --onefile --windowed --icon=focuspro.ico --add-data "focuspro.wav;." --add-data "templates/graph.html;templates" --add-data "focuspro.ico;." FocusPro.py --name "Remeinium FocusPro"
```

## Usage

1. Select task category (Maths/Physics/ICT/General)
2. Set duration using slider or input
3. Click Start to begin focus session
4. View analytics through the Analytics button

## Keyboard Shortcuts

- `Space`: Start/Pause session
- `R`: Reset timer
- `S`: Stop session

## Developer Documentation

### Project Structure
```
Remeinium-FocusPro/
├── templates/
│   └── graph.html          # Analytics template
├── FocusPro.py             # Main application
├── focuspro.ico            # Application icon
├── focuspro.wav            # Notification sound
└── requirements.txt        # Dependencies
```

### Key Components
- **CustomTkinter**: Modern UI framework
- **SQLite**: Local data storage
- **Pygame**: Audio handling
- **Plyer**: System notifications

### Data Schema
Sessions are stored in `focus_sessions.db` with schema:
```sql
CREATE TABLE sessions (
    id INTEGER PRIMARY KEY,
    date TEXT NOT NULL,
    task_category TEXT NOT NULL,
    duration INTEGER NOT NULL,
    completed INTEGER NOT NULL,
    start_time TEXT NOT NULL,
    end_time TEXT
);
```

### Extending the Project

#### Adding New Features
1. Create a new branch
2. Implement changes
3. Update version in `FocusPro.py`
4. Submit pull request

#### Debugging Tips
- Check `debug.log` for runtime errors
- Enable console output during development:
  ```python
  if __name__ == "__main__":
      import sys
      app = FocusSessionApp()
      sys.exit(app.run())
  ```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Missing sound file | Ensure `focuspro.wav` is in same directory as EXE |
| Analytics not loading | Check `templates/graph.html` exists |
| Database errors | Delete `focus_sessions.db` to reset |

## License
MIT License - See [LICENSE](LICENSE) file

---

**Created with ❤️ by Remeinium Corp.**  
[Report Issues](https://github.com/thekusaldarshana/FocusPro/issues)

