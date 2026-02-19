"""
Transcript Analyzer with KMITL Skill Mapping
============================================
Analyzes academic transcripts and calculates skill scores using KMITL data.

Calculation Formula (from CEPP68-19 Report #4):
1. Skill Score (per subject) = LevelWeight × GradeScore
2. Total Category Score = Σ Skill Scores for all subjects
3. Max Possible Score = Σ (LevelWeight × 4.0)
4. Category Percentage = (Total Score / Max Score) × 100
5. User Level derived from percentage (80%=5, 60%=4, 40%=3, 20%=2, else=1)

Job Matching:
  Hard/Soft Skills Score = avg(min(user_level / required_level, 1.0)) × 100
  Overall Score = (Hard Skills Score × 0.5) + (Soft Skills Score × 0.5)
"""

import re
import pdfplumber
from typing import Dict, List, Optional
from ..schemas.transcript import CourseInfo, StudentInfo
from .kmitl_data_loader import (
    load_subjects, load_hard_skills, load_soft_skills,
    get_all_jobs,
)


class TranscriptAnalyzer:

    # Grade to score mapping
    GRADE_SCORES = {
        "A": 4.0,
        "B+": 3.5,
        "B": 3.0,
        "C+": 2.5,
        "C": 2.0,
        "D+": 1.5,
        "D": 1.0,
        "F": 0.0,
        "S": None,
        "U": None,
        "W": None,
        "I": None,
        "IP": None,
    }

    # Keep for backward-compat (analyze_debug still uses these)
    GRADE_POINTS = GRADE_SCORES

    COURSE_CATEGORIES = {
        "Programming/Backend": [
            "PROGRAMMING", "OBJECT ORIENTED", "DATA STRUCTURE",
            "SOFTWARE DEVELOPMENT", "ALGORITHM"
        ],
        "Frontend/Web": [
            "WEB APPLICATION", "WEB DEVELOPMENT", "FRONTEND"
        ],
        "UX/UI Design": [
            "USER EXPERIENCE", "USER INTERFACE", "UX", "UI DESIGN"
        ],
        "Database": [
            "DATABASE", "SQL", "DATA MANAGEMENT"
        ],
        "Networks": [
            "NETWORK", "INTERNETWORKING", "COMMUNICATION PROTOCOL"
        ],
        "Cloud/DevOps": [
            "CLOUD", "DEVOPS", "CONTAINER", "KUBERNETES"
        ],
        "Security": [
            "SECURITY", "HACKING", "PENETRATION", "CRYPTOGRAPHY", "CYBER"
        ],
        "Hardware/Embedded": [
            "MICROCONTROLLER", "CIRCUITS", "ELECTRONICS", "EMBEDDED",
            "DIGITAL SYSTEM", "COMPUTER ORGANIZATION", "ARCHITECTURE"
        ],
        "OS/Systems": [
            "OPERATING SYSTEM", "PLATFORM ADMINISTRATION", "LINUX", "UNIX"
        ],
        "AI/ML/Data Science": [
            "MACHINE LEARNING", "ARTIFICIAL INTELLIGENCE", "AI", "ML",
            "DATA SCIENCE", "DEEP LEARNING"
        ],
        "Math/Statistics": [
            "CALCULUS", "DISCRETE", "DIFFERENTIAL", "LINEAR ALGEBRA",
            "PROBABILITY", "STATISTICS", "COMPUTATION"
        ],
        "General/Soft Skills": [
            "ENGLISH", "MANAGEMENT", "LEADERSHIP", "COMMUNICATION",
            "FOUNDATION", "SOCIETY", "BUSINESS"
        ]
    }

    JOB_RECOMMENDATIONS = {
        "Frontend/Web": ["Frontend Developer", "Web Developer", "React Developer"],
        "Programming/Backend": ["Backend Developer", "Software Engineer", "Python Developer"],
        "UX/UI Design": ["UX Designer", "UI Designer", "Product Designer"],
        "Database": ["Database Administrator", "Data Engineer"],
        "Networks": ["Network Engineer", "System Administrator"],
        "Cloud/DevOps": ["DevOps Engineer", "Cloud Engineer", "SRE"],
        "Security": ["Security Engineer", "Penetration Tester", "Security Analyst"],
        "Hardware/Embedded": ["Embedded Engineer", "IoT Developer", "Firmware Engineer"],
        "OS/Systems": ["System Administrator", "Platform Engineer"],
        "AI/ML/Data Science": ["ML Engineer", "Data Scientist", "AI Engineer"]
    }

    def __init__(self):
        self._subjects_data = load_subjects()
        self._hard_skills_data = load_hard_skills()
        self._soft_skills_data = load_soft_skills()
        self._build_lookups()

    # ------------------------------------------------------------------
    # Lookup helpers
    # ------------------------------------------------------------------

    def _build_lookups(self):
        """Build in-memory lookup dicts for fast subject/skill access"""
        self._subject_by_code = {}
        self._subject_by_name = {}
        for subject in self._subjects_data.get("subjects", []):
            self._subject_by_code[subject["code"]] = subject
            name = (subject.get("name_en") or "").upper().strip()
            if name:
                self._subject_by_name[name] = subject

        self._hard_skill_by_id = {
            s["id"]: s for s in self._hard_skills_data.get("hard_skills", [])
        }
        self._soft_skill_by_id = {
            s["id"]: s for s in self._soft_skills_data.get("soft_skills", [])
        }

    # ------------------------------------------------------------------
    # PDF / parse methods (unchanged from original)
    # ------------------------------------------------------------------

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        text = ""
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text

    def is_scanned_pdf(self, text: str) -> bool:
        return len(text.strip()) < 100

    def parse_student_info(self, text: str) -> Optional[StudentInfo]:
        name_patterns = [
            r"Name[:\s]+(?:Mr\.|Mrs\.|Ms\.|Miss)?\s*([A-Za-zก-๙\s\-]+?)(?:\n|Date of Birth)",
            r"(?:Name|ชื่อ|ชื่อ-สกุล)[:\s]+([A-Za-zก-๙\s]+?)(?:\n|Student|รหัส|ID)",
            r"(?:Student Name|ชื่อนักศึกษา)[:\s]+([A-Za-zก-๙\s]+?)(?:\n|Student|รหัส|ID)",
            r"ชื่อ[:\s]*([ก-๙\s]+?)(?:\n|รหัส)"
        ]
        student_id_patterns = [
            r"Student ID[:\s]*(\d{8,})",
            r"(?:Student ID|รหัสนักศึกษา|รหัส)[:\s]+(\d{8,})",
            r"(?:ID|StudentID)[:\s]+(\d{8,})",
            r"รหัส[:\s]*(\d{8,})"
        ]
        major_patterns = [
            r"Major\s+([A-Za-z\s\-]+?(?:\s*\([A-Za-z\s]+\))?)\s+COURSE",
            r"Major\s+([A-Za-z\s\-]+?(?:\s*\([A-Za-z\s]+\))?)\s*\n",
            r"(?:สาขา|สาขาวิชา)\s+([ก-๙\s\-]+?(?:\s*\([ก-๙\s]+\))?)\s*\n"
        ]
        degree_patterns = [
            r"Degree\s+([A-Za-z\s\.]+?(?:\s*\([A-Za-z\s]+\))?)\s+Major",
            r"Degree\s+([A-Za-z\s\.]+?(?:\s*\([A-Za-z\s]+\))?)\s*\n",
            r"(?:ระดับ|ระดับการศึกษา)\s+([ก-๙\s\.]+?(?:\s*\([ก-๙\s]+\))?)\s*\n"
        ]
        gpa_patterns = [
            r"Cumulative GPA[:\s]+([\d.]+)",
            r"(?:Cumulative GPA|CGPA|GPA|เกรดเฉลี่ย|เกรดเฉลี่ยสะสม)[:\s]+([\d.]+)",
            r"(?:Grade Point Average|Overall GPA)[:\s]+([\d.]+)",
            r"(?:GPAX)[:\s]+([\d.]+)"
        ]
        credits_patterns = [
            r"Total number of credit earned[:\s]*(\d+)",
            r"(?:Total Credits|หน่วยกิตสะสม|หน่วยกิต|Credits)[:\s]+(\d+)",
            r"(?:Earned Credits|Credits Earned)[:\s]+(\d+)",
            r"หน่วยกิต[:\s]*(\d+)"
        ]

        def try_patterns(patterns, text):
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    return match.group(1).strip()
            return None

        name = try_patterns(name_patterns, text)
        student_id = try_patterns(student_id_patterns, text)
        major = try_patterns(major_patterns, text)
        degree = try_patterns(degree_patterns, text)
        gpa_str = try_patterns(gpa_patterns, text)
        gpa = float(gpa_str) if gpa_str else 0.0
        credits_str = try_patterns(credits_patterns, text)
        credits = int(credits_str) if credits_str else 0

        if not name and not student_id:
            return None

        return StudentInfo(
            name=name or "N/A",
            student_id=student_id or "N/A",
            major=major or "N/A",
            degree=degree or "N/A",
            cumulative_gpa=gpa,
            total_credits=credits
        )

    def parse_courses(self, text: str) -> List[CourseInfo]:
        courses = []
        seen_courses = set()

        pattern_with_grade = r"(\d{8})\s+([A-Z][A-Z\s\&\-\.\/\(\)0-9]+?)\s+(\d)\s+([ABCDFSWU][+\-]?)(?=\s|$)"
        pattern_no_grade = r"(\d{8})\s+([A-Z][A-Z\s\&\-\.\/\(\)0-9]+?)\s+(\d)(?=\s*(?:\n|GPS|$))"

        for match in re.finditer(pattern_with_grade, text):
            course_code = match.group(1)
            course_name = match.group(2).strip()
            grade = match.group(4)
            if 'GPS' in course_name or 'GPA' in course_name:
                continue
            if course_code not in seen_courses:
                seen_courses.add(course_code)
                courses.append(CourseInfo(
                    course_code=course_code,
                    course_name=course_name,
                    credits=int(match.group(3)),
                    grade=grade,
                    grade_point=self.GRADE_SCORES.get(grade)
                ))

        for match in re.finditer(pattern_no_grade, text):
            course_code = match.group(1)
            course_name = match.group(2).strip()
            if course_code in seen_courses or 'GPS' in course_name or 'GPA' in course_name:
                continue
            seen_courses.add(course_code)
            courses.append(CourseInfo(
                course_code=course_code,
                course_name=course_name,
                credits=int(match.group(3)),
                grade="IP",
                grade_point=None
            ))

        return courses

    # ------------------------------------------------------------------
    # Legacy methods — still used by analyze_debug
    # ------------------------------------------------------------------

    def categorize_course(self, course_name: str) -> List[str]:
        categories = []
        course_name_upper = course_name.upper()
        for category, keywords in self.COURSE_CATEGORIES.items():
            for keyword in keywords:
                if keyword in course_name_upper:
                    categories.append(category)
                    break
        return categories if categories else ["General/Soft Skills"]

    def calculate_domain_scores(self, courses: List[CourseInfo]) -> Dict[str, float]:
        domain_totals: Dict[str, float] = {}
        domain_weights: Dict[str, int] = {}
        for course in courses:
            if course.grade_point is None:
                continue
            for category in self.categorize_course(course.course_name):
                domain_totals.setdefault(category, 0.0)
                domain_weights.setdefault(category, 0)
                domain_totals[category] += course.grade_point * course.credits
                domain_weights[category] += course.credits
        return {
            cat: round(domain_totals[cat] / domain_weights[cat], 2)
            for cat in domain_totals if domain_weights[cat] > 0
        }

    def get_top_strengths(self, domain_scores: Dict[str, float], top_n: int = 3) -> List[str]:
        return [d for d, _ in sorted(domain_scores.items(), key=lambda x: x[1], reverse=True)[:top_n]]

    def get_job_recommendations(self, strengths: List[str]) -> List[str]:
        seen: set = set()
        result: List[str] = []
        for strength in strengths:
            for job in self.JOB_RECOMMENDATIONS.get(strength, []):
                if job not in seen:
                    seen.add(job)
                    result.append(job)
        return result[:6]

    # ------------------------------------------------------------------
    # KMITL skill calculation
    # ------------------------------------------------------------------

    def find_subject_in_kmitl_data(self, course_code: str, course_name: str) -> Optional[Dict]:
        """Match a transcript course to KMITL subject by code, then by name"""
        if course_code in self._subject_by_code:
            return self._subject_by_code[course_code]

        name_upper = course_name.upper().strip()
        if name_upper in self._subject_by_name:
            return self._subject_by_name[name_upper]

        for subject_name, subject in self._subject_by_name.items():
            if name_upper in subject_name or subject_name in name_upper:
                return subject

        return None

    def calculate_skill_scores(self, courses: List[CourseInfo]) -> Dict:
        """
        Calculate skill scores using KMITL formula.

        Skill Score (per subject) = LevelWeight × GradeScore
        Total Score  = Σ Skill Scores
        Max Score    = Σ (LevelWeight × 4.0)
        Percentage   = (Total / Max) × 100
        """
        hard_skills: Dict[str, Dict] = {}
        soft_skills: Dict[str, Dict] = {}
        unmatched_courses = []

        for course in courses:
            grade_score = self.GRADE_SCORES.get(course.grade)
            if grade_score is None:
                continue

            subject = self.find_subject_in_kmitl_data(course.course_code, course.course_name)
            if not subject:
                unmatched_courses.append({
                    "course_code": course.course_code,
                    "course_name": course.course_name,
                    "credits": course.credits,
                    "grade": course.grade
                })
                continue

            for skill_info in subject.get("hard_skills", []):
                skill_id = skill_info["skill_id"]
                skill_key = skill_info["skill_name_en"].upper()
                level_weight = skill_info["level"]
                if skill_key not in hard_skills:
                    hard_skills[skill_key] = {
                        "skill_id": skill_id,
                        "skill_name_en": skill_info["skill_name_en"],
                        "skill_name_th": skill_info.get("skill_name_th", ""),
                        "total_score": 0.0,
                        "max_score": 0.0,
                        "contributing_courses": []
                    }
                skill_score = level_weight * grade_score
                hard_skills[skill_key]["total_score"] += skill_score
                hard_skills[skill_key]["max_score"] += level_weight * 4.0
                hard_skills[skill_key]["contributing_courses"].append({
                    "course_code": course.course_code,
                    "course_name": course.course_name,
                    "grade": course.grade,
                    "grade_score": grade_score,
                    "skill_level": level_weight,
                    "skill_score": round(skill_score, 2)
                })

            for skill_info in subject.get("soft_skills", []):
                skill_id = skill_info["skill_id"]
                skill_key = skill_info["skill_name_en"].upper()
                level_weight = skill_info["level"]
                if skill_key not in soft_skills:
                    soft_skills[skill_key] = {
                        "skill_id": skill_id,
                        "skill_name_en": skill_info["skill_name_en"],
                        "skill_name_th": skill_info.get("skill_name_th", ""),
                        "total_score": 0.0,
                        "max_score": 0.0,
                        "contributing_courses": []
                    }
                skill_score = level_weight * grade_score
                soft_skills[skill_key]["total_score"] += skill_score
                soft_skills[skill_key]["max_score"] += level_weight * 4.0
                soft_skills[skill_key]["contributing_courses"].append({
                    "course_code": course.course_code,
                    "course_name": course.course_name,
                    "grade": course.grade,
                    "grade_score": grade_score,
                    "skill_level": level_weight,
                    "skill_score": round(skill_score, 2)
                })

        # Finalize percentages and levels
        for skill_key, data in hard_skills.items():
            pct = (data["total_score"] / data["max_score"] * 100) if data["max_score"] > 0 else 0
            data["percentage"] = round(pct, 1)
            data["level"] = self._percentage_to_level(pct)
            level_info = self._hard_skill_by_id.get(data["skill_id"], {}).get("levels", {}).get(str(data["level"]), {})
            data["level_description_en"] = level_info.get("description_en", "")
            data["level_description_th"] = level_info.get("description_th", "")

        for skill_key, data in soft_skills.items():
            pct = (data["total_score"] / data["max_score"] * 100) if data["max_score"] > 0 else 0
            data["percentage"] = round(pct, 1)
            data["level"] = self._percentage_to_level(pct)
            level_info = self._soft_skill_by_id.get(data["skill_id"], {}).get("levels", {}).get(str(data["level"]), {})
            data["level_description_en"] = level_info.get("description_en", "")
            data["level_description_th"] = level_info.get("description_th", "")

        return {"hard_skills": hard_skills, "soft_skills": soft_skills, "unmatched_courses": unmatched_courses}

    def _percentage_to_level(self, percentage: float) -> int:
        """Convert percentage score to skill level 1-5"""
        if percentage >= 80:
            return 5
        elif percentage >= 60:
            return 4
        elif percentage >= 40:
            return 3
        elif percentage >= 20:
            return 2
        return 1

    # ------------------------------------------------------------------
    # Job matching
    # ------------------------------------------------------------------

    def calculate_job_matching(self, user_skills: Dict) -> List[Dict]:
        """
        Match user skill levels against each job's required levels.

        NOTE: Currently using Hard Skills ONLY for matching score.
        Soft Skills data is kept but not included in overall calculation.
        """
        user_hard = user_skills.get("hard_skills", {})
        user_soft = user_skills.get("soft_skills", {})
        results = []

        for job in get_all_jobs():
            hard_scores, hard_details, missing_hard = [], [], []
            for req in job.get("required_hard_skills", []):
                sid = req["skill_id"]
                skill_name = req["skill_name_en"].strip().upper()
                req_lvl = req["required_level"]

                user_skill = None
                for key, val in user_hard.items():
                    if key == skill_name or val.get("skill_name_en", "").strip().upper() == skill_name:
                        user_skill = val
                        break

                if user_skill:
                    u_lvl = user_skill["level"]
                    u_pct = user_skill["percentage"]
                    score = min(u_lvl / req_lvl, 1.0) if req_lvl > 0 else 1.0
                    hard_scores.append(score)
                    status = "exceeded" if u_lvl > req_lvl else ("met" if u_lvl == req_lvl else "below")
                    hard_details.append({
                        "skill_id": sid,
                        "skill_name_en": req["skill_name_en"],
                        "required_level": req_lvl,
                        "user_level": u_lvl,
                        "user_percentage": u_pct,
                        "status": status,
                        "gap": max(0, req_lvl - u_lvl),
                        "score": round(score, 3)
                    })
                else:
                    hard_scores.append(0)
                    missing_hard.append({
                        "skill_id": sid,
                        "skill_name_en": req["skill_name_en"],
                        "required_level": req_lvl
                    })
                    hard_details.append({
                        "skill_id": sid,
                        "skill_name_en": req["skill_name_en"],
                        "required_level": req_lvl,
                        "user_level": 0,
                        "user_percentage": 0,
                        "status": "missing",
                        "gap": req_lvl,
                        "score": 0
                    })

            # Soft skills - calculate but don't include in overall score
            soft_scores, soft_details, missing_soft = [], [], []
            for req in job.get("required_soft_skills", []):
                sid = req["skill_id"]
                skill_name = req["skill_name_en"].strip().upper()
                req_lvl = req["required_level"]

                user_skill = None
                for key, val in user_soft.items():
                    if key == skill_name or val.get("skill_name_en", "").strip().upper() == skill_name:
                        user_skill = val
                        break

                if user_skill:
                    u_lvl = user_skill["level"]
                    u_pct = user_skill["percentage"]
                    score = min(u_lvl / req_lvl, 1.0) if req_lvl > 0 else 1.0
                    soft_scores.append(score)
                    status = "exceeded" if u_lvl > req_lvl else ("met" if u_lvl == req_lvl else "below")
                    soft_details.append({
                        "skill_id": sid,
                        "skill_name_en": req["skill_name_en"],
                        "required_level": req_lvl,
                        "user_level": u_lvl,
                        "user_percentage": u_pct,
                        "status": status,
                        "gap": max(0, req_lvl - u_lvl),
                        "score": round(score, 3)
                    })
                else:
                    soft_scores.append(0)
                    missing_soft.append({
                        "skill_id": sid,
                        "skill_name_en": req["skill_name_en"],
                        "required_level": req_lvl
                    })
                    soft_details.append({
                        "skill_id": sid,
                        "skill_name_en": req["skill_name_en"],
                        "required_level": req_lvl,
                        "user_level": 0,
                        "user_percentage": 0,
                        "status": "missing",
                        "gap": req_lvl,
                        "score": 0
                    })

            # Calculate scores — overall uses Hard Skills ONLY
            hard_score = (sum(hard_scores) / len(hard_scores) * 100) if hard_scores else 0
            soft_score = (sum(soft_scores) / len(soft_scores) * 100) if soft_scores else 0
            overall = hard_score

            results.append({
                "job_id": job["id"],
                "job_name_en": job["name_en"],
                "job_field": job.get("job_field"),
                "job_group": job.get("job_group"),
                "overall_score": round(overall, 1),
                "hard_skills_score": round(hard_score, 1),
                "soft_skills_score": round(soft_score, 1),
                "hard_skill_details": hard_details,
                "soft_skill_details": soft_details,
                "missing_hard_skills": missing_hard,
                "missing_soft_skills": missing_soft,
                "stats": {
                    "total_required_hard_skills": len(job.get("required_hard_skills", [])),
                    "matched_hard_skills": len([d for d in hard_details if d["status"] != "missing"]),
                    "total_required_soft_skills": len(job.get("required_soft_skills", [])),
                    "matched_soft_skills": len([d for d in soft_details if d["status"] != "missing"])
                }
            })

        results.sort(key=lambda x: x["overall_score"], reverse=True)
        return results

    def get_top_skills(self, skill_scores: Dict, top_n: int = 5) -> List[Dict]:
        """Return top N hard skills by percentage"""
        skills = list(skill_scores.get("hard_skills", {}).values())
        skills.sort(key=lambda x: x["percentage"], reverse=True)
        return skills[:top_n]

    # ------------------------------------------------------------------
    # Main entry points
    # ------------------------------------------------------------------

    def analyze(self, pdf_path: str) -> Dict:
        """Analyze transcript using KMITL skill mapping data"""
        try:
            text = self.extract_text_from_pdf(pdf_path)

            if self.is_scanned_pdf(text):
                return {
                    "success": False,
                    "message": "This PDF appears to be scanned. Scanned PDFs are not supported yet."
                }

            student_info = self.parse_student_info(text)
            if not student_info:
                return {
                    "success": False,
                    "message": "Unable to parse student information from transcript."
                }

            courses = self.parse_courses(text)
            if not courses:
                return {
                    "success": False,
                    "message": "Unable to parse courses from transcript."
                }

            skill_scores = self.calculate_skill_scores(courses)
            job_recommendations = self.calculate_job_matching(skill_scores)
            top_skills = self.get_top_skills(skill_scores)

            matched_count = sum(
                1 for c in courses
                if self.find_subject_in_kmitl_data(c.course_code, c.course_name)
            )

            return {
                "success": True,
                "student_info": student_info.dict(),
                "courses": [c.dict() for c in courses],
                "skill_scores": {
                    "hard_skills": list(skill_scores["hard_skills"].values()),
                    "soft_skills": list(skill_scores["soft_skills"].values())
                },
                "job_recommendations": job_recommendations[:10],
                "top_skills": top_skills,
                "unmatched_courses": skill_scores["unmatched_courses"],
                "summary": {
                    "total_courses": len(courses),
                    "total_credits": student_info.total_credits,
                    "cumulative_gpa": student_info.cumulative_gpa,
                    "total_hard_skills": len(skill_scores["hard_skills"]),
                    "total_soft_skills": len(skill_scores["soft_skills"]),
                    "matched_subjects": matched_count
                }
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"Error analyzing transcript: {str(e)}"
            }

    def analyze_debug(self, pdf_path: str) -> Dict:
        """Debug analysis — shows raw text, regex matches, and old keyword categorization"""
        try:
            text = self.extract_text_from_pdf(pdf_path)
            text_length = len(text)
            is_scanned = self.is_scanned_pdf(text)

            if is_scanned:
                return {
                    "success": False,
                    "message": "This PDF appears to be scanned. Scanned PDFs are not supported yet.",
                    "debug_info": {
                        "raw_text": text[:1000] + "..." if len(text) > 1000 else text,
                        "text_length": text_length,
                        "is_scanned": is_scanned
                    }
                }

            student_info = self.parse_student_info(text)
            student_info_debug = {
                "found": student_info is not None,
                "name": student_info.name if student_info else None,
                "student_id": student_info.student_id if student_info else None,
                "major": student_info.major if student_info else None,
                "degree": student_info.degree if student_info else None,
                "gpa": student_info.cumulative_gpa if student_info else None,
                "credits": student_info.total_credits if student_info else None
            }

            if not student_info:
                return {
                    "success": False,
                    "message": "Unable to parse student information from transcript.",
                    "debug_info": {
                        "raw_text": text[:2000] + "..." if len(text) > 2000 else text,
                        "text_length": text_length,
                        "is_scanned": is_scanned,
                        "student_info_debug": student_info_debug
                    }
                }

            courses = self.parse_courses(text)
            courses_with_grade = [c for c in courses if c.grade != "IP"]
            courses_in_progress = [c for c in courses if c.grade == "IP"]

            categorization_details = []
            for course in courses:
                categories = self.categorize_course(course.course_name)
                matched_keywords = []
                for cat in categories:
                    for kw in self.COURSE_CATEGORIES.get(cat, []):
                        if kw in course.course_name.upper():
                            matched_keywords.append(kw)
                            break
                categorization_details.append({
                    "course_code": course.course_code,
                    "course_name": course.course_name,
                    "grade": course.grade,
                    "credits": course.credits,
                    "categories": categories,
                    "matched_keywords": matched_keywords
                })

            if not courses:
                return {
                    "success": False,
                    "message": "Unable to parse courses from transcript.",
                    "debug_info": {
                        "raw_text": text[:2000] + "..." if len(text) > 2000 else text,
                        "text_length": text_length,
                        "is_scanned": is_scanned,
                        "student_info_debug": student_info_debug
                    }
                }

            domain_scores = self.calculate_domain_scores(courses)
            strengths = self.get_top_strengths(domain_scores)
            job_recommendations = self.get_job_recommendations(strengths)

            # Also run KMITL matching for debug
            skill_scores = self.calculate_skill_scores(courses)
            matched_count = sum(
                1 for c in courses
                if self.find_subject_in_kmitl_data(c.course_code, c.course_name)
            )

            return {
                "success": True,
                "student_info": student_info.dict(),
                "courses": [c.dict() for c in courses],
                "domain_scores": domain_scores,
                "strengths": strengths,
                "job_recommendations": job_recommendations,
                "summary": {
                    "total_courses": len(courses),
                    "total_credits": student_info.total_credits,
                    "cumulative_gpa": student_info.cumulative_gpa
                },
                "debug_info": {
                    "raw_text": text,
                    "text_length": text_length,
                    "is_scanned": is_scanned,
                    "student_info_debug": student_info_debug,
                    "parsed_courses_raw": [
                        {"course_code": c.course_code, "course_name": c.course_name,
                         "credits": c.credits, "grade": c.grade}
                        for c in courses
                    ],
                    "courses_stats": {
                        "total_courses": len(courses),
                        "courses_with_grade": len(courses_with_grade),
                        "courses_in_progress": len(courses_in_progress)
                    },
                    "categorization_details": categorization_details,
                    "regex_patterns_info": {
                        "total_categories": len(self.COURSE_CATEGORIES),
                        "categories": list(self.COURSE_CATEGORIES.keys())
                    },
                    "kmitl_matching": {
                        "matched_subjects": matched_count,
                        "total_hard_skills_found": len(skill_scores["hard_skills"]),
                        "total_soft_skills_found": len(skill_scores["soft_skills"])
                    }
                }
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"Error analyzing transcript: {str(e)}",
                "debug_info": {"error": str(e), "error_type": type(e).__name__}
            }
