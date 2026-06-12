# Thumbnail Doctor Pro Ultimate

Complete production-ready desktop application combining AI thumbnail design coaching with Python code analysis.

## Features

### 1. AI Thumbnail Design Coach
- Color analysis and harmony detection
- Font readability assessment
- Composition analysis (Rule of Thirds, balance, negative space)
- Subject/focal point detection
- CTR estimation
- Photoshop-specific fix recommendations

### 2. AI Photoshop Coach
- Screen capture integration
- Real-time workspace analysis
- Step-by-step improvement suggestions

### 3. Python Project Doctor
- AST-based code analysis
- Ruff linting integration
- Pylint analysis
- Bandit security scanning
- Radon complexity metrics
- AI-powered code review

### 4. Code Review & Security Audit
- Unused imports/variables detection
- Large function/class warnings
- Cyclomatic complexity analysis
- Security vulnerability detection
- Architecture recommendations

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python main.py
```

## Keyboard Shortcuts

- `Ctrl+Shift+A` - Capture screen for thumbnail analysis
- `Ctrl+O` - Open project folder
- `Ctrl+S` - Save report
- `Ctrl+Q` - Quit application

## Project Structure

```
thumbnail_doctor_pro/
├── main.py                 # Application entry point
├── core/                   # Core functionality
│   ├── database.py         # SQLite database manager
│   └── settings_manager.py # Settings with encryption
├── engines/                # Analysis engines
│   ├── screen_capture.py   # MSS/OpenCV screen capture
│   ├── thumbnail_analyzer.py # Thumbnail CV analysis
│   └── python_doctor.py    # Python code analysis
├── models/                 # AI models
│   └── gemini_manager.py   # Google Gemini integration
├── ui/                     # PySide6 UI components
│   ├── main_window.py      # Main application window
│   └── pages/              # Page widgets
├── reports/                # Report generation
│   └── report_generator.py # PDF/HTML/JSON export
└── utils/                  # Utilities
    └── logger.py           # Logging system
```

## Requirements

- Python 3.12+
- PySide6
- Google Gemini API key (for AI features)
- OpenCV, Pillow, MSS (for image processing)
- Ruff, Pylint, Bandit, Radon (for code analysis)

## License

Proprietary - All rights reserved
