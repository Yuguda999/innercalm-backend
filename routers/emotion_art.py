"""
Emotion art router for generative art based on emotional state.
"""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any

from database import get_db
from routers.auth import get_current_active_user
from models.user import User
from models.emotion_art import EmotionArt, ArtCustomization, ArtGallery, ArtShare, ArtStyle, ArtStatus
from models.emotion import EmotionAnalysis
from models.voice_journal import VoiceJournal
from schemas.emotion_art import (
    EmotionArtCreate, EmotionArtUpdate, EmotionArtResponse,
    ArtCustomizationCreate, ArtCustomizationUpdate, ArtCustomizationResponse,
    ArtGalleryCreate, ArtGalleryUpdate, ArtGalleryResponse, ArtGalleryWithArt,
    ArtShareCreate, ArtShareUpdate, ArtShareResponse,
    ArtGenerationRequest, ArtCustomizationRequest, EmotionArtAnalytics
)
from services.emotion_art_generator import EmotionArtGenerator

router = APIRouter(prefix="/emotion-art", tags=["emotion-art"])


@router.post("/generate", response_model=EmotionArtResponse)
async def generate_emotion_art(
    generation_request: ArtGenerationRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Generate emotion art based on emotion data."""
    try:
        # Create art record
        art = EmotionArt(
            user_id=current_user.id,
            title=generation_request.title,
            description=generation_request.description,
            art_style=generation_request.art_style.value,
            status=ArtStatus.GENERATING.value,
            emotion_snapshot=generation_request.emotion_data,
            dominant_emotion=max(generation_request.emotion_data, key=generation_request.emotion_data.get),
            emotional_intensity=max(generation_request.emotion_data.values()),
            complexity_level=generation_request.complexity_level
        )

        # Set source references
        if generation_request.source_type == "analysis" and generation_request.source_id:
            art.source_emotion_analysis_id = generation_request.source_id
        elif generation_request.source_type == "voice_journal" and generation_request.source_id:
            art.source_voice_journal_id = generation_request.source_id

        db.add(art)
        db.commit()
        db.refresh(art)

        # Generate art in background
        background_tasks.add_task(
            _generate_art_background,
            art.id,
            generation_request.emotion_data,
            generation_request.art_style,
            generation_request.complexity_level,
            generation_request.color_preferences,
            db
        )

        return art

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating emotion art: {str(e)}"
        )


async def _generate_art_background(
    art_id: int,
    emotion_data: Dict[str, float],
    art_style: ArtStyle,
    complexity_level: int,
    color_preferences: Optional[List[str]],
    db: Session
):
    """Background task to generate art."""
    try:
        generator = EmotionArtGenerator()

        # Generate the art
        result = await generator.generate_emotion_art(
            emotion_data=emotion_data,
            art_style=art_style,
            complexity_level=complexity_level,
            color_preferences=color_preferences
        )

        # Update the art record
        art = db.query(EmotionArt).filter(EmotionArt.id == art_id).first()
        if art:
            art.status = result["status"]
            art.svg_content = result.get("svg_content")
            art.svg_data_url = result.get("svg_data_url")
            art.color_palette = result.get("color_palette")
            art.generation_seed = result.get("generation_seed")
            art.generation_parameters = result.get("generation_parameters")

            if result["status"] == ArtStatus.COMPLETED.value:
                from datetime import datetime
                art.generated_at = datetime.utcnow()

            db.commit()

    except Exception as e:
        # Mark as failed
        art = db.query(EmotionArt).filter(EmotionArt.id == art_id).first()
        if art:
            art.status = ArtStatus.FAILED.value
            db.commit()


@router.get("/artworks", response_model=List[EmotionArtResponse])
async def get_user_artworks(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    limit: int = 20,
    offset: int = 0,
    style_filter: Optional[ArtStyle] = None,
    status_filter: Optional[ArtStatus] = None
):
    """Get user's emotion artworks."""
    try:
        query = db.query(EmotionArt).filter(
            EmotionArt.user_id == current_user.id
        )

        if style_filter:
            query = query.filter(EmotionArt.art_style == style_filter.value)

        if status_filter:
            query = query.filter(EmotionArt.status == status_filter.value)

        artworks = query.order_by(
            EmotionArt.created_at.desc()
        ).offset(offset).limit(limit).all()

        return artworks

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving artworks: {str(e)}"
        )


@router.get("/artworks/{artwork_id}", response_model=EmotionArtResponse)
async def get_artwork(
    artwork_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a specific artwork."""
    try:
        artwork = db.query(EmotionArt).filter(
            EmotionArt.id == artwork_id,
            EmotionArt.user_id == current_user.id
        ).first()

        if not artwork:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Artwork not found"
            )

        # Update view count and last viewed
        artwork.view_count += 1
        from datetime import datetime
        artwork.last_viewed_at = datetime.utcnow()
        db.commit()

        return artwork

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving artwork: {str(e)}"
        )


@router.put("/artworks/{artwork_id}", response_model=EmotionArtResponse)
async def update_artwork(
    artwork_id: int,
    update_data: EmotionArtUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update an artwork."""
    try:
        artwork = db.query(EmotionArt).filter(
            EmotionArt.id == artwork_id,
            EmotionArt.user_id == current_user.id
        ).first()

        if not artwork:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Artwork not found"
            )

        # Update fields
        for field, value in update_data.dict(exclude_unset=True).items():
            setattr(artwork, field, value)

        db.commit()
        db.refresh(artwork)

        return artwork

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating artwork: {str(e)}"
        )


