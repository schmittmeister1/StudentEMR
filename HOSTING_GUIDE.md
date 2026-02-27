# Hosting PTA EMR Playground as a Website (Students Access via Browser)

This app is a Flask web application. To make it accessible as a **website**, you deploy it to a server that runs 24/7.

## Important safety note
This is an **educational sandbox** and is **not HIPAA compliant**. Use **synthetic data only** and do not enter real patient information.

---

## Step 0 — Add the production hosting files (this patch)

Copy these files into the **same folder as `app.py`**:

- `wsgi.py`
- `Procfile` (optional; useful for Heroku-style platforms)
- (optional) `Dockerfile`
- Update `requirements.txt` to include the packages listed in `requirements_hosting_additions.txt`

---

## Step 1 — Use a real database (recommended)

For a public/hosted site, use **PostgreSQL** instead of SQLite.

Your app already supports this:
- Set the environment variable `DATABASE_URL` to a Postgres connection string.
- Example formats typically start with `postgres://` or `postgresql://`.

---

## Step 2 — Set required environment variables

Set these on your hosting provider:

- `SECRET_KEY` = a long random value (at least 32 chars)
- `DATABASE_URL` = your hosted Postgres URL

Optional / provider-specific:
- `PORT` is usually set automatically by the platform

---

## Step 3 — Production start command

Use gunicorn (instead of `python app.py`):

### Build command
    pip install -r requirements.txt

### Start command
    gunicorn wsgi:app --bind 0.0.0.0:$PORT

---

## Option A — Cloud-hosted (recommended for students anywhere)

You can use any provider that supports Python web apps. Common choices include:

- Render / Railway / Fly.io / Azure App Service / AWS Elastic Beanstalk / DigitalOcean App Platform

Provider-specific steps differ slightly, but the pattern is the same:

1. Put your project in a Git repo (GitHub/GitLab).
2. Create a new “Web App / Web Service”.
3. Attach a Postgres database.
4. Set `SECRET_KEY` and `DATABASE_URL`.
5. Use build/start commands above.
6. Deploy.
7. You’ll get a URL like `https://your-app-name.provider.com`.

### After deployment
- Log in with the instructor account
- Immediately create your own admin account
- Change default passwords or delete default accounts

---

## Option B — Campus / classroom network website (no cloud)

If you want students to access it **only on campus Wi‑Fi**:

1. Run the server on an instructor workstation on the same network.
2. Start Flask listening on all network interfaces:
    python app.py

3. In `app.py` (bottom), change host to `0.0.0.0`:
    app.run(debug=True, host="0.0.0.0", port=5000)

4. Find your computer’s local IP address (example: `192.168.1.50`)
5. Students browse to:
    http://192.168.1.50:5000

**Downside:** the server must stay running, and campus firewall rules may block access unless IT opens the port.

---

## Recommended classroom security controls

If you deploy on the public internet:

- Use strong passwords and rotate them each term
- Do not allow anonymous registration
- Restrict who can create users (admin/instructor only)
- Consider putting the site behind a VPN, SSO, or an IP allowlist if your IT department supports it

---

## Troubleshooting

### App deploys but shows “Application error”
Common causes:
- Missing `SECRET_KEY`
- Missing/invalid `DATABASE_URL`
- Start command points to wrong WSGI module

### Data disappears after redeploy
This happens if you used SQLite on an ephemeral filesystem. Use Postgres or a persistent disk.

