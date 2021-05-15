import os
import re
from apscheduler.schedulers.background import BackgroundScheduler
import time
from selenium import webdriver
from flask import Flask, request, render_template, redirect, url_for
from flask_mail import Mail, Message
from models import db, User

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")[:8] + "ql" + os.environ.get("DATABASE_URL")[8:]
print(app.config["SQLALCHEMY_DATABASE_URI"])
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY")

db.app = app
db.init_app(app)

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = "grenchat@gmail.com"
app.config['MAIL_PASSWORD'] = os.environ.get("PASSWORD")

mail = Mail(app)

regex = "^[a-zA-Z0-9]+[\._]?[a-zA-Z0-9]+[@]\w+[.]\w{2,3}$"

def check(email):
    if (re.search(regex, email)):
        return True
    else:
        return False

def send_email(user, subject, html):
    with app.app_context(), app.test_request_context():
        msg = Message()
        html = html + "<br><a href=" + '"' + url_for("delete", token=user.generate_token(), _external=True) + '"' + ">Prestani slati mailove</a>"
        #print(subject, html)
        msg.subject = subject
        msg.sender = app.config['MAIL_USERNAME']
        msg.recipients = [user.email]
        msg.html = html
        mail.send(msg)
        print("Sent to: " + user.email)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")
    else:
        email = request.form.get("email")
        print(email)
        if not check(email):
            return "Unesite pravilnu email adresu"
        check_user = User.query.filter_by(email=email).first()
        if check_user:
            return "Registrirani ste"
        user = User(email=email)
        db.session.add(user)
        db.session.commit()
        print(email)
        return "Registrirani ste"

@app.route("/delete/<token>", methods=["GET", "POST"])
def delete(token):
    if request.method == "GET":
        return render_template("delete.html")
    else:
        user = User.verify_token(token)
        if not user:
            return "Neeeema te"
        db.session.delete(user)
        db.session.commit()
        return "Ok"

options = webdriver.ChromeOptions()
options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
options.add_argument("--headless")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--no-sandbox")
options.add_experimental_option('excludeSwitches', ['enable-logging'])
zadnji = ""

def job():
    global zadnji
    driver = webdriver.Chrome(executable_path=os.environ.get("CHROMEDRIVER_PATH"), options=options)
    print("OPENED")
    driver.get("http://www.gimnazija-varazdin.skole.hr/")
    element = driver.find_element_by_class_name("news_leads")
    if not zadnji or element.find_element_by_class_name("text").text == zadnji:
        print("Nema nist novog")
        zadnji = element.find_element_by_class_name("text").text
        driver.close()
        print("CLOSED")
        return
    print("Mailovi se salju")
    subject = element.find_element_by_class_name("text").text
    html = element.get_attribute("innerHTML")

    x = 0
    while True:
        pos = subject.find("src", x, len(subject))
        if pos == -1:
            break
        subject = subject[:(pos+5)] + "http://www.gimnazija-varazdin.skole.hr" + subject[(pos+5):]
        x = pos + 20

    x = 0
    while True:
        pos = html.find("src", x, len(html))
        if pos == -1:
            break
        html = html[:(pos+5)] + "http://www.gimnazija-varazdin.skole.hr" + html[(pos+5):]
        x = pos + 20

    x = 0
    while True:
        pos = html.find("href", x, len(html))
        if pos == -1:
            break
        html = html[:(pos+6)] + "http://www.gimnazija-varazdin.skole.hr" + html[(pos+6):]
        x = pos + 20

    users = User.query.all()
    if users:
        for user in users:
            try:
                send_email(user, subject, html)
            except:
                print("Error on user:", user)
    zadnji = element.find_element_by_class_name("text").text
    driver.close()
    print("CLOSED")

scheduler = BackgroundScheduler(deamon=True)
scheduler.add_job(job, "interval", minutes=1)
scheduler.start()

if __name__ == "__main__":
    db.create_all()
    app.run()
