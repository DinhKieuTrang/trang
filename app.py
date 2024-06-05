from flask import Flask, render_template, request
from werkzeug.utils import secure_filename
import docx
import PyPDF2
from difflib import SequenceMatcher
import requests
from bs4 import BeautifulSoup
import difflib
import matplotlib.pyplot as plt
import os
import io
import base64
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import string

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


# Hàm loại bỏ stopwords và dấu câu
def preprocess_text(text):
    stop_words = set(stopwords.words('vietnamese'))
    tokens = word_tokenize(text.lower())
    tokens = [word for word in tokens if word.isalnum() and word not in stop_words]
    return set(tokens)

# Hàm tính toán độ tương đồng giữa hai đoạn văn bản
def compare_text(text1, text2):
    words1 = preprocess_text(text1)
    words2 = preprocess_text(text2)
    intersection = len(words1.intersection(words2))
    union = len(words1.union(words2))
    similarity_ratio = intersection / union if union != 0 else 0
    similarity_percentage = int(similarity_ratio * 100)
    return similarity_percentage


def check_plagiarism(text1, text2):
    seq = difflib.SequenceMatcher(None, text1, text2)
    return seq.ratio()

def create_plagiarism_chart(similarity):
    labels = ['Plagiarized', 'Not Plagiarized']
    sizes = [similarity * 100, (1 - similarity) * 100]
    colors = ['#ff6666', '#66b3ff']
    explode = (0.1, 0)  # explode 1st slice

    fig, ax = plt.subplots()
    ax.pie(sizes, explode=explode, labels=labels, colors=colors,
           autopct='%1.1f%%', shadow=True, startangle=140)
    ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.

    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    chart_url = base64.b64encode(img.getvalue()).decode()
    plt.close(fig)
    return 'data:image/png;base64,{}'.format(chart_url)

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
    chart_url = None
    sources = []

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
            chart_url = create_plagiarism_chart(similarity_percentage / 100)
            sources = find_sources(text1, text2)

    return render_template('daovan.html', text1=text1, text2=text2,
                           similarity_percentage=similarity_percentage, chart_url=chart_url, sources=sources)

def find_sources(text1, text2):
    api_key = 'AIzaSyDCyPLcLiMSas18yd--UYrQk2uvABinFJY'  # Thay thế bằng API Key của bạn
    search_engine_id = 'b664f8aebfede4584'  # Thay thế bằng Search Engine ID của bạn
    
    query1 = text1[:100]  # Sử dụng một phần của văn bản để tìm kiếm
    query2 = text2[:100]  # Sử dụng một phần của văn bản để tìm kiếm
    
    def search_google(query):
        url = f'https://www.googleapis.com/customsearch/v1?q={query}&key={api_key}&cx={search_engine_id}'
        response = requests.get(url)
        results = response.json().get('items', [])
        return [result['link'] for result in results]
    
    sources1 = search_google(query1)
    sources2 = search_google(query2)
    
    # Hợp nhất và loại bỏ các liên kết trùng lặp
    sources = list(set(sources1 + sources2))
    
    return sources

    # Hàm này sẽ thực hiện tìm kiếm các nguồn tương đồng trên Internet
    # Bạn cần implement hàm này để trả về danh sách các nguồn


if __name__ == '__main__':
    app.run(debug=True)