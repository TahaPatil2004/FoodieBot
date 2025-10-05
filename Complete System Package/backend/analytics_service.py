import logging
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, timedelta
from backend.models import Conversation, InteractionLog, Product, ProductRecommendation

class AnalyticsService:
    def __init__(self):
        pass

    def get_conversation_analytics(self, db: Session) -> Dict[str, Any]:
        """Get comprehensive conversation analytics"""
        
        # Basic conversation metrics
        total_conversations = db.query(Conversation).count()
        active_conversations = db.query(Conversation).filter(Conversation.status == "active").count()
        
        # Interest score analytics
        avg_interest_score = db.query(func.avg(Conversation.current_interest_score)).scalar() or 0
        max_interest_score = db.query(func.max(Conversation.current_interest_score)).scalar() or 0
        
        # Interaction analytics
        total_interactions = db.query(InteractionLog).count()
        avg_interactions_per_conversation = total_interactions / max(total_conversations, 1)
        
        # Interest score distribution
        score_ranges = {
            "0-20": db.query(Conversation).filter(Conversation.current_interest_score.between(0, 20)).count(),
            "21-40": db.query(Conversation).filter(Conversation.current_interest_score.between(21, 40)).count(),
            "41-60": db.query(Conversation).filter(Conversation.current_interest_score.between(41, 60)).count(),
            "61-80": db.query(Conversation).filter(Conversation.current_interest_score.between(61, 80)).count(),
            "81-100": db.query(Conversation).filter(Conversation.current_interest_score.between(81, 100)).count(),
        }
        
        # Recent activity (last 24 hours)
        yesterday = datetime.utcnow() - timedelta(days=1)
        recent_conversations = db.query(Conversation).filter(
            Conversation.started_at >= yesterday
        ).count()
        
        recent_interactions = db.query(InteractionLog).filter(
            InteractionLog.timestamp >= yesterday
        ).count()
        
        # Top engagement factors
        engagement_factors = {}
        logs_with_factors = db.query(InteractionLog).filter(
            InteractionLog.engagement_factors.isnot(None)
        ).all()
        
        for log in logs_with_factors:
            factors = log.engagement_factors or {}
            for factor, score in factors.items():
                if factor in engagement_factors:
                    engagement_factors[factor] += score
                else:
                    engagement_factors[factor] = score
        
        # Sort engagement factors by total score
        top_engagement_factors = sorted(
            engagement_factors.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:10]
        
        # Conversation duration analytics
        duration_stats = self._calculate_conversation_durations(db)
        
        return {
            "overview": {
                "total_conversations": total_conversations,
                "active_conversations": active_conversations,
                "total_interactions": total_interactions,
                "avg_interactions_per_conversation": round(avg_interactions_per_conversation, 2),
                "avg_interest_score": round(avg_interest_score, 2),
                "max_interest_score": round(max_interest_score, 2)
            },
            "recent_activity": {
                "conversations_last_24h": recent_conversations,
                "interactions_last_24h": recent_interactions
            },
            "interest_score_distribution": score_ranges,
            "top_engagement_factors": [
                {"factor": factor, "total_score": score} 
                for factor, score in top_engagement_factors
            ],
            "conversation_durations": duration_stats,
            "generated_at": datetime.utcnow().isoformat()
        }

    def get_product_analytics(self, db: Session) -> Dict[str, Any]:
        """Get comprehensive product performance analytics"""
        
        # Basic product metrics
        total_products = db.query(Product).count()
        
        # Category distribution
        category_stats = db.query(
            Product.category, 
            func.count(Product.id)
        ).group_by(Product.category).all()
        
        category_distribution = {category: count for category, count in category_stats}
        
        # Price analytics
        avg_price = db.query(func.avg(Product.price)).scalar() or 0
        min_price = db.query(func.min(Product.price)).scalar() or 0
        max_price = db.query(func.max(Product.price)).scalar() or 0
        
        # Popularity analytics
        avg_popularity = db.query(func.avg(Product.popularity_score)).scalar() or 0
        top_products_by_popularity = db.query(Product).order_by(
            desc(Product.popularity_score)
        ).limit(10).all()
        
        # Recommendation analytics
        most_recommended = db.query(
            ProductRecommendation.product_id,
            func.count(ProductRecommendation.id).label('recommendation_count')
        ).group_by(ProductRecommendation.product_id).order_by(
            desc('recommendation_count')
        ).limit(10).all()
        
        # Get product details for most recommended
        most_recommended_products = []
        for product_id, count in most_recommended:
            product = db.query(Product).filter(Product.product_id == product_id).first()
            if product:
                most_recommended_products.append({
                    "product_id": product_id,
                    "name": product.name,
                    "category": product.category,
                    "price": product.price,
                    "recommendation_count": count
                })
        
        # Dietary tags analytics
        dietary_tags_count = {}
        products_with_tags = db.query(Product).filter(Product.dietary_tags.isnot(None)).all()
        
        for product in products_with_tags:
            for tag in (product.dietary_tags or []):
                dietary_tags_count[tag] = dietary_tags_count.get(tag, 0) + 1
        
        # Spice level distribution
        spice_distribution = {}
        for i in range(11):  # 0-10 spice levels
            count = db.query(Product).filter(Product.spice_level == i).count()
            if count > 0:
                spice_distribution[str(i)] = count
        
        # Special items
        chef_specials = db.query(Product).filter(Product.chef_special == True).count()
        limited_time = db.query(Product).filter(Product.limited_time == True).count()
        
        return {
            "overview": {
                "total_products": total_products,
                "avg_price": round(avg_price, 2),
                "price_range": {
                    "min": round(min_price, 2),
                    "max": round(max_price, 2)
                },
                "avg_popularity_score": round(avg_popularity, 2),
                "chef_specials": chef_specials,
                "limited_time_offers": limited_time
            },
            "category_distribution": category_distribution,
            "top_products_by_popularity": [
                {
                    "product_id": product.product_id,
                    "name": product.name,
                    "category": product.category,
                    "popularity_score": product.popularity_score,
                    "price": product.price
                } for product in top_products_by_popularity
            ],
            "most_recommended_products": most_recommended_products,
            "dietary_tags_distribution": dict(sorted(
                dietary_tags_count.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:15]),
            "spice_level_distribution": spice_distribution,
            "generated_at": datetime.utcnow().isoformat()
        }

    def get_interest_score_analytics(self, db: Session) -> Dict[str, Any]:
        """Get detailed interest score analytics"""
        
        # Interest score progression over time
        score_progression = db.query(
            InteractionLog.conversation_id,
            InteractionLog.current_interest_score,
            InteractionLog.timestamp
        ).order_by(InteractionLog.timestamp).all()
        
        # Group by conversation for progression analysis
        conversation_progressions = {}
        for conv_id, score, timestamp in score_progression:
            if conv_id not in conversation_progressions:
                conversation_progressions[conv_id] = []
            conversation_progressions[conv_id].append({
                "score": score,
                "timestamp": timestamp.isoformat()
            })
        
        # Calculate score change patterns
        positive_changes = db.query(InteractionLog).filter(
            InteractionLog.interest_score_change > 0
        ).count()
        
        negative_changes = db.query(InteractionLog).filter(
            InteractionLog.interest_score_change < 0
        ).count()
        
        neutral_changes = db.query(InteractionLog).filter(
            InteractionLog.interest_score_change == 0
        ).count()
        
        # Average score changes
        avg_positive_change = db.query(func.avg(InteractionLog.interest_score_change)).filter(
            InteractionLog.interest_score_change > 0
        ).scalar() or 0
        
        avg_negative_change = db.query(func.avg(InteractionLog.interest_score_change)).filter(
            InteractionLog.interest_score_change < 0
        ).scalar() or 0
        
        # Highest scoring conversations
        high_score_conversations = db.query(Conversation).filter(
            Conversation.current_interest_score >= 80
        ).order_by(desc(Conversation.current_interest_score)).limit(5).all()
        
        # Conversion correlation (interest score vs recommendations)
        recommendation_correlations = db.query(
            InteractionLog.current_interest_score,
            func.count(InteractionLog.recommended_products)
        ).filter(
            InteractionLog.recommended_products.isnot(None)
        ).group_by(InteractionLog.current_interest_score).all()
        
        return {
            "score_change_patterns": {
                "positive_changes": positive_changes,
                "negative_changes": negative_changes,
                "neutral_changes": neutral_changes,
                "avg_positive_change": round(avg_positive_change, 2),
                "avg_negative_change": round(avg_negative_change, 2)
            },
            "high_scoring_conversations": [
                {
                    "conversation_id": conv.conversation_id,
                    "interest_score": conv.current_interest_score,
                    "total_interactions": conv.total_interactions,
                    "started_at": conv.started_at.isoformat() if conv.started_at else None
                } for conv in high_score_conversations
            ],
            "conversation_progressions": dict(list(conversation_progressions.items())[:5]),
            "recommendation_correlations": [
                {
                    "interest_score": score,
                    "recommendation_count": count
                } for score, count in recommendation_correlations
            ],
            "generated_at": datetime.utcnow().isoformat()
        }

    def _calculate_conversation_durations(self, db: Session) -> Dict[str, Any]:
        """Calculate conversation duration statistics"""
        
        # Get conversations with multiple interactions
        conversations_with_duration = []
        
        conversations = db.query(Conversation).filter(
            Conversation.total_interactions > 1
        ).all()
        
        for conv in conversations:
            first_interaction = db.query(InteractionLog).filter(
                InteractionLog.conversation_id == conv.conversation_id
            ).order_by(InteractionLog.timestamp).first()
            
            last_interaction = db.query(InteractionLog).filter(
                InteractionLog.conversation_id == conv.conversation_id
            ).order_by(desc(InteractionLog.timestamp)).first()
            
            if first_interaction and last_interaction:
                duration = (last_interaction.timestamp - first_interaction.timestamp).total_seconds() / 60
                conversations_with_duration.append(duration)
        
        if not conversations_with_duration:
            return {
                "avg_duration_minutes": 0,
                "max_duration_minutes": 0,
                "min_duration_minutes": 0,
                "total_conversations_analyzed": 0
            }
        
        return {
            "avg_duration_minutes": round(sum(conversations_with_duration) / len(conversations_with_duration), 2),
            "max_duration_minutes": round(max(conversations_with_duration), 2),
            "min_duration_minutes": round(min(conversations_with_duration), 2),
            "total_conversations_analyzed": len(conversations_with_duration)
        }

    def get_real_time_metrics(self, db: Session) -> Dict[str, Any]:
        """Get real-time metrics for dashboard"""
        
        now = datetime.utcnow()
        hour_ago = now - timedelta(hours=1)
        
        # Recent activity
        recent_interactions = db.query(InteractionLog).filter(
            InteractionLog.timestamp >= hour_ago
        ).count()
        
        recent_conversations = db.query(Conversation).filter(
            Conversation.last_interaction >= hour_ago
        ).count()
        
        # Current average interest score
        current_avg_score = db.query(func.avg(Conversation.current_interest_score)).filter(
            Conversation.status == "active"
        ).scalar() or 0
        
        # Most recent interactions
        latest_interactions = db.query(InteractionLog).order_by(
            desc(InteractionLog.timestamp)
        ).limit(5).all()
        
        return {
            "recent_interactions_last_hour": recent_interactions,
            "active_conversations_last_hour": recent_conversations,
            "current_avg_interest_score": round(current_avg_score, 2),
            "latest_interactions": [
                {
                    "conversation_id": interaction.conversation_id,
                    "interest_score": interaction.current_interest_score,
                    "timestamp": interaction.timestamp.isoformat(),
                    "score_change": interaction.interest_score_change
                } for interaction in latest_interactions
            ],
            "generated_at": now.isoformat()
        }
