# InternMatch Database Schema Documentation

## Entity Relationship Diagram

```
┌──────────────┐       ┌──────────────────┐
│     users    │       │ student_profiles │
├──────────────┤       ├──────────────────┤
│ id (PK)      │◄──────│ id (PK)          │
│ email        │       │ user_id (FK)     │
│ password_hash│       │ phone_number     │
│ full_name    │       │ state            │
│ role         │       │ district         │
│ is_active    │       │ preferred_...    │
│ created_at   │       │ completion_%     │
│ updated_at   │       │ created_at       │
│ last_login   │       │ updated_at       │
└──────────────┘       └────────┬─────────┘
                                │
                                │ 1:N
                                ▼
                       ┌──────────────────┐
                       │ education_records│
                       ├──────────────────┤
                       │ id (PK)          │
                       │ profile_id (FK) │
                       │ qualification    │
                       │ course           │
                       │ specialization   │
                       │ institution      │
                       │ graduation_year  │
                       │ current_status   │
                       │ percentage_cgpa  │
                       └──────────────────┘

┌──────────────┐       ┌──────────────┐
│     users    │       │   skills     │
├──────────────┤       ├──────────────┤
│ id (PK)      │       │ id (PK)      │
│              │       │ name         │
│              │       │ category     │
│              │       │ synonyms     │
│              │       │ is_active    │
│              │       └──────────────┘
│              │              ▲
│              │              │
│              │              │ 1:N
│              │              │
│              │       ┌──────┴──────┐
│              │       │student_skills│
│              │       ├──────────────┤
│              │       │ id (PK)      │
│              │       │ user_id (FK) │
│              │       │ skill_id (FK)│
│              │       │ proficiency  │
│              │       │ source       │
│              │       └──────────────┘
└──────────────┘

┌──────────────┐       ┌──────────────┐
│     users    │       │   resumes    │
├──────────────┤       ├──────────────┤
│ id (PK)      │◄──────│ id (PK)      │
│              │       │ user_id (FK) │
│              │       │ filename     │
│              │       │ file_path    │
│              │       │ upload_date   │
│              │       │ is_processed │
│              │       └──────┬───────┘
│              │              │ 1:1
│              │              │
│              │              ▼
│              │       ┌──────────────────┐
│              │       │resume_extractions│
│              │       ├──────────────────┤
│              │       │ id (PK)          │
│              │       │ resume_id (FK)   │
│              │       │ raw_text         │
│              │       │ extracted_...    │
│              │       │ extraction_date  │
│              │       │ is_reviewed      │
│              │       └──────────────────┘
└──────────────┘

┌──────────────────┐       ┌──────────────┐
│  organizations   │       │opportunities │
├──────────────────┤       ├──────────────┤
│ id (PK)          │◄──────│ id (PK)      │
│ name             │       │ org_id (FK)  │
│ sector           │       │ title        │
│ description      │       │ description  │
│ website          │       │ qualification│
│ is_verified      │       │ skills_req   │
│ created_at       │       │ location     │
│ updated_at       │       │ domain       │
└──────────────────┘       │ role_type    │
                           │ stipend      │
                           │ duration     │
                           │ deadline     │
                           │ is_published │
                           │ is_sample    │
                           │ source_url   │
                           │ created_at   │
                           └──────┬───────┘
                                  │
                                  │ 1:N
                                  ▼
                           ┌──────────────────┐
                           │opportunity_skills│
                           ├──────────────────┤
                           │ id (PK)          │
                           │ opp_id (FK)      │
                           │ skill_id (FK)    │
                           │ is_required      │
                           └──────────────────┘

┌──────────────┐       ┌──────────────────┐
│     users    │       │recommendations  │
├──────────────┤       ├──────────────────┤
│ id (PK)      │◄──────│ id (PK)          │
│              │       │ user_id (FK)     │
│              │       │ algorithm_ver    │
│              │       │ generated_at     │
│              │       │ profile_snapshot │
│              │       └──────┬───────────┘
│              │              │ 1:N
│              │              │
│              │              ▼
│              │       ┌──────────────────────┐
│              │       │recommendation_items │
│              │       ├──────────────────────┤
│              │       │ id (PK)              │
│              │       │ rec_id (FK)          │
│              │       │ opp_id (FK)          │
│              │       │ match_score          │
│              │       │ skills_score         │
│              │       │ education_score      │
│              │       │ text_similarity      │
│              │       │ preference_score     │
│              │       │ location_score       │
│              │       │ eligibility_status   │
│              │       │ explanation          │
│              │       │ matching_skills      │
│              │       │ missing_skills       │
│              │       │ rank                 │
│              │       └──────────────────────┘
└──────────────┘

┌──────────────┐       ┌──────────────┐
│     users    │       │ applications │
├──────────────┤       ├──────────────┤
│ id (PK)      │◄──────│ id (PK)      │
│              │       │ user_id (FK) │
│              │       │ opp_id (FK)  │
│              │       │ status       │
│              │       │ app_date     │
│              │       │ notes        │
│              │       │ follow_up    │
│              │       │ created_at   │
│              │       │ updated_at   │
└──────────────┘       └──────────────┘

┌──────────────┐       ┌──────────────┐
│     users    │       │ notifications│
├──────────────┤       ├──────────────┤
│ id (PK)      │◄──────│ id (PK)      │
│              │       │ user_id (FK) │
│              │       │ title        │
│              │       │ message      │
│              │       │ type         │
│              │       │ link         │
│              │       │ is_read      │
│              │       │ created_at   │
└──────────────┘       └──────────────┘

┌──────────────┐       ┌──────────────┐
│     users    │       │saved_opp     │
├──────────────┤       ├──────────────┤
│ id (PK)      │◄──────│ id (PK)      │
│              │       │ user_id (FK) │
│              │       │ opp_id (FK)  │
│              │       │ notes        │
│              │       │ created_at   │
└──────────────┘       └──────────────┘

┌──────────────┐       ┌──────────────┐
│     skills   │       │learning_res  │
├──────────────┤       ├──────────────┤
│ id (PK)      │◄──────│ id (PK)      │
│              │       │ skill_id (FK)│
│              │       │ title        │
│              │       │ description  │
│              │       │ url          │
│              │       │ resource_type│
│              │       │ provider     │
│              │       │ is_verified  │
│              │       │ created_at   │
└──────────────┘       └──────────────┘

┌──────────────┐
│eligibility_  │
│    rules     │
├──────────────┤
│ id (PK)      │
│ name         │
│ description  │
│ rule_type    │
│ condition    │
│ is_mandatory │
│ is_active    │
│ source       │
│ verification │
│ created_at   │
│ updated_at   │
└──────────────┘

┌──────────────┐
│  audit_logs  │
├──────────────┤
│ id (PK)      │
│ user_id (FK) │
│ action       │
│ resource_type│
│ resource_id  │
│ ip_address   │
│ user_agent   │
│ details      │
│ status       │
│ created_at   │
└──────────────┘
```

