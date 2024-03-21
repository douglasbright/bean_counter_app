from app import db, models, app 

def add_user():
    name = input("Enter the user's name: ")
    user = models.Person(name=name)
    with app.app_context():  # Create the context
        db.session.add(user)
        db.session.commit()
    print(f"User '{name}' added successfully!")

if __name__ == '__main__':
    print("Welcome to the User Adder:")
    while True:
        add_user()
        continue_adding = input("Add another user? (y/n): ").lower()
        if continue_adding != 'y':
            print("Exiting...")
            break
