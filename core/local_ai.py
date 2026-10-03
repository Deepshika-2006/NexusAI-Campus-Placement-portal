import re
from typing import List, Dict

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


# ============================================================
# LOAD LOCAL AI MODEL
# ============================================================

# Free local Sentence Transformer model.
# No OpenAI API key is required.
_MODEL = SentenceTransformer(
    "sentence-transformers/all-MiniLM-L6-v2"
)


# ============================================================
# TEXT NORMALIZATION
# ============================================================

def _clean_text(text: str) -> str:
    """
    Normalize text for reliable keyword matching.
    """

    if not text:
        return ""

    text = str(text).lower()

    # Normalize common punctuation/formatting.
    text = text.replace("–", "-")
    text = text.replace("—", "-")
    text = text.replace("’", "'")
    text = text.replace("&", " and ")

    # Keep letters, numbers, common technical symbols and spaces.
    text = re.sub(
        r"[^a-z0-9+#./\- ]+",
        " ",
        text,
    )

    # Normalize whitespace.
    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()


# ============================================================
# KEYWORD LIBRARY
# ============================================================

KNOWN_KEYWORDS = [
    # Programming languages
    "python",
    "java",
    "javascript",
    "typescript",
    "c",
    "c++",

    # Frontend
    "react",
    "react.js",
    "reactjs",
    "angular",
    "vue",
    "html",
    "css",
    "tailwind",
    "bootstrap",
    "next.js",
    "nextjs",
    "vite",
    "redux",

    # Backend
    "django",
    "flask",
    "fastapi",
    "node.js",
    "node",
    "nodejs",
    "express",
    "express.js",

    # Databases
    "mysql",
    "postgresql",
    "postgres",
    "mongodb",
    "sqlite",
    "sql",
    "redis",
    "firebase",

    # Cloud / DevOps
    "git",
    "github",
    "docker",
    "kubernetes",
    "aws",
    "azure",
    "gcp",
    "cloud",

    # AI / ML
    "machine learning",
    "deep learning",
    "artificial intelligence",
    "ai",
    "nlp",
    "natural language processing",
    "tensorflow",
    "pytorch",
    "scikit-learn",
    "pandas",
    "numpy",
    "opencv",
    "llm",
    "large language model",
    "generative ai",

    # APIs / Development
    "rest api",
    "rest apis",
    "rest",
    "api",
    "postman",
    "microservices",

    # CS concepts
    "data structures",
    "data structure",
    "dsa",
    "algorithms",
    "algorithm",
    "oop",
    "object oriented programming",
    "dbms",
    "operating systems",
    "computer networks",
    "system design",

    # Data
    "seaborn",
    "matplotlib",
    "power bi",
    "excel",
    "data analysis",
    "data science",
    "statistics",

    # Office / professional skills
    "ms office",
    "microsoft office",
    "word",
    "powerpoint",
    "outlook",
    "software engineering",
    "software development",
    "communication",
    "problem solving",
]


# ============================================================
# ALIASES
# ============================================================

KEYWORD_ALIASES = {
    "react.js": [
        "react.js",
        "reactjs",
        "react",
    ],

    "reactjs": [
        "reactjs",
        "react.js",
        "react",
    ],

    "node.js": [
        "node.js",
        "nodejs",
        "node",
    ],

    "nodejs": [
        "nodejs",
        "node.js",
        "node",
    ],

    "next.js": [
        "next.js",
        "nextjs",
    ],

    "nextjs": [
        "nextjs",
        "next.js",
    ],

    "postgresql": [
        "postgresql",
        "postgres",
    ],

    "rest api": [
        "rest api",
        "rest apis",
        "rest",
    ],

    "rest apis": [
        "rest apis",
        "rest api",
        "rest",
    ],

    "dsa": [
        "dsa",
        "data structures",
        "data structure",
        "algorithms",
    ],

    "data structures": [
        "data structures",
        "data structure",
        "dsa",
    ],

    "data structure": [
        "data structure",
        "data structures",
        "dsa",
    ],

    "algorithms": [
        "algorithms",
        "algorithm",
        "dsa",
    ],

    "algorithm": [
        "algorithm",
        "algorithms",
        "dsa",
    ],

    "ms office": [
        "ms office",
        "microsoft office",
    ],

    "microsoft office": [
        "microsoft office",
        "ms office",
    ],
}


# ============================================================
# PHRASE MATCHING
# ============================================================

