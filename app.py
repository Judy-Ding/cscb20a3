from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

@app.route('/') #default page you want to do certain things
@app.route('/homeafterlogin')
def home():
    pagename = 'homeafterlogin'
    return render_template('homeafterlogin.html', pagename = pagename)

if __name__ == '__main__':
        app.run(debug = True)

