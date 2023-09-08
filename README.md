### Project Setup:

##### Pre-requisites:
1. Python3.9 or above.
2. Postgres14 or above

After cloning the project, you should now have a directory named `LoanApp`.
Run the following commands inside this LoanApp directory.

##### Setting up the Venv.
1. Create a python venv using `python3 -m venv venv_name`
2. To activate the venv, run `source venv_name/bin/activate`
3. Install python dependencies: `pip install -r requirements-dev.txt`

##### Setting up the database.
1. Start the postgres server. (if using brew run: `brew services start postgresql`)
2. To create the database run- `psql < db_setup.sql`
3. To apply the migrations run- `python manage.py migrate`
4. To create some users of the system, run the command: `python manage.py localsetup`
5. Once the users are created you can you the postman collection to test out the flows.
    - The script will create 5 customers (add 1 to the last 2 digits of the username and password to get a new user): `username: customer20, password: customerpass20`
    - The script will create 2 admins (add 1 to the last 2 digits of the username and password to get a new user): `username: admin21, password: adminpass21`
    - Use the username and password for Basic Authentication while firing requests to the webserver.

##### Starting the webserver.
1. Run `python manage.py runserver`

##### Note: there are tests covering the various flows in LoanApp/loans/tests
To run tests: `python manage.py test`