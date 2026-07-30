import csv
import os
from functools import wraps
from math import atan2, cos, radians, sin, sqrt
from pathlib import Path
from flask import Flask, flash, jsonify, redirect, render_template, request, session, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import inspect, text

BASE_DIR = Path(__file__).resolve().parent

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{BASE_DIR / 'community_compass.db'}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# Only needed so flash() can store a one-time message in the session cookie.
app.config['SECRET_KEY'] = 'community-compass-dev-key'

# Password for the /admin moderation queue.
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'password')

EARTH_RADIUS_MILES = 3958.8

db = SQLAlchemy(app)

CATEGORIES = {
    'Food': 'food',
    'Shelter': 'shelter',
    'Healthcare': 'healthcare',
    'Legal': 'legal',
    'Employment': 'employment',
    'Education': 'education'
}

US_STATES = {
    'AL': 'Alabama', 'AK': 'Alaska', 'AZ': 'Arizona', 'AR': 'Arkansas',
    'CA': 'California', 'CO': 'Colorado', 'CT': 'Connecticut', 'DE': 'Delaware',
    'FL': 'Florida', 'GA': 'Georgia', 'HI': 'Hawaii', 'ID': 'Idaho',
    'IL': 'Illinois', 'IN': 'Indiana', 'IA': 'Iowa', 'KS': 'Kansas',
    'KY': 'Kentucky', 'LA': 'Louisiana', 'ME': 'Maine', 'MD': 'Maryland',
    'MA': 'Massachusetts', 'MI': 'Michigan', 'MN': 'Minnesota', 'MS': 'Mississippi',
    'MO': 'Missouri', 'MT': 'Montana', 'NE': 'Nebraska', 'NV': 'Nevada',
    'NH': 'New Hampshire', 'NJ': 'New Jersey', 'NM': 'New Mexico', 'NY': 'New York',
    'NC': 'North Carolina', 'ND': 'North Dakota', 'OH': 'Ohio', 'OK': 'Oklahoma',
    'OR': 'Oregon', 'PA': 'Pennsylvania', 'RI': 'Rhode Island', 'SC': 'South Carolina',
    'SD': 'South Dakota', 'TN': 'Tennessee', 'TX': 'Texas', 'UT': 'Utah',
    'VT': 'Vermont', 'VA': 'Virginia', 'WA': 'Washington', 'WV': 'West Virginia',
    'WI': 'Wisconsin', 'WY': 'Wyoming'
}


class Resource(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)
    address = db.Column(db.String(255))
    city = db.Column(db.String(80))
    state = db.Column(db.String(80))
    phone = db.Column(db.String(50))
    website = db.Column(db.String(255))
    hours = db.Column(db.String(100))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    # Seeded/demo data is auto-approved (default True). Visitor-submitted
    # resources are explicitly set to False in suggest_resource() below and
    # sit in the /admin queue until a moderator approves them.
    is_approved = db.Column(db.Boolean, nullable=False, default=True)

    @property
    def icon(self):
        return CATEGORIES.get(self.category)


def ensure_schema():
    """Lightweight migration: adds is_approved to an existing SQLite db that
    predates this column, so you don't have to delete community_compass.db
    to pick up the moderation feature."""
    inspector = inspect(db.engine)
    if 'resource' not in inspector.get_table_names():
        return
    columns = {col['name'] for col in inspector.get_columns('resource')}
    if 'is_approved' not in columns:
        with db.engine.connect() as conn:
            conn.execute(text('ALTER TABLE resource ADD COLUMN is_approved BOOLEAN DEFAULT 1'))
            conn.commit()


def seed_from_csv():
    if Resource.query.first():
        return

    csv_path = BASE_DIR / 'data' / 'resources.csv'
    with csv_path.open(newline='', encoding='utf-8') as handle:
        for row in csv.DictReader(handle):
            db.session.add(Resource(
                name=row['name'],
                category=row['category'],
                description=row['description'],
                address=row['address'],
                city=row['city'],
                state=row['state'],
                phone=row['phone'],
                website=row['website'],
                hours=row['hours'],
                latitude=float(row['latitude']),
                longitude=float(row['longitude']),
                is_approved=True,
            ))
    db.session.commit()


def filtered_resources(q, category, include_pending=False):
    query = Resource.query
    if not include_pending:
        query = query.filter_by(is_approved=True)
    if q:
        like = f"%{q}%"
        query = query.filter(
            Resource.name.ilike(like)
            | Resource.description.ilike(like)
            | Resource.city.ilike(like)
        )
    if category:
        query = query.filter_by(category=category)
    return query.order_by(Resource.name)


def parse_optional_float(raw_value):
    raw_value = (raw_value or '').strip()
    if not raw_value:
        return None
    try:
        return float(raw_value)
    except ValueError:
        return None


def haversine_miles(lat1, lon1, lat2, lon2):
    """Great-circle distance between two lat/lon points, in miles."""
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return EARTH_RADIUS_MILES * c


def sort_by_distance(resources, lat, lon):
    """Attach a .distance_miles attribute to each resource and return the
    list sorted nearest-first. Resources without coordinates sort last."""
    decorated = []
    for resource in resources:
        if resource.latitude is None or resource.longitude is None:
            resource.distance_miles = None
            decorated.append((float('inf'), resource))
            continue
        distance = haversine_miles(lat, lon, resource.latitude, resource.longitude)
        resource.distance_miles = round(distance, 1)
        decorated.append((distance, resource))
    decorated.sort(key=lambda pair: pair[0])
    return [resource for _, resource in decorated]


def admin_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if not session.get('is_admin'):
            flash('Log in to access the moderation queue.', 'danger')
            return redirect(url_for('admin_login'))
        return view(*args, **kwargs)
    return wrapped_view


