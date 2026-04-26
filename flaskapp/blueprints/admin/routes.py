from functools import wraps
from flask import Blueprint, flash, redirect, render_template, request, url_for, session, jsonify
from flask_login import current_user, login_required, login_user, logout_user
from flaskapp import bcrypt, db
from flaskapp.models import (
    Admin,
    Program,
    Department,
    Semester,
    Subject,
    Unit,
    Question,
    User,
)
from flaskapp.utils import CognitiveEnum, DifficultyEnum, QuestionTypeEnum
from datetime import datetime

admin = Blueprint("admin", __name__)


# =========================
# ADMIN REQUIRED DECORATOR
# =========================
def admin_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated:
            flash("Login required.", "danger")
            return redirect(url_for("admin.admin_login"))

        if session.get("user_type") != "admin":
            flash("Admin access required.", "danger")
            return redirect(url_for("main.index"))

        return func(*args, **kwargs)
    return wrapper


# =========================
# ADMIN LOGIN
# =========================
@admin.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if current_user.is_authenticated and session.get("user_type") == "admin":
        return redirect(url_for("admin.dashboard"))

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        admin_user = Admin.query.filter_by(email=email).first()

        if admin_user and bcrypt.check_password_hash(admin_user.password, password):
            login_user(admin_user)
            session["user_type"] = "admin"
            return redirect(url_for("admin.dashboard"))

        flash("Invalid email or password", "danger")

    return render_template("admin/login.html", title="Admin Login")


# =========================
# ADMIN LOGOUT
# =========================
@admin.route("/admin/logout")
@login_required
@admin_required
def admin_logout():
    logout_user()
    session.pop("user_type", None)
    return redirect(url_for("main.index"))


# =========================
# ADMIN DASHBOARD
# =========================
@admin.route("/admin/dashboard")
@login_required
@admin_required
def dashboard():
    programs = Program.query.all()
    departments = Department.query.all()
    subjects = Subject.query.all()
    users = User.query.all()

    return render_template(
        "admin/dashboard.html",
        title="Admin Dashboard",
        programs=programs,
        departments=departments,
        subjects=subjects,
        users=users,
    )


# =========================
# PROGRAM MANAGEMENT
# =========================
@admin.route("/admin/programs", methods=["GET", "POST"])
@login_required
@admin_required
def manage_programs():
    if request.method == "POST":
        name = request.form.get("name")
        duration = request.form.get("duration", 3)

        if name:
            program = Program(name=name, duration_years=int(duration))
            db.session.add(program)
            db.session.commit()
            flash(f"Program {name} added successfully!", "success")

    programs = Program.query.all()
    return render_template("admin/programs.html", title="Manage Programs", programs=programs)


@admin.route("/admin/programs/<int:program_id>/delete")
@login_required
@admin_required
def delete_program(program_id):
    program = Program.query.get_or_404(program_id)
    db.session.delete(program)
    db.session.commit()
    flash("Program deleted successfully!", "success")
    return redirect(url_for("admin.manage_programs"))


# =========================
# DEPARTMENT MANAGEMENT
# =========================
@admin.route("/admin/departments", methods=["GET", "POST"])
@login_required
@admin_required
def manage_departments():
    if request.method == "POST":
        name = request.form.get("name")
        program_id = request.form.get("program_id")

        if name and program_id:
            dept = Department(name=name, program_id=int(program_id))
            db.session.add(dept)
            db.session.commit()
            flash(f"Department {name} added successfully!", "success")

    programs = Program.query.all()
    departments = Department.query.all()

    return render_template(
        "admin/departments.html",
        title="Manage Departments",
        programs=programs,
        departments=departments,
    )


@admin.route("/admin/departments/<int:dept_id>/delete")
@login_required
@admin_required
def delete_department(dept_id):
    dept = Department.query.get_or_404(dept_id)
    db.session.delete(dept)
    db.session.commit()
    flash("Department deleted successfully!", "success")
    return redirect(url_for("admin.manage_departments"))


# =========================
# SEMESTER MANAGEMENT
# =========================
@admin.route("/admin/semesters", methods=["GET", "POST"])
@login_required
@admin_required
def manage_semesters():
    if request.method == "POST":
        number = request.form.get("number")
        department_id = request.form.get("department_id")

        if number and department_id:
            semester = Semester(number=int(number), department_id=int(department_id))
            db.session.add(semester)
            db.session.commit()
            flash(f"Semester {number} added successfully!", "success")

    departments = Department.query.all()
    semesters = Semester.query.all()

    return render_template(
        "admin/semesters.html",
        title="Manage Semesters",
        departments=departments,
        semesters=semesters,
    )


@admin.route("/admin/semesters/<int:semester_id>/delete")
@login_required
@admin_required
def delete_semester(semester_id):
    semester = Semester.query.get_or_404(semester_id)
    db.session.delete(semester)
    db.session.commit()
    flash("Semester deleted successfully!", "success")
    return redirect(url_for("admin.manage_semesters"))


