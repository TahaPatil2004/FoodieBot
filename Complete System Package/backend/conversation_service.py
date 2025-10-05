import logging
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import desc
from backend.models import Conversation, InteractionLog
from backend.gemini_service import GeminiService
from backend.recommendation_engine import RecommendationEngine
import uuid
import re
from datetime import datetime, timedelta


class ConversationService:
    def __init__(self, gemini_service: GeminiService):
        self.gemini_service = gemini_service
        self.recommendation_engine = RecommendationEngine()


        self.ENGAGEMENT_FACTORS = {
            'specific_preferences': 15,  # "I love spicy Korean food"
            'dietary_restrictions': 10,  # "I'm vegetarian"
            'budget_mention': 5,  # "Under $15"
            'mood_indication': 20,  # "I'm feeling adventurous"
            'question_asking': 10,  # "What's the spice level?"
            'enthusiasm_words': 8,  # "amazing", "perfect", "love"
            'price_inquiry': 25,  # "How much is that?"
            'order_intent': 30,  # "I'll take it", "Add to cart"
        }

        self.NEGATIVE_FACTORS = {
            'hesitation': -10,  # "maybe", "not sure"
            'budget_concern': -15,  # "too expensive"
            'dietary_conflict': -20,  # Product doesn't match restrictions
            'rejection': -25,  # "I don't like that"
            'delay_response': -5,  # Long response time
        }

        # Keywords for detection
        self.specific_preference_keywords = [
            'spicy', 'mild', 'hot', 'korean', 'mexican', 'italian', 'chinese',
            'burger', 'pizza', 'taco', 'salad', 'chicken', 'beef', 'vegetarian',
            'vegan', 'crispy', 'juicy', 'creamy', 'crunchy', 'sweet', 'salty'
        ]

        self.dietary_keywords = [
            'vegetarian', 'vegan', 'gluten-free', 'dairy-free', 'keto', 'low-carb',
            'halal', 'kosher', 'allergic', 'allergy', 'no dairy', 'no gluten'
        ]

        self.mood_keywords = [
            'adventurous', 'comfort', 'healthy', 'indulgent', 'quick', 'fancy',
            'feeling', 'mood', 'craving', 'want something', 'in the mood for'
        ]

        self.enthusiasm_keywords = [
            'amazing', 'perfect', 'love', 'awesome', 'fantastic', 'great',
            'excellent', 'wonderful', 'delicious', 'yummy', 'sounds good'
        ]

        self.hesitation_keywords = [
            'maybe', 'not sure', 'uncertain', 'hmm', 'i think', 'perhaps',
            'possibly', 'might', 'could be', 'not really sure'
        ]

        self.budget_concern_keywords = [
            'too expensive', 'too much', 'costly', 'pricey', 'expensive',
            'cheap', 'affordable', 'budget', 'money'
        ]

        self.question_keywords = [
            'what', 'how', 'when', 'where', 'why', 'which', 'can you',
            'do you have', 'is it', 'does it', 'spice level', 'ingredients'
        ]

        self.order_intent_keywords = [
            "i'll take", "add to cart", "order", "get me", "i want that",
            "sounds perfect", "i'll have", "give me", "let's go with"
        ]

    async def process_message(
            self,
            message: str,
            conversation_id: Optional[str],
            db: Session
    ) -> Dict[str, Any]:
        """Process user message and return response with interest scoring"""

        try:
            # Get or create conversation
            if conversation_id:
                conversation = db.query(Conversation).filter(
                    Conversation.conversation_id == conversation_id
                ).first()
            else:
                conversation = None

            if not conversation:
                conversation_id = str(uuid.uuid4())
                conversation = Conversation(
                    conversation_id=conversation_id,
                    user_preferences=[],
                    dietary_restrictions=[],
                    mood_tags=[],
                    interest_score=0  # Start at 0
                )
                db.add(conversation)
                db.commit()
                db.refresh(conversation)


            score_change, engagement_factors = self._calculate_interest_score_change(
                message, conversation, db
            )

            # Update conversation interest score
            new_score = max(0, min(100, conversation.interest_score + score_change))
            conversation.interest_score = new_score

            # Extract and update user preferences
            preferences = self._extract_preferences(message)
            if preferences['dietary']:
                for dietary in preferences['dietary']:
                    if dietary not in conversation.dietary_restrictions:
                        conversation.dietary_restrictions.append(dietary)

            if preferences['moods']:
                for mood in preferences['moods']:
                    if mood not in conversation.mood_tags:
                        conversation.mood_tags.append(mood)

            if preferences['specific_prefs']:
                for pref in preferences['specific_prefs']:
                    if pref not in conversation.user_preferences:
                        conversation.user_preferences.append(pref)

            db.commit()

            # Generate AI response
            bot_response = await self.gemini_service.generate_response(
                message, conversation, engagement_factors
            )

            # Get recommendations if interest score is high enough
            recommendations = []
            if conversation.interest_score > 30:  # Only recommend if some interest
                try:
                    recommendations = await self.recommendation_engine.get_personalized_recommendations(
                        conversation_id, db, current_message=message, limit=3
                    )
                except Exception as e:
                    logging.error(f"Error getting recommendations: {e}")

            # Log interaction
            interaction = InteractionLog(
                conversation_id=conversation_id,
                user_message=message,
                bot_response=bot_response,
                interest_score=new_score,
                engagement_factors=engagement_factors
            )
            db.add(interaction)
            db.commit()

            return {
                'conversation_id': conversation_id,
                'bot_response': bot_response,
                'interest_score': new_score,
                'interest_score_change': score_change,
                'engagement_factors': engagement_factors,
                'recommendations': recommendations
            }

        except Exception as e:
            logging.error(f"Error processing message: {e}")
            raise

    def _calculate_interest_score_change(
            self,
            message: str,
            conversation: Conversation,
            db: Session
    ) -> tuple[int, List[str]]:
        """Calculate interest score change based on message analysis"""

        message_lower = message.lower()
        score_change = 0
        engagement_factors = []

        # Check for specific preferences
        specific_prefs_found = 0
        for keyword in self.specific_preference_keywords:
            if keyword in message_lower:
                specific_prefs_found += 1

        if specific_prefs_found > 0:
            score_change += self.ENGAGEMENT_FACTORS['specific_preferences']
            engagement_factors.append(f"Specific preferences mentioned ({specific_prefs_found} detected)")

        # Check for dietary restrictions
        dietary_found = False
        for keyword in self.dietary_keywords:
            if keyword in message_lower:
                dietary_found = True
                break

        if dietary_found:
            score_change += self.ENGAGEMENT_FACTORS['dietary_restrictions']
            engagement_factors.append("Dietary restrictions mentioned")

        # Check for budget mention
        budget_patterns = [
            r'under \$?(\d+)', r'below \$?(\d+)', r'less than \$?(\d+)',
            r'around \$?(\d+)', r'about \$?(\d+)', r'\$(\d+)'
        ]

        budget_mentioned = False
        for pattern in budget_patterns:
            if re.search(pattern, message_lower):
                budget_mentioned = True
                break

        if budget_mentioned:
            score_change += self.ENGAGEMENT_FACTORS['budget_mention']
            engagement_factors.append("Budget mentioned")

        # Check for mood indication
        mood_found = False
        for keyword in self.mood_keywords:
            if keyword in message_lower:
                mood_found = True
                break

        if mood_found:
            score_change += self.ENGAGEMENT_FACTORS['mood_indication']
            engagement_factors.append("Mood/feeling indicated")

        # Check for questions
        question_found = False
        for keyword in self.question_keywords:
            if keyword in message_lower:
                question_found = True
                break

        if question_found or '?' in message:
            score_change += self.ENGAGEMENT_FACTORS['question_asking']
            engagement_factors.append("Question asked")

        # Check for enthusiasm
        enthusiasm_found = 0
        for keyword in self.enthusiasm_keywords:
            if keyword in message_lower:
                enthusiasm_found += 1

        if enthusiasm_found > 0:
            score_change += self.ENGAGEMENT_FACTORS['enthusiasm_words']
            engagement_factors.append(f"Enthusiasm detected ({enthusiasm_found} positive words)")

        # Check for price inquiry (specific to price questions)
        price_inquiry_patterns = [
            'how much', 'what does it cost', 'price', 'cost', 'expensive',
            'how much is', 'what\'s the price'
        ]

        price_inquiry = False
        for pattern in price_inquiry_patterns:
            if pattern in message_lower:
                price_inquiry = True
                break

        if price_inquiry:
            score_change += self.ENGAGEMENT_FACTORS['price_inquiry']
            engagement_factors.append("Price inquiry detected")

        # Check for order intent
        order_intent = False
        for keyword in self.order_intent_keywords:
            if keyword in message_lower:
                order_intent = True
                break

        if order_intent:
            score_change += self.ENGAGEMENT_FACTORS['order_intent']
            engagement_factors.append("Order intent detected")

        # NEGATIVE FACTORS

        # Check for hesitation
        hesitation_found = False
        for keyword in self.hesitation_keywords:
            if keyword in message_lower:
                hesitation_found = True
                break

        if hesitation_found:
            score_change += self.NEGATIVE_FACTORS['hesitation']
            engagement_factors.append("Hesitation detected (-10)")

        # Check for budget concerns
        budget_concern = False
        for keyword in self.budget_concern_keywords:
            if keyword in message_lower and ('too' in message_lower or 'expensive' in message_lower):
                budget_concern = True
                break

        if budget_concern:
            score_change += self.NEGATIVE_FACTORS['budget_concern']
            engagement_factors.append("Budget concern detected (-15)")

        # Check for rejection
        rejection_patterns = [
            "i don't like", "not interested", "no thanks", "don't want",
            "hate", "dislike", "not for me", "pass"
        ]

        rejection_found = False
        for pattern in rejection_patterns:
            if pattern in message_lower:
                rejection_found = True
                break

        if rejection_found:
            score_change += self.NEGATIVE_FACTORS['rejection']
            engagement_factors.append("Rejection detected (-25)")

        return score_change, engagement_factors

    def _extract_preferences(self, message: str) -> Dict[str, List[str]]:
        """Extract preferences from user message"""

        message_lower = message.lower()

        # Extract specific food preferences
        specific_prefs = []
        for keyword in self.specific_preference_keywords:
            if keyword in message_lower:
                specific_prefs.append(keyword)

        # Extract dietary restrictions
        dietary = []
        for keyword in self.dietary_keywords:
            if keyword in message_lower:
                dietary.append(keyword)

        # Extract moods
        moods = []
        mood_map = {
            'adventurous': ['adventurous', 'adventure', 'try something new'],
            'comfort': ['comfort', 'cozy', 'familiar'],
            'healthy': ['healthy', 'light', 'fresh'],
            'indulgent': ['indulgent', 'rich', 'treat myself'],
            'quick': ['quick', 'fast', 'hurry'],
            'fancy': ['fancy', 'special', 'gourmet']
        }

        for mood, keywords in mood_map.items():
            for keyword in keywords:
                if keyword in message_lower:
                    moods.append(mood)
                    break

        return {
            'specific_prefs': specific_prefs,
            'dietary': dietary,
            'moods': moods
        }