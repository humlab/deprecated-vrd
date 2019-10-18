from flask import Flask, request
from werkzeug.utils import secure_filename
from flask_cors import CORS

app = Flask(__name__)
CORS(app)


@app.route('/')
def hello_world():
    return 'Hello, world!'


@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        f = request.files['file']
        f.save(secure_filename(f.filename))

        return 'file uploaded successfully!'


if __name__ == '__main__':
    app.run()
