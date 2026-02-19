"""
KMITL Skill Mapping Data Loader
================================
Loads and provides access to KMITL skill mapping data from JSON files.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from functools import lru_cache

DATA_DIR = Path(__file__).parent.parent / "data"


@lru_cache(maxsize=1)
def load_subjects() -> Dict:
    """Load subjects data with skills mapping"""
    with open(DATA_DIR / "kmitl_subjects.json", "r", encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=1)
def load_hard_skills() -> Dict:
    """Load hard skills with level descriptions"""
    with open(DATA_DIR / "kmitl_hard_skills.json", "r", encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=1)
def load_soft_skills() -> Dict:
    """Load soft skills with level descriptions"""
    with open(DATA_DIR / "kmitl_soft_skills.json", "r", encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=1)
def load_jobs() -> Dict:
    """Load jobs with required skills"""
    with open(DATA_DIR / "kmitl_jobs.json", "r", encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=1)
def load_job_fields() -> Dict:
    """Load job fields"""
    with open(DATA_DIR / "kmitl_job_fields.json", "r", encoding="utf-8") as f:
        return json.load(f)


def get_subject_by_code(code: str) -> Optional[Dict]:
    """Find subject by course code"""
    data = load_subjects()
    for subject in data.get("subjects", []):
        if subject["code"] == code:
            return subject
    return None


def get_subject_by_name(name: str) -> Optional[Dict]:
    """Find subject by name (case-insensitive partial match)"""
    data = load_subjects()
    name_upper = name.upper().strip()

    for subject in data.get("subjects", []):
        subject_name = (subject.get("name_en") or "").upper().strip()
        if subject_name == name_upper:
            return subject
        if name_upper in subject_name or subject_name in name_upper:
            return subject

    return None


def get_hard_skill_by_id(skill_id: str) -> Optional[Dict]:
    """Get hard skill details by ID"""
    data = load_hard_skills()
    for skill in data.get("hard_skills", []):
        if skill["id"] == skill_id:
            return skill
    return None


def get_hard_skill_by_name(name: str) -> Optional[Dict]:
    """Get hard skill details by name"""
    data = load_hard_skills()
    name_upper = name.upper().strip()
    for skill in data.get("hard_skills", []):
        if (skill.get("name_en") or "").upper().strip() == name_upper:
            return skill
    return None


def get_soft_skill_by_id(skill_id: str) -> Optional[Dict]:
    """Get soft skill details by ID"""
    data = load_soft_skills()
    for skill in data.get("soft_skills", []):
        if skill["id"] == skill_id:
            return skill
    return None


def get_job_by_id(job_id: str) -> Optional[Dict]:
    """Get job details by ID"""
    data = load_jobs()
    for job in data.get("jobs", []):
        if job["id"] == job_id:
            return job
    return None


def get_all_jobs() -> List[Dict]:
    """Get all jobs"""
    data = load_jobs()
    return data.get("jobs", [])


def get_skill_level_description(skill_id: str, level: int, skill_type: str = "hard") -> str:
    """Get the description for a specific skill level"""
    if skill_type == "hard":
        skill = get_hard_skill_by_id(skill_id)
    else:
        skill = get_soft_skill_by_id(skill_id)

    if skill and "levels" in skill:
        level_data = skill["levels"].get(str(level), {})
        return level_data.get("description_th") or level_data.get("description_en") or ""

    return ""
