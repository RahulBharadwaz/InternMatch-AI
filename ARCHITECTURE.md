# InternMatch Architecture Documentation

## System Architecture Overview

InternMatch follows a classic three-tier web application architecture:

```
┌─────────────────────────────────────────────────────────────┐
│                     Presentation Layer                       │
│  (HTML Templates, CSS, JavaScript, Bootstrap 5)             │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      Application Layer                       │
│  (Flask Web Framework, Routes, Services, Business Logic)   │
│  - Authentication & Authorization                           │
│  - Profile Management                                       │
│  - Resume Processing                                        │
│  - Recommendation Engine                                    │
│  - Opportunity Management                                   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                       Data Layer                             │
│  (MySQL Database via SQLAlchemy ORM)                        │
│  - Users & Profiles                                         │
│  - Opportunities & Organizations                           │
│  - Recommendations & Applications                           │
│  - Skills & Learning Resources                             │
└─────────────────────────────────────────────────────────────┘
```

## Component Architecture

### 1. Flask Application Factory Pattern

The application uses the factory pattern for better testability and configuration management:

```
app/
├── __init__.py           # create_app() factory function
├── extensions.py         # Flask extensions (db, login_manager, csrf)
├── config.py            # Configuration classes
└── run.py               # Application entry point
```

**Benefits**:
- Easy configuration switching (development/production/testing)
- Better test isolation
- Lazy initialization of extensions

### 2. Database Models (ORM Layer)

SQLAlchemy ORM provides an abstraction over MySQL:

```
models/
├── user.py              # User authentication
├── profile.py           # Student profiles and education
├── skill.py             # Skills and student-skill relationships
├── resume.py            # Resume uploads and extractions
├── opportunity.py       # Opportunities and organizations
├── eligibility.py       # Eligibility rules
├── recommendation.py    # Recommendations and feedback
├── application.py       # Application tracking
├── notification.py      # User notifications
├── learning.py          # Learning resources
└── audit.py            # Security audit logs
```

**Key Relationships**:
- User → StudentProfile (1:1)
- StudentProfile → EducationRecord (1:N)
- User → StudentSkill (1:N)
- User → Resume (1:1)
- Organization → Opportunity (1:N)
- Opportunity → OpportunitySkill (1:N)
- User → Recommendation (1:N)
- Recommendation → RecommendationItem (1:N)

### 3. Route Handlers (Controller Layer)

Flask blueprints organize routes by functionality:

```
routes/
├── main.py              # Homepage, about, FAQ
├── auth.py              # Login, register, logout
├── profile.py           # Profile management
├── resume.py            # Resume upload
├── opportunities.py     # Opportunity explorer
├── recommendations.py  # Recommendation generation
├── applications.py      # Application tracking
├── admin.py            # Admin dashboard
└── errors.py           # Error handlers
```

**Pattern**:
- Each blueprint handles a specific domain
- Routes are protected with @login_required decorator
- Admin routes use @admin_required decorator
- CSRF protection on all POST requests

### 4. Service Layer (Business Logic)

Complex business logic is separated into service modules:

```
services/
├── eligibility_engine.py    # Eligibility rule evaluation
├── recommendation_engine.py # Hybrid recommendation algorithm
└── resume_parser.py         # Resume text extraction
```

**Benefits**:
- Reusable business logic
- Easier testing
- Clear separation from routes

### 5. Template Layer (View Layer)

Jinja2 templates with inheritance:

```
templates/
├── base.html            # Base template with header/footer
├── index.html           # Homepage
├── auth/                # Authentication templates
├── dashboard/           # Dashboard templates
├── profile/             # Profile management templates
├── opportunities/       # Opportunity templates
├── recommendations/    # Recommendation templates
├── applications/       # Application templates
├── admin/              # Admin templates
└── errors/             # Error page templates
```

**Pattern**:
- Template inheritance reduces duplication
- Macros for reusable components
- Custom filters for data formatting

## Data Flow Diagrams

### User Registration Flow

```
User → Registration Form
       ↓
POST /auth/register
       ↓
Validate Input
       ↓
Check Email Uniqueness
       ↓
Hash Password (Werkzeug)
       ↓
Create User Record
       ↓
Create Empty Profile
       ↓
Commit to Database
       ↓
Redirect to Login
```

### Recommendation Generation Flow

