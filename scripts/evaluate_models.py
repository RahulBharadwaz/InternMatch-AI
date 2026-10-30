"""
Offline Model Evaluation & Benchmarking Pipeline
Compares:
1. TF-IDF Text Similarity Baseline
2. Sentence-BERT Semantic Matching (all-MiniLM-L6-v2)
3. InternMatch Explainable Hybrid Recommendation Engine

Calculates Information Retrieval & Ranking Metrics:
- Precision@K (K=3, 5)
- Recall@K (K=3, 5)
- NDCG@K (K=3, 5)
- MRR@K (K=3, 5)
- Inference Latency Benchmark (ms)
"""
import os
import sys
import time
import json
from typing import List, Dict, Any
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Add root directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.evaluation import RankingEvaluator
from app.services.skill_extractor import SkillExtractor
from app.services.recommendation_engine import get_sbert_model

# -----------------------------------------------------------------------------
# BENCHMARK EVALUATION DATASET
# Manually curated ground truth representing 5 diverse candidate archetypes
# evaluated against 15 realistic PM internship opportunities.
# -----------------------------------------------------------------------------

BENCHMARK_OPPORTUNITIES = [
    {
        'id': 101,
        'title': 'AI & Computer Vision Research Intern',
        'domain': 'Artificial Intelligence',
        'role_type': 'ML Engineer',
        'skills': ['Python', 'PyTorch', 'Computer Vision', 'Deep Learning', 'OpenCV'],
        'qualification': 'B.Tech Computer Science',
        'location': 'Thane, Maharashtra',
        'sector': 'Healthcare & Biotechnology',
        'description': 'Work on deep learning and computer vision algorithms for microscopic image classification and pattern recognition.'
    },
    {
        'id': 102,
        'title': 'Machine Learning & NLP Intern',
        'domain': 'Data Science',
        'role_type': 'Data Scientist',
        'skills': ['Python', 'Scikit-Learn', 'Natural Language Processing', 'Pandas', 'TensorFlow'],
        'qualification': 'B.Tech / M.Sc Computer Science',
        'location': 'Bangalore, Karnataka',
        'sector': 'Information Technology',
        'description': 'Develop NLP pipelines and information extraction models from unstructured text documents and candidate resumes.'
    },
    {
        'id': 103,
        'title': 'Full-Stack Web Development Intern',
        'domain': 'Software Engineering',
        'role_type': 'Full Stack Developer',
        'skills': ['Python', 'Django', 'React', 'JavaScript', 'SQL', 'REST APIs'],
        'qualification': 'B.Tech / B.E.',
        'location': 'Pune, Maharashtra',
        'sector': 'Information Technology',
        'description': 'Build responsive web portals, robust backend REST APIs, and integrate database systems for digital government services.'
    },
    {
        'id': 104,
        'title': 'Frontend React & UI/UX Intern',
        'domain': 'Web Development',
        'role_type': 'Frontend Developer',
        'skills': ['React', 'JavaScript', 'TypeScript', 'HTML', 'CSS', 'UI/UX', 'Figma'],
        'qualification': 'Bachelor Degree',
        'location': 'Mumbai, Maharashtra',
        'sector': 'Design & Media',
        'description': 'Create user-friendly interfaces, design interactive wireframes in Figma, and build responsive web components in React.'
    },
    {
        'id': 105,
        'title': 'Cloud DevOps & Infrastructure Intern',
        'domain': 'Cloud Computing',
        'role_type': 'DevOps Engineer',
        'skills': ['AWS', 'Docker', 'Kubernetes', 'Linux', 'CI/CD', 'Git'],
        'qualification': 'B.Tech IT / Computer Science',
        'location': 'Hyderabad, Telangana',
        'sector': 'Cloud & Infrastructure',
        'description': 'Automate containerized deployments with Docker and Kubernetes, configure CI/CD pipelines, and manage cloud resources.'
    },
    {
        'id': 106,
        'title': 'Data Analytics & Business Intelligence Intern',
        'domain': 'Business Intelligence',
        'role_type': 'Data Analyst',
        'skills': ['SQL', 'Tableau', 'Power BI', 'Data Analysis', 'Excel', 'Data Visualization'],
        'qualification': 'B.Com / B.Sc / B.Tech',
        'location': 'New Delhi, Delhi',
        'sector': 'Banking & Financial Services',
        'description': 'Analyze transactional trends, write complex SQL queries, and construct executive dashboards using Tableau and Power BI.'
    },
    {
        'id': 107,
        'title': 'Product Management & Strategy Intern',
        'domain': 'Product Management',
        'role_type': 'Product Manager',
        'skills': ['Product Management', 'Product Strategy', 'Market Research', 'User Research', 'Agile', 'Roadmapping'],
        'qualification': 'MBA / B.Tech',
        'location': 'Bangalore, Karnataka',
        'sector': 'Internet & E-Commerce',
        'description': 'Define product feature roadmaps, conduct user feedback interviews, prioritize backlog in Agile sprints, and track PM KPIs.'
    },
    {
        'id': 108,
        'title': 'Backend Systems & API Intern',
        'domain': 'Backend Engineering',
        'role_type': 'Backend Developer',
        'skills': ['Java', 'Spring Boot', 'PostgreSQL', 'Microservices', 'REST APIs', 'Docker'],
        'qualification': 'B.Tech Computer Science',
        'location': 'Chennai, Tamil Nadu',
        'sector': 'Fintech',
        'description': 'Design scalable microservices using Java and Spring Boot, manage relational schemas in PostgreSQL, and build secure endpoints.'
    },
    {
        'id': 109,
        'title': 'Mobile App Development Intern',
        'domain': 'Mobile Engineering',
        'role_type': 'Mobile Developer',
        'skills': ['Flutter', 'React Native', 'JavaScript', 'Mobile Development', 'REST APIs'],
        'qualification': 'B.Tech / BCA',
        'location': 'Noida, Uttar Pradesh',
        'sector': 'Consumer Tech',
        'description': 'Build cross-platform mobile applications in Flutter and React Native, implementing offline storage and real-time syncing.'
    },
    {
        'id': 110,
        'title': 'Cybersecurity & Security Audit Intern',
        'domain': 'Cybersecurity',
        'role_type': 'Security Analyst',
        'skills': ['Cybersecurity', 'Linux', 'Git', 'Bash', 'Networking'],
        'qualification': 'B.Tech IT / Cybersecurity',
        'location': 'Gurgaon, Haryana',
        'sector': 'Defense & Public Safety',
        'description': 'Conduct vulnerability assessments, audit security policies, monitor network logs, and implement defense-in-depth security.'
    },
    {
        'id': 111,
        'title': 'Deep Learning & Medical Imaging Intern',
        'domain': 'Artificial Intelligence',
        'role_type': 'Research Engineer',
        'skills': ['Python', 'PyTorch', 'Deep Learning', 'Computer Vision', 'SciPy', 'OpenCV'],
        'qualification': 'B.Tech / M.Tech in CS/AI',
        'location': 'Thane, Maharashtra',
        'sector': 'Healthcare & Biotechnology',
        'description': 'Design convolutional neural networks and vision transformers for automated histopathology tissue analysis and cell segmentation.'
    },
    {
        'id': 112,
        'title': 'Digital Marketing & Content Strategy Intern',
        'domain': 'Marketing',
        'role_type': 'Marketing Specialist',
        'skills': ['Digital Marketing', 'Market Research', 'Data Analysis', 'Excel'],
        'qualification': 'B.A. / B.Com / BBA',
        'location': 'Jaipur, Rajasthan',
        'sector': 'Marketing & Advertising',
        'description': 'Plan SEO campaigns, analyze engagement metrics in Excel, and craft content marketing strategies for public awareness.'
    },
    {
        'id': 113,
        'title': 'Embedded Systems & IoT Firmware Intern',
        'domain': 'Hardware & IoT',
        'role_type': 'Embedded Engineer',
        'skills': ['C', 'C++', 'Linux', 'Git'],
        'qualification': 'B.Tech Electronics / Electrical',
        'location': 'Ahmedabad, Gujarat',
        'sector': 'Manufacturing & Electronics',
        'description': 'Develop microcontroller firmware in C/C++, interface with sensors, and debug low-level hardware protocols on embedded Linux.'
    },
    {
        'id': 114,
        'title': 'Database Administration & SQL Developer Intern',
        'domain': 'Database Engineering',
        'role_type': 'Database Specialist',
        'skills': ['SQL', 'PostgreSQL', 'MySQL', 'Redis', 'Database Administration'],
        'qualification': 'B.Tech / BCA / MCA',
        'location': 'Pune, Maharashtra',
        'sector': 'Enterprise Software',
        'description': 'Tune query performance, manage backups, optimize indexing strategies, and configure Redis caching layers.'
    },
    {
        'id': 115,
        'title': 'Associate Product Manager Intern',
        'domain': 'Product Management',
        'role_type': 'Associate PM',
        'skills': ['Product Management', 'User Research', 'Product Analytics', 'SQL', 'Agile', 'Stakeholder Management'],
        'qualification': 'B.Tech / MBA',
        'location': 'Mumbai, Maharashtra',
        'sector': 'Financial Technology',
        'description': 'Collaborate with engineering and design teams to build user stories, run A/B experiments, and drive product adoption.'
    }
]