@app.route('/')
def home():
    featured = Resource.query.filter_by(is_approved=True).order_by(Resource.name).limit(3).all()
    return render_template('home.html', categories=CATEGORIES, featured=featured)


@app.route('/resources')
def list_resources():
    q = request.args.get('q', '').strip()
    category = request.args.get('category', '').strip()
    lat = parse_optional_float(request.args.get('lat'))
    lon = parse_optional_float(request.args.get('lon'))

    resources = filtered_resources(q, category).all()
    sorted_by_distance = lat is not None and lon is not None
    if sorted_by_distance:
        resources = sort_by_distance(resources, lat, lon)

    return render_template(
        'resources.html',
        resources=resources,
        categories=CATEGORIES,
        q=q,
        selected_category=category,
        sorted_by_distance=sorted_by_distance,
        lat=lat,
        lon=lon,
    )


@app.route('/resources/<int:resource_id>')
def resource_detail(resource_id):
    resource = Resource.query.get_or_404(resource_id)
    return render_template('resource_detail.html', resource=resource)


@app.route('/api/map-data')
def map_data():
    # Same filters as /resources, but returns JSON for the Leaflet map (map.js).
    q = request.args.get('q', '').strip()
    category = request.args.get('category', '').strip()
    lat = parse_optional_float(request.args.get('lat'))
    lon = parse_optional_float(request.args.get('lon'))

    resources = filtered_resources(q, category).all()
    if lat is not None and lon is not None:
        resources = sort_by_distance(resources, lat, lon)

    return jsonify([
        {
            'id': r.id,
            'name': r.name,
            'category': r.category,
            'icon': r.icon,
            'city': r.city,
            'state': r.state,
            'latitude': r.latitude,
            'longitude': r.longitude,
            'distance_miles': getattr(r, 'distance_miles', None),
        }
        for r in resources
    ])


@app.route('/resources/suggest', methods=['GET', 'POST'])
def suggest_resource():
    """POST endpoint: a visitor submits a new community resource and it is
    written to the database (a real state change, not an echo form). GET
    just renders the empty form."""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        category = request.form.get('category', '').strip()
        description = request.form.get('description', '').strip()
        address = request.form.get('address', '').strip()
        city = request.form.get('city', '').strip()
        state = request.form.get('state', '').strip()
        phone = request.form.get('phone', '').strip()
        website = request.form.get('website', '').strip()
        hours = request.form.get('hours', '').strip()
        latitude = parse_optional_float(request.form.get('latitude'))
        longitude = parse_optional_float(request.form.get('longitude'))

        errors = []
        if not name:
            errors.append('Name is required.')
        if category not in CATEGORIES:
            errors.append('Please choose a valid category.')
        if not description:
            errors.append('Description is required.')
        if not city:
            errors.append('City is required.')
        if not state:
            errors.append('State is required.')

        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template(
                'suggest_resource.html',
                categories=CATEGORIES,
                us_states=US_STATES,
                form=request.form,
            ), 400

        resource = Resource(
            name=name,
            category=category,
            description=description,
            address=address or None,
            city=city,
            state=state,
            phone=phone or None,
            website=website or None,
            hours=hours or None,
            latitude=latitude,
            longitude=longitude,
            is_approved=False,
        )
        db.session.add(resource)
        db.session.commit()

        flash(
            f'"{resource.name}" was submitted and is awaiting review before it '
            'appears in the directory. Thanks for the tip!',
            'success',
        )
        return redirect(url_for('resource_detail', resource_id=resource.id))

    return render_template(
        'suggest_resource.html',
        categories=CATEGORIES,
        us_states=US_STATES,
        form={},
    )


@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if session.get('is_admin'):
        return redirect(url_for('admin_pending'))

    if request.method == 'POST':
        if request.form.get('password') == ADMIN_PASSWORD:
            session['is_admin'] = True
            flash('Logged in.', 'success')
            return redirect(url_for('admin_pending'))
        flash('Incorrect password.', 'danger')

    return render_template('admin_login.html')


@app.route('/admin/logout')
def admin_logout():
    session.pop('is_admin', None)
    flash('Logged out.', 'info')
    return redirect(url_for('home'))


@app.route('/admin')
@admin_required
def admin_pending():
    pending = Resource.query.filter_by(is_approved=False).order_by(Resource.id.desc()).all()
    published = Resource.query.filter_by(is_approved=True).order_by(Resource.name).all()
    return render_template('admin_pending.html', pending=pending, published=published, categories=CATEGORIES)


@app.route('/admin/resources/<int:resource_id>/approve', methods=['POST'])
@admin_required
def admin_approve(resource_id):
    resource = Resource.query.get_or_404(resource_id)
    resource.is_approved = True
    db.session.commit()
    flash(f'"{resource.name}" approved and published.', 'success')
    return redirect(url_for('admin_pending'))


@app.route('/admin/resources/<int:resource_id>/reject', methods=['POST'])
@admin_required
def admin_reject(resource_id):
    """Deletes a resource outright. Used both to reject a pending submission
    and to remove an already-published resource (e.g. spam or test entries
    that slipped through approval) from the "Published resources" list."""
    resource = Resource.query.get_or_404(resource_id)
    name = resource.name
    was_published = resource.is_approved
    db.session.delete(resource)
    db.session.commit()
    if was_published:
        flash(f'"{name}" was deleted from the directory.', 'info')
    else:
        flash(f'"{name}" rejected and removed.', 'info')
    return redirect(url_for('admin_pending'))


with app.app_context():
    db.create_all()
    ensure_schema()
    seed_from_csv()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', '0') == '1'
    app.run(host='0.0.0.0', port=port, debug=debug)
