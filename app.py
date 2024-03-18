from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.utils import secure_filename
import os
import csv
import io
import pathlib
import textwrap
from PIL import Image
import google.generativeai as genai

app = Flask(__name__)
app.secret_key = 'xyzsdfg'
app.config['UPLOAD_FOLDER'] = './uploaded_images'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg'}

# Ensure the upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Configure the Google API key
google_api_key = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=google_api_key)

# Function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Function to load OpenAI model and get responses
def get_gemini_response(input, image):
    model = genai.GenerativeModel('gemini-pro-vision')
    if input != "":
        response = model.generate_content([input, image])
    else:
        response = model.generate_content(image)
    return response.text

@app.route('/', methods=['GET', 'POST'])
def index():
    if 'loggedin' in session:
        # User is already logged in, show the index page
        if request.method == 'POST':
            # Check if the post request has the file part
            if'file' not in request.files:
                flash('No file part')
                return redirect(request.url)
            file = request.files['file']
            input_prompt = request.form['input_prompt']
            
            # If the user does not select a file, the browser submits an empty file without a filename.
            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)
            
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                
                # Process the image and get response
                image = Image.open(file_path)
                response = get_gemini_response(input_prompt, image)
                
                image_url = url_for('static', filename=filename)
                
                # Pass the response and image URL to the template
                return render_template('index.html', response=response, image_url=image_url)

        # Initial page load or no file uploaded
        return render_template('index.html')
    else:
        # User is not logged in, redirect to the login page
        return redirect(url_for('login'))

# Function to save user credentials to a CSV file
def save_user_credentials_to_csv(email, password):
    with open('user_credentials.csv', mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([email, password])

@app.route('/login', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():
    session.permanent = True  # Make the session last indefinitely
    app.secret_key = 'xyzsdfg'  # Set a secret key for the session
    message = ''
    if request.method == 'POST' and 'email' in request.form and 'password' in request.form:
        email = request.form['email']
        password = request.form['password']
        
        # For demonstration purposes, checking credentials by reading from CSV file
        with open('user_credentials.csv', 'r') as file:
            csv_reader = csv.reader(file)
            for row in csv_reader:
                stored_email, stored_password = row
                if email == stored_email and password == stored_password:
                    session['loggedin'] = True
                    session['email'] = email
                    message = "Logged in successfully!"
                    return redirect(url_for('index'))  # Redirect to index page on successful login
        
        message = "Please enter correct email / password!"
    
    return render_template('login.html', message=message)  # Pass the message variable to the template

@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('email', None)
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    message = ''
    if request.method == 'POST' and 'name' in request.form and 'password' in request.form and 'email' in request.form:
        username = request.form['name']
        password = request.form['password']
        email = request.form['email']
        
        # For demonstration purposes, storing credentials in a CSV file
        save_user_credentials_to_csv(email, password)
        
        message = 'You have successfully registered!'
        return redirect(url_for('login'))  # Redirect to login page after successful registration

    elif request.method == 'POST':
        message = 'Please fill out the form!'

    return render_template('register.html', message=message)

if __name__ == "__main__":
    # Start the login page directly
    login()
    app.run(debug=True,host="0.0.0.0",port=8000)