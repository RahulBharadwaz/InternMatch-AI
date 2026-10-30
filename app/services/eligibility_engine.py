"""
Eligibility Evaluation Engine
Evaluates student eligibility based on configurable rules (qualification, age, employment).
"""
import json
from datetime import date
from typing import Dict, Any, List, Optional
from app.extensions import db
from app.models import EligibilityRule, StudentProfile, EducationRecord, StudentSkill


class EligibilityEngine:
    """Engine for evaluating student eligibility against active PMIS and institutional rules."""

    def __init__(self, rules: Optional[List[EligibilityRule]] = None):
        self.rules = rules if rules is not None else EligibilityRule.query.filter_by(is_active=True).all()

    def evaluate_student(self, user_id: int) -> Dict[str, Any]:
        """
        Evaluate a student's eligibility across all mandatory and advisory rules.

        Args:
            user_id: The ID of the student user.

        Returns:
            dict: Comprehensive evaluation results with overall status and granular failure reasons.
        """
        profile = StudentProfile.query.filter_by(user_id=user_id).first()
        education = EducationRecord.query.filter_by(profile_id=profile.id).all() if profile else []
        skills = StudentSkill.query.filter_by(user_id=user_id).all()

        results = {
            'eligible': True,
            'mandatory_failures': [],
            'warnings': [],
            'insufficient_info': []
        }

        for rule in self.rules:
            if not rule.is_mandatory:
                continue

            evaluation = self._evaluate_rule(rule, profile, education, skills)

            if evaluation['status'] == 'fail':
                results['eligible'] = False
                results['mandatory_failures'].append({
                    'rule': rule.name,
                    'reason': evaluation['reason']
                })
            elif evaluation['status'] == 'warning':
                results['warnings'].append({
                    'rule': rule.name,
                    'reason': evaluation['reason']
                })
            elif evaluation['status'] == 'insufficient_info':
                results['insufficient_info'].append({
                    'rule': rule.name,
                    'reason': evaluation['reason']
                })

        # Determine overall status
        if results['mandatory_failures']:
            results['overall_status'] = 'ineligible'
        elif results['insufficient_info']:
            results['overall_status'] = 'insufficient_info'
        else:
            results['overall_status'] = 'eligible'

        return results

    def _evaluate_rule(self, rule: EligibilityRule, profile: Optional[StudentProfile],
                       education: List[EducationRecord], skills: List[StudentSkill]) -> Dict[str, str]:
        """Evaluate a single rule against student details."""
        try:
            condition = json.loads(rule.condition) if rule.condition else {}
        except (TypeError, json.JSONDecodeError):
            condition = {}

        if rule.rule_type == 'qualification':
            return self._evaluate_qualification(condition, education)
        elif rule.rule_type == 'age':
            return self._evaluate_age(condition, profile)
        elif rule.rule_type == 'employment_status':
            return self._evaluate_employment(condition, profile)
        else:
            return {'status': 'insufficient_info', 'reason': f'Unsupported rule type: {rule.rule_type}'}

    def _evaluate_qualification(self, condition: Dict[str, Any], education: List[EducationRecord]) -> Dict[str, str]:
        """Evaluate educational attainment against the minimum qualification requirement."""
        min_level = condition.get('min_level', 'bachelor').lower()

        if not education:
            return {'status': 'insufficient_info', 'reason': 'No education records found in profile.'}

        qualification_levels = {
            'diploma': 1,
            'bachelor': 2,
            'master': 3,
            'phd': 4
        }
        required_rank = qualification_levels.get(min_level, 2)

        for edu in education:
            qual = (edu.highest_qualification or '').lower()
            course = (edu.course or '').lower()
            combined = f"{qual} {course}"

            level_rank = 0
            if any(term in combined for term in ['phd', 'doctorate', 'ph.d']):
                level_rank = 4
            elif any(term in combined for term in ['m.tech', 'm.e.', 'm.sc', 'mba', 'mca', 'master']):
                level_rank = 3
            elif any(term in combined for term in ['b.tech', 'b.e.', 'b.sc', 'b.com', 'b.a', 'bba', 'bachelor', 'b.ca', 'bca']):
                level_rank = 2
            elif any(term in combined for term in ['diploma', 'polytechnic', '12th', 'hsc']):
                level_rank = 1

            if level_rank >= required_rank:
                return {'status': 'pass', 'reason': f'Qualification meets or exceeds requirement ({min_level.title()}).'}

        return {'status': 'fail', 'reason': f'Qualification is below the required level of {min_level.title()}.'}

    def _evaluate_age(self, condition: Dict[str, Any], profile: Optional[StudentProfile]) -> Dict[str, str]:
        """Evaluate candidate age using Date of Birth from StudentProfile."""
        if not profile or not profile.date_of_birth:
            return {'status': 'insufficient_info', 'reason': 'Date of birth not provided in student profile.'}

        dob = profile.date_of_birth
        today = date.today()
        # Compute age in complete years
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

        min_age = condition.get('min_age')
        max_age = condition.get('max_age')

        if min_age is not None and age < min_age:
            return {
                'status': 'fail',
                'reason': f'Age {age} is below the minimum required age of {min_age} years.'
            }
        if max_age is not None and age > max_age:
            return {
                'status': 'fail',
                'reason': f'Age {age} exceeds the maximum allowed age of {max_age} years.'
            }

        return {
            'status': 'pass',
            'reason': f'Age {age} is within the required range ({min_age}-{max_age} years).'
        }

    def _evaluate_employment(self, condition: Dict[str, Any], profile: Optional[StudentProfile]) -> Dict[str, str]:
        """Evaluate candidate employment status against scheme eligibility criteria."""
        if not profile or not profile.employment_status:
            return {'status': 'insufficient_info', 'reason': 'Employment status not specified in profile.'}

        status = profile.employment_status.strip().lower()

        # PMIS criteria: Candidate must not be in full-time employment
        must_not_be_employed = condition.get('employed') is False or condition.get('allow_employed') is False

        if must_not_be_employed and status in {'employed', 'self_employed', 'working'}:
            return {
                'status': 'fail',
                'reason': f'Current employment status ({status.replace("_", " ").title()}) is ineligible for this scheme.'
            }

        # Check for allowed statuses if explicitly provided
        allowed_statuses = condition.get('allowed_statuses')
        if allowed_statuses and status not in [s.lower() for s in allowed_statuses]:
            return {
                'status': 'fail',
                'reason': f'Employment status ({status.title()}) is not in the allowed list.'
            }

        return {
            'status': 'pass',
            'reason': f'Employment status ({status.replace("_", " ").title()}) is eligible.'
        }
