import os

class Config:
    PROJECT_ID = os.environ.get("GCP_PROJECT", "vital-octagon-19612")
    LOCATION = "us-central1"
    VIDEO_DIR = "static/videos"
    GCS_BUCKET_NAME = os.environ.get("GCS_BUCKET_NAME", "gk-test-veo")
    SQLALCHEMY_DATABASE_URI = 'sqlite:///history.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    GEMINI_MODEL = "gemini-2.5-flash"
