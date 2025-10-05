from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
import uvicorn

from .database import get_db, engine, Base
from .models import Product, Conversation, InteractionLog
from .gemini_service import GeminiService
from .conversation_service import ConversationService
from .recommendation_engine import RecommendationEngine
from .analytics_service import AnalyticsService
from .product_generator import ProductGenerator


Base.metadata.create_all(bind=engine)

app = FastAPI(title="FoodieBot API", description="AI Food Ordering System API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)

# Initialize services
gemini_service = GeminiService()
conversation_service = ConversationService(gemini_service)
recommendation_engine = RecommendationEngine()
analytics_service = AnalyticsService()
product_generator = ProductGenerator(gemini_service)

@app.get("/")
async def root():
    return {"message": "FoodieBot API is running!"}

@app.post("/generate-products")
async def generate_products(db: Session = Depends(get_db)):
    try:
        products = await product_generator.generate_all_products(db)
        return {"message": f"Generated {len(products)} products successfully", "count": len(products)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/products")
async def get_products(
    category: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    dietary_tags: Optional[str] = None,
    mood_tags: Optional[str] = None,
    db: Session = Depends(get_db)
):
    try:
        products = recommendation_engine.get_filtered_products(
            db, category, min_price, max_price, dietary_tags, mood_tags
        )

        return [p.to_dict() for p in products]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat")
async def chat_with_bot(
    message: str,
    conversation_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    try:
        response = await conversation_service.process_message(message, conversation_id, db)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

