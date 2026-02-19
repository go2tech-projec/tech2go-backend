from pydantic import BaseModel
from typing import List, Optional, Dict, Any


class CourseInfo(BaseModel):
    course_code: str
    course_name: str
    credits: int
    grade: str
    grade_point: Optional[float] = None


class StudentInfo(BaseModel):
    name: str
    student_id: str
    major: Optional[str] = None
    degree: Optional[str] = None
    cumulative_gpa: float
    total_credits: int


class SkillScore(BaseModel):
    skill_id: str
    skill_name_en: str
    skill_name_th: Optional[str] = None
    total_score: float
    max_score: float
    percentage: float
    level: int  # 1-5
    level_description_en: Optional[str] = None
    level_description_th: Optional[str] = None
    contributing_courses: List[Dict[str, Any]]


class SkillMatchDetail(BaseModel):
    skill_id: str
    skill_name_en: str
    skill_name_th: Optional[str] = None
    required_level: int
    user_level: int
    user_percentage: float
    status: str  # exceeded | met | below | missing
    gap: int
    score: float


class JobMatch(BaseModel):
    job_id: str
    job_name_en: str
    job_field: Optional[Dict] = None
    job_group: Optional[Dict] = None
    overall_score: float
    hard_skills_score: float
    soft_skills_score: float
    hard_skill_details: List[SkillMatchDetail]
    soft_skill_details: List[SkillMatchDetail]
    missing_hard_skills: List[Dict]
    missing_soft_skills: List[Dict]
    stats: Dict


class TranscriptAnalysisResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    student_info: Optional[StudentInfo] = None
    courses: Optional[List[CourseInfo]] = None
    skill_scores: Optional[Dict[str, List[SkillScore]]] = None
    job_recommendations: Optional[List[JobMatch]] = None
    top_skills: Optional[List[SkillScore]] = None
    summary: Optional[Dict] = None
