"""
Hybrid Recommendation Engine for InternMatch
Combines Rule-Based Matching, TF-IDF Text Similarity Baseline, and
Sentence-BERT (Transformer) Semantic Embeddings with In-Memory Caching and Explainability.
"""
import json
import logging
from datetime import date, datetime
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy import or_
from sqlalchemy.orm import joinedload

from app.extensions import db
from app.models import (
    StudentProfile, EducationRecord, StudentSkill,
    Opportunity, OpportunitySkill, Recommendation, RecommendationItem,
    Resume, ResumeExtraction
)
from app.services.eligibility_engine import EligibilityEngine
from app.services.skill_extractor import SkillExtractor
from app.services.vector_index import FAISSVectorIndex
from config import Config

logger = logging.getLogger(__name__)

# Global singletons for model, FAISS index, and embedding cache across requests
_SBERT_MODEL = None
_FAISS_INDEX = FAISSVectorIndex(dimension=384, index_type='flat')
_OPPORTUNITY_EMBEDDING_CACHE: Dict[int, Tuple[datetime, np.ndarray]] = {}


def get_faiss_index() -> FAISSVectorIndex:
    """Return the global FAISS vector index singleton."""
    global _FAISS_INDEX
    return _FAISS_INDEX


def get_sbert_model():
    """Lazy-load and return the Sentence-BERT model singleton."""
    global _SBERT_MODEL
    if _SBERT_MODEL is None:
        try:
            from sentence_transformers import SentenceTransformer
            model_name = getattr(Config, 'SBERT_MODEL_NAME', 'all-MiniLM-L6-v2')
            logger.info("Loading Sentence-BERT model: %s", model_name)
            _SBERT_MODEL = SentenceTransformer(model_name)
        except Exception as e:
            logger.warning("Failed to load Sentence-BERT model (%s). Fallback to TF-IDF semantic approximation: %s",
                           getattr(Config, 'SBERT_MODEL_NAME', 'all-MiniLM-L6-v2'), e)
            _SBERT_MODEL = False
    return _SBERT_MODEL if _SBERT_MODEL is not False else None


