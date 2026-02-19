import re
import pdfplumber
from typing import Dict, List, Tuple, Optional
from ..schemas.transcript import CourseInfo, StudentInfo


class TranscriptAnalyzer:
    # Grade Points
    GRADE_POINTS = {
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
        "IP": None  # In Progress (currently studying)
    }

    # Course Categories
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

    # Job Recommendations
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

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from PDF file"""
        text = ""
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text

    def is_scanned_pdf(self, text: str) -> bool:
        """Check if PDF is scanned (has less than 100 characters)"""
        return len(text.strip()) < 100

    def parse_student_info(self, text: str) -> Optional[StudentInfo]:
        """Parse student information from transcript - flexible patterns for multiple formats"""

        # Multiple patterns for each field to support different transcript formats
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

        # Try multiple patterns for each field
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

        # At least need name OR student_id to proceed
        if not name and not student_id:
            return None

        return StudentInfo(
            name=name if name else "N/A",
            student_id=student_id if student_id else "N/A",
            major=major if major else "N/A",
            degree=degree if degree else "N/A",
            cumulative_gpa=gpa,
            total_credits=credits
        )

    def parse_courses(self, text: str) -> List[CourseInfo]:
        """Parse courses from transcript - handle both with and without grades"""

        courses = []
        seen_courses = set()  # To avoid duplicates

        # Pattern 1: Course with grade (8-digit code, name, credits, grade)
        pattern_with_grade = r"(\d{8})\s+([A-Z][A-Z\s\&\-\.\/\(\)0-9]+?)\s+(\d)\s+([ABCDFSWU][+\-]?)(?=\s|$)"

        # Pattern 2: Course without grade (8-digit code, name, credits only)
        # Must end with newline or be followed by non-uppercase letter
        pattern_no_grade = r"(\d{8})\s+([A-Z][A-Z\s\&\-\.\/\(\)0-9]+?)\s+(\d)(?=\s*(?:\n|GPS|$))"

        # First, find all courses with grades
        for match in re.finditer(pattern_with_grade, text):
            course_code = match.group(1)
            course_name = match.group(2).strip()
            credits_str = match.group(3)
            grade = match.group(4)

            # Skip if it's a GPS/GPA line
            if 'GPS' in course_name or 'GPA' in course_name:
                continue

            credits = int(credits_str)
            grade_point = self.GRADE_POINTS.get(grade)

            # Avoid duplicates
            if course_code not in seen_courses:
                seen_courses.add(course_code)
                courses.append(CourseInfo(
                    course_code=course_code,
                    course_name=course_name,
                    credits=credits,
                    grade=grade,
                    grade_point=grade_point
                ))

        # Then, find courses without grades (current studying)
        for match in re.finditer(pattern_no_grade, text):
            course_code = match.group(1)
            course_name = match.group(2).strip()
            credits_str = match.group(3)

            # Skip if already found with grade or it's a GPS/GPA line
            if course_code in seen_courses or 'GPS' in course_name or 'GPA' in course_name:
                continue

            credits = int(credits_str)

            seen_courses.add(course_code)
            courses.append(CourseInfo(
                course_code=course_code,
                course_name=course_name,
                credits=credits,
                grade="IP",  # In Progress
                grade_point=None
            ))

        return courses

    def categorize_course(self, course_name: str) -> List[str]:
        """Categorize a course into one or more categories"""
        categories = []
        course_name_upper = course_name.upper()

        for category, keywords in self.COURSE_CATEGORIES.items():
            for keyword in keywords:
                if keyword in course_name_upper:
                    categories.append(category)
                    break

        return categories if categories else ["General/Soft Skills"]

    def calculate_domain_scores(self, courses: List[CourseInfo]) -> Dict[str, float]:
        """Calculate domain scores based on courses and grades"""
        domain_totals = {}
        domain_weights = {}

        for course in courses:
            if course.grade_point is None:  # Skip S, U, W grades
                continue

            categories = self.categorize_course(course.course_name)

            for category in categories:
                if category not in domain_totals:
                    domain_totals[category] = 0.0
                    domain_weights[category] = 0

                # Weighted by credits and grade point
                domain_totals[category] += course.grade_point * course.credits
                domain_weights[category] += course.credits

        # Calculate average scores
        domain_scores = {}
        for category in domain_totals:
            if domain_weights[category] > 0:
                avg_score = domain_totals[category] / domain_weights[category]
                domain_scores[category] = round(avg_score, 2)

        return domain_scores

    def get_top_strengths(self, domain_scores: Dict[str, float], top_n: int = 3) -> List[str]:
        """Get top N strengths based on domain scores"""
        # Sort by score descending
        sorted_domains = sorted(domain_scores.items(), key=lambda x: x[1], reverse=True)
        return [domain for domain, score in sorted_domains[:top_n]]

    def get_job_recommendations(self, strengths: List[str]) -> List[str]:
        """Get job recommendations based on top strengths"""
        recommendations = []

        for strength in strengths:
            if strength in self.JOB_RECOMMENDATIONS:
                recommendations.extend(self.JOB_RECOMMENDATIONS[strength])

        # Remove duplicates while preserving order
        seen = set()
        unique_recommendations = []
        for job in recommendations:
            if job not in seen:
                seen.add(job)
                unique_recommendations.append(job)

        return unique_recommendations[:6]  # Return top 6 recommendations

    def analyze(self, pdf_path: str) -> Dict:
        """Main analysis function"""
        try:
            # Extract text from PDF
            text = self.extract_text_from_pdf(pdf_path)

            # Check if scanned PDF
            if self.is_scanned_pdf(text):
                return {
                    "success": False,
                    "message": "This PDF appears to be scanned. Scanned PDFs are not supported yet."
                }

            # Parse student info
            student_info = self.parse_student_info(text)
            if not student_info:
                return {
                    "success": False,
                    "message": "Unable to parse student information from transcript."
                }

            # Parse courses
            courses = self.parse_courses(text)
            if not courses:
                return {
                    "success": False,
                    "message": "Unable to parse courses from transcript."
                }

            # Calculate domain scores
            domain_scores = self.calculate_domain_scores(courses)

            # Get top strengths
            strengths = self.get_top_strengths(domain_scores)

            # Get job recommendations
            job_recommendations = self.get_job_recommendations(strengths)

            # Prepare summary
            summary = {
                "total_courses": len(courses),
                "total_credits": student_info.total_credits,
                "cumulative_gpa": student_info.cumulative_gpa
            }

            return {
                "success": True,
                "student_info": student_info.dict(),
                "courses": [course.dict() for course in courses],
                "domain_scores": domain_scores,
                "strengths": strengths,
                "job_recommendations": job_recommendations,
                "summary": summary
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"Error analyzing transcript: {str(e)}"
            }

    def analyze_debug(self, pdf_path: str) -> Dict:
        """Debug analysis function with detailed information for teachers"""
        try:
            # Extract text from PDF
            text = self.extract_text_from_pdf(pdf_path)
            text_length = len(text)

            # Check if scanned PDF
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

            # Parse student info with debug details
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

            # Parse courses with debug details
            courses = self.parse_courses(text)
            courses_with_grade = [c for c in courses if c.grade != "IP"]
            courses_in_progress = [c for c in courses if c.grade == "IP"]

            # Get categorization details for ALL courses
            categorization_details = []
            for course in courses:  # Show all courses
                categories = self.categorize_course(course.course_name)
                matched_keywords = []

                for category in categories:
                    if category in self.COURSE_CATEGORIES:
                        for keyword in self.COURSE_CATEGORIES[category]:
                            if keyword in course.course_name.upper():
                                matched_keywords.append(keyword)
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

            # Calculate domain scores
            domain_scores = self.calculate_domain_scores(courses)

            # Get top strengths
            strengths = self.get_top_strengths(domain_scores)

            # Get job recommendations
            job_recommendations = self.get_job_recommendations(strengths)

            # Prepare summary
            summary = {
                "total_courses": len(courses),
                "total_credits": student_info.total_credits,
                "cumulative_gpa": student_info.cumulative_gpa
            }

            # Prepare parsed courses (after regex, before categorization)
            parsed_courses_raw = []
            for course in courses:
                parsed_courses_raw.append({
                    "course_code": course.course_code,
                    "course_name": course.course_name,
                    "credits": course.credits,
                    "grade": course.grade
                })

            # Prepare debug info
            debug_info = {
                "raw_text": text,  # Full raw text
                "text_length": text_length,
                "is_scanned": is_scanned,
                "student_info_debug": student_info_debug,
                "parsed_courses_raw": parsed_courses_raw,  # Courses after regex parsing
                "courses_stats": {
                    "total_courses": len(courses),
                    "courses_with_grade": len(courses_with_grade),
                    "courses_in_progress": len(courses_in_progress)
                },
                "categorization_details": categorization_details,
                "regex_patterns_info": {
                    "total_categories": len(self.COURSE_CATEGORIES),
                    "categories": list(self.COURSE_CATEGORIES.keys())
                }
            }

            return {
                "success": True,
                "student_info": student_info.dict(),
                "courses": [course.dict() for course in courses],
                "domain_scores": domain_scores,
                "strengths": strengths,
                "job_recommendations": job_recommendations,
                "summary": summary,
                "debug_info": debug_info
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"Error analyzing transcript: {str(e)}",
                "debug_info": {
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            }
