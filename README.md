Resume Screener
A powerful tool that analyzes resumes against job descriptions and provides results in Excel format.

Features
Supports 11 job descriptions (DESE/NIMT roles)
Processes multiple resume formats (PDF, DOCX, TXT)
Outputs analysis results as Excel files
Simple Streamlit user interface
Shareable Python project

Prerequisites
Windows/Mac/Linux
Python 3.8 or newer
VS Code (recommended for development)
Internet connection for API access

Setup
1. Get the Code
Clone or download the project to your computer:
C:\Resume_Screener

2. Environment Setup
Open a command prompt or PowerShell and navigate to the project directory:
powershell# Create a virtual environment
python -m venv venv

# Activate the virtual environment
.\venv\Scripts\activate

# Install required packages
pip install -r requirements.txt

3. Run the Application
With the virtual environment activated, start the Streamlit application:
powershellstreamlit run src/main.py

4. Access the UI
After running the command, your web browser should automatically open the application. If not, navigate to the URL shown in the terminal (typically http://localhost:8501).
System Requirements


