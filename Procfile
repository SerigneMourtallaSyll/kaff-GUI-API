# Railway Procfile - defines how to run the application

# Web process: run Gunicorn with optimal settings for Railway
web: python manage.py migrate --noinput && python manage.py collectstatic --noinput && gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 60 --access-logfile - --error-logfile - --log-level info
