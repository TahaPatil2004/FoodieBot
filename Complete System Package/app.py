from dotenv import load_dotenv
import os

load_dotenv()

db_url = os.getenv("DATABASE_URL")
api_key = os.getenv("GEMINI_API_KEY")


import streamlit as st
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from frontend.chat_interface import render_chat_interface
from frontend.analytics_dashboard import render_analytics_dashboard
from frontend.product_search import render_product_search

st.set_page_config(
    page_title="FoodieBot - AI Food Ordering System",
    page_icon="🍔",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Sidebar navigation
st.sidebar.title("🍔 FoodieBot")
st.sidebar.markdown("---")

page = st.sidebar.selectbox(
    "Navigate to:",
    ["Chat Interface", "Product Search", "Analytics Dashboard"]
)

if page == "Chat Interface":
    render_chat_interface()
elif page == "Product Search":
    render_product_search()
elif page == "Analytics Dashboard":
    render_analytics_dashboard()
