FROM python:3.9.7-slim-bullseye

# Set environment variables
ENV PIP_DISABLE_PIP_VERSION_CHECK 1
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /code

# Install dependencies
COPY . .
RUN pip install -r requirements.txt

CMD python manage.py runserver 0.0.0.0:80
EXPOSE 8000
