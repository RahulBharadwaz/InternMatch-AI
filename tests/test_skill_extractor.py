"""
Unit tests for SkillExtractor service
Validates canonical taxonomy, alias mapping, boundary guards, and normalization.
"""
import pytest
from app.services.skill_extractor import SkillExtractor


@pytest.fixture
def extractor():
    return SkillExtractor()


def test_taxonomy_canonical_names(extractor):
    """Verify canonical skills are correctly registered."""
    skills = extractor.extract_skills("Experienced in Python, PyTorch, Docker, and PostgreSQL.")
    assert "Python" in skills
    assert "PyTorch" in skills
    assert "Docker" in skills
    assert "PostgreSQL" in skills


def test_synonym_and_alias_mapping(extractor):
    """Verify aliases and abbreviations map to their canonical names."""
    text = "Proficient in py, k8s, reactjs, postgres, and aws."
    skills = extractor.extract_skills(text)
    assert "Python" in skills
    assert "Kubernetes" in skills
    assert "React" in skills
    assert "PostgreSQL" in skills
    assert "AWS" in skills


def test_boundary_protection_prevents_subword_matches(extractor):
    """Verify that substring skills do not trigger on larger words."""
    # 'Java' should not trigger on 'JavaScript'
    # 'C' should not trigger on 'CSS' or 'C++'
    text = "We write JavaScript, TypeScript, and CSS."
    skills = extractor.extract_skills(text)
    assert "JavaScript" in skills
    assert "TypeScript" in skills
    assert "CSS" in skills
    assert "Java" not in skills
    assert "C" not in skills


def test_special_symbol_skills(extractor):
    """Verify programming languages with symbols are correctly parsed."""
    text = "Strong foundations in C++, C#, and Node.js backend development."
    skills = extractor.extract_skills(text)
    assert "C++" in skills
    assert "C#" in skills
    assert "Node.js" in skills


def test_deduplication_and_normalization(extractor):
    """Verify duplicate and mixed-case skills normalize to unique canonical names."""
    raw_list = ["python", "Python 3", "PYTHON", "Py", "react", "ReactJS"]
    normalized = extractor.normalize_skills(raw_list)
    assert normalized == ["Python", "React"]


def test_skill_category_lookup(extractor):
    """Verify skill category classification."""
    assert extractor.get_skill_category("PyTorch") == "data_and_ml"
    assert extractor.get_skill_category("Kubernetes") == "cloud_and_devops"
    assert extractor.get_skill_category("React") == "frameworks_and_libraries"
    assert extractor.get_skill_category("Product Management") == "product_and_business"
    assert extractor.get_skill_category("UnknownSkill") == "general"


def test_empty_and_none_handling(extractor):
    """Verify extractor handles empty or invalid inputs gracefully."""
    assert extractor.extract_skills("") == []
    assert extractor.extract_skills(None) == []
    assert extractor.normalize_skill("") is None
    assert extractor.normalize_skills([]) == []

