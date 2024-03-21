from . import db
from .models import ShoutRound, ShoutCompleted, Attendee, ShoutAbsence, Person

def get_shout_history():
    shout_rounds = ShoutRound.query.all()
    history_data = []

    for round in shout_rounds:
        # Fetch the names of people who completed the shout
        completed_by_ids = [shout.person_id for shout in round.completed_shouts]
        completed_by = [Person.query.filter_by(id=id).first().name for id in completed_by_ids]

        # Fetch the names of attendees
        attendees_ids = [attendee.person_id for attendee in round.attendees]
        attendees = [Person.query.filter_by(id=id).first().name for id in attendees_ids]

        # Fetch the names of absentees
        absentees_ids = [absence.person_id for absence in round.absences]
        absentees = [Person.query.filter_by(id=id).first().name for id in absentees_ids]

        history_data.append({
            'round_id': round.id,
            'completed_by': ', '.join(completed_by),
            'attendees': ', '.join(attendees),
            'absentees': ', '.join(absentees)
        })

    return history_data
