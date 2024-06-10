from flask import flash, redirect, render_template, request, url_for
from . import app
from app import models, db
from app.user_management_functions import add_user, edit_user, toggle_user_status
from .shout import get_or_create_current_round, determine_current_shouter,determine_next_shouter, mark_person_absent, complete_shout_round, get_active_member_ids, get_last_10_shouts
from .index import reset_shouts
from .history import get_shout_history, get_people
from .stats import get_coffee_matrix
from .charts import prepare_coffee_chart_data
from app.models import Person, ShoutAbsence, ShoutRound, ShoutCompleted, Attendee
from sqlalchemy.exc import IntegrityError 
from datetime import datetime
from math import ceil


@app.context_processor
def inject_shouter_info():
    current_shouter = determine_current_shouter()
    next_shouter = determine_next_shouter()  # Since determine_current_shouter sets the next shouter after marking the current one
    return dict(current_shouter=current_shouter, next_shouter=next_shouter)

@app.route('/user_management', methods=['GET', 'POST'])
def user_management():
    if request.method == 'POST':
        errors = False
        try:
            # Handle updates
            for user_id, name, shout_sequence, is_current_shouter in zip(
                    request.form.getlist('user_id'),
                    request.form.getlist('name'),
                    request.form.getlist('shout_sequence'),
                    request.form.getlist('is_current_shouter', type=int)):

                user = Person.query.get(user_id)

                # Check if any fields have changed
                name_changed = user.name != name
                shout_sequence_changed = user.shout_sequence != int(shout_sequence)
                is_current_shouter_changed = user.is_current_shouter != bool(is_current_shouter)

                if name_changed or shout_sequence_changed or is_current_shouter_changed:
                    user.name = name
                    user.shout_sequence = int(shout_sequence)
                    user.is_current_shouter = bool(is_current_shouter)

                    try:
                        db.session.commit()
                    except IntegrityError as e:
                        db.session.rollback()
                        app.logger.error(f"IntegrityError: {e}")
                        flash(f"Failed to update user {name}. Ensure the name and shout sequence are unique.", 'danger')
                        errors = True

            if not errors:
                flash("Users updated successfully!", 'success')

        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Exception: {e}")
            flash("An unexpected error occurred. Please try again.", 'danger')

    # Retrieve all users ordered by shout_sequence
    users = Person.query.order_by(Person.shout_sequence).all()
    return render_template('user_management.html', users=users)

@app.route('/edit_user', methods=['POST'])
def edit_user():
    try:
        user_id = request.form.get('user_id')
        new_name = request.form.get('name')

        if not user_id or not new_name:
            raise ValueError("User ID and new name are required")

        user = Person.query.get(user_id)
        user.name = new_name

        db.session.commit()
        flash(f"User name updated to {new_name}!", 'success')
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Exception: {e}")
        flash(f"An error occurred: {str(e)}", 'danger')
    return redirect(url_for('user_management'))

@app.route('/toggle_catchup_due/<int:user_id>', methods=['POST'])
def toggle_catchup_due(user_id):
    try:
        user = Person.query.get(user_id)
        user.catchup_due = not user.catchup_due
        db.session.commit()
        flash(f"Catchup due status for {user.name} updated!", 'success')
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Exception: {e}")
        flash(f"An error occurred: {str(e)}", 'danger')
    return redirect(url_for('user_management'))

@app.route('/toggle_available/<int:user_id>', methods=['POST'])
def toggle_available(user_id):
    try:
        user = Person.query.get(user_id)
        user.available = not user.available
        db.session.commit()
        flash(f"Availability status for {user.name} updated!", 'success')
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Exception: {e}")
        flash(f"An error occurred: {str(e)}", 'danger')
    return redirect(url_for('user_management'))

@app.route('/set_current_shouter', methods=['POST'])
def set_current_shouter():
    try:
        user_id = request.form.get('user_id')

        if not user_id:
            raise ValueError("User ID is required")

        # Clear the current shouter flag for all users
        Person.query.update({Person.is_current_shouter: False})
        db.session.flush()  # Flush to apply changes

        # Set the current shouter flag for the selected user
        user = Person.query.get(user_id)
        user.is_current_shouter = True

        db.session.commit()
        flash(f"{user.name} is now the current shouter!", 'success')
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Exception: {e}")
        flash(f"An error occurred: {str(e)}", 'danger')
    return redirect(url_for('user_management'))

@app.route('/add_user', methods=['POST'])
def add_user_route():
    name = request.form.get('name')
    if name:
        try:
            add_user(name)
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

