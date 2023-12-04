from flask import Flask, jsonify, request, render_template
from flask_sqlalchemy import SQLAlchemy
import os
import zipfile

app = Flask(__name__)
UPLOAD_FOLDER = 'UPLOAD'
ALLOWED_EXTENSIONS = {'zip'}
EXTENSION_LIST = 'txt'

# Konfiguracja SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///file_labels.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Definicja modelu bazy danych
class FileLabel(db.Model):
    __tablename__ = 'file_label'
    id = db.Column(db.Integer, primary_key=True)
    file_path = db.Column(db.String, unique=True, nullable=False)
    file_label = db.Column(db.String, nullable=False)
    order = db.Column(db.Integer)  # Nowa kolumna do przechowywania kolejności

# Inicjalizacja bazy danych
with app.app_context():
    db.create_all()

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['EXTENSION_LIST'] = EXTENSION_LIST

file_with_labels = []

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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
    new_order = request.json
    for index, item in enumerate(new_order):
        record = FileLabel.query.filter_by(file_path=item['filename']).first()
        if record:
            record.order = index
            db.session.commit()

    # Pobieranie i zwracanie zaktualizowanych rekordów
    updated_records = FileLabel.query.order_by(FileLabel.order).all()
    return jsonify({"success": True, "new_order": [r.file_path for r in updated_records]})

def label_items():
    # Pobieranie aktualnej listy plików z bazy danych
    current_files = FileLabel.query.order_by(FileLabel.order).all()
    # Tworzenie zbioru istniejących ścieżek plików
    existing_file_paths = set(f.file_path for f in current_files)
    # Wyszukiwanie nowych plików w folderze UPLOAD
    new_files = [f for f in os.listdir(app.config['UPLOAD_FOLDER']) 
                 if f.endswith(app.config['EXTENSION_LIST']) and f not in existing_file_paths]
    for file in new_files:
        # Dodawanie nowego rekordu
        new_record = FileLabel(file_path=file, file_label='2')  # Domyślnie label '2' dla nowych plików
        db.session.add(new_record)
    # Zatwierdzanie zmian w bazie danych
    db.session.commit()


@app.route('/filelist')
def filelist():
    # Pobieranie aktualnej listy plików z bazy danych
    current_files = FileLabel.query.order_by(FileLabel.order).all()

    # Przekazywanie listy plików do template
    return render_template('filelist.html', files=current_files)

@app.route('/update_order', methods=['POST'])
def update_order():
    new_order = request.json

    # Aktualizacja kolejności i etykiet
    for index, item in enumerate(new_order):
        record = FileLabel.query.filter_by(file_path=item['filename']).first()
        if record:
            record.order = index
            record.file_label = '1' if index == 0 else '2'  # Aktualizacja etykiety
            db.session.commit()

    # Pobieranie i zwracanie zaktualizowanych rekordów
    updated_records = FileLabel.query.order_by(FileLabel.order).all()
    updated_data = [{'filename': r.file_path, 'label': r.file_label} for r in updated_records]
    return jsonify({"success": True, "new_order": updated_data})



@app.route('/get_current_order', methods=['GET'])
def get_current_order():
    # Pobieranie danych bezpośrednio z bazy danych
    file_labels = FileLabel.query.order_by(FileLabel.order).all()
    # Przygotowanie danych do wysłania
    current_order = [{'filename': file_label.file_path, 'label': file_label.file_label} for file_label in file_labels]
    return jsonify({"current_order": current_order})


if __name__ == '__main__':
    app.run(debug=True)
    
