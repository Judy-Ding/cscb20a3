from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from flask_bcrypt import Bcrypt
app = Flask(__name__)

app.config['SECRET_KEY'] = 'e3f5894c596f4342124d351a4d981f0f60f01ea18a86976ae619c15893e592a9'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///a3db.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes = 10)

# Initialize extensions
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

# Initialize database tables
with app.app_context():
    db.create_all()
    print("Database tables created")

#--------------DATABASE---------------------------------------------------------
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

    user_id = db.Column(db.Integer, db.ForeignKey('userInfo.ID'), nullable=False) # Foreign key

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

    # Define the relationship using backref for bidirectional access
    studentMarks = db.relationship('studentMarks', backref='user', lazy=True)

    def __repr__(self):
        return f"User('{self.ID}', '{self.name}')"

    def verify_password(self, password):
        return bcrypt.check_password_hash(self.password, password)


#--------------ROUTE APPLICATIONS---------------------------------------------------------




#STUDENT INTERFACE SECTOR
@app.route('/template')
def template():
    pagename='Test'
    return render_template('template.html', pagename=pagename)

@app.route('/') #default page you want to do certain things => this needs to be changed to monica's default login page
@app.route('/s_homeafterlogin')
def s_homeafterlogin():
    pagename = 's_homeafterlogin'
    return render_template('s_homeafterlogin.html', pagename = pagename)

@app.route('/s_anonfeedback', methods = ['GET', 'POST'])
def s_anonfeedback():
    if request.method == 'GET':
        instructors = User.query.filter_by(user_type='Instructor').all()
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
        return render_template('s_anonfeedback.html', pagename='s_anonfeedback')

def add_anonfeedback(anonyFeedback_details):
    new_feedback = anonyFeedback(
        instructorID=anonyFeedback_details[0],
        like_teaching=anonyFeedback_details[1],
        improvement_teaching=anonyFeedback_details[2],
        like_labs=anonyFeedback_details[3],
        improvement_labs=anonyFeedback_details[4],
        viewed_status='Not Viewed',
        user_id=session.get('user_id')
    )
    db.session.add(new_feedback)
    db.session.commit()

@app.route('/s_marks')
#session
def s_marks():
    pagename = 's_marks'
    return render_template('s_anonfeedback.html', pagename = pagename)

@app.route('/s_lectures')
def s_lectures():
    pagename = 's_lectures'
    return render_template('s_lectures.html', pagename = pagename)

@app.route('/s_calendar')
def s_calendar():
    pagename = 's_calendar'
    return render_template('s_calendar.html', pagename = pagename)

@app.route('/s_courseteam')
def s_courseteam():
    pagename = 's_courseteam'
    return render_template('s_courseteam.html', pagename = pagename)

if __name__ == '__main__':
        app.run(debug = True)