@app.route('/delete_user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    user = Person.query.get_or_404(user_id)
    try:
        db.session.delete(user)
        db.session.commit()
        flash(f'User {user.name} deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting user: {str(e)}', 'danger')
    return redirect(url_for('user_management'))

@app.route('/update_order', methods=['POST'])
def update_order():
    try:
        user_ids = request.form.getlist('user_id')
        shout_sequences = request.form.getlist('shout_sequence')

        app.logger.debug(f"Received user IDs: {user_ids}")
        app.logger.debug(f"Received shout sequences: {shout_sequences}")

        if len(user_ids) != len(shout_sequences):
            raise ValueError("User IDs and shout sequences length mismatch")

        with db.session.no_autoflush:
            # Step 1: Temporarily set the sequences to avoid conflicts
            temp_offset = 1000
            for user_id in user_ids:
                user = Person.query.get(user_id)
                user.shout_sequence = temp_offset + int(user_id)
                app.logger.debug(f"Temporarily set {user.name} (ID: {user_id}) sequence to {temp_offset + int(user_id)}")

            db.session.flush()  # Flush to apply temporary changes

            # Step 2: Set the final sequences based on the reordered data
            for user_id, sequence in zip(user_ids, shout_sequences):
                user = Person.query.get(user_id)
                user.shout_sequence = int(sequence)
                app.logger.debug(f"Set {user.name} (ID: {user_id}) sequence to {sequence}")

            db.session.commit()
            flash("User order updated successfully!", 'success')
    except IntegrityError as e:
        db.session.rollback()
        app.logger.error(f"IntegrityError: {e}")
        flash("Failed to update user order. Ensure shout sequences are unique.", 'danger')
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Exception: {e}")
        flash(f"An error occurred: {str(e)}", 'danger')
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
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    sort = request.args.get('sort', 'round_id')
    order = request.args.get('order', 'desc')

    query = ShoutRound.query.join(ShoutCompleted).order_by(getattr(ShoutCompleted, sort).desc() if order == 'desc' else getattr(ShoutCompleted, sort).asc())
    total = query.count()
    shout_rounds = query.paginate(page=page, per_page=per_page, error_out=False)

    pagination = {
        'page': page,
        'per_page': per_page,
        'total': total,
        'pages': shout_rounds.pages,
        'has_next': shout_rounds.has_next,
        'has_prev': shout_rounds.has_prev,
        'next_num': shout_rounds.next_num,
        'prev_num': shout_rounds.prev_num
    }

    history_data = get_shout_history(shout_rounds.items)
    people = get_people()
    return render_template('history.html', history_data=history_data, people=people, pagination=pagination, sort=sort, order=order, per_page=per_page)

@app.route('/edit_round', methods=['POST'])
def edit_round():
    round_id = request.form.get('round_id')
    date_str = request.form.get('date')
    shouter_id = request.form.get('shouter_id')
    attendee_ids = request.form.getlist('attendees')
    absentees_ids = request.form.getlist('absentees')

    try:
        if date_str:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
        else:
            date = None
        
        shout_round = ShoutRound.query.get(round_id)
        completed_shout = ShoutCompleted.query.filter_by(round_id=round_id).first()
        
        if not completed_shout:
            completed_shout = ShoutCompleted(round_id=round_id)
            db.session.add(completed_shout)
        
        if date:
            completed_shout.date = date
        if shouter_id:
            completed_shout.person_id = shouter_id

        # Clear existing attendees and add the new ones
        if attendee_ids:
            shout_round.attendees.clear()
            attendees = Person.query.filter(Person.id.in_(attendee_ids)).all()
            for attendee in attendees:
                shout_round.attendees.append(Attendee(person_id=attendee.id, shout_round_id=round_id))

        # Clear existing absentees and add the new ones
        if absentees_ids:
            shout_round.absences.clear()
            absentees = Person.query.filter(Person.id.in_(absentees_ids)).all()
            for absentee in absentees:
                shout_round.absences.append(ShoutAbsence(person_id=absentee.id, round_id=round_id))

        db.session.commit()
        flash('Round updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'An error occurred: {str(e)}', 'danger')

    return redirect(url_for('history'))

@app.route('/stats')
def stats():
    names_list, matrix_dict, total_purchases_dict, grand_total_coffees = get_coffee_matrix()

    # Debug: Print the names list to verify the order
    print(f"Names List: {names_list}")

    return render_template(
        'stats.html',
        names_list=names_list,
        matrix_dict=matrix_dict,
        total_purchases_dict=total_purchases_dict,
        grand_total_coffees=grand_total_coffees
    )
