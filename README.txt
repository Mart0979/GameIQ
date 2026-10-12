GAMEIQ v0.1 - WINDOWS SETUP

1. Install Python 3.12 or 3.13 from https://www.python.org/downloads/windows/
   During installation, enable "Add python.exe to PATH" if offered.
2. Unzip this folder somewhere convenient (e.g. Desktop).
3. Open Command Prompt (Windows key, type cmd).
4. Change directory to this folder using cd /d "C:\path\to\gameiq_v01"
   TIP: In File Explorer, open the folder, click the address bar, type cmd, press Enter.
5. Run: py -m pip install -r requirements.txt
6. Double-click start_gameiq.bat (or run: py -m streamlit run app.py).
7. Open http://localhost:8501 if your browser does not open automatically.

Play tags are saved to plays.json in this folder. Video uploads are used only
in the running session; they are not saved as video files by the app.
The prototype does NOT automatically recognize players or plays in video.
It generates transparent, rule-based findings from manually tagged observations.
For rights and privacy, only use video you have permission to analyze.
