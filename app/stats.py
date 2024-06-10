from app import db
from .models import Person, ShoutRound, ShoutCompleted, Attendee
from collections import defaultdict
from sqlalchemy.orm import joinedload

def get_coffee_matrix():
    # Preload related entities to reduce the number of database queries
    shout_rounds = ShoutRound.query.options(joinedload(ShoutRound.completed_shouts), joinedload(ShoutRound.attendees)).all()
    # Ensure persons are ordered by shout_sequence
    persons = Person.query.order_by(Person.shout_sequence).all()

    # Debug: Print out the shout sequence for each person
    for person in persons:
        print(f"Person: {person.name}, Shout Sequence: {person.shout_sequence}")

    # Mapping of person IDs to names, with a marker for inactive persons
    names_ordered = {person.id: f"{person.name} (Seq: {person.shout_sequence}){' *' if not person.active else ''}" for person in persons}
    names_list = [names_ordered[person.id] for person in persons]

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
    matrix_dict = {names_ordered[k]: {names_ordered[ak]: av for ak, av in v.items() if ak in names_ordered} for k, v in matrix.items() if k in names_ordered}
    total_purchases_dict = {names_ordered[k]: v for k, v in total_purchases_per_person.items() if k in names_ordered}
    grand_total_coffees = sum(total_purchases_per_person.values())

    # Return the ordered list of names based on shout_sequence, alongside the other calculated values
    return names_list, matrix_dict, total_purchases_dict, grand_total_coffees
