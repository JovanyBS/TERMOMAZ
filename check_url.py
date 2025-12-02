from app import app
from flask import url_for

with app.app_context():
    try:
        url = url_for('reports')
        print(f"Success: URL for reports is {url}")
    except Exception as e:
        print(f"Error: {e}")
