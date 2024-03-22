from app import db, models
from app.models import Person, ShoutRound, ShoutAbsence, Attendee, ShoutCompleted
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text

def reset_shouts():
    try:
        # Delete dependent records first to avoid foreign key constraints violation
        ShoutAbsence.query.delete()
        ShoutCompleted.query.delete()
        Attendee.query.delete()
        
        # Now it's safe to delete records from ShoutRound
        ShoutRound.query.delete()
        
        # Update Person records as previously, no change needed here
        Person.query.update({
            Person.available: True,
            Person.catchup_due: False,
            Person.is_current_shouter: False
        }, synchronize_session='fetch')  # Changed to 'fetch' to avoid potential issues
        
        # Reset the sequence for ShoutRound.id
        sequence_name = 'shout_rounds_id_seq'  # Make sure this is the correct sequence name
        # Wrap the raw SQL command in text()
        db.session.execute(text(f'ALTER SEQUENCE {sequence_name} RESTART WITH 1;'))
        
        # Commit all changes
        db.session.commit()

        message = "Shout data reset successfully!"
        return message

    except Exception as e:
        db.session.rollback()
        # It's generally a good idea to log the exception
        print(f"An error occurred: {e}")
        return "An error occurred during the reset process."