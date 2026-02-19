"""
KMITL Skill Mapping Data Crawler (Complete Version)
====================================================
Fetches ALL data from KMITL Skill Mapping GraphQL API including:
- Jobs with required skills
- Hard Skills with descriptions, levels, related jobs & subjects
- Soft Skills with descriptions, levels, related jobs & subjects
- Subjects with skills mapping
- Job Fields

Usage:
    cd backend
    python scripts/crawl_kmitl_data.py
"""

import requests
import json
from datetime import datetime
from pathlib import Path

# Configuration
GRAPHQL_URL = "https://skill-mapping-hasura.aegis.aginix.tech/v1/graphql"
CURRICULUM_ID = "01007"
OUTPUT_DIR = Path(__file__).parent.parent / "app" / "data"


def graphql_query(query: str, variables: dict = None) -> dict:
    """Execute GraphQL query"""
    response = requests.post(
        GRAPHQL_URL,
        json={"query": query, "variables": variables or {}},
        headers={"Content-Type": "application/json"},
        timeout=30
    )
    response.raise_for_status()
    return response.json()


def save_json(data: dict, filename: str):
    """Save data to JSON file"""
    filepath = OUTPUT_DIR / filename
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Saved: {filepath}")


# ==================== GraphQL QUERIES ====================

QUERY_JOBS = """
query GetJobs($curriculum_id: String!) {
  jobs(where: {curriculum_id: {_eq: $curriculum_id}}, order_by: {name: asc}) {
    id
    name
    name_th
    description
    description_th
    job_group {
      id
      name
      name_th
      job_field {
        id
        name
        name_th
      }
    }
    hard_skills(order_by: {skill: {name: asc}}) {
      level
      skill {
        id
        name
        name_th
      }
    }
    soft_skills(order_by: {skill: {name: asc}}) {
      level
      skill {
        id
        name
        name_th
      }
    }
  }
}
"""

# Hard skills: relation names are levels/jobs/subjects (not hard_skill_levels/job_hard_skills/subject_hard_skills)
QUERY_HARD_SKILLS_DETAIL = """
query GetHardSkillsDetail($curriculum_id: String!) {
  hard_skills(where: {curriculum_id: {_eq: $curriculum_id}}, order_by: {name: asc}) {
    id
    name
    name_th
    description
    description_th
    job_field {
      id
      name
      name_th
    }
    levels(order_by: {level: asc}) {
      level
      description
      description_th
    }
    jobs(order_by: {job: {name: asc}}) {
      level
      job {
        id
        name
        name_th
      }
    }
    subjects(order_by: {subject: {name: asc}}) {
      level
      subject {
        id
        code
        name
        name_th
      }
    }
  }
}
"""

# Soft skills: no curriculum_id field — fetch all, filter related jobs to curriculum
QUERY_SOFT_SKILLS_DETAIL = """
query GetSoftSkillsDetail($curriculum_id: String!) {
  soft_skills(order_by: {name: asc}) {
    id
    name
    name_th
    description
    description_th
    levels(order_by: {level: asc}) {
      level
      description
      description_th
    }
    jobs(
      where: {job: {curriculum_id: {_eq: $curriculum_id}}},
      order_by: {job: {name: asc}}
    ) {
      level
      job {
        id
        name
        name_th
      }
    }
    subjects(
      where: {subject: {curriculum_subjects: {curriculum_id: {_eq: $curriculum_id}}}},
      order_by: {subject: {name: asc}}
    ) {
      level
      subject {
        id
        code
        name
        name_th
      }
    }
  }
}
"""

QUERY_SUBJECTS = """
query GetSubjects($curriculum_id: String!) {
  curriculum_subjects(
    where: {curriculum_id: {_eq: $curriculum_id}},
    order_by: {subject: {code: asc}}
  ) {
    subject {
      id
      code
      name
      name_th
      hard_skills(order_by: {skill: {name: asc}}) {
        level
        skill {
          id
          name
          name_th
        }
      }
      soft_skills(order_by: {skill: {name: asc}}) {
        level
        skill {
          id
          name
          name_th
        }
      }
    }
  }
}
"""

