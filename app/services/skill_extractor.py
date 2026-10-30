"""
Skill Extraction and Taxonomy Module
Extracts, normalizes, and categorizes technical and domain skills from text.
Supports synonym mapping, case-insensitivity, and robust boundary checking.
"""
import re
from typing import List, Dict, Set, Optional, Tuple


class SkillExtractor:
    """Extracts and normalizes skills from text using a canonical taxonomy and alias map."""

    # Canonical taxonomy: mapping category -> set of canonical skill names
    TAXONOMY = {
        'programming_languages': {
            'Python', 'Java', 'JavaScript', 'TypeScript', 'C++', 'C#', 'C', 'PHP',
            'Go', 'Rust', 'Ruby', 'Kotlin', 'Swift', 'SQL', 'R', 'Scala', 'Bash'
        },
        'frameworks_and_libraries': {
            'React', 'Angular', 'Vue.js', 'Node.js', 'Django', 'Flask', 'FastAPI',
            'Spring Boot', 'Express.js', 'Laravel', 'Next.js', 'HTML', 'CSS',
            'Tailwind CSS', 'Bootstrap'
        },
        'data_and_ml': {
            'Machine Learning', 'Deep Learning', 'Natural Language Processing',
            'Computer Vision', 'PyTorch', 'TensorFlow', 'Scikit-Learn', 'Pandas',
            'NumPy', 'Data Analysis', 'Data Visualization', 'Tableau', 'Power BI',
            'Keras', 'Hugging Face', 'OpenCV', 'SciPy', 'Excel'
        },
        'cloud_and_devops': {
            'AWS', 'Azure', 'GCP', 'Docker', 'Kubernetes', 'Git', 'Linux',
            'CI/CD', 'Jenkins', 'Terraform', 'Microservices', 'REST APIs',
            'GraphQL', 'DevOps', 'Cybersecurity'
        },
        'databases': {
            'MongoDB', 'PostgreSQL', 'MySQL', 'Redis', 'SQLite', 'Elasticsearch',
            'Cassandra', 'Oracle'
        },
        'product_and_business': {
            'Product Management', 'Product Strategy', 'Market Research',
            'User Research', 'Product Analytics', 'Roadmapping',
            'Stakeholder Management', 'Agile', 'Scrum', 'Business Analysis',
            'UI/UX', 'Figma', 'Project Management'
        }
    }

    # Aliases and synonyms mapped to canonical skill name
    ALIASES: Dict[str, str] = {
        # Programming Languages
        'python': 'Python',
        'py': 'Python',
        'python 3': 'Python',
        'python3': 'Python',
        'java': 'Java',
        'javascript': 'JavaScript',
        'js': 'JavaScript',
        'es6': 'JavaScript',
        'ecmascript': 'JavaScript',
        'typescript': 'TypeScript',
        'ts': 'TypeScript',
        'c plus plus': 'C++',
        'cpp': 'C++',
        'c++': 'C++',
        'c sharp': 'C#',
        'c#': 'C#',
        'c': 'C',
        'php': 'PHP',
        'go': 'Go',
        'golang': 'Go',
        'rust': 'Rust',
        'ruby': 'Ruby',
        'kotlin': 'Kotlin',
        'swift': 'Swift',
        'sql': 'SQL',
        'r': 'R',
        'scala': 'Scala',
        'bash': 'Bash',
        'shell scripting': 'Bash',
        'shell': 'Bash',

        # Frameworks & Web
        'react': 'React',
        'react.js': 'React',
        'reactjs': 'React',
        'react native': 'React Native',
        'angular': 'Angular',
        'angular.js': 'Angular',
        'angularjs': 'Angular',
        'vue': 'Vue.js',
        'vuejs': 'Vue.js',
        'vue.js': 'Vue.js',
        'node': 'Node.js',
        'nodejs': 'Node.js',
        'node.js': 'Node.js',
        'express': 'Express.js',
        'expressjs': 'Express.js',
        'express.js': 'Express.js',
        'django': 'Django',
        'flask': 'Flask',
        'fastapi': 'FastAPI',
        'spring boot': 'Spring Boot',
        'spring': 'Spring Boot',
        'springboot': 'Spring Boot',
        'laravel': 'Laravel',
        'next.js': 'Next.js',
        'nextjs': 'Next.js',
        'html': 'HTML',
        'html5': 'HTML',
        'css': 'CSS',
        'css3': 'CSS',
        'html/css': 'HTML',
        'tailwind css': 'Tailwind CSS',
        'tailwind': 'Tailwind CSS',
        'bootstrap': 'Bootstrap',

        # Data & ML
        'machine learning': 'Machine Learning',
        'ml': 'Machine Learning',
        'deep learning': 'Deep Learning',
        'dl': 'Deep Learning',
        'natural language processing': 'Natural Language Processing',
        'nlp': 'Natural Language Processing',
        'computer vision': 'Computer Vision',
        'cv': 'Computer Vision',
        'pytorch': 'PyTorch',
        'torch': 'PyTorch',
        'tensorflow': 'TensorFlow',
        'tf': 'TensorFlow',
        'scikit-learn': 'Scikit-Learn',
        'scikit learn': 'Scikit-Learn',
        'sklearn': 'Scikit-Learn',
        'pandas': 'Pandas',
        'numpy': 'NumPy',
        'scipy': 'SciPy',
        'data analysis': 'Data Analysis',
        'data analytics': 'Data Analysis',
        'data science': 'Data Analysis',
        'data visualization': 'Data Visualization',
        'tableau': 'Tableau',
        'power bi': 'Power BI',
        'powerbi': 'Power BI',
        'keras': 'Keras',
        'hugging face': 'Hugging Face',
        'huggingface': 'Hugging Face',
        'opencv': 'OpenCV',
        'excel': 'Excel',
        'ms excel': 'Excel',

        # Cloud & DevOps
        'aws': 'AWS',
        'amazon web services': 'AWS',
        'azure': 'Azure',
        'microsoft azure': 'Azure',
        'gcp': 'GCP',
        'google cloud': 'GCP',
        'google cloud platform': 'GCP',
        'docker': 'Docker',
        'containers': 'Docker',
        'kubernetes': 'Kubernetes',
        'k8s': 'Kubernetes',
        'git': 'Git',
        'github': 'Git',
        'gitlab': 'Git',
        'linux': 'Linux',
        'unix': 'Linux',
        'ci/cd': 'CI/CD',
        'cicd': 'CI/CD',
        'continuous integration': 'CI/CD',
        'jenkins': 'Jenkins',
        'terraform': 'Terraform',
        'microservices': 'Microservices',
        'rest apis': 'REST APIs',
        'rest api': 'REST APIs',
        'rest': 'REST APIs',
        'restful': 'REST APIs',
        'graphql': 'GraphQL',
        'devops': 'DevOps',
        'cybersecurity': 'Cybersecurity',

        # Databases
        'mongodb': 'MongoDB',
        'mongo': 'MongoDB',
        'postgresql': 'PostgreSQL',
        'postgres': 'PostgreSQL',
        'mysql': 'MySQL',
        'redis': 'Redis',
        'sqlite': 'SQLite',
        'elasticsearch': 'Elasticsearch',
        'cassandra': 'Cassandra',
        'oracle': 'Oracle',

        # Product & Management
        'product management': 'Product Management',
        'product strategy': 'Product Strategy',
        'market research': 'Market Research',
        'user research': 'User Research',
        'product analytics': 'Product Analytics',
        'roadmapping': 'Roadmapping',
        'stakeholder management': 'Stakeholder Management',
        'agile': 'Agile',
        'scrum': 'Scrum',
        'business analysis': 'Business Analysis',
        'ui/ux': 'UI/UX',
        'ui ux': 'UI/UX',
        'ux design': 'UI/UX',
        'ui design': 'UI/UX',
        'figma': 'Figma',
        'project management': 'Project Management'
    }

    def __init__(self):
        # Auto-register any taxonomy items not yet in ALIASES
        for category, skills in self.TAXONOMY.items():
            for skill in skills:
                lower_skill = skill.lower()
                if lower_skill not in self.ALIASES:
                    self.ALIASES[lower_skill] = skill
        # Precompile regex patterns
        self._compiled_patterns = self._build_patterns()

    def _build_patterns(self) -> List[Tuple[re.Pattern, str]]:
        """Pre-compile regex patterns with boundary guards sorted longest-first."""
        sorted_phrases = sorted(self.ALIASES.keys(), key=lambda k: len(k), reverse=True)
        patterns = []
        for phrase in sorted_phrases:
            canonical = self.ALIASES[phrase]
            escaped = re.escape(phrase)
            if phrase.lower() == 'c':
                pattern = re.compile(r'(?<![a-zA-Z0-9])c(?![a-zA-Z0-9+#])', re.IGNORECASE)
            else:
                pattern = re.compile(r'(?<![a-zA-Z0-9])' + escaped + r'(?![a-zA-Z0-9])', re.IGNORECASE)
            patterns.append((pattern, canonical))
        return patterns

    def extract_skills(self, text: str) -> List[str]:
        """
        Extract canonical skills from text.

        Args:
            text: Raw input text from resume or opportunity description.

        Returns:
            Alphabetically sorted, deduplicated list of canonical skill names.
        """
        if not text or not isinstance(text, str):
            return []

        matched_skills: Set[str] = set()
        for pattern, canonical in self._compiled_patterns:
            if pattern.search(text):
                matched_skills.add(canonical)

        return sorted(matched_skills)

    def normalize_skill(self, skill_name: str) -> Optional[str]:
        """
        Normalize a single skill name to its canonical representation.

        Args:
            skill_name: The raw or variant skill name (e.g., 'reactjs', 'k8s').

        Returns:
            Canonical skill name or title-cased fallback if unknown.
        """
        if not skill_name or not isinstance(skill_name, str):
            return None
        clean = skill_name.strip().lower()
        if clean in self.ALIASES:
            return self.ALIASES[clean]
        for category, skills in self.TAXONOMY.items():
            for skill in skills:
                if skill.lower() == clean:
                    return skill
        return skill_name.strip()

    def normalize_skills(self, skills: List[str]) -> List[str]:
        """Normalize a collection of skill names to canonical forms, deduplicated."""
        normalized = set()
        for s in skills:
            canonical = self.normalize_skill(s)
            if canonical:
                normalized.add(canonical)
        return sorted(normalized)

    def get_skill_category(self, canonical_skill: str) -> str:
        """Return the category for a given canonical skill name."""
        for category, skills in self.TAXONOMY.items():
            if canonical_skill in skills:
                return category
        return 'general'
