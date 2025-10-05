from dotenv import load_dotenv
import os

load_dotenv()

db_url = os.getenv("DATABASE_URL")


import json
import logging
import asyncio
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from pydantic import BaseModel


from backend.models import Product
from backend.gemini_service import GeminiService
from backend.database import get_db



class ProductData(BaseModel):
    product_id: str
    name: str
    category: str
    description: str
    ingredients: List[str]
    price: float
    calories: int
    prep_time: str
    dietary_tags: List[str]
    mood_tags: List[str]
    allergens: List[str]
    popularity_score: int
    chef_special: bool
    limited_time: bool
    spice_level: int
    image_prompt: str


class ProductList(BaseModel):
    products: List[ProductData]


# The main class to generate products
class ProductGenerator:
    def __init__(self, gemini_service: GeminiService):
        self.gemini_service = gemini_service

        self.categories = {
            "Burgers": {"count": 10, "description": "classic, fusion, vegetarian burgers"},
            "Pizza": {"count": 10, "description": "traditional, gourmet, personal pizzas"},
            "Fried Chicken": {"count": 10, "description": "wings, tenders, sandwiches"},
            "Tacos & Wraps": {"count": 10, "description": "mexican, fusion, healthy options"},
            "Sides & Appetizers": {"count": 10, "description": "fries, onion rings, appetizers"},
            "Beverages": {"count": 10, "description": "sodas, shakes, specialty drinks"},
            "Desserts": {"count": 10, "description": "ice cream, cookies, pastries"},
            "Salads & Healthy Options": {"count": 10, "description": "fresh salads and healthy meals"},
            "Breakfast Items": {"count": 10, "description": "all-day breakfast options"},
            "Limited Time Specials": {"count": 10, "description": "seasonal and special menu items"}
        }

    async def generate_products_for_category(self, category: str, count: int, description: str) -> List[Dict[str, Any]]:
        """Generate products for a specific category"""

        system_instruction = f"""
        You are a creative fast food menu designer. Generate {count} unique and realistic fast food products for the {category} category.

        Requirements:
        - Each product must be unique and creative
        - Include fusion and international flavors where appropriate
        - Vary price ranges from budget to premium
        - Include different spice levels (0-10 scale)
        - Create appetizing and realistic descriptions
        - Assign appropriate dietary tags like: vegetarian, vegan, gluten-free, keto, spicy, etc.
        - Assign mood tags like: comfort, adventurous, indulgent, healthy, quick, satisfying
        - Include realistic calorie counts and prep times
        - Make some items chef specials or limited time offers
        - Generate descriptive image prompts for each item

        Product ID format: Use category prefix (BR for Burgers, PZ for Pizza, FC for Fried Chicken, TW for Tacos & Wraps, SA for Sides & Appetizers, BV for Beverages, DS for Desserts, SH for Salads & Healthy, BI for Breakfast Items, LT for Limited Time) followed by 3-digit number.

        Focus on: {description}
        """

        prompt = f"""
        Generate {count} diverse and creative {category} products with complete data structure.
        Each product should be realistic, appealing, and unique.
        Make sure to include a good mix of traditional and innovative options.
        """

        try:
            response = await self.gemini_service.generate_structured_response(
                prompt,
                ProductList,
                system_instruction
            )
            return response.get('products', [])
        except Exception as e:
            logging.error(f"Error generating products for {category}: {e}")
            return []

    async def generate_all_products(self, db: Session) -> List[Product]:
        """Generate all 100 products across all categories"""

        existing_count = db.query(Product).count()
        if existing_count >= 100:
            logging.info(f"Products already exist ({existing_count} found). Skipping generation.")
            return db.query(Product).all()

        all_products = []

        for category, info in self.categories.items():
            logging.info(f"Generating {info['count']} products for {category}...")

            try:
                products_data = await self.generate_products_for_category(
                    category, info['count'], info['description']
                )

                for product_data in products_data:
                    product = Product(
                        product_id=product_data['product_id'],
                        name=product_data['name'],
                        category=category,
                        description=product_data['description'],
                        ingredients=product_data['ingredients'],
                        price=product_data['price'],
                        calories=product_data['calories'],
                        prep_time=product_data['prep_time'],
                        dietary_tags=product_data['dietary_tags'],
                        mood_tags=product_data['mood_tags'],
                        allergens=product_data['allergens'],
                        popularity_score=product_data['popularity_score'],
                        chef_special=product_data['chef_special'],
                        limited_time=product_data['limited_time'],
                        spice_level=product_data['spice_level'],
                        image_prompt=product_data['image_prompt']
                    )

                    existing = db.query(Product).filter(Product.product_id == product.product_id).first()
                    if not existing:
                        db.add(product)
                        all_products.append(product)
                    else:
                        all_products.append(existing)

                db.commit()
                logging.info(f"Successfully generated {len(products_data)} products for {category}")

            except Exception as e:
                logging.error(f"Failed to generate products for {category}: {e}")
                db.rollback()
                continue

        logging.info(f"Total products generated: {len(all_products)}")
        return all_products

    async def regenerate_category(self, category: str, db: Session) -> List[Product]:
        """Regenerate products for a specific category"""

        if category not in self.categories:
            raise ValueError(f"Invalid category: {category}")

        db.query(Product).filter(Product.category == category).delete()
        db.commit()

        info = self.categories[category]
        products_data = await self.generate_products_for_category(
            category, info['count'], info['description']
        )

        products = []
        for product_data in products_data:
            product = Product(
                product_id=product_data['product_id'],
                name=product_data['name'],
                category=category,
                description=product_data['description'],
                ingredients=product_data['ingredients'],
                price=product_data['price'],
                calories=product_data['calories'],
                prep_time=product_data['prep_time'],
                dietary_tags=product_data['dietary_tags'],
                mood_tags=product_data['mood_tags'],
                allergens=product_data['allergens'],
                popularity_score=product_data['popularity_score'],
                chef_special=product_data['chef_special'],
                limited_time=product_data['limited_time'],
                spice_level=product_data['spice_level'],
                image_prompt=product_data['image_prompt']
            )

            db.add(product)
            products.append(product)

        db.commit()
        return products


async def main():
    """The main function to run the product generation script."""
    # Set up basic logging to see the progress from your script
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    print("--- Initializing services ---")
    gemini_service = GeminiService()
    product_generator = ProductGenerator(gemini_service)

    # Get a database session from your database setup
    print("--- Getting database session ---")
    db_session = next(get_db())

    print("--- Starting to generate all products. This may take several minutes... ---")
    try:
        await product_generator.generate_all_products(db_session)
        print("--- Process finished successfully. Check your database. ---")
    except Exception as e:
        print(f"An error occurred during product generation: {e}")
    finally:
        db_session.close()
        print("--- Database session closed. ---")


if __name__ == "__main__":
    # asyncio.run() is used to execute the async main function
    asyncio.run(main())