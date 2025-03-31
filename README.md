![Translink Project Screenshot](https://github.com/Innocentem/translink/static/images/Capture1.PNG)
Translink - A Seamless Cargo Transportation Platform
Table of Contents
Introduction
Features
Technologies Used
Getting Started
Project Structure
Contributing
License
Introduction
Translink is a web application that connects shippers with reliable truck drivers, making it easier to transport goods efficiently and affordably. The platform aims to provide a seamless cargo transportation experience for both shippers and truck drivers.
Features
User registration and authentication
Truck and cargo listing with filtering and searching options
Requesting trucks for transportation
Messaging system for communication between shippers and truck drivers
Rating and review system for truck drivers
Payment integration for secure transactions
Technologies Used
Python 3.9
Flask web framework
Bootstrap 4 for responsive design
Jinja2 templating engine
SQLite database for development
PostgreSQL database for production
Google Maps API for location-based services
![Translink Project Screenshot](https://github.com/Innocentem/translink/static/images/Capture2.PNG)
Getting Started
1.
Clone the repository: git clone https://github.com/Innocentem/translink.git
2.
Create a virtual environment: python3 -m venv venv
3.
Activate the virtual environment: source venv/bin/activate
4.
Install dependencies: pip install -r requirements.txt
5.
Set up environment variables (optional):
FLASK_APP: app.py
FLASK_ENV: venv/Scripts/activate
SECRET_KEY: Set to a strong secret key for session encryption
DATABASE_URI: instance/translink.db
6.
Initialize the database: flask db init
7.
Migrate the database: flask db migrate
8.
Upgrade the database: flask db upgrade
9.
Run the development server: flask run
![Translink Project Screenshot](https://github.com/Innocentem/translink/static/images/Capture3.PNG)
Project Structure
translink/
├── app/
│   ├── __init__.py
│   ├── models.py
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth_routes.py
│   │   ├── dashboard_routes.py
│   │   └── browse_routes.py
│   ├── static/
│   │   └── (static files)
│   └── templates/
│       └── (HTML templates)
├── migrations/
│   └── (database migration files)
├── requirements.txt
├── run.py
![Translink Project Screenshot](https://github.com/Innocentem/translink/static/images/Capture4.PNG)
Contributing
Contributions are welcome! If you have any ideas or improvements, feel free to open an issue or submit a pull request.
![Translink Project Screenshot](https://github.com/Innocentem/translink/static/images/Capture5.PNG)
License
This project is licensed under the MIT License. See the LICENSE file for more details.
That's it! I hope this README helps you get started with your Translink project. Let me know if you have any questions or need further assistance!
![Translink Project Screenshot](https://github.com/Innocentem/translink/static/images/Capture6.PNG)
![Translink Project Screenshot](https://github.com/Innocentem/translink/static/images/Capture7.PNG)
![Translink Project Screenshot](https://github.com/Innocentem/translink/static/images/Capture8.PNG)
![Translink Project Screenshot](https://github.com/Innocentem/translink/static/images/Capture9.PNG)
![Translink Project Screenshot](https://github.com/Innocentem/translink/static/images/Capture10.PNG)
![Translink Project Screenshot](https://github.com/Innocentem/translink/static/images/Capture01.PNG)
![Translink Project Screenshot](https://github.com/Innocentem/translink/static/images/Capture02.PNG)
