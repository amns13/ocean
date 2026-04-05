# builder stage
FROM python:3.14.3-slim as builder

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /usr/src/app

RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libpq-dev

RUN pip install --upgrade pip
COPY ./requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /usr/src/app/wheels -r requirements.txt

# final stage
FROM python:3.14.3-slim

RUN mkdir -p /home/app

# create the app user
RUN addgroup --system app && adduser --system --group app

# create the appropriate directories
ENV HOME=/home/app
ENV APP_HOME=/home/app/backend
RUN mkdir $APP_HOME
WORKDIR $APP_HOME

RUN apt-get update && apt-get install -y --no-install-recommends netcat-openbsd gcc libpq-dev
COPY --from=builder /usr/src/app/wheels /wheels
COPY --from=builder /usr/src/app/requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache gunicorn
RUN pip install --no-cache /wheels/*

COPY ./entrypoint.sh .
RUN chmod +x  $APP_HOME/entrypoint.sh

# copy project
COPY . $APP_HOME

# chown all the files to the app user
RUN chown -R app:app $HOME

# change to the app user
USER app
RUN mkdir $APP_HOME/staticfiles
# RUN chown -R app:app $APP_HOME/staticfiles
ENTRYPOINT ["/home/app/backend/entrypoint.sh"]

