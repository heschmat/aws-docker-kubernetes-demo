import logging
import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Use DATABASE_URL if available, otherwise construct it from parts
db_url = os.environ.get("DATABASE_URL")

if not db_url:
    db_username = os.environ["POSTGRES_USER"]
    db_password = os.environ["POSTGRES_PASSWORD"]
    db_host = os.environ.get("DB_HOST", "127.0.0.1")
    db_port = os.environ.get("DB_PORT", "5432")
    db_name = os.environ.get("POSTGRES_DB", "postgres")
    db_url = f"postgresql://{db_username}:{db_password}@{db_host}:{db_port}/{db_name}"

app.config["SQLALCHEMY_DATABASE_URI"] = db_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

app.logger.setLevel(logging.DEBUG)
