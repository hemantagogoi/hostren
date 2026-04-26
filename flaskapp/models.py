from flask import current_app, session
from flask_login import UserMixin
from itsdangerous import BadSignature
from itsdangerous import URLSafeTimedSerializer as Serializer
from flaskapp import db, login_manager
from flaskapp.utils import (
    CognitiveEnum,
    DifficultyEnum,
    QuestionTypeEnum,
    default_instructions,
)


# =========================
# LOGIN MANAGER USER LOADER
# =========================
@login_manager.user_loader
def load_user(user_id):
    """
    Safely load User or Admin based on session user_type.
    Prevents ID conflict between tables.
    """
    user_type = session.get("user_type")

    if user_type == "admin":
        return db.session.get(Admin, int(user_id))

    if user_type == "user":
        return db.session.get(User, int(user_id))

    return None


# =========================
# ADMIN MODEL
# =========================
class Admin(db.Model, UserMixin):
    __tablename__ = "admin"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    is_admin = db.Column(db.Boolean, default=True)

    # Relationship to track approved users
    approved_users = db.relationship("User", backref="approving_admin", lazy=True)

    def __repr__(self):
        return f"Admin({self.username}, {self.email})"


# =========================
# PROGRAM MODEL
# =========================
class Program(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    duration_years = db.Column(db.Integer, nullable=False, default=3)

    departments = db.relationship(
        "Department",
        backref="program",
        lazy=True,
        cascade="all, delete-orphan",
    )

    def to_dict(self):
        return dict(id=self.id, name=self.name, duration_years=self.duration_years)


# =========================
# DEPARTMENT MODEL
# =========================
class Department(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    program_id = db.Column(db.Integer, db.ForeignKey("program.id"), nullable=False)

    users = db.relationship("User", backref="department", lazy=True)

    semesters = db.relationship(
        "Semester",
        backref="department",
        lazy=True,
        cascade="all, delete-orphan",
    )

    def to_dict(self):
        return dict(id=self.id, name=self.name, program_id=self.program_id)


# =========================
# SEMESTER MODEL
# =========================
class Semester(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.Integer, nullable=False)
    department_id = db.Column(
        db.Integer,
        db.ForeignKey("department.id"),
        nullable=False,
    )

    subjects = db.relationship(
        "Subject",
        backref="semester",
        lazy=True,
        cascade="all, delete-orphan",
    )

    def to_dict(self):
        return dict(id=self.id, number=self.number, department_id=self.department_id)


# =========================
# SUBJECT MODEL
# =========================
class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    code = db.Column(db.String(20), nullable=True)
    include_asked = db.Column(db.Boolean, default=False)

    semester_id = db.Column(
        db.Integer,
        db.ForeignKey("semester.id"),
        nullable=False,
    )

    units = db.relationship(
        "Unit",
        backref="subject",
        lazy=True,
        cascade="all, delete-orphan",
    )

    papers = db.relationship(
        "Paper",
        backref="subject",
        lazy=True,
        cascade="all, delete-orphan",
    )

    def to_dict(self):
        return dict(id=self.id, name=self.name, code=self.code)


# =========================
# USER MODEL
# =========================
class User(db.Model, UserMixin):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default="default.svg")
    password = db.Column(db.String(60), nullable=False)
    
    # Admin approval status
    is_approved = db.Column(db.Boolean, default=False, nullable=False)
    approval_requested_at = db.Column(db.DateTime, nullable=True)
    approved_at = db.Column(db.DateTime, nullable=True)
    approved_by = db.Column(db.Integer, db.ForeignKey("admin.id"), nullable=True)

    department_id = db.Column(
        db.Integer,
        db.ForeignKey("department.id"),
        nullable=True,
    )

    def get_reset_token(self, expires_sec=86400):
        s = Serializer(current_app.config["SECRET_KEY"])
        return s.dumps({"user_id": self.id})

    @staticmethod
    def verify_reset_token(token):
        s = Serializer(current_app.config["SECRET_KEY"])
        try:
            user_id = s.loads(token, max_age=86400)["user_id"]
        except BadSignature:
            return None
        return db.session.get(User, user_id)

    def __repr__(self):
        return f"User({self.username}, {self.email})"

    def to_dict(self):
        return dict(
            id=self.id,
            username=self.username,
            email=self.email,
            image_file=self.image_file,
        )


# =========================
# UNIT MODEL
# =========================
class Unit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chapter_no = db.Column(db.Integer, nullable=False)
    name = db.Column(db.Text, nullable=True)

    subject_id = db.Column(
        db.Integer,
        db.ForeignKey("subject.id"),
        nullable=False,
    )

    questions = db.relationship(
        "Question",
        backref="unit",
        lazy=True,
        cascade="all, delete-orphan",
    )

    def to_dict(self):
        return dict(id=self.id, chapter_no=self.chapter_no, name=self.name)


# =========================
# QUESTION MODEL
# =========================
class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.JSON, nullable=False)
    mark = db.Column(db.Integer, nullable=False)

    difficulty = db.Column(db.Enum(DifficultyEnum), nullable=False)
    cognitive_level = db.Column(db.Enum(CognitiveEnum), nullable=False)
    question_type = db.Column(db.Enum(QuestionTypeEnum), nullable=False)

    imp = db.Column(db.Boolean, default=False)
    is_asked = db.Column(db.Boolean, default=False)

    unit_id = db.Column(
        db.Integer,
        db.ForeignKey("unit.id"),
        nullable=False,
    )

    def to_dict(self):
        data = dict(
            id=self.id,
            mark=self.mark,
            difficulty=self.difficulty.name,
            cognitive_level=self.cognitive_level.name,
            question_type=self.question_type.name,
            imp=self.imp,
        )
        data.update(self.question)
        return data


# =========================
# PAPER MODEL
# =========================
class Paper(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.Text, nullable=False)
    paper_logo = db.Column(db.Text, nullable=False, default="logo.svg")
    term = db.Column(db.Text, nullable=False)
    exam_date = db.Column(db.Date, nullable=False)
    time_limit = db.Column(db.Text, nullable=False)

    instructions = db.Column(
        db.JSON,
        nullable=True,
        default=default_instructions,
    )

    subject_id = db.Column(
        db.Integer,
        db.ForeignKey("subject.id"),
        nullable=False,
    )

    mark = db.Column(db.Integer, nullable=False)
    paper_format = db.Column(db.JSON, nullable=False)

    def to_dict(self):
        return dict(
            id=self.id,
            name=self.name,
            term=self.term,
            mark=self.mark,
            paper_format=self.paper_format,
            paper_logo=self.paper_logo,
            exam_date=self.exam_date.isoformat(),
            time_limit=self.time_limit,
            instructions=self.instructions,
        )