QUERY_JOB_FIELDS = """
query GetJobFields($curriculum_id: String!) {
  job_fields(
    where: {job_groups: {jobs: {curriculum_id: {_eq: $curriculum_id}}}},
    order_by: {name: asc}
  ) {
    id
    name
    name_th
    hard_skills(
      where: {curriculum_id: {_eq: $curriculum_id}},
      order_by: {name: asc}
    ) {
      id
      name
      name_th
    }
    job_groups(
      where: {jobs: {curriculum_id: {_eq: $curriculum_id}}},
      order_by: {name: asc}
    ) {
      id
      name
      name_th
      jobs(
        where: {curriculum_id: {_eq: $curriculum_id}},
        order_by: {name: asc}
      ) {
        id
        name
        name_th
      }
    }
  }
}
"""

QUERY_CURRICULUM = """
query GetCurriculum($curriculum_id: String!) {
  curriculums_by_pk(id: $curriculum_id) {
    id
    name
    name_th
    year
    faculty {
      id
      name
      name_th
    }
    jobs_aggregate {
      aggregate {
        count
      }
    }
    hard_skills_aggregate {
      aggregate {
        count
      }
    }
  }
}
"""


# ==================== CRAWL FUNCTIONS ====================

def crawl_jobs():
    """Fetch Jobs data"""
    print("\nCrawling Jobs...")
    result = graphql_query(QUERY_JOBS, {"curriculum_id": CURRICULUM_ID})

    if "errors" in result:
        print(f"Error: {result['errors']}")
        return None

    jobs = result.get("data", {}).get("jobs", [])
    print(f"   Found {len(jobs)} jobs")

    transformed = []
    for job in jobs:
        job_group = job.get("job_group") or {}
        job_field = job_group.get("job_field") or {}

        transformed.append({
            "id": job["id"],
            "name_en": job["name"],
            "name_th": job["name_th"],
            "duties_en": [d.strip() for d in (job.get("description") or "").split("\n") if d.strip()],
            "duties_th": [d.strip() for d in (job.get("description_th") or "").split("\n") if d.strip()],
            "job_group": {
                "id": job_group.get("id"),
                "name_en": job_group.get("name"),
                "name_th": job_group.get("name_th"),
            } if job_group else None,
            "job_field": {
                "id": job_field.get("id"),
                "name_en": job_field.get("name"),
                "name_th": job_field.get("name_th"),
            } if job_field else None,
            "required_hard_skills": [
                {
                    "skill_id": hs["skill"]["id"],
                    "skill_name_en": hs["skill"]["name"],
                    "skill_name_th": hs["skill"]["name_th"],
                    "required_level": hs["level"]
                }
                for hs in job.get("hard_skills", [])
            ],
            "required_soft_skills": [
                {
                    "skill_id": ss["skill"]["id"],
                    "skill_name_en": ss["skill"]["name"],
                    "skill_name_th": ss["skill"]["name_th"],
                    "required_level": ss["level"]
                }
                for ss in job.get("soft_skills", [])
            ]
        })

    return {
        "metadata": {
            "source": GRAPHQL_URL,
            "curriculum_id": CURRICULUM_ID,
            "total_jobs": len(transformed),
            "crawled_at": datetime.now().isoformat()
        },
        "jobs": transformed
    }


