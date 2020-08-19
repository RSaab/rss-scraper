



# Description

- [x] Follow and unfollow multiple feeds
- [x] List all feeds registered by them
- [x] List feed items belonging to one feed
- [x] Mark items as read
- [x] Filter read/unread feed items per feed and globally, ordered by the date of the last update
- [x] Force a feed update
- [x] Feeds (followed) (and feed items) are updated asynchronously in the background using Dramatiq
- [x] A back-off mechanism for feed fetching
	- [x] If a feed fails to be updated, the system should fall back for a while.
	- [x] After a certain amount of failed tries, the system should stop updating the feed automatically.
	- [x] Users are notified and able to retry the feed update if it is stalled after these failed tries.
- [x] pagination

# Documentation

The application is packaged in docker containers and uses docker-compose for launching all services.

It consists of the following services:
	- RSS Feeder App which holds the functionality API,
	- Database (PostgreSQL for production and docker developmet and sqlite for quick native prototyping)
	- RabbitMQ  for async functions handled by Dramatiq
	- Celery for running scheduled tasks 

The project API documentation is written in swagger yaml format and can be viewed within the swagger-ui platform after downloading the schema.yaml from the server on the following endpoint `/static/api_schema.yaml` 

# How To Run

The root directory of the project contains 4 shell scripts for getting the app up and running in docker containers using docker-compose. 

Once the containers are started, you can use the "createsuperuser.sh" script to create a super user that will allow you to interact with the API from the Swagger-UI platform.

The api is by defualt available on: `localhost:8000/api/v1/`

#### Development
 To start: ` ./start_development.sh`
To stop: `./stop_development.sh`

#### Production
Includes an nginx reverse proxy for load balancing
To start: `./start_production.sh`
To stop:`./stop_production.sh`

#### Creating a super user for manual testing
Run the `./createsuperuser.sh` script and enter the user details

## PyTest

### test cases
Tests are written using pytest and can be run natively by installing the project requirements through pip within the "app" directory of the project

```
pip install -r requirements.txt

pytest
```

## Settings

The project has configurable options that are set via environment files passed to the docker-compose start command. Two files are provided, .env.dev for the development setup and .env.prod for production setup

- DEBUG
- SECRET_KEY 
- DJANGO_ALLOWED_HOSTS
- SQL_ENGINE
- SQL_DATABASE
- SQL_USER
- SQL_PASSWORD
- SQL_HOST
- SQL_PORT
- DATABASE
- DRAMATIQ_BROKER_URL
- DRAMATIQ_BROKER

## ToDo:

- [ ] use HTTPS and SSL certifiates for nginx production setup
- [ ] use logging library andl Link container logs to disk files
- [ ] use epoch timestamps for all date/time fields
- [ ] Swagger-UI (for now it simply serves the ".yaml" schema file)
	- [ ] integrate full swagger-ui serving, OR
	- [ ] serve serialized yaml file for use with online demo version on swagger-UI