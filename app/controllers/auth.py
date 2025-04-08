from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.models.user import User
from app import db, bcrypt
from flask_login import login_user, logout_user

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        # Get form data
        prenom = request.form["prenom"]
        nom = request.form["nom"]
        age = request.form["age"]
        email = request.form["email"]
        telephone = request.form["telephone"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        # Validate password match
        if password != confirm_password:
            flash("Passwords do not match", "danger")
            return render_template("auth/signup.html")

        # Check if email already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("Email already registered", "danger")
            return render_template("auth/signup.html")

        # Create new user
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        user = User(
            prenom=prenom,
            nom=nom,
            age=int(age) if age else None,
            email=email,
            telephone=telephone,
            mot_de_passe=hashed_password
        )

        db.session.add(user)
        db.session.commit()

        flash("Registration successful! Please login.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/signup.html")

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        user = User.query.filter_by(email=email).first()

        if user and bcrypt.check_password_hash(user.mot_de_passe, password):
            login_user(user)
            return redirect(url_for("task.calendar"))

        flash("Invalid credentials", "danger")

    return render_template("auth/login.html")

@auth_bp.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("auth.login"))