def crawl_hard_skills():
    """Fetch Hard Skills with full details (description, levels, jobs, subjects)"""
    print("\nCrawling Hard Skills (Full Details)...")
    result = graphql_query(QUERY_HARD_SKILLS_DETAIL, {"curriculum_id": CURRICULUM_ID})

    if "errors" in result:
        print(f"Error: {result['errors']}")
        return None

    skills = result.get("data", {}).get("hard_skills", [])
    print(f"   Found {len(skills)} hard skills")

    transformed = []
    for skill in skills:
        # Level descriptions (1-6)
        levels = {}
        for lvl in skill.get("levels", []):
            levels[str(lvl["level"])] = {
                "description_en": lvl.get("description") or "",
                "description_th": lvl.get("description_th") or ""
            }

        # Jobs that require this skill
        related_jobs = []
        for js in skill.get("jobs", []):
            if js.get("job"):
                related_jobs.append({
                    "job_id": js["job"]["id"],
                    "job_name_en": js["job"]["name"],
                    "job_name_th": js["job"]["name_th"],
                    "required_level": js["level"]
                })

        # Subjects that teach this skill
        related_subjects = []
        for ss in skill.get("subjects", []):
            if ss.get("subject"):
                related_subjects.append({
                    "subject_id": ss["subject"]["id"],
                    "subject_code": ss["subject"]["code"],
                    "subject_name_en": ss["subject"]["name"],
                    "subject_name_th": ss["subject"]["name_th"],
                    "level": ss["level"]
                })

        job_field = skill.get("job_field") or {}
        transformed.append({
            "id": skill["id"],
            "name_en": skill["name"],
            "name_th": skill["name_th"],
            "description_en": skill.get("description") or "",
            "description_th": skill.get("description_th") or "",
            "job_field": {
                "id": job_field.get("id"),
                "name_en": job_field.get("name"),
                "name_th": job_field.get("name_th"),
            } if job_field else None,
            "levels": levels,
            "related_jobs": related_jobs,
            "related_subjects": related_subjects,
            "stats": {
                "total_levels": len(levels),
                "total_jobs": len(related_jobs),
                "total_subjects": len(related_subjects)
            }
        })

    return {
        "metadata": {
            "source": GRAPHQL_URL,
            "curriculum_id": CURRICULUM_ID,
            "total_skills": len(transformed),
            "crawled_at": datetime.now().isoformat()
        },
        "hard_skills": transformed
    }


def crawl_soft_skills():
    """Fetch Soft Skills with full details (description, levels, jobs, subjects)"""
    print("\nCrawling Soft Skills (Full Details)...")
    result = graphql_query(QUERY_SOFT_SKILLS_DETAIL, {"curriculum_id": CURRICULUM_ID})

    if "errors" in result:
        print(f"Error: {result['errors']}")
        return None

    skills = result.get("data", {}).get("soft_skills", [])
    print(f"   Found {len(skills)} soft skills")

    transformed = []
    for skill in skills:
        # Level descriptions
        levels = {}
        for lvl in skill.get("levels", []):
            levels[str(lvl["level"])] = {
                "description_en": lvl.get("description") or "",
                "description_th": lvl.get("description_th") or ""
            }

        # Jobs that require this skill (already filtered to curriculum in query)
        related_jobs = []
        for js in skill.get("jobs", []):
            if js.get("job"):
                related_jobs.append({
                    "job_id": js["job"]["id"],
                    "job_name_en": js["job"]["name"],
                    "job_name_th": js["job"]["name_th"],
                    "required_level": js["level"]
                })

        # Subjects that teach this skill
        related_subjects = []
        for ss in skill.get("subjects", []):
            if ss.get("subject"):
                related_subjects.append({
                    "subject_id": ss["subject"]["id"],
                    "subject_code": ss["subject"]["code"],
                    "subject_name_en": ss["subject"]["name"],
                    "subject_name_th": ss["subject"]["name_th"],
                    "level": ss["level"]
                })

        transformed.append({
            "id": skill["id"],
            "name_en": skill["name"],
            "name_th": skill["name_th"],
            "description_en": skill.get("description") or "",
            "description_th": skill.get("description_th") or "",
            "levels": levels,
            "related_jobs": related_jobs,
            "related_subjects": related_subjects,
            "stats": {
                "total_levels": len(levels),
                "total_jobs": len(related_jobs),
                "total_subjects": len(related_subjects)
            }
        })

    return {
        "metadata": {
            "source": GRAPHQL_URL,
            "curriculum_id": CURRICULUM_ID,
            "total_skills": len(transformed),
            "crawled_at": datetime.now().isoformat()
        },
        "soft_skills": transformed
    }


