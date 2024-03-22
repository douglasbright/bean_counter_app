from app import db
from .models import Person, ShoutRound, ShoutCompleted, Attendee
from collections import defaultdict
from sqlalchemy.orm import joinedload
from sqlalchemy import func

def get_coffee_matrix():
    # Preload related entities to reduce the number of database queries
    shout_rounds = ShoutRound.query.options(joinedload(ShoutRound.completed_shouts), joinedload(ShoutRound.attendees)).all()
    # Ensure persons are ordered by ID
    persons = Person.query.order_by(Person.id).all()

    # Mapping of person IDs to names, with a marker for inactive persons
    # This now implicitly preserves the order based on Person.id
    names_ordered = {person.id: f"{person.name}{' *' if not person.active else ''}" for person in persons}

    # Initialize matrix and totals
    matrix = defaultdict(lambda: defaultdict(int))
    total_purchases_per_person = defaultdict(int)

    for round in shout_rounds:
        for shout_completed in round.completed_shouts:
            purchaser_id = shout_completed.person_id
            # Ensure attendees are counted for the current shout
            attendee_ids = [attendee.person_id for attendee in round.attendees]

            for attendee_id in attendee_ids:
                if purchaser_id in names_ordered and attendee_id in names_ordered:  # Check if IDs are valid
                    matrix[purchaser_id][attendee_id] += 1
                    total_purchases_per_person[purchaser_id] += 1

    # Convert the nested default dicts to regular dicts for template compatibility
    # Adjust to use the ordered names
    matrix_dict = {names_ordered[k]: {names_ordered[ak]: av for ak, av in v.items() if ak in names_ordered} for k, v in matrix.items() if k in names_ordered}
    total_purchases_dict = {names_ordered[k]: v for k, v in total_purchases_per_person.items() if k in names_ordered}
    grand_total_coffees = sum(total_purchases_per_person.values())

    # Return the ordered list of names based on ID, alongside the other calculated values
    return list(names_ordered.values()), matrix_dict, total_purchases_dict, grand_total_coffees
