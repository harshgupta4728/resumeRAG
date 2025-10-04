# ResumeRAG - AI-Powered Resume Matching System

ResumeRAG is a full-stack web application that allows recruiters to upload candidate resumes, search their contents using natural language queries, and automatically match them against job descriptions using AI-powered vector similarity search.

## 🚀 Features

- **Resume Upload**: Support for PDF, DOCX, and ZIP files
- **PII Redaction**: Automatic redaction of personally identifiable information
- **Natural Language Search**: Ask questions about resumes using natural language
- **AI-Powered Matching**: Vector similarity search to match candidates to jobs
- **Role-Based Access Control**: Different permissions for recruiters and candidates
- **Rate Limiting**: 60 requests per minute per user
- **Idempotency**: Prevents duplicate processing of requests
- **Real-time Processing**: Fast resume parsing and embedding generation

## 🛠️ Tech Stack

### Backend
- **FastAPI** - Modern, fast web framework for building APIs
- **PostgreSQL** - Primary database with pgvector extension for vector operations
- **SQLAlchemy** - ORM for database operations
- **Redis** - Caching and idempotency storage
- **sentence-transformers** - AI model for generating text embeddings
- **spaCy** - NLP library for PII detection and redaction
- **pypdf & python-docx** - Resume parsing libraries

### Frontend
- **React 18** - Modern React with hooks
- **Vite** - Fast build tool and development server
- **Tailwind CSS** - Utility-first CSS framework
- **Axios** - HTTP client for API calls
- **Zustand** - Lightweight state management
- **React Router** - Client-side routing
- **React Dropzone** - File upload with drag-and-drop

### Infrastructure
- **Docker & Docker Compose** - Containerization and orchestration
- **pgvector** - PostgreSQL extension for vector similarity search

## 📁 Project Structure

```
resume-rag-hackathon/
├── backend/
│   ├── app/
│   │   ├── api/              # API routers
│   │   │   ├── auth.py       # Authentication endpoints
│   │   │   ├── resumes.py    # Resume management endpoints
│   │   │   └── jobs.py       # Job management endpoints
│   │   ├── core/             # Core configuration
│   │   │   ├── config.py     # Application settings
│   │   │   └── security.py   # Authentication & security
│   │   ├── models/           # Database models
│   │   │   └── models.py     # SQLAlchemy ORM models
│   │   ├── schemas/          # Pydantic schemas
│   │   │   └── schemas.py    # Request/response validation
│   │   ├── services/         # Business logic
│   │   │   └── resume_service.py  # Resume processing & AI
│   │   ├── tests/            # Test suite
│   │   ├── database.py       # Database configuration
│   │   └── main.py           # FastAPI application
│   ├── Dockerfile
│   ├── requirements.txt
│   └── env.example
├── frontend/
│   ├── src/
│   │   ├── api/              # API client
│   │   ├── components/       # Reusable components
│   │   ├── pages/            # Page components
│   │   ├── store/            # State management
│   │   └── App.jsx           # Main application
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
└── README.md
```

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Node.js 18+ (for local development)

### Local Development

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd resume-rag-hackathon
   ```

2. **Start the application**
   ```bash
   docker-compose up --build
   ```

3. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

### Test Credentials

The application comes with pre-configured test users:

- **Recruiter**: `recruiter@example.com` / `strongpassword`
- **Candidate**: `candidate@example.com` / `strongpassword`

## 📚 API Documentation

### Authentication Endpoints

#### POST /api/register
Register a new user.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "password123",
  "role": "recruiter"
}
```

**Response:**
```json
{
  "id": 1,
  "email": "user@example.com",
  "role": "recruiter",
  "created_at": "2024-01-01T00:00:00Z"
}
```

