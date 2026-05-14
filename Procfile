# Railway Procfile - defines how to run the application

# Release phase: run migrations and collect static files
release: python manage.py migrate --noinput && python manage.py collectstatic --noinput

# Web process: run Gunicorn with optimal settings for Railway
web: gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 60 --access-logfile - --error-logfile - --log-level info
