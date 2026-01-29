# GO2TECH - Tech Job Platform

แพลตฟอร์มหางานสายเทคโนโลยี พร้อมระบบวิเคราะห์ Transcript และแนะนำอาชีพที่เหมาะสม

## Features (Step 1)

- อัปโหลดและอ่าน Transcript (PDF)
- วิเคราะห์รายวิชาและเกรด
- คำนวณคะแนนความถนัดแต่ละด้าน (Domain Scores)
- แสดงจุดแข็ง Top 3
- แนะนำตำแหน่งงานที่เหมาะสม

## Tech Stack

- **Backend**: Python FastAPI
- **Frontend**: React (Vite) + TailwindCSS
- **PDF Processing**: pdfplumber

## Quick Start Guide

### Step-by-Step: Running the Application

#### 1️⃣ Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# For Windows (Command Prompt):
venv\Scripts\activate.bat
# For Windows (PowerShell):
venv\Scripts\activate
# For macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run backend server
uvicorn app.main:app --reload
```

**Backend is now running at:** `http://localhost:8000`
**API Docs:** `http://localhost:8000/docs`

---

#### 2️⃣ Frontend Setup

**Open a new terminal** (keep backend running), then:

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Run frontend development server
npm run dev
```

**Frontend is now running at:** `http://localhost:5173`

---

#### 3️⃣ Usage

1. Open browser and go to `http://localhost:5173`
2. Upload your academic transcript (PDF file)
3. View your analysis results:
   - Student Information
   - All Courses with Grades
   - Domain Scores
   - Top 3 Strengths
   - Job Recommendations

---

### Troubleshooting

**Windows PowerShell Execution Policy Error:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**Or use Command Prompt (cmd) instead of PowerShell**

---

## Project Structure

```
go2tech/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   └── transcript.py
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   └── config.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   └── transcript_analyzer.py
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   └── transcript.py
│   │   ├── models/
│   │   │   └── __init__.py
│   │   ├── __init__.py
│   │   └── main.py
│   ├── uploads/
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── FileUpload.jsx
│   │   │   └── AnalysisResult.jsx
│   │   ├── services/
│   │   │   └── api.js
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── index.css
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   └── postcss.config.js
│
└── README.md
```

## Backend Setup

### Prerequisites

- Python 3.8 or higher
- pip

### Installation

1. เข้าไปที่โฟลเดอร์ backend:
```bash
cd backend
```

2. สร้าง virtual environment:
```bash
python -m venv venv
```

3. เปิดใช้งาน virtual environment:

**Windows:**
```bash
venv\Scripts\activate
```

**macOS/Linux:**
```bash
source venv/bin/activate
```

4. ติดตั้ง dependencies:
```bash
pip install -r requirements.txt
```

5. สร้างไฟล์ `.env` (optional):
```bash
copy .env.example .env
```

### Running the Backend

รัน server:
```bash
uvicorn app.main:app --reload
```

Backend จะรันที่ `http://localhost:8000`

- API Documentation: `http://localhost:8000/docs`
- Alternative Documentation: `http://localhost:8000/redoc`

## Frontend Setup

### Prerequisites

- Node.js 16 or higher
- npm or yarn

### Installation

1. เข้าไปที่โฟลเดอร์ frontend:
```bash
cd frontend
```

2. ติดตั้ง dependencies:
```bash
npm install
```

### Running the Frontend

รัน development server:
```bash
npm run dev
```

Frontend จะรันที่ `http://localhost:5173`

### Build for Production

```bash
npm run build
```

ไฟล์ production จะถูกสร้างใน folder `dist/`

## API Endpoints

### Base URL
```
http://localhost:8000/api/v1
```

### Endpoints

#### 1. Upload Transcript
```http
POST /transcript/upload
```

**Request:**
- Content-Type: `multipart/form-data`
- Body: `file` (PDF file)

