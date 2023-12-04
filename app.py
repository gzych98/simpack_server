from flask import Flask, jsonify, request, render_template
import os
import zipfile

app = Flask(__name__)
UPLOAD_FOLDER = 'UPLOAD'
ALLOWED_EXTENSIONS = {'zip'}
EXTENSION_LIST = 'txt'

file_with_labels = []

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['EXTENSION_LIST'] = EXTENSION_LIST

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/upload_files', methods=['GET', 'POST'])
def upload_file():
    messages = []
    if request.method == 'POST':
        files = request.files.getlist('file')
        user_ip = request.remote_addr  # Pobieranie adresu IP użytkownika

        if not files:
            messages.append('Nie wybrano żadnych plików.')
        else:
            for file in files:
                if file and allowed_file(file.filename):
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
                    file.save(filepath)
                    with zipfile.ZipFile(filepath) as zip_ref:
                        zip_ref.extractall(app.config['UPLOAD_FOLDER'])
                    messages.append(f"File uploaded: {file.filename}")
                else:
                    messages.append(f"Extension error: {file.filename}. Only .zip files accepted.<br>")
    label_items()
    return render_template('upload.html', messages=messages)

@app.route('/debug')
def debug():
    label_items()
    return jsonify({"success": True, "debug": file_with_labels})

def label_items():
    global file_with_labels

    # Usuwanie z listy elementów, które nie są słownikami
    file_with_labels = [f for f in file_with_labels if isinstance(f, dict) and 'filename' in f]

    # Utworzenie zbioru z istniejących nazw plików
    existing_files = set(f['filename'] for f in file_with_labels)

    # Wyszukiwanie nowych plików, które jeszcze nie znajdują się w file_with_labels
    new_files = [f for f in os.listdir(app.config['UPLOAD_FOLDER']) if f.endswith(app.config['EXTENSION_LIST']) and f not in existing_files]

    for file in new_files:
        # Przypisywanie etykiet: '1' dla pierwszego pliku, '2' dla pozostałych
        label = '1' if not existing_files else '2'
        file_with_labels.append({'filename': file, 'label': label})

    print(f'-- Aktualny stan: {file_with_labels}')



@app.route('/filelist')
def filelist():
    label_items()
    return render_template('filelist.html', files=file_with_labels)


@app.route('/update_order', methods=['GET', 'POST'])
def update_order():
    global file_with_labels
    new_order = request.json
    file_with_labels = new_order
    print(f"-- Current file order: {' | '.join(map(str, file_with_labels))}")
    return jsonify({"success": True, "new_order": file_with_labels})

@app.route('/get_current_order', methods=['GET'])
def get_current_order():
    global file_with_labels
    return jsonify({"current_order": file_with_labels})

if __name__ == '__main__':
    app.run(debug=True)
