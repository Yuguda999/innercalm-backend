"""
Practice Plan Service for generating personalized homework and accountability tracking.
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from models.user import User
from models.professional_bridge import Appointment, PracticePlan, PracticePlanStatus
from models.trauma_mapping import TraumaMapping
from schemas.professional_bridge import PracticePlanCreate

logger = logging.getLogger(__name__)


class PracticePlanService:
    """
    Service for generating and managing personalized practice plans after therapy sessions.
    """

    def __init__(self):
        # Therapeutic exercise templates
        self.exercise_templates = {
            "cognitive_behavioral_therapy": {
                "thought_record": {
                    "name": "Daily Thought Record",
                    "description": "Track and challenge negative thought patterns",
                    "frequency": "daily",
                    "duration_minutes": 10,
                    "instructions": [
                        "Identify the triggering situation",
                        "Notice your automatic thoughts",
                        "Rate the intensity of emotions (1-10)",
                        "Challenge the thought with evidence",
                        "Create a balanced alternative thought"
                    ]
                },
                "behavioral_activation": {
                    "name": "Pleasant Activity Scheduling",
                    "description": "Schedule and engage in mood-boosting activities",
                    "frequency": "daily",
                    "duration_minutes": 30,
                    "instructions": [
                        "Choose one pleasant activity for today",
                        "Schedule a specific time",
                        "Rate your mood before and after",
                        "Note any obstacles and how you overcame them"
                    ]
                }
            },
            "mindfulness_based": {
                "breathing_exercise": {
                    "name": "Mindful Breathing",
                    "description": "Practice focused breathing for emotional regulation",
                    "frequency": "twice_daily",
                    "duration_minutes": 10,
                    "instructions": [
                        "Find a quiet, comfortable position",
                        "Focus on your natural breath",
                        "Count breaths from 1 to 10, then repeat",
                        "When mind wanders, gently return to breath",
                        "End with gratitude for this moment"
                    ]
                },
                "body_scan": {
                    "name": "Progressive Body Scan",
                    "description": "Develop body awareness and release tension",
                    "frequency": "daily",
                    "duration_minutes": 15,
                    "instructions": [
                        "Lie down comfortably",
                        "Start with toes, notice sensations",
                        "Slowly move attention up through body",
                        "Breathe into areas of tension",
                        "End with whole-body awareness"
                    ]
                }
            },
            "trauma_informed": {
                "grounding_technique": {
                    "name": "5-4-3-2-1 Grounding",
                    "description": "Use senses to stay present during distress",
                    "frequency": "as_needed",
                    "duration_minutes": 5,
                    "instructions": [
                        "Name 5 things you can see",
                        "Name 4 things you can touch",
                        "Name 3 things you can hear",
                        "Name 2 things you can smell",
                        "Name 1 thing you can taste"
                    ]
                },
                "safe_place_visualization": {
                    "name": "Safe Place Visualization",
                    "description": "Create and access internal sense of safety",
                    "frequency": "daily",
                    "duration_minutes": 10,
                    "instructions": [
                        "Close eyes and breathe deeply",
                        "Imagine your ideal safe place",
                        "Engage all senses in the visualization",
                        "Notice feelings of safety and calm",
                        "Create a cue word to access this feeling"
                    ]
                }
            }
        }

        # Micro-task templates
        self.micro_tasks = {
            "morning": [
                "Set one positive intention for the day",
                "Practice 3 minutes of deep breathing",
                "Write down one thing you're grateful for",
                "Do gentle stretching or movement"
            ],
            "midday": [
                "Take a mindful lunch break",
                "Check in with your emotions",
                "Practice a grounding technique",
                "Connect with a supportive person"
            ],
            "evening": [
                "Reflect on the day's positive moments",
                "Practice relaxation technique",
                "Prepare for restful sleep",
                "Journal about your progress"
            ]
        }

    async def generate_practice_plan(
        self,
        db: Session,
        appointment: Appointment,
        session_notes: Optional[str] = None,
        custom_goals: Optional[List[str]] = None
    ) -> PracticePlan:
        """
        Generate a personalized practice plan based on therapy session and user's needs.
        """
        try:
            # Get user's trauma analysis and preferences
            user_analysis = await self._analyze_user_needs(db, appointment.user_id)
            
            # Get therapist's specialties
            therapist_specialties = appointment.therapist.specialties
            
            # Generate plan components
            goals = custom_goals or self._generate_goals(user_analysis, therapist_specialties)
            daily_tasks = self._generate_daily_tasks(user_analysis, therapist_specialties)
            weekly_goals = self._generate_weekly_goals(user_analysis)
            exercises = self._generate_exercises(therapist_specialties, user_analysis)
            
            # Create practice plan
            plan_data = PracticePlanCreate(
                appointment_id=appointment.id,
                title=f"Practice Plan - Week of {datetime.now().strftime('%B %d, %Y')}",
                description=f"Personalized homework following your session with {appointment.therapist.full_name}",
                goals=goals,
                daily_tasks=daily_tasks,
                weekly_goals=weekly_goals,
                exercises=exercises,
                start_date=datetime.now(),
                end_date=datetime.now() + timedelta(days=7),
                reminder_frequency="daily"
            )
            
            practice_plan = PracticePlan(
                user_id=appointment.user_id,
                appointment_id=appointment.id,
                title=plan_data.title,
                description=plan_data.description,
                goals=plan_data.goals,
                daily_tasks=plan_data.daily_tasks,
                weekly_goals=plan_data.weekly_goals,
                exercises=plan_data.exercises,
                start_date=plan_data.start_date,
                end_date=plan_data.end_date,
                reminder_frequency=plan_data.reminder_frequency,
                status=PracticePlanStatus.ACTIVE
            )
            
            db.add(practice_plan)
            db.commit()
            db.refresh(practice_plan)
            
            logger.info(f"Generated practice plan {practice_plan.id} for user {appointment.user_id}")
            return practice_plan
            
        except Exception as e:
            logger.error(f"Error generating practice plan: {e}")
            db.rollback()
            raise

    async def _analyze_user_needs(self, db: Session, user_id: int) -> Dict[str, Any]:
        """Analyze user's current needs and progress."""
        # Get recent trauma mappings
        recent_mappings = db.query(TraumaMapping).filter(
            TraumaMapping.user_id == user_id
        ).order_by(TraumaMapping.analyzed_at.desc()).limit(5).all()
        
        # Get recent practice plans for progress tracking
        recent_plans = db.query(PracticePlan).filter(
            PracticePlan.user_id == user_id
        ).order_by(PracticePlan.created_at.desc()).limit(3).all()
        
        analysis = {
            "primary_concerns": [],
            "healing_stage": "acceptance",
            "severity_level": 5.0,
            "progress_trends": [],
            "preferred_activities": [],
            "completion_patterns": {}
        }
        
        if recent_mappings:
            # Analyze trauma patterns
            concerns = []
            stages = []
            severities = []
            
            for mapping in recent_mappings:
                concerns.extend(mapping.trauma_indicators)
                stages.append(mapping.healing_stage)
                severities.append(mapping.severity_score)
            
            analysis["primary_concerns"] = list(set(concerns))[:3]
            analysis["healing_stage"] = max(set(stages), key=stages.count) if stages else "acceptance"
            analysis["severity_level"] = sum(severities) / len(severities) if severities else 5.0
        
        if recent_plans:
            # Analyze completion patterns
            total_completion = sum(plan.completion_percentage for plan in recent_plans)
            analysis["average_completion"] = total_completion / len(recent_plans)
            
            # Find preferred task types
            task_preferences = {}
            for plan in recent_plans:
                for task in plan.completed_tasks:
                    task_type = task.split("_")[0] if "_" in task else task
                    task_preferences[task_type] = task_preferences.get(task_type, 0) + 1
            
            analysis["preferred_activities"] = sorted(
                task_preferences.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:3]
        
        return analysis

    def _generate_goals(
        self, 
        user_analysis: Dict[str, Any], 
        therapist_specialties: List[str]
    ) -> List[str]:
        """Generate personalized goals based on user needs and therapy approach."""
        goals = []
        
        # Base goals based on healing stage
        stage_goals = {
            "denial": [
                "Increase awareness of emotional patterns",
                "Practice gentle self-observation",
                "Build foundation of self-compassion"
            ],
            "anger": [
                "Develop healthy emotional expression",
                "Practice anger management techniques",
                "Build distress tolerance skills"
            ],
            "bargaining": [
                "Challenge unhelpful thought patterns",
                "Practice acceptance of difficult emotions",
                "Develop realistic expectations"
            ],
            "depression": [
                "Increase daily pleasant activities",
                "Challenge negative self-talk",
                "Build social connection and support"
            ],
            "acceptance": [
                "Integrate healing insights into daily life",
                "Maintain emotional regulation skills",
                "Continue personal growth journey"
            ]
        }
        
        healing_stage = user_analysis.get("healing_stage", "acceptance")
        goals.extend(stage_goals.get(healing_stage, stage_goals["acceptance"]))
        
        # Add therapy-specific goals
        if "cognitive_behavioral_therapy" in therapist_specialties:
            goals.append("Practice identifying and challenging automatic thoughts")
        
        if "mindfulness_based" in therapist_specialties:
            goals.append("Develop consistent mindfulness practice")
        
        if "trauma_informed" in therapist_specialties:
            goals.append("Strengthen sense of safety and grounding")
        
        return goals[:4]  # Limit to 4 goals

    def _generate_daily_tasks(
        self, 
        user_analysis: Dict[str, Any], 
        therapist_specialties: List[str]
    ) -> List[Dict[str, Any]]:
        """Generate daily micro-tasks."""
        tasks = []
        
        # Morning tasks
        morning_tasks = self.micro_tasks["morning"].copy()
        tasks.append({
            "id": "morning_routine",
            "time_of_day": "morning",
            "name": "Morning Mindfulness",
            "description": "Start your day with intention",
            "options": morning_tasks,
            "required": True,
            "estimated_minutes": 5
        })
        
        # Therapy-specific tasks
        if "cognitive_behavioral_therapy" in therapist_specialties:
            tasks.append({
                "id": "thought_check",
                "time_of_day": "midday",
                "name": "Thought Check-In",
                "description": "Notice and evaluate your thoughts",
                "options": [
                    "Identify one automatic thought",
                    "Rate the thought's helpfulness (1-10)",
                    "Consider alternative perspectives"
                ],
                "required": True,
                "estimated_minutes": 5
            })
        
        if "mindfulness_based" in therapist_specialties:
            tasks.append({
                "id": "mindful_moment",
                "time_of_day": "midday",
                "name": "Mindful Moment",
                "description": "Practice present-moment awareness",
                "options": [
                    "Take 5 mindful breaths",
                    "Notice your surroundings mindfully",
                    "Practice mindful eating"
                ],
                "required": True,
                "estimated_minutes": 3
            })
        
        # Evening reflection
        tasks.append({
            "id": "evening_reflection",
            "time_of_day": "evening",
            "name": "Daily Reflection",
            "description": "Reflect on your day and progress",
            "options": self.micro_tasks["evening"],
            "required": True,
            "estimated_minutes": 10
        })
        
        return tasks

    def _generate_weekly_goals(self, user_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate weekly objectives."""
        weekly_goals = [
            {
                "id": "consistency_goal",
                "name": "Practice Consistency",
                "description": "Complete daily tasks at least 5 out of 7 days",
                "target_metric": "completion_rate",
                "target_value": 0.7,
                "reward": "Celebrate your commitment to healing"
            },
            {
                "id": "skill_practice",
                "name": "Skill Development",
                "description": "Practice your main therapeutic technique daily",
                "target_metric": "skill_usage",
                "target_value": 7,
                "reward": "Notice improvements in emotional regulation"
            },
            {
                "id": "self_compassion",
                "name": "Self-Compassion Practice",
                "description": "Practice self-kindness when facing difficulties",
                "target_metric": "self_compassion_moments",
                "target_value": 3,
                "reward": "Acknowledge your growing self-acceptance"
            }
        ]
        
        return weekly_goals

    def _generate_exercises(
        self, 
        therapist_specialties: List[str], 
        user_analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate specific therapeutic exercises."""
        exercises = []
        
        # Add exercises based on therapist specialties
        for specialty in therapist_specialties:
            if specialty in self.exercise_templates:
                specialty_exercises = self.exercise_templates[specialty]
                for exercise_key, exercise_data in specialty_exercises.items():
                    exercises.append({
                        "id": f"{specialty}_{exercise_key}",
                        "category": specialty,
                        **exercise_data
                    })
        
        # Limit to 3-4 exercises to avoid overwhelming
        return exercises[:4]
