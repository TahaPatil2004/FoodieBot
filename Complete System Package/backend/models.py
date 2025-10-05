from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import json

Base = declarative_base()

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(String, unique=True, index=True)
    name = Column(String, index=True)
    category = Column(String, index=True)
    description = Column(Text)
    ingredients = Column(JSON)
    price = Column(Float)
    calories = Column(Integer)
    prep_time = Column(String)
    dietary_tags = Column(JSON)
    mood_tags = Column(JSON)
    allergens = Column(JSON)
    popularity_score = Column(Integer)
    chef_special = Column(Boolean, default=False)
    limited_time = Column(Boolean, default=False)
    spice_level = Column(Integer)
    image_prompt = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "product_id": self.product_id,
            "name": self.name,
            "category": self.category,
            "description": self.description,
            "ingredients": self.ingredients,
            "price": self.price,
            "calories": self.calories,
            "prep_time": self.prep_time,
            "dietary_tags": self.dietary_tags,
            "mood_tags": self.mood_tags,
            "allergens": self.allergens,
            "popularity_score": self.popularity_score,
            "chef_special": self.chef_special,
            "limited_time": self.limited_time,
            "spice_level": self.spice_level,
            "image_prompt": self.image_prompt,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(String, unique=True, index=True)
    user_preferences = Column(JSON)
    dietary_restrictions = Column(JSON)
    budget_range = Column(String)
    mood_tags = Column(JSON)
    current_interest_score = Column(Float, default=0.0)
    total_interactions = Column(Integer, default=0)
    started_at = Column(DateTime, default=datetime.utcnow)
    last_interaction = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="active")

    # Relationship to interaction logs
    interactions = relationship("InteractionLog", back_populates="conversation")

    def to_dict(self):
        return {
            "id": self.id,
            "conversation_id": self.conversation_id,
            "user_preferences": self.user_preferences,
            "dietary_restrictions": self.dietary_restrictions,
            "budget_range": self.budget_range,
            "mood_tags": self.mood_tags,
            "current_interest_score": self.current_interest_score,
            "total_interactions": self.total_interactions,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "last_interaction": self.last_interaction.isoformat() if self.last_interaction else None,
            "status": self.status
        }

class InteractionLog(Base):
    __tablename__ = "interaction_logs"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(String, ForeignKey("conversations.conversation_id"))
    user_message = Column(Text)
    bot_response = Column(Text)
    interest_score_change = Column(Float)
    current_interest_score = Column(Float)
    engagement_factors = Column(JSON)
    recommended_products = Column(JSON)
    timestamp = Column(DateTime, default=datetime.utcnow)

    # Relationship back to conversation
    conversation = relationship("Conversation", back_populates="interactions")

    def to_dict(self):
        return {
            "id": self.id,
            "conversation_id": self.conversation_id,
            "user_message": self.user_message,
            "bot_response": self.bot_response,
            "interest_score_change": self.interest_score_change,
            "current_interest_score": self.current_interest_score,
            "engagement_factors": self.engagement_factors,
            "recommended_products": self.recommended_products,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None
        }

class ProductRecommendation(Base):
    __tablename__ = "product_recommendations"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(String, ForeignKey("conversations.conversation_id"))
    product_id = Column(String, ForeignKey("products.product_id"))
    recommendation_score = Column(Float)
    reason = Column(Text)
    clicked = Column(Boolean, default=False)
    ordered = Column(Boolean, default=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "conversation_id": self.conversation_id,
            "product_id": self.product_id,
            "recommendation_score": self.recommendation_score,
            "reason": self.reason,
            "clicked": self.clicked,
            "ordered": self.ordered,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None
        }
