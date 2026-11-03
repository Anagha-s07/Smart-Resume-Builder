
import re

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# Starting weights for the three matching components.
SKILLS_WEIGHT = 45
EDUCATION_WEIGHT = 20
TEXT_WEIGHT = 35


# Common aliases help the matcher recognize equivalent skill names.
SKILL_ALIASES = {
    "python": ["python", "python programming"],
    "django": ["django", "django framework"],
    "javascript": ["javascript", "js"],
    "html": ["html", "html5"],
    "css": ["css", "css3"],
    "sql": ["sql", "structured query language"],
    "mysql": ["mysql"],
    "postgresql": ["postgresql", "postgres"],
    "machine learning": ["machine learning", "ml"],
    "deep learning": ["deep learning"],
    "data analysis": ["data analysis", "data analytics"],
    "data science": ["data science"],
    "artificial intelligence": [
        "artificial intelligence",
        "ai",
    ],
    "tensorflow": ["tensorflow"],
    "pytorch": ["pytorch"],
    "scikit-learn": ["scikit-learn", "sklearn"],
    "excel": ["excel", "microsoft excel"],
    "power bi": ["power bi", "powerbi"],
    "tableau": ["tableau"],
    "java": ["java"],
    "c++": ["c++"],
    "c#": ["c#"],
    "react": ["react", "react.js", "reactjs"],
    "node.js": ["node.js", "nodejs", "node js"],
    "git": ["git", "version control"],
    "aws": ["aws", "amazon web services"],
    "communication": ["communication", "communication skills"],
    "problem solving": ["problem solving", "problem-solving"],
}


def _clean_text(value):
    """Convert a value to normalized text safely."""
    if value is None:
        return ""

    return re.sub(r"\s+", " ", str(value)).strip()


def _field(obj, field_name):
    """Read a field from a Django model or dictionary."""
    if isinstance(obj, dict):
        return _clean_text(obj.get(field_name, ""))

    return _clean_text(getattr(obj, field_name, ""))


def _contains_term(text, term):
    """Check for a whole-word or whole-phrase match."""
    pattern = r"(?<!\w)" + re.escape(term.lower()) + r"(?!\w)"
    return re.search(pattern, text.lower()) is not None


def _extract_skills(text):
    """
    Extract recognized skills from text.

    This is dictionary-based skill extraction, not a trained
    skill-classification model. Extend SKILL_ALIASES as needed.
    """
    text = _clean_text(text).lower()
    found = set()

    for canonical_name, aliases in SKILL_ALIASES.items():
        for alias in aliases:
            if _contains_term(text, alias):
                found.add(canonical_name)
                break

    return found


def _skill_score(resume_skills, required_skills):
    """
    Calculate required-skill coverage as a percentage.

    The denominator is the number of distinct recognized
    skills in the job requirements.
    """
    required = _extract_skills(required_skills)
    candidate = _extract_skills(resume_skills)

    if not required or not candidate:
        return None

    matched = required.intersection(candidate)
    return (len(matched) / len(required)) * 100


def _education_score(resume_education, job_qualification):
    """
    Compare education text with the stated qualification.

    This is a text-based comparison, not verification of a degree.
    """
    education = _clean_text(resume_education)
    qualification = _clean_text(job_qualification)

    if not education or not qualification:
        return None

    education_lower = education.lower()
    qualification_lower = qualification.lower()

    # Recognize common degree abbreviations and their full forms.
    degree_groups = [
        {"bca", "bachelor of computer applications"},
        {"mca", "master of computer applications"},
        {"bsc", "b.sc", "bachelor of science"},
        {"msc", "m.sc", "master of science"},
        {"btech", "b.tech", "bachelor of technology"},
        {"mtech", "m.tech", "master of technology"},
        {"bcom", "b.com", "bachelor of commerce"},
        {"mcom", "m.com", "master of commerce"},
        {"mba", "master of business administration"},
        {"bba", "bachelor of business administration"},
        {"ba", "b.a.", "bachelor of arts"},
        {"ma", "m.a.", "master of arts"},
        {"be", "b.e.", "bachelor of engineering"},
        {"me", "m.e.", "master of engineering"},
    ]

    for group in degree_groups:
        education_has_group = any(
            _contains_term(education_lower, term)
            for term in group
        )
        qualification_has_group = any(
            _contains_term(qualification_lower, term)
            for term in group
        )

        if education_has_group and qualification_has_group:
            return 100.0

    # Fall back to TF-IDF similarity when no degree alias matches.
    return _text_similarity(education, qualification)


def _text_similarity(text_a, text_b):
    """Return TF-IDF cosine similarity as a percentage."""
    text_a = _clean_text(text_a)
    text_b = _clean_text(text_b)

    if not text_a or not text_b:
        return None

    try:
        vectorizer = TfidfVectorizer(
            lowercase=True,
            stop_words="english",
            ngram_range=(1, 2),
            sublinear_tf=True,
        )

        vectors = vectorizer.fit_transform([text_a, text_b])

        score = cosine_similarity(
            vectors[0:1],
            vectors[1:2],
        )[0][0]

        return max(0.0, min(100.0, float(score) * 100))

    except ValueError:
        # For example, both inputs may contain only stop words.
        return 0.0


def _combine_scores(components):
    """
    Combine available component scores and normalize their weights.

    Missing resume fields do not automatically count as zero.
    The returned score is a matching score, not a hiring probability.
    """
    weights = {
        "skills": SKILLS_WEIGHT,
        "education": EDUCATION_WEIGHT,
        "text": TEXT_WEIGHT,
    }

    available = {
        name: score
        for name, score in components.items()
        if score is not None
    }

    if not available:
        return 0.0

    total_weight = sum(weights[name] for name in available)

    if total_weight == 0:
        return 0.0

    combined = sum(
        float(score) * weights[name]
        for name, score in available.items()
    ) / total_weight

    return round(max(0.0, min(100.0, combined)), 2)


def calculate_resume_job_match(resume, job):
    """
    Calculate a weighted resume-job matching score.

    Expected resume fields:
        skills, education, projects, certifications,
        internships, career_objective

    Expected job fields:
        required_skills, qualification, job_title,
        experience, job_description
    """
    resume_skills = _field(resume, "skills")
    resume_education = _field(resume, "education")

    job_skills = _field(job, "required_skills")
    job_qualification = _field(job, "qualification")

    resume_text = " ".join(
        filter(None, [
            _field(resume, "career_objective"),
            resume_education,
            resume_skills,
            _field(resume, "projects"),
            _field(resume, "certifications"),
            _field(resume, "internships"),
        ])
    )

    job_text = " ".join(
        filter(None, [
            _field(job, "job_title"),
            job_skills,
            job_qualification,
            _field(job, "experience"),
            _field(job, "job_description"),
        ])
    )

    components = {
        "skills": _skill_score(resume_skills, job_skills),
        "education": _education_score(
            resume_education,
            job_qualification,
        ),
        "text": _text_similarity(resume_text, job_text),
    }

    return _combine_scores(components)


def calculate_match(resume_text, job_text):
    """
    Backward-compatible text-only matching function.

    Keep this function for existing code that passes two text strings.
    For better skill and education matching, use
    calculate_resume_job_match(resume, job).
    """
    score = _text_similarity(resume_text, job_text)

    if score is None:
        return 0.0

    return round(score, 2)
