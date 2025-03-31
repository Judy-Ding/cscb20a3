from flask import Flask, request, jsonify, render_template, url_for, flash, redirect, request, session
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
import re

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///a3db.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

# Initialize database tables
with app.app_context():
    db.create_all()
    print("Database tables created")

# ------------------------------------------------------------------------------
class anonyFeedback(db.Model):
    __tablename__ = "anonyFeedback"
    feedbackID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    instructorID = db.Column(db.Integer)
    like_teaching = db.Column(db.Text)
    improvement_teaching = db.Column(db.Text)
    like_labs = db.Column(db.Text)
    improvement_labs = db.Column(db.Text)
    viewed_status = db.Column(db.Text)

    def __repr__(self):
        return f"anonyFeedback('{self.feedbackID}', '{self.instructorID}')"

# ------------------------------------------------------------------------------
class studentMarks(db.Model):
    __tablename__ = "studentMarks"
    ID = db.Column(db.Integer, db.ForeignKey('userInfo.ID'), primary_key=True)
    assessment_type = db.Column(db.Text, primary_key=True)  # Composite primary key
    grade = db.Column(db.Float)
    
    # Composite primary key constraint
    __table_args__ = (
        db.PrimaryKeyConstraint('ID', 'assessment_type'),
    )

    def __repr__(self):
        return f"studentMarks('{self.ID}', '{self.assessment_type}', '{self.grade}')"

# ------------------------------------------------------------------------------
class regradeReq(db.Model):
    __tablename__ = "regradeReq"
    remarkID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_name = db.Column(db.Text)
    assessment = db.Column(db.Text)
    reason = db.Column(db.Text)
    remark_status = db.Column(db.Text)
    remark_action = db.Column(db.Text)

    def __repr__(self):
        return f"regradeReq('{self.remarkID}', '{self.student_name}')"

# ------------------------------------------------------------------------------
class User(db.Model):
    __tablename__ = "userInfo"
    
    ID = db.Column(db.Integer, primary_key=True)
    university_id = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    utor_email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    user_type = db.Column(db.String(20), nullable=False)

    def __repr__(self):
        return f"User('{self.ID}', '{self.name}')"

    def verify_password(self, password):
        return bcrypt.check_password_hash(self.password, password)

#-----------------------------
class lectureNotes(db.Model):
    __tablename__ = 'lectureNotes'
    id = db.Column(db.Integer, primary_key=True)
    week = db.Column(db.Integer)
    topic = db.Column(db.String(100))
    url = db.Column(db.String(200))

    def __repr__(self):
        return f"lectureNotes('{self.week}', '{self.topic}', '{self.url}')"

#-----------------------------

@app.route('/test_db')
def test_db():
    try:
        db.session.query(User).first()
        return "Connected to the database successfully!"
    except Exception as e:
        return "An error occurred when connecting to the database: " + str(e)

@app.route('/')
@app.route('/home')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    else:
        university_id = request.form.get('university_id')
        name = request.form.get('name')
        utor_email = request.form.get('utor_email')
        password = bcrypt.generate_password_hash(request.form['password']).decode('utf-8')
        user_type = request.form.get('user_type')

        registration_details = (
            university_id,
            name,
            utor_email,
            password,
            user_type
        )

        try:
            add_users(registration_details)
            flash('Registration Successful! Please login now:')
            return redirect(url_for('login'))
        except ValueError as e:
            flash(str(e))
            return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    # POST: Process login form
    utor_email = request.form['utor_email']
    password = request.form['password']
    user = User.query.filter_by(utor_email=utor_email).first()

    if not user or not bcrypt.check_password_hash(user.password, password):
        flash('Invalid login details. Please try again.', 'error')
        return render_template('login.html')

    # Successful login, starts the user's session
    session['utor_email'] = utor_email
    session['user_id'] = user.ID
    session['user_type'] = user.user_type
    session['user_name'] = user.name
    
    session.permanent = True

    # Redirect based on user type
    if user.user_type == 'instructor':
        return redirect(url_for('i_homeafterlogin'))
    elif user.user_type == 'student':
        return redirect(url_for('s_homeafterlogin'))
    else:
        flash('User type not recognized.', 'error')
        return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/i_homeafterlogin')
def i_homeafterlogin():
    if 'user_type' not in session or session['user_type'] != 'instructor':
        return redirect(url_for('login'))
    pagename = 'Home'
    return render_template('i_homeafterlogin.html', pagename=pagename)

