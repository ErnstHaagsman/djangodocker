Django Todo App in Docker
=========================

This is a simple todo app used to demonstrate how to dockerize
a Django application.

Getting started
---------------

Prerequisite:

- Make sure that Docker and Docker Compose are installed and 
  working. [See the docs](https://docs.docker.com/install/)
- Have this repo checked out

Start up the project and apply the migrations by running:

    docker-compose run --rm web python3 manage.py migrate
    
If this command fails the first time because it couldn't 
connect to the DB, wait a couple seconds, and try again.
The Django server doesn't wait for the DB to come alive,
so if it's too fast it'll simply say "Cannot connect to DB".

Afterwards, you can start the application with:

    docker-compose up
    
The application is exposed on port 8000.

[Check out the PyCharm docs](https://www.jetbrains.com/help/pycharm/using-docker-compose-as-a-remote-interpreter.html)
for getting started with Docker Compose in PyCharm.