@router.post("/artworks/{artwork_id}/customize", response_model=ArtCustomizationResponse)
async def customize_artwork(
    artwork_id: int,
    customization_request: ArtCustomizationRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Apply customizations to an artwork."""
    try:
        artwork = db.query(EmotionArt).filter(
            EmotionArt.id == artwork_id,
            EmotionArt.user_id == current_user.id
        ).first()

        if not artwork:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Artwork not found"
            )

        if not artwork.svg_content:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Artwork has no content to customize"
            )

        # Apply customization
        generator = EmotionArtGenerator()
        customized_svg = await generator.customize_art(
            artwork.svg_content,
            customization_request.customization_type,
            customization_request.parameters
        )

        if customization_request.preview_only:
            # Return preview without saving
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "preview_svg": customized_svg,
                    "message": "Preview generated successfully"
                }
            )

        # Save customization
        customization = ArtCustomization(
            emotion_art_id=artwork_id,
            user_id=current_user.id,
            customization_type=customization_request.customization_type,
            original_value={"svg_content": artwork.svg_content},
            new_value=customization_request.parameters
        )

        # Update artwork with customized version
        artwork.svg_content = customized_svg
        artwork.svg_data_url = generator._svg_to_data_url(customized_svg)

        db.add(customization)
        db.commit()
        db.refresh(customization)

        return customization

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error customizing artwork: {str(e)}"
        )


@router.get("/artworks/{artwork_id}/customizations", response_model=List[ArtCustomizationResponse])
async def get_artwork_customizations(
    artwork_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get customizations for an artwork."""
    try:
        # Verify artwork ownership
        artwork = db.query(EmotionArt).filter(
            EmotionArt.id == artwork_id,
            EmotionArt.user_id == current_user.id
        ).first()

        if not artwork:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Artwork not found"
            )

        customizations = db.query(ArtCustomization).filter(
            ArtCustomization.emotion_art_id == artwork_id
        ).order_by(ArtCustomization.applied_at.desc()).all()

        return customizations

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving customizations: {str(e)}"
        )


@router.post("/galleries", response_model=ArtGalleryResponse)
async def create_art_gallery(
    gallery_data: ArtGalleryCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new art gallery."""
    try:
        gallery = ArtGallery(
            user_id=current_user.id,
            name=gallery_data.name,
            description=gallery_data.description,
            is_public=gallery_data.is_public,
            art_pieces=gallery_data.art_pieces or [],
            total_pieces=len(gallery_data.art_pieces) if gallery_data.art_pieces else 0
        )

        db.add(gallery)
        db.commit()
        db.refresh(gallery)

        return gallery

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating art gallery: {str(e)}"
        )


@router.get("/galleries", response_model=List[ArtGalleryResponse])
async def get_user_galleries(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    include_public: bool = False
):
    """Get user's art galleries."""
    try:
        query = db.query(ArtGallery).filter(
            ArtGallery.user_id == current_user.id
        )

        if include_public:
            # Include public galleries from other users
            public_query = db.query(ArtGallery).filter(
                ArtGallery.is_public == True,
                ArtGallery.user_id != current_user.id
            )
            galleries = query.union(public_query).order_by(ArtGallery.created_at.desc()).all()
        else:
            galleries = query.order_by(ArtGallery.created_at.desc()).all()

        return galleries

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving galleries: {str(e)}"
        )


@router.get("/galleries/{gallery_id}", response_model=ArtGalleryWithArt)
async def get_gallery_with_artworks(
    gallery_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a gallery with its artworks."""
    try:
        gallery = db.query(ArtGallery).filter(
            ArtGallery.id == gallery_id
        ).first()

        if not gallery:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Gallery not found"
            )

        # Check access permissions
        if gallery.user_id != current_user.id and not gallery.is_public:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to private gallery"
            )

        # Get artworks in the gallery
        artworks = []
        if gallery.art_pieces:
            artworks = db.query(EmotionArt).filter(
                EmotionArt.id.in_(gallery.art_pieces)
            ).all()

        # Update view count if not owner
        if gallery.user_id != current_user.id:
            gallery.total_views += 1
            db.commit()

        # Convert to response with artworks
        gallery_dict = {
            "id": gallery.id,
            "user_id": gallery.user_id,
            "name": gallery.name,
            "description": gallery.description,
            "is_public": gallery.is_public,
            "art_pieces": gallery.art_pieces,
            "total_pieces": gallery.total_pieces,
            "total_views": gallery.total_views,
            "created_at": gallery.created_at,
            "updated_at": gallery.updated_at,
            "artworks": artworks
        }

        return ArtGalleryWithArt(**gallery_dict)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving gallery: {str(e)}"
        )


@router.put("/galleries/{gallery_id}", response_model=ArtGalleryResponse)
async def update_gallery(
    gallery_id: int,
    update_data: ArtGalleryUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update an art gallery."""
    try:
        gallery = db.query(ArtGallery).filter(
            ArtGallery.id == gallery_id,
            ArtGallery.user_id == current_user.id
        ).first()

        if not gallery:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Gallery not found"
            )

        # Update fields
        for field, value in update_data.dict(exclude_unset=True).items():
            setattr(gallery, field, value)

        # Update total pieces count if art_pieces changed
        if update_data.art_pieces is not None:
            gallery.total_pieces = len(update_data.art_pieces)

        from datetime import datetime
        gallery.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(gallery)

        return gallery

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating gallery: {str(e)}"
        )


