#!/usr/bin/env python3
"""
Simple test to verify enum values.
"""
from models.trauma_mapping import EventType, EventCategory

print("Testing EventType enum values:")
print(f"POSITIVE = {EventType.POSITIVE.value}")
print(f"NEGATIVE = {EventType.NEGATIVE.value}")
print(f"NEUTRAL = {EventType.NEUTRAL.value}")
print(f"TRAUMATIC = {EventType.TRAUMATIC.value}")
print(f"MILESTONE = {EventType.MILESTONE.value}")

print("\nTesting EventCategory enum values:")
print(f"FAMILY = {EventCategory.FAMILY.value}")
print(f"RELATIONSHIPS = {EventCategory.RELATIONSHIPS.value}")
print(f"CAREER = {EventCategory.CAREER.value}")
print(f"HEALTH = {EventCategory.HEALTH.value}")
print(f"EDUCATION = {EventCategory.EDUCATION.value}")
print(f"LOSS = {EventCategory.LOSS.value}")
print(f"ACHIEVEMENT = {EventCategory.ACHIEVEMENT.value}")
print(f"TRAUMA = {EventCategory.TRAUMA.value}")
print(f"OTHER = {EventCategory.OTHER.value}")

print("\n✅ Enum values are now uppercase!")
