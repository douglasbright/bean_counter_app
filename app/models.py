from sqlalchemy import UniqueConstraint
from . import db

class Person(db.Model):
    __tablename__ = 'people'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True)
    available = db.Column(db.Boolean, default=True)
    catchup_due = db.Column(db.Boolean, default=False)
    active = db.Column(db.Boolean, default=True)
    absences = db.relationship("ShoutAbsence", back_populates="person")
    is_current_shouter = db.Column(db.Boolean, default=False)
    attendance_records = db.relationship("Attendee", back_populates="person")
    shout_sequence = db.Column(db.Integer, unique=True)  # New field for shout sequence

class ShoutRound(db.Model):
    __tablename__ = 'shout_rounds'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    completed = db.Column(db.Boolean, default=False)
    absences = db.relationship("ShoutAbsence", back_populates="round")
    completed_shouts = db.relationship("ShoutCompleted", back_populates="round")
    attendees = db.relationship("Attendee", back_populates="shout_round")

class ShoutAbsence(db.Model):
    __tablename__ = 'shout_absences'
    id = db.Column(db.Integer, primary_key=True)
    round_id = db.Column(db.Integer, db.ForeignKey('shout_rounds.id'))
    person_id = db.Column(db.Integer, db.ForeignKey('people.id'))
    first_miss = db.Column(db.Boolean, default=False)
    second_miss = db.Column(db.Boolean, default=False)
    round = db.relationship("ShoutRound", back_populates="absences")
    person = db.relationship("Person", back_populates="absences")

class ShoutCompleted(db.Model):
    __tablename__ = 'shout_completed'
    id = db.Column(db.Integer, primary_key=True)
    person_id = db.Column(db.Integer, db.ForeignKey('people.id'))
    date = db.Column(db.DateTime)
    round_id = db.Column(db.Integer, db.ForeignKey('shout_rounds.id'))
    round = db.relationship("ShoutRound", back_populates="completed_shouts")

class Attendee(db.Model):
    __tablename__ = 'attendees'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    person_id = db.Column(db.Integer, db.ForeignKey('people.id'))
    shout_round_id = db.Column(db.Integer, db.ForeignKey('shout_rounds.id'))
    person = db.relationship("Person", back_populates="attendance_records")
    shout_round = db.relationship("ShoutRound", back_populates="attendees")
