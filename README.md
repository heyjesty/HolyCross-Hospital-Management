# HolyCross Hospital Management

A hospital website and appointment system built with Django 5.2.

**Patients** can browse departments and doctors, register securely, book 30-minute appointment slots, and track or cancel their bookings from their account.
**Staff** use a dashboard at `/Backend/` to confirm appointments, manage doctors and departments, read contact messages and moderate patient stories.

## Features

| Public website | Staff dashboard (`/Backend/`) |
| --- | --- |
| Responsive, modern design (Bootstrap 5) | Overview with today's schedule, 7-day booking chart, status counts |
| Doctor search by name, department or language | Appointment list with filters, search and one-click status updates |
| Doctor profiles with live slot availability | Doctor and department management (administrators) |
| Booking with validation (no past dates, no double-booking) | Patient directory (administrators) |
| Patient accounts with hashed passwords, profile, history, cancellation | Contact-form inbox, patient-story moderation |
| Printable booking confirmation | Role-based access: staff vs administrator |
| Contact form (stored, optionally emailed), video consultation (optional) | Django admin at `/admin/` |

## Run locally

```bash
python -m venv .venv
.venv\Scripts\activate          # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo       # demo departments, doctors and stories (only if the DB is empty)
python manage.py createsuperuser # your staff/admin login
python manage.py runserver
```

Open http://127.0.0.1:8000. The staff dashboard is at http://127.0.0.1:8000/Backend/.
Optional settings go in a `.env` file (copy `.env.example`).

Run the tests with `python manage.py test`.

## Deploy to Vercel

1. Push this repository to GitHub.
2. In Vercel, choose **Add New → Project** and import the repo. No build settings are needed: `vercel.json` already configures the Python runtime.
3. **Add a database** (recommended). Open **Storage → Create → Neon (Postgres)** and connect it to the project. This sets `DATABASE_URL` / `POSTGRES_URL` automatically. Any Postgres connection string in `DATABASE_URL` also works.
4. Under **Settings → Environment Variables**, add:

   | Variable | Value |
   | --- | --- |
   | `DJANGO_SECRET_KEY` | a long random string: `python -c "import secrets; print(secrets.token_urlsafe(50))"` |
   | `DJANGO_ADMIN_USERNAME` | staff/admin username to create on first start |
   | `DJANGO_ADMIN_PASSWORD` | a strong password |
   | `DJANGO_ALLOWED_HOSTS`, `DJANGO_CSRF_TRUSTED_ORIGINS` | only if you add a custom domain (see `.env.example`) |

5. Deploy. On each cold start the app automatically runs migrations, loads demo data into an empty database and creates the admin account.

> **No database configured?** The site still runs, but on a temporary SQLite database in `/tmp`. A banner warns visitors that data resets. Use this only for previews.

### Things to know about serverless hosting

- **Uploaded images** (new doctor/department/profile photos) are written to temporary storage on Vercel and disappear when the instance recycles. The bundled photos in `media/` are always available. For permanent uploads, connect object storage such as Vercel Blob, S3 or Cloudinary through `django-storages`.
- **Email** is optional. Set `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` (for Gmail, an app password) and `CONTACT_EMAIL` to receive contact-form messages by email. Without them, messages still appear in the dashboard inbox.
- **Video consultation** appears only when `ZEGO_APP_ID` and `ZEGO_SERVER_SECRET` are set. It uses ZegoCloud's test-token mode, which exposes the secret in the browser. That is fine for demos, but production use needs a server-generated token.

## Project structure

```
HospitalManagement/   settings (env-driven), urls, wsgi entry point, Vercel bootstrap
Frontend/             public site: views, forms, templates, static/hc (CSS, JS, images)
Backend/              staff dashboard, Deptdb/Doctordb models, demo fixture, seed_demo command
media/                bundled doctor and department images
vercel.json           Vercel Python runtime configuration
```
