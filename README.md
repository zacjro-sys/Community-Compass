# Community Compass

Community Compass helps people find nearby community services. Things like food banks, shelters, clinics, legal aid, job help, and education programs.

## What it does right now

You can search resources by keyword. You can filter by category, city, or state. You can see results on an interactive map. You can click into a resource for its full details: address, phone, hours, and website. You can suggest a new resource for review. There's also an admin login at `/admin/login` for approving or rejecting suggested resources.
Most of the data is fictional demo content. A handful of Colorado resources are real organizations. We verified name, address, phone, and website as part of the data pull, but hours and contact details can change. **Do not treat this site as a reliable source for aid.**

## Requirements

- Python 3.9 or newer
- pip
- The app code lives in the `community-compass-simple/` folder

## Running it locally

1. Move into the app folder:

```bash
cd community-compass-simple
```

2. Create a virtual environment and install dependencies:

macOS / Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Windows (PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

This installs everything listed in `requirements.txt`: Flask 3.0.3 and Flask-SQLAlchemy 3.1.1.

3. (Optional) Set an admin password for the `/admin` moderation queue. If you skip this, it defaults to `password`.

macOS / Linux:

```bash
export ADMIN_PASSWORD=your-password-here
```

Windows (PowerShell):

```powershell
$env:ADMIN_PASSWORD = "your-password-here"
```

4. Start the app:

```bash
python app.py
```

5. Open http://127.0.0.1:5000 in your browser.

## Project layout

Everything below lives inside `community-compass-simple/`:

- `app.py` - the entire Flask app: routes, the `Resource` model, search/filter logic, admin moderation, and CSV seeding
- `data/resources.csv` - source data used to seed the database on first run
- `community_compass.db` - SQLite database (created automatically, persists between restarts)
- `templates/` - Jinja templates (`base.html`, `home.html`, `resources.html`, `resource_detail.html`, `suggest_resource.html`, `admin_login.html`, `admin_pending.html`)
- `static/` - CSS, the Leaflet map JS, and category icons
- `requirements.txt` - pinned dependencies (Flask, Flask-SQLAlchemy)

## Point requirements completed

This project satisfies all 3 point requirements.

1. Persistent data storage - SQLite via Flask-SQLAlchemy

   - Resource model: app.py
   - Database is seeded once from resources.csv via seed_from_csv(), and is maintained after restarts in community_compass.db

2. Meaningful POST usage - POST endpoints trigger real state changes

   - /resource/suggest - validates required fields, then writes the new resource to the database.
   - /admin/resources/<id<id>>/approve - approves the resource and makes it public
   - /admin/resources/<id<id>>/reject - rejects the resource and does not make it public

3. Public Hosting

   - Our web app (Community Compass) is live
   - It can be accessed using the following link: https://community-compass-uxq8.onrender.com/

## Known Limitations

1. Most data is fictional and is only serving as a placeholder, so it is not a representation of real coverage
2. All admins share a single password to access the admin panel. It is not possible to distinguish between admins and there is no record of which admin approved/rejected a resource.
3. There are no validation checks to confirm the format of phone number or website when submitting a new resource.
4. It is also not possible to make changes to a resource once it has already been submitted. The only way to make changes is to delete the resource and resubmit. 
