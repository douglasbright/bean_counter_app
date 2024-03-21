from app import db, models

def add_user(name):
    new_user = models.Person(name=name)
    db.session.add(new_user)
    db.session.commit()

def edit_user(user_id, new_name):
    user = models.Person.query.get_or_404(user_id)  # Fetch user or raise an error
    user.name = new_name
    db.session.commit()

def toggle_user_status(user_id):
    user = models.Person.query.get_or_404(user_id)
    user.status = not user.status  # Toggle the status
    db.session.commit()
