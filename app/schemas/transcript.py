from pydantic import BaseModel
from typing import List, Optional, Dict


class CourseInfo(BaseModel):
    course_code: str
    course_name: str
    credits: int
    grade: str
    grade_point: Optional[float] = None


class StudentInfo(BaseModel):
    name: str
    student_id: str
    major: str
    degree: str
    cumulative_gpa: float
    total_credits: int


class TranscriptAnalysisResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    student_info: Optional[StudentInfo] = None
    courses: Optional[List[CourseInfo]] = None
    domain_scores: Optional[Dict[str, float]] = None
    strengths: Optional[List[str]] = None
    job_recommendations: Optional[List[str]] = None
    summary: Optional[Dict] = None
