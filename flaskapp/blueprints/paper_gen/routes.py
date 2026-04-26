import random
from datetime import date
from collections import defaultdict

from flask import Blueprint
from flask import flash
from flask import jsonify
from flask import redirect
from flask import render_template
from flask import request
from flask import session
from flask import url_for
from flask_login import current_user
from flask_login import login_required
try:
    from flask_weasyprint import render_pdf
    WEASYPRINT_AVAILABLE = True
except (OSError, ImportError):
    render_pdf = None
    WEASYPRINT_AVAILABLE = False

from flaskapp import db
from flaskapp.models import Program, Department, Semester, Subject, Unit, Question, Paper
from flaskapp.utils import CognitiveEnum, DifficultyEnum, QuestionTypeEnum

paper_gen = Blueprint("paper_gen", __name__)


def find_questions_by_marks(subject_id, mark, count, exclude_ids=None):
    """Find random questions with specific marks for a subject"""
    exclude_ids = exclude_ids or []

    # Get all units for this subject
    units = Unit.query.filter_by(subject_id=subject_id).all()
    unit_ids = [u.id for u in units]

    # Get questions with specific marks
    questions = Question.query.filter(
        Question.unit_id.in_(unit_ids),
        Question.mark == mark,
        ~Question.id.in_(exclude_ids) if exclude_ids else True
    ).all()

    if len(questions) < count:
        return None

    return random.sample(questions, count)


@paper_gen.route("/paper/select-program")
@login_required
def select_program():
    """Step 1: Select Program"""
    programs = Program.query.all()
    return render_template("paper_gen/select_program.html",
                           title="Select Program",
                           programs=programs)


@paper_gen.route("/paper/select-department/<int:program_id>")
@login_required
def select_department(program_id):
    """Step 2: Select Department"""
    program = Program.query.get_or_404(program_id)
    departments = Department.query.filter_by(program_id=program_id).all()
    return render_template("paper_gen/select_department.html",
                           title="Select Department",
                           program=program,
                           departments=departments)


@paper_gen.route("/paper/select-semester/<int:dept_id>")
@login_required
def select_semester(dept_id):
    """Step 3: Select Semester"""
    department = Department.query.get_or_404(dept_id)
    semesters = Semester.query.filter_by(department_id=dept_id).all()
    return render_template("paper_gen/select_semester.html",
                           title="Select Semester",
                           department=department,
                           semesters=semesters)


@paper_gen.route("/paper/select-subject/<int:semester_id>")
@login_required
def select_subject(semester_id):
    """Step 4: Select Subject"""
    semester = Semester.query.get_or_404(semester_id)
    subjects = Subject.query.filter_by(semester_id=semester_id).all()
    return render_template("paper_gen/select_subject.html",
                           title="Select Subject",
                           semester=semester,
                           subjects=subjects)


@paper_gen.route("/paper/configure/<int:subject_id>", methods=["GET", "POST"])
@login_required
def configure_paper(subject_id):
    """Step 5: Configure Question Counts"""
    subject = Subject.query.get_or_404(subject_id)

    # Get available marks from questions in this subject
    units = Unit.query.filter_by(subject_id=subject_id).all()
    unit_ids = [u.id for u in units]

    # Get distinct marks available
    marks_query = db.session.query(Question.mark).filter(
        Question.unit_id.in_(unit_ids)
    ).distinct().order_by(Question.mark).all()
    available_marks = [m[0] for m in marks_query]

    if request.method == "POST":
        # Store configuration in session
        paper_config = {
            "subject_id": subject_id,
            "name": request.form.get("paper_name", f"Question Paper - {subject.name}"),
            "term": request.form.get("term", "Internal Assessment"),
            "exam_date": request.form.get("exam_date", str(date.today())),
            "time_limit": request.form.get("time_limit", "3 Hours"),
            "questions": {}
        }

        total_marks = 0
        for mark in available_marks:
            count = int(request.form.get(f"mark_{mark}", 0))
            if count > 0:
                paper_config["questions"][str(mark)] = count
                total_marks += mark * count

        paper_config["total_marks"] = total_marks
        session["paper_config"] = paper_config

        return redirect(url_for("paper_gen.generate_paper"))

    return render_template("paper_gen/configure.html",
                           title="Configure Paper",
                           subject=subject,
                           available_marks=available_marks)


