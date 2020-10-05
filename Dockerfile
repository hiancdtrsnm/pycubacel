FROM python:3.8

RUN mkdir /code
WORKDIR /code

COPY pyproject.toml /code
RUN pip install poetry

RUN poetry install


COPY . /code/


