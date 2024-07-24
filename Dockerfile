# --------- requirements ---------
# FROM python:3.12 as requirements-stage
FROM docker.io/python:3.12.3-slim-bookworm as requirements-stage

WORKDIR /tmp

RUN pip install poetry

COPY ./pyproject.toml ./poetry.lock* /tmp/

RUN poetry export -f requirements.txt --output requirements.txt --without-hashes


# --------- final image build ---------
FROM requirements-stage as python

WORKDIR /code

# Install required system dependencies
RUN apt-get update && apt-get install --no-install-recommends -y \
  # psycopg dependencies
  libpq-dev \
  # Translations dependencies
  gettext 


COPY --from=requirements-stage /tmp/requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY . /code

COPY scripts/entrypoint /entrypoint
RUN sed -i 's/\r$//g' /entrypoint
RUN chmod +x /entrypoint

COPY scripts/start /start
RUN sed -i 's/\r$//g' /start
RUN chmod +x /start

# Set the entry point
ENTRYPOINT ["/entrypoint"]
