import random
from datetime import date
from collections import defaultdict
from sqlalchemy import or_, and_

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
from flaskapp.blueprints.questions.forms import QuestionForm, MCQQuestionForm
from flaskapp.blueprints.questions.utils import add_question_to_db

paper_gen = Blueprint("paper_gen", __name__)


def balance_questions_across_units(questions, units):
    """Balance questions across different units to ensure coverage"""
    if len(questions) <= len(units):
        return questions  # Not enough questions to balance
    
    # Group questions by unit
    unit_questions = defaultdict(list)
    for q in questions:
        unit_questions[q.unit_id].append(q)
    
    # Calculate ideal distribution
    total_questions = len(questions)
    questions_per_unit = max(1, total_questions // len(units))
    
    balanced_questions = []
    remaining_slots = total_questions
    
    # First pass: get equal distribution from each unit
    for unit in units:
        available = unit_questions.get(unit.id, [])
        if available:
            take = min(questions_per_unit, len(available), remaining_slots)
            selected = random.sample(available, take)
            balanced_questions.extend(selected)
            remaining_slots -= take
    
    # Second pass: fill remaining slots randomly from remaining questions
    if remaining_slots > 0:
        used_ids = {q.id for q in balanced_questions}
        remaining_questions = [q for q in questions if q.id not in used_ids]
        if remaining_questions:
            additional = random.sample(remaining_questions, min(remaining_slots, len(remaining_questions)))
            balanced_questions.extend(additional)
    
    # Shuffle final selection
    random.shuffle(balanced_questions)
    return balanced_questions


def generate_paper_with_fallback(subject_id, marks_config, total_marks_required, max_attempts=3):
    """Generate paper with intelligent fallback logic"""
    best_attempt = None
    best_score = 0
    error_messages = []
    
    for attempt in range(max_attempts):
        try:
            paper_format = defaultdict(list)
            all_selected_questions = []
            current_total = 0
            attempt_errors = []
            
            # Try to fulfill each marks requirement
            for mark_str, count in marks_config.items():
                mark = int(mark_str)
                questions, error = find_questions_by_marks(
                    subject_id, mark, count,
                    exclude_ids=[q.id for q in all_selected_questions],
                    balance_units=True,
                    difficulty_distribution={'Easy': 0.3, 'Medium': 0.5, 'Hard': 0.2}
                )
                
                if questions is None:
                    attempt_errors.append(error)
                    # Try with reduced count
                    available_count = get_available_question_count(subject_id, mark, all_selected_questions)
                    if available_count > 0:
                        questions, _ = find_questions_by_marks(
                            subject_id, mark, available_count,
                            exclude_ids=[q.id for q in all_selected_questions]
                        )
                        if questions:
                            paper_format[mark] = [q.id for q in questions]
                            all_selected_questions.extend(questions)
                            current_total += mark * len(questions)
                else:
                    paper_format[mark] = [q.id for q in questions]
                    all_selected_questions.extend(questions)
                    current_total += mark * len(questions)
            
            # Score this attempt based on how close it is to the target
            score = 100 - abs(total_marks_required - current_total)
            
            if score > best_score:
                best_score = score
                best_attempt = {
                    'paper_format': dict(paper_format),
                    'questions': all_selected_questions,
                    'total_marks': current_total,
                    'errors': attempt_errors.copy()
                }
            
            # Perfect match found
            if current_total == total_marks_required:
                break
                
        except Exception as e:
            attempt_errors.append(f"Attempt {attempt + 1} failed: {str(e)}")
            error_messages.extend(attempt_errors)
    
    return best_attempt, error_messages


def get_available_question_count(subject_id, mark, exclude_ids=None):
    """Get count of available questions for specific marks"""
    exclude_ids = exclude_ids or []
    units = Unit.query.filter_by(subject_id=subject_id).all()
    unit_ids = [u.id for u in units]
    
    count = Question.query.filter(
        Question.unit_id.in_(unit_ids),
        Question.mark == mark,
        ~Question.id.in_(exclude_ids) if exclude_ids else True
    ).count()
    
    return count


def organize_questions_into_sections(paper_format):
    """Organize questions into sections (A, B, C) based on marks distribution"""
    sections = {}
    section_names = {}
    section_counter = 65  # ASCII for 'A'
    
    # Sort marks to create logical sections (usually from lowest to highest marks)
    sorted_marks = sorted(paper_format.keys(), key=lambda x: int(x))
    
    for mark in sorted_marks:
        section_letter = chr(section_counter)
        sections[section_letter] = paper_format[mark]
        
        # Create descriptive section name
        mark_int = int(mark)
        if mark_int <= 2:
            section_names[section_letter] = f"Section {section_letter}: Short Answer Questions ({mark_int} marks each)"
        elif mark_int <= 5:
            section_names[section_letter] = f"Section {section_letter}: Medium Answer Questions ({mark_int} marks each)"
        else:
            section_names[section_letter] = f"Section {section_letter}: Long Answer Questions ({mark_int} marks each)"
        
        section_counter += 1
    
    return sections, section_names


def find_questions_by_marks(subject_id, mark, count, exclude_ids=None, balance_units=True, difficulty_distribution=None):
    """Find random questions with specific marks for a subject with enhanced features"""
    exclude_ids = exclude_ids or []
    difficulty_distribution = difficulty_distribution or {'Easy': 0.3, 'Medium': 0.5, 'Hard': 0.2}
    
    # Get all units for this subject
    units = Unit.query.filter_by(subject_id=subject_id).all()
    unit_ids = [u.id for u in units]
    
    # Base query for questions with specific marks
    base_query = Question.query.filter(
        Question.unit_id.in_(unit_ids),
        Question.mark == mark,
        ~Question.id.in_(exclude_ids) if exclude_ids else True
    )
    
    # Get all available questions
    all_questions = base_query.all()
    
    if len(all_questions) < count:
        return None, f"Not enough questions available for {mark} mark(s). Available: {len(all_questions)}, Required: {count}"
    
    selected_questions = []
    remaining_questions = all_questions.copy()
    
    # Apply difficulty distribution if requested
    if difficulty_distribution and len(all_questions) >= count:
        difficulty_questions = defaultdict(list)
        for q in remaining_questions:
            difficulty_questions[q.difficulty.name].append(q)
        
        # Calculate target counts for each difficulty
        target_counts = {}
        for difficulty, ratio in difficulty_distribution.items():
            target_counts[difficulty] = max(1, int(count * ratio))
        
        # Adjust if total doesn't match required count
        total_target = sum(target_counts.values())
        if total_target != count:
            # Adjust the most common difficulty
            most_common = max(target_counts.keys(), key=lambda x: len(difficulty_questions.get(x, [])))
            target_counts[most_common] += (count - total_target)
        
        # Select questions by difficulty
        for difficulty, target_count in target_counts.items():
            available = difficulty_questions.get(difficulty, [])
            if available:
                actual_count = min(target_count, len(available))
                selected = random.sample(available, actual_count)
                selected_questions.extend(selected)
                # Remove selected from remaining pool
                for q in selected:
                    remaining_questions.remove(q)
        
        # Fill remaining slots if needed
        if len(selected_questions) < count and remaining_questions:
            needed = count - len(selected_questions)
            additional = random.sample(remaining_questions, min(needed, len(remaining_questions)))
            selected_questions.extend(additional)
    else:
        # Simple random selection
        selected_questions = random.sample(all_questions, count)
    
    # Apply unit balancing if requested
    if balance_units and len(selected_questions) == count:
        selected_questions = balance_questions_across_units(selected_questions, units)
    
    return selected_questions[:count], None


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


@paper_gen.route("/paper/manage-questions/<int:subject_id>", methods=["GET", "POST"])
@login_required
def manage_questions_for_paper(subject_id):
    """Show units management page for users (redirects to units view)"""
    return redirect(url_for("paper_gen.manage_units_for_paper", subject_id=subject_id))


@paper_gen.route("/paper/units/<int:subject_id>", methods=["GET", "POST"])
@login_required
def manage_units_for_paper(subject_id):
    """Manage units for paper configuration - user accessible version"""
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
        "paper_gen/units.html",
        title=f"Units - {subject.name}",
        subject=subject,
        units=units,
    )


