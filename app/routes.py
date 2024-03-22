from flask import flash, redirect, render_template, request, url_for
from . import app
from app import models, db
from app.user_management_functions import add_user, edit_user, toggle_user_status
from .shout import get_or_create_current_round, determine_current_shouter, mark_person_absent, complete_shout_round, get_active_member_ids, get_last_10_shouts
from .index import reset_shouts
from .history import get_shout_history
from .stats import get_coffee_matrix
from .charts import prepare_coffee_chart_data
from app.models import Person
from sqlalchemy.exc import IntegrityError 
from datetime import datetime

@app.route('/user_management', methods=['GET'])
def user_management():
    users = Person.query.all()  # Retrieve all users
    return render_template('user_management.html', users=users)

@app.route('/add_user', methods=['POST'])
def add_user_route():
    name = request.form.get('name')
    if name:
        try:
            new_user = Person(name=name)  
            db.session.add(new_user)
            db.session.commit()
            flash("User added successfully!", 'success')
        except IntegrityError:
            db.session.rollback()  # Rollback the transaction in case of error
            flash("Failed to add user. A user with that name already exists.", 'danger')
    else:
        flash("Failed to add user. Name cannot be empty.", 'danger')
    return redirect(url_for('user_management'))

@app.route('/toggle_status/<int:user_id>', methods=['POST'])
def toggle_status_route(user_id):
    user = Person.query.get_or_404(user_id)
    user.active = not user.active  # Toggle the status
    db.session.commit()
    flash(f"User {'activated' if user.active else 'deactivated'} successfully!", 'success')
    return redirect(url_for('user_management'))

@app.route('/edit_user', methods=['POST'])
def edit_user_route():
    user_id = request.form.get('user_id')
    new_name = request.form.get('name')
    user = Person.query.get_or_404(user_id)

    if new_name:
        try:
            user.name = new_name
            db.session.commit()
            flash("User name updated successfully!", 'success')
        except IntegrityError:
            db.session.rollback()
            flash("Cannot update name, Failed to update user. A user with that name already exists.", 'danger')
    else:
        flash("Failed to update user name. New name cannot be empty.", 'danger')
    return redirect(url_for('user_management'))

@app.route('/delete_user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    user = Person.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash("User deleted successfully!", 'success')
    return redirect(url_for('user_management'))

@app.route('/')
def index():
    coffee_chart_data = prepare_coffee_chart_data()
    return render_template('index.html', coffee_chart_data=coffee_chart_data)

@app.route('/reset_shouts', methods=['POST'])
def reset_shouts_route():
    try:
        reset_shouts()  # Perform the reset operation
        flash('Shout data reset successfully!', 'success')  # Optional: Flash a success message
    except Exception as e:
        flash(f'An error occurred: {e}', 'error')  # Optional: Flash an error message

    return redirect(url_for('index'))  # Redirect to the index route or another appropriate page

@app.route('/shout')
def shout_page():
    current_round = get_or_create_current_round()
    current_shouter = determine_current_shouter()
    active_members = Person.query.filter_by(active=True).all()
    last_10_shouts = get_last_10_shouts()  # Fetch the last 10 shouts
    
    return render_template('shout.html', current_round=current_round,
                           current_shouter=current_shouter,
                           active_members=active_members,
                           last_10_shouts=last_10_shouts)

@app.route('/mark_absent', methods=['POST'])
def mark_absent():
    round_id = request.form.get('round_id')
    person_id = request.form.get('shouter_id')
    print(person_id)
    message = mark_person_absent(round_id, person_id)
    flash(message, 'success')
    return redirect(url_for('shout_page'))

@app.route('/complete_shout', methods=['POST'])
def complete_shout():
    round_id = request.form.get('round_id')
    shouter_id = request.form.get('shouter_id')
    shout_date = request.form.get('shout_date')  # Retrieve the shout date from the form
    attendee_ids = request.form.getlist('attendee_ids')

    # Convert shout_date from string to datetime object
    if shout_date:
        try:
            shout_date = datetime.strptime(shout_date, '%Y-%m-%d')
        except ValueError:
            flash('Invalid date format.', 'danger')
            return redirect(url_for('shout_page'))

    if not attendee_ids:
        flash('No team members were selected. Please select at least one attendee.', 'warning')
        return redirect(url_for('shout_page'))

    current_shouter = Person.query.get(shouter_id)

    success, message = complete_shout_round(round_id, current_shouter, attendee_ids, shout_date)  # Pass shout_date to your function

    flash(message, 'success' if success else 'danger')
    return redirect(url_for('stats_page'))

@app.route('/history')
def history():
    history_data = get_shout_history()
    return render_template('history.html', history_data=history_data)

@app.route('/stats')
def stats_page():
    names_list, matrix_dict, total_purchases_dict, grand_total_coffees = get_coffee_matrix()
    return render_template('stats.html', names_list=sorted(names_list), matrix_dict=matrix_dict, total_purchases_dict=total_purchases_dict, grand_total_coffees=grand_total_coffees)