## Table Descriptions

### 1. users
Stores user account information for authentication.

**Columns:**
- `id` (Integer, PK): Unique identifier
- `email` (String 120, Unique, Indexed): User email address
- `password_hash` (String 255): Hashed password (Werkzeug)
- `full_name` (String 100): User's full name
- `role` (String 20): User role ('student' or 'admin')
- `is_active` (Boolean): Account active status
- `created_at` (DateTime): Account creation timestamp
- `updated_at` (DateTime): Last update timestamp
- `last_login` (DateTime): Last successful login

**Indexes:**
- Primary key on `id`
- Unique index on `email`

**Relationships:**
- One-to-one with `student_profiles`
- One-to-many with `student_skills`
- One-to-many with `resumes`
- One-to-many with `recommendations`
- One-to-many with `applications`
- One-to-many with `saved_opportunities`
- One-to-many with `notifications`
- One-to-many with `audit_logs`

### 2. student_profiles
Stores detailed student profile information.

**Columns:**
- `id` (Integer, PK): Unique identifier
- `user_id` (Integer, FK): Reference to users table
- `phone_number` (String 20): Contact phone number
- `state` (String 100): State of residence
- `district` (String 100): District of residence
- `preferred_language` (String 20): Language preference (en/hi/mr)
- `preferred_industries` (Text, JSON): Array of preferred industries
- `preferred_domains` (Text, JSON): Array of preferred domains
- `preferred_roles` (Text, JSON): Array of preferred roles
- `skills` (Text, JSON): Array of student skills
- `preferred_location` (String 100): Preferred work location
- `relocation_preference` (String 20): Willingness to relocate (yes/no/maybe)
- `completion_percentage` (Integer): Profile completion percentage (0-100)
- `created_at` (DateTime): Profile creation timestamp
- `updated_at` (DateTime): Last update timestamp

