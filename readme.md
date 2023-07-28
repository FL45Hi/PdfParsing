Assignment :: PDF Parsing using Python OCR .
This is the user documentation for the PDF Parsing.

 
## Introduction
PDF Parsing Assignment code is written in Python.
Objective: Extract the texts and images from pdf through OCR and store it in Postgres database.


## Pre-requisites
*   Python 3.9
*   Postgres 15.1 database 
*   Tesseract OCR for windows

## Configuration
The following commands you have to run in your command prompt in order to set up the python virtual environment with appropriate dependancy.
1. pip install virtualenvwrapper-win
2. mkvirtualenv pdfparsing
4. pip install pytesseract
3. pip install Pillow
5. pip install pdf2image

### Install the tesseract-ocr in your windows machine. 
You can Download tesseract exe file from https://github.com/UB-Mannheim/tesseract/wiki .
then set the variable pytesseract.pytesseract.tesseract_cmd = r'C:\Users\<username>\AppData\Local\Programs\Tesseract-OCR\tesseract' in the starting main.py file.
 
### Download the poppler release. 
You can download the release from https://github.com/oschwartz10612/poppler-windows/releases .
Extract the popple zip in project folder and set the poppler path. 
for example, poppler_path=r"poppler-23.07.0\Library\bin"
 

# Steps to Execute the code
1.  Update File_name variable in main.py with pdf name.
1.  To activate an environment run "workon pdfparsing" in command terminal
2.  run "python main.py".

 