@app.route('/s_homeafterlogin')
def s_homeafterlogin():
    if 'user_type' not in session or session['user_type'] != 'student':
        return redirect(url_for('login'))
    pagename = 's_homeafterlogin'
    return render_template('s_homeafterlogin.html', pagename=pagename)

@app.route('/i_anonfeedback')
def i_anonfeedback():
    if 'user_type' not in session or session['user_type'] != 'instructor':
        return redirect(url_for('login'))
    
    instructor_id = session.get('user_id')
    pagename = 'Anonymous Feedback'
    query_feedback_result=i_query_feedback(instructor_id) #query for feedback for instructor and return
    return render_template('i_anonfeedback.html', pagename=pagename, query_feedback_result=query_feedback_result)

def i_query_feedback(instructor_id):
    feedback_data=anonyFeedback.query.filter_by(instructorID=instructor_id).all() 
    return feedback_data

@app.route('/s_anonfeedback', methods=['GET', 'POST'])
def s_anonfeedback():
    if 'user_type' not in session or session['user_type'] != 'student':
        return redirect(url_for('login'))

    if request.method == 'GET':
        instructors = User.query.filter_by(user_type='instructor').all()
        return render_template('s_anonfeedback.html', pagename='s_anonfeedback', instructors=instructors)
    else:
        anonyFeedback_details = (
            request.form['instructor'],
            request.form['like-teaching'],
            request.form['improve-teaching'],
            request.form['like-labs'],
            request.form['improve-labs']
        )
        add_anonfeedback(anonyFeedback_details)
        flash('Feedback submitted successfully!', 'success')
        return redirect(url_for('s_anonfeedback'))

def add_anonfeedback(anonyFeedback_details):
    instructor = User.query.filter_by(name=anonyFeedback_details[0], user_type='instructor').first()
    if not instructor:
        print('Instructor not found!')
        return
    
    new_feedback = anonyFeedback(
        instructorID=instructor.ID,
        like_teaching=anonyFeedback_details[1],
        improvement_teaching=anonyFeedback_details[2],
        like_labs=anonyFeedback_details[3],
        improvement_labs=anonyFeedback_details[4],
        viewed_status='Not Viewed',
    )
    db.session.add(new_feedback)
    db.session.commit()

@app.route('/s_marks')
def s_marks():
    student_id = session.get('user_id')

    if not student_id:
        flash('Please log in first.', 'warning')
        return redirect(url_for('login'))
    
    marks = studentMarks.query.filter_by(ID=student_id).all()
    remark_requests = {request.assessment: request for request in regradeReq.query.all()}
    return render_template('s_marks.html', marks=marks, remark_requests=remark_requests)

@app.route('/submit_remark', methods=['POST'])
def submit_remark():
    assessment = request.form.get('assessment_type')
    reason = request.form.get('reason')
    student_name = session['user_name']

    existing_request = regradeReq.query.filter_by(assessment=assessment).first()
    if existing_request:
        flash(f'A remark request for {assessment} has already been submitted.', 'warning')
    else:
        new_request = regradeReq(
            student_name=student_name,
            assessment=assessment,
            reason=reason,
            remark_status="Pending",
            remark_action=""
        )
        db.session.add(new_request)
        db.session.commit()
        flash(f'Remark request for {assessment} submitted successfully!', 'success')

    return redirect(url_for('s_marks'))

@app.route('/s_lectures')
def s_lectures():
    if 'user_type' not in session or session['user_type'] != 'student':
        return redirect(url_for('login'))

    lecture_notes = lectureNotes.query.all()
    
    return render_template('s_lectures.html', lecture_notes=lecture_notes)

def add_users(registration_details):
    university_id, name, utor_email, password, user_type = registration_details
    existing_user = User.query.filter_by(university_id=university_id).first()

    if existing_user is None:
        new_user = User(
            university_id=university_id,
            name=name,
            utor_email=utor_email,
            password=password,
            user_type=user_type
        )
        db.session.add(new_user)
        db.session.commit()
    else:
        raise ValueError(f"A user with the ID {university_id} already exists.")

def get_identity_by_email(utor_email):
    current_user = User.query.filter_by(utor_email=utor_email).first()
    return current_user.user_type