def _phrase_exists(text: str, phrase: str) -> bool:
    """
    Check whether a complete keyword/phrase exists in the text.

    This avoids incorrect substring matches.

    Example:
        software engineering
    will NOT match:
        software development

    Also:
        sql
    will NOT match:
        mysql
    """

    text = _clean_text(text)
    phrase = _clean_text(phrase)

    if not text or not phrase:
        return False

    # Escape the phrase so characters such as +, ., # are safe.
    escaped = re.escape(phrase)

    # Require word boundaries around the phrase.
    pattern = rf"(?<![a-z0-9]){escaped}(?![a-z0-9])"

    return re.search(
        pattern,
        text,
        flags=re.IGNORECASE,
    ) is not None


# ============================================================
# KEYWORD EXTRACTION
# ============================================================

def _extract_keywords(text: str) -> List[str]:
    """
    Extract known technical/professional keywords from text.
    """

    text = _clean_text(text)

    if not text:
        return []

    found = []

    for keyword in KNOWN_KEYWORDS:
        variations = KEYWORD_ALIASES.get(
            keyword,
            [keyword],
        )

        if any(
            _phrase_exists(text, variation)
            for variation in variations
        ):
            found.append(keyword)

    # Remove aliases that would create duplicates.
    canonical = []

    for keyword in found:

        if keyword == "react.js":
            value = "react"

        elif keyword == "reactjs":
            value = "react"

        elif keyword in {"node", "nodejs"}:
            value = "node.js"

        elif keyword == "nextjs":
            value = "next.js"

        elif keyword == "postgres":
            value = "postgresql"

        elif keyword in {"rest", "rest apis"}:
            value = "rest api"

        elif keyword in {"data structure", "algorithms", "algorithm"}:
            value = keyword

        elif keyword == "microsoft office":
            value = "ms office"

        else:
            value = keyword

        if value not in canonical:
            canonical.append(value)

    return canonical


# ============================================================
# RECRUITER JOB SKILLS
# ============================================================

def _extract_job_skills(job_skills: str) -> List[str]:
    """
    Extract skills entered separately by the recruiter.

    Example:

        react, html, css, django, ms office,
        dsa, software engineering

    becomes:

        [
            "react",
            "html",
            "css",
            "django",
            "ms office",
            "dsa",
            "software engineering"
        ]
    """

    if not job_skills:
        return []

    # Support commas, semicolons, pipes and new lines.
    parts = re.split(
        r"[,;|\n]+",
        job_skills,
    )

    cleaned = []

    for part in parts:

        value = _clean_text(part)

        if value and len(value) > 1:

            # Normalize recruiter-entered aliases.
            if value == "microsoft office":
                value = "ms office"

            elif value == "react.js":
                value = "react"

            elif value == "reactjs":
                value = "react"

            elif value in {"node", "nodejs"}:
                value = "node.js"

            elif value == "nextjs":
                value = "next.js"

            elif value == "postgres":
                value = "postgresql"

            elif value in {"rest", "rest apis"}:
                value = "rest api"

            elif value in {
                "data structure",
                "algorithm",
                "algorithms",
            }:
                # Keep DSA as the canonical recruiter skill
                # only when DSA itself is supplied separately.
                pass

            if value not in cleaned:
                cleaned.append(value)

    return cleaned


# ============================================================
# SEMANTIC SIMILARITY
# ============================================================

def _semantic_similarity(
    resume_text: str,
    job_text: str,
) -> float:
    """
    Calculate semantic similarity between the resume
    and job description using Sentence Transformers.
    """

    if not resume_text.strip() or not job_text.strip():
        return 0.0

    embeddings = _MODEL.encode(
        [
            resume_text,
            job_text,
        ],
        convert_to_numpy=True,
        normalize_embeddings=True,
    )

    score = cosine_similarity(
        [embeddings[0]],
        [embeddings[1]],
    )[0][0]

    return max(
        0.0,
        min(
            1.0,
            float(score),
        ),
    )


# ============================================================
# CHECK WHETHER A REQUIRED KEYWORD EXISTS IN RESUME
# ============================================================

def _keyword_matches_resume(
    resume_text: str,
    keyword: str,
) -> bool:
    """
    Determine whether a required job keyword genuinely exists
    in the student's resume.

    Important:
    We check ONLY resume_text.

    We never use the job description itself to decide whether
    a keyword is matched.
    """

    resume_text = _clean_text(resume_text)
    keyword = _clean_text(keyword)

    if not resume_text or not keyword:
        return False

    variations = KEYWORD_ALIASES.get(
        keyword,
        [keyword],
    )

    return any(
        _phrase_exists(
            resume_text,
            variation,
        )
        for variation in variations
    )


# ============================================================
# MAIN RESUME ANALYSIS
# ============================================================

