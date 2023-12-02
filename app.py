from flask import Flask, jsonify, request, render_template
import os
import zipfile

app = Flask(__name__)
UPLOAD_FOLDER = 'UPLOAD'
ALLOWED_EXTENSIONS = {'zip'}
EXTENSION_LIST = 'zip'

current_order = []


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
    if request.method == 'POST':
        files = request.files.getlist('file')
        for file in files:
            if file and allowed_file(file.filename):
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename) 
                file.save(filepath)
                #rozpakuj pliki
                with zipfile.ZipFile(filepath) as zip_ref:
                    zip_ref.extractall(app.config['UPLOAD_FOLDER'])
        return 'Plik został przesłany'
    return render_template('upload.html')

@app.route('/filelist')
def filelist():
    files = [f for f in os.listdir(app.config['UPLOAD_FOLDER']) if f.endswith(app.config['EXTENSION_LIST'])] 
    return render_template('filelist.html', files=files)

@app.route ('/update_order', methods=['POST'])
def update_order():
    global current_order
    new_order = request.json
    current_order = new_order
    print(f"-- Current file order: {' | '.join(map(str, current_order))}")
    return jsonify({"success": True, "new_order": current_order})

if __name__ == '__main__':
    app.run(debug=True)
