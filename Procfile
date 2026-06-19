web: cd jds_web && python manage.py collectstatic --noinput && gunicorn jds_web.wsgi:application --workers=2 --threads=2 --timeout=120 --bind=0.0.0.0:$PORT
