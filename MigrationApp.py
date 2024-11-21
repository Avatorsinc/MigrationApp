# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = "sadcszxc134adcsxzczasda"

# Database configuration
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///migration_app.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# Database models
class Country(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    stores = db.relationship("Store", backref="country", lazy=True)

class Chain(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

class Store(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    country_id = db.Column(db.Integer, db.ForeignKey("country.id"), nullable=False)
    chain_id = db.Column(db.Integer, db.ForeignKey("chain.id"), nullable=True)

class Warehouse(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

class MigrationStatus(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    total_devices = db.Column(db.Integer, nullable=False, default=0)
    migrated_devices = db.Column(db.Integer, nullable=False, default=0)

class Issue(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(50), nullable=False, default="New")  # New, In Progress, Solved

# Initialize the database
with app.app_context():
    db.create_all()

# Seed data (if needed)
with app.app_context():
    if not Warehouse.query.first():
        warehouses = [Warehouse(name="BTG"), Warehouse(name="BSG")]
        db.session.add_all(warehouses)
        db.session.commit()

    if not Chain.query.first():
        chains = [
            Chain(name="Netto"),
            Chain(name="BR"),
            Chain(name="Salling"),
            Chain(name="Carl's Jr"),
            Chain(name="Bilka"),
            Chain(name="Fotex"),
        ]
        db.session.add_all(chains)
        db.session.commit()

    if not Country.query.first():
        poland = Country(name="Poland")
        denmark = Country(name="Denmark")
        germany = Country(name="Germany")
        db.session.add_all([poland, denmark, germany])
        db.session.commit()

        # Add stores for Poland and Germany Netto
        netto_chain = Chain.query.filter_by(name="Netto").first()
        for i in range(705):
            db.session.add(Store(name=f"Poland Netto Store {i+1}", country_id=poland.id, chain_id=netto_chain.id))
        for i in range(364):
            db.session.add(Store(name=f"Germany Netto Store {i+1}", country_id=germany.id, chain_id=netto_chain.id))

        # Add stores for Denmark with the correct counts
        chains = {chain.name: chain.id for chain in Chain.query.all()}  # Get all chains
        denmark_id = denmark.id

        # Bilka: 18 stores
        for i in range(18):
            db.session.add(Store(name=f"Bilka Store {i+1}", country_id=denmark_id, chain_id=chains["Bilka"]))

        # Fotex: 110 stores
        for i in range(110):
            db.session.add(Store(name=f"Fotex Store {i+1}", country_id=denmark_id, chain_id=chains["Fotex"]))

        # Netto: 551 stores
        for i in range(551):
            db.session.add(Store(name=f"Netto Store {i+1}", country_id=denmark_id, chain_id=chains["Netto"]))

        # Salling: 4 stores
        for i in range(4):
            db.session.add(Store(name=f"Salling Store {i+1}", country_id=denmark_id, chain_id=chains["Salling"]))

        # BR: 30 stores
        for i in range(30):
            db.session.add(Store(name=f"BR Store {i+1}", country_id=denmark_id, chain_id=chains["BR"]))

        db.session.commit()

    if not MigrationStatus.query.first():
        migration_status = MigrationStatus(total_devices=12206, migrated_devices=112)
        db.session.add(migration_status)
        db.session.commit()

# Predefined admin user
USERNAME = "sallingdelfi"
PASSWORD = "Password2be16long"

@app.route("/")
def home():
    return redirect(url_for("dashboard"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if username == USERNAME and password == PASSWORD:
            session["logged_in"] = True
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid username or password", "danger")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("logged_in", None)
    flash("You have been logged out", "info")
    return redirect(url_for("dashboard"))

@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    countries = Country.query.all()
    chains = Chain.query.all()
    warehouses = Warehouse.query.all()

    migration_status = MigrationStatus.query.first()
    progress = (migration_status.migrated_devices / migration_status.total_devices) * 100 if migration_status.total_devices > 0 else 0

    # Aggregate total stores per country
    country_totals = []
    for country in countries:
        total_stores = Store.query.filter_by(country_id=country.id).count()
        country_totals.append({"country": country.name, "total_stores": total_stores})

    # Group data for each section
    dashboard_data = []
    for country in countries:
        for chain in chains:
            stores_count = Store.query.filter_by(country_id=country.id, chain_id=chain.id).count()
            if stores_count > 0:
                dashboard_data.append({"country": country.name, "chain": chain.name, "stores": stores_count})

    issues = Issue.query.all()

    return render_template(
        "dashboard.html",
        country_totals=country_totals,
        dashboard_data=dashboard_data,
        warehouses=warehouses,
        migration_status=migration_status,
        progress=progress,
        issues=issues,
        logged_in="logged_in" in session
    )


    # Group data for each section
    dashboard_data = []
    for country in countries:
        for chain in chains:
            stores_count = Store.query.filter_by(country_id=country.id, chain_id=chain.id).count()
            if stores_count > 0:
                dashboard_data.append({"country": country.name, "chain": chain.name, "stores": stores_count})

    issues = Issue.query.all()

    return render_template(
        "dashboard.html",
        dashboard_data=dashboard_data,
        warehouses=warehouses,
        migration_status=migration_status,
        progress=progress,
        issues=issues,
        logged_in="logged_in" in session
    )


@app.route("/admin", methods=["GET", "POST"])
def admin():
    if "logged_in" not in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        action = request.form["action"]
        if action == "add_issue":
            title = request.form["title"]
            if title:
                db.session.add(Issue(title=title, status="New"))
                db.session.commit()
                flash(f"Issue '{title}' added successfully!", "success")
        elif action == "update_status":
            issue_id = int(request.form["issue_id"])
            new_status = request.form["status"]
            issue = Issue.query.get(issue_id)
            if issue:
                issue.status = new_status
                db.session.commit()
                flash(f"Issue '{issue.title}' updated to '{new_status}'!", "success")

    issues = Issue.query.all()
    return render_template("admin.html", issues=issues)

if __name__ == "__main__":
    app.run(debug=True)