```
User → Generate Recommendations
       ↓
Load User Profile
       ↓
Load Published Opportunities
       ↓
For Each Opportunity:
  ├─ Calculate Skills Score (35%)
  ├─ Calculate Education Score (20%)
  ├─ Calculate Text Similarity (20%)
  ├─ Calculate Preference Score (15%)
  └─ Calculate Location Score (10%)
       ↓
Weighted Sum → Total Score
       ↓
Evaluate Eligibility Rules
       ↓
Generate Explanation
       ↓
Rank by Total Score
       ↓
Save Recommendation Record
       ↓
Display Top 10 Recommendations
```

### Resume Processing Flow

```
User → Upload Resume (PDF/DOCX)
       ↓
Validate File Type & Size
       ↓
Generate Secure Filename
       ↓
Save to Uploads Directory
       ↓
Create Resume Record
       ↓
Parse Resume:
  ├─ Extract Text (PyMuPDF/python-docx)
  ├─ Extract Skills (Keyword Matching)
  ├─ Extract Education (Pattern Matching)
  ├─ Extract Projects (NLP)
  └─ Extract Certifications (Pattern Matching)
       ↓
Save Extraction Record
       ↓
Mark Resume as Processed
       ↓
Allow User Review & Correction
```

## Recommendation Algorithm Architecture

### Hybrid Recommendation Engine

The recommendation engine combines multiple techniques:

```
┌─────────────────────────────────────────┐
│         User Profile Data               │
│  - Skills                               │
│  - Education                            │
│  - Preferences                          │
│  - Resume Text                          │
└─────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────┐
│    Opportunity Requirements Data        │
│  - Required Skills                      │
│  - Qualification Requirements            │
│  - Description Text                     │
│  - Location                             │
└─────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────┐
│         Scoring Components              │
│  ├─ Skills Match (35%)                 │
│  │   └─ Set overlap calculation       │
│  ├─ Education Compatibility (20%)       │
│  │   └─ Qualification matching         │
│  ├─ Text Similarity (20%)              │
│  │   └─ TF-IDF + Cosine Similarity    │
│  ├─ Preference Match (15%)             │
│  │   └─ Industry/Domain/Role match     │
│  └─ Location Preference (10%)          │
│      └─ Location + Relocation check    │
└─────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────┐
│      Weighted Score Calculation        │
│  Total = Σ(Component × Weight)         │
└─────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────┐
│         Eligibility Evaluation          │
│  - Qualification Rules                  │
│  - Age Rules                            │
│  - Employment Status Rules              │
└─────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────┐
│      Ranking & Explanation              │
│  - Sort by Total Score                  │
│  - Generate Human Explanation           │
│  - Identify Matching/Missing Skills     │
└─────────────────────────────────────────┘
```

### Eligibility Evaluation

```
┌─────────────────────────────────────────┐
│      Configurable Eligibility Rules     │
│  - Qualification Requirements           │
│  - Age Limits                           │
│  - Employment Status                    │
│  - Other Scheme-Specific Rules          │
└─────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────┐
│         Rule Evaluation Engine          │
│  For Each Mandatory Rule:               │
│  ├─ Parse Rule Condition (JSON)        │
│  ├─ Evaluate Against Profile Data     │
│  ├─ Return: Pass/Fail/Warning/Info     │
│  └─ Collect Failure Reasons            │
└─────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────┐
│         Eligibility Status              │
│  - Eligible (All mandatory pass)        │
│  - Ineligible (Mandatory failure)      │
│  - Insufficient Info (Data missing)     │
│  - Requires Verification                │
└─────────────────────────────────────────┘
```

## Security Architecture

### Authentication & Authorization

```
┌─────────────────────────────────────────┐
│         Authentication Flow             │
│  1. User submits credentials           │
│  2. Server validates email/password    │
│  3. Password compared with hash        │
│  4. Session created with user ID       │
│  5. Flask-Login manages session       │
│  6. Protected routes check session     │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│         Authorization Flow              │
│  1. User role checked (student/admin)  │
│  2. @login_required decorator          │
│  3. @admin_required decorator         │
│  4. Ownership checks on private data   │
│  5. Audit logging for sensitive actions│
└─────────────────────────────────────────┘
```

### Security Measures

1. **Password Security**
   - Werkzeug password hashing (PBKDF2)
   - Salted hashes
   - Minimum 8-character requirement

2. **CSRF Protection**
   - Flask-WTF CSRF tokens on all forms
   - Token validation on POST requests

3. **Session Security**
   - Secure session cookies
   - HTTP-only flag
   - SameSite attribute
   - Configurable expiration

