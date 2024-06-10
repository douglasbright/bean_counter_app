from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

db = SQLAlchemy(app)

# Import models here so that they are registered with SQLAlchemy before creating the tables
from app import models

def create_database():
    with app.app_context():
        db.create_all()
        print("Database tables created.")

# Now that models are imported, we can create the database tables
create_database()

# Import routes at the end to avoid circular imports as routes will likely import 'app' and 'db'
from app import routes
