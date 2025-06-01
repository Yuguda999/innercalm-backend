"""
AI-powered group management service for automatically creating and managing Shared Wound Groups.
"""
import logging
import hashlib
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func, or_

import numpy as np
from sklearn.cluster import DBSCAN, KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score

from models.user import User
from models.emotion import EmotionAnalysis
from models.community import (
    SharedWoundGroup, PeerCircle, CircleMembership, UserClusterProfile
)
from services.clustering_service import ClusteringService

logger = logging.getLogger(__name__)


class AIGroupManager:
    """AI-powered service for automatically creating and managing Shared Wound Groups."""

    def __init__(self):
        self.clustering_service = ClusteringService()
        self.min_group_size = 5  # Minimum users needed to form a group
        self.max_group_size = 50  # Maximum users per group before splitting
        self.review_interval_days = 7  # How often AI reviews groups
        self.confidence_threshold = 0.6  # Minimum confidence for group creation
        self.cohesion_threshold = 0.4  # Minimum cohesion to keep group active

    async def run_ai_group_management(self, db: Session) -> Dict[str, Any]:
        """Main AI group management routine - run this periodically."""
        try:
            logger.info("Starting AI group management cycle")

            results = {
                "groups_created": 0,
                "groups_updated": 0,
                "groups_merged": 0,
                "groups_split": 0,
                "groups_archived": 0,
                "users_reassigned": 0,
                "timestamp": datetime.utcnow().isoformat()
            }

            # Step 1: Update all user cluster profiles
            await self._update_all_user_profiles(db)

            # Step 2: Discover new groups from unassigned users
            new_groups = await self._discover_new_groups(db)
            results["groups_created"] = len(new_groups)

            # Step 3: Review and optimize existing groups
            optimization_results = await self._optimize_existing_groups(db)
            results.update(optimization_results)

            # Step 4: Auto-create peer circles for active groups
            await self._auto_create_peer_circles(db)

            # Step 5: Schedule next review for all groups
            await self._schedule_next_reviews(db)

            logger.info(f"AI group management completed: {results}")
            return results

        except Exception as e:
            logger.error(f"Error in AI group management: {e}")
            raise

    async def _update_all_user_profiles(self, db: Session):
        """Update cluster profiles for all users with recent activity."""
        try:
            # Get users with recent emotion analyses (last 30 days)
            recent_cutoff = datetime.utcnow() - timedelta(days=30)

            active_users = db.query(User.id).join(EmotionAnalysis).filter(
                EmotionAnalysis.created_at >= recent_cutoff
            ).distinct().all()

            for user_id_tuple in active_users:
                user_id = user_id_tuple[0]
                try:
                    await self.clustering_service.update_user_cluster_profile(
                        db, user_id, force_recluster=False
                    )
                except Exception as e:
                    logger.warning(f"Failed to update profile for user {user_id}: {e}")

        except Exception as e:
            logger.error(f"Error updating user profiles: {e}")

    async def _discover_new_groups(self, db: Session) -> List[SharedWoundGroup]:
        """Discover and create new groups from unassigned users."""
        try:
            # Get users without active group membership
            unassigned_users = await self._get_unassigned_users(db)

            if len(unassigned_users) < self.min_group_size:
                logger.info(f"Not enough unassigned users for new groups: {len(unassigned_users)}")
                return []

            # Perform clustering on unassigned users
            clusters = await self._cluster_users(db, unassigned_users)

            new_groups = []
            for cluster_id, user_profiles in clusters.items():
                if len(user_profiles) >= self.min_group_size:
                    group = await self._create_group_from_cluster(db, cluster_id, user_profiles)
                    if group:
                        new_groups.append(group)

            return new_groups

        except Exception as e:
            logger.error(f"Error discovering new groups: {e}")
            return []

    async def _get_unassigned_users(self, db: Session) -> List[UserClusterProfile]:
        """Get users who aren't in any active shared wound group."""
        try:
            # Get users with cluster profiles but no active group membership
            subquery = db.query(CircleMembership.user_id).join(PeerCircle).join(SharedWoundGroup).filter(
                and_(
                    CircleMembership.status == "active",
                    SharedWoundGroup.is_active == True
                )
            ).distinct().subquery()

            unassigned = db.query(UserClusterProfile).filter(
                and_(
                    UserClusterProfile.cluster_vector.isnot(None),
                    ~UserClusterProfile.user_id.in_(subquery)
                )
            ).all()

            return unassigned

        except Exception as e:
            logger.error(f"Error getting unassigned users: {e}")
            return []

    async def _cluster_users(self, db: Session, user_profiles: List[UserClusterProfile]) -> Dict[str, List[UserClusterProfile]]:
        """Cluster users into potential groups using advanced algorithms."""
        try:
            if len(user_profiles) < self.min_group_size:
                return {}

            # Prepare feature matrix
            vectors = np.array([profile.cluster_vector for profile in user_profiles])

            # Standardize features
            scaler = StandardScaler()
            scaled_vectors = scaler.fit_transform(vectors)

            # Use DBSCAN for density-based clustering (better for varying group sizes)
            eps = self._calculate_optimal_eps(scaled_vectors)
            min_samples = max(3, len(user_profiles) // 10)

            clustering = DBSCAN(eps=eps, min_samples=min_samples, metric='euclidean')
            cluster_labels = clustering.fit_predict(scaled_vectors)

            # Group users by cluster
            clusters = {}
            for i, label in enumerate(cluster_labels):
                if label != -1:  # Ignore noise points
                    cluster_key = f"cluster_{label}"
                    if cluster_key not in clusters:
                        clusters[cluster_key] = []
                    clusters[cluster_key].append(user_profiles[i])

            # Filter clusters by minimum size
            valid_clusters = {k: v for k, v in clusters.items() if len(v) >= self.min_group_size}

            logger.info(f"Created {len(valid_clusters)} valid clusters from {len(user_profiles)} users")
            return valid_clusters

        except Exception as e:
            logger.error(f"Error clustering users: {e}")
            return {}

    def _calculate_optimal_eps(self, vectors: np.ndarray) -> float:
        """Calculate optimal eps parameter for DBSCAN using k-distance graph."""
        try:
            from sklearn.neighbors import NearestNeighbors

            k = min(4, len(vectors) - 1)
            neighbors = NearestNeighbors(n_neighbors=k)
            neighbors_fit = neighbors.fit(vectors)
            distances, indices = neighbors_fit.kneighbors(vectors)

            # Sort distances and find the "elbow"
            distances = np.sort(distances[:, k-1], axis=0)

            # Use 75th percentile as a reasonable eps value
            eps = np.percentile(distances, 75)
            return max(eps, 0.1)  # Ensure minimum eps

        except Exception as e:
            logger.warning(f"Error calculating optimal eps: {e}")
            return 0.5  # Default value

    async def _create_group_from_cluster(
        self,
        db: Session,
        cluster_id: str,
        user_profiles: List[UserClusterProfile]
    ) -> Optional[SharedWoundGroup]:
        """Create a new shared wound group from a cluster of users."""
        try:
            # Calculate group characteristics
            group_emotions = self._calculate_group_emotions(user_profiles)
            group_themes = self._calculate_group_themes(user_profiles)
            group_stage = self._calculate_group_healing_stage(user_profiles)

            # Generate group name and description
            group_name = self._generate_group_name(group_themes, group_stage)
            group_description = self._generate_group_description(group_emotions, group_themes, group_stage)

            # Calculate confidence score
            confidence = self._calculate_group_confidence(user_profiles)

            if confidence < self.confidence_threshold:
                logger.info(f"Skipping group creation due to low confidence: {confidence}")
                return None

            # Create unique cluster identifier
            cluster_hash = self._generate_cluster_hash(group_emotions, group_themes, group_stage)

            # Create the group
            group = SharedWoundGroup(
                name=group_name,
                description=group_description,
                cluster_id=cluster_hash,
                ai_generated=True,
                confidence_score=confidence,
                emotional_pattern=group_emotions,
                trauma_themes=group_themes,
                healing_stage=group_stage,
                member_count=len(user_profiles),
                activity_score=0.0,
                cohesion_score=confidence,
                growth_potential=self._calculate_growth_potential(user_profiles),
                max_members=self.max_group_size,
                is_active=True,
                requires_approval=False,
                last_ai_review=datetime.utcnow(),
                next_ai_review=datetime.utcnow() + timedelta(days=self.review_interval_days)
            )

            db.add(group)
            db.commit()
            db.refresh(group)

            logger.info(f"Created new AI group: {group_name} with {len(user_profiles)} members")
            return group

        except Exception as e:
            logger.error(f"Error creating group from cluster: {e}")
            db.rollback()
            return None

    def _calculate_group_emotions(self, user_profiles: List[UserClusterProfile]) -> Dict[str, float]:
        """Calculate dominant emotions for a group."""
        try:
            emotion_sums = {}
            total_users = len(user_profiles)

            for profile in user_profiles:
                for emotion, intensity in profile.dominant_emotions.items():
                    if emotion not in emotion_sums:
                        emotion_sums[emotion] = 0
                    emotion_sums[emotion] += intensity

            # Calculate averages and normalize
            group_emotions = {}
            for emotion, total in emotion_sums.items():
                group_emotions[emotion] = total / total_users

            # Sort by intensity and keep top 5
            sorted_emotions = sorted(group_emotions.items(), key=lambda x: x[1], reverse=True)
            return dict(sorted_emotions[:5])

        except Exception as e:
            logger.error(f"Error calculating group emotions: {e}")
            return {"anxiety": 0.5, "sadness": 0.3}  # Default fallback

    def _calculate_group_themes(self, user_profiles: List[UserClusterProfile]) -> List[str]:
        """Calculate common trauma themes for a group."""
        try:
            theme_counts = {}

            for profile in user_profiles:
                if profile.trauma_themes:
                    for theme in profile.trauma_themes:
                        theme_counts[theme] = theme_counts.get(theme, 0) + 1

            # Sort by frequency and return top themes
            sorted_themes = sorted(theme_counts.items(), key=lambda x: x[1], reverse=True)

            # Include themes that appear in at least 30% of users
            min_frequency = max(1, len(user_profiles) * 0.3)
            common_themes = [theme for theme, count in sorted_themes if count >= min_frequency]

            return common_themes[:5]  # Limit to top 5 themes

        except Exception as e:
            logger.error(f"Error calculating group themes: {e}")
            return ["emotional_healing", "support"]  # Default fallback

    def _calculate_group_healing_stage(self, user_profiles: List[UserClusterProfile]) -> str:
        """Determine the dominant healing stage for a group."""
        try:
            stage_counts = {}

            for profile in user_profiles:
                if profile.healing_stage:
                    stage = profile.healing_stage
                    stage_counts[stage] = stage_counts.get(stage, 0) + 1

            if not stage_counts:
                return "processing"  # Default stage

            # Return the most common stage
            dominant_stage = max(stage_counts.items(), key=lambda x: x[1])[0]
            return dominant_stage

        except Exception as e:
            logger.error(f"Error calculating group healing stage: {e}")
            return "processing"  # Default fallback

    def _calculate_group_confidence(self, user_profiles: List[UserClusterProfile]) -> float:
        """Calculate confidence score for group coherence."""
        try:
            if len(user_profiles) < 2:
                return 0.0

            # Calculate similarity between all pairs of users
            similarities = []
            vectors = [profile.cluster_vector for profile in user_profiles]

            for i in range(len(vectors)):
                for j in range(i + 1, len(vectors)):
                    similarity = self._calculate_vector_similarity(vectors[i], vectors[j])
                    similarities.append(similarity)

            # Average similarity is our confidence score
            confidence = np.mean(similarities) if similarities else 0.0

            # Boost confidence for larger groups (up to a point)
            size_bonus = min(0.1, len(user_profiles) * 0.02)
            confidence += size_bonus

            return min(1.0, confidence)

        except Exception as e:
            logger.error(f"Error calculating group confidence: {e}")
            return 0.5  # Default confidence

    def _calculate_vector_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        try:
            v1 = np.array(vec1)
            v2 = np.array(vec2)

            dot_product = np.dot(v1, v2)
            norm_v1 = np.linalg.norm(v1)
            norm_v2 = np.linalg.norm(v2)

            if norm_v1 == 0 or norm_v2 == 0:
                return 0.0

            similarity = dot_product / (norm_v1 * norm_v2)
            return max(0.0, similarity)  # Ensure non-negative

        except Exception as e:
            logger.error(f"Error calculating vector similarity: {e}")
            return 0.0

    def _calculate_growth_potential(self, user_profiles: List[UserClusterProfile]) -> float:
        """Calculate the potential for this group to help members heal."""
        try:
            # Factors that contribute to growth potential:
            # 1. Diversity in healing stages (different perspectives)
            # 2. Balanced emotional patterns (not all negative)
            # 3. Variety in coping patterns

            stages = [p.healing_stage for p in user_profiles if p.healing_stage]
            stage_diversity = len(set(stages)) / max(1, len(stages))

            # Calculate emotional balance (mix of positive and negative emotions)
            positive_emotions = ["joy", "hope", "gratitude", "love", "peace"]
            emotion_balance = 0.0

            for profile in user_profiles:
                positive_score = sum(profile.dominant_emotions.get(e, 0) for e in positive_emotions)
                total_score = sum(profile.dominant_emotions.values())
                if total_score > 0:
                    emotion_balance += positive_score / total_score

            emotion_balance /= len(user_profiles)

            # Combine factors
            growth_potential = (stage_diversity * 0.4 + emotion_balance * 0.6)
            return min(1.0, growth_potential)

        except Exception as e:
            logger.error(f"Error calculating growth potential: {e}")
            return 0.5  # Default potential

    def _generate_group_name(self, themes: List[str], healing_stage: str) -> str:
        """Generate a meaningful name for the group."""
        try:
            # Name templates based on themes and stages
            stage_prefixes = {
                "early": "Beginning",
                "processing": "Journey",
                "integration": "Healing",
                "growth": "Thriving"
            }

            theme_keywords = {
                "anxiety": "Calm",
                "depression": "Hope",
                "trauma": "Recovery",
                "grief": "Remembrance",
                "relationship": "Connection",
                "family": "Bonds",
                "work": "Balance",
                "self_esteem": "Worth",
                "anger": "Peace",
                "fear": "Courage"
            }

            prefix = stage_prefixes.get(healing_stage, "Healing")

            # Find the most relevant theme keyword
            keyword = "Hearts"  # Default
            for theme in themes:
                if theme in theme_keywords:
                    keyword = theme_keywords[theme]
                    break

            # Generate name variations
            name_templates = [
                f"{prefix} {keyword} Circle",
                f"{keyword} & {prefix}",
                f"The {keyword} Journey",
                f"{prefix} Together",
                f"Circle of {keyword}"
            ]

            # Use hash to consistently pick the same name for similar groups
            theme_hash = hash(str(sorted(themes)) + healing_stage) % len(name_templates)
            return name_templates[theme_hash]

        except Exception as e:
            logger.error(f"Error generating group name: {e}")
            return "Healing Circle"

    def _generate_group_description(self, emotions: Dict[str, float], themes: List[str], stage: str) -> str:
        """Generate a description for the group."""
        try:
            stage_descriptions = {
                "early": "beginning their healing journey",
                "processing": "actively working through their experiences",
                "integration": "integrating their healing insights",
                "growth": "focused on continued growth and helping others"
            }

            stage_desc = stage_descriptions.get(stage, "on their healing path")

            if themes:
                theme_text = ", ".join(themes[:3])
                description = f"A supportive community for those {stage_desc} and dealing with {theme_text}. "
            else:
                description = f"A supportive community for those {stage_desc}. "

            description += "This group was intelligently formed based on shared emotional patterns and experiences to provide the most relevant peer support."

            return description

        except Exception as e:
            logger.error(f"Error generating group description: {e}")
            return "A supportive community for healing and growth."

    def _generate_cluster_hash(self, emotions: Dict[str, float], themes: List[str], stage: str) -> str:
        """Generate a unique hash for the cluster characteristics."""
        try:
            # Create a consistent string representation
            emotion_str = json.dumps(emotions, sort_keys=True)
            theme_str = json.dumps(sorted(themes))
            cluster_data = f"{emotion_str}_{theme_str}_{stage}"

            # Generate hash
            return hashlib.md5(cluster_data.encode()).hexdigest()[:16]

        except Exception as e:
            logger.error(f"Error generating cluster hash: {e}")
            return hashlib.md5(str(datetime.utcnow()).encode()).hexdigest()[:16]

    async def _optimize_existing_groups(self, db: Session) -> Dict[str, int]:
        """Review and optimize existing AI-managed groups."""
        try:
            results = {
                "groups_updated": 0,
                "groups_merged": 0,
                "groups_split": 0,
                "groups_archived": 0,
                "users_reassigned": 0
            }

            # Get groups that need review
            review_cutoff = datetime.utcnow()
            groups_to_review = db.query(SharedWoundGroup).filter(
                and_(
                    SharedWoundGroup.ai_generated == True,
                    SharedWoundGroup.is_active == True,
                    or_(
                        SharedWoundGroup.next_ai_review <= review_cutoff,
                        SharedWoundGroup.next_ai_review.is_(None)
                    )
                )
            ).all()

            for group in groups_to_review:
                try:
                    # Update group metrics
                    await self._update_group_metrics(db, group)

                    # Check if group needs optimization
                    if group.cohesion_score < self.cohesion_threshold:
                        if group.member_count < self.min_group_size:
                            # Archive small, low-cohesion groups
                            await self._archive_group(db, group)
                            results["groups_archived"] += 1
                        else:
                            # Try to improve cohesion by reassigning outlier members
                            reassigned = await self._reassign_outlier_members(db, group)
                            results["users_reassigned"] += reassigned

                    elif group.member_count > self.max_group_size:
                        # Split large groups
                        if await self._split_group(db, group):
                            results["groups_split"] += 1

                    # Update review schedule
                    group.last_ai_review = datetime.utcnow()
                    group.next_ai_review = datetime.utcnow() + timedelta(days=self.review_interval_days)
                    results["groups_updated"] += 1

                except Exception as e:
                    logger.error(f"Error optimizing group {group.id}: {e}")

            db.commit()
            return results

        except Exception as e:
            logger.error(f"Error optimizing existing groups: {e}")
            return {"groups_updated": 0, "groups_merged": 0, "groups_split": 0, "groups_archived": 0, "users_reassigned": 0}

    async def _update_group_metrics(self, db: Session, group: SharedWoundGroup):
        """Update activity and cohesion metrics for a group."""
        try:
            # Get group members
            members = db.query(CircleMembership).join(PeerCircle).filter(
                and_(
                    PeerCircle.shared_wound_group_id == group.id,
                    CircleMembership.status == "active"
                )
            ).all()

            group.member_count = len(members)

            if members:
                # Calculate activity score based on recent messages
                recent_cutoff = datetime.utcnow() - timedelta(days=7)
                total_messages = sum(m.message_count for m in members)
                recent_activity = len([m for m in members if m.last_seen_at and m.last_seen_at >= recent_cutoff])

                group.activity_score = min(1.0, (recent_activity / len(members)) * 0.7 + (total_messages / (len(members) * 10)) * 0.3)

                # Recalculate cohesion based on current member profiles
                user_profiles = []
                for member in members:
                    profile = db.query(UserClusterProfile).filter(
                        UserClusterProfile.user_id == member.user_id
                    ).first()
                    if profile:
                        user_profiles.append(profile)

                if user_profiles:
                    group.cohesion_score = self._calculate_group_confidence(user_profiles)
            else:
                group.activity_score = 0.0
                group.cohesion_score = 0.0

        except Exception as e:
            logger.error(f"Error updating group metrics for group {group.id}: {e}")

    async def _archive_group(self, db: Session, group: SharedWoundGroup):
        """Archive a group that's no longer viable."""
        try:
            group.is_active = False
            group.updated_at = datetime.utcnow()

            # Also deactivate associated peer circles
            circles = db.query(PeerCircle).filter(
                PeerCircle.shared_wound_group_id == group.id
            ).all()

            for circle in circles:
                circle.status = "closed"

            logger.info(f"Archived group {group.name} due to low cohesion/activity")

        except Exception as e:
            logger.error(f"Error archiving group {group.id}: {e}")

    async def _reassign_outlier_members(self, db: Session, group: SharedWoundGroup) -> int:
        """Reassign members who don't fit well in the current group."""
        try:
            # This is a placeholder for a more sophisticated outlier detection
            # In a full implementation, you'd identify members whose profiles
            # are significantly different from the group average
            return 0

        except Exception as e:
            logger.error(f"Error reassigning outlier members for group {group.id}: {e}")
            return 0

    async def _split_group(self, db: Session, group: SharedWoundGroup) -> bool:
        """Split a large group into smaller, more cohesive groups."""
        try:
            # Get all members of the group
            members = db.query(CircleMembership).join(PeerCircle).filter(
                and_(
                    PeerCircle.shared_wound_group_id == group.id,
                    CircleMembership.status == "active"
                )
            ).all()

            if len(members) <= self.max_group_size:
                return False

            # Get user profiles for clustering
            user_profiles = []
            for member in members:
                profile = db.query(UserClusterProfile).filter(
                    UserClusterProfile.user_id == member.user_id
                ).first()
                if profile:
                    user_profiles.append(profile)

            if len(user_profiles) < self.min_group_size * 2:
                return False

            # Cluster into 2 groups
            clusters = await self._cluster_users(db, user_profiles)

            if len(clusters) >= 2:
                # Create new groups from clusters
                cluster_items = list(clusters.items())
                for i, (cluster_id, cluster_profiles) in enumerate(cluster_items[:2]):
                    if i == 0:
                        # Update the original group with first cluster
                        await self._update_group_with_cluster(db, group, cluster_profiles)
                    else:
                        # Create new group with second cluster
                        await self._create_group_from_cluster(db, f"{cluster_id}_split", cluster_profiles)

                logger.info(f"Split group {group.name} into {len(clusters)} smaller groups")
                return True

            return False

        except Exception as e:
            logger.error(f"Error splitting group {group.id}: {e}")
            return False

    async def _update_group_with_cluster(self, db: Session, group: SharedWoundGroup, user_profiles: List[UserClusterProfile]):
        """Update an existing group with new cluster characteristics."""
        try:
            group.emotional_pattern = self._calculate_group_emotions(user_profiles)
            group.trauma_themes = self._calculate_group_themes(user_profiles)
            group.healing_stage = self._calculate_group_healing_stage(user_profiles)
            group.confidence_score = self._calculate_group_confidence(user_profiles)
            group.member_count = len(user_profiles)
            group.updated_at = datetime.utcnow()

        except Exception as e:
            logger.error(f"Error updating group with cluster: {e}")

    async def _auto_create_peer_circles(self, db: Session):
        """Automatically create peer circles for active groups that need them."""
        try:
            # Get active groups without enough peer circles
            active_groups = db.query(SharedWoundGroup).filter(
                and_(
                    SharedWoundGroup.is_active == True,
                    SharedWoundGroup.member_count >= self.min_group_size
                )
            ).all()

            for group in active_groups:
                # Count existing active circles
                circle_count = db.query(PeerCircle).filter(
                    and_(
                        PeerCircle.shared_wound_group_id == group.id,
                        PeerCircle.status == "active"
                    )
                ).count()

                # Calculate needed circles (aim for 6-8 members per circle)
                needed_circles = max(1, group.member_count // 7)

                if circle_count < needed_circles:
                    # Create additional circles
                    for i in range(needed_circles - circle_count):
                        circle_name = f"{group.name} - Circle {circle_count + i + 1}"

                        new_circle = PeerCircle(
                            shared_wound_group_id=group.id,
                            name=circle_name,
                            description=f"A peer support circle within {group.name}",
                            status="active",
                            max_members=8,
                            is_private=True,
                            requires_invitation=False,  # AI manages membership
                            facilitator_id=None,  # AI-managed
                            last_activity_at=datetime.utcnow(),
                            message_count=0
                        )

                        db.add(new_circle)

                    db.commit()
                    logger.info(f"Created {needed_circles - circle_count} new circles for group {group.name}")

        except Exception as e:
            logger.error(f"Error auto-creating peer circles: {e}")

    async def _schedule_next_reviews(self, db: Session):
        """Schedule next AI review for all active groups."""
        try:
            groups_without_schedule = db.query(SharedWoundGroup).filter(
                and_(
                    SharedWoundGroup.ai_generated == True,
                    SharedWoundGroup.is_active == True,
                    SharedWoundGroup.next_ai_review.is_(None)
                )
            ).all()

            for group in groups_without_schedule:
                group.next_ai_review = datetime.utcnow() + timedelta(days=self.review_interval_days)

            db.commit()

        except Exception as e:
            logger.error(f"Error scheduling next reviews: {e}")


# Global AI Group Manager instance
ai_group_manager = AIGroupManager()
