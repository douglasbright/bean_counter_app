# charts.py
from .models import db, Person, ShoutCompleted, Attendee
from collections import defaultdict

def prepare_coffee_chart_data():
    total_coffees_per_person = defaultdict(int)

    # Fetch all completed shouts and their corresponding attendees
    completed_shouts = ShoutCompleted.query.all()
    for shout in completed_shouts:
        # Find the number of attendees for this shout (excluding the shouter for self-purchases if desired)
        attendees_count = Attendee.query.filter_by(shout_round_id=shout.round_id).count()

        # Increment the total coffees given out by this person
        total_coffees_per_person[shout.person_id] += attendees_count
    
    # Fetch names for each person_id in total_coffees_per_person
    persons = Person.query.filter(Person.id.in_(total_coffees_per_person.keys())).all()
    person_names = {person.id: person.name for person in persons}
    
    labels = [person_names[id] for id in total_coffees_per_person.keys()]
    values = list(total_coffees_per_person.values())

    chart_data = {
        'labels': labels,
        'datasets': [{
            'data': values,
            'backgroundColor': ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#F7464A', '#46BFBD', '#FDB45C'],
        }]
    }
    return chart_data