BENCHMARK_CANDIDATES = [
    {
        'id': 1,
        'name': 'Candidate 1: Deep Learning & Computer Vision Enthusiast',
        'education': 'B.Tech Computer Science',
        'location': 'Thane, Maharashtra',
        'relocation': 'yes',
        'preferred_domains': ['Artificial Intelligence', 'Data Science'],
        'preferred_roles': ['ML Engineer', 'Research Engineer'],
        'preferred_industries': ['Healthcare & Biotechnology', 'Information Technology'],
        'skills': ['Python', 'PyTorch', 'Computer Vision', 'Deep Learning', 'OpenCV', 'Scikit-Learn', 'Pandas', 'NumPy', 'Git'],
        'resume_text': (
            'Passionate machine learning engineer with research focus on deep learning and computer vision. '
            'Implemented convolutional neural networks and vision models in PyTorch. Experienced with OpenCV image preprocessing, '
            'feature extraction, data augmentation, and medical image segmentation. Proficient in Python, Scikit-Learn, and Git.'
        ),
        # Ground truth relevance: 2 = highly relevant, 1 = partially relevant, 0 = irrelevant
        'ground_truth': {
            101: 2,  # AI & Computer Vision Research Intern
            111: 2,  # Deep Learning & Medical Imaging Intern
            102: 1,  # Machine Learning & NLP Intern
            103: 0, 104: 0, 105: 0, 106: 0, 107: 0, 108: 0, 109: 0, 110: 0, 112: 0, 113: 0, 114: 0, 115: 0
        }
    },
    {
        'id': 2,
        'name': 'Candidate 2: Full-Stack Web & Python Developer',
        'education': 'B.Tech Information Technology',
        'location': 'Pune, Maharashtra',
        'relocation': 'yes',
        'preferred_domains': ['Software Engineering', 'Web Development'],
        'preferred_roles': ['Full Stack Developer', 'Backend Developer'],
        'preferred_industries': ['Information Technology', 'Enterprise Software'],
        'skills': ['Python', 'Django', 'React', 'JavaScript', 'SQL', 'PostgreSQL', 'HTML', 'CSS', 'REST APIs', 'Git'],
        'resume_text': (
            'Full stack web developer experienced in building scalable applications with Python and Django. '
            'Built responsive React frontends with modern state management. Designed relational schemas and complex SQL queries '
            'in PostgreSQL. Familiar with RESTful API architecture, Git version control, and containerization fundamentals.'
        ),
        'ground_truth': {
            103: 2,  # Full-Stack Web Development Intern
            104: 1,  # Frontend React & UI/UX Intern
            108: 1,  # Backend Systems & API Intern
            114: 1,  # Database Administration & SQL Developer Intern
            101: 0, 102: 0, 105: 0, 106: 0, 107: 0, 109: 0, 110: 0, 111: 0, 112: 0, 113: 0, 115: 0
        }
    },
    {
        'id': 3,
        'name': 'Candidate 3: Cloud & DevOps Automation Specialist',
        'education': 'B.Tech Computer Science',
        'location': 'Hyderabad, Telangana',
        'relocation': 'no',
        'preferred_domains': ['Cloud Computing', 'Cybersecurity'],
        'preferred_roles': ['DevOps Engineer', 'Security Analyst'],
        'preferred_industries': ['Cloud & Infrastructure', 'Defense & Public Safety'],
        'skills': ['AWS', 'Docker', 'Kubernetes', 'Linux', 'CI/CD', 'Git', 'Jenkins', 'Bash', 'Cybersecurity'],
        'resume_text': (
            'Cloud and infrastructure enthusiast experienced in automated CI/CD pipelines and container orchestration. '
            'Managed Docker containers, Kubernetes clusters, and AWS resources. Proficient with Linux administration, '
            'shell scripting in Bash, Git workflows, and security baseline auditing.'
        ),
        'ground_truth': {
            105: 2,  # Cloud DevOps & Infrastructure Intern
            110: 2,  # Cybersecurity & Security Audit Intern
            108: 1,  # Backend Systems & API Intern
            101: 0, 102: 0, 103: 0, 104: 0, 106: 0, 107: 0, 109: 0, 111: 0, 112: 0, 113: 0, 114: 0, 115: 0
        }
    },
    {
        'id': 4,
        'name': 'Candidate 4: Product Manager & User Research Associate',
        'education': 'MBA / B.Tech',
        'location': 'Bangalore, Karnataka',
        'relocation': 'yes',
        'preferred_domains': ['Product Management', 'Business Intelligence'],
        'preferred_roles': ['Product Manager', 'Associate PM', 'Data Analyst'],
        'preferred_industries': ['Internet & E-Commerce', 'Financial Technology'],
        'skills': ['Product Management', 'Product Strategy', 'Market Research', 'User Research', 'Product Analytics', 'Roadmapping', 'Agile', 'Scrum', 'SQL', 'Stakeholder Management'],
        'resume_text': (
            'Product management professional with a dual technical and business background. Led user discovery interviews, '
            'drafted product requirement documents (PRDs), and prioritized Agile sprint backlogs. Proficient in product analytics, '
            'market research, roadmap planning, and writing SQL to track user activation and retention metrics.'
        ),
        'ground_truth': {
            107: 2,  # Product Management & Strategy Intern
            115: 2,  # Associate Product Manager Intern
            106: 1,  # Data Analytics & BI Intern
            101: 0, 102: 0, 103: 0, 104: 0, 105: 0, 108: 0, 109: 0, 110: 0, 111: 0, 112: 0, 113: 0, 114: 0
        }
    },
    {
        'id': 5,
        'name': 'Candidate 5: Data Analyst & Business Intelligence Specialist',
        'education': 'B.Sc Statistics / Computer Science',
        'location': 'New Delhi, Delhi',
        'relocation': 'maybe',
        'preferred_domains': ['Business Intelligence', 'Data Science'],
        'preferred_roles': ['Data Analyst', 'Data Scientist'],
        'preferred_industries': ['Banking & Financial Services', 'Information Technology'],
        'skills': ['SQL', 'Tableau', 'Power BI', 'Data Analysis', 'Excel', 'Data Visualization', 'Python', 'Pandas'],
        'resume_text': (
            'Data analyst proficient in quantitative analysis, complex relational SQL queries, and interactive reporting. '
            'Designed multi-page operational dashboards in Tableau and Power BI. Experienced in Python data wrangling with Pandas '
            'and statistical analysis in Excel for enterprise business intelligence.'
        ),
        'ground_truth': {
            106: 2,  # Data Analytics & BI Intern
            114: 1,  # Database Administration & SQL Developer Intern
            102: 1,  # Machine Learning & NLP Intern
            107: 0, 101: 0, 103: 0, 104: 0, 105: 0, 108: 0, 109: 0, 110: 0, 111: 0, 112: 0, 113: 0, 115: 0
        }
    }
]


