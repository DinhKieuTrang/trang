from flask import Flask, render_template, request
from werkzeug.utils import secure_filename
import os
import docx
import PyPDF2
from difflib import SequenceMatcher
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def read_docx(file_path):
    doc = docx.Document(file_path)
    text = ''
    for paragraph in doc.paragraphs:
        text += paragraph.text + '\n'
    return text

def read_pdf(file_path):
    text = ''
    with open(file_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        for page_num in range(len(reader.pages)):
            page = reader.pages[page_num]
            text += page.extract_text()
    return text

def read_code(file_path):
    with open(file_path, 'r') as file:
        return file.read()

def fetch_text_from_url(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            paragraphs = soup.find_all('p')
            text = ' '.join([para.get_text() for para in paragraphs])
            return text
        else:
            return ""
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return ""

def compare_text(text1, text2):
    d = SequenceMatcher(None, text1, text2)
    similarity_ratio = d.ratio()
    similarity_percentage = int(similarity_ratio * 100)
    return similarity_percentage

@app.route('/', methods=['GET', 'POST'])
def daovan():
    text1 = ""
    text2 = ""
    similarity_percentage = None

    if request.method == 'POST':
        text1_input = request.form.get('text1')
        file1 = request.files.get('file1')
        url1 = request.form.get('url1')
        
        text2_input = request.form.get('text2')
        file2 = request.files.get('file2')
        url2 = request.form.get('url2')

        if text1_input:
            text1 = text1_input

        if file1 and file1.filename:
            filename1 = secure_filename(file1.filename)
            file_path1 = os.path.join(app.config['UPLOAD_FOLDER'], filename1)
            file1.save(file_path1)
            if filename1.endswith('.docx'):
                text1 = read_docx(file_path1)
            elif filename1.endswith('.pdf'):
                text1 = read_pdf(file_path1)
            elif filename1.endswith(('.py', '.java', '.cpp', '.c', '.js', '.html', '.css', '.txt')):
                text1 = read_code(file_path1)
            else:
                with open(file_path1, 'r') as f:
                    text1 = f.read()

        if not text1 and url1:
            text1 = fetch_text_from_url(url1)

        if text2_input:
            text2 = text2_input

        if file2 and file2.filename:
            filename2 = secure_filename(file2.filename)
            file_path2 = os.path.join(app.config['UPLOAD_FOLDER'], filename2)
            file2.save(file_path2)
            if filename2.endswith('.docx'):
                text2 = read_docx(file_path2)
            elif filename2.endswith('.pdf'):
                text2 = read_pdf(file_path2)
            elif filename2.endswith(('.py', '.java', '.cpp', '.c', '.js', '.html', '.css', '.txt')):
                text2 = read_code(file_path2)
            else:
                with open(file_path2, 'r') as f:
                    text2 = f.read()

        if not text2 and url2:
            text2 = fetch_text_from_url(url2)

        if text1 and text2:
            similarity_percentage = compare_text(text1, text2)

    return render_template('daovan.html', text1=text1, text2=text2,
                          similarity_percentage=similarity_percentage)

if __name__ == '__main__':
    app.run(debug=True)