@app.route('/i_marks') # view student marks
def i_marks():
    if 'user_type' not in session or session['user_type'] != 'instructor':
        return redirect(url_for('login'))
    pagename = 'Marks'
    student_names = {user.ID: user.name for user in User.query.filter_by(user_type='student')}
    marks = studentMarks.query.all()
    return render_template('i_marks.html', marks=marks, student_names=student_names, pagename='Marks')

@app.route('/i_updatemarks', methods=['GET', 'POST']) # update student marks
def i_updatemarks():
    if 'user_type' not in session or session['user_type'] != 'instructor':
        return redirect(url_for('login'))
    
    if request.method == 'GET':
        students = User.query.filter_by(user_type='student').all()
        assessment_types = ['Assignment 1', 'Assignment 2', 'Assignment 3', 'Midterm', 'Final'] 
        return render_template('i_updatemarks.html', pagename='Update Marks', students=students, assessment_types=assessment_types)
    else:
        student_name = request.form['student']
        assessment_type = request.form['assessment-type']
        mark = float(request.form['update-mark'])
        
        student = User.query.filter_by(name=student_name, user_type='student').first()
        if not student:
            flash('Student not found!', 'danger')
            return redirect(url_for('i_updatemarks'))
        
        existing_mark = studentMarks.query.filter_by(
            ID=student.ID,
            assessment_type=assessment_type
        ).first()
        
        if existing_mark:
            # updates existing mark
            existing_mark.grade = mark
        else:
            # else, creates new mark entry
            new_mark = studentMarks(
                ID=student.ID,
                assessment_type=assessment_type,
                grade=mark
            )
            db.session.add(new_mark)
        db.session.commit()
        flash('Marks updated successfully!', 'success')
        return redirect(url_for('i_updatemarks'))

@app.route('/i_lectures') # view lec
def i_lectures():
    pagename = 'lecture notes'
    if 'user_type' not in session or session['user_type'] != 'instructor':
        return redirect(url_for('login'))

    lecture_notes = lectureNotes.query.all()
    
    return render_template('i_lectures.html', lecture_notes=lecture_notes, pagename = pagename)

@app.route('/i_updatelectures') # update lec
def i_updatelectures():
    if 'user_type' not in session or session['user_type'] != 'instructor':
        return redirect(url_for('login'))
    pagename = 'Update Lecture Notes'
    return render_template('i_updatelectures.html', pagename = pagename)

@app.route('/update_status', methods=['POST'])
def update_status():
    data = request.get_json()
    feedback = anonyFeedback.query.get(data['feedbackID'])
    
    if feedback:
        feedback.viewed_status = data['newStatus']
        db.session.commit()
        return jsonify({'success': True})
    
    return jsonify({'success': False})

@app.route('/i_remarkreqs') # view student remark requests
def i_remarkreqs():
    if 'user_type' not in session or session['user_type'] != 'instructor':
        flash('Please login as instructor to view remark requests', 'error')
        return redirect(url_for('login'))
    
    pagename = 'Remark Requests'

    status_filter = request.args.get('status')
    query = regradeReq.query.filter(
        regradeReq.remark_status.in_(['Pending', 'Approved', 'Rejected'])
    )

    remarks = query.order_by(regradeReq.remark_status, regradeReq.remarkID).all()
    
    return render_template('i_remarkreqs.html', remark_requests=remarks)

@app.route('/update_remark_status', methods=['POST'])
def update_remark_status():
    if 'user_type' not in session or session['user_type'] != 'instructor':
        flash('Unauthorized action', 'error')
        return redirect(url_for('login'))
    
    remark_id = request.form.get('remarkID')
    new_status = request.form.get('remark_status')
    
    remark = regradeReq.query.get(remark_id)
    if remark:
        remark.remark_status = new_status
        remark.remark_action = f"Status changed to {new_status} by {session.get('username')}"
        db.session.commit()
        flash(f'Remark request #{remark_id} updated to {new_status}', 'success')
    else:
        flash('Remark request not found', 'error')
    
    return redirect(url_for('i_remarkreqs'))

@app.route('/add_lecture', methods=['POST'])
def add_lecture():
    week = request.form['week']
    topic = request.form['topic']
    url = request.form['url']

    new_lecture = lectureNotes(week=week, topic=topic, url=url)
    pagename = 'Update Lecture Notes'

    db.session.add(new_lecture)
    db.session.commit()

    flash('Lecture notes submitted successfully!', 'success')

    return redirect(url_for('i_updatelectures'))

if __name__ == '__main__':
    app.run(debug=True)
    #to put the two tests