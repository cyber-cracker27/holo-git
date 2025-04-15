from flask import Flask, render_template, jsonify, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from models import db, User, StreamSession, Attendance, Resource, Interaction
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///streaming.db'
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
db.init_app(app)

# Create tables
with app.app_context():
    db.create_all()
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

# Authentication routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if not username or not password:
            flash('Username and password are required', 'danger')
            return redirect(url_for('login'))

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['role'] = user.role
            session['username'] = user.username
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        flash('Invalid credentials', 'danger')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role')

        if not username or not password or not role:
            flash('All fields are required', 'danger')
            return redirect(url_for('register'))

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists', 'danger')
            return redirect(url_for('register'))

        new_user = User(username=username, role=role)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully', 'success')
    return redirect(url_for('login'))

# Dashboard based on role
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('Please log in to access the dashboard', 'warning')
        return redirect(url_for('login'))
    
    if session.get('role') == 'teacher':
        return render_template('teacher_dashboard.html')
    elif session.get('role') == 'student':
        return render_template('student_dashboard.html')
    else:
        flash('Invalid role', 'danger')
        return redirect(url_for('login'))

# Teacher streaming controls
@app.route("/stream/start", methods=["POST"])
def start_stream():
    if 'user_id' not in session or session.get('role') != 'teacher':
        return jsonify({"error": "Unauthorized"}), 403
    
    data = request.json
    title = data.get('title', 'Untitled Session')
    stream_url = data.get('stream_url')  # Get the stream URL from the request

    if not title or not stream_url:
        return jsonify({"error": "Title and stream URL are required"}), 400

    # Create a new stream session
    new_session = StreamSession(
        teacher_id=session['user_id'],
        start_time=datetime.now(),
        title=title,
        stream_url=stream_url  # Store the stream URL
    )
    db.session.add(new_session)
    db.session.commit()
    
    return jsonify({
        "message": "Stream started!",
        "session_id": new_session.id,
        "stream_url": new_session.stream_url
    })

@app.route("/stream/stop", methods=["POST"])
def stop_stream():
    if 'user_id' not in session or session.get('role') != 'teacher':
        return jsonify({"error": "Unauthorized"}), 403
    
    current_session = StreamSession.query.filter_by(
        teacher_id=session['user_id'],
        end_time=None
    ).first()
    
    if not current_session:
        return jsonify({"error": "No active stream to stop"}), 404

    current_session.end_time = datetime.now()
    db.session.commit()
    
    return jsonify({"message": "Stream stopped!"})

# Stream status for all users
@app.route("/stream/status", methods=["GET"])
def stream_status():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 403

    current_session = StreamSession.query.filter_by(end_time=None).first()
    if not current_session:
        return jsonify({"status": "No active stream"}), 200

    return jsonify({
        "status": "Active",
        "title": current_session.title,
        "start_time": current_session.start_time.strftime("%Y-%m-%d %H:%M:%S"),
        "teacher_id": current_session.teacher_id,
        "stream_url": current_session.stream_url  # Include the stream URL
    })

# Attendance tracking
@app.route("/stream/join", methods=["POST"])
def join_stream():
    if 'user_id' not in session or session.get('role') != 'student':
        return jsonify({"error": "Unauthorized"}), 403

    current_session = StreamSession.query.filter_by(end_time=None).first()
    if not current_session:
        return jsonify({"error": "No active stream to join"}), 404

    existing_attendance = Attendance.query.filter_by(
        session_id=current_session.id,
        student_id=session['user_id']
    ).first()
    if existing_attendance:
        return jsonify({"message": "Already joined"}), 200

    new_attendance = Attendance(
        session_id=current_session.id,
        student_id=session['user_id'],
        join_time=datetime.now()
    )
    db.session.add(new_attendance)
    db.session.commit()

    return jsonify({"message": "Joined stream!"})

@app.route("/stream/attendance", methods=["GET"])
def get_attendance():
    if 'user_id' not in session or session.get('role') != 'teacher':
        return jsonify({"error": "Unauthorized"}), 403

    current_session = StreamSession.query.filter_by(end_time=None).first()
    if not current_session:
        return jsonify({"attendees": []}), 200

    attendees = [
        {
            "id": a.student.id,
            "name": a.student.username,
            "join_time": a.join_time.strftime("%H:%M:%S")
        }
        for a in current_session.attendances
    ]
    return jsonify({"attendees": attendees})

# Resource management
@app.route("/resource/upload", methods=["POST"])
def upload_resource():
    if 'user_id' not in session or session.get('role') != 'teacher':
        return jsonify({"error": "Unauthorized"}), 403

    current_session = StreamSession.query.filter_by(end_time=None).first()
    if not current_session:
        return jsonify({"error": "No active stream"}), 404

    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    filename = file.filename
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)

    file_size = f"{os.path.getsize(file_path) / 1024 / 1024:.1f} MB"
    file_type = filename.split('.')[-1].upper()

    new_resource = Resource(
        session_id=current_session.id,
        name=filename,
        file_type=file_type,
        file_size=file_size,
        file_path=file_path
    )
    db.session.add(new_resource)
    db.session.commit()

    return jsonify({
        "message": "Resource uploaded!",
        "resource": {
            "id": new_resource.id,
            "name": new_resource.name,
            "file_type": new_resource.file_type,
            "file_size": new_resource.file_size
        }
    })

@app.route("/resources", methods=["GET"])
def get_resources():
    current_session = StreamSession.query.filter_by(end_time=None).first()
    if not current_session:
        return jsonify({"resources": []}), 200

    resources = [
        {
            "id": r.id,
            "name": r.name,
            "file_type": r.file_type,
            "file_size": r.file_size,
            "file_path": f"/{r.file_path}"
        }
        for r in current_session.resources
    ]
    return jsonify({"resources": resources})

# Interaction handling
@app.route("/interaction", methods=["POST"])
def submit_interaction():
    if 'user_id' not in session or session.get('role') != 'student':
        return jsonify({"error": "Unauthorized"}), 403

    current_session = StreamSession.query.filter_by(end_time=None).first()
    if not current_session:
        return jsonify({"error": "No active stream"}), 404

    data = request.json
    interaction_type = data.get('type')
    content = data.get('content')

    if interaction_type not in ['raise_hand', 'question', 'message']:
        return jsonify({"error": "Invalid interaction type"}), 400

    new_interaction = Interaction(
        session_id=current_session.id,
        student_id=session['user_id'],
        type=interaction_type,
        content=content
    )
    db.session.add(new_interaction)
    db.session.commit()

    return jsonify({"message": "Interaction submitted!"})

@app.route("/interactions", methods=["GET"])
def get_interactions():
    if 'user_id' not in session or session.get('role') != 'teacher':
        return jsonify({"error": "Unauthorized"}), 403

    current_session = StreamSession.query.filter_by(end_time=None).first()
    if not current_session:
        return jsonify({"interactions": []}), 200

    interactions = [
        {
            "id": i.id,
            "type": i.type,
            "content": i.content,
            "student": i.student.username,
            "timestamp": i.timestamp.strftime("%H:%M:%S")
        }
        for i in current_session.interactions
    ]
    return jsonify({"interactions": interactions})

if __name__ == "__main__":
    app.run(debug=True)