@paper_gen.route("/paper/units/<int:unit_id>/delete")
@login_required
def delete_unit_from_paper(unit_id):
    """Delete a unit from paper management"""
    unit = Unit.query.get_or_404(unit_id)
    subject_id = unit.subject_id
    
    try:
        db.session.delete(unit)
        db.session.commit()
        flash("Unit deleted successfully!", "success")
    except Exception as e:
        flash(f"Error deleting unit: {str(e)}", "danger")
    
    return redirect(url_for("paper_gen.manage_units_for_paper", subject_id=subject_id))


@paper_gen.route("/paper/questions/<int:unit_id>", methods=["GET", "POST"])
@login_required
def manage_questions_for_unit(unit_id):
    """Manage questions for a specific unit - user accessible version using admin template"""
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
        "paper_gen/user_questions.html",
        title=f"Questions - Unit {unit.chapter_no}",
        unit=unit,
        subject=subject,
        questions=questions,
        difficulties=[e.name for e in DifficultyEnum],
        cognitive_levels=[e.name for e in CognitiveEnum],
        question_types=[e.name for e in QuestionTypeEnum],
    )


@paper_gen.route("/paper/questions/<int:question_id>/delete")
@login_required
def delete_question_from_paper(question_id):
    """Delete a question from paper management"""
    question = Question.query.get_or_404(question_id)
    subject_id = question.unit.subject_id
    
    try:
        db.session.delete(question)
        db.session.commit()
        flash("Question deleted successfully!", "success")
    except Exception as e:
        flash(f"Error deleting question: {str(e)}", "danger")
    
    return redirect(url_for("paper_gen.manage_questions_for_paper", subject_id=subject_id))