#### POST /api/login
Authenticate user and get access token.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer"
}
```

### Resume Endpoints

#### POST /api/resumes
Upload resume files (supports PDF, DOCX, ZIP).

**Request:** Multipart form data with `files` field

**Response:**
```json
[
  {
    "id": 1,
    "filename": "resume.pdf",
    "content_text": "Full resume content...",
    "pii_redacted_content": "Resume with [REDACTED]...",
    "owner_id": 1,
    "created_at": "2024-01-01T00:00:00Z"
  }
]
```

#### GET /api/resumes
List resumes with optional search.

**Query Parameters:**
- `q` (optional): Search query
- `limit` (default: 10): Number of results
- `offset` (default: 0): Pagination offset

#### GET /api/resumes/{id}
Get a specific resume.

**Response:** Same as upload response

#### POST /api/ask
Ask questions about resumes using natural language.

**Request Body:**
```json
{
  "query": "Who has experience with Python?",
  "k": 3
}
```

**Response:**
```json
{
  "results": [
    {
      "resume_id": 1,
      "filename": "resume.pdf",
      "content": "Relevant content snippet...",
      "similarity_score": 0.85
    }
  ]
}
```

### Job Endpoints

#### POST /api/jobs
Create a new job description.

**Request Body:**
```json
{
  "title": "Python Developer",
  "description": "Looking for a Python developer with FastAPI experience..."
}
```

#### GET /api/jobs/{id}
Get a specific job.

#### POST /api/jobs/{id}/match
Match candidates to a job.

**Request Body:**
```json
{
  "top_n": 5
}
```

**Response:**
```json
{
  "job_id": 1,
  "matches": [
    {
      "resume_id": 1,
      "filename": "resume.pdf",
      "similarity_score": 0.92,
      "evidence": "Relevant experience snippet...",
      "missing_requirements": ["Docker experience", "React skills"]
    }
  ]
}
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the backend directory:

```env
DATABASE_URL=postgresql://postgres:password@localhost:5432/resumerag
SECRET_KEY=your-secret-key-here-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REDIS_URL=redis://localhost:6379
```

### Database Setup

The application uses PostgreSQL with the pgvector extension for vector operations. The database is automatically created and configured when using Docker Compose.

## 🧪 Testing

Run the test suite:

```bash
# Backend tests
cd backend
pytest

# Frontend tests (if implemented)
cd frontend
npm test
```

## 🚀 Deployment

### Using Docker

1. **Build and run with Docker Compose:**
   ```bash
   docker-compose up --build -d
   ```

2. **For production, update environment variables:**
   - Change `SECRET_KEY` to a secure random string
   - Update `DATABASE_URL` to your production database
   - Set `REDIS_URL` to your production Redis instance

### Manual Deployment

1. **Backend (FastAPI):**
   ```bash
   cd backend
   pip install -r requirements.txt
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

2. **Frontend (React):**
   ```bash
   cd frontend
   npm install
   npm run build
   # Serve the build directory with a web server
   ```

## 🔒 Security Features

- **JWT Authentication**: Secure token-based authentication
- **PII Redaction**: Automatic redaction of sensitive information
- **Rate Limiting**: 60 requests per minute per user
- **Input Validation**: Comprehensive request validation using Pydantic
- **CORS Configuration**: Configurable cross-origin resource sharing
- **Error Handling**: Uniform error response format

## 🤖 AI/ML Features

- **Vector Embeddings**: Uses sentence-transformers for semantic search
- **Similarity Matching**: Cosine similarity for candidate-job matching
- **PII Detection**: spaCy-based named entity recognition
- **Requirement Analysis**: Automatic analysis of missing job requirements

## 📊 Performance

- **Vector Search**: Optimized PostgreSQL queries with pgvector
- **Caching**: Redis-based caching for improved performance
- **Async Processing**: Non-blocking file processing
- **Pagination**: Efficient data pagination for large datasets

## 🐛 Troubleshooting

### Common Issues

1. **Database Connection Error**
   - Ensure PostgreSQL is running
   - Check database credentials in environment variables

2. **Redis Connection Error**
   - Ensure Redis is running
   - Check Redis URL configuration

3. **File Upload Issues**
   - Check file size limits
   - Ensure supported file formats (PDF, DOCX, ZIP)

4. **Authentication Issues**
   - Verify JWT token is included in requests
   - Check token expiration

### Logs

View application logs:

```bash
# All services
docker-compose logs

# Specific service
docker-compose logs backend
docker-compose logs frontend
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🏆 Hackathon Submission

This project was built for the Skillion Full-Stack Hackathon 2025, demonstrating:

- Modern full-stack development practices
- AI/ML integration for practical use cases
- Scalable architecture with microservices
- Comprehensive testing and documentation
- Production-ready deployment configuration

---

**Built with ❤️ for the Skillion Full-Stack Hackathon 2025**
