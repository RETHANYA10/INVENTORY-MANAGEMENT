from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///inventory.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# ---------------- Models ----------------
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200))

class Location(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

class Movement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    from_location_id = db.Column(db.Integer, db.ForeignKey("location.id"), nullable=True)
    to_location_id = db.Column(db.Integer, db.ForeignKey("location.id"), nullable=True)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False)
    qty = db.Column(db.Integer, nullable=False)

    from_location = db.relationship("Location", foreign_keys=[from_location_id])
    to_location = db.relationship("Location", foreign_keys=[to_location_id])
    product = db.relationship("Product")

# ---------------- Routes ----------------

# Home page
@app.route("/")
def index():
    return render_template("base.html")

# Products
@app.route("/products")
def products():
    all_products = Product.query.all()
    return render_template("products.html", products=all_products)

@app.route("/add_product", methods=["GET", "POST"])
def add_product():
    if request.method == "POST":
        name = request.form["name"]
        description = request.form.get("description")
        p = Product(name=name, description=description)
        db.session.add(p)
        db.session.commit()
        return redirect("/products")
    return render_template("add_product.html")

# Locations
@app.route("/locations")
def locations():
    all_locations = Location.query.all()
    return render_template("locations.html", locations=all_locations)

@app.route("/add_location", methods=["GET", "POST"])
def add_location():
    if request.method == "POST":
        name = request.form["name"]
        l = Location(name=name)
        db.session.add(l)
        db.session.commit()
        return redirect("/locations")
    return render_template("add_location.html")

# Movements
@app.route("/movements")
def movements():
    all_movements = Movement.query.order_by(Movement.timestamp.desc()).all()
    return render_template("movements.html", movements=all_movements)

@app.route("/add_movement", methods=["GET", "POST"])
def add_movement():
    products = Product.query.all()
    locations = Location.query.all()
    if request.method == "POST":
        product_id = request.form["product_id"]
        from_location_id = request.form.get("from_location") or None
        to_location_id = request.form.get("to_location") or None
        qty = int(request.form["qty"])
        m = Movement(
            product_id=product_id,
            from_location_id=from_location_id,
            to_location_id=to_location_id,
            qty=qty
        )
        db.session.add(m)
        db.session.commit()
        return redirect("/movements")
    return render_template("add_movement.html", products=products, locations=locations)

# Inventory Report
@app.route("/report")
def report():
    results = []
    products = Product.query.all()
    locations = Location.query.all()
    for p in products:
        for l in locations:
            qty_in = db.session.query(db.func.sum(Movement.qty)).filter_by(product_id=p.id, to_location_id=l.id).scalar() or 0
            qty_out = db.session.query(db.func.sum(Movement.qty)).filter_by(product_id=p.id, from_location_id=l.id).scalar() or 0
            balance = qty_in - qty_out
            if balance != 0:
                results.append({"product": p, "location": l, "qty": balance})
    return render_template("report.html", report=results)

# ---------------- Run App ----------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
