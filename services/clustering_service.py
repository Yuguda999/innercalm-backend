"""
User clustering service for emotion-based peer group matching.
"""
import logging
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func
from sklearn.cluster import KMeans, DBSCAN, AgglomerativeClustering
from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
from sklearn.feature_extraction.text import TfidfVectorizer
from scipy.spatial.distance import pdist, squareform
from scipy.cluster.hierarchy import linkage, fcluster

from models.user import User
from models.emotion import EmotionAnalysis, EmotionPattern
from models.trauma_mapping import LifeEvent, TraumaMapping
from models.community import (
    UserClusterProfile, SharedWoundGroup, PeerCircle, CircleMembership,
    CircleStatus, MembershipStatus
)

logger = logging.getLogger(__name__)


class ClusteringService:
    """Service for clustering users based on emotional patterns and trauma themes."""

    def __init__(self):
        self.emotion_weights = {
            'sadness': 1.2,
            'anger': 1.1,
            'fear': 1.3,
            'joy': 0.8,
            'surprise': 0.6,
            'disgust': 1.0
        }
        self.min_data_points = 5  # Minimum emotion analyses needed for clustering
        self.cluster_update_threshold = 0.3  # Similarity threshold for cluster updates

    async def analyze_user_for_clustering(
        self,
        db: Session,
        user_id: int,
        days_back: int = 30
    ) -> Optional[Dict[str, Any]]:
        """Analyze a user's emotional patterns for clustering."""
        try:
            # Get recent emotion analyses
            cutoff_date = datetime.utcnow() - timedelta(days=days_back)
            emotion_analyses = db.query(EmotionAnalysis).filter(
                and_(
                    EmotionAnalysis.user_id == user_id,
                    EmotionAnalysis.analyzed_at >= cutoff_date
                )
            ).order_by(desc(EmotionAnalysis.analyzed_at)).limit(100).all()

            if len(emotion_analyses) < self.min_data_points:
                logger.warning(f"Insufficient emotion data for user {user_id}")
                return None

            # Calculate dominant emotions
            emotion_totals = {
                'joy': 0.0, 'sadness': 0.0, 'anger': 0.0,
                'fear': 0.0, 'surprise': 0.0, 'disgust': 0.0
            }

            for analysis in emotion_analyses:
                for emotion in emotion_totals.keys():
                    emotion_totals[emotion] += getattr(analysis, emotion, 0.0)

            # Normalize by count
            count = len(emotion_analyses)
            dominant_emotions = {k: v / count for k, v in emotion_totals.items()}

            # Calculate emotional intensity and variability
            intensities = []
            for analysis in emotion_analyses:
                intensity = max([
                    getattr(analysis, emotion, 0.0) for emotion in emotion_totals.keys()
                ])
                intensities.append(intensity)

            emotion_intensity = np.mean(intensities)
            emotion_variability = np.std(intensities)

            # Get trauma themes from life events
            trauma_themes = await self._extract_trauma_themes(db, user_id)

            # Determine healing stage
            healing_stage = await self._determine_healing_stage(db, user_id, emotion_analyses)

            # Get coping patterns from user memory
            coping_patterns = await self._extract_coping_patterns(db, user_id)

            # Determine communication style
            communication_style = await self._determine_communication_style(db, user_id)

            # Create cluster vector for similarity calculations
            cluster_vector = self._create_cluster_vector(
                dominant_emotions, emotion_intensity, emotion_variability,
                trauma_themes, healing_stage, coping_patterns
            )

            return {
                'dominant_emotions': dominant_emotions,
                'emotion_intensity': float(emotion_intensity),
                'emotion_variability': float(emotion_variability),
                'trauma_themes': trauma_themes,
                'healing_stage': healing_stage,
                'coping_patterns': coping_patterns,
                'communication_style': communication_style,
                'cluster_vector': cluster_vector.tolist()
            }

        except Exception as e:
            logger.error(f"Error analyzing user {user_id} for clustering: {e}")
            return None

    async def update_user_cluster_profile(
        self,
        db: Session,
        user_id: int,
        force_update: bool = False
    ) -> Optional[UserClusterProfile]:
        """Update or create user cluster profile."""
        try:
            # Check if profile exists and if update is needed
            existing_profile = db.query(UserClusterProfile).filter(
                UserClusterProfile.user_id == user_id
            ).first()

            if existing_profile and not force_update:
                # Check if enough time has passed for update
                if existing_profile.updated_at:
                    time_since_update = datetime.utcnow() - existing_profile.updated_at
                    if time_since_update.days < 7:  # Update weekly
                        return existing_profile

            # Analyze user for clustering
            analysis_data = await self.analyze_user_for_clustering(db, user_id)
            if not analysis_data:
                return existing_profile

            # Update or create profile
            if existing_profile:
                for key, value in analysis_data.items():
                    setattr(existing_profile, key, value)
                existing_profile.last_clustered_at = datetime.utcnow()
                existing_profile.updated_at = datetime.utcnow()
            else:
                existing_profile = UserClusterProfile(
                    user_id=user_id,
                    last_clustered_at=datetime.utcnow(),
                    **analysis_data
                )
                db.add(existing_profile)

            db.commit()
            db.refresh(existing_profile)

            logger.info(f"Updated cluster profile for user {user_id}")
            return existing_profile

        except Exception as e:
            logger.error(f"Error updating cluster profile for user {user_id}: {e}")
            db.rollback()
            return None

    async def find_matching_groups(
        self,
        db: Session,
        user_id: int,
        limit: int = 5
    ) -> List[Tuple[SharedWoundGroup, float]]:
        """Find shared wound groups that match a user's profile."""
        try:
            # Get or update user cluster profile
            user_profile = await self.update_user_cluster_profile(db, user_id)
            if not user_profile:
                return []

            # Get active shared wound groups
            groups = db.query(SharedWoundGroup).filter(
                SharedWoundGroup.is_active == True
            ).all()

            if not groups:
                return []

            user_vector = np.array(user_profile.cluster_vector)
            matches = []

            for group in groups:
                # Calculate similarity score
                similarity = self._calculate_group_similarity(
                    user_profile, group
                )

                if similarity > 0.3:  # Minimum similarity threshold
                    matches.append((group, similarity))

            # Sort by similarity score
            matches.sort(key=lambda x: x[1], reverse=True)

            return matches[:limit]

        except Exception as e:
            logger.error(f"Error finding matching groups for user {user_id}: {e}")
            return []

    async def suggest_peer_circles(
        self,
        db: Session,
        user_id: int,
        shared_wound_group_id: int,
        limit: int = 3
    ) -> List[PeerCircle]:
        """Suggest peer circles within a shared wound group."""
        try:
            # Get circles in the group that aren't full and are active
            circles = db.query(PeerCircle).filter(
                and_(
                    PeerCircle.shared_wound_group_id == shared_wound_group_id,
                    PeerCircle.status == CircleStatus.ACTIVE
                )
            ).all()

            suitable_circles = []

            for circle in circles:
                # Check if circle has space
                member_count = db.query(CircleMembership).filter(
                    and_(
                        CircleMembership.peer_circle_id == circle.id,
                        CircleMembership.status == MembershipStatus.ACTIVE
                    )
                ).count()

                if member_count < circle.max_members:
                    # Check if user is already a member
                    existing_membership = db.query(CircleMembership).filter(
                        and_(
                            CircleMembership.user_id == user_id,
                            CircleMembership.peer_circle_id == circle.id
                        )
                    ).first()

                    if not existing_membership:
                        suitable_circles.append(circle)

            # Sort by recent activity
            suitable_circles.sort(
                key=lambda x: x.last_activity_at,
                reverse=True
            )

            return suitable_circles[:limit]

        except Exception as e:
            logger.error(f"Error suggesting peer circles for user {user_id}: {e}")
            return []

    def _calculate_group_similarity(
        self,
        user_profile: UserClusterProfile,
        group: SharedWoundGroup
    ) -> float:
        """Calculate similarity between user profile and group."""
        try:
            similarity_score = 0.0

            # Emotional pattern similarity (40% weight)
            if group.emotional_pattern and user_profile.dominant_emotions:
                emotion_sim = self._calculate_emotion_similarity(
                    user_profile.dominant_emotions,
                    group.emotional_pattern
                )
                similarity_score += emotion_sim * 0.4

            # Trauma themes similarity (30% weight)
            if group.trauma_themes and user_profile.trauma_themes:
                theme_sim = self._calculate_theme_similarity(
                    user_profile.trauma_themes,
                    group.trauma_themes
                )
                similarity_score += theme_sim * 0.3

            # Healing stage similarity (20% weight)
            if group.healing_stage and user_profile.healing_stage:
                if group.healing_stage == user_profile.healing_stage:
                    similarity_score += 0.2
                elif self._are_adjacent_stages(group.healing_stage, user_profile.healing_stage):
                    similarity_score += 0.1

            # Activity level compatibility (10% weight)
            similarity_score += 0.1  # Base compatibility score

            return min(similarity_score, 1.0)

        except Exception as e:
            logger.error(f"Error calculating group similarity: {e}")
            return 0.0

    def _calculate_emotion_similarity(
        self,
        user_emotions: Dict[str, float],
        group_emotions: Dict[str, Any]
    ) -> float:
        """Calculate emotional pattern similarity."""
        try:
            # Convert to vectors
            emotions = ['joy', 'sadness', 'anger', 'fear', 'surprise', 'disgust']
            user_vector = [user_emotions.get(e, 0.0) for e in emotions]
            group_vector = [group_emotions.get(e, 0.0) for e in emotions]

            # Apply weights
            weighted_user = [user_vector[i] * self.emotion_weights.get(emotions[i], 1.0)
                           for i in range(len(emotions))]
            weighted_group = [group_vector[i] * self.emotion_weights.get(emotions[i], 1.0)
                            for i in range(len(emotions))]

            # Calculate cosine similarity
            user_array = np.array(weighted_user).reshape(1, -1)
            group_array = np.array(weighted_group).reshape(1, -1)

            similarity = cosine_similarity(user_array, group_array)[0][0]
            return max(0.0, similarity)

        except Exception as e:
            logger.error(f"Error calculating emotion similarity: {e}")
            return 0.0

    def _calculate_theme_similarity(
        self,
        user_themes: List[str],
        group_themes: List[str]
    ) -> float:
        """Calculate trauma theme similarity."""
        try:
            if not user_themes or not group_themes:
                return 0.0

            # Calculate Jaccard similarity
            user_set = set(user_themes)
            group_set = set(group_themes)

            intersection = len(user_set.intersection(group_set))
            union = len(user_set.union(group_set))

            return intersection / union if union > 0 else 0.0

        except Exception as e:
            logger.error(f"Error calculating theme similarity: {e}")
            return 0.0

    def _are_adjacent_stages(self, stage1: str, stage2: str) -> bool:
        """Check if healing stages are adjacent."""
        stages = ['early', 'processing', 'integration', 'growth']
        try:
            idx1 = stages.index(stage1)
            idx2 = stages.index(stage2)
            return abs(idx1 - idx2) == 1
        except ValueError:
            return False

    def _create_cluster_vector(
        self,
        emotions: Dict[str, float],
        intensity: float,
        variability: float,
        themes: Optional[List[str]],
        stage: Optional[str],
        coping: Optional[List[str]]
    ) -> np.ndarray:
        """Create numerical vector for clustering."""
        vector = []

        # Emotion values
        emotion_order = ['joy', 'sadness', 'anger', 'fear', 'surprise', 'disgust']
        for emotion in emotion_order:
            vector.append(emotions.get(emotion, 0.0))

        # Intensity and variability
        vector.extend([intensity, variability])

        # Healing stage (one-hot encoding)
        stages = ['early', 'processing', 'integration', 'growth']
        for s in stages:
            vector.append(1.0 if stage == s else 0.0)

        return np.array(vector)

    async def _extract_trauma_themes(self, db: Session, user_id: int) -> List[str]:
        """Extract trauma themes from user's life events."""
        try:
            life_events = db.query(LifeEvent).filter(
                LifeEvent.user_id == user_id
            ).all()

            themes = set()
            for event in life_events:
                if event.category:
                    themes.add(event.category.value)
                if event.tags:
                    themes.update(event.tags)

            return list(themes)

        except Exception as e:
            logger.error(f"Error extracting trauma themes for user {user_id}: {e}")
            return []

    async def _determine_healing_stage(
        self,
        db: Session,
        user_id: int,
        emotion_analyses: List[EmotionAnalysis]
    ) -> str:
        """Determine user's current healing stage."""
        try:
            # Simple heuristic based on emotional patterns and trends
            recent_analyses = emotion_analyses[:10]  # Last 10 analyses

            if not recent_analyses:
                return 'early'

            # Calculate average emotional intensity
            avg_intensity = np.mean([
                max([getattr(a, e, 0.0) for e in ['sadness', 'anger', 'fear']])
                for a in recent_analyses
            ])

            # Calculate trend (improvement over time)
            if len(emotion_analyses) >= 20:
                early_intensity = np.mean([
                    max([getattr(a, e, 0.0) for e in ['sadness', 'anger', 'fear']])
                    for a in emotion_analyses[-10:]  # Earlier analyses
                ])

                improvement = early_intensity - avg_intensity

                if avg_intensity < 0.3 and improvement > 0.2:
                    return 'growth'
                elif avg_intensity < 0.5 and improvement > 0.1:
                    return 'integration'
                elif improvement > 0.05:
                    return 'processing'

            if avg_intensity > 0.7:
                return 'early'
            elif avg_intensity > 0.5:
                return 'processing'
            elif avg_intensity > 0.3:
                return 'integration'
            else:
                return 'growth'

        except Exception as e:
            logger.error(f"Error determining healing stage for user {user_id}: {e}")
            return 'early'

    async def _extract_coping_patterns(self, db: Session, user_id: int) -> List[str]:
        """Extract coping patterns from user interactions."""
        # This would analyze user's conversation patterns, recommendations used, etc.
        # For now, return empty list - can be enhanced later
        return []

    async def _determine_communication_style(self, db: Session, user_id: int) -> str:
        """Determine user's communication style."""
        # This would analyze message patterns, length, emotional expression, etc.
        # For now, return default - can be enhanced later
        return 'balanced'

    async def perform_advanced_clustering(
        self,
        db: Session,
        algorithm: str = "hierarchical",
        min_users: int = 10
    ) -> Dict[str, Any]:
        """Perform advanced clustering on all users with sufficient data."""
        try:
            # Get all user profiles with sufficient data
            profiles = db.query(UserClusterProfile).filter(
                UserClusterProfile.cluster_vector.isnot(None)
            ).all()

            if len(profiles) < min_users:
                logger.warning(f"Insufficient users for clustering: {len(profiles)} < {min_users}")
                return {"error": "Insufficient data for clustering"}

            # Prepare data matrix
            user_ids = [p.user_id for p in profiles]
            vectors = np.array([p.cluster_vector for p in profiles])

            # Standardize features
            scaler = StandardScaler()
            scaled_vectors = scaler.fit_transform(vectors)

            # Perform clustering based on algorithm
            if algorithm == "hierarchical":
                clusters = self._hierarchical_clustering(scaled_vectors)
            elif algorithm == "dbscan":
                clusters = self._dbscan_clustering(scaled_vectors)
            elif algorithm == "emotion_based":
                clusters = self._emotion_based_clustering(profiles, scaled_vectors)
            else:
                clusters = self._kmeans_clustering(scaled_vectors)

            # Create cluster assignments
            cluster_assignments = {}
            for i, cluster_id in enumerate(clusters):
                user_id = user_ids[i]
                cluster_assignments[user_id] = int(cluster_id)

            # Update shared wound groups based on clusters
            await self._update_shared_wound_groups(db, cluster_assignments, profiles)

            # Calculate cluster quality metrics
            quality_metrics = self._calculate_cluster_quality(scaled_vectors, clusters)

            return {
                "algorithm": algorithm,
                "total_users": len(profiles),
                "num_clusters": len(set(clusters)),
                "cluster_assignments": cluster_assignments,
                "quality_metrics": quality_metrics,
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Error performing advanced clustering: {e}")
            return {"error": str(e)}

    def _hierarchical_clustering(self, vectors: np.ndarray, n_clusters: int = None) -> np.ndarray:
        """Perform hierarchical clustering."""
        try:
            if n_clusters is None:
                # Determine optimal number of clusters
                n_clusters = min(8, max(3, len(vectors) // 5))

            clustering = AgglomerativeClustering(
                n_clusters=n_clusters,
                linkage='ward',
                metric='euclidean'
            )

            return clustering.fit_predict(vectors)

        except Exception as e:
            logger.error(f"Error in hierarchical clustering: {e}")
            return np.zeros(len(vectors))

    def _dbscan_clustering(self, vectors: np.ndarray) -> np.ndarray:
        """Perform DBSCAN clustering for density-based grouping."""
        try:
            # Calculate optimal eps using k-distance graph
            distances = pdist(vectors)
            eps = np.percentile(distances, 10)  # Use 10th percentile as eps

            clustering = DBSCAN(
                eps=eps,
                min_samples=max(3, len(vectors) // 10),
                metric='euclidean'
            )

            clusters = clustering.fit_predict(vectors)

            # Handle noise points by assigning them to nearest cluster
            noise_mask = clusters == -1
            if np.any(noise_mask):
                # Assign noise points to nearest cluster centroid
                unique_clusters = np.unique(clusters[clusters != -1])
                if len(unique_clusters) > 0:
                    for i in np.where(noise_mask)[0]:
                        distances_to_clusters = []
                        for cluster_id in unique_clusters:
                            cluster_points = vectors[clusters == cluster_id]
                            centroid = np.mean(cluster_points, axis=0)
                            dist = np.linalg.norm(vectors[i] - centroid)
                            distances_to_clusters.append(dist)

                        nearest_cluster = unique_clusters[np.argmin(distances_to_clusters)]
                        clusters[i] = nearest_cluster

            return clusters

        except Exception as e:
            logger.error(f"Error in DBSCAN clustering: {e}")
            return np.zeros(len(vectors))

    def _emotion_based_clustering(
        self,
        profiles: List[UserClusterProfile],
        vectors: np.ndarray
    ) -> np.ndarray:
        """Perform emotion-focused clustering with custom similarity."""
        try:
            # Extract emotion vectors (first 6 dimensions)
            emotion_vectors = vectors[:, :6]

            # Calculate emotion-weighted similarity matrix
            similarity_matrix = np.zeros((len(profiles), len(profiles)))

            for i in range(len(profiles)):
                for j in range(i + 1, len(profiles)):
                    # Emotion similarity
                    emotion_sim = cosine_similarity(
                        emotion_vectors[i].reshape(1, -1),
                        emotion_vectors[j].reshape(1, -1)
                    )[0][0]

                    # Trauma theme similarity
                    theme_sim = self._calculate_theme_similarity(
                        profiles[i].trauma_themes or [],
                        profiles[j].trauma_themes or []
                    )

                    # Healing stage similarity
                    stage_sim = 1.0 if profiles[i].healing_stage == profiles[j].healing_stage else 0.3

                    # Combined similarity
                    combined_sim = (emotion_sim * 0.5 + theme_sim * 0.3 + stage_sim * 0.2)
                    similarity_matrix[i][j] = combined_sim
                    similarity_matrix[j][i] = combined_sim

            # Convert similarity to distance
            distance_matrix = 1 - similarity_matrix

            # Perform hierarchical clustering on custom distance matrix
            condensed_distances = squareform(distance_matrix)
            linkage_matrix = linkage(condensed_distances, method='average')

            # Determine number of clusters
            n_clusters = min(6, max(3, len(profiles) // 4))
            clusters = fcluster(linkage_matrix, n_clusters, criterion='maxclust') - 1

            return clusters

        except Exception as e:
            logger.error(f"Error in emotion-based clustering: {e}")
            return np.zeros(len(profiles))

    def _kmeans_clustering(self, vectors: np.ndarray) -> np.ndarray:
        """Perform K-means clustering."""
        try:
            # Determine optimal number of clusters using elbow method
            max_k = min(10, len(vectors) // 3)
            inertias = []

            for k in range(2, max_k + 1):
                kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
                kmeans.fit(vectors)
                inertias.append(kmeans.inertia_)

            # Find elbow point
            if len(inertias) > 2:
                # Simple elbow detection
                diffs = np.diff(inertias)
                second_diffs = np.diff(diffs)
                elbow_idx = np.argmax(second_diffs) + 2
                optimal_k = min(elbow_idx, max_k)
            else:
                optimal_k = 3

            # Perform final clustering
            kmeans = KMeans(n_clusters=optimal_k, random_state=42, n_init=10)
            return kmeans.fit_predict(vectors)

        except Exception as e:
            logger.error(f"Error in K-means clustering: {e}")
            return np.zeros(len(vectors))

    async def _update_shared_wound_groups(
        self,
        db: Session,
        cluster_assignments: Dict[int, int],
        profiles: List[UserClusterProfile]
    ):
        """Update shared wound groups based on clustering results."""
        try:
            # Group profiles by cluster
            clusters = {}
            for profile in profiles:
                cluster_id = cluster_assignments.get(profile.user_id)
                if cluster_id is not None:
                    if cluster_id not in clusters:
                        clusters[cluster_id] = []
                    clusters[cluster_id].append(profile)

            # Create or update shared wound groups
            for cluster_id, cluster_profiles in clusters.items():
                if len(cluster_profiles) < 3:  # Skip small clusters
                    continue

                # Calculate cluster characteristics
                cluster_emotions = self._calculate_cluster_emotions(cluster_profiles)
                cluster_themes = self._calculate_cluster_themes(cluster_profiles)
                cluster_stage = self._calculate_cluster_stage(cluster_profiles)

                # Check if group already exists
                existing_group = db.query(SharedWoundGroup).filter(
                    SharedWoundGroup.cluster_id == cluster_id
                ).first()

                if existing_group:
                    # Update existing group
                    existing_group.emotional_pattern = cluster_emotions
                    existing_group.trauma_themes = cluster_themes
                    existing_group.healing_stage = cluster_stage
                    existing_group.member_count = len(cluster_profiles)
                    existing_group.updated_at = datetime.utcnow()
                else:
                    # Create new group
                    group_name = self._generate_group_name(cluster_themes, cluster_stage)
                    new_group = SharedWoundGroup(
                        name=group_name,
                        description=f"A supportive community for those experiencing {', '.join(cluster_themes[:3])}",
                        emotional_pattern=cluster_emotions,
                        trauma_themes=cluster_themes,
                        healing_stage=cluster_stage,
                        cluster_id=cluster_id,
                        member_count=len(cluster_profiles),
                        is_active=True
                    )
                    db.add(new_group)

            db.commit()
            logger.info(f"Updated {len(clusters)} shared wound groups")

        except Exception as e:
            logger.error(f"Error updating shared wound groups: {e}")
            db.rollback()

    def _calculate_cluster_quality(self, vectors: np.ndarray, clusters: np.ndarray) -> Dict[str, float]:
        """Calculate clustering quality metrics."""
        try:
            from sklearn.metrics import silhouette_score, calinski_harabasz_score

            if len(set(clusters)) < 2:
                return {"silhouette_score": 0.0, "calinski_harabasz_score": 0.0}

            silhouette = silhouette_score(vectors, clusters)
            calinski_harabasz = calinski_harabasz_score(vectors, clusters)

            return {
                "silhouette_score": float(silhouette),
                "calinski_harabasz_score": float(calinski_harabasz)
            }

        except Exception as e:
            logger.error(f"Error calculating cluster quality: {e}")
            return {"silhouette_score": 0.0, "calinski_harabasz_score": 0.0}

    def _calculate_cluster_emotions(self, profiles: List[UserClusterProfile]) -> Dict[str, float]:
        """Calculate average emotions for a cluster."""
        try:
            emotions = ['joy', 'sadness', 'anger', 'fear', 'surprise', 'disgust']
            cluster_emotions = {emotion: 0.0 for emotion in emotions}

            for profile in profiles:
                if profile.dominant_emotions:
                    for emotion in emotions:
                        cluster_emotions[emotion] += profile.dominant_emotions.get(emotion, 0.0)

            # Average the emotions
            count = len(profiles)
            return {emotion: value / count for emotion, value in cluster_emotions.items()}

        except Exception as e:
            logger.error(f"Error calculating cluster emotions: {e}")
            return {}

    def _calculate_cluster_themes(self, profiles: List[UserClusterProfile]) -> List[str]:
        """Calculate most common themes for a cluster."""
        try:
            theme_counts = {}

            for profile in profiles:
                if profile.trauma_themes:
                    for theme in profile.trauma_themes:
                        theme_counts[theme] = theme_counts.get(theme, 0) + 1

            # Sort by frequency and return top themes
            sorted_themes = sorted(theme_counts.items(), key=lambda x: x[1], reverse=True)
            return [theme for theme, count in sorted_themes[:5]]

        except Exception as e:
            logger.error(f"Error calculating cluster themes: {e}")
            return []

    def _calculate_cluster_stage(self, profiles: List[UserClusterProfile]) -> str:
        """Calculate most common healing stage for a cluster."""
        try:
            stage_counts = {}

            for profile in profiles:
                if profile.healing_stage:
                    stage_counts[profile.healing_stage] = stage_counts.get(profile.healing_stage, 0) + 1

            if not stage_counts:
                return 'early'

            # Return most common stage
            return max(stage_counts.items(), key=lambda x: x[1])[0]

        except Exception as e:
            logger.error(f"Error calculating cluster stage: {e}")
            return 'early'

    def _generate_group_name(self, themes: List[str], stage: str) -> str:
        """Generate a meaningful name for a shared wound group."""
        try:
            stage_names = {
                'early': 'Beginning',
                'processing': 'Processing',
                'integration': 'Integration',
                'growth': 'Growth'
            }

            stage_name = stage_names.get(stage, 'Support')

            if themes:
                primary_theme = themes[0].replace('_', ' ').title()
                return f"{primary_theme} {stage_name} Circle"
            else:
                return f"{stage_name} Support Circle"

        except Exception as e:
            logger.error(f"Error generating group name: {e}")
            return "Support Circle"

    async def get_cluster_insights(
        self,
        db: Session,
        user_id: int
    ) -> Dict[str, Any]:
        """Get insights about user's cluster and potential matches."""
        try:
            # Get user's cluster profile
            user_profile = db.query(UserClusterProfile).filter(
                UserClusterProfile.user_id == user_id
            ).first()

            if not user_profile:
                return {"error": "User cluster profile not found"}

            # Find similar users
            similar_users = await self._find_similar_users(db, user_profile)

            # Get cluster statistics
            cluster_stats = await self._get_cluster_statistics(db, user_profile)

            # Generate personalized insights
            insights = self._generate_personalized_insights(user_profile, similar_users, cluster_stats)

            return {
                "user_profile": {
                    "dominant_emotions": user_profile.dominant_emotions,
                    "healing_stage": user_profile.healing_stage,
                    "trauma_themes": user_profile.trauma_themes
                },
                "similar_users_count": len(similar_users),
                "cluster_statistics": cluster_stats,
                "insights": insights,
                "recommendations": self._generate_cluster_recommendations(user_profile, similar_users)
            }

        except Exception as e:
            logger.error(f"Error getting cluster insights for user {user_id}: {e}")
            return {"error": str(e)}

    async def _find_similar_users(
        self,
        db: Session,
        user_profile: UserClusterProfile,
        limit: int = 10
    ) -> List[UserClusterProfile]:
        """Find users with similar profiles."""
        try:
            # Get all other user profiles
            other_profiles = db.query(UserClusterProfile).filter(
                UserClusterProfile.user_id != user_profile.user_id
            ).all()

            if not other_profiles:
                return []

            user_vector = np.array(user_profile.cluster_vector)
            similarities = []

            for profile in other_profiles:
                other_vector = np.array(profile.cluster_vector)
                similarity = cosine_similarity(
                    user_vector.reshape(1, -1),
                    other_vector.reshape(1, -1)
                )[0][0]
                similarities.append((profile, similarity))

            # Sort by similarity and return top matches
            similarities.sort(key=lambda x: x[1], reverse=True)
            return [profile for profile, sim in similarities[:limit] if sim > 0.5]

        except Exception as e:
            logger.error(f"Error finding similar users: {e}")
            return []

    async def _get_cluster_statistics(
        self,
        db: Session,
        user_profile: UserClusterProfile
    ) -> Dict[str, Any]:
        """Get statistics about the user's cluster."""
        try:
            # This would get statistics about users in the same cluster
            # For now, return basic stats
            return {
                "total_users_in_cluster": 0,
                "average_healing_progress": 0.0,
                "common_themes": user_profile.trauma_themes or [],
                "cluster_activity_level": "moderate"
            }

        except Exception as e:
            logger.error(f"Error getting cluster statistics: {e}")
            return {}

    def _generate_personalized_insights(
        self,
        user_profile: UserClusterProfile,
        similar_users: List[UserClusterProfile],
        cluster_stats: Dict[str, Any]
    ) -> List[str]:
        """Generate personalized insights for the user."""
        insights = []

        try:
            # Healing stage insight
            if user_profile.healing_stage:
                insights.append(f"You're in the {user_profile.healing_stage} stage of your healing journey.")

            # Similar users insight
            if similar_users:
                insights.append(f"We found {len(similar_users)} users with similar experiences who might understand your journey.")

            # Dominant emotion insight
            if user_profile.dominant_emotions:
                dominant_emotion = max(user_profile.dominant_emotions.items(), key=lambda x: x[1])
                insights.append(f"Your most prominent emotion pattern is {dominant_emotion[0]}, which is common in your healing stage.")

            # Trauma themes insight
            if user_profile.trauma_themes:
                insights.append(f"Your primary areas of focus include {', '.join(user_profile.trauma_themes[:3])}.")

            return insights

        except Exception as e:
            logger.error(f"Error generating personalized insights: {e}")
            return ["We're still learning about your patterns to provide personalized insights."]

    def _generate_cluster_recommendations(
        self,
        user_profile: UserClusterProfile,
        similar_users: List[UserClusterProfile]
    ) -> List[Dict[str, str]]:
        """Generate recommendations based on cluster analysis."""
        recommendations = []

        try:
            # Group recommendations
            if similar_users:
                recommendations.append({
                    "type": "group_joining",
                    "title": "Join a Support Circle",
                    "description": "Connect with others who share similar experiences and healing stages."
                })

            # Healing stage recommendations
            if user_profile.healing_stage == 'early':
                recommendations.append({
                    "type": "resource",
                    "title": "Foundation Building",
                    "description": "Focus on building emotional awareness and safety practices."
                })
            elif user_profile.healing_stage == 'processing':
                recommendations.append({
                    "type": "activity",
                    "title": "Processing Support",
                    "description": "Engage in guided reflection and trauma processing activities."
                })

            return recommendations

        except Exception as e:
            logger.error(f"Error generating cluster recommendations: {e}")
            return []
