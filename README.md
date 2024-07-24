# User Recommendation System

This is a Django-based web application for a user recommendation system, which uses PostgreSQL as the database and provides a REST API endpoint for user recommendations.

## Table of Contents

- [Getting Started](#getting-started)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Running the Application](#running-the-application)
- [Running Tests](#running-tests)
- [Environment Variables](#environment-variables)
- [Contributing](#contributing)
- [License](#license)

## Getting Started

Follow these instructions to get a copy of the project up and running on your local machine for development and testing purposes.

### Prerequisites

- [Docker](https://www.docker.com/products/docker-desktop) installed on your machine.
- [Docker Compose](https://docs.docker.com/compose/install/) installed on your machine.

### Installation

1. **Clone the repository:**
    ```bash
    git clone https://github.com/gr1nch3/user_recommendation.git
    cd user_recommendation
    ```

2. **Set up environment variables:**

    Create a `.env` file in the root directory of the project and add the following environment variables:

    ```env
    POSTGRES_HOST=db
    POSTGRES_PORT=5432
    POSTGRES_DB=recdb
    POSTGRES_USER=postgres
    POSTGRES_PASSWORD=insecure-postgres
    DJANGO_DEBUG=True
    ```

### Running the Application

1. **Build and run the Docker containers:**
    ```bash
    docker compose up build
    ```

    This command will build the Docker images and start the containers for the web application, PostgreSQL database, and pgAdmin.

2. **Apply database migrations:**
    ```bash
    docker compose run --rm web python manage.py migrate
    ```

3. **Import Data to the database:**
	There are .txt files that contains filtered data in the  `filtered/*` folder. There is a file for user, tweet and a hashtag table for relational purposes. To populate the data in the database, use the following commands:
	```bash
	# command to populate the user database (do this first)
	docker compose exec web python manage.py populate_users
	
	# next command to populate the tweets
	docker compose exec web python manage.py populate_tweets

	# command to populate the hashtags
	docker compose exec web python manage.py populate_hashtags

	# command to add popular hashtags to ensure better recomendation
	docker compose exec web python manage.py update_hashtags
	```
	
	The `malformed_duplicate_filter.py` file contains code to generate the files in the `filtered` folder from the query2_ref.txt file in the `challenge/dataset/*`	folder.  You can delete the files from the filtered folder and generate new ones should you ever feel the need to.

5. **Access the application:**

    The application will be accessible at `http://localhost:8000`.
	The endpoint for the user recommendation test should be like:
	```
	GET http://localhost:8000/q2?user_id=102482331&type=both&phrase=una&hashtag=%23RE
	```

5. **Access pgAdmin:**

    pgAdmin will be accessible at `http://localhost:5050`. Use the following credentials to log in:
    - Email: `admin@example.com`
    - Password: `admin`

### Running Tests

To run the tests, execute the following command:
```bash
docker compose exec web python manage.py test
```