# -----------------------------------------------------------------------------
# ALGORITHM IMPLEMENTATIONS FOR EVALUATION
# -----------------------------------------------------------------------------

def build_opp_text(opp: Dict[str, Any]) -> str:
    """Build unified text representation for an opportunity."""
    return f"{opp['title']} {opp['domain']} {opp['role_type']} {' '.join(opp['skills'])} {opp['description']}"

def build_candidate_text(cand: Dict[str, Any]) -> str:
    """Build unified text representation for a candidate."""
    return f"{' '.join(cand['skills'])} {' '.join(cand['preferred_domains'])} {' '.join(cand['preferred_roles'])} {cand['resume_text']}"


def run_tfidf_baseline(candidate: Dict[str, Any], opportunities: List[Dict[str, Any]]) -> List[int]:
    """
    Model 1: Pure TF-IDF Baseline.
    Ranks opportunities purely by TF-IDF cosine similarity.
    """
    cand_text = build_candidate_text(candidate)
    opp_texts = [build_opp_text(opp) for opp in opportunities]
    corpus = [cand_text] + opp_texts

    vectorizer = TfidfVectorizer(stop_words='english', max_features=3000, ngram_range=(1, 2))
    tfidf_matrix = vectorizer.fit_transform(corpus)
    similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:])[0]

    ranked_indices = np.argsort(similarities)[::-1]
    return [opportunities[i]['id'] for i in ranked_indices]


