C:\Users\Administrator\Documents\CoachAiThumbnail\YoutubeCutter-main\thumbnail_doctor_pro>python main.py
C:\Users\Administrator\Documents\CoachAiThumbnail\YoutubeCutter-main\thumbnail_doctor_pro\main.py:16: DeprecationWarning: Enum value 'Qt::ApplicationAttribute.AA_EnableHighDpiScaling' is marked as deprecated, please check the documentation for more information.
  QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
C:\Users\Administrator\Documents\CoachAiThumbnail\YoutubeCutter-main\thumbnail_doctor_pro\main.py:18: DeprecationWarning: Enum value 'Qt::ApplicationAttribute.AA_UseHighDpiPixmaps' is marked as deprecated, please check the documentation for more information.
  QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
C:\Users\Administrator\Documents\CoachAiThumbnail\YoutubeCutter-main\thumbnail_doctor_pro\models\gemini_manager.py:5: FutureWarning:

All support for the `google.generativeai` package has ended. It will no longer be receiving
updates or bug fixes. Please switch to the `google.genai` package as soon as possible.
See README for more details:

https://github.com/google-gemini/deprecated-generative-ai-python/blob/main/README.md

  import google.generativeai as genai
Traceback (most recent call last):
  File "C:\Users\Administrator\Documents\CoachAiThumbnail\YoutubeCutter-main\thumbnail_doctor_pro\main.py", line 39, in <module>
    main()
    ~~~~^^
  File "C:\Users\Administrator\Documents\CoachAiThumbnail\YoutubeCutter-main\thumbnail_doctor_pro\main.py", line 33, in main
    window = MainWindow(db_manager, settings_manager)
  File "C:\Users\Administrator\Documents\CoachAiThumbnail\YoutubeCutter-main\thumbnail_doctor_pro\ui\main_window.py", line 360, in __init__
    self._setup_ui()
    ~~~~~~~~~~~~~~^^
  File "C:\Users\Administrator\Documents\CoachAiThumbnail\YoutubeCutter-main\thumbnail_doctor_pro\ui\main_window.py", line 395, in _setup_ui
    self._setup_content_pages()
    ~~~~~~~~~~~~~~~~~~~~~~~~~^^
  File "C:\Users\Administrator\Documents\CoachAiThumbnail\YoutubeCutter-main\thumbnail_doctor_pro\ui\main_window.py", line 409, in _setup_content_pages
    from ui.pages import (
    ...<3 lines>...
    )
  File "C:\Users\Administrator\Documents\CoachAiThumbnail\YoutubeCutter-main\thumbnail_doctor_pro\ui\pages\__init__.py", line 22, in <module>
    from engines.screen_capture import ScreenCaptureEngine, CaptureRegion
  File "C:\Users\Administrator\Documents\CoachAiThumbnail\YoutubeCutter-main\thumbnail_doctor_pro\engines\__init__.py", line 5, in <module>
    from .thumbnail_analyzer import ThumbnailAnalysisEngine
  File "C:\Users\Administrator\Documents\CoachAiThumbnail\YoutubeCutter-main\thumbnail_doctor_pro\engines\thumbnail_analyzer.py", line 12, in <module>
    from models.gemini_manager import GeminiManager
ImportError: cannot import name 'GeminiManager' from 'models.gemini_manager' (C:\Users\Administrator\Documents\CoachAiThumbnail\YoutubeCutter-main\thumbnail_doctor_pro\models\gemini_manager.py). Did you mean: 'gemini_manager'?

C:\Users\Administrator\Documents\CoachAiThumbnail\YoutubeCutter-main\thumbnail_doctor_pro>





























