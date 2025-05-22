nrittya_backend.py

from flask import Flask, render_template, request, redirect, session, url_for, flash 
from werkzeug.utils import secure_filename import os import sqlite3 
from tensorflow.keras.models import load_model 
from tensorflow.keras.preprocessing import image 
from tensorflow.keras.applications.vgg16 import preprocess_input import numpy as np 
from gtts import gTTS 
from datetime import datetime import base64 import cv2 import io import PIL.Image

Flask app initialization

app = Flask(name) app.secret_key = 'nrittya_secret_key' UPLOAD_FOLDER = 'static/uploads' AUDIO_FOLDER = 'static/audio' app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER app.config['AUDIO_FOLDER'] = AUDIO_FOLDER

Load pre-trained CNN model (based on VGG16 architecture, fine-tuned on dance/mudra images)

model = load_model('model/vgg16_cnn_model.h5') labels = ['Bharatanatyam', 'Kathak', 'Kuchipudi', 'Mudra1', 'Mudra2']  # Update with actual classes

Database configuration

DB_NAME = 'users.db'

def init_db(): with sqlite3.connect(DB_NAME) as conn: conn.execute('''CREATE TABLE IF NOT EXISTS users ( username TEXT PRIMARY KEY, password TEXT NOT NULL)''')

Home route

@app.route('/') def home(): return "Welcome to Nrittya - Go to /register or /login"

User registration

@app.route('/register', methods=['GET', 'POST']) def register(): if request.method == 'POST': username = request.form['username'] password = request.form['password'] with sqlite3.connect(DB_NAME) as conn: try: conn.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password)) flash("Registration successful! Please login.") return redirect(url_for('login')) except sqlite3.IntegrityError: return "Username already exists. Try another." return '''<form method="POST"> Username: <input type="text" name="username"><br> Password: <input type="password" name="password"><br> <input type="submit" value="Register"> </form>'''

User login

@app.route('/login', methods=['GET', 'POST']) def login(): if request.method == 'POST': username = request.form['username'] password = request.form['password'] with sqlite3.connect(DB_NAME) as conn: cursor = conn.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password)) if cursor.fetchone(): session['user'] = username return redirect(url_for('upload')) else: return "Invalid credentials. Try again." return '''<form method="POST"> Username: <input type="text" name="username"><br> Password: <input type="password" name="password"><br> <input type="submit" value="Login"> </form>'''

CNN-based prediction function

def predict_dance(img_path): img = image.load_img(img_path, target_size=(224, 224)) img_array = image.img_to_array(img) img_array = np.expand_dims(img_array, axis=0) img_array = preprocess_input(img_array)  # For VGG-style preprocessing predictions = model.predict(img_array) return labels[np.argmax(predictions)]

Upload and predict route

@app.route('/upload', methods=['GET', 'POST']) def upload(): if 'user' not in session: return redirect(url_for('login'))

if request.method == 'POST':
    if 'image' in request.files:
        file = request.files['image']
        if file:
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], f"{timestamp}_{filename}")
            file.save(filepath)

    elif 'captured_image' in request.form:
        captured_data = request.form['captured_image']
        header, encoded = captured_data.split(",")
        img_data = base64.b64decode(encoded)
        img = PIL.Image.open(io.BytesIO(img_data))
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"capture_{timestamp}.jpg"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        img.save(filepath)

    else:
        return "No image uploaded or captured."

    label = predict_dance(filepath)

    # Generate informative audio feedback using gTTS
    audio_file = f"result_{timestamp}.mp3"
    audio_path = os.path.join(app.config['AUDIO_FOLDER'], audio_file)
    tts = gTTS(text=f"This image represents {label}, a form of classical Indian art.", lang='en')
    tts.save(audio_path)

    return f"<h3>Prediction: {label}</h3><br><img src='/{filepath}' width='300'><br><audio controls src='/{audio_path}'></audio>"

return '''<form method="POST" enctype="multipart/form-data">
            Upload Image: <input type="file" name="image"><br><br>
            Or Capture Image:<br>
            <video id="video" width="320" height="240" autoplay></video><br>
            <button type="button" onclick="capture()">Capture</button>
            <input type="hidden" name="captured_image" id="captured_image">
            <canvas id="canvas" width="320" height="240" style="display:none;"></canvas><br>
            <input type="submit" value="Predict">
          </form>
          <script>
            const video = document.getElementById('video');
            const canvas = document.getElementById('canvas');
            const context = canvas.getContext('2d');
            navigator.mediaDevices.getUserMedia({ video: true })
                .then(stream => {
                    video.srcObject = stream;
                });
            function capture() {
                context.drawImage(video, 0, 0, canvas.width, canvas.height);
                document.getElementById('captured_image').value = canvas.toDataURL('image/jpeg');
            }
          </script>'''

Logout

@app.route('/logout') def logout(): session.pop('user', None) return redirect(url_for('home'))

Run app

if name == 'main': init_db() os.makedirs(UPLOAD_FOLDER, exist_ok=True) os.makedirs(AUDIO_FOLDER, exist_ok=True) app.run(debug=True)