def crawl_subjects():
    """Fetch Subjects with Skills Mapping (via curriculum_subjects)"""
    print("\nCrawling Subjects...")
    result = graphql_query(QUERY_SUBJECTS, {"curriculum_id": CURRICULUM_ID})

    if "errors" in result:
        print(f"Error: {result['errors']}")
        return None

    rows = result.get("data", {}).get("curriculum_subjects", [])
    print(f"   Found {len(rows)} subjects")

    transformed = []
    for row in rows:
        subject = row.get("subject") or {}
        transformed.append({
            "id": subject["id"],
            "code": subject["code"],
            "name_en": subject["name"],
            "name_th": subject["name_th"],
            "hard_skills": [
                {
                    "skill_id": hs["skill"]["id"],
                    "skill_name_en": hs["skill"]["name"],
                    "skill_name_th": hs["skill"]["name_th"],
                    "level": hs["level"]
                }
                for hs in subject.get("hard_skills", [])
            ],
            "soft_skills": [
                {
                    "skill_id": ss["skill"]["id"],
                    "skill_name_en": ss["skill"]["name"],
                    "skill_name_th": ss["skill"]["name_th"],
                    "level": ss["level"]
                }
                for ss in subject.get("soft_skills", [])
            ]
        })

    return {
        "metadata": {
            "source": GRAPHQL_URL,
            "curriculum_id": CURRICULUM_ID,
            "total_subjects": len(transformed),
            "crawled_at": datetime.now().isoformat()
        },
        "subjects": transformed
    }


def crawl_job_fields():
    """Fetch Job Fields with specific skills, job groups, and jobs"""
    print("\nCrawling Job Fields...")
    result = graphql_query(QUERY_JOB_FIELDS, {"curriculum_id": CURRICULUM_ID})

    if "errors" in result:
        print(f"Error: {result['errors']}")
        return None

    fields = result.get("data", {}).get("job_fields", [])
    print(f"   Found {len(fields)} job fields")

    transformed = []
    for field in fields:
        job_groups = []
        total_jobs = 0
        for jg in field.get("job_groups", []):
            jobs = [
                {"id": j["id"], "name_en": j["name"], "name_th": j["name_th"]}
                for j in jg.get("jobs", [])
            ]
            total_jobs += len(jobs)
            job_groups.append({
                "id": jg["id"],
                "name_en": jg["name"],
                "name_th": jg["name_th"],
                "jobs": jobs
            })

        specific_skills = [
            {"id": hs["id"], "name_en": hs["name"], "name_th": hs["name_th"]}
            for hs in field.get("hard_skills", [])
        ]

        transformed.append({
            "id": field["id"],
            "name_en": field["name"],
            "name_th": field["name_th"],
            "specific_skills": specific_skills,
            "job_groups": job_groups,
            "stats": {
                "total_jobs": total_jobs,
                "total_job_groups": len(job_groups),
                "total_specific_skills": len(specific_skills)
            }
        })

    return {
        "metadata": {
            "source": GRAPHQL_URL,
            "curriculum_id": CURRICULUM_ID,
            "total_fields": len(transformed),
            "crawled_at": datetime.now().isoformat()
        },
        "job_fields": transformed
    }


def crawl_curriculum_info():
    """Fetch Curriculum Info"""
    print("\nCrawling Curriculum Info...")
    result = graphql_query(QUERY_CURRICULUM, {"curriculum_id": CURRICULUM_ID})

    if "errors" in result:
        print(f"Error: {result['errors']}")
        return None

    curriculum = result.get("data", {}).get("curriculums_by_pk")
    if curriculum:
        return {
            "id": curriculum["id"],
            "name_en": curriculum["name"],
            "name_th": curriculum["name_th"],
            "year": curriculum["year"],
            "faculty": {
                "id": curriculum["faculty"]["id"],
                "name_en": curriculum["faculty"]["name"],
                "name_th": curriculum["faculty"]["name_th"]
            } if curriculum.get("faculty") else None,
            "stats": {
                "total_jobs": curriculum["jobs_aggregate"]["aggregate"]["count"],
                "total_hard_skills": curriculum["hard_skills_aggregate"]["aggregate"]["count"]
            }
        }
    return None


