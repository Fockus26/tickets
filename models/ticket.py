from extensions import db

class Ticket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    page_name = db.Column(db.String(100), nullable=False)
    concert_name = db.Column(db.String(150), nullable=False)
    event_name = db.Column(db.String(150), nullable=False)
    event_day = db.Column(db.JSON, nullable=False)
    event_month = db.Column(db.String(15), nullable=False)
    event_time = db.Column(db.String(15), nullable=False)
    tickets_data = db.Column(db.Text, nullable=False)
