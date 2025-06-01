"""
Therapist Matching Service for AI-powered therapist recommendations.
"""
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc

from models.user import User
from models.trauma_mapping import TraumaMapping, LifeEvent
from models.professional_bridge import TherapistProfile, TherapistMatch, TherapyModality
from schemas.professional_bridge import TherapistMatchRequest

logger = logging.getLogger(__name__)


class TherapistMatchingService:
    """
    AI-powered therapist matching service based on user's trauma map and preferences.
    """

    def __init__(self):
        # Therapy modality compatibility matrix
        self.modality_compatibility = {
            "trauma": [
                TherapyModality.EMDR,
                TherapyModality.TRAUMA_INFORMED,
                TherapyModality.SOMATIC,
                TherapyModality.CBT
            ],
            "anxiety": [
                TherapyModality.CBT,
                TherapyModality.DBT,
                TherapyModality.MINDFULNESS_BASED
            ],
            "depression": [
                TherapyModality.CBT,
                TherapyModality.PSYCHODYNAMIC,
                TherapyModality.HUMANISTIC
            ],
            "relationship": [
                TherapyModality.FAMILY_THERAPY,
                TherapyModality.HUMANISTIC,
                TherapyModality.PSYCHODYNAMIC
            ],
            "grief": [
                TherapyModality.HUMANISTIC,
                TherapyModality.PSYCHODYNAMIC,
                TherapyModality.TRAUMA_INFORMED
            ]
        }

        # Healing stage preferences
        self.healing_stage_modalities = {
            "denial": [TherapyModality.HUMANISTIC, TherapyModality.TRAUMA_INFORMED],
            "anger": [TherapyModality.DBT, TherapyModality.SOMATIC],
            "bargaining": [TherapyModality.CBT, TherapyModality.PSYCHODYNAMIC],
            "depression": [TherapyModality.CBT, TherapyModality.HUMANISTIC],
            "acceptance": [TherapyModality.MINDFULNESS_BASED, TherapyModality.HUMANISTIC]
        }

    async def find_matches(
        self,
        db: Session,
        user: User,
        request: TherapistMatchRequest,
        max_matches: int = 3
    ) -> List[TherapistMatch]:
        """
        Find the best therapist matches for a user based on their trauma map and preferences.
        """
        try:
            # Get user's trauma analysis
            trauma_analysis = await self._analyze_user_trauma(db, user.id)
            
            # Get available therapists
            available_therapists = self._get_available_therapists(db, request)
            
            # Score and rank therapists
            scored_matches = []
            for therapist in available_therapists:
                compatibility_score = self._calculate_compatibility_score(
                    therapist, request, trauma_analysis
                )
                
                if compatibility_score > 0.3:  # Minimum threshold
                    match_data = self._create_match_data(
                        therapist, request, trauma_analysis, compatibility_score
                    )
                    scored_matches.append(match_data)
            
            # Sort by compatibility score and take top matches
            scored_matches.sort(key=lambda x: x["compatibility_score"], reverse=True)
            top_matches = scored_matches[:max_matches]
            
            # Create and save match records
            matches = []
            for match_data in top_matches:
                match = TherapistMatch(
                    user_id=user.id,
                    therapist_id=match_data["therapist_id"],
                    compatibility_score=match_data["compatibility_score"],
                    match_reasons=match_data["match_reasons"],
                    preferred_modalities=request.preferred_modalities,
                    trauma_categories=request.trauma_categories,
                    healing_stage=request.healing_stage,
                    therapist_specialties_match=match_data["therapist_specialties_match"],
                    experience_relevance=match_data["experience_relevance"]
                )
                db.add(match)
                matches.append(match)
            
            db.commit()
            
            # Refresh to get relationships
            for match in matches:
                db.refresh(match)
            
            logger.info(f"Found {len(matches)} therapist matches for user {user.id}")
            return matches
            
        except Exception as e:
            logger.error(f"Error finding therapist matches: {e}")
            db.rollback()
            raise

    async def _analyze_user_trauma(self, db: Session, user_id: int) -> Dict[str, Any]:
        """Analyze user's trauma patterns from their trauma mapping."""
        trauma_mappings = db.query(TraumaMapping).filter(
            TraumaMapping.user_id == user_id
        ).all()
        
        if not trauma_mappings:
            return {
                "trauma_categories": [],
                "severity_levels": [],
                "healing_stages": [],
                "dominant_patterns": []
            }
        
        # Aggregate trauma data
        trauma_categories = []
        severity_levels = []
        healing_stages = []
        
        for mapping in trauma_mappings:
            trauma_categories.extend(mapping.trauma_indicators)
            severity_levels.append(mapping.severity_score)
            healing_stages.append(mapping.healing_stage)
        
        # Find dominant patterns
        category_counts = {}
        for category in trauma_categories:
            category_counts[category] = category_counts.get(category, 0) + 1
        
        dominant_patterns = sorted(
            category_counts.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:3]
        
        return {
            "trauma_categories": list(set(trauma_categories)),
            "severity_levels": severity_levels,
            "healing_stages": healing_stages,
            "dominant_patterns": [pattern[0] for pattern in dominant_patterns],
            "average_severity": sum(severity_levels) / len(severity_levels) if severity_levels else 0,
            "most_common_stage": max(set(healing_stages), key=healing_stages.count) if healing_stages else "acceptance"
        }

    def _get_available_therapists(
        self, 
        db: Session, 
        request: TherapistMatchRequest
    ) -> List[TherapistProfile]:
        """Get available therapists based on basic filters."""
        query = db.query(TherapistProfile).filter(
            and_(
                TherapistProfile.is_active == True,
                TherapistProfile.is_verified == True,
                TherapistProfile.is_accepting_new_clients == True
            )
        )
        
        # Apply filters
        if request.max_hourly_rate:
            query = query.filter(TherapistProfile.hourly_rate <= request.max_hourly_rate)
        
        if request.insurance_required:
            query = query.filter(TherapistProfile.accepts_insurance == True)
        
        return query.all()

    def _calculate_compatibility_score(
        self,
        therapist: TherapistProfile,
        request: TherapistMatchRequest,
        trauma_analysis: Dict[str, Any]
    ) -> float:
        """Calculate compatibility score between therapist and user needs."""
        score = 0.0
        
        # Modality match (40% weight)
        modality_score = self._score_modality_match(
            therapist.specialties, request.preferred_modalities
        )
        score += modality_score * 0.4
        
        # Trauma specialization (30% weight)
        trauma_score = self._score_trauma_specialization(
            therapist.specialties, trauma_analysis["trauma_categories"]
        )
        score += trauma_score * 0.3
        
        # Healing stage compatibility (20% weight)
        stage_score = self._score_healing_stage_compatibility(
            therapist.specialties, request.healing_stage
        )
        score += stage_score * 0.2
        
        # Experience and ratings (10% weight)
        experience_score = min(therapist.years_experience / 10.0, 1.0)
        rating_score = therapist.average_rating / 5.0 if therapist.average_rating > 0 else 0.5
        score += (experience_score * 0.5 + rating_score * 0.5) * 0.1
        
        return min(score, 1.0)

    def _score_modality_match(
        self, 
        therapist_specialties: List[str], 
        preferred_modalities: List[TherapyModality]
    ) -> float:
        """Score how well therapist specialties match preferred modalities."""
        if not preferred_modalities:
            return 0.5
        
        matches = 0
        for modality in preferred_modalities:
            if modality.value in therapist_specialties:
                matches += 1
        
        return matches / len(preferred_modalities)

    def _score_trauma_specialization(
        self, 
        therapist_specialties: List[str], 
        trauma_categories: List[str]
    ) -> float:
        """Score therapist's specialization in user's trauma categories."""
        if not trauma_categories:
            return 0.5
        
        trauma_relevant_modalities = []
        for category in trauma_categories:
            if category.lower() in self.modality_compatibility:
                trauma_relevant_modalities.extend(
                    self.modality_compatibility[category.lower()]
                )
        
        if not trauma_relevant_modalities:
            return 0.5
        
        matches = 0
        for modality in trauma_relevant_modalities:
            if modality.value in therapist_specialties:
                matches += 1
        
        return min(matches / len(set(trauma_relevant_modalities)), 1.0)

    def _score_healing_stage_compatibility(
        self, 
        therapist_specialties: List[str], 
        healing_stage: str
    ) -> float:
        """Score compatibility with user's current healing stage."""
        if healing_stage not in self.healing_stage_modalities:
            return 0.5
        
        stage_modalities = self.healing_stage_modalities[healing_stage]
        matches = 0
        
        for modality in stage_modalities:
            if modality.value in therapist_specialties:
                matches += 1
        
        return matches / len(stage_modalities) if stage_modalities else 0.5

    def _create_match_data(
        self,
        therapist: TherapistProfile,
        request: TherapistMatchRequest,
        trauma_analysis: Dict[str, Any],
        compatibility_score: float
    ) -> Dict[str, Any]:
        """Create match data structure."""
        # Generate match reasons
        match_reasons = []
        
        # Check modality matches
        modality_matches = [
            modality.value for modality in request.preferred_modalities
            if modality.value in therapist.specialties
        ]
        if modality_matches:
            match_reasons.append(f"Specializes in your preferred approaches: {', '.join(modality_matches)}")
        
        # Check trauma specialization
        trauma_specialties = []
        for category in trauma_analysis["trauma_categories"]:
            if category.lower() in self.modality_compatibility:
                relevant_modalities = self.modality_compatibility[category.lower()]
                for modality in relevant_modalities:
                    if modality.value in therapist.specialties:
                        trauma_specialties.append(modality.value)
        
        if trauma_specialties:
            match_reasons.append(f"Experienced in trauma-informed approaches: {', '.join(set(trauma_specialties))}")
        
        # Check experience
        if therapist.years_experience >= 5:
            match_reasons.append(f"{therapist.years_experience} years of experience")
        
        # Check ratings
        if therapist.average_rating >= 4.0:
            match_reasons.append(f"Highly rated ({therapist.average_rating:.1f}/5.0)")
        
        return {
            "therapist_id": therapist.id,
            "compatibility_score": compatibility_score,
            "match_reasons": match_reasons,
            "therapist_specialties_match": modality_matches,
            "experience_relevance": min(therapist.years_experience / 10.0, 1.0)
        }