# ==================== MAIN ====================

def main():
    print("=" * 60)
    print("KMITL Skill Mapping Data Crawler (Complete Version)")
    print("=" * 60)
    print(f"GraphQL URL: {GRAPHQL_URL}")
    print(f"Curriculum ID: {CURRICULUM_ID}")
    print(f"Output Directory: {OUTPUT_DIR}")

    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Create __init__.py
    init_file = OUTPUT_DIR / "__init__.py"
    if not init_file.exists():
        init_file.write_text('"""KMITL Skill Mapping Data"""\n')

    # Crawl curriculum info
    curriculum = crawl_curriculum_info()
    if curriculum:
        print(f"\nCurriculum: {curriculum['name_en']} ({curriculum['name_th']})")
        if curriculum.get('faculty'):
            print(f"   Faculty: {curriculum['faculty']['name_en']}")
        print(f"   Stats: {curriculum['stats']}")

    # Crawl all data
    jobs_data = crawl_jobs()
    if jobs_data:
        save_json(jobs_data, "kmitl_jobs.json")

    hard_skills_data = crawl_hard_skills()
    if hard_skills_data:
        save_json(hard_skills_data, "kmitl_hard_skills.json")

    soft_skills_data = crawl_soft_skills()
    if soft_skills_data:
        save_json(soft_skills_data, "kmitl_soft_skills.json")

    subjects_data = crawl_subjects()
    if subjects_data:
        save_json(subjects_data, "kmitl_subjects.json")

    job_fields_data = crawl_job_fields()
    if job_fields_data:
        save_json(job_fields_data, "kmitl_job_fields.json")

    # Create metadata file
    metadata = {
        "source": "KMITL Skill Mapping",
        "graphql_url": GRAPHQL_URL,
        "curriculum_id": CURRICULUM_ID,
        "curriculum": curriculum,
        "crawled_at": datetime.now().isoformat(),
        "files": {
            "jobs": "kmitl_jobs.json",
            "hard_skills": "kmitl_hard_skills.json",
            "soft_skills": "kmitl_soft_skills.json",
            "subjects": "kmitl_subjects.json",
            "job_fields": "kmitl_job_fields.json"
        },
        "data_summary": {
            "total_jobs": jobs_data["metadata"]["total_jobs"] if jobs_data else 0,
            "total_hard_skills": hard_skills_data["metadata"]["total_skills"] if hard_skills_data else 0,
            "total_soft_skills": soft_skills_data["metadata"]["total_skills"] if soft_skills_data else 0,
            "total_subjects": subjects_data["metadata"]["total_subjects"] if subjects_data else 0,
            "total_job_fields": job_fields_data["metadata"]["total_fields"] if job_fields_data else 0
        }
    }
    save_json(metadata, "kmitl_metadata.json")

    print("\n" + "=" * 60)
    print("Crawling completed!")
    print("=" * 60)
    print(f"\nOutput files in: {OUTPUT_DIR}")
    for f in sorted(OUTPUT_DIR.glob("*.json")):
        size = f.stat().st_size
        print(f"   - {f.name} ({size:,} bytes)")

    print("\nData Summary:")
    print(f"   - Jobs:        {metadata['data_summary']['total_jobs']}")
    print(f"   - Hard Skills: {metadata['data_summary']['total_hard_skills']}")
    print(f"   - Soft Skills: {metadata['data_summary']['total_soft_skills']}")
    print(f"   - Subjects:    {metadata['data_summary']['total_subjects']}")
    print(f"   - Job Fields:  {metadata['data_summary']['total_job_fields']}")


if __name__ == "__main__":
    main()
