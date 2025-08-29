from app import db
    
class Registration(db.Model) :
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(100), nullable = False)
    fathers_name = db.Column(db.String(100), nullable = False)
    joining_date = db.Column(db.Date, nullable = False)
    fees = db.Column(db.Integer, nullable = False)
    type = db.Column(db.String(100))
    # mobile_number = db.Column(db.Integer, nullable = False)
    mobile_number = db.Column(db.String(15), nullable=False)

    gmail = db.Column(db.String(100))
    status = db.Column(db.String(20), default = "Active")

    # Relationship to fees table
    fees_records = db.relationship('FeesRecord', backref='student', lazy=True)


class FeesRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('registration.id'), nullable=False)
    fees_due_date = db.Column(db.Date, nullable=False)   # Next due date
    last_payment_date = db.Column(db.Date, nullable=True) # Last payment date
    amount = db.Column(db.Float, nullable=False)
    is_paid = db.Column(db.Boolean, default=False)       # NEW column








