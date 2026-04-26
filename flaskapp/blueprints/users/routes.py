from flask import Blueprint, flash, redirect, render_template, request, url_for, session
from flask_login import current_user, login_required, login_user, logout_user
from flaskapp import bcrypt, db
from flaskapp.blueprints.users.forms import (
    LoginForm,
    RegistrationForm,
    RequestResetForm,
    ResetPasswordForm,
    UpdateAccountForm,
)
from flaskapp.blueprints.users.utils import save_picture, send_reset_email
from flaskapp.models import User
from flaskapp.utils import profile_path
from datetime import datetime

users = Blueprint("users", __name__)


# =========================
# REGISTER
# =========================
@users.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        if session.get("user_type") == "admin":
            return redirect(url_for("admin.dashboard"))
        return redirect(url_for("paper_gen.select_program"))

    form = RegistrationForm()

    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(
            form.password.data
        ).decode("utf-8")

        user = User(
            username=form.username.data,
            email=form.email.data,
            password=hashed_password,
            is_approved=False,  # Set to pending approval
            approval_requested_at=datetime.utcnow(),
        )

        db.session.add(user)
        db.session.commit()

        flash("Your account has been created! Please wait for admin approval before logging in.", "info")
        return redirect(url_for("users.login"))

    return render_template(
        "users/register.html",
        title="Register",
        form=form,
        css_files=["css/users/register.css"],
        js_files=["js/users/register.js"],
        btn_name="Back",
    )


# =========================
# LOGIN
# =========================
@users.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        if session.get("user_type") == "admin":
            return redirect(url_for("admin.dashboard"))
        return redirect(url_for("paper_gen.select_program"))

    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()

        if user and bcrypt.check_password_hash(user.password, form.password.data):
            # Check if user is approved
            if not user.is_approved:
                flash("Your account is pending admin approval. Please wait for an administrator to approve your account.", "warning")
                return render_template(
                    "users/login.html",
                    title="Login",
                    form=form,
                    css_files=["css/users/login.css"],
                    js_files=["js/users/login.js"],
                    btn_name="Back",
                )
            
            login_user(user, remember=form.remember.data)
            session["user_type"] = "user"

            next_page = request.args.get("next")

            if next_page:
                return redirect(next_page)

            return redirect(url_for("paper_gen.select_program"))

        flash("Login Unsuccessful. Please check email and password.", "danger")

    return render_template(
        "users/login.html",
        title="Login",
        form=form,
        css_files=["css/users/login.css"],
        js_files=["js/users/login.js"],
        btn_name="Back",
    )


# =========================
# LOGOUT
# =========================
@users.route("/logout")
@login_required
def logout():
    logout_user()
    session.pop("user_type", None)
    return redirect(url_for("main.index"))


# =========================
# ACCOUNT
# =========================
@users.route("/account", methods=["GET", "POST"])
@login_required
def account():
    if session.get("user_type") != "user":
        flash("Access denied.", "danger")
        return redirect(url_for("main.index"))

    form = UpdateAccountForm()

    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file

        current_user.username = form.username.data
        current_user.email = form.email.data

        db.session.commit()
        flash("Your account has been updated!", "success")
        return redirect(url_for("users.account"))

    form.username.data = current_user.username
    form.email.data = current_user.email
    image_file = profile_path()

    return render_template(
        "users/account.html",
        title="Account",
        css_files=["css/base.css", "css/users/accounts.css"],
        image_file=image_file,
        form=form,
        js_files=["js/users/account.js"],
    )


# =========================
# RESET PASSWORD REQUEST
# =========================
@users.route("/reset_password", methods=["GET", "POST"])
def reset_request():
    if current_user.is_authenticated:
        if session.get("user_type") == "admin":
            return redirect(url_for("admin.dashboard"))
        return redirect(url_for("paper_gen.select_program"))

    form = RequestResetForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()

        if user:
            send_reset_email(user)

        flash(
            "If your email exists, a reset link has been sent.",
            "info",
        )
        return redirect(url_for("users.login"))

    return render_template(
        "users/reset_request.html",
        title="Reset Password",
        form=form,
        js_files=["js/users/reset_password.js"],
    )


# =========================
# RESET TOKEN
# =========================
@users.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_token(token):
    if current_user.is_authenticated:
        if session.get("user_type") == "admin":
            return redirect(url_for("admin.dashboard"))
        return redirect(url_for("paper_gen.select_program"))

    user = User.verify_reset_token(token)

    if user is None:
        flash("That is an invalid or expired token.", "warning")
        return redirect(url_for("users.reset_request"))

    form = ResetPasswordForm()

    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(
            form.password.data
        ).decode("utf-8")

        user.password = hashed_password
        db.session.commit()

        flash("Your password has been updated! You can now log in.", "success")
        return redirect(url_for("users.login"))

    return render_template(
        "users/reset_token.html",
        title="Reset Password",
        form=form,
        js_files=["js/users/reset_password.js"],
    )


# =========================
# DELETE ACCOUNT
# =========================
@users.route("/account/delete/")
@login_required
def delete_account():
    if session.get("user_type") != "user":
        flash("Access denied.", "danger")
        return redirect(url_for("main.index"))

    db.session.delete(current_user)
    db.session.commit()

    logout_user()
    session.pop("user_type", None)

    flash("Your account has been deleted.", "info")
    return redirect(url_for("main.index"))