@paper_gen.route("/paper/generate", methods=["GET", "POST"])
@login_required
def generate_paper():
    """Generate the paper"""
    config = session.get("paper_config")
    if not config:
        flash("No paper configuration found", "danger")
        return redirect(url_for("paper_gen.select_program"))

    subject_id = config["subject_id"]
    subject = Subject.query.get_or_404(subject_id)

    # Generate paper
    paper_format = defaultdict(list)
    all_selected_questions = []

    for mark_str, count in config["questions"].items():
        mark = int(mark_str)
        questions = find_questions_by_marks(
            subject_id, mark, count,
            exclude_ids=[q.id for q in all_selected_questions]
        )

        if questions is None:
            flash(f"Not enough questions available for {mark} mark(s). Available: less than {count}", "danger")
            return redirect(url_for("paper_gen.configure_paper", subject_id=subject_id))

        paper_format[mark] = [q.id for q in questions]
        all_selected_questions.extend(questions)

    if request.method == "POST":
        # Save paper to database
        paper = Paper(
            name=config["name"],
            term=config["term"],
            exam_date=date.fromisoformat(config["exam_date"]),
            time_limit=config["time_limit"],
            mark=config["total_marks"],
            paper_format=dict(paper_format),
            subject_id=subject_id
        )
        db.session.add(paper)
        db.session.commit()

        flash(f"Paper generated successfully! Total marks: {config['total_marks']}", "success")
        return redirect(url_for("paper_gen.view_paper", paper_id=paper.id))

    # Preview mode
    questions_by_mark = {}
    for mark_str, q_ids in paper_format.items():
        mark = int(mark_str)
        questions = Question.query.filter(Question.id.in_(q_ids)).all()
        questions_by_mark[mark] = questions

    return render_template("paper_gen/preview.html",
                           title="Preview Paper",
                           subject=subject,
                           config=config,
                           questions_by_mark=questions_by_mark)


@paper_gen.route("/paper/view/<int:paper_id>")
@login_required
def view_paper(paper_id):
    """View generated paper"""
    paper = Paper.query.get_or_404(paper_id)
    subject = Subject.query.get(paper.subject_id)

    # Get questions by mark
    questions_by_mark = {}
    paper_format = paper.paper_format

    for mark_str, q_ids in paper_format.items():
        mark = int(mark_str)
        questions = Question.query.filter(Question.id.in_(q_ids)).all()
        questions_by_mark[mark] = questions

    return render_template("paper_gen/view_paper.html",
                           title="Question Paper",
                           paper=paper,
                           subject=subject,
                           questions_by_mark=questions_by_mark)


@paper_gen.route("/paper/pdf/<int:paper_id>")
@login_required
def download_pdf(paper_id):
    """Download paper as PDF"""
    if not WEASYPRINT_AVAILABLE:
        flash("PDF generation requires WeasyPrint system libraries. Showing HTML version instead.", "warning")
        return view_paper(paper_id)

    paper = Paper.query.get_or_404(paper_id)
    subject = Subject.query.get(paper.subject_id)

    # Get questions by mark
    questions_by_mark = {}
    paper_format = paper.paper_format

    for mark_str, q_ids in paper_format.items():
        mark = int(mark_str)
        questions = Question.query.filter(Question.id.in_(q_ids)).all()
        questions_by_mark[mark] = questions

    html = render_template("paper_gen/paper_pdf.html",
                          paper=paper,
                          subject=subject,
                          questions_by_mark=questions_by_mark)

    return render_pdf(html)


@paper_gen.route("/paper/my-papers")
@login_required
def my_papers():
    """List all papers generated by user"""
    papers = Paper.query.all()  # In a real app, filter by user
    return render_template("paper_gen/my_papers.html",
                           title="My Question Papers",
                           papers=papers)