def analyze_resume_against_job(
    resume_text: str,
    job_description: str,
    job_skills: str = "",
) -> Dict:
    """
    Main NexusAI local AI resume screening function.

    It combines:

    1. Exact job keyword matching
    2. Recruiter-entered skills
    3. Missing keyword detection
    4. Sentence Transformer semantic similarity
    5. ATS score
    6. Strengths
    7. Improvement suggestions

    IMPORTANT:

    Missing keywords are NEVER added automatically
    to the student's resume.
    """

    resume_text = resume_text or ""
    job_description = job_description or ""
    job_skills = job_skills or ""

    # --------------------------------------------------------
    # Normalize
    # --------------------------------------------------------

    resume_clean = _clean_text(
        resume_text
    )

    job_clean = _clean_text(
        job_description
    )

    # --------------------------------------------------------
    # Extract keywords
    # --------------------------------------------------------

    description_keywords = _extract_keywords(
        job_clean
    )

    recruiter_keywords = _extract_job_skills(
        job_skills
    )

    # --------------------------------------------------------
    # Combine required job keywords
    # --------------------------------------------------------

    required_keywords = []

    for keyword in (
        description_keywords
        + recruiter_keywords
    ):

        keyword = _clean_text(
            keyword
        )

        if not keyword:
            continue

        if keyword == "microsoft office":
            keyword = "ms office"

        if keyword == "react.js":
            keyword = "react"

        if keyword == "reactjs":
            keyword = "react"

        if keyword in {"node", "nodejs"}:
            keyword = "node.js"

        if keyword == "nextjs":
            keyword = "next.js"

        if keyword == "postgres":
            keyword = "postgresql"

        if keyword in {
            "rest",
            "rest apis",
        }:
            keyword = "rest api"

        if keyword not in required_keywords:
            required_keywords.append(
                keyword
            )

    # --------------------------------------------------------
    # MATCH / MISSING KEYWORDS
    # --------------------------------------------------------

    matched_keywords = []
    missing_keywords = []

    for keyword in required_keywords:

        if _keyword_matches_resume(
            resume_clean,
            keyword,
        ):
            matched_keywords.append(
                keyword
            )
        else:
            missing_keywords.append(
                keyword
            )

    # --------------------------------------------------------
    # KEYWORD SCORE
    # --------------------------------------------------------

    if required_keywords:

        keyword_score = (
            len(matched_keywords)
            / len(required_keywords)
        )

    else:
        keyword_score = 0.0

    # --------------------------------------------------------
    # SEMANTIC AI SCORE
    # --------------------------------------------------------

    semantic_score = _semantic_similarity(
        resume_text,
        (
            f"{job_description}\n"
            f"Required skills: {job_skills}"
        ),
    )

    # --------------------------------------------------------
    # COMBINED ATS SCORE
    # --------------------------------------------------------

    if required_keywords:

        ats_score = (
            keyword_score * 60
            + semantic_score * 40
        )

    else:

        ats_score = (
            semantic_score * 100
        )

    ats_score = round(
        max(
            0.0,
            min(
                100.0,
                ats_score,
            ),
        )
    )

    # --------------------------------------------------------
    # STRENGTHS
    # --------------------------------------------------------

    strengths = []

    if matched_keywords:

        strengths.append(
            "Resume matches these job requirements: "
            + ", ".join(
                matched_keywords[:8]
            )
            + "."
        )

    if semantic_score >= 0.70:

        strengths.append(
            "The resume has strong semantic relevance "
            "to the job description."
        )

    elif semantic_score >= 0.50:

        strengths.append(
            "The resume has moderate semantic relevance "
            "to the job description."
        )

    if not strengths:

        strengths.append(
            "The resume was analyzed against the "
            "provided job description."
        )

    # --------------------------------------------------------
    # SUGGESTIONS
    # --------------------------------------------------------

    suggestions = []

    if missing_keywords:

        suggestions.append(
            "Review the missing job keywords and add "
            "them only where they genuinely match "
            "your skills or experience."
        )

    if semantic_score < 0.50:

        suggestions.append(
            "Consider tailoring your resume summary "
            "and project descriptions to the job requirements."
        )

    if not suggestions:

        suggestions.append(
            "Your resume is reasonably aligned with "
            "the provided job description."
        )

    # --------------------------------------------------------
    # RETURN RESULT
    # --------------------------------------------------------

    return {
        "ats_score": ats_score,

        "matched_keywords": matched_keywords,

        "missing_keywords": missing_keywords,

        "strengths": strengths,

        "suggestions": suggestions,

        "ai_powered": True,

        "semantic_similarity": round(
            semantic_score,
            3,
        ),

        "keyword_match_percentage": round(
            keyword_score * 100,
            1,
        ),

        "raw_response": (
            "NexusAI local AI screening completed "
            "using Sentence Transformers."
        ),
    }