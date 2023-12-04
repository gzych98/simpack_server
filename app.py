from flask import Flask, jsonify, request, render_template
import os
import zipfile

app = Flask(__name__)
UPLOAD_FOLDER = 'UPLOAD'
ALLOWED_EXTENSIONS = {'zip'}
EXTENSION_LIST = 'txt'

current_order = []
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
                    # Rozpakuj pliki
                    with zipfile.ZipFile(filepath) as zip_ref:
                        zip_ref.extractall(app.config['UPLOAD_FOLDER'])
                    messages.append(f"File uploaded: {file.filename}")
                    #current_order.append({'filename': file.filename, 'user_ip': user_ip})
                else:
                    messages.append(f"Extension error: {file.filename}. Only .zip files accepted.<br>")
    print(current_order)
    label_items()
    return render_template('upload.html', messages=messages)

def label_items():
    global file_with_labels
    if not file_with_labels:
        files = [f for f in os.listdir(app.config['UPLOAD_FOLDER']) if f.endswith(app.config['EXTENSION_LIST'])]
        for file in files:
            label = '1' if not file_with_labels else '2'
            file_with_labels.append({'filename': file, 'label': label})
        return print(file_with_labels)
    else:
        update_label()
    return print(file_with_labels)

def update_label():
    global file_with_labels
    print(file_with_labels)
    for index, file_dict in enumerate(file_with_labels):
        if index == 0:
            file_dict['label'] = '1'  # Przypisz etykietę '1' pierwszemu elementowi
        else:
            file_dict['label'] = '2'  # Przypisz etykietę '2' wszystkim pozostałym elementom

@app.route('/filelist')
def filelist():
    label_items()
    return render_template('filelist.html', files=file_with_labels)

# WERSJA Z IP UŻYTKOWNIKA
# @app.route('/filelist')
# def filelist():
#     # Tu zakładamy, że `current_order` przechowuje listę słowników z 'filename' i 'user_ip'
#     global current_order
#     return render_template('filelist.html', files=current_order)


@app.route('/update_order', methods=['GET', 'POST'])
def update_order():
    global current_order
    new_order = request.json
    current_order = new_order
    print(f"-- Current file order: {' | '.join(map(str, current_order))}")
    return jsonify({"success": True, "new_order": current_order})

@app.route('/get_current_order', methods=['GET'])
def get_current_order():
    global current_order
    return jsonify({"current_order": current_order})

if __name__ == '__main__':
    app.run(debug=True)
