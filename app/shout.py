from app import db, models
from app.models import Person, ShoutRound, ShoutAbsence, Attendee, ShoutCompleted
from datetime import datetime
from sqlalchemy import not_, exists, desc

def get_or_create_current_round():
    current_round = models.ShoutRound.query.filter_by(completed=False).first()

    if not current_round:
        current_round = models.ShoutRound(completed=False)
        db.session.add(current_round)
        db.session.commit()

    return current_round

def determine_current_shouter():
    # Get the IDs of active members
    active_member_ids = get_active_member_ids()

    # Check if there is an existing shouter among active members
    current_shouter = Person.query.filter_by(is_current_shouter=True)\
                                   .filter(Person.id.in_(active_member_ids)).first()
    if current_shouter:
        return current_shouter

    # Get the current round
    current_round = get_or_create_current_round()

    # Prioritize catchup_due, excluding those absent in the current round
    # Subquery to find persons who are absent in the current round
    subquery = (db.session.query(ShoutAbsence.person_id)
                .filter(ShoutAbsence.round_id == current_round.id)
                .subquery())

    # Main query to find active persons not absent in the current round and due for a catchup
    candidates = (Person.query
                  .filter(Person.id.in_(active_member_ids))  # Ensure only active members are considered
                  .filter(~exists().where(Person.id == subquery.c.person_id))  # Exclude those absent in the current round
                  .filter(Person.catchup_due == True)  # Filter for catchup due
                  .order_by(Person.shout_sequence)  # Order by shout_sequence
                  .all())

    # If there are candidates with catchup_due, select the first one
    if candidates:
        current_shouter = candidates[0]
        current_shouter.is_current_shouter = True
        current_shouter.available = False
        db.session.commit()
        return current_shouter

    # Select based on availability among active members
    candidates = Person.query.filter(Person.id.in_(active_member_ids))\
                             .filter(Person.available == True)\
                             .order_by(Person.shout_sequence).all()

    # If there are available candidates, select the first one
    if candidates:
        current_shouter = candidates[0]
        current_shouter.is_current_shouter = True
        current_shouter.available = False
        db.session.commit()
        return current_shouter

    # Full Reset Logic - reset only for active members
    Person.query.filter(Person.id.in_(active_member_ids)).update({Person.available: True}, synchronize_session=False)
    db.session.commit()

    # Fallback - Select first from active members
    current_shouter = Person.query.filter(Person.id.in_(active_member_ids))\
                                  .order_by(Person.shout_sequence).first()
    if current_shouter:
        current_shouter.is_current_shouter = True
        current_shouter.available = False
        db.session.commit()
        return current_shouter
    
def determine_next_shouter():
    # Get the IDs of active members
    active_member_ids = get_active_member_ids()

    # Get the current round
    current_round = get_or_create_current_round()

    # Subquery to find persons who are absent in the current round
    subquery = (db.session.query(ShoutAbsence.person_id)
                .filter(ShoutAbsence.round_id == current_round.id)
                .subquery())

    # Get the current shouter
    current_shouter = Person.query.filter_by(is_current_shouter=True).first()

    # If there is no current shouter, simply use determine_current_shouter
    if not current_shouter:
        return determine_current_shouter()

    # Simulate that the current shouter has completed their shout
    current_shouter_id = current_shouter.id if current_shouter else None

    # Find candidates who are due for a catchup and not absent in the current round, excluding the current shouter
    candidates = (Person.query
                  .filter(Person.id.in_(active_member_ids))
                  .filter(~exists().where(Person.id == subquery.c.person_id))
                  .filter(Person.catchup_due == True)
                  .filter(Person.id != current_shouter_id)
                  .order_by(Person.shout_sequence)
                  .all())

    # If there are candidates with catchup_due, select the first one
    if candidates:
        return candidates[0]

    # Find available candidates, excluding the current shouter
    candidates = Person.query.filter(Person.id.in_(active_member_ids))\
                             .filter(Person.available == True)\
                             .filter(Person.id != current_shouter_id)\
                             .order_by(Person.shout_sequence).all()

    # If there are available candidates, select the first one
    if candidates:
        return candidates[0]

    # If no available candidates, fallback to the first active person in sequence, excluding the current shouter
    candidates = Person.query.filter(Person.id.in_(active_member_ids))\
                             .filter(Person.id != current_shouter_id)\
                             .order_by(Person.shout_sequence).first()

    return candidates

