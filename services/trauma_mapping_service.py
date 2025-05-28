"""
Agentic trauma mapping service using LangGraph for intelligent pattern analysis and healing insights.
"""
import logging
import hashlib
import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict, Annotated

from models.trauma_mapping import LifeEvent, TraumaMapping, ReframeSession, EventType, EventCategory
from models.emotion import EmotionAnalysis
from services.emotion_analyzer import EmotionAnalyzer
from config import settings

logger = logging.getLogger(__name__)


class TraumaMappingState(TypedDict):
    """State for the trauma mapping agent workflow."""
    messages: Annotated[List, add_messages]
    user_id: int
    life_events: List[Dict[str, Any]]
    analysis_context: Dict[str, Any]
    patterns_identified: List[Dict[str, Any]]
    trauma_indicators: List[str]
    healing_insights: List[str]
    recommendations: List[str]
    confidence_scores: Dict[str, float]
    current_stage: str  # analysis, pattern_detection, insight_generation, recommendation
    session_context: Dict[str, Any]


class TraumaMappingService:
    """Agentic trauma mapping service using LangGraph for intelligent analysis."""

    def __init__(self):
        self.emotion_analyzer = EmotionAnalyzer()
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            temperature=0.3  # Lower temperature for more consistent analysis
        )
        self.workflow = self._create_trauma_mapping_workflow()

        # Simple in-memory cache for timeline analysis
        self._analysis_cache = {}
        self._cache_ttl = 600  # 10 minutes

        # Trauma indicators for pattern recognition
        self.trauma_indicators = {
            "emotional": ["overwhelming sadness", "persistent fear", "anger outbursts", "emotional numbness"],
            "behavioral": ["avoidance", "isolation", "self-destructive behavior", "hypervigilance"],
            "cognitive": ["intrusive thoughts", "negative self-talk", "memory gaps", "concentration issues"],
            "physical": ["sleep disturbances", "chronic pain", "fatigue", "panic attacks"]
        }

        # Healing stages mapping
        self.healing_stages = {
            "denial": {"description": "Minimizing or denying the impact", "progress_range": (0, 2)},
            "anger": {"description": "Feeling angry about what happened", "progress_range": (2, 4)},
            "bargaining": {"description": "Trying to make sense of the experience", "progress_range": (4, 6)},
            "depression": {"description": "Processing the full emotional impact", "progress_range": (6, 8)},
            "acceptance": {"description": "Integrating the experience and moving forward", "progress_range": (8, 10)}
        }

    def _create_trauma_mapping_workflow(self) -> StateGraph:
        """Create the agentic trauma mapping workflow using LangGraph."""
        workflow = StateGraph(TraumaMappingState)

        # Add workflow nodes
        workflow.add_node("initialize_analysis", self._initialize_analysis)
        workflow.add_node("analyze_events", self._analyze_events)
        workflow.add_node("detect_patterns", self._detect_patterns)
        workflow.add_node("identify_trauma_indicators", self._identify_trauma_indicators)
        workflow.add_node("generate_insights", self._generate_insights)
        workflow.add_node("create_recommendations", self._create_recommendations)
        workflow.add_node("validate_analysis", self._validate_analysis)
        workflow.add_node("finalize_results", self._finalize_results)

        # Define workflow edges
        workflow.set_entry_point("initialize_analysis")
        workflow.add_edge("initialize_analysis", "analyze_events")
        workflow.add_edge("analyze_events", "detect_patterns")
        workflow.add_edge("detect_patterns", "identify_trauma_indicators")
        workflow.add_edge("identify_trauma_indicators", "generate_insights")
        workflow.add_edge("generate_insights", "create_recommendations")
        workflow.add_edge("create_recommendations", "validate_analysis")
        workflow.add_edge("validate_analysis", "finalize_results")
        workflow.add_edge("finalize_results", END)

        return workflow.compile()

    def _initialize_analysis(self, state: TraumaMappingState) -> TraumaMappingState:
        """Initialize the trauma mapping analysis."""
        try:
            state["current_stage"] = "initialization"
            state["patterns_identified"] = []
            state["trauma_indicators"] = []
            state["healing_insights"] = []
            state["recommendations"] = []
            state["confidence_scores"] = {}

            # Create initial analysis context
            state["analysis_context"] = {
                "total_events": len(state["life_events"]),
                "traumatic_events": [e for e in state["life_events"] if e.get("trauma_severity", 0) > 3],
                "positive_events": [e for e in state["life_events"] if e.get("event_type") == "positive"],
                "unresolved_events": [e for e in state["life_events"] if not e.get("is_resolved", False)],
                "analysis_timestamp": datetime.now().isoformat()
            }

            logger.info(f"Initialized trauma mapping analysis for user {state['user_id']}")
            return state

        except Exception as e:
            logger.error(f"Error initializing analysis: {e}")
            state["current_stage"] = "error"
            return state

    def _analyze_events(self, state: TraumaMappingState) -> TraumaMappingState:
        """Analyze individual life events using AI."""
        try:
            state["current_stage"] = "event_analysis"

            # Prepare events data for AI analysis
            events_summary = self._prepare_events_for_analysis(state["life_events"])

            # Create AI prompt for event analysis
            system_prompt = """
            You are a trauma-informed AI specialist analyzing life events for patterns and healing opportunities.
            Analyze each event for:
            1. Emotional impact and trauma severity
            2. Recurring themes and triggers
            3. Resilience factors and coping mechanisms
            4. Connections between events
            5. Healing progression over time

            Provide detailed, compassionate analysis focused on understanding and healing.
            """

            user_prompt = f"""
            Analyze these life events for trauma patterns and healing insights:

            {events_summary}

            Provide analysis in JSON format with:
            - event_insights: detailed insights for each event
            - temporal_patterns: patterns across time
            - emotional_themes: recurring emotional themes
            - resilience_factors: identified strengths and resources
            - healing_opportunities: specific areas for growth
            """

            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]

            response = self.llm.invoke(messages)

            # Parse AI response and update state
            try:
                import json
                analysis_result = json.loads(response.content)
                state["analysis_context"]["ai_analysis"] = analysis_result
                state["confidence_scores"]["event_analysis"] = 0.85
            except json.JSONDecodeError:
                # Fallback to basic analysis
                state["analysis_context"]["ai_analysis"] = {
                    "event_insights": "AI analysis completed",
                    "temporal_patterns": [],
                    "emotional_themes": [],
                    "resilience_factors": [],
                    "healing_opportunities": []
                }
                state["confidence_scores"]["event_analysis"] = 0.6

            logger.info(f"Completed event analysis for user {state['user_id']}")
            return state

        except Exception as e:
            logger.error(f"Error analyzing events: {e}")
            state["confidence_scores"]["event_analysis"] = 0.3
            return state

    def _detect_patterns(self, state: TraumaMappingState) -> TraumaMappingState:
        """Detect patterns across life events using AI pattern recognition."""
        import json

        try:
            state["current_stage"] = "pattern_detection"

            # Use AI to detect sophisticated patterns
            system_prompt = """
            You are an expert pattern recognition specialist for trauma and healing.
            Identify complex patterns including:
            1. Recurring trauma themes and triggers
            2. Temporal clustering of difficult events
            3. Relationship patterns and attachment styles
            4. Coping mechanism evolution
            5. Healing progression patterns
            6. Resilience development over time

            Focus on patterns that reveal both challenges and growth opportunities.
            """

            events_data = state["life_events"]
            ai_analysis = state["analysis_context"].get("ai_analysis", {})

            user_prompt = f"""
            Based on this life events data and initial analysis, identify key patterns:

            Events Data: {json.dumps(events_data[:10])}  # Limit for token efficiency
            Initial Analysis: {json.dumps(ai_analysis)}

            Return patterns in JSON format with:
            - trauma_patterns: recurring trauma themes
            - temporal_clusters: time-based event clusters
            - relationship_patterns: interpersonal patterns
            - coping_evolution: how coping has changed
            - healing_progression: signs of growth and healing
            - priority_patterns: most important patterns to address
            """

            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]

            response = self.llm.invoke(messages)

            # Parse and store patterns
            try:
                patterns_result = json.loads(response.content)
                state["patterns_identified"] = patterns_result
                state["confidence_scores"]["pattern_detection"] = 0.9
            except json.JSONDecodeError:
                # Fallback pattern detection
                state["patterns_identified"] = self._fallback_pattern_detection(events_data)
                state["confidence_scores"]["pattern_detection"] = 0.7

            logger.info(f"Detected patterns for user {state['user_id']}")
            return state

        except Exception as e:
            logger.error(f"Error detecting patterns: {e}")
            state["patterns_identified"] = self._fallback_pattern_detection(state["life_events"])
            state["confidence_scores"]["pattern_detection"] = 0.5
            return state

    async def analyze_timeline_patterns(self, db: Session, user_id: int) -> Dict[str, Any]:
        """Analyze patterns across user's life timeline using agentic workflow."""
        try:
            # Check cache first
            cache_key = self._generate_cache_key(user_id, db)
            cached_result = self._get_cached_analysis(cache_key)
            if cached_result:
                logger.info(f"Returning cached timeline analysis for user {user_id}")
                return cached_result

            # Get all life events for the user
            events = db.query(LifeEvent).filter(
                LifeEvent.user_id == user_id
            ).order_by(LifeEvent.event_date).all()

            if not events:
                return {
                    "total_events": 0,
                    "patterns": [],
                    "emotion_heatmap": [],
                    "recommendations": []
                }

            # Convert events to dict format for the workflow
            events_data = [
                {
                    "id": event.id,
                    "title": event.title,
                    "description": event.description,
                    "event_date": event.event_date.isoformat(),
                    "event_type": event.event_type.value,
                    "category": event.category.value,
                    "emotional_impact_score": event.emotional_impact_score,
                    "trauma_severity": event.trauma_severity,
                    "is_resolved": event.is_resolved,
                    "associated_emotions": event.associated_emotions,
                    "triggers": event.triggers,
                    "themes": event.themes
                }
                for event in events
            ]

            # Initialize the agentic workflow state
            initial_state = TraumaMappingState(
                messages=[],
                user_id=user_id,
                life_events=events_data,
                analysis_context={},
                patterns_identified=[],
                trauma_indicators=[],
                healing_insights=[],
                recommendations=[],
                confidence_scores={},
                current_stage="initialization",
                session_context={"db": db, "timestamp": datetime.now()}
            )

            # Run the agentic workflow
            final_state = await self.workflow.ainvoke(initial_state)

            # Handle case where final_state might be a list or unexpected format
            if isinstance(final_state, list):
                logger.warning("Workflow returned a list instead of dict, using fallback analysis")
                final_state = initial_state
            elif not isinstance(final_state, dict):
                logger.warning(f"Workflow returned unexpected type {type(final_state)}, using fallback analysis")
                final_state = initial_state

            # Extract results from the final state and format for TimelineAnalysisResponse
            recommendations_data = final_state.get("recommendations", {})

            # Convert recommendations dict to list of strings
            recommendations_list = []
            if isinstance(recommendations_data, dict):
                for category, items in recommendations_data.items():
                    if isinstance(items, list):
                        for item in items:
                            if isinstance(item, dict):
                                # Extract string values from dict items
                                for key, value in item.items():
                                    if isinstance(value, str):
                                        recommendations_list.append(value)
                            elif isinstance(item, str):
                                recommendations_list.append(item)
                    elif isinstance(items, str):
                        recommendations_list.append(items)
            elif isinstance(recommendations_data, list):
                for item in recommendations_data:
                    if isinstance(item, dict):
                        # Extract string values from dict items
                        for key, value in item.items():
                            if isinstance(value, str):
                                recommendations_list.append(value)
                    elif isinstance(item, str):
                        recommendations_list.append(item)

            # Format pattern clusters
            patterns_data = final_state.get("patterns_identified", {})
            pattern_clusters = self._format_pattern_clusters(patterns_data)

            result = {
                "total_events": len(events_data),
                "traumatic_events_count": len([e for e in events_data if e.get("trauma_severity", 0) > 3]),
                "positive_events_count": len([e for e in events_data if e.get("event_type") == "POSITIVE"]),
                "unresolved_events_count": len([e for e in events_data if not e.get("is_resolved", False)]),
                "emotion_heatmap": self._generate_emotion_heatmap_from_data(events_data),
                "pattern_clusters": pattern_clusters,
                "healing_progress": final_state.get("analysis_context", {}).get("healing_progress", {}),
                "recommendations": recommendations_list
            }

            # Cache the result
            self._cache_analysis(cache_key, result)
            return result

        except Exception as e:
            logger.error(f"Error analyzing timeline patterns: {e}")
            raise

    def _identify_trauma_indicators(self, state: TraumaMappingState) -> TraumaMappingState:
        """Identify trauma indicators using AI analysis."""
        import json

        try:
            state["current_stage"] = "trauma_indicator_identification"

            # Use AI to identify sophisticated trauma indicators
            system_prompt = """
            You are a trauma specialist identifying indicators of unresolved trauma and healing opportunities.
            Analyze for:
            1. Emotional trauma indicators (numbness, overwhelming emotions, mood swings)
            2. Behavioral trauma indicators (avoidance, hypervigilance, self-destructive patterns)
            3. Cognitive trauma indicators (intrusive thoughts, negative self-talk, memory issues)
            4. Physical trauma indicators (sleep issues, chronic pain, panic symptoms)
            5. Relational trauma indicators (trust issues, attachment difficulties, isolation)
            6. Spiritual trauma indicators (loss of meaning, disconnection, existential crisis)

            Focus on identifying both challenges and existing strengths/resources.
            """

            patterns = state.get("patterns_identified", {})
            events_data = state["life_events"]

            user_prompt = f"""
            Based on the identified patterns and life events, identify trauma indicators:

            Patterns: {json.dumps(patterns)}
            Sample Events: {json.dumps(events_data[:5])}

            Return indicators in JSON format with:
            - emotional_indicators: emotional trauma signs
            - behavioral_indicators: behavioral patterns
            - cognitive_indicators: thought patterns
            - physical_indicators: somatic symptoms
            - relational_indicators: relationship patterns
            - spiritual_indicators: meaning and purpose issues
            - severity_assessment: overall trauma impact (1-10)
            - resilience_factors: existing strengths and resources
            """

            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]

            response = self.llm.invoke(messages)

            # Parse and store trauma indicators
            try:
                indicators_result = json.loads(response.content)
                state["trauma_indicators"] = indicators_result
                state["confidence_scores"]["trauma_indicators"] = 0.85
            except json.JSONDecodeError:
                # Fallback indicators
                state["trauma_indicators"] = self._fallback_trauma_indicators(events_data)
                state["confidence_scores"]["trauma_indicators"] = 0.6

            logger.info(f"Identified trauma indicators for user {state['user_id']}")
            return state

        except Exception as e:
            logger.error(f"Error identifying trauma indicators: {e}")
            state["trauma_indicators"] = self._fallback_trauma_indicators(state["life_events"])
            state["confidence_scores"]["trauma_indicators"] = 0.4
            return state

    def _generate_insights(self, state: TraumaMappingState) -> TraumaMappingState:
        """Generate healing insights using AI."""
        import json

        try:
            state["current_stage"] = "insight_generation"

            # Use AI to generate deep healing insights
            system_prompt = """
            You are a wise, compassionate healing guide generating insights for trauma recovery.
            Create insights that:
            1. Connect past experiences to present patterns
            2. Identify growth opportunities and healing paths
            3. Recognize existing strengths and resilience
            4. Offer hope and empowerment
            5. Suggest specific healing approaches
            6. Honor the person's journey and wisdom

            Focus on empowerment, self-compassion, and practical healing steps.
            """

            patterns = state.get("patterns_identified", {})
            trauma_indicators = state.get("trauma_indicators", {})
            analysis_context = state.get("analysis_context", {})

            user_prompt = f"""
            Generate healing insights based on this comprehensive analysis:

            Patterns: {json.dumps(patterns)}
            Trauma Indicators: {json.dumps(trauma_indicators)}
            Analysis Context: {json.dumps(analysis_context)}

            Return insights in JSON format with:
            - core_insights: fundamental understanding gained
            - healing_opportunities: specific areas for growth
            - strength_recognition: identified resilience and resources
            - connection_insights: how past connects to present
            - empowerment_messages: encouraging realizations
            - next_steps: practical healing actions
            """

            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]

            response = self.llm.invoke(messages)

            # Parse and store insights
            try:
                insights_result = json.loads(response.content)
                state["healing_insights"] = insights_result
                state["confidence_scores"]["insights"] = 0.9
            except json.JSONDecodeError:
                # Fallback insights
                state["healing_insights"] = self._fallback_healing_insights()
                state["confidence_scores"]["insights"] = 0.5

            logger.info(f"Generated healing insights for user {state['user_id']}")
            return state

        except Exception as e:
            logger.error(f"Error generating insights: {e}")
            state["healing_insights"] = self._fallback_healing_insights()
            state["confidence_scores"]["insights"] = 0.3
            return state

    def _identify_patterns(self, events: List[LifeEvent]) -> List[Dict[str, Any]]:
        """Identify recurring patterns in life events."""
        patterns = []

        # Group events by category and analyze
        category_groups = {}
        for event in events:
            category = event.category.value
            if category not in category_groups:
                category_groups[category] = []
            category_groups[category].append(event)

        # Analyze each category for patterns
        for category, category_events in category_groups.items():
            if len(category_events) >= 2:  # Need at least 2 events to identify a pattern
                pattern = self._analyze_category_pattern(category, category_events)
                if pattern:
                    patterns.append(pattern)

        # Look for temporal patterns
        temporal_patterns = self._identify_temporal_patterns(events)
        patterns.extend(temporal_patterns)

        return patterns

    def _analyze_category_pattern(self, category: str, events: List[LifeEvent]) -> Optional[Dict[str, Any]]:
        """Analyze patterns within a specific category."""
        if len(events) < 2:
            return None

        # Calculate average emotional impact
        avg_impact = sum(event.emotional_impact_score for event in events) / len(events)
        avg_trauma_severity = sum(event.trauma_severity for event in events) / len(events)

        # Find common themes
        all_themes = []
        for event in events:
            if event.themes:
                all_themes.extend(event.themes)

        common_themes = list(set(all_themes))

        # Determine pattern severity
        if avg_trauma_severity > 7:
            severity = "high"
        elif avg_trauma_severity > 4:
            severity = "moderate"
        else:
            severity = "low"

        return {
            "pattern_name": f"{category.title()} Pattern",
            "category": category,
            "event_count": len(events),
            "average_impact": avg_impact,
            "average_trauma_severity": avg_trauma_severity,
            "severity": severity,
            "common_themes": common_themes,
            "date_range": {
                "start": min(event.event_date for event in events),
                "end": max(event.event_date for event in events)
            },
            "unresolved_count": len([e for e in events if not e.is_resolved])
        }

    def _identify_temporal_patterns(self, events: List[LifeEvent]) -> List[Dict[str, Any]]:
        """Identify patterns based on timing and sequence."""
        patterns = []

        # Sort events by date
        sorted_events = sorted(events, key=lambda x: x.event_date)

        # Look for clusters of traumatic events
        traumatic_events = [e for e in sorted_events if e.trauma_severity > 5]
        if len(traumatic_events) >= 2:
            clusters = self._find_event_clusters(traumatic_events)
            for cluster in clusters:
                patterns.append({
                    "pattern_name": "Trauma Cluster",
                    "type": "temporal",
                    "events": [e.id for e in cluster],
                    "timespan_days": (cluster[-1].event_date - cluster[0].event_date).days,
                    "severity": "high",
                    "description": f"Cluster of {len(cluster)} traumatic events within a short timespan"
                })

        return patterns

    def _find_event_clusters(self, events: List[LifeEvent], max_gap_days: int = 365) -> List[List[LifeEvent]]:
        """Find clusters of events that occurred close together in time."""
        if len(events) < 2:
            return []

        clusters = []
        current_cluster = [events[0]]

        for i in range(1, len(events)):
            days_gap = (events[i].event_date - events[i-1].event_date).days

            if days_gap <= max_gap_days:
                current_cluster.append(events[i])
            else:
                if len(current_cluster) >= 2:
                    clusters.append(current_cluster)
                current_cluster = [events[i]]

        # Don't forget the last cluster
        if len(current_cluster) >= 2:
            clusters.append(current_cluster)

        return clusters

    def _generate_emotion_heatmap(self, events: List[LifeEvent]) -> List[Dict[str, Any]]:
        """Generate emotion heatmap data for timeline visualization."""
        heatmap_points = []

        for event in events:
            # Determine dominant emotion from associated emotions
            dominant_emotion = "neutral"
            if event.associated_emotions:
                dominant_emotion = max(event.associated_emotions, key=event.associated_emotions.get)

            heatmap_points.append({
                "event_id": event.id,
                "date": event.event_date.isoformat(),
                "emotional_impact": event.emotional_impact_score,
                "trauma_severity": event.trauma_severity,
                "dominant_emotion": dominant_emotion,
                "is_resolved": event.is_resolved,
                "category": event.category.value,
                "title": event.title
            })

        return heatmap_points

    def _identify_trauma_clusters(self, events: List[LifeEvent]) -> List[Dict[str, Any]]:
        """Identify clusters of related traumatic experiences."""
        traumatic_events = [e for e in events if e.trauma_severity > 3]

        if len(traumatic_events) < 2:
            return []

        # Group by themes and triggers
        theme_clusters = {}
        for event in traumatic_events:
            if event.themes:
                for theme in event.themes:
                    if theme not in theme_clusters:
                        theme_clusters[theme] = []
                    theme_clusters[theme].append(event)

        clusters = []
        for theme, theme_events in theme_clusters.items():
            if len(theme_events) >= 2:
                avg_severity = sum(e.trauma_severity for e in theme_events) / len(theme_events)
                clusters.append({
                    "cluster_name": f"{theme.title()} Trauma Cluster",
                    "theme": theme,
                    "events": [e.id for e in theme_events],
                    "event_count": len(theme_events),
                    "average_severity": avg_severity,
                    "unresolved_count": len([e for e in theme_events if not e.is_resolved])
                })

        return clusters

    def _assess_healing_progress(self, db: Session, user_id: int, events: List[LifeEvent]) -> Dict[str, float]:
        """Assess overall healing progress across all traumatic events."""
        traumatic_events = [e for e in events if e.trauma_severity > 3]

        if not traumatic_events:
            return {"overall_progress": 10.0, "resolved_percentage": 100.0}

        # Calculate resolution rate
        resolved_count = len([e for e in traumatic_events if e.is_resolved])
        resolution_rate = (resolved_count / len(traumatic_events)) * 100

        # Get trauma mappings for progress assessment
        trauma_mappings = db.query(TraumaMapping).filter(
            TraumaMapping.user_id == user_id
        ).all()

        if trauma_mappings:
            avg_progress = sum(tm.progress_score for tm in trauma_mappings) / len(trauma_mappings)
        else:
            # Estimate progress based on resolution status
            avg_progress = (resolution_rate / 100) * 10

        return {
            "overall_progress": avg_progress,
            "resolved_percentage": resolution_rate,
            "total_traumatic_events": len(traumatic_events),
            "resolved_events": resolved_count
        }

    def _generate_timeline_recommendations(self, events: List[LifeEvent], patterns: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations based on timeline analysis."""
        recommendations = []

        # Check for unresolved traumatic events
        unresolved_traumatic = [e for e in events if e.trauma_severity > 5 and not e.is_resolved]
        if unresolved_traumatic:
            recommendations.append(
                f"Consider starting reframe sessions for {len(unresolved_traumatic)} unresolved traumatic events"
            )

        # Check for patterns requiring attention
        high_severity_patterns = [p for p in patterns if p.get("severity") == "high"]
        if high_severity_patterns:
            recommendations.append(
                "Multiple high-severity patterns detected - consider professional trauma therapy"
            )

        # Check for recent traumatic events
        recent_trauma = [
            e for e in events
            if e.trauma_severity > 5 and
            (datetime.now() - e.event_date.replace(tzinfo=None)).days < 90
        ]
        if recent_trauma:
            recommendations.append(
                "Recent traumatic events detected - prioritize immediate emotional support and coping strategies"
            )

        # General recommendations
        if len(events) > 10:
            recommendations.append(
                "Rich life timeline detected - consider exploring connections between past and present patterns"
            )

        return recommendations

    def _create_recommendations(self, state: TraumaMappingState) -> TraumaMappingState:
        """Create healing recommendations based on analysis."""
        import json

        try:
            state["current_stage"] = "recommendation_creation"

            # Use AI to create personalized recommendations
            system_prompt = """
            You are a compassionate healing guide creating personalized recommendations for trauma recovery.
            Based on the comprehensive analysis, provide specific, actionable recommendations that:
            1. Address identified trauma patterns and triggers
            2. Build on existing strengths and resilience
            3. Offer practical healing steps
            4. Include both immediate and long-term strategies
            5. Consider the person's unique circumstances
            6. Prioritize safety and self-compassion

            Focus on empowerment and gradual, sustainable healing.
            """

            patterns = state.get("patterns_identified", {})
            trauma_indicators = state.get("trauma_indicators", {})
            healing_insights = state.get("healing_insights", {})

            user_prompt = f"""
            Based on this comprehensive trauma analysis, create personalized healing recommendations:

            Patterns: {json.dumps(patterns)}
            Trauma Indicators: {json.dumps(trauma_indicators)}
            Healing Insights: {json.dumps(healing_insights)}

            Return recommendations in JSON format with:
            - immediate_actions: urgent steps to take now
            - short_term_goals: goals for next 1-3 months
            - long_term_vision: healing vision for 6+ months
            - therapeutic_approaches: recommended therapy types
            - self_care_practices: daily/weekly practices
            - support_resources: community and professional resources
            - crisis_plan: steps for difficult moments
            """

            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]

            response = self.llm.invoke(messages)

            # Parse and store recommendations
            try:
                recommendations_result = json.loads(response.content)
                state["recommendations"] = recommendations_result
                state["confidence_scores"]["recommendations"] = 0.9
            except json.JSONDecodeError:
                # Fallback recommendations
                state["recommendations"] = self._fallback_recommendations()
                state["confidence_scores"]["recommendations"] = 0.6

            logger.info(f"Created recommendations for user {state['user_id']}")
            return state

        except Exception as e:
            logger.error(f"Error creating recommendations: {e}")
            state["recommendations"] = self._fallback_recommendations()
            state["confidence_scores"]["recommendations"] = 0.4
            return state

    def _validate_analysis(self, state: TraumaMappingState) -> TraumaMappingState:
        """Validate the analysis results for quality and safety."""
        try:
            state["current_stage"] = "validation"

            # Validate confidence scores
            confidence_scores = state.get("confidence_scores", {})
            overall_confidence = sum(confidence_scores.values()) / len(confidence_scores) if confidence_scores else 0.5

            # Validate completeness
            required_components = ["patterns_identified", "trauma_indicators", "healing_insights", "recommendations"]
            completeness_score = sum(1 for component in required_components if state.get(component)) / len(required_components)

            # Safety validation - check for crisis indicators
            trauma_indicators = state.get("trauma_indicators", {})
            crisis_indicators = []

            if isinstance(trauma_indicators, dict):
                # Check for high-severity indicators
                severity_assessment = trauma_indicators.get("severity_assessment", 0)
                # Ensure severity_assessment is a number
                if isinstance(severity_assessment, (int, float)) and severity_assessment > 8:
                    crisis_indicators.append("High trauma severity detected")

                # Check for specific crisis patterns
                emotional_indicators = trauma_indicators.get("emotional_indicators", [])
                if any("suicidal" in str(indicator).lower() or "self-harm" in str(indicator).lower()
                       for indicator in emotional_indicators):
                    crisis_indicators.append("Self-harm indicators detected")

            # Update state with validation results
            state["analysis_context"]["validation"] = {
                "overall_confidence": overall_confidence,
                "completeness_score": completeness_score,
                "crisis_indicators": crisis_indicators,
                "validation_timestamp": datetime.now().isoformat(),
                "quality_score": (overall_confidence + completeness_score) / 2
            }

            logger.info(f"Validated analysis for user {state['user_id']}")
            return state

        except Exception as e:
            logger.error(f"Error validating analysis: {e}")
            state["analysis_context"]["validation"] = {
                "overall_confidence": 0.5,
                "completeness_score": 0.5,
                "crisis_indicators": [],
                "validation_timestamp": datetime.now().isoformat(),
                "quality_score": 0.5
            }
            return state

    def _finalize_results(self, state: TraumaMappingState) -> TraumaMappingState:
        """Finalize the analysis results."""
        try:
            state["current_stage"] = "finalized"

            # Create final summary
            final_summary = {
                "analysis_completed": True,
                "total_events_analyzed": len(state.get("life_events", [])),
                "patterns_identified_count": len(state.get("patterns_identified", [])),
                "recommendations_count": len(state.get("recommendations", [])),
                "overall_confidence": state.get("analysis_context", {}).get("validation", {}).get("overall_confidence", 0.5),
                "completion_timestamp": datetime.now().isoformat()
            }

            state["analysis_context"]["final_summary"] = final_summary

            logger.info(f"Finalized analysis for user {state['user_id']}")
            return state

        except Exception as e:
            logger.error(f"Error finalizing results: {e}")
            return state

    def _prepare_events_for_analysis(self, events: List[Dict[str, Any]]) -> str:
        """Prepare events data for AI analysis."""
        try:
            # Create a structured summary of events
            summary_parts = []

            for i, event in enumerate(events[:20]):  # Limit to first 20 events for token efficiency
                event_summary = f"""
                Event {i+1}:
                - Title: {event.get('title', 'Unknown')}
                - Date: {event.get('event_date', 'Unknown')}
                - Type: {event.get('event_type', 'Unknown')}
                - Category: {event.get('category', 'Unknown')}
                - Emotional Impact: {event.get('emotional_impact_score', 0)}/10
                - Trauma Severity: {event.get('trauma_severity', 0)}/10
                - Resolved: {event.get('is_resolved', False)}
                - Description: {event.get('description', 'No description')[:100]}...
                """
                summary_parts.append(event_summary)

            return "\n".join(summary_parts)

        except Exception as e:
            logger.error(f"Error preparing events for analysis: {e}")
            return "Events data could not be processed"

    def _fallback_pattern_detection(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Fallback pattern detection when AI analysis fails."""
        patterns = []

        # Simple category-based pattern detection
        categories = {}
        for event in events:
            category = event.get('category', 'other')
            if category not in categories:
                categories[category] = []
            categories[category].append(event)

        for category, category_events in categories.items():
            if len(category_events) >= 2:
                avg_trauma = sum(e.get('trauma_severity', 0) for e in category_events) / len(category_events)
                patterns.append({
                    "pattern_name": f"{category.title()} Pattern",
                    "category": category,
                    "event_count": len(category_events),
                    "average_trauma_severity": avg_trauma,
                    "description": f"Recurring pattern in {category} events"
                })

        return patterns

    def _fallback_trauma_indicators(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Fallback trauma indicators when AI analysis fails."""
        high_trauma_events = [e for e in events if e.get('trauma_severity', 0) > 5]
        unresolved_events = [e for e in events if not e.get('is_resolved', False)]

        return {
            "emotional_indicators": ["High trauma severity detected"] if high_trauma_events else [],
            "behavioral_indicators": ["Unresolved trauma patterns"] if unresolved_events else [],
            "cognitive_indicators": [],
            "physical_indicators": [],
            "relational_indicators": [],
            "spiritual_indicators": [],
            "severity_assessment": max((e.get('trauma_severity', 0) for e in events), default=0),
            "resilience_factors": ["Seeking help", "Self-awareness"]
        }

    def _generate_emotion_heatmap_from_data(self, events_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate emotion heatmap from events data."""
        heatmap_points = []

        for event in events_data:
            # Determine dominant emotion from associated emotions
            dominant_emotion = "neutral"
            associated_emotions = event.get("associated_emotions")
            if associated_emotions and isinstance(associated_emotions, dict):
                dominant_emotion = max(associated_emotions, key=associated_emotions.get)

            heatmap_points.append({
                "event_id": event.get("id"),
                "date": event.get("event_date"),
                "emotional_impact": event.get("emotional_impact_score", 0),
                "trauma_severity": event.get("trauma_severity", 0),
                "dominant_emotion": dominant_emotion,
                "is_resolved": event.get("is_resolved", False),
                "category": event.get("category", "OTHER"),
                "title": event.get("title", "Unknown Event")
            })

        return heatmap_points

    def _extract_trauma_clusters_from_patterns(self, patterns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract trauma clusters from identified patterns."""
        trauma_clusters = []

        if isinstance(patterns, dict):
            # If patterns is a dict, look for temporal_clusters
            temporal_clusters = patterns.get("temporal_clusters", [])
            if isinstance(temporal_clusters, list):
                trauma_clusters.extend(temporal_clusters)
        elif isinstance(patterns, list):
            # If patterns is a list, filter for trauma-related patterns
            for pattern in patterns:
                if isinstance(pattern, dict):
                    pattern_type = pattern.get("type", "")
                    pattern_name = pattern.get("pattern_name", "")
                    if "trauma" in pattern_type.lower() or "trauma" in pattern_name.lower():
                        trauma_clusters.append(pattern)

        return trauma_clusters

    def _format_pattern_clusters(self, patterns_data: Any) -> List[Dict[str, Any]]:
        """Format patterns data into pattern clusters for the response."""
        pattern_clusters = []

        if isinstance(patterns_data, dict):
            # Extract temporal clusters if available
            temporal_clusters = patterns_data.get("temporal_clusters", [])
            if isinstance(temporal_clusters, list):
                pattern_clusters.extend(temporal_clusters)

            # Extract trauma patterns
            trauma_patterns = patterns_data.get("trauma_patterns", [])
            if isinstance(trauma_patterns, list):
                pattern_clusters.extend(trauma_patterns)

            # Extract other pattern types
            for key, value in patterns_data.items():
                if key not in ["temporal_clusters", "trauma_patterns"] and isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict):
                            pattern_clusters.append({
                                "pattern_type": key,
                                "pattern_name": item.get("name", key),
                                "description": item.get("description", ""),
                                "severity": item.get("severity", "unknown"),
                                "events": item.get("events", []),
                                "themes": item.get("themes", [])
                            })
        elif isinstance(patterns_data, list):
            pattern_clusters = patterns_data

        return pattern_clusters

    def _fallback_healing_insights(self) -> Dict[str, Any]:
        """Fallback healing insights when AI analysis fails."""
        return {
            "core_insights": ["Your journey of self-awareness is a strength"],
            "healing_opportunities": ["Focus on self-compassion and gradual healing"],
            "strength_recognition": ["You have the courage to seek understanding"],
            "connection_insights": ["Past experiences shape but don't define you"],
            "empowerment_messages": ["You have the power to heal and grow"],
            "next_steps": ["Take one small step at a time toward healing"]
        }

    def _fallback_recommendations(self) -> Dict[str, Any]:
        """Fallback recommendations when AI analysis fails."""
        return {
            "immediate_actions": ["Practice deep breathing", "Reach out to a trusted friend"],
            "short_term_goals": ["Establish a daily self-care routine", "Consider journaling"],
            "long_term_vision": ["Build resilience and emotional well-being"],
            "therapeutic_approaches": ["Consider trauma-informed therapy", "Explore mindfulness practices"],
            "self_care_practices": ["Regular exercise", "Adequate sleep", "Healthy nutrition"],
            "support_resources": ["Mental health professionals", "Support groups", "Crisis hotlines"],
            "crisis_plan": ["Call emergency services if in immediate danger", "Contact a mental health professional"]
        }

    def _generate_cache_key(self, user_id: int, db: Session) -> str:
        """Generate a cache key based on user events."""
        # Get the latest event timestamp to invalidate cache when events change
        latest_event = db.query(LifeEvent).filter(
            LifeEvent.user_id == user_id
        ).order_by(LifeEvent.updated_at.desc()).first()

        if latest_event:
            timestamp = latest_event.updated_at.isoformat()
        else:
            timestamp = datetime.now().isoformat()

        # Create hash of user_id and latest timestamp
        cache_data = f"{user_id}:{timestamp}"
        return hashlib.md5(cache_data.encode()).hexdigest()

    def _get_cached_analysis(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached analysis if still valid."""
        if cache_key in self._analysis_cache:
            cached_data, timestamp = self._analysis_cache[cache_key]
            if (datetime.now() - timestamp).total_seconds() < self._cache_ttl:
                return cached_data
            else:
                # Remove expired cache
                del self._analysis_cache[cache_key]
        return None

    def _cache_analysis(self, cache_key: str, result: Dict[str, Any]) -> None:
        """Cache the analysis result."""
        self._analysis_cache[cache_key] = (result, datetime.now())

        # Simple cache cleanup - remove old entries if cache gets too large
        if len(self._analysis_cache) > 100:
            # Remove oldest entries
            sorted_cache = sorted(
                self._analysis_cache.items(),
                key=lambda x: x[1][1]  # Sort by timestamp
            )
            # Keep only the 50 most recent entries
            self._analysis_cache = dict(sorted_cache[-50:])