def run_sbert_semantic_matching(candidate: Dict[str, Any], opportunities: List[Dict[str, Any]],
                                model) -> List[int]:
    """
    Model 2: Pure Sentence-BERT Semantic Matching.
    Ranks opportunities purely by cosine similarity of dense 384-dimensional embeddings.
    """
    cand_text = build_candidate_text(candidate)
    opp_texts = [build_opp_text(opp) for opp in opportunities]

    cand_emb = model.encode(cand_text, normalize_embeddings=True)
    opp_embs = model.encode(opp_texts, batch_size=16, normalize_embeddings=True)

    similarities = np.dot(opp_embs, cand_emb)
    ranked_indices = np.argsort(similarities)[::-1]
    return [opportunities[i]['id'] for i in ranked_indices]


def run_hybrid_matcher(candidate: Dict[str, Any], opportunities: List[Dict[str, Any]],
                       model, skill_extractor: SkillExtractor) -> List[int]:
    """
    Model 3: InternMatch Explainable Hybrid Recommendation Engine.
    Combines:
    - Rule-based Skill Overlap (30%)
    - Sentence-BERT Semantic Matching (25%)
    - TF-IDF Baseline Similarity (15%)
    - Education Compatibility (15%)
    - Domain/Role/Industry Preferences (10%)
    - Location Compatibility (5%)
    """
    cand_text = build_candidate_text(candidate)
    opp_texts = [build_opp_text(opp) for opp in opportunities]
    corpus = [cand_text] + opp_texts

    # 1. TF-IDF
    vectorizer = TfidfVectorizer(stop_words='english', max_features=3000, ngram_range=(1, 2))
    tfidf_matrix = vectorizer.fit_transform(corpus)
    tfidf_sims = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:])[0]

    # 2. SBERT Semantic Similarity
    cand_emb = model.encode(cand_text, normalize_embeddings=True)
    opp_embs = model.encode(opp_texts, batch_size=16, normalize_embeddings=True)
    sbert_sims = np.dot(opp_embs, cand_emb)
    # Scale from [-1, 1] to [0, 1]
    sbert_sims = np.clip((sbert_sims + 1.0) / 2.0, 0.0, 1.0)

    # 3. Rule-based scores
    cand_skills = set(s.lower() for s in skill_extractor.normalize_skills(candidate['skills']))
    scores = []

    for i, opp in enumerate(opportunities):
        # Skills match score
        opp_skills = set(s.lower() for s in skill_extractor.normalize_skills(opp['skills']))
        skills_score = len(cand_skills & opp_skills) / len(opp_skills) if opp_skills else 1.0

        # Education match score
        cand_edu = candidate['education'].lower()
        opp_qual = opp['qualification'].lower()
        if 'b.tech' in opp_qual and 'b.tech' in cand_edu:
            edu_score = 1.0
        elif any(deg in cand_edu for deg in ['b.tech', 'b.e.', 'm.sc', 'mba']) and any(deg in opp_qual for deg in ['bachelor', 'b.tech', 'degree']):
            edu_score = 0.9
        else:
            edu_score = 0.5

        # Preference match score
        pref_score = 0.0
        factors = 0
        if opp['domain'] in candidate['preferred_domains']:
            pref_score += 1.0
        factors += 1
        if opp['role_type'] in candidate['preferred_roles']:
            pref_score += 1.0
        factors += 1
        if opp['sector'] in candidate['preferred_industries']:
            pref_score += 1.0
        factors += 1
        pref_score = pref_score / factors if factors else 0.5

        # Location score
        if candidate['location'].lower() in opp['location'].lower():
            loc_score = 1.0
        elif candidate.get('relocation') == 'yes':
            loc_score = 0.8
        elif candidate.get('relocation') == 'maybe':
            loc_score = 0.6
        else:
            loc_score = 0.3

        # Hybrid composite score
        total_score = (
            skills_score * 0.30 +
            float(sbert_sims[i]) * 0.25 +
            float(tfidf_sims[i]) * 0.15 +
            edu_score * 0.15 +
            pref_score * 0.10 +
            loc_score * 0.05
        )
        scores.append(total_score)

    ranked_indices = np.argsort(scores)[::-1]
    return [opportunities[i]['id'] for i in ranked_indices]