# =========================
# SUBJECT MANAGEMENT
# =========================
@admin.route("/admin/subjects", methods=["GET", "POST"])
@login_required
@admin_required
def manage_subjects():
    if request.method == "POST":
        name = request.form.get("name")
        code = request.form.get("code")
        semester_id = request.form.get("semester_id")

        if name and semester_id:
            subject = Subject(name=name, code=code, semester_id=int(semester_id))
            db.session.add(subject)
            db.session.commit()
            flash(f"Subject {name} added successfully!", "success")

    semesters = Semester.query.all()
    subjects = Subject.query.all()

    return render_template(
        "admin/subjects.html",
        title="Manage Subjects",
        semesters=semesters,
        subjects=subjects,
    )


@admin.route("/admin/subjects/<int:subject_id>/delete")
@login_required
@admin_required
def delete_subject(subject_id):
    subject = Subject.query.get_or_404(subject_id)
    db.session.delete(subject)
    db.session.commit()
    flash("Subject deleted successfully!", "success")
    return redirect(url_for("admin.manage_subjects"))


# =========================
# UNIT MANAGEMENT
# =========================
@admin.route("/admin/subjects/<int:subject_id>/units", methods=["GET", "POST"])
@login_required
@admin_required
def manage_units(subject_id):
    subject = Subject.query.get_or_404(subject_id)

    if request.method == "POST":
        chapter_no = request.form.get("chapter_no")
        name = request.form.get("name")

        if chapter_no:
            unit = Unit(
                chapter_no=int(chapter_no),
                name=name,
                subject_id=subject_id,
            )
            db.session.add(unit)
            db.session.commit()
            flash("Unit added successfully!", "success")

    units = Unit.query.filter_by(subject_id=subject_id).all()

    return render_template(
        "admin/units.html",
        title=f"Units - {subject.name}",
        subject=subject,
        units=units,
    )


@admin.route("/admin/units/<int:unit_id>/delete")
@login_required
@admin_required
def delete_unit(unit_id):
    unit = Unit.query.get_or_404(unit_id)
    subject_id = unit.subject_id
    db.session.delete(unit)
    db.session.commit()
    flash("Unit deleted successfully!", "success")
    return redirect(url_for("admin.manage_units", subject_id=subject_id))


# =========================
# QUESTION MANAGEMENT
# =========================
@admin.route("/admin/units/<int:unit_id>/questions", methods=["GET", "POST"])
@login_required
@admin_required
def manage_questions(unit_id):
    unit = Unit.query.get_or_404(unit_id)
    subject = Subject.query.get(unit.subject_id)

    if request.method == "POST":
        question_text = request.form.get("question")
        mark = request.form.get("mark", 1)
        difficulty = request.form.get("difficulty", "Easy")
        cognitive = request.form.get("cognitive", "Knowledge")
        qtype = request.form.get("question_type", "sub")
        imp = request.form.get("imp") == "on"

        if question_text:
            question = Question(
                question={"question": question_text},
                mark=int(mark),
                difficulty=DifficultyEnum.from_string(difficulty),
                cognitive_level=CognitiveEnum.from_string(cognitive),
                question_type=QuestionTypeEnum.from_string(qtype),
                imp=imp,
                unit_id=unit_id,
            )
            db.session.add(question)
            db.session.commit()
            flash("Question added successfully!", "success")

    questions = Question.query.filter_by(unit_id=unit_id).all()

    return render_template(
        "admin/questions.html",
        title=f"Questions - Unit {unit.chapter_no}",
        unit=unit,
        subject=subject,
        questions=questions,
        difficulties=[e.name for e in DifficultyEnum],
        cognitive_levels=[e.name for e in CognitiveEnum],
        question_types=[e.name for e in QuestionTypeEnum],
    )


@admin.route("/admin/questions/<int:question_id>/delete")
@login_required
@admin_required
def delete_question(question_id):
    question = Question.query.get_or_404(question_id)
    unit_id = question.unit_id
    db.session.delete(question)
    db.session.commit()
    flash("Question deleted successfully!", "success")
    return redirect(url_for("admin.manage_questions", unit_id=unit_id))


# =========================
# USER MANAGEMENT
# =========================
@admin.route("/admin/users", methods=["GET"])
@login_required
@admin_required
def manage_users():
    users = User.query.all()
    departments = Department.query.all()

    return render_template(
        "admin/users.html",
        title="Manage Users",
        users=users,
        departments=departments,
    )


@admin.route("/admin/users/<int:user_id>/approve", methods=["POST"])
@login_required
@admin_required
def approve_user(user_id):
    user = User.query.get_or_404(user_id)
    
    if user.is_approved:
        return jsonify({"success": False, "message": "User is already approved"})
    
    # Update user approval status
    user.is_approved = True
    user.approved_at = datetime.utcnow()
    user.approved_by = current_user.id
    
    db.session.commit()
    
    return jsonify({"success": True, "message": "User approved successfully"})


@admin.route("/admin/users/<int:user_id>/reject", methods=["POST"])
@login_required
@admin_required
def reject_user(user_id):
    user = User.query.get_or_404(user_id)
    
    if user.is_approved:
        return jsonify({"success": False, "message": "Cannot reject an approved user"})
    
    # Delete the user account (rejection)
    db.session.delete(user)
    db.session.commit()
    
    return jsonify({"success": True, "message": "User rejected and deleted successfully"})


@admin.route("/admin/users/<int:user_id>/delete")
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash("User deleted successfully!", "success")
    return redirect(url_for("admin.manage_users"))