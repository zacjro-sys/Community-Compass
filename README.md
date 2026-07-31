<img width="1470" height="834" alt="image" src="https://github.com/user-attachments/assets/90056cd4-5b42-4e9b-acdf-fe970047e9b8" />

# Community Compass

Community Compass helps people find nearby community services. Things like food banks, shelters, clinics, legal aid, job help, and education programs.

## Why it is interesting

People experiencing homelessness or financial hardships often need to find resources such as food or healthcare quickly, but information about such resources is often incomplete or just scattered across multiple websites. Community Compass compiles all available information on these resources into a searchable and map-based web app where all resources are organised by category, allowing for easy access.

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

2. Create a virtual environment:

macOS / Linux:

```bash
python3 -m venv .venv
```

Windows (PowerShell):

```powershell
python -m venv .venv
```

3. Activate the virtual environment and install dependencies:

macOS / Linux:

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

Windows (PowerShell):

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

This installs everything listed in `requirements.txt`: Flask 3.0.3 and Flask-SQLAlchemy 3.1.1.

4. (Optional) Set an admin password for the `/admin` moderation queue. If you skip this, it defaults to `password`.

macOS / Linux:

```bash
export ADMIN_PASSWORD=your-password-here
```

Windows (PowerShell):

```powershell
$env:ADMIN_PASSWORD = "your-password-here"
```

5. Start the app:

```bash
python app.py
```

6. Open http://127.0.0.1:5000 in your browser.

## Project layout

Everything below lives inside `community-compass-simple/`:

- `app.py` - the entire Flask app: routes, the `Resource` model, search/filter logic, admin moderation, and CSV seeding
- `data/resources.csv` - source data used to seed the database on first run
- `community_compass.db` - SQLite database (created automatically, persists between restarts)
- `templates/` - Jinja templates (`base.html`, `home.html`, `resources.html`, `resource_detail.html`, `suggest_resource.html`, `admin_login.html`, `admin_pending.html`)
- `static/` - CSS, the Leaflet map JS, and category icons
- `requirements.txt` - pinned dependencies (Flask, Flask-SQLAlchemy)

## Map-based browsing

On the resources page, a map is displayed with different resources pinned.

<img width="1470" height="834" alt="image" src="https://github.com/user-attachments/assets/98737f52-20c1-462a-9f47-90317eff1284" />

## Point requirements completed

This project satisfies all 3 point requirements.

1. Persistent data storage - SQLite via Flask-SQLAlchemy

   - Resource model: app.py
   - Database is seeded once from resources.csv via seed_from_csv(), and is maintained after restarts in community_compass.db

2. Meaningful POST usage - POST endpoints trigger real state changes

   - /resources/suggest - validates required fields, then writes the new resource to the database.
   - /admin/resources/`<id>`/approve - approves the resource and makes it public
   - /admin/resources/`<id>`/reject - rejects the resource and does not make it public
<img width="1470" height="834" alt="image" src="https://github.com/user-attachments/assets/a52c327f-0a38-4535-a6c8-2319bb9c4114" />

3. Public Hosting - Community Compass is publicly reachable via Render

   - Live at: https://community-compass-uxq8.onrender.com/
   - Hosted using gunicorn as the production WSGI server, with the app configured to read its port from Render's PORT environment variable.

## Known Limitations

1. Most data is fictional and is only serving as a placeholder, so it is not a representation of real coverage
2. All admins share a single password to access the admin panel. It is not possible to distinguish between admins and there is no record of which admin approved/rejected a resource.
3. There are no validation checks to confirm the format of phone number or website when submitting a new resource.
4. It is also not possible to make changes to a resource once it has already been submitted. The only way to make changes is to delete the resource and resubmit.
5. Search is a substring match on name, description, and city so it will show no results unless that exact word appears in the listing.