**Relationships:**
- Many-to-one with `users`
- One-to-many with `education_records`

#### Updating an existing database

If the application reports a missing profile or resume-source column, update
the existing tables without deleting their data:

```bash
python scripts\migrate_profile_skills.py
```

The migration is safe to run more than once. It adds profile skills and resume
source columns only when they are missing.

### 3. education_records
Stores education history for students.

**Columns:**
- `id` (Integer, PK): Unique identifier
- `profile_id` (Integer, FK): Reference to student_profiles
- `highest_qualification` (String 100): Degree/certificate (e.g., B.Tech)
- `course` (String 100): Course name (e.g., Computer Science)
- `specialization` (String 100): Specialization (e.g., Data Science)
- `institution` (String 200): College/university name
- `graduation_year` (Integer): Year of graduation
- `current_status` (String 50): Status (pursuing/completed/gap_year)
- `percentage_cgpa` (String 10): Percentage or CGPA
- `created_at` (DateTime): Record creation timestamp
- `updated_at` (DateTime): Last update timestamp

**Relationships:**
- Many-to-one with `student_profiles`

### 4. skills
Master table of all skills in the system.

**Columns:**
- `id` (Integer, PK): Unique identifier
- `name` (String 100, Unique, Indexed): Skill name
- `category` (String 50): Skill category (technical/soft/domain)
- `synonyms` (Text, JSON): Array of synonym names
- `is_active` (Boolean): Active status
- `created_at` (DateTime): Skill creation timestamp
- `updated_at` (DateTime): Last update timestamp

**Indexes:**
- Primary key on `id`
- Unique index on `name`

**Relationships:**
- One-to-many with `student_skills`
- One-to-many with `opportunity_skills`
- One-to-many with `learning_resources`

### 5. student_skills
Junction table linking students to skills.

**Columns:**
- `id` (Integer, PK): Unique identifier
- `user_id` (Integer, FK): Reference to users
- `skill_id` (Integer, FK): Reference to skills
- `proficiency_level` (String 20): Proficiency (beginner/intermediate/advanced/expert)
- `source` (String 50): Source of skill (manual/resume_extracted)
- `created_at` (DateTime): Assignment timestamp

**Constraints:**
- Unique constraint on (user_id, skill_id)

**Relationships:**
- Many-to-one with `users`
- Many-to-one with `skills`

### 6. resumes
Stores uploaded resume information.

**Columns:**
- `id` (Integer, PK): Unique identifier
- `user_id` (Integer, FK, Unique): Reference to users
- `filename` (String 255): Secure generated filename
- `original_filename` (String 255): Original uploaded filename
- `file_path` (String 500): Full file system path
- `file_size` (Integer): File size in bytes
- `mime_type` (String 100): MIME type
- `upload_date` (DateTime): Upload timestamp
- `is_processed` (Boolean): Processing status

**Constraints:**
- Unique constraint on `user_id`

**Relationships:**
- Many-to-one with `users`
- One-to-one with `resume_extractions`

### 7. resume_extractions
Stores extracted data from resumes.

**Columns:**
- `id` (Integer, PK): Unique identifier
- `resume_id` (Integer, FK, Unique): Reference to resumes
- `raw_text` (Text): Full extracted text
- `extracted_skills` (Text, JSON): Array of extracted skills
- `extracted_education` (Text, JSON): Array of education records
- `extracted_projects` (Text, JSON): Array of projects
- `extracted_certifications` (Text, JSON): Array of certifications
- `extracted_experience` (Text, JSON): Array of work experience
- `extraction_date` (DateTime): Extraction timestamp
- `is_reviewed` (Boolean): User review status

**Constraints:**
- Unique constraint on `resume_id`

**Relationships:**
- Many-to-one with `resumes`

### 8. organizations
Stores organization information.

**Columns:**
- `id` (Integer, PK): Unique identifier
- `name` (String 200): Organization name
- `sector` (String 100): Industry sector
- `description` (Text): Organization description
- `website` (String 255): Organization website URL
- `is_verified` (Boolean): Verification status
- `created_at` (DateTime): Creation timestamp
- `updated_at` (DateTime): Last update timestamp

**Relationships:**
- One-to-many with `opportunities`

### 9. opportunities
Stores internship opportunity information.