class RecommendationEngine:
    """Production-grade hybrid recommendation engine for PM internship opportunities."""

    def __init__(self):
        self.eligibility_engine = EligibilityEngine()
        self.skill_extractor = SkillExtractor()
        self.weights = self._normalize_weights(Config.RECOMMENDATION_WEIGHTS)

    @staticmethod
    def _normalize_weights(raw_weights: Dict[str, float]) -> Dict[str, float]:
        """Ensure recommendation weights sum to 1.0."""
        total = sum(raw_weights.values())
        if total <= 0:
            return {
                'skills_match': 0.30,
                'semantic_similarity': 0.25,
                'text_similarity': 0.15,
                'education_compatibility': 0.15,
                'preference_match': 0.10,
                'location_match': 0.05
            }
        return {k: v / total for k, v in raw_weights.items()}

    def generate_recommendations(self, user_id: int, top_n: int = 10) -> Optional[int]:
        """
        Generate ranked recommendations for a user.

        Args:
            user_id: ID of the user to generate recommendations for.
            top_n: Number of recommendations to store (default: 10).

        Returns:
            int: ID of the newly generated recommendation record, or None if no open opportunities exist.
        """
        profile = StudentProfile.query.filter_by(user_id=user_id).first()
        education = EducationRecord.query.filter_by(profile_id=profile.id).all() if profile else []
        user_skills_records = StudentSkill.query.filter_by(user_id=user_id).options(joinedload(StudentSkill.skill)).all()

        # Collect raw skill names from all available profile sources
        raw_skills = [us.skill.name for us in user_skills_records if us.skill]
        if profile and profile.skills:
            raw_skills.extend(self._json_list(profile.skills))

        resume = Resume.query.filter_by(user_id=user_id).first()
        extraction = ResumeExtraction.query.filter_by(resume_id=resume.id).first() if resume else None
        if extraction and extraction.extracted_skills:
            raw_skills.extend(self._json_list(extraction.extracted_skills))

        # Normalize skills using canonical taxonomy and deduplicate
        user_skills = self.skill_extractor.normalize_skills(raw_skills)
        profile_text = self._build_profile_text(profile, education, user_skills, extraction)

        # Exclude opportunities with past deadlines; eagerly load relationships to prevent N+1 queries
        opportunities = Opportunity.query.filter_by(is_published=True).filter(
            or_(
                Opportunity.application_deadline.is_(None),
                Opportunity.application_deadline >= date.today()
            )
        ).options(
            joinedload(Opportunity.organization),
            joinedload(Opportunity.opportunity_skills).joinedload(OpportunitySkill.skill)
        ).all()

        if not opportunities:
            return None

        # Pre-evaluate eligibility ONCE for the student (fixes N+1 query bug)
        eligibility_result = self.eligibility_engine.evaluate_student(user_id)
        overall_eligibility = eligibility_result.get('overall_status', 'eligible')

        # Batch-compute TF-IDF similarities across all opportunities
        tfidf_scores = self._batch_calculate_tfidf_similarity(profile_text, opportunities)

        # Batch-compute Sentence-BERT semantic similarities across all opportunities with caching
        semantic_scores = self._batch_calculate_semantic_similarity(profile_text, opportunities)

        scored_opportunities = []
        for i, opp in enumerate(opportunities):
            score_data = self._calculate_opportunity_score(
                user_id=user_id,
                opp=opp,
                profile=profile,
                education=education,
                user_skills=user_skills,
                tfidf_score=tfidf_scores[i],
                semantic_score=semantic_scores[i],
                eligibility_status=overall_eligibility
            )
            scored_opportunities.append({
                'opportunity': opp,
                'score': score_data
            })

        # Sort descending by total match score
        scored_opportunities.sort(key=lambda x: x['score']['total_score'], reverse=True)

        # Persist recommendation snapshot
        recommendation = Recommendation(
            user_id=user_id,
            algorithm_version=Config.RECOMMENDATION_ALGORITHM_VERSION,
            profile_snapshot=json.dumps({
                'skills': user_skills,
                'education': [{'qualification': e.highest_qualification, 'course': e.course} for e in education],
                'preferences': {
                    'industries': self._json_list(profile.preferred_industries) if profile else [],
                    'domains': self._json_list(profile.preferred_domains) if profile else [],
                    'location': profile.preferred_location
                } if profile else {},
                'resume_analyzed': extraction is not None,
                'weights': self.weights
            })
        )
        db.session.add(recommendation)
        db.session.flush()

        # Persist top-N recommendation items
        for rank, item in enumerate(scored_opportunities[:top_n], 1):
            score_info = item['score']
            rec_item = RecommendationItem(
                recommendation_id=recommendation.id,
                opportunity_id=item['opportunity'].id,
                match_score=float(score_info['total_score']),
                skills_score=float(score_info['skills_score']),
                education_score=float(score_info['education_score']),
                text_similarity_score=float(score_info['text_similarity_score']),
                semantic_score=float(score_info.get('semantic_score', 0.0)),
                preference_score=float(score_info['preference_score']),
                location_score=float(score_info['location_score']),
                eligibility_status=score_info['eligibility_status'],
                explanation=score_info['explanation'],
                matching_skills=json.dumps(score_info['matching_skills']),
                missing_skills=json.dumps(score_info['missing_skills']),
                rank=rank
            )
            db.session.add(rec_item)

        db.session.commit()
        return recommendation.id

    def _calculate_opportunity_score(self, user_id: int, opp: Opportunity, profile: Optional[StudentProfile],
                                   education: List[EducationRecord], user_skills: List[str],
                                   tfidf_score: float, semantic_score: float,
                                   eligibility_status: str) -> Dict[str, Any]:
        """Compute all granular match signals and composite score for an individual opportunity."""
        # Collect and normalize required skills for this opportunity
        opp_raw_skills = [item.skill.name for item in opp.opportunity_skills if item.skill]
        if opp.skills_required:
            opp_raw_skills.extend(self._json_list(opp.skills_required))
        opp_skills = self.skill_extractor.normalize_skills(opp_raw_skills)

        # Skill scoring
        skills_score = self._calculate_skills_score(user_skills, opp_skills)
        education_score = self._calculate_education_score(education, opp)
        preference_score = self._calculate_preference_score(profile, opp)
        location_score = self._calculate_location_score(profile, opp)

        # Weighted composite score
        total_score = (
            skills_score * self.weights.get('skills_match', 0.30) +
            semantic_score * self.weights.get('semantic_similarity', 0.25) +
            tfidf_score * self.weights.get('text_similarity', 0.15) +
            education_score * self.weights.get('education_compatibility', 0.15) +
            preference_score * self.weights.get('preference_match', 0.10) +
            location_score * self.weights.get('location_match', 0.05)
        )
        total_score = max(0.0, min(1.0, float(total_score)))

        # Determine matching and missing skills
        user_skills_set = set(s.lower() for s in user_skills)
        opp_skills_lookup = {s.lower(): s for s in opp_skills}

        matching_keys = user_skills_set & opp_skills_lookup.keys()
        matching_skills = sorted(opp_skills_lookup[k] for k in matching_keys)
        missing_skills = sorted(s for k, s in opp_skills_lookup.items() if k not in user_skills_set)

        # Generate explainable rationale
        explanation = self._generate_explanation(
            skills_score=skills_score,
            semantic_score=semantic_score,
            education_score=education_score,
            preference_score=preference_score,
            location_score=location_score,
            matching_skills=matching_skills,
            missing_skills=missing_skills,
            opp_title=opp.title
        )

        return {
            'total_score': total_score,
            'skills_score': skills_score,
            'semantic_score': semantic_score,
            'text_similarity_score': tfidf_score,
            'education_score': education_score,
            'preference_score': preference_score,
            'location_score': location_score,
            'eligibility_status': eligibility_status,
            'explanation': explanation,
            'matching_skills': matching_skills,
            'missing_skills': missing_skills
        }

    def _calculate_skills_score(self, user_skills: List[str], opp_skills: List[str]) -> float:
        """Calculate skill overlap ratio using canonical normalized skills."""
        if not opp_skills:
            return 1.0
        if not user_skills:
            return 0.0

        user_set = set(s.lower() for s in user_skills)
        opp_set = set(s.lower() for s in opp_skills)
        overlap = len(user_set & opp_set)
        return float(overlap / len(opp_set))

    def _calculate_education_score(self, education: List[EducationRecord], opp: Opportunity) -> float:
        """Score candidate education against required qualification using level hierarchy."""
        if not education or not opp.qualification_required:
            return 0.5  # Neutral default

        opp_qual = opp.qualification_required.lower()

        # Target qualification level rank
        target_rank = 2  # default bachelor
        if any(term in opp_qual for term in ['phd', 'doctorate']):
            target_rank = 4
        elif any(term in opp_qual for term in ['m.tech', 'm.e.', 'm.sc', 'mba', 'mca', 'master']):
            target_rank = 3
        elif any(term in opp_qual for term in ['b.tech', 'b.e.', 'b.sc', 'b.com', 'b.a', 'bachelor']):
            target_rank = 2
        elif any(term in opp_qual for term in ['diploma', '12th']):
            target_rank = 1

        best_score = 0.3
        for edu in education:
            qual = (edu.highest_qualification or '').lower()
            course = (edu.course or '').lower()
            combined = f"{qual} {course}"

            cand_rank = 0
            if any(term in combined for term in ['phd', 'doctorate']):
                cand_rank = 4
            elif any(term in combined for term in ['m.tech', 'm.e.', 'm.sc', 'mba', 'mca', 'master']):
                cand_rank = 3
            elif any(term in combined for term in ['b.tech', 'b.e.', 'b.sc', 'b.com', 'b.a', 'bachelor']):
                cand_rank = 2
            elif any(term in combined for term in ['diploma', '12th']):
                cand_rank = 1

            if cand_rank >= target_rank:
                best_score = max(best_score, 1.0)
            elif cand_rank == target_rank - 1:
                best_score = max(best_score, 0.7)

        return best_score

    def _batch_calculate_tfidf_similarity(self, profile_text: str, opportunities: List[Opportunity]) -> List[float]:
        """
        Compute TF-IDF cosine similarity for profile_text against all opportunities simultaneously.
        Builds a true multi-document corpus ensuring proper Inverse Document Frequency (IDF) estimation.
        """
        if not profile_text or not opportunities:
            return [0.5] * len(opportunities)

        opp_texts = [self._build_opportunity_text(opp) for opp in opportunities]
        corpus = [profile_text] + opp_texts

        try:
            vectorizer = TfidfVectorizer(stop_words='english', max_features=3000, ngram_range=(1, 2))
            tfidf_matrix = vectorizer.fit_transform(corpus)
            # Row 0 is profile vector; rows 1..N are opportunity vectors
            sims = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:])[0]
            return [float(max(0.0, min(1.0, s))) for s in sims]
        except Exception as e:
            logger.warning("TF-IDF vectorization failed: %s. Using neutral similarity.", e)
            return [0.5] * len(opportunities)

    def _batch_calculate_semantic_similarity(self, profile_text: str, opportunities: List[Opportunity]) -> List[float]:
        """
        Compute dense semantic similarity using Sentence-BERT with caching.
        Caches opportunity embeddings by (id, last_updated) to minimize inference latency.
        """
        model = get_sbert_model()
        if model is None or not profile_text:
            # Graceful fallback: return neutral or TF-IDF-based estimate
            return [0.5] * len(opportunities)

        try:
            # 1. Encode profile text (normalize for fast cosine similarity via dot product)
            user_embedding = model.encode(profile_text, normalize_embeddings=True)

            # 2. Retrieve or compute opportunity embeddings
            opp_embeddings = []
            to_encode_indices = []
            to_encode_texts = []

            for idx, opp in enumerate(opportunities):
                cached = _OPPORTUNITY_EMBEDDING_CACHE.get(opp.id)
                # Check if cached and not modified
                if cached and cached[0] == opp.last_updated:
                    opp_embeddings.append(cached[1])
                else:
                    opp_embeddings.append(None)
                    to_encode_indices.append(idx)
                    to_encode_texts.append(self._build_opportunity_text(opp))

            # Batch encode any uncached opportunities
            if to_encode_texts:
                new_embeddings = model.encode(
                    to_encode_texts,
                    batch_size=32,
                    show_progress_bar=False,
                    normalize_embeddings=True
                )
                for i, new_emb in enumerate(new_embeddings):
                    idx = to_encode_indices[i]
                    opp = opportunities[idx]
                    opp_embeddings[idx] = new_emb
                    _OPPORTUNITY_EMBEDDING_CACHE[opp.id] = (opp.last_updated, new_emb)

            # 3. Synchronize FAISS Vector Index and retrieve similarities
            embeddings_matrix = np.vstack(opp_embeddings)
            opp_ids = [opp.id for opp in opportunities]

            # Re-index if count changed or index uninitialized
            if _FAISS_INDEX.total_vectors != len(opportunities):
                _FAISS_INDEX.build_index(opp_ids, embeddings_matrix)

            # Query FAISS vector index with user embedding
            return _FAISS_INDEX.get_similarities_for_opportunities(user_embedding, opp_ids)

        except Exception as e:
            logger.exception("Semantic similarity computation encountered error: %s", e)
            return [0.5] * len(opportunities)

    def _calculate_preference_score(self, profile: Optional[StudentProfile], opp: Opportunity) -> float:
        """Calculate candidate preference alignment across industry, domain, and role."""
        if not profile:
            return 0.5

        score = 0.0
        factors = 0

        # Industry preference
        if profile.preferred_industries:
            factors += 1
            industries = [i.lower() for i in self._json_list(profile.preferred_industries)]
            opp_sector = (opp.organization.sector or '').lower() if opp.organization else ''
            if any(ind in opp_sector for ind in industries):
                score += 1.0

        # Domain preference
        if profile.preferred_domains:
            factors += 1
            domains = [d.lower() for d in self._json_list(profile.preferred_domains)]
            opp_domain = (opp.domain or '').lower()
            if any(d in opp_domain for d in domains):
                score += 1.0

        # Role preference
        if profile.preferred_roles:
            factors += 1
            roles = [r.lower() for r in self._json_list(profile.preferred_roles)]
            opp_role = (opp.role_type or '').lower()
            if any(r in opp_role for r in roles):
                score += 1.0

        return score / factors if factors > 0 else 0.5

    def _calculate_location_score(self, profile: Optional[StudentProfile], opp: Opportunity) -> float:
        """Calculate location compatibility considering candidate relocation preference."""
        if not profile or not profile.preferred_location or not opp.location:
            return 0.5

        pref_loc = profile.preferred_location.strip().lower()
        opp_loc = opp.location.strip().lower()

        if pref_loc in opp_loc or opp_loc in pref_loc or 'remote' in opp_loc or 'virtual' in opp_loc:
            return 1.0

        reloc = (profile.relocation_preference or 'no').lower()
        if reloc == 'yes':
            return 0.8
        elif reloc == 'maybe':
            return 0.6
        return 0.3

    def _build_profile_text(self, profile: Optional[StudentProfile], education: List[EducationRecord],
                            user_skills: List[str], extraction: Optional[ResumeExtraction]) -> str:
        """Construct unified semantic representation of a candidate profile."""
        parts = list(user_skills)
        if profile:
            for pref in (profile.preferred_domains, profile.preferred_roles, profile.preferred_industries):
                parts.extend(self._json_list(pref))
            if profile.preferred_location:
                parts.append(profile.preferred_location)

        for record in education:
            parts.extend(filter(None, (
                record.course,
                record.specialization,
                record.highest_qualification
            )))

        if extraction and extraction.raw_text:
            # Include clean resume text snippet for richer semantic matching
            parts.append(extraction.raw_text[:4000])

        return ' '.join(str(p) for p in parts if p)

    def _build_opportunity_text(self, opp: Opportunity) -> str:
        """Construct full textual description for an opportunity."""
        parts = [opp.title or '', opp.description or '']
        if opp.domain:
            parts.append(opp.domain)
        if opp.role_type:
            parts.append(opp.role_type)
        if opp.skills_required:
            parts.extend(self._json_list(opp.skills_required))
        if opp.qualification_required:
            parts.append(opp.qualification_required)
        return ' '.join(filter(None, parts))

    def _generate_explanation(self, skills_score: float, semantic_score: float,
                              education_score: float, preference_score: float,
                              location_score: float, matching_skills: List[str],
                              missing_skills: List[str], opp_title: str) -> str:
        """Synthesize explainable, candidate-friendly rationale for why an opportunity was matched."""
        points = []

        if matching_skills:
            top_skills = ', '.join(matching_skills[:4])
            points.append(f"Strong overlap on {len(matching_skills)} relevant skills: {top_skills}")

        if semantic_score >= 0.70:
            points.append(f"High semantic alignment with {opp_title} responsibilities")
        elif semantic_score >= 0.45:
            points.append("Good contextual match with your experience and interests")

        if education_score >= 0.9:
            points.append("Your educational background satisfies or exceeds qualifications")

        if preference_score >= 0.7:
            points.append("Matches your chosen domain and role preferences")

        if location_score >= 0.8:
            points.append("Fulfills your location preference")

        if missing_skills:
            key_missing = ', '.join(missing_skills[:3])
            points.append(f"Recommended skills to develop: {key_missing}")

        return '. '.join(points) + '.' if points else "Opportunity aligns with your profile and interests."

    @staticmethod
    def _json_list(value) -> List[str]:
        """Safely deserialize JSON lists with fallback."""
        if not value:
            return []
        if isinstance(value, list):
            return [str(v) for v in value]
        try:
            decoded = json.loads(value)
            return [str(v) for v in decoded] if isinstance(decoded, list) else []
        except (TypeError, json.JSONDecodeError):
            return []
