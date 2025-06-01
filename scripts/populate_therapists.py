"""
Script to populate the database with sample therapist profiles.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from database import SessionLocal, engine
from models.professional_bridge import TherapistProfile, TherapyModality

def create_sample_therapists():
    """Create sample therapist profiles for testing."""
    db = SessionLocal()
    
    try:
        # Sample therapist data
        therapists_data = [
            {
                "full_name": "Dr. Sarah Chen",
                "email": "sarah.chen@therapycare.com",
                "phone": "+1-555-0101",
                "license_number": "LPC-12345",
                "credentials": ["Licensed Professional Counselor", "Certified EMDR Therapist", "Trauma Specialist"],
                "specialties": [
                    TherapyModality.EMDR.value,
                    TherapyModality.TRAUMA_INFORMED.value,
                    TherapyModality.CBT.value
                ],
                "years_experience": 8,
                "bio": "Dr. Chen specializes in trauma recovery and EMDR therapy. She has extensive experience helping clients process difficult life experiences and develop healthy coping strategies.",
                "hourly_rate": 150.0,
                "accepts_insurance": True,
                "insurance_providers": ["Blue Cross", "Aetna", "Cigna"],
                "availability_schedule": {
                    "monday": ["09:00-17:00"],
                    "tuesday": ["09:00-17:00"],
                    "wednesday": ["09:00-17:00"],
                    "thursday": ["09:00-17:00"],
                    "friday": ["09:00-15:00"]
                },
                "timezone": "America/New_York",
                "average_rating": 4.8,
                "total_reviews": 127,
                "is_verified": True,
                "is_active": True,
                "is_accepting_new_clients": True
            },
            {
                "full_name": "Dr. Michael Rodriguez",
                "email": "michael.rodriguez@mindfulhealing.com",
                "phone": "+1-555-0102",
                "license_number": "LMFT-67890",
                "credentials": ["Licensed Marriage and Family Therapist", "Mindfulness-Based Stress Reduction Certified"],
                "specialties": [
                    TherapyModality.MINDFULNESS_BASED.value,
                    TherapyModality.CBT.value,
                    TherapyModality.FAMILY_THERAPY.value
                ],
                "years_experience": 12,
                "bio": "Dr. Rodriguez integrates mindfulness practices with evidence-based therapy to help individuals and families find balance and healing.",
                "hourly_rate": 175.0,
                "accepts_insurance": True,
                "insurance_providers": ["Blue Cross", "United Healthcare", "Kaiser"],
                "availability_schedule": {
                    "monday": ["10:00-18:00"],
                    "tuesday": ["10:00-18:00"],
                    "wednesday": ["10:00-18:00"],
                    "thursday": ["10:00-18:00"],
                    "saturday": ["09:00-13:00"]
                },
                "timezone": "America/Los_Angeles",
                "average_rating": 4.9,
                "total_reviews": 203,
                "is_verified": True,
                "is_active": True,
                "is_accepting_new_clients": True
            },
            {
                "full_name": "Dr. Emily Thompson",
                "email": "emily.thompson@somatichealing.com",
                "phone": "+1-555-0103",
                "license_number": "LCSW-11111",
                "credentials": ["Licensed Clinical Social Worker", "Somatic Experiencing Practitioner", "Yoga Therapist"],
                "specialties": [
                    TherapyModality.SOMATIC.value,
                    TherapyModality.TRAUMA_INFORMED.value,
                    TherapyModality.MINDFULNESS_BASED.value
                ],
                "years_experience": 6,
                "bio": "Dr. Thompson specializes in somatic therapy and body-based healing approaches for trauma recovery and emotional regulation.",
                "hourly_rate": 140.0,
                "accepts_insurance": False,
                "insurance_providers": [],
                "availability_schedule": {
                    "tuesday": ["11:00-19:00"],
                    "wednesday": ["11:00-19:00"],
                    "thursday": ["11:00-19:00"],
                    "friday": ["11:00-19:00"],
                    "saturday": ["10:00-14:00"]
                },
                "timezone": "America/Denver",
                "average_rating": 4.7,
                "total_reviews": 89,
                "is_verified": True,
                "is_active": True,
                "is_accepting_new_clients": True
            },
            {
                "full_name": "Dr. James Wilson",
                "email": "james.wilson@cognitivetherapy.com",
                "phone": "+1-555-0104",
                "license_number": "PhD-22222",
                "credentials": ["Licensed Psychologist", "Cognitive Behavioral Therapy Specialist", "DBT Certified"],
                "specialties": [
                    TherapyModality.CBT.value,
                    TherapyModality.DBT.value,
                    TherapyModality.PSYCHODYNAMIC.value
                ],
                "years_experience": 15,
                "bio": "Dr. Wilson has extensive experience in cognitive behavioral therapy and dialectical behavior therapy, specializing in anxiety, depression, and emotional regulation.",
                "hourly_rate": 200.0,
                "accepts_insurance": True,
                "insurance_providers": ["Blue Cross", "Aetna", "United Healthcare", "Cigna"],
                "availability_schedule": {
                    "monday": ["08:00-16:00"],
                    "tuesday": ["08:00-16:00"],
                    "wednesday": ["08:00-16:00"],
                    "thursday": ["08:00-16:00"],
                    "friday": ["08:00-12:00"]
                },
                "timezone": "America/Chicago",
                "average_rating": 4.6,
                "total_reviews": 156,
                "is_verified": True,
                "is_active": True,
                "is_accepting_new_clients": True
            },
            {
                "full_name": "Dr. Lisa Park",
                "email": "lisa.park@humanistictherapy.com",
                "phone": "+1-555-0105",
                "license_number": "LPCC-33333",
                "credentials": ["Licensed Professional Clinical Counselor", "Humanistic Therapy Specialist", "Grief Counselor"],
                "specialties": [
                    TherapyModality.HUMANISTIC.value,
                    TherapyModality.PSYCHODYNAMIC.value,
                    TherapyModality.GROUP_THERAPY.value
                ],
                "years_experience": 10,
                "bio": "Dr. Park provides compassionate, person-centered therapy with a focus on grief, loss, and life transitions. She believes in the inherent wisdom and healing capacity of each individual.",
                "hourly_rate": 160.0,
                "accepts_insurance": True,
                "insurance_providers": ["Blue Cross", "Aetna"],
                "availability_schedule": {
                    "monday": ["12:00-20:00"],
                    "tuesday": ["12:00-20:00"],
                    "wednesday": ["12:00-20:00"],
                    "thursday": ["12:00-20:00"],
                    "friday": ["12:00-18:00"]
                },
                "timezone": "America/New_York",
                "average_rating": 4.9,
                "total_reviews": 94,
                "is_verified": True,
                "is_active": True,
                "is_accepting_new_clients": True
            }
        ]
        
        # Create therapist profiles
        for therapist_data in therapists_data:
            # Check if therapist already exists
            existing = db.query(TherapistProfile).filter(
                TherapistProfile.email == therapist_data["email"]
            ).first()
            
            if not existing:
                therapist = TherapistProfile(**therapist_data)
                db.add(therapist)
                print(f"Added therapist: {therapist_data['full_name']}")
            else:
                print(f"Therapist already exists: {therapist_data['full_name']}")
        
        db.commit()
        print(f"\nSuccessfully populated {len(therapists_data)} therapist profiles!")
        
    except Exception as e:
        print(f"Error populating therapists: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("Populating sample therapist profiles...")
    create_sample_therapists()
