import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from backend.models import Product, Conversation, InteractionLog, ProductRecommendation
import random
import re


class RecommendationEngine:
    def __init__(self):
        self.recommendation_weights = {
            'current_request_match': 0.4,  # Highest weight for current request
            'preference_match': 0.2,
            'mood_match': 0.15,
            'dietary_compatibility': 0.15,
            'budget_fit': 0.05,
            'popularity': 0.05
        }

        # Keywords for different food categories
        self.category_keywords = {
            'burgers': ['burger', 'hamburger', 'cheeseburger', 'beef burger', 'chicken burger'],
            'pizza': ['pizza', 'margherita', 'pepperoni', 'cheese pizza'],
            'tacos': ['taco', 'burrito', 'quesadilla', 'mexican'],
            'desserts': ['dessert', 'cake', 'ice cream', 'cookie', 'sweet', 'chocolate', 'pie'],
            'salads': ['salad', 'caesar', 'garden', 'healthy', 'greens'],
            'drinks': ['drink', 'beverage', 'soda', 'juice', 'coffee', 'tea'],
            'sandwiches': ['sandwich', 'sub', 'wrap', 'panini'],
            'pasta': ['pasta', 'spaghetti', 'fettuccine', 'lasagna', 'ravioli'],
            'chicken': ['chicken', 'wings', 'nuggets', 'fried chicken'],
            'seafood': ['fish', 'shrimp', 'salmon', 'seafood', 'lobster']
        }

        # STRICT dietary restrictions - products containing these are EXCLUDED
        self.dietary_exclusions = {
            'vegetarian': ['beef', 'pork', 'chicken', 'turkey', 'fish', 'seafood', 'meat', 'bacon', 'ham', 'sausage'],
            'vegan': ['beef', 'pork', 'chicken', 'turkey', 'fish', 'seafood', 'meat', 'dairy', 'cheese', 'milk',
                      'butter', 'cream', 'egg', 'honey'],
            'gluten-free': ['wheat', 'gluten', 'bread', 'pasta', 'flour', 'barley', 'rye'],
            'dairy-free': ['milk', 'cheese', 'butter', 'cream', 'yogurt', 'dairy'],
            'keto': ['bread', 'pasta', 'rice', 'potato', 'sugar', 'flour'],
            'low-carb': ['bread', 'pasta', 'rice', 'potato', 'sugar', 'flour', 'carbs']
        }

        # Enhanced dietary keywords with variations
        self.dietary_detection_keywords = {
            'vegetarian': ['vegetarian', 'veg', 'veggie', 'no meat', 'plant-based'],
            'vegan': ['vegan', 'plant-based', 'no animal products', 'dairy-free and vegetarian'],
            'gluten-free': ['gluten-free', 'gluten free', 'no gluten', 'celiac'],
            'dairy-free': ['dairy-free', 'dairy free', 'no dairy', 'lactose-free', 'no milk'],
            'keto': ['keto', 'ketogenic', 'low-carb', 'no carbs'],
            'low-carb': ['low-carb', 'low carb', 'no carbs', 'carb-free']
        }

    def extract_food_preferences_from_message(self, message: str) -> Dict[str, Any]:
        """Extract food preferences from user's current message with enhanced dietary detection"""
        message_lower = message.lower()

        # Extract categories
        detected_categories = []
        for category, keywords in self.category_keywords.items():
            for keyword in keywords:
                if keyword in message_lower:
                    detected_categories.append(category)
                    break

        # Extract price preferences
        budget_info = None
        price_patterns = [
            r'under \$?(\d+)',
            r'below \$?(\d+)',
            r'less than \$?(\d+)',
            r'around \$?(\d+)',
            r'about \$?(\d+)'
        ]

        for pattern in price_patterns:
            match = re.search(pattern, message_lower)
            if match:
                price = float(match.group(1))
                if 'under' in pattern or 'below' in pattern or 'less than' in pattern:
                    budget_info = f"under ${price}"
                else:
                    budget_info = f"around ${price}"
                break

        # ENHANCED dietary preference detection
        detected_dietary = []
        for dietary_type, keywords in self.dietary_detection_keywords.items():
            for keyword in keywords:
                if keyword in message_lower:
                    detected_dietary.append(dietary_type)
                    break

        # Extract mood/occasion
        mood_keywords = {
            'comfort': ['comfort', 'cozy', 'warm'],
            'healthy': ['healthy', 'light', 'fresh', 'clean'],
            'indulgent': ['indulgent', 'rich', 'decadent', 'treat'],
            'spicy': ['spicy', 'hot', 'kick'],
            'quick': ['quick', 'fast', 'grab'],
            'fancy': ['fancy', 'special', 'gourmet']
        }

        detected_moods = []
        for mood, keywords in mood_keywords.items():
            for keyword in keywords:
                if keyword in message_lower:
                    detected_moods.append(mood)
                    break

        return {
            'categories': detected_categories,
            'budget': budget_info,
            'dietary': detected_dietary,
            'moods': detected_moods
        }

    def _strict_dietary_filter(self, products: List[Product], dietary_restrictions: List[str]) -> List[Product]:
        """Apply STRICT dietary filtering - exclude products that don't meet requirements"""
        if not dietary_restrictions:
            return products

        filtered_products = []

        for product in products:
            is_suitable = True

            for restriction in dietary_restrictions:
                # Check if product has the required dietary tag
                product_dietary_tags = [tag.lower() for tag in (product.dietary_tags or [])]

                if restriction.lower() not in product_dietary_tags:
                    # If the required dietary tag is missing, check ingredients and description for exclusions
                    product_text = f"{product.name} {product.description} {' '.join(product.ingredients or [])}".lower()

                    # Check if product contains excluded ingredients
                    exclusions = self.dietary_exclusions.get(restriction, [])
                    for exclusion in exclusions:
                        if exclusion in product_text:
                            is_suitable = False
                            break

                    # Special case: if no dietary tag and no exclusions found,
                    # still exclude for strict dietary requirements
                    if restriction in ['vegetarian', 'vegan'] and restriction.lower() not in product_dietary_tags:
                        is_suitable = False

                if not is_suitable:
                    break

            if is_suitable:
                filtered_products.append(product)

        return filtered_products

    async def get_personalized_recommendations(
            self,
            conversation_id: str,
            db: Session,
            current_message: str = "",
            limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Get personalized product recommendations with STRICT dietary filtering"""

        # Extract preferences from current message
        current_preferences = self.extract_food_preferences_from_message(current_message)

        # Get conversation context
        conversation = db.query(Conversation).filter(
            Conversation.conversation_id == conversation_id
        ).first()

        # Combine current dietary preferences with conversation history
        all_dietary_restrictions = current_preferences['dietary'].copy()
        if conversation and conversation.dietary_restrictions:
            for restriction in conversation.dietary_restrictions:
                if restriction not in all_dietary_restrictions:
                    all_dietary_restrictions.append(restriction)

        # Get all products
        all_products = db.query(Product).all()

        # STEP 1: Apply STRICT dietary filtering FIRST (most important)
        if all_dietary_restrictions:
            all_products = self._strict_dietary_filter(all_products, all_dietary_restrictions)

            # If no products match dietary requirements, return empty with explanation
            if not all_products:
                return [{
                    'product_id': 'no_match',
                    'name': 'No suitable products found',
                    'category': 'Notice',
                    'description': f"Sorry, no products match your {', '.join(all_dietary_restrictions)} requirements.",
                    'price': 0,
                    'dietary_tags': all_dietary_restrictions,
                    'mood_tags': [],
                    'spice_level': 0,
                    'popularity_score': 0,
                    'recommendation_score': 0,
                    'reasons': [f"Strict {', '.join(all_dietary_restrictions)} filtering applied"]
                }]

        # STEP 2: Filter by category
        if current_preferences['categories']:
            filtered_products = []
            for product in all_products:
                for category in current_preferences['categories']:
                    if (category.lower() in product.category.lower() or
                            any(keyword in product.name.lower() for keyword in
                                self.category_keywords.get(category, []))):
                        filtered_products.append(product)
                        break
            all_products = filtered_products if filtered_products else all_products

        # STEP 3: Apply budget filter
        if current_preferences['budget']:
            try:
                if 'under' in current_preferences['budget']:
                    max_price = float(current_preferences['budget'].replace('under $', ''))
                    all_products = [p for p in all_products if p.price <= max_price]
                elif 'around' in current_preferences['budget']:
                    target_price = float(current_preferences['budget'].replace('around $', ''))
                    min_price = target_price * 0.8
                    max_price = target_price * 1.2
                    all_products = [p for p in all_products if min_price <= p.price <= max_price]
            except:
                pass

        # STEP 4: Calculate recommendation scores
        recommendations = []
        for product in all_products:
            score = self._calculate_recommendation_score(product, conversation, current_preferences)
            # BONUS SCORE for meeting dietary requirements
            if all_dietary_restrictions:
                score += 20  # Bonus for meeting dietary requirements

            recommendations.append({
                'product': product,
                'score': score,
                'reasons': self._get_recommendation_reasons(product, conversation, current_preferences)
            })

        # Sort by score and get top recommendations
        recommendations.sort(key=lambda x: x['score'], reverse=True)
        top_recommendations = recommendations[:limit]

        # STEP 5: Fallback with dietary constraints maintained
        if not top_recommendations or all(rec['score'] < 30 for rec in top_recommendations):
            if current_preferences['categories']:
                category = current_preferences['categories'][0]

                # Apply category filter
                fallback_products = db.query(Product).filter(
                    Product.category.ilike(f'%{category}%')
                ).order_by(Product.popularity_score.desc()).all()

                # Apply dietary filter to fallback products too
                if all_dietary_restrictions:
                    fallback_products = self._strict_dietary_filter(fallback_products, all_dietary_restrictions)

                if fallback_products:
                    top_recommendations = [
                        {
                            'product': product,
                            'score': (product.popularity_score or 50) + 20,  # Bonus for dietary compliance
                            'reasons': [f'Popular {category} option that meets your dietary requirements',
                                        'High customer rating']
                        }
                        for product in fallback_products[:limit]
                    ]

        # Log recommendations
        try:
            for rec in top_recommendations:
                if rec['product'].__class__.__name__ == 'Product':  # Skip "no match" entries
                    existing_rec = db.query(ProductRecommendation).filter(
                        and_(
                            ProductRecommendation.conversation_id == conversation_id,
                            ProductRecommendation.product_id == rec['product'].product_id
                        )
                    ).first()

                    if not existing_rec:
                        new_rec = ProductRecommendation(
                            conversation_id=conversation_id,
                            product_id=rec['product'].product_id,
                            recommendation_score=rec['score'],
                            reason=', '.join(rec['reasons'])
                        )
                        db.add(new_rec)
            db.commit()
        except Exception as e:
            print(f"Error logging recommendations: {e}")

        # Format response
        return [
            {
                'product_id': rec['product'].product_id,
                'name': rec['product'].name,
                'category': rec['product'].category,
                'description': rec['product'].description,
                'price': rec['product'].price,
                'dietary_tags': rec['product'].dietary_tags,
                'mood_tags': rec['product'].mood_tags,
                'spice_level': rec['product'].spice_level,
                'popularity_score': rec['product'].popularity_score,
                'recommendation_score': rec['score'],
                'reasons': rec['reasons']
            }
            for rec in top_recommendations if hasattr(rec['product'], 'product_id')
        ]

    def _calculate_recommendation_score(self, product: Product, conversation: Conversation,
                                        current_preferences: Dict) -> float:
        """Calculate recommendation score - ENHANCED for dietary compliance"""

        score = 0.0

        # Current request matching (highest priority)
        current_request_score = 0

        # Category matching
        if current_preferences['categories']:
            for category in current_preferences['categories']:
                if (category.lower() in product.category.lower() or
                        any(keyword in product.name.lower() for keyword in self.category_keywords.get(category, []))):
                    current_request_score += 80
                    break

        # ENHANCED dietary matching - STRICT compliance
        if current_preferences['dietary']:
            product_dietary_tags = [tag.lower() for tag in (product.dietary_tags or [])]
            for dietary in current_preferences['dietary']:
                if dietary.lower() in product_dietary_tags:
                    current_request_score += 50  # Higher score for dietary compliance
                else:
                    # If dietary requirement not met, significantly reduce score
                    current_request_score -= 30

        # Mood matching from current request
        if current_preferences['moods']:
            for mood in current_preferences['moods']:
                if mood in (product.mood_tags or []):
                    current_request_score += 15

        current_request_score = max(0, min(current_request_score, 100))
        score += current_request_score * self.recommendation_weights['current_request_match']

        # Historical preference matching
        if conversation:
            user_preferences = conversation.user_preferences or []
            preference_matches = 0
            for pref in user_preferences:
                if (pref.lower() in product.name.lower() or
                        pref.lower() in product.description.lower() or
                        pref in (product.dietary_tags or []) or
                        pref in (product.mood_tags or [])):
                    preference_matches += 1

            preference_score = min(preference_matches * 20, 100)
            score += preference_score * self.recommendation_weights['preference_match']

            # Mood matching from conversation
            user_moods = conversation.mood_tags or []
            mood_matches = len(set(user_moods) & set(product.mood_tags or []))
            mood_score = min(mood_matches * 30, 100)
            score += mood_score * self.recommendation_weights['mood_match']

            # STRICT dietary compatibility
            dietary_restrictions = conversation.dietary_restrictions or []
            dietary_score = 100

            for restriction in dietary_restrictions:
                # Check allergens
                if restriction in (product.allergens or []):
                    dietary_score = 0
                    break
                # Check dietary tags compliance
                product_dietary_tags = [tag.lower() for tag in (product.dietary_tags or [])]
                if restriction.lower() not in product_dietary_tags:
                    # Check if product contains excluded ingredients
                    product_text = f"{product.name} {product.description} {' '.join(product.ingredients or [])}".lower()
                    exclusions = self.dietary_exclusions.get(restriction, [])
                    for exclusion in exclusions:
                        if exclusion in product_text:
                            dietary_score = 0
                            break
                    if dietary_score == 0:
                        break

            score += dietary_score * self.recommendation_weights['dietary_compatibility']

            # Budget fit
            budget_score = 100
            budget_range = current_preferences['budget'] or getattr(conversation, 'budget_range', None)
            if budget_range:
                try:
                    if "under" in str(budget_range).lower():
                        budget_limit = float(str(budget_range).lower().replace("under", "").replace("$", "").strip())
                        if product.price <= budget_limit:
                            budget_score = 100
                        else:
                            budget_score = max(0, 100 - (product.price - budget_limit) * 10)
                    elif "around" in str(budget_range).lower():
                        target_price = float(str(budget_range).lower().replace("around", "").replace("$", "").strip())
                        price_diff = abs(product.price - target_price)
                        budget_score = max(0, 100 - price_diff * 5)
                except:
                    budget_score = 100

            score += budget_score * self.recommendation_weights['budget_fit']

        # Popularity score
        popularity_score = product.popularity_score or 50
        score += popularity_score * self.recommendation_weights['popularity']

        return round(score, 2)

    def _get_recommendation_reasons(self, product: Product, conversation: Conversation,
                                    current_preferences: Dict) -> List[str]:
        """Get reasons why this product is recommended - ENHANCED for dietary"""

        reasons = []

        # Current request reasons
        if current_preferences['categories']:
            for category in current_preferences['categories']:
                if category.lower() in product.category.lower():
                    reasons.append(f"Perfect {category} match for your request")
                    break

        # ENHANCED dietary reasons
        if current_preferences['dietary']:
            product_dietary_tags = [tag.lower() for tag in (product.dietary_tags or [])]
            for dietary in current_preferences['dietary']:
                if dietary.lower() in product_dietary_tags:
                    reasons.append(f"✅ Meets your {dietary} requirements")

        if current_preferences['moods']:
            for mood in current_preferences['moods']:
                if mood in (product.mood_tags or []):
                    reasons.append(f"Great for a {mood} meal")

        # Historical preferences
        if conversation:
            user_preferences = getattr(conversation, 'user_preferences', []) or []
            for pref in user_preferences:
                if (pref.lower() in product.name.lower() or
                        pref.lower() in product.description.lower()):
                    reasons.append(f"Matches your preference for {pref}")
                    break

            # Budget fit
            budget_range = current_preferences['budget'] or getattr(conversation, 'budget_range', None)
            if budget_range and "under" in str(budget_range).lower():
                try:
                    budget_limit = float(str(budget_range).lower().replace("under", "").replace("$", "").strip())
                    if product.price <= budget_limit:
                        reasons.append(f"Within your ${budget_limit} budget")
                except:
                    pass

        # Product features
        if product.chef_special:
            reasons.append("Chef's special recommendation")

        if product.limited_time:
            reasons.append("Limited time offer")

        if product.popularity_score and product.popularity_score > 80:
            reasons.append("Highly popular choice")

        return reasons[:3]

    def get_filtered_products(
            self,
            db: Session,
            category: Optional[str] = None,
            min_price: Optional[float] = None,
            max_price: Optional[float] = None,
            dietary_tags: Optional[str] = None,
            mood_tags: Optional[str] = None
    ) -> List[Product]:
        """Get products with STRICT dietary filtering"""

        query = db.query(Product)

        if category:
            query = query.filter(Product.category.ilike(f'%{category}%'))

        if min_price is not None:
            query = query.filter(Product.price >= min_price)

        if max_price is not None:
            query = query.filter(Product.price <= max_price)

        # Get all products that match basic criteria
        products = query.order_by(Product.popularity_score.desc()).all()

        # Apply STRICT dietary filtering
        if dietary_tags:
            dietary_list = [tag.strip() for tag in dietary_tags.split(',')]
            products = self._strict_dietary_filter(products, dietary_list)

        # Filter by mood tags in Python
        if mood_tags:
            mood_list = [tag.strip() for tag in mood_tags.split(',')]
            filtered_products = []
            for product in products:
                product_mood_tags = product.mood_tags or []
                if any(tag in product_mood_tags for tag in mood_list):
                    filtered_products.append(product)
            products = filtered_products

        return products