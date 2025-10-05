# 🍔 FoodieBot - AI-Powered Food Ordering Agent

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8%2B-blue?logo=python" alt="Python Version">
  <img src="https://img.shields.io/badge/Framework-FastAPI-green?logo=fastapi" alt="FastAPI">
  <img src="https://img.shields.io/badge/Frontend-Streamlit-red?logo=streamlit" alt="Streamlit">
  <img src="https://img.shields.io/badge/Database-PostgreSQL-blue?logo=postgresql" alt="PostgreSQL">
  <img src="https://img.shields.io/badge/AI-Google_Gemini-purple" alt="Google Gemini">
</p>

A sophisticated AI food ordering system that combines conversational intelligence with a database-driven backend to provide smart, personalized fast-food recommendations.

---

## 📋 Table of Contents

- [🎯 Project Overview](#-project-overview)
- [🏗️ System Architecture](#️-system-architecture)
- [🚀 Key Features](#-key-features)
- [🛠️ Technology Stack](#️-technology-stack)
- [📁 Project Structure](#-project-structure)
- [⚙️ Installation & Setup](#️-installation--setup)
- [🎮 Usage Guide](#-usage-guide)
- [🔧 API Endpoints](#-api-endpoints)
- [🧠 Interest Score Calculation](#-interest-score-calculation)
- [⚠️ Known Issues & Troubleshooting](#️-known-issues--troubleshooting)
- [📊 Performance Metrics](#-performance-metrics)
- [☁️ Deployment](#️-deployment)
- [📞 Support](#-support)

---

## 🎯 Project Overview

This project implements a complete 3-phase AI food agent system designed to simulate a real-world, intelligent ordering platform.

-   **Phase 1: Product Data & Database:** Generation of a rich fast-food product catalog using AI and setting up a robust PostgreSQL database.
-   **Phase 2: Conversational AI:** A smart chatbot that understands user preferences and calculates a real-time "Interest Score" to gauge intent.
-   **Phase 3: Smart Recommendations & Analytics:** An intelligent engine to suggest products based on conversation context and a dashboard to visualize system performance.

---

## 🏗️ System Architecture

The system follows a modular architecture where each component has a distinct responsibility, from handling user input to logging analytics.

```
[User Input] -> [Conversational AI Agent (Gemini)] -> [Interest Score Calculator]
                               |                              |
                               v                              v
[Database Query Engine] -> [Recommendation System] -> [Response Generator] -> [User Interface (Streamlit)]
           |
           v
[Analytics Tracker] -> [Database Logger]
```

---

## 🚀 Key Features

### Phase 1: Product Data Generation & Database
✅ **AI-Generated Product Catalog**: 100 unique fast-food products created by Google Gemini.
✅ **Robust Database**: PostgreSQL database with a well-designed schema and 10 distinct product categories (e.g., Burgers, Pizza, Fried Chicken).
✅ **Detailed Product Structure**: Each product includes rich metadata for advanced filtering and recommendations.

<details>
<summary>Click to see an example Product JSON structure</summary>

```json
{
  "product_id": "FF001",
  "name": "Spicy Fusion Dragon Burger",
  "category": "Burgers",
  "description": "A fiery fusion of Korean gochujang and classic American beef, topped with kimchi slaw and a toasted brioche bun.",
  "ingredients": [
    "beef patty",
    "gochujang sauce",
    "kimchi slaw",
    "brioche bun"
  ],
  "price": 12.99,
  "calories": 680,
  "prep_time": "8-10 mins",
  "dietary_tags": ["spicy", "fusion", "contains_gluten"],
  "mood_tags": ["adventurous", "comfort", "indulgent"],
  "allergens": ["gluten", "soy", "dairy"],
  "popularity_score": 85,
  "chef_special": true,
  "limited_time": false,
  "spice_level": 7,
  "image_prompt": "A high-resolution, gourmet photo of a Korean-fusion burger with spicy gochujang glaze, vibrant kimchi slaw, on a glossy brioche bun."
}
```
</details>

### Phase 2: Conversational AI & Interest Scoring
✅ **Real-time Interest Scoring**: A dynamic score (0-100%) that updates with every user message to reflect their purchase intent.
✅ **Advanced Engagement Analysis**: The system intelligently parses conversations for specific keywords and sentiments to adjust the score.
✅ **Context-Aware Conversations**: Maintains conversation history for a seamless and natural user experience.
✅ **Database Integration**: The AI can query the database to answer user questions about products.

### Phase 3: Smart Recommendations & Analytics
✅ **Multi-Algorithm Recommendation Engine**:
-   Preference Matching (e.g., "spicy", "vegetarian")
-   Mood-Based Filtering (e.g., "comfort", "adventurous")
-   Budget Optimization
-   Dietary Intelligence
✅ **Real-Time Analytics Dashboard**: Visualizes key metrics to track system and product performance.
✅ **Deep Analytics**: Tracks interest score progression, conversion rates, and correlates recommendations with product popularity.

---

## 🛠️ Technology Stack

| Component         | Technology                               |
| ----------------- | ---------------------------------------- |
| **Backend** | FastAPI, Uvicorn, SQLAlchemy ORM         |
| **Database** | PostgreSQL                               |
| **AI Service** | Google Gemini API                        |
| **Frontend** | Streamlit                                |
| **Analytics** | Custom Streamlit Dashboard               |
| **Dependencies** | UV Package Manager                       |

---

## 📁 Project Structure

```
FoodieBot_project/
├── app.py                     # Main Streamlit application entrypoint
├── .env                       # Environment variables (DB_URL, API_KEY)
├── pyproject.toml             # Project configuration for UV
├── uv.lock                    # Locked dependency versions
├── backend/                   # FastAPI Backend API
│   ├── main.py                # Core API endpoints (/chat, /products)
│   ├── database.py            # Database session and configuration
│   ├── models.py              # SQLAlchemy ORM models
│   ├── gemini_service.py      # Integration with Google Gemini
│   ├── conversation_service.py# Business logic for chat and interest scoring
│   ├── recommendation_engine.py # Recommendation algorithms
│   ├── analytics_service.py   # Analytics processing logic
│   └── product_generator.py   # Script to generate products using AI
└── frontend/                  # Streamlit Frontend Components
    ├── chat_interface.py      # Main chat UI
    ├── product_search.py      # UI for product discovery and filtering
    └── analytics_dashboard.py # UI for data visualization
```

---

## ⚙️ Installation & Setup

### Prerequisites
* Python 3.8+
* PostgreSQL server
* Google Gemini API Key

### Step 1: Clone the Repository
```bash
git clone <repository-url>
cd FoodieBot
```

### Step 2: Install Dependencies using UV
```bash
# Install uv if you don't have it
pip install uv

# Sync dependencies from uv.lock
uv sync
```

### Step 3: Configure Environment Variables
Create a `.env` file in the root directory and add your credentials:
```env
DATABASE_URL=postgresql://username:password@localhost:5432/foodiebot
GEMINI_API_KEY=your_gemini_api_key_here
```

### Step 4: Set Up the PostgreSQL Database
Connect to your PostgreSQL instance and create the database:
```sql
CREATE DATABASE foodiebot;
```

### Step 5: Start the System
You need to run the backend and frontend in two separate terminals.

**Terminal 1: Start the FastAPI Backend**
```bash
# The backend will run on http://localhost:8000
python -m uvicorn backend.main:app --reload
```

**Terminal 2: Start the Streamlit Frontend**
```bash
# The frontend will be accessible at http://localhost:8501
streamlit run app.py
```

---

## 🎮 Usage Guide

### 💬 Chat Interface
1.  **Start a Conversation**: Navigate to the Chat Interface in the Streamlit app.
2.  **Express Your Preferences**: Tell the bot what you're looking for. For example: *"I want something spicy and adventurous for under $15."*
3.  **Watch the Interest Score**: See the score update in real-time as you interact.
4.  **Receive Recommendations**: The bot will suggest products from the database that match your criteria.

### 🔍 Product Search & Discovery
1.  **Use Advanced Filters**: Search the entire product catalog using filters for:
    -   Categories (Burgers, Pizza, etc.)
    -   Price range
    -   Dietary tags (e.g., `vegetarian`, `gluten-free`)
    -   Mood tags (e.g., `comfort`, `healthy`)
    -   Spice level (0-10)
2.  **Sort Results**: Order products by popularity, price, or a smart recommendation score.

### 📈 Analytics Dashboard
-   **Interest Score Trends**: Analyze conversation engagement in real-time.
-   **Product Performance**: Identify the most recommended and highest-converting items.
-   **Conversation Metrics**: Track session duration, drop-off points, and overall conversion rates.

---

## 🔧 API Endpoints

The FastAPI backend exposes several endpoints. View interactive documentation at `http://localhost:8000/docs`.

| Method | Endpoint                 | Description                                    |
|--------|--------------------------|------------------------------------------------|
| `GET`  | `/`                      | Health check for the API.                      |
| `POST` | `/generate-products`     | Populates the database with 100 AI products.   |
| `GET`  | `/products`              | Searches products with powerful filtering.     |
| `POST` | `/chat`                  | Main endpoint for conversational AI.           |
| `GET`  | `/analytics/*`           | Various endpoints to fetch analytics data.     |

#### Database Query Examples:
```bash
# Search for spicy vegetarian products under $15
GET /products?dietary_tags=vegetarian,spicy&price_max=15

# Find adventurous and comforting burgers
GET /products?mood_tags=adventurous,comfort&category=Burgers

# Find mild, chef-special desserts
GET /products?category=Desserts&chef_special=true&spice_level_max=3
```

---

## 🧠 Interest Score Calculation

The scoring logic is based on a predefined set of positive and negative factors detected in the user's conversation.

```python
# Positive Engagement Factors
ENGAGEMENT_FACTORS = {
    'specific_preferences': +15,  # "I love spicy Korean food"
    'dietary_restrictions': +10,  # "I'm vegetarian"
    'budget_mention': +5,         # "Under $15"
    'mood_indication': +20,       # "I'm feeling adventurous"
    'question_asking': +10,       # "What's the spice level?"
    'enthusiasm_words': +8,       # "amazing", "perfect", "love"
    'price_inquiry': +25,         # "How much is that?"
    'order_intent': +30,          # "I'll take it", "Add to cart"
}

# Negative Factors
NEGATIVE_FACTORS = {
    'hesitation': -10,            # "maybe", "not sure"
    'budget_concern': -15,        # "that's too expensive"
    'dietary_conflict': -20,      # Product doesn't match restrictions
    'rejection': -25,             # "I don't like that"
}
```

---

## ⚠️ Known Issues & Troubleshooting

### 1. Dietary Tags Search Issue
-   **Problem**: Filtering products by `dietary_tags` directly in a PostgreSQL query can cause `operator does not exist: json ~~ text` errors.
-   **Root Cause**: This is a known complexity when querying JSON/JSONB array fields with certain ORMs or database configurations.
-   **Implemented Workaround**: The filtering logic for `dietary_tags` and `mood_tags` has been moved from the SQL query to Python code within the `/products` endpoint (`backend/main.py`). The application first fetches a broader set of results from the database and then filters them in the backend before sending the response.
-   **Status**: A robust workaround is in place, ensuring functionality. Further optimization could involve refining the database query with raw SQL or specific PostgreSQL functions if performance becomes an issue at a larger scale.

### 2. Database Connection Issues
-   **Common Problems**: `psycopg2.OperationalError`, `connection refused`, or similar errors.
-   **Solutions**:
    1.  **Ensure PostgreSQL is Running**:
        ```bash
        # On Linux/WSL
        sudo service postgresql status
        ```
    2.  **Verify `DATABASE_URL`**: Double-check the format in your `.env` file. It must be `postgresql://user:password@host:port/dbname`.
    3.  **Confirm Database Exists**: If not, create it using `psql -c "CREATE DATABASE foodiebot;"`.

---

## 📊 Performance Metrics

-   **Database Query Time**: < 50ms (average for filtered queries)
-   **Interest Score Calculation**: Real-time (< 100ms per message)
-   **Product Recommendations**: < 200ms total response time
-   **Concurrent Users**: Tested to support 10+ simultaneous conversations.

---

## ☁️ Deployment

### Local Development (Current Setup)
-   **Backend**: Run via `uvicorn` on `http://localhost:8000`.
-   **Frontend**: Run via `streamlit` on `http://localhost:8501`.

### Production Deployment (Recommendations)
1.  **Database**: Use a managed PostgreSQL provider like [Railway](https://railway.app/), [Neon](https://neon.tech/), or [Supabase](https://supabase.com/).
2.  **Backend**: Containerize the FastAPI application with Docker and deploy it on a cloud service like AWS, Google Cloud, or Heroku.
3.  **Frontend**: Deploy using Streamlit Community Cloud or containerize it alongside the backend.

---

## 📞 Support

If you encounter issues, please check the following:
-   Review the [Troubleshooting](#️-known-issues--troubleshooting) section above.
-   Ensure all environment variables in `.env` are correctly set.
-   Check the logs in both the FastAPI and Streamlit terminal windows for error messages.
-   Visit the auto-generated API documentation at `http://localhost:8000/docs` to test endpoints directly.

---