**Response:**
```json
{
  "success": true,
  "file_id": "uuid",
  "filename": "transcript.pdf",
  "message": "File uploaded successfully"
}
```

#### 2. Analyze Transcript (Upload + Analyze)
```http
POST /transcript/analyze
```

**Request:**
- Content-Type: `multipart/form-data`
- Body: `file` (PDF file)

**Response:**
```json
{
  "success": true,
  "student_info": {
    "name": "...",
    "student_id": "...",
    "major": "...",
    "degree": "...",
    "cumulative_gpa": 3.06,
    "total_credits": 115
  },
  "courses": [...],
  "domain_scores": {
    "Programming/Backend": 3.5,
    "Frontend/Web": 3.2,
    ...
  },
  "strengths": [
    "Programming/Backend",
    "Database",
    "AI/ML/Data Science"
  ],
  "job_recommendations": [
    "Backend Developer",
    "Software Engineer",
    "Python Developer",
    ...
  ],
  "summary": {
    "total_courses": 47,
    "total_credits": 115,
    "cumulative_gpa": 3.06
  }
}
```

#### 3. Analyze Uploaded File
```http
GET /transcript/analyze/{file_id}
```

**Response:** Same as above

## Domain Categories

ระบบจัดหมวดหมู่วิชาตามคำสำคัญ:

- **Programming/Backend**: PROGRAMMING, OBJECT ORIENTED, DATA STRUCTURE, SOFTWARE DEVELOPMENT, ALGORITHM
- **Frontend/Web**: WEB APPLICATION, WEB DEVELOPMENT, FRONTEND
- **UX/UI Design**: USER EXPERIENCE, USER INTERFACE, UX, UI DESIGN
- **Database**: DATABASE, SQL, DATA MANAGEMENT
- **Networks**: NETWORK, INTERNETWORKING, COMMUNICATION PROTOCOL
- **Cloud/DevOps**: CLOUD, DEVOPS, CONTAINER, KUBERNETES
- **Security**: SECURITY, HACKING, PENETRATION, CRYPTOGRAPHY, CYBER
- **Hardware/Embedded**: MICROCONTROLLER, CIRCUITS, ELECTRONICS, EMBEDDED, DIGITAL SYSTEM, COMPUTER ORGANIZATION, ARCHITECTURE
- **OS/Systems**: OPERATING SYSTEM, PLATFORM ADMINISTRATION, LINUX, UNIX
- **AI/ML/Data Science**: MACHINE LEARNING, ARTIFICIAL INTELLIGENCE, AI, ML, DATA SCIENCE, DEEP LEARNING
- **Math/Statistics**: CALCULUS, DISCRETE, DIFFERENTIAL, LINEAR ALGEBRA, PROBABILITY, STATISTICS, COMPUTATION
- **General/Soft Skills**: ENGLISH, MANAGEMENT, LEADERSHIP, COMMUNICATION, FOUNDATION, SOCIETY, BUSINESS

## Limitations

- รองรับเฉพาะ text-based PDF (ไม่รองรับ scanned PDF)
- Pattern การ parse วิชาเหมาะกับ Transcript ของมหาวิทยาลัยในไทยที่มีรูปแบบมาตรฐาน
- รหัสวิชาต้องเป็น 8 หลัก

## Future Development

- [ ] รองรับ Scanned PDF (OCR)
- [ ] ระบบจัดการโปรไฟล์และ Portfolio
- [ ] ระบบค้นหาและแมทช์งาน
- [ ] ระบบสมัครงานและติดตามสถานะ
- [ ] ระบบจับกลุ่มทำโปรเจกต์
- [ ] ระบบรีวิว Soft Skills
- [ ] ระบบสำหรับบริษัท/ผู้ประกาศงาน
- [ ] ระบบแจ้งเตือน

## License

MIT License

## Contact

สำหรับข้อสงสัยหรือข้อเสนอแนะ กรุณาติดต่อผ่าน GitHub Issues
