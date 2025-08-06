import datetime
from extensions import db

class GenerationHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    operation_id = db.Column(db.String(80), unique=True, nullable=False)
    prompt = db.Column(db.String(500), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='queued')
    video_path = db.Column(db.String(500), nullable=True)
    image_path = db.Column(db.String(500), nullable=True)
    error_message = db.Column(db.String(500), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    input_payload = db.Column(db.Text, nullable=True)
    output_payload = db.Column(db.Text, nullable=True)
    operation_type = db.Column(db.String(50), nullable=True)

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class SystemInstruction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    content = db.Column(db.Text, nullable=False)

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