4. **File Upload Security**
   - File type validation (MIME type)
   - Extension whitelist (PDF, DOCX)
   - File size limits (16MB)
   - Secure random filenames
   - Storage outside web root

5. **SQL Injection Prevention**
   - SQLAlchemy ORM parameterized queries
   - No raw SQL string concatenation

6. **Input Validation**
   - Server-side form validation
   - Email validation
   - Length checks
   - Type conversion

7. **Audit Logging**
   - Log sensitive actions
   - Record IP address and user agent
   - Track data modifications

## Deployment Architecture

### Development Environment

```
Windows Machine
├── XAMPP (Apache + MySQL)
│   ├── Apache (Port 80)
│   └── MySQL (Port 3306)
└── Python Virtual Environment
    ├── Flask (Port 5000)
    └── Application Code
```

### Production Environment (Recommended)

```
┌─────────────────────────────────────────┐
│              Nginx (Port 443)           │
│         SSL/TLS Termination             │
│         Static File Serving             │
└─────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────┐
│         Gunicorn/uWSGI                 │
│         WSGI Application Server         │
│         Multiple Workers               │
└─────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────┐
│              Flask App                 │
│         Application Logic               │
└─────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────┐
│         MySQL Database                 │
│         (Separate Server)              │
│         Connection Pooling             │
└─────────────────────────────────────────┘
```

## Technology Rationale

### Flask over Django
- Simpler learning curve for academic project
- More flexibility in architecture
- Lightweight and fast
- Sufficient for project requirements

### MySQL over PostgreSQL
- XAMPP includes MySQL by default
- Familiar to students
- Adequate for project scale
- Good tooling (phpMyAdmin)

### SQLAlchemy ORM
- Database-agnostic (easy to switch)
- Pythonic API
- Built-in migration support
- Strong community support

### scikit-learn over TensorFlow/PyTorch
- Simpler for tabular data
- Sufficient for recommendation task
- Easier to explain and debug
- Lower computational requirements

### Bootstrap 5 over React/Vue
- Faster development for academic timeline
- No build step required
- Good government-style templates available
- Sufficient for project requirements

## Performance Considerations

### Database Optimization
- Indexes on frequently queried columns
- Foreign key constraints for integrity
- Connection pooling via SQLAlchemy
- Pagination for large datasets

### Caching Strategy (Future)
- Cache recommendation results
- Cache static assets
- Cache frequently accessed data
- Invalidate on profile/opportunity changes

### Query Optimization
- Use eager loading (joinedload) for relationships
- Avoid N+1 query problems
- Select only required columns
- Use database aggregation where possible

## Scalability Considerations

### Current Limitations
- Single Flask instance (not horizontally scalable)
- Synchronous processing (no async)
- No message queue for background tasks
- No distributed caching

### Future Improvements
- Add Celery for background tasks
- Implement Redis caching
- Use Gunicorn with multiple workers
- Add load balancer for horizontal scaling
- Consider microservices architecture for larger scale

## Monitoring & Logging

### Current Implementation
- Flask debug mode in development
- Basic error handling
- Audit logging for sensitive actions

### Future Improvements
- Structured logging (JSON format)
- Error tracking (Sentry)
- Performance monitoring
- Uptime monitoring
- Database query logging

## Testing Strategy

### Test Coverage
- Unit tests for services
- Integration tests for routes
- End-to-end tests for critical flows
- Security tests for authentication

### Test Tools
- pytest for test framework
- pytest-cov for coverage
- Flask test client for integration tests
- Factory pattern for test fixtures

## Documentation

### Code Documentation
- Docstrings on all functions and classes
- Type hints where appropriate
- Inline comments for complex logic
- README for project overview

### Architecture Documentation
- This ARCHITECTURE.md file
- ER diagram (separate document)
- API documentation (future)
- Deployment guide (SETUP_GUIDE.md)

## Maintenance Considerations

### Database Migrations
- Current: Drop and recreate (simple)
- Future: Alembic for versioned migrations
- Backup strategy before migrations

### Dependency Management
- requirements.txt with pinned versions
- Regular security updates
- Virtual environment isolation

### Code Quality
- PEP 8 compliance
- Linting (flake8/pylint)
- Type checking (mypy)
- Code review process

## Conclusion

This architecture provides a solid foundation for the InternMatch academic project. It balances simplicity for development with best practices for maintainability and security. The modular design allows for future enhancements while keeping the codebase understandable for students and reviewers.

