from flask import current_app
from flask_sqlalchemy import SQLAlchemy
import jwt
from time import time

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(80), unique=True, nullable=False)

    def generate_token(self):
        return jwt.encode({"email": self.email,
                           "exp": time() + 360000}, 
                           current_app.config["SECRET_KEY"], algorithm="HS256")
    
    def verify_token(token):
        try:
            email = jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=["HS256"])["email"]
        except Exception as e:
            print(e)
            return
        return User.query.filter_by(email=email).first()

    def __repr__(self):
        return f"User {self.email}"