**Columns:**
- `id` (Integer, PK): Unique identifier
- `organization_id` (Integer, FK): Reference to organizations
- `title` (String 200, Indexed): Opportunity title
- `description` (Text): Opportunity description
- `qualification_required` (String 100): Required qualification
- `minimum_percentage` (String 10): Minimum percentage/CGPA
- `skills_required` (Text, JSON): Array of required skills
- `experience_required` (String 50): Experience requirement
- `location` (String 100): Work location
- `domain` (String 100): Domain/field
- `role_type` (String 50): Type of role
- `stipend` (String 100): Stipend amount
- `duration` (String 50): Internship duration
- `application_deadline` (Date): Application deadline
- `start_date` (Date): Internship start date
- `is_published` (Boolean): Publication status
- `is_sample` (Boolean): Sample/demo data flag
- `source_url` (String 500): Source URL
- `verification_date` (DateTime): Last verification date
- `last_updated` (DateTime): Last update timestamp
- `created_at` (DateTime): Creation timestamp

**Indexes:**
- Primary key on `id`
- Index on `title`

**Relationships:**
- Many-to-one with `organizations`
- One-to-many with `opportunity_skills`
- One-to-many with `saved_opportunities`
- One-to-many with `applications`
- One-to-many with `recommendation_items`

### 10. opportunity_skills
Junction table linking opportunities to skills.

**Columns:**
- `id` (Integer, PK): Unique identifier
- `opportunity_id` (Integer, FK): Reference to opportunities
- `skill_id` (Integer, FK): Reference to skills
- `is_required` (Boolean): Whether skill is mandatory

**Constraints:**
- Unique constraint on (opportunity_id, skill_id)

**Relationships:**
- Many-to-one with `opportunities`
- Many-to-one with `skills`

### 11. eligibility_rules
Stores configurable eligibility rules.

**Columns:**
- `id` (Integer, PK): Unique identifier
- `name` (String 100): Rule name
- `description` (Text): Rule description
- `rule_type` (String 50): Rule type (qualification/age/employment)
- `condition` (Text, JSON): Rule condition logic
- `is_mandatory` (Boolean): Mandatory flag
- `is_active` (Boolean): Active status
- `source` (String 255): Source of rule
- `verification_date` (DateTime): Last verification date
- `created_at` (DateTime): Creation timestamp
- `updated_at` (DateTime): Last update timestamp

### 12. saved_opportunities
Stores opportunities saved by students.

**Columns:**
- `id` (Integer, PK): Unique identifier
- `user_id` (Integer, FK): Reference to users
- `opportunity_id` (Integer, FK): Reference to opportunities
- `notes` (Text): User notes
- `created_at` (DateTime): Save timestamp

**Constraints:**
- Unique constraint on (user_id, opportunity_id)

**Relationships:**
- Many-to-one with `users`
- Many-to-one with `opportunities`

### 13. recommendations
Stores recommendation run results.

**Columns:**
- `id` (Integer, PK): Unique identifier
- `user_id` (Integer, FK): Reference to users
- `algorithm_version` (String 20): Algorithm version
- `generated_at` (DateTime): Generation timestamp
- `profile_snapshot` (Text, JSON): Profile snapshot at generation time

**Relationships:**
- Many-to-one with `users`
- One-to-many with `recommendation_items`

### 14. recommendation_items
Stores individual recommended opportunities.

**Columns:**
- `id` (Integer, PK): Unique identifier
- `recommendation_id` (Integer, FK): Reference to recommendations
- `opportunity_id` (Integer, FK): Reference to opportunities
- `match_score` (Float): Total match score (0-1)
- `skills_score` (Float): Skills component score
- `education_score` (Float): Education component score
- `text_similarity_score` (Float): Text similarity score
- `preference_score` (Float): Preference match score
- `location_score` (Float): Location match score
- `eligibility_status` (String 50): Eligibility status
- `explanation` (Text): Human-readable explanation
- `matching_skills` (Text, JSON): Array of matching skills
- `missing_skills` (Text, JSON): Array of missing skills
- `rank` (Integer): Recommendation rank

**Relationships:**
- Many-to-one with `recommendations`
- Many-to-one with `opportunities`

### 15. recommendation_feedback
Stores user feedback on recommendations.

**Columns:**
- `id` (Integer, PK): Unique identifier
- `user_id` (Integer, FK): Reference to users
- `opportunity_id` (Integer, FK): Reference to opportunities
- `is_relevant` (Boolean): User relevance rating
- `feedback_comment` (Text): User comments
- `created_at` (DateTime): Feedback timestamp

