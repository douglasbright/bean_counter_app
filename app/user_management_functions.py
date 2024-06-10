from app import db, models
from sqlalchemy import func

def add_user(name):
    # Determine the next shout sequence number
    max_sequence = db.session.query(func.max(models.Person.shout_sequence)).scalar()
    next_sequence = 1 if max_sequence is None else max_sequence + 1

    new_user = models.Person(name=name, shout_sequence=next_sequence)
    db.session.add(new_user)
    db.session.commit()

def edit_user(user_id, new_name, new_sequence):
    user = models.Person.query.get_or_404(user_id)
    user.name = new_name
    user.shout_sequence = new_sequence
    db.session.commit()

def toggle_user_status(user_id):
    user = models.Person.query.get_or_404(user_id)
    user.active = not user.active
    db.session.commit()
