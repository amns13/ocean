#!/bin/sh

echo "Waiting for postgres..."

while ! nc -z $OCEAN_DB_HOST $OCEAN_DB_PORT; do
  sleep 0.1
  echo "Failed to connect postgres.."
done

echo "PostgreSQL started"

python manage.py migrate
python manage.py collectstatic --noinput

if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_USEREMAIL" ]; then
  echo "Creating superuser..."
  python manage.py createsuperuser \
    --noinput \
    --username "$DJANGO_SUPERUSER_USERNAME" \
    --email "$DJANGO_SUPERUSER_USEREMAIL"
  echo "Superuser created!"
fi

exec "$@"
