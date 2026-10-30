"""
Demo data seed script for InternMatch
Populates database with verified student profile for Deevi Rahul Bharadwaz (IIIT Lucknow),
industry tech opportunities, and comprehensive skill taxonomy for testing & demonstration.
"""
import sys
import os
from datetime import datetime, date, timedelta, timezone
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db
from app.models import *
from werkzeug.security import generate_password_hash

def seed_demo_data():
    """Seed database with InternMatch demo data"""
    app = create_app('development')
    
    with app.app_context():
        print("Seeding InternMatch demo data...")
        
        # Check if data already exists
        if User.query.filter_by(email='admin@internmatch.local').first():
            print("Demo data already exists (admin@internmatch.local). Skipping seed.")
            return
        
        # 1. Create Admin User
        admin = User(
            email='admin@internmatch.local',
            full_name='InternMatch Administrator',
            role='admin',
            is_active=True
        )
        admin.set_password('Admin@123')
        db.session.add(admin)
        
        # 2. Create Primary Student User: Deevi Rahul Bharadwaz (IIIT Lucknow)
        student1 = User(
            email='rahulbharadwazdeevi@gmail.com',
            full_name='Deevi Rahul Bharadwaz',
            role='student',
            is_active=True
        )
        student1.set_password('Student@123')
        db.session.add(student1)
        
        # 3. Create Secondary Student User for multi-candidate testing
        student2 = User(
            email='priya.sharma@example.com',
            full_name='Priya Sharma',
            role='student',
            is_active=True
        )
        student2.set_password('Student@123')
        db.session.add(student2)
        
        db.session.flush()
        
        # 4. Create Skills (Canonical tech, domain, and soft skills)
        skills_data = [
            # Technical Skills - Programming Languages
            ('Python', 'technical', ['Python 3', 'Py', 'Python3']),
            ('C++', 'technical', ['C Plus Plus', 'CPP', 'C/C++']),
            ('JavaScript', 'technical', ['JS', 'ES6', 'ECMAScript']),
            ('TypeScript', 'technical', ['TS', 'Typed JavaScript']),
            ('Java', 'technical', ['Java SE', 'J2EE', 'Java 17']),
            ('SQL', 'technical', ['MySQL', 'PostgreSQL', 'T-SQL', 'SQLite']),
            ('HTML/CSS', 'technical', ['HTML5', 'CSS3', 'SASS', 'Tailwind CSS']),
            
            # Frameworks & Libraries
            ('React', 'technical', ['React.js', 'ReactJS', 'React Native']),
            ('Node.js', 'technical', ['NodeJS', 'Express', 'Express.js', 'NestJS']),
            ('FastAPI', 'technical', ['Fast API', 'FastAPI Framework']),
            ('Flask', 'technical', ['Flask Framework', 'Python Micro']),
            ('Django', 'technical', ['Django Framework', 'Python Web']),
            ('PyTorch', 'technical', ['Torch', 'PyTorch Framework', 'Deep Learning PyTorch']),
            ('TensorFlow', 'technical', ['TF', 'Keras', 'Deep Learning']),
            ('Scikit-learn', 'technical', ['Sklearn', 'Scikit Learn']),
            ('Pandas', 'technical', ['Data Manipulation', 'Pandas DataFrame']),
            ('NumPy', 'technical', ['Numerical Python', 'NumPy Arrays']),
            ('LightGBM', 'technical', ['LGBM', 'Light Gradient Boosted Machine']),
            
            # Databases & Infrastructure
            ('PostgreSQL', 'technical', ['Postgres', 'PostgreSQL DB']),
            ('MongoDB', 'technical', ['NoSQL', 'Document DB', 'Mongo']),
            ('Redis', 'technical', ['Cache', 'In-Memory DB']),
            ('Docker', 'technical', ['Containers', 'Containerization']),
            ('Kubernetes', 'technical', ['K8s', 'Container Orchestration']),
            ('Git', 'technical', ['Version Control', 'GitHub', 'GitLab']),
            ('Linux', 'technical', ['Unix', 'Shell Scripting', 'Bash']),
            ('REST APIs', 'technical', ['API Design', 'RESTful Services', 'JSON APIs']),
            ('Microservices', 'technical', ['Microservice Architecture', 'SOA']),
            ('CI/CD', 'technical', ['Continuous Integration', 'DevOps', 'GitHub Actions']),
            
            # AI / ML / Data Concepts
            ('Machine Learning', 'domain', ['ML', 'Supervised Learning', 'Unsupervised Learning']),
            ('Deep Learning', 'domain', ['Neural Networks', 'DL', 'Transformers']),
            ('Computer Vision', 'domain', ['CV', 'Image Processing', 'OpenCV']),
            ('Natural Language Processing', 'domain', ['NLP', 'Text Mining', 'Sentence-BERT']),
            ('Data Analysis', 'domain', ['Analytics', 'Data Science', 'Data Mining']),
            ('Cloud Computing', 'domain', ['AWS', 'Azure', 'GCP', 'Google Cloud']),
            
            # Soft Skills
            ('Problem Solving', 'soft', ['Critical Thinking', 'Analytical Skills', 'Algorithms']),
            ('Communication', 'soft', ['Verbal Communication', 'Written Communication']),
            ('Teamwork', 'soft', ['Collaboration', 'Peer Programming', 'Agile']),
            ('Leadership', 'soft', ['Initiative', 'Project Ownership']),
            ('Time Management', 'soft', ['Sprint Planning', 'Productivity']),
        ]
        
        skills = {}
        for name, category, synonyms in skills_data:
            skill = Skill(
                name=name,
                category=category,
                synonyms=json.dumps(synonyms),
                is_active=True
            )
            db.session.add(skill)
            db.session.flush()
            skills[name] = skill
        
        # 5. Create Organizations
        org1 = Organization(
            name='NeuralCraft AI Labs',
            sector='Artificial Intelligence',
            description='Applied AI research lab focusing on computer vision, NLP, and intelligent recommendation systems.',
            website='https://neuralcraft.example.com',
            is_verified=True
        )
        db.session.add(org1)
        
        org2 = Organization(
            name='HyperScale Cloud Systems',
            sector='Cloud Infrastructure',
            description='Enterprise cloud infrastructure provider building distributed backend systems and developer platforms.',
            website='https://hyperscale.example.com',
            is_verified=True
        )
        db.session.add(org2)
        
        org3 = Organization(
            name='Apex Software Solutions',
            sector='Information Technology',
            description='Full-stack web engineering and enterprise application solutions provider.',
            website='https://apexsolutions.example.com',
            is_verified=True
        )
        db.session.add(org3)
        
        org4 = Organization(
            name='PulseHealth Informatics',
            sector='Healthcare AI',
            description='Digital healthcare intelligence platform deploying predictive analytics and biomedical signal processing.',
            website='https://pulsehealth.example.com',
            is_verified=True
        )
        db.session.add(org4)
        
        org5 = Organization(
            name='FinEdge Technologies',
            sector='FinTech',
            description='Next-generation algorithmic trading, risk analytics, and scalable financial service infrastructure.',
            website='https://finedge.example.com',
            is_verified=True
        )
        db.session.add(org5)
        
        db.session.flush()
        
        now_utc = datetime.now(timezone.utc)
        
        # 6. Create Realistic Tech Internship Opportunities
        opportunities_data = [
            {
                'org': org1,
                'title': 'AI/ML Research Intern',
                'description': 'Design and develop machine learning and deep learning pipelines. Implement neural models using PyTorch, perform feature engineering with Scikit-learn, and optimize inference pipelines for real-time recommendation and ranking.',
                'qualification': 'B.Tech/M.Tech in Computer Science, AI, or related field',
                'minimum_percentage': '70% / 7.0 CGPA',
                'skills': ['Python', 'Machine Learning', 'Deep Learning', 'PyTorch', 'Scikit-learn', 'Pandas'],
                'location': 'Bangalore / Hybrid',
                'domain': 'AI/ML',
                'role_type': 'Machine Learning Engineer',
                'stipend': '₹35,000/month',
                'duration': '6 months',
                'deadline': date.today() + timedelta(days=45),
                'source_url': 'https://internmatch.example.com/opps/neuralcraft-aiml'
            },
            {
                'org': org2,
                'title': 'Backend Software Development Engineer Intern',
                'description': 'Build high-performance REST APIs and microservices using Python, FastAPI, and PostgreSQL. Implement containerized deployments with Docker and design scalable database schemas and caching layers.',
                'qualification': 'B.Tech in Computer Science, Information Technology, or Software Engineering',
                'minimum_percentage': '65% / 6.5 CGPA',
                'skills': ['Python', 'FastAPI', 'SQL', 'PostgreSQL', 'Docker', 'REST APIs', 'Git'],
                'location': 'Hyderabad / Remote',
                'domain': 'Backend Development',
                'role_type': 'Backend Developer',
                'stipend': '₹30,000/month',
                'duration': '6 months',
                'deadline': date.today() + timedelta(days=40),
                'source_url': 'https://internmatch.example.com/opps/hyperscale-backend'
            },
            {
                'org': org3,
                'title': 'Full Stack Web Developer Intern',
                'description': 'Develop responsive web applications using React, Node.js, and TypeScript. Collaborate on modern UI/UX workflows, build RESTful endpoints, and manage document-based databases with MongoDB.',
                'qualification': 'B.Tech/B.E. in Computer Science or related engineering discipline',
                'minimum_percentage': '65% / 6.5 CGPA',
                'skills': ['JavaScript', 'TypeScript', 'React', 'Node.js', 'MongoDB', 'HTML/CSS'],
                'location': 'Pune / Hybrid',
                'domain': 'Web Development',
                'role_type': 'Full Stack Developer',
                'stipend': '₹28,000/month',
                'duration': '6 months',
                'deadline': date.today() + timedelta(days=35),
                'source_url': 'https://internmatch.example.com/opps/apex-fullstack'
            },
            {
                'org': org1,
                'title': 'Computer Vision & Deep Learning Intern',
                'description': 'Implement deep neural network architectures for image classification, feature extraction, and pattern recognition using PyTorch and OpenCV. Optimize algorithms for computational efficiency.',
                'qualification': 'B.Tech/M.Tech in CS/AI with strong mathematics and linear algebra background',
                'minimum_percentage': '75% / 7.5 CGPA',
                'skills': ['Python', 'C++', 'PyTorch', 'Computer Vision', 'Deep Learning', 'NumPy'],
                'location': 'Bangalore',
                'domain': 'Computer Vision',
                'role_type': 'Computer Vision Engineer',
                'stipend': '₹35,000/month',
                'duration': '6 months',
                'deadline': date.today() + timedelta(days=50),
                'source_url': 'https://internmatch.example.com/opps/neuralcraft-cv'
            },
            {
                'org': org2,
                'title': 'Cloud Platform & DevOps Intern',
                'description': 'Manage containerized microservices across cloud clusters. Build CI/CD pipelines using GitHub Actions, configure Kubernetes manifests, and automate Linux server administration.',
                'qualification': 'B.Tech in Computer Science, IT, or Electronics',
                'minimum_percentage': '65% / 6.5 CGPA',
                'skills': ['Cloud Computing', 'Docker', 'Kubernetes', 'Linux', 'CI/CD', 'Git'],
                'location': 'Bangalore / Remote',
                'domain': 'Cloud & DevOps',
                'role_type': 'DevOps Engineer',
                'stipend': '₹30,000/month',
                'duration': '6 months',
                'deadline': date.today() + timedelta(days=60),
                'source_url': 'https://internmatch.example.com/opps/hyperscale-devops'
            },
            {
                'org': org4,
                'title': 'Data Science & Healthcare Analytics Intern',
                'description': 'Analyze clinical datasets, perform statistical modeling, and extract exploratory insights using Python, Pandas, and Scikit-learn. Develop reproducible data pipelines and dashboards.',
                'qualification': 'B.Tech in CS/Data Science or B.Sc/M.Sc in Statistics',
                'minimum_percentage': '65% / 6.5 CGPA',
                'skills': ['Python', 'Pandas', 'NumPy', 'SQL', 'Data Analysis', 'Machine Learning'],
                'location': 'Delhi NCR',
                'domain': 'Data Science',
                'role_type': 'Data Scientist',
                'stipend': '₹25,000/month',
                'duration': '6 months',
                'deadline': date.today() + timedelta(days=30),
                'source_url': 'https://internmatch.example.com/opps/pulsehealth-analytics'
            },
            {
                'org': org5,
                'title': 'High-Performance Systems & FinTech Intern',
                'description': 'Develop low-latency backend services and data structures for financial transaction processing. Profile algorithmic performance and memory footprint in C++ and Python.',
                'qualification': 'B.Tech in Computer Science or Software Engineering with strong DSA foundation',
                'minimum_percentage': '75% / 7.5 CGPA',
                'skills': ['C++', 'Python', 'SQL', 'Problem Solving', 'REST APIs'],
                'location': 'Mumbai',
                'domain': 'FinTech',
                'role_type': 'Systems Engineer',
                'stipend': '₹35,000/month',
                'duration': '6 months',
                'deadline': date.today() + timedelta(days=45),
                'source_url': 'https://internmatch.example.com/opps/finedge-systems'
            },
            {
                'org': org3,
                'title': 'Frontend UI/UX Engineering Intern',
                'description': 'Architect modern single-page applications using React, TypeScript, and Tailwind CSS. Implement accessible UI components, state management, and API integration.',
                'qualification': 'B.Tech/BCA/B.Sc in Computer Science or equivalent',
                'minimum_percentage': '60% / 6.0 CGPA',
                'skills': ['React', 'JavaScript', 'TypeScript', 'HTML/CSS', 'Problem Solving'],
                'location': 'Remote',
                'domain': 'Web Development',
                'role_type': 'Frontend Developer',
                'stipend': '₹22,000/month',
                'duration': '4 months',
                'deadline': date.today() + timedelta(days=25),
                'source_url': 'https://internmatch.example.com/opps/apex-frontend'
            }
        ]
        
        for opp_data in opportunities_data:
            opp = Opportunity(
                organization_id=opp_data['org'].id,
                title=opp_data['title'],
                description=opp_data['description'],
                qualification_required=opp_data['qualification'],
                minimum_percentage=opp_data['minimum_percentage'],
                skills_required=json.dumps(opp_data['skills']),
                location=opp_data['location'],
                domain=opp_data['domain'],
                role_type=opp_data['role_type'],
                stipend=opp_data['stipend'],
                duration=opp_data['duration'],
                application_deadline=opp_data['deadline'],
                is_published=True,
                is_sample=True,
                source_url=opp_data['source_url'],
                verification_date=now_utc
            )
            db.session.add(opp)
            db.session.flush()
            
            for skill_name in opp_data['skills']:
                if skill_name in skills:
                    opp_skill = OpportunitySkill(
                        opportunity_id=opp.id,
                        skill_id=skills[skill_name].id,
                        is_required=True
                    )
                    db.session.add(opp_skill)
        
        # 7. Student Profiles
        # Primary Profile: Deevi Rahul Bharadwaz
        profile1 = StudentProfile(
            user_id=student1.id,
            phone_number='+91 9876543210',
            state='Uttar Pradesh',
            district='Lucknow',
            preferred_language='en',
            preferred_industries=json.dumps(['Artificial Intelligence', 'Information Technology', 'Software Engineering']),
            preferred_domains=json.dumps(['AI/ML', 'Backend Development', 'Computer Vision']),
            preferred_roles=json.dumps(['Machine Learning Engineer', 'Backend Developer', 'Computer Vision Engineer']),
            preferred_location='Lucknow / Remote / Bangalore',
            relocation_preference='yes',
            completion_percentage=95
        )
        db.session.add(profile1)
        
        # Secondary Profile: Priya Sharma
        profile2 = StudentProfile(
            user_id=student2.id,
            phone_number='+91 9876543211',
            state='Karnataka',
            district='Bangalore',
            preferred_language='en',
            preferred_industries=json.dumps(['Information Technology']),
            preferred_domains=json.dumps(['Web Development']),
            preferred_roles=json.dumps(['Frontend Developer', 'Full Stack Developer']),
            preferred_location='Bangalore',
            relocation_preference='no',
            completion_percentage=75
        )
        db.session.add(profile2)
        
        db.session.flush()
        
        # 8. Education Records
        # Deevi Rahul Bharadwaz - IIIT Lucknow B.Tech CSAI
        edu1 = EducationRecord(
            profile_id=profile1.id,
            highest_qualification='B.Tech',
            course='Computer Science and Artificial Intelligence',
            specialization='Artificial Intelligence & Machine Learning',
            institution='Indian Institute of Information Technology, Lucknow (IIIT Lucknow)',
            graduation_year=2027,
            current_status='pursuing',
            percentage_cgpa='8.14 CGPA'
        )
        db.session.add(edu1)
        
        # Priya Sharma - RV College of Engineering
        edu2 = EducationRecord(
            profile_id=profile2.id,
            highest_qualification='B.Tech',
            course='Information Science and Engineering',
            specialization='Web & Mobile Systems',
            institution='RV College of Engineering, Bangalore',
            graduation_year=2026,
            current_status='pursuing',
            percentage_cgpa='8.2 CGPA'
        )
        db.session.add(edu2)
        
        # 9. Student Skills Mapping
        # Rahul's actual technical background & projects (UniLoop, CampusLink, DevDuel, Amazon ML Challenge 2026)
        student1_skills = [
            ('Python', 'advanced'),
            ('PyTorch', 'intermediate'),
            ('C++', 'advanced'),
            ('SQL', 'advanced'),
            ('Machine Learning', 'advanced'),
            ('FastAPI', 'advanced'),
            ('React', 'intermediate'),
            ('Node.js', 'intermediate'),
            ('JavaScript', 'intermediate'),
            ('TypeScript', 'intermediate'),
            ('PostgreSQL', 'intermediate'),
            ('MongoDB', 'intermediate'),
            ('Docker', 'intermediate'),
            ('Git', 'advanced'),
            ('Pandas', 'advanced'),
            ('NumPy', 'advanced'),
            ('Scikit-learn', 'advanced'),
            ('Problem Solving', 'advanced'),
            ('Teamwork', 'advanced'),
            ('Communication', 'advanced')
        ]
        
        for skill_name, proficiency in student1_skills:
            if skill_name in skills:
                ss = StudentSkill(
                    user_id=student1.id,
                    skill_id=skills[skill_name].id,
                    proficiency_level=proficiency,
                    source='manual'
                )
                db.session.add(ss)
        
        student2_skills = [
            ('JavaScript', 'advanced'),
            ('HTML/CSS', 'advanced'),
            ('React', 'advanced'),
            ('Node.js', 'intermediate'),
            ('TypeScript', 'intermediate'),
            ('SQL', 'intermediate'),
            ('Communication', 'advanced'),
            ('Problem Solving', 'intermediate'),
        ]
        
        for skill_name, proficiency in student2_skills:
            if skill_name in skills:
                ss = StudentSkill(
                    user_id=student2.id,
                    skill_id=skills[skill_name].id,
                    proficiency_level=proficiency,
                    source='manual'
                )
                db.session.add(ss)
        
        # 10. Eligibility Rules (Academic Standards)
        eligibility_rules = [
            {
                'name': 'Undergraduate / Engineering Enrollment',
                'description': 'Candidate must be actively enrolled in or completed a Bachelor\'s degree (B.Tech, B.E., B.Sc, or equivalent)',
                'rule_type': 'qualification',
                'condition': json.dumps({'min_level': 'bachelor'}),
                'is_mandatory': True,
                'source': 'InternMatch Academic Standards'
            },
            {
                'name': 'Age Eligibility Window',
                'description': 'Candidate age must fall within the student internship eligibility window (18-28 years)',
                'rule_type': 'age',
                'condition': json.dumps({'min_age': 18, 'max_age': 28}),
                'is_mandatory': True,
                'source': 'InternMatch Verification Standards'
            },
            {
                'name': 'Internship Availability Status',
                'description': 'Candidate is available for full-time or semester internship commitments',
                'rule_type': 'employment_status',
                'condition': json.dumps({'employed': False, 'full_time_education': False}),
                'is_mandatory': False,
                'source': 'InternMatch Guidelines'
            },
        ]
        
        for rule_data in eligibility_rules:
            rule = EligibilityRule(
                name=rule_data['name'],
                description=rule_data['description'],
                rule_type=rule_data['rule_type'],
                condition=rule_data['condition'],
                is_mandatory=rule_data['is_mandatory'],
                is_active=True,
                source=rule_data['source'],
                verification_date=now_utc
            )
            db.session.add(rule)
        
        # 11. Learning Resources for Skill Gap Analysis
        learning_resources = [
            {
                'skill': 'PyTorch',
                'title': 'Deep Learning with PyTorch: A 60 Minute Blitz',
                'description': 'Official PyTorch tutorial on neural networks and tensor computation',
                'url': 'https://pytorch.org/tutorials/beginner/deep_learning_60min_blitz.html',
                'resource_type': 'tutorial',
                'provider': 'PyTorch Official'
            },
            {
                'skill': 'FastAPI',
                'title': 'FastAPI Modern Python Web Framework',
                'description': 'High-performance API design with type annotations and OpenAPI generation',
                'url': 'https://fastapi.tiangolo.com/tutorial/',
                'resource_type': 'documentation',
                'provider': 'FastAPI'
            },
            {
                'skill': 'Docker',
                'title': 'Docker for Developers: From Beginner to Container Mastery',
                'description': 'Comprehensive containerization, Dockerfile optimization, and Compose orchestration',
                'url': 'https://docs.docker.com/get-started/',
                'resource_type': 'guide',
                'provider': 'Docker Docs'
            },
            {
                'skill': 'Machine Learning',
                'title': 'Machine Learning Specialization',
                'description': 'Foundational supervised learning, neural networks, and ML pipelines by Andrew Ng',
                'url': 'https://www.coursera.org/specializations/machine-learning-introduction',
                'resource_type': 'course',
                'provider': 'Coursera & DeepLearning.AI'
            },
            {
                'skill': 'React',
                'title': 'Full-Stack React & TypeScript Handbook',
                'description': 'Modern component architecture, hooks, and TypeScript patterns for scalable web apps',
                'url': 'https://react.dev/learn',
                'resource_type': 'documentation',
                'provider': 'React Core Team'
            },
        ]
        
        for lr_data in learning_resources:
            if lr_data['skill'] in skills:
                lr = LearningResource(
                    skill_id=skills[lr_data['skill']].id,
                    title=lr_data['title'],
                    description=lr_data['description'],
                    url=lr_data['url'],
                    resource_type=lr_data['resource_type'],
                    provider=lr_data['provider'],
                    is_verified=True
                )
                db.session.add(lr)
        
        # Commit all changes
        db.session.commit()
        
        print("\nInternMatch demo data seeded successfully!")
        print("\nDemonstration Accounts:")
        print(f"1. Admin: admin@internmatch.local / Admin@123")
        print(f"2. Primary Student (Deevi Rahul Bharadwaz - IIIT Lucknow): rahulbharadwazdeevi@gmail.com / Student@123")
        print(f"3. Secondary Student (Priya Sharma): priya.sharma@example.com / Student@123")
        print(f"\nSeeded:")
        print(f"- {len(skills_data)} Canonical Skills")
        print(f"- 5 Organizations (NeuralCraft AI, HyperScale Cloud, Apex Solutions, etc.)")
        print(f"- {len(opportunities_data)} CS/Engineering Internship Opportunities")
        print(f"- 2 Verified Student Profiles & Education Records")
        print(f"- {len(student1_skills) + len(student2_skills)} Student Skill Mappings")
        print(f"- {len(eligibility_rules)} Eligibility Rules")
        print(f"- {len(learning_resources)} Verified Learning Resources")

if __name__ == '__main__':
    seed_demo_data()
