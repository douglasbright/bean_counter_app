from app import db, models
from app.models import Person, ShoutRound, ShoutAbsence, Attendee, ShoutCompleted
  # Assuming 'app' is your Flask application

def reset_shouts():
    # Reset other tables first if they depend on Person
    ShoutRound.query.delete()
    ShoutAbsence.query.delete()
    ShoutCompleted.query.delete()
    Attendee.query.delete()

    # Update Person records
    Person.query.update({
        Person.available: True,
        Person.catchup_due: False,
        Person.is_current_shouter: False
    }, synchronize_session=False)
    db.session.commit()

    message = "Shout data reset successfully!"
    return message
