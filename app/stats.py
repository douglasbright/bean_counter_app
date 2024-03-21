from app import db
from .models import Person, ShoutRound, ShoutCompleted, Attendee
from collections import defaultdict
from sqlalchemy.orm import joinedload
from sqlalchemy import func

def get_coffee_matrix():
    # Preload related entities to reduce the number of database queries
    shout_rounds = ShoutRound.query.options(joinedload(ShoutRound.completed_shouts), joinedload(ShoutRound.attendees)).all()
    persons = Person.query.all()

    # Mapping of person IDs to names, with a marker for inactive persons
    names = {person.id: f"{person.name}{' *' if not person.active else ''}" for person in persons}

    # Initialize matrix and totals
    matrix = defaultdict(lambda: defaultdict(int))
    total_purchases_per_person = defaultdict(int)

    for round in shout_rounds:
        for shout_completed in round.completed_shouts:
            purchaser_id = shout_completed.person_id
            # Ensure attendees are counted for the current shout
            attendee_ids = [attendee.person_id for attendee in round.attendees]
            
            for attendee_id in attendee_ids:
                matrix[purchaser_id][attendee_id] += 1
                total_purchases_per_person[purchaser_id] += 1

    # Convert the nested default dicts to regular dicts for template compatibility
    matrix_dict = {names[k]: {names[ak]: av for ak, av in v.items()} for k, v in matrix.items()}
    total_purchases_dict = {names[k]: v for k, v in total_purchases_per_person.items()}
    grand_total_coffees = sum(total_purchases_per_person.values())
    print(names)
    print(matrix)

    return list(names.values()), matrix_dict, total_purchases_dict, grand_total_coffees