@paper_gen.route("/paper/add-question/<int:subject_id>", methods=["GET", "POST"])
@login_required
def add_question_to_paper(subject_id):
    """Add a question specifically for paper configuration (legacy route)"""
    return redirect(url_for("paper_gen.manage_questions_for_paper", subject_id=subject_id))


def get_all_questions_for_subject(subject_id):
    """Get all questions for a subject with unit information"""
    units = Unit.query.filter_by(subject_id=subject_id).all()
    unit_ids = [u.id for u in units]
    
    questions = Question.query.filter(
        Question.unit_id.in_(unit_ids)
    ).order_by(Question.unit_id, Question.mark).all()
    
    return questions


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
    """Generate the paper with enhanced random selection"""
    config = session.get("paper_config")
    if not config:
        flash("No paper configuration found", "danger")
        return redirect(url_for("paper_gen.select_program"))

    subject_id = config["subject_id"]
    subject = Subject.query.get_or_404(subject_id)

    # Generate paper with enhanced algorithm
    result, errors = generate_paper_with_fallback(
        subject_id, 
        config["questions"], 
        config["total_marks"]
    )
    
    if result is None:
        flash("Failed to generate paper. Please try different configuration.", "danger")
        for error in errors:
            flash(error, "warning")
        return redirect(url_for("paper_gen.configure_paper", subject_id=subject_id))

    paper_format = result['paper_format']
    all_selected_questions = result['questions']
    actual_total = result['total_marks']
    
    # Show warnings if paper couldn't meet exact requirements
    if actual_total != config["total_marks"]:
        flash(f"Paper generated with {actual_total} marks (target: {config["total_marks"]}).", "warning")
        for error in result['errors']:
            flash(error, "info")
    else:
        flash(f"Paper generated successfully! Total marks: {actual_total}", "success")

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

    # Preview mode with sections
    sections, section_names = organize_questions_into_sections(paper_format)
    questions_by_section = {}
    
    for section_letter, q_ids in sections.items():
        questions = Question.query.filter(Question.id.in_(q_ids)).all()
        questions_by_section[section_letter] = questions

    return render_template("paper_gen/preview.html",
                           title="Preview Paper",
                           subject=subject,
                           config=config,
                           questions_by_section=questions_by_section,
                           section_names=section_names,
                           actual_total=actual_total)


@paper_gen.route("/paper/view/<int:paper_id>")
@login_required
def view_paper(paper_id):
    """View generated paper"""
    paper = Paper.query.get_or_404(paper_id)
    subject = Subject.query.get(paper.subject_id)

    # Get questions by section
    sections, section_names = organize_questions_into_sections(paper.paper_format)
    questions_by_section = {}
    
    for section_letter, q_ids in sections.items():
        questions = Question.query.filter(Question.id.in_(q_ids)).all()
        questions_by_section[section_letter] = questions

    return render_template("paper_gen/view_paper.html",
                           title="Question Paper",
                           paper=paper,
                           subject=subject,
                           questions_by_section=questions_by_section,
                           section_names=section_names)


@paper_gen.route("/paper/pdf/<int:paper_id>")
@login_required
def download_pdf(paper_id):
    """Download paper as PDF"""
    if not WEASYPRINT_AVAILABLE:
        flash("PDF generation requires WeasyPrint system libraries. Showing HTML version instead.", "warning")
        return view_paper(paper_id)

    paper = Paper.query.get_or_404(paper_id)
    subject = Subject.query.get(paper.subject_id)

    # Get questions by section for PDF
    sections, section_names = organize_questions_into_sections(paper.paper_format)
    questions_by_section = {}
    
    for section_letter, q_ids in sections.items():
        questions = Question.query.filter(Question.id.in_(q_ids)).all()
        questions_by_section[section_letter] = questions

    html = render_template("paper_gen/paper_pdf.html",
                          paper=paper,
                          subject=subject,
                          questions_by_section=questions_by_section,
                          section_names=section_names)

    return render_pdf(html)


@paper_gen.route("/paper/my-papers")
@login_required
def my_papers():
    """List all papers generated by user"""
    papers = Paper.query.all()  # In a real app, filter by user
    return render_template("paper_gen/my_papers.html",
                           title="My Question Papers",
                           papers=papers)