**Relationships:**
- Many-to-one with `users`
- Many-to-one with `opportunities`

### 16. applications
Stores application tracking information.

**Columns:**
- `id` (Integer, PK): Unique identifier
- `user_id` (Integer, FK): Reference to users
- `opportunity_id` (Integer, FK): Reference to opportunities
- `status` (String 50): Application status
- `application_date` (Date): Date applied
- `notes` (Text): User notes
- `follow_up_reminder` (Date): Follow-up reminder date
- `created_at` (DateTime): Creation timestamp
- `updated_at` (DateTime): Last update timestamp

**Relationships:**
- Many-to-one with `users`
- Many-to-one with `opportunities`

### 17. notifications
Stores user notifications.

**Columns:**
- `id` (Integer, PK): Unique identifier
- `user_id` (Integer, FK): Reference to users
- `title` (String 200): Notification title
- `message` (Text): Notification message
- `notification_type` (String 50): Type (info/success/warning/alert)
- `link` (String 255): Related link
- `is_read` (Boolean): Read status
- `created_at` (DateTime): Creation timestamp

**Relationships:**
- Many-to-one with `users`

### 18. learning_resources
Stores learning resources for skill development.

**Columns:**
- `id` (Integer, PK): Unique identifier
- `skill_id` (Integer, FK): Reference to skills
- `title` (String 200): Resource title
- `description` (Text): Resource description
- `url` (String 500): Resource URL
- `resource_type` (String 50): Type (course/tutorial/documentation/video)
- `provider` (String 100): Provider name
- `is_verified` (Boolean): Verification status
- `created_at` (DateTime): Creation timestamp

**Relationships:**
- Many-to-one with `skills`

### 19. audit_logs
Stores security audit trail.

**Columns:**
- `id` (Integer, PK): Unique identifier
- `user_id` (Integer, FK): Reference to users (nullable)
- `action` (String 100): Action performed
- `resource_type` (String 50): Type of resource
- `resource_id` (Integer): ID of resource
- `ip_address` (String 45): User IP address
- `user_agent` (String 255): Browser user agent
- `details` (Text): Additional details
- `status` (String 20): Action status (success/failure)
- `created_at` (DateTime): Log timestamp

**Relationships:**
- Many-to-one with `users`

## Database Design Principles

### Normalization
- Database is in Third Normal Form (3NF)
- No redundant data
- Proper foreign key relationships
- Atomic values in columns

### Indexing Strategy
- Primary keys on all tables
- Unique indexes on natural keys (email, skill name)
- Indexes on frequently queried columns (opportunity titles)
- Composite indexes on junction tables

### Data Integrity
- Foreign key constraints enforce referential integrity
- Unique constraints prevent duplicates
- NOT NULL constraints on required fields
- Default values where appropriate

### Security Considerations
- Passwords never stored in plain text
- Sensitive data in audit logs excluded
- File paths stored, not file contents
- User data isolated by user_id

### Performance Considerations
- Appropriate data types (Integer vs String)
- TEXT type for large JSON data
- DateTime for temporal data
- Boolean for flags
- Pagination support via LIMIT/OFFSET

## Migration Strategy

### Current Approach
- Drop and recreate tables for development
- Seed script for demo data
- Simple and fast for academic project

### Production Recommendation
- Use Alembic for versioned migrations
- Migration files for each schema change
- Rollback capability
- Migration history tracking

## Backup Strategy

### Development
- Manual export via phpMyAdmin
- SQL dump files
- Version control for seed scripts

### Production Recommendation
- Automated daily backups
- Point-in-time recovery
- Off-site backup storage
- Backup retention policy

## Query Optimization

### Common Query Patterns
1. User profile with relationships: Use eager loading (joinedload)
2. Opportunity search: Use indexes on title, location
3. Recommendations: Pre-compute and cache
4. Dashboard statistics: Use COUNT queries

### N+1 Query Prevention
- Use SQLAlchemy eager loading
- joinedload() for 1:N relationships
- selectinload() for N:N relationships
- Avoid queries in loops

## Conclusion

This database schema provides a solid foundation for the InternMatch application. It balances normalization with performance, includes proper relationships and constraints, and supports all required features. The schema is designed to be maintainable and extensible for future enhancements.

