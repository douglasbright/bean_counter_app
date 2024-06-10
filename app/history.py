from . import db
from .models import ShoutRound, ShoutCompleted, Attendee, ShoutAbsence, Person
from datetime import datetime

def get_shout_history(shout_rounds=None):
    if shout_rounds is None:
        shout_rounds = ShoutRound.query.all()

    history_data = []

    for round in shout_rounds:
        # Fetch the names of people who completed the shout
        completed_shout = ShoutCompleted.query.filter_by(round_id=round.id).first()
        completed_by = Person.query.filter_by(id=completed_shout.person_id).first().name if completed_shout else 'N/A'
        date = completed_shout.date if completed_shout else None

        # Fetch the names of attendees
        attendees_ids = [attendee.person_id for attendee in round.attendees]
        attendees = [Person.query.filter_by(id=id).first().name for id in attendees_ids]

        # Fetch the names of absentees
        absentees_ids = [absence.person_id for absence in round.absences]
        absentees = [Person.query.filter_by(id=id).first().name for id in absentees_ids]

        history_data.append({
            'round_id': round.id,
            'date': date,
            'completed_by': completed_by,
            'attendees': ', '.join(attendees),
            'absentees': ', '.join(absentees)
        })

    return history_data

def get_people():
    return Person.query.all()