@router.post("/artworks/{artwork_id}/share", response_model=ArtShareResponse)
async def share_artwork(
    artwork_id: int,
    share_data: ArtShareCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Share an artwork with the community."""
    try:
        # Verify artwork ownership
        artwork = db.query(EmotionArt).filter(
            EmotionArt.id == artwork_id,
            EmotionArt.user_id == current_user.id
        ).first()

        if not artwork:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Artwork not found"
            )

        # Check if already shared
        existing_share = db.query(ArtShare).filter(
            ArtShare.emotion_art_id == artwork_id
        ).first()

        if existing_share:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Artwork is already shared"
            )

        # Create share record
        share = ArtShare(
            emotion_art_id=artwork_id,
            user_id=current_user.id,
            share_message=share_data.share_message,
            is_anonymous=share_data.is_anonymous
        )

        # Mark artwork as shared
        artwork.is_shared = True

        db.add(share)
        db.commit()
        db.refresh(share)

        return share

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error sharing artwork: {str(e)}"
        )


@router.get("/shared-artworks", response_model=List[ArtShareResponse])
async def get_shared_artworks(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    limit: int = 20,
    offset: int = 0
):
    """Get shared artworks from the community."""
    try:
        shares = db.query(ArtShare).filter(
            ArtShare.is_approved == True,
            ArtShare.is_flagged == False
        ).order_by(
            ArtShare.shared_at.desc()
        ).offset(offset).limit(limit).all()

        return shares

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving shared artworks: {str(e)}"
        )


@router.get("/analytics", response_model=EmotionArtAnalytics)
async def get_emotion_art_analytics(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    days: int = 30
):
    """Get emotion art analytics for the user."""
    try:
        from datetime import datetime, timedelta

        cutoff_date = datetime.utcnow() - timedelta(days=days)

        # Get artworks in date range
        artworks = db.query(EmotionArt).filter(
            EmotionArt.user_id == current_user.id,
            EmotionArt.created_at >= cutoff_date
        ).all()

        # Calculate analytics
        total_artworks = len(artworks)
        favorite_count = sum(1 for art in artworks if art.is_favorite)
        shared_count = sum(1 for art in artworks if art.is_shared)
        total_views = sum(art.view_count for art in artworks)

        # Style usage
        style_counts = {}
        for artwork in artworks:
            style = artwork.art_style
            style_counts[style] = style_counts.get(style, 0) + 1

        most_used_styles = [
            {"style": style, "count": count}
            for style, count in sorted(style_counts.items(), key=lambda x: x[1], reverse=True)
        ]

        # Emotion distribution
        emotion_counts = {}
        for artwork in artworks:
            emotion = artwork.dominant_emotion
            emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1

        # Color preferences (simplified)
        color_preferences = ["#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7"]

        # Customization frequency
        customizations = db.query(ArtCustomization).join(EmotionArt).filter(
            EmotionArt.user_id == current_user.id,
            ArtCustomization.applied_at >= cutoff_date
        ).all()

        customization_counts = {}
        for custom in customizations:
            ctype = custom.customization_type
            customization_counts[ctype] = customization_counts.get(ctype, 0) + 1

        # Engagement metrics
        engagement_metrics = {
            "average_views_per_artwork": total_views / total_artworks if total_artworks > 0 else 0,
            "favorite_rate": favorite_count / total_artworks if total_artworks > 0 else 0,
            "share_rate": shared_count / total_artworks if total_artworks > 0 else 0,
            "customization_rate": len(customizations) / total_artworks if total_artworks > 0 else 0
        }

        return EmotionArtAnalytics(
            total_artworks=total_artworks,
            favorite_count=favorite_count,
            shared_count=shared_count,
            total_views=total_views,
            most_used_styles=most_used_styles,
            emotion_distribution=emotion_counts,
            color_preferences=color_preferences,
            customization_frequency=customization_counts,
            engagement_metrics=engagement_metrics
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving emotion art analytics: {str(e)}"
        )


@router.delete("/artworks/{artwork_id}")
async def delete_artwork(
    artwork_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete an artwork."""
    try:
        artwork = db.query(EmotionArt).filter(
            EmotionArt.id == artwork_id,
            EmotionArt.user_id == current_user.id
        ).first()

        if not artwork:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Artwork not found"
            )

        db.delete(artwork)
        db.commit()

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": "Artwork deleted successfully"}
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting artwork: {str(e)}"
        )
