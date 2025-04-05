from flask import Flask
from extensions import db
from models import User

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///translink.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

with app.app_context():
    admins = User.query.filter_by(role='admin').all()
    if admins:
        print("\n=== TransLink Admin Accounts ===")
        print(f"Total admin accounts: {len(admins)}")
        print("\nAdmin Details:")
        for admin in admins:
            print(f"\nUsername: {admin.username}")
            print(f"Created: {admin.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Last seen: {admin.last_seen.strftime('%Y-%m-%d %H:%M:%S') if admin.last_seen else 'Never'}")
            print("-" * 30)
    else:
        print("No admin accounts found!")