def update_current_shouter(user_id):
    # First, set everyone else to not be the current shouter
    models.Person.query.update({models.Person.is_current_shouter: False})
    
    # Then, set the current shouter
    current_shouter = models.Person.query.get(user_id)
    if current_shouter:
        current_shouter.is_current_shouter = True
        db.session.commit()

def mark_person_absent(round_id, person_id):
    # Get the person directly
    person = Person.query.get(person_id)
    if not person:
        return 'Person not found.'

    # Handle consecutive absences and initial absence with catchup
    if person.catchup_due:  
        # Create a new absence record (second miss)
        new_absence = ShoutAbsence(round_id=round_id, person_id=person_id, second_miss=True) 
        db.session.add(new_absence)
        print("Absence added for person - Second", person.name)
        # Clear the 'catchup_due' flag
        person.catchup_due = False
        message = 'Shouter marked absent (subsequent round with catchup) and status updated.'
    else: 
        # Create an initial absence record
        new_absence = ShoutAbsence(round_id=round_id, person_id=person_id, first_miss=True)
        db.session.add(new_absence)
        print("Absence added for person - First", person.name)
        # Set 'catchup_due' flag to True
        person.catchup_due = True
        message = 'Shouter marked as absent (initial) and status updated.'

    # Update person status (common to both scenarios)
    person.available = False
    person.is_current_shouter = False  
    print(f"Absence added for person - {person.name} marked absent")
    db.session.commit()
    return message

def complete_shout_round(round_id, current_shouter, attendee_ids, shout_date): 
    shout_round = ShoutRound.query.get(round_id)
    if shout_round:
        shout_round.completed = True  

        if current_shouter:
            # Assuming debug prints are for your verification and will be removed or commented out in production
            completed_shout = ShoutCompleted(
                person_id=current_shouter.id,
                date=shout_date, 
                round_id=round_id
            )
            db.session.add(completed_shout)
            current_shouter.is_current_shouter = False
            if current_shouter.catchup_due:
                current_shouter.catchup_due = False
            current_shouter.available = False

        # Fetch names of attendees for the message
        attendee_names = [Person.query.get(attendee_id).name for attendee_id in attendee_ids]
        
        # Record attendees
        for attendee_id in attendee_ids:
            new_attendee = Attendee(
                person_id=attendee_id,
                shout_round_id=round_id
            )
            db.session.add(new_attendee)

        db.session.commit()
        
        formatted_date = shout_date.strftime('%Y-%m-%d')  # Formats the date as YYYY-MM-DD
        # Constructing the detailed message
        message = f"Round {round_id} completed successfully! {formatted_date} Shouter: {current_shouter.name}. Attendees: {', '.join(attendee_names)}."
        return True, message

    return False, "Shout round not found."

def get_active_member_ids():
    active_members = Person.query.filter_by(active=True).all()
    return [member.id for member in active_members]

def get_last_10_shouts():
    # Fetch the last 10 shout completions based on round_id
    last_10_shouts = ShoutCompleted.query.order_by(desc(ShoutCompleted.round_id)).limit(10).all()
    
    # Fetch the details for each shouter
    shouters_details = []
    for shout in last_10_shouts:
        shouter = Person.query.get(shout.person_id)
        shouters_details.append({"shouter": shouter.name, "round_id": shout.round_id, "date": shout.date})
    
    return shouters_details