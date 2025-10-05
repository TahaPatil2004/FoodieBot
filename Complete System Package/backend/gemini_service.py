import json
import logging
import os
from typing import Dict, Any, List, Optional
from google import genai
from google.genai import types
from pydantic import BaseModel

class GeminiService:
    def __init__(self):
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY", "default_key"))
        self.model = "gemini-1.5-pro"

    async def generate_content(self, prompt: str, system_instruction: Optional[str] = None) -> str:
        """Generate content using Gemini API"""
        try:
            if system_instruction:
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction
                    )
                )
            else:
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=prompt
                )
            
            return response.text or "I apologize, but I couldn't generate a response at the moment."
        except Exception as e:
            logging.error(f"Gemini API error: {e}")
            return "I'm experiencing some technical difficulties. Please try again later."

    async def generate_structured_response(self, prompt: str, response_schema: BaseModel, system_instruction: str) -> Dict[str, Any]:
        """Generate structured JSON response using Gemini API"""
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    response_mime_type="application/json",
                    response_schema=response_schema
                )
            )
            
            if response.text:
                return json.loads(response.text)
            else:
                raise ValueError("Empty response from model")
        except Exception as e:
            logging.error(f"Gemini structured response error: {e}")
            raise Exception(f"Failed to generate structured response: {e}")

    async def analyze_conversation_sentiment(self, message: str) -> Dict[str, Any]:
        """Analyze the sentiment and engagement factors of a user message"""
        system_instruction = """
        You are an expert at analyzing customer conversations for a food ordering system.
        Analyze the user's message and identify engagement factors that would affect their interest score.
        
        Consider these positive factors:
        - Specific food preferences (+15)
        - Dietary restrictions mention (+10)
        - Budget mention (+5)
        - Mood indication (+20)
        - Asking questions (+10)
        - Enthusiasm words (+8)
        - Price inquiries (+25)
        - Order intent (+30)
        
        Consider these negative factors:
        - Hesitation (-10)
        - Budget concerns (-15)
        - Dietary conflicts (-20)
        - Rejection (-25)
        - Delayed responses (-5)
        
        Return the analysis with detected factors and their scores in a simple format.
        """
        
        class SentimentAnalysis(BaseModel):
            engagement_factors: str  # Comma-separated list
            total_score_change: int
            detected_preferences: str  # Comma-separated list
            detected_restrictions: str  # Comma-separated list
            budget_indication: str
            mood_indication: str
            enthusiasm_level: int  # 1-10 scale

        prompt = f"Analyze this customer message for engagement factors: '{message}'. Return engagement_factors, detected_preferences, and detected_restrictions as comma-separated strings. Use 'none' if nothing detected."
        
        try:
            result = await self.generate_structured_response(prompt, SentimentAnalysis, system_instruction)
            
            # Convert string lists back to arrays and create factor_scores
            engagement_factors = [f.strip() for f in result.get('engagement_factors', '').split(',') if f.strip() and f.strip() != 'none']
            detected_preferences = [p.strip() for p in result.get('detected_preferences', '').split(',') if p.strip() and p.strip() != 'none']
            detected_restrictions = [r.strip() for r in result.get('detected_restrictions', '').split(',') if r.strip() and r.strip() != 'none']
            
            # Create factor scores based on engagement factors
            factor_scores = {}
            for factor in engagement_factors:
                if 'preference' in factor.lower():
                    factor_scores[factor] = 15
                elif 'restriction' in factor.lower():
                    factor_scores[factor] = 10
                elif 'budget' in factor.lower():
                    factor_scores[factor] = 5 if 'concern' not in factor.lower() else -15
                elif 'mood' in factor.lower():
                    factor_scores[factor] = 20
                elif 'question' in factor.lower():
                    factor_scores[factor] = 10
                elif 'enthusiasm' in factor.lower():
                    factor_scores[factor] = 8
                elif 'price' in factor.lower():
                    factor_scores[factor] = 25
                elif 'order' in factor.lower():
                    factor_scores[factor] = 30
                elif 'hesitation' in factor.lower():
                    factor_scores[factor] = -10
                elif 'rejection' in factor.lower():
                    factor_scores[factor] = -25
                else:
                    factor_scores[factor] = 5  # Default positive score
            
            return {
                'engagement_factors': engagement_factors,
                'factor_scores': factor_scores,
                'total_score_change': result.get('total_score_change', 0),
                'detected_preferences': detected_preferences,
                'detected_restrictions': detected_restrictions,
                'budget_indication': result.get('budget_indication', '') if result.get('budget_indication', '') != 'none' else None,
                'mood_indication': result.get('mood_indication', '') if result.get('mood_indication', '') != 'none' else None,
                'enthusiasm_level': result.get('enthusiasm_level', 5)
            }
        except Exception as e:
            logging.error(f"Error in sentiment analysis: {e}")
            # Return a default structure if API fails
            return {
                'engagement_factors': [],
                'factor_scores': {},
                'total_score_change': 0,
                'detected_preferences': [],
                'detected_restrictions': [],
                'budget_indication': None,
                'mood_indication': None,
                'enthusiasm_level': 5
            }

    async def generate_bot_response(self, user_message: str, conversation_context: Dict[str, Any], recommended_products: List[Dict]) -> str:
        """Generate a natural bot response based on conversation context and recommendations"""
        
        context_str = f"""
        Conversation Context:
        - Current Interest Score: {conversation_context.get('interest_score', 0)}%
        - User Preferences: {conversation_context.get('preferences', [])}
        - Dietary Restrictions: {conversation_context.get('restrictions', [])}
        - Budget Range: {conversation_context.get('budget', 'Not specified')}
        - Mood Tags: {conversation_context.get('mood_tags', [])}
        
        Recommended Products: {json.dumps(recommended_products[:3], indent=2) if recommended_products else 'None available'}
        """
        
        system_instruction = """
        You are FoodieBot, a friendly and knowledgeable AI assistant for a fast food ordering system.
        Your personality is enthusiastic about food, helpful, and conversational.
        
        Guidelines:
        - Be natural and engaging in conversation
        - Ask follow-up questions to understand preferences better
        - Suggest products from the recommendations provided
        - Mention specific details about products (price, ingredients, etc.)
        - If interest score is low, try to re-engage the customer
        - If interest score is high, guide towards making a decision
        - Always be respectful of dietary restrictions and budget concerns
        """
        
        prompt = f"""
        {context_str}
        
        User Message: "{user_message}"
        
        Generate a helpful and engaging response that acknowledges the user's message and provides relevant suggestions based on the context and recommendations.
        """
        
        return await self.generate_content(prompt, system_instruction)