def run_evaluation() -> Dict[str, Any]:
    """Run full evaluation suite across all 5 benchmark candidates and 3 models."""
    print("=" * 80)
    print("INTERNMATCH RECOMMENDATION ENGINE - EMPIRICAL BENCHMARK EVALUATION")
    print("Comparing: (1) TF-IDF Baseline  (2) Sentence-BERT Semantic  (3) Hybrid Engine")
    print("=" * 80)

    t_load_start = time.time()
    sbert_model = get_sbert_model()
    skill_extractor = SkillExtractor()
    model_load_time = time.time() - t_load_start
    print(f"[*] Sentence-BERT model loaded in {model_load_time:.2f} seconds.")

    models = ['TF-IDF Baseline', 'Sentence-BERT Semantic', 'Hybrid Recommender']
    results_by_model: Dict[str, List[Dict[str, float]]] = {m: [] for m in models}
    latencies: Dict[str, List[float]] = {m: [] for m in models}

    for cand in BENCHMARK_CANDIDATES:
        print(f"\nEvaluating: {cand['name']}")
        gt = cand['ground_truth']

        # 1. TF-IDF
        t0 = time.time()
        tfidf_ranks = run_tfidf_baseline(cand, BENCHMARK_OPPORTUNITIES)
        latencies['TF-IDF Baseline'].append((time.time() - t0) * 1000)
        tfidf_metrics = RankingEvaluator.evaluate_ranking(tfidf_ranks, gt, ks=[3, 5])
        results_by_model['TF-IDF Baseline'].append(tfidf_metrics)

        # 2. SBERT
        t0 = time.time()
        sbert_ranks = run_sbert_semantic_matching(cand, BENCHMARK_OPPORTUNITIES, sbert_model)
        latencies['Sentence-BERT Semantic'].append((time.time() - t0) * 1000)
        sbert_metrics = RankingEvaluator.evaluate_ranking(sbert_ranks, gt, ks=[3, 5])
        results_by_model['Sentence-BERT Semantic'].append(sbert_metrics)

        # 3. Hybrid
        t0 = time.time()
        hybrid_ranks = run_hybrid_matcher(cand, BENCHMARK_OPPORTUNITIES, sbert_model, skill_extractor)
        latencies['Hybrid Recommender'].append((time.time() - t0) * 1000)
        hybrid_metrics = RankingEvaluator.evaluate_ranking(hybrid_ranks, gt, ks=[3, 5])
        results_by_model['Hybrid Recommender'].append(hybrid_metrics)

    # Aggregate metrics across all candidates
    summary: Dict[str, Dict[str, float]] = {}
    metric_keys = ['P@3', 'P@5', 'R@3', 'R@5', 'NDCG@3', 'NDCG@5', 'MRR@3', 'MRR@5']

    for m in models:
        summary[m] = {}
        for mk in metric_keys:
            vals = [res[mk] for res in results_by_model[m]]
            summary[m][mk] = float(np.mean(vals))
        summary[m]['Avg_Latency_ms'] = float(np.mean(latencies[m]))

    # Print summary table
    print("\n" + "=" * 95)
    print("AGGREGATE EMPIRICAL EVALUATION RESULTS (Across 5 Benchmark Test Personas)")
    print("=" * 95)
    header = f"{'Model':<25} | {'P@3':<7} | {'P@5':<7} | {'R@3':<7} | {'R@5':<7} | {'NDCG@3':<8} | {'NDCG@5':<8} | {'MRR@5':<7} | {'Latency':<8}"
    print(header)
    print("-" * 95)
    for m in models:
        s = summary[m]
        row = (
            f"{m:<25} | {s['P@3']:.4f}  | {s['P@5']:.4f}  | {s['R@3']:.4f}  | {s['R@5']:.4f}  | "
            f"{s['NDCG@3']:.4f}   | {s['NDCG@5']:.4f}   | {s['MRR@5']:.4f}  | {s['Avg_Latency_ms']:.1f} ms"
        )
        print(row)
    print("=" * 95)

    # Save to JSON
    output_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'evaluation_report.json')
    report_data = {
        'benchmark_dataset': {
            'candidates_count': len(BENCHMARK_CANDIDATES),
            'opportunities_count': len(BENCHMARK_OPPORTUNITIES),
            'methodology': 'Manually labeled ground-truth evaluation set with graded relevance (0=irrelevant, 1=marginal, 2=high)',
            'evaluation_date': time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())
        },
        'models_compared': models,
        'summary_metrics': summary,
        'per_candidate_results': {
            cand['name']: {
                m: results_by_model[m][idx] for m in models
            }
            for idx, cand in enumerate(BENCHMARK_CANDIDATES)
        }
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, indent=2)
    print(f"\n[+] Full evaluation report successfully saved to: {output_path}")

    return report_data


if __name__ == '__main__':
    run_evaluation()

