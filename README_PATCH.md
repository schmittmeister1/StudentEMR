PTA EMR Hosting Patch
=====================

This zip contains production/deployment helper files.

How to use:
1) Copy contents into your EMR project folder (where app.py lives)
2) Add gunicorn + psycopg2-binary to requirements.txt (see requirements_hosting_additions.txt)
3) Deploy to a Python-compatible web host with Postgres
4) Start with: gunicorn wsgi:app --bind 0.0.0.0:$PORT

See HOSTING_GUIDE.md for details.
