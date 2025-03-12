# UPlant

Before you begin, make sure you have Python installed on your system. This project uses Python 3.8 or later.

## Clone the Repository

First, make sure you've cloned the project repository from GitHub to your local machine.

## Create a Virtual Environment

A virtual environment is a self-contained directory that contains a Python installation for a particular version of Python, plus a number of additional packages. Creating a virtual environment allows you to manage project dependencies separately from your global Python environment.

For Windows
Run the following commands in your command prompt:

  ```
  python -m venv env
  env\Scripts\activate
  ```

For macOS and Linux
Run the following commands in your terminal. You have to change the path to the root of your project:

  ```
  python -m venv env
  source /pathto/ProjectName/root/env/bin/activate
  ```

After activation, your terminal prompt will change to show the name of the activated environment.

## Install Project Dependencies

With your virtual environment activated, install the project dependencies using the following command:
  
  ```
  pip install -r requirements.txt
  ```

This command reads the requirements.txt file in your project directory and installs all the necessary Python packages.

## Set Up the Database

Run the following command to make migrations to your database. This step sets up your database schema according to the models defined in your Django apps.

  ```
  python manage.py makemigrations
  python manage.py migrate
  ```

## Create an Admin User

To access the Django admin interface, you need to create a superuser account. Use the following command and follow the prompts to set up the user:

  ```
  python manage.py createsuperuser
  ```

Enter your desired username, email, and password when prompted.

## Run the Development Server

Now you're ready to start the development server and see the project in action. Run:

  ```
  python manage.py runserver
  ```

This command starts the Django development server. You can access your application by navigating to http://127.0.0.1:8000/ in your web browser.

## Development Tools
List All URLs of the Project

  ```
  python manage.py show_urls
  ```

Interactive Django Shell

  ```
  python manage.py shell
  ```

Example use for shell: resetting a user's password (your own if you bug the app)

  ```
  from django.contrib.auth.hashers import make_password
  from user_management.models import User
  
  user = User.objects.get(email='jbartosz@uwm.edu') // replace with your email
  if not user.is_active:
      user.is_active = True
      user.save()
  new_password = 'new_password'
  user.password = make_password(new_password)
  user.save()
  print(f'Password has been reset for {user.email}. Please try logging in with the new password.')

  ```

  To print out the file structure, navigate to the project file and run the commands below.

  ```
tree -I '__pycache__|migrations|venv|node_modules'

  ```
or
  ```
find . -maxdepth 5 -type d \( -name '__pycache__' -o -name 'migrations' -o -name 'venv' -o -name 'node_modules' -o -name '.git' \) -prune -o -print

  ```

## Testing

To run the tests, use the following command:

  ```
  python manage.py test user_management // (or any other app)
  ```

Run Tests with Coverage
    
  ```
  coverage run manage.py test user_management // (or any other app)
  coverage report
  ```

## Managing Static/Requirement Files

To collect static files into the STATIC_ROOT directory, run the following command:

  ```
  python manage.py collectstatic
  ```
  
Grab current requirements.

  ```
  pip freeze > requirements_complete.txt
  ```
  
## Access the Admin Panel

To access the Django admin interface, navigate to http://127.0.0.1:8000/admin and log in using the superuser credentials you created earlier.

## Stopping the Server

To stop the Django development server, press Ctrl+C in your command prompt or terminal window.
