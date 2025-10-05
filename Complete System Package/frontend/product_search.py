import streamlit as st
import requests
import pandas as pd
from typing import List, Dict, Any
import html
import re

# Backend API URL
API_BASE = "http://localhost:8000"


def clean_html_text(text):
    if not text:
        return ""
    clean_text = re.sub('<.*?>', '', str(text))
    clean_text = html.unescape(clean_text)
    clean_text = ' '.join(clean_text.split())
    return clean_text


def format_spice_level(level):
    """Format spice level with emojis"""
    if level is None: return "N/A"
    if level == 0:
        return "🟢 Mild"
    elif level <= 3:
        return "🟡 Medium"
    elif level <= 6:
        return "🟠 Spicy"
    elif level <= 8:
        return "🔴 Very Spicy"
    else:
        return "🌶️ Extremely Hot"


def render_product_search():
    """Render the product search and filtering interface"""
    st.title("🔍 Product Search & Discovery")
    st.markdown("Explore our diverse fast food menu with advanced filtering options.")

    # Search and filter section
    with st.expander("🎛️ Search & Filters", expanded=True):
        col1, col2 = st.columns(2)

        with col1:
            categories = [
                "All Categories", "Burgers", "Pizza", "Fried Chicken", "Tacos & Wraps",
                "Sides & Appetizers", "Beverages", "Desserts", "Salads & Healthy Options",
                "Breakfast Items", "Limited Time Specials"
            ]
            selected_category = st.selectbox("📂 Category", categories)
            price_range = st.slider("💰 Price Range", 0.0, 50.0, (0.0, 50.0), step=0.50)
            dietary_options = [
                "vegetarian", "vegan", "gluten-free", "dairy-free", "keto",
                "low-carb", "high-protein", "spicy", "mild"
            ]
            selected_dietary = st.multiselect("🥗 Dietary Tags", dietary_options)

        with col2:
            mood_options = [
                "comfort", "adventurous", "indulgent", "healthy", "quick",
                "satisfying", "energizing", "cozy", "exotic"
            ]
            selected_moods = st.multiselect("😋 Mood Tags", mood_options)
            col2_1, col2_2 = st.columns(2)
            with col2_1:
                chef_special = st.checkbox("👨‍🍳 Chef Specials Only")
                limited_time = st.checkbox("⏰ Limited Time Only")
            with col2_2:
                spice_level = st.slider("🌶️ Max Spice Level", 0, 10, 10)
                sort_by = st.selectbox("📊 Sort By", [
                    "Popularity", "Price (Low to High)", "Price (High to Low)",
                    "Name (A-Z)", "Spice Level"
                ])

    if st.button("🔍 Search Products", type="primary"):
        search_products(
            category=None if selected_category == "All Categories" else selected_category,
            min_price=price_range[0],
            max_price=price_range[1],
            dietary_tags=selected_dietary,
            mood_tags=selected_moods,
            chef_special=chef_special,
            limited_time=limited_time,
            spice_level=spice_level,
            sort_by=sort_by
        )

    if "search_results" in st.session_state and st.session_state.search_results:
        display_search_results(st.session_state.search_results)
    else:
        # Initial load or empty search
        search_products(None, 0.0, 50.0, [], [], False, False, 10, "Popularity")
        if "search_results" in st.session_state and st.session_state.search_results:
            display_search_results(st.session_state.search_results)


def search_products(category, min_price, max_price, dietary_tags, mood_tags,
                    chef_special, limited_time, spice_level, sort_by):
    """Search products and apply filters"""
    try:
        params = {}
        if category: params["category"] = category
        if min_price > 0: params["min_price"] = min_price
        if max_price < 50: params["max_price"] = max_price
        if dietary_tags: params["dietary_tags"] = ",".join(dietary_tags)
        if mood_tags: params["mood_tags"] = ",".join(mood_tags)

        response = requests.get(f"{API_BASE}/products", params=params)
        if response.status_code == 200:
            products = response.json()

            # Apply client-side filters
            if chef_special:
                products = [p for p in products if p.get("chef_special")]
            if limited_time:
                products = [p for p in products if p.get("limited_time")]
            if spice_level < 10:
                products = [p for p in products if p.get("spice_level", 0) <= spice_level]

            products = sort_products(products, sort_by)
            st.session_state.search_results = products
            if len(products) < 20:  # Don't show success message on initial load
                st.success(f"Found {len(products)} products matching your criteria!")
        else:
            st.error(f"Failed to search products: {response.text}")
    except Exception as e:
        st.error(f"Search error: {e}")


def sort_products(products: List[Dict], sort_by: str) -> List[Dict]:
    """Sort products based on selected criteria"""
    if sort_by == "Popularity":
        return sorted(products, key=lambda x: x.get("popularity_score", 0), reverse=True)
    elif sort_by == "Price (Low to High)":
        return sorted(products, key=lambda x: x.get("price", 0))
    elif sort_by == "Price (High to Low)":
        return sorted(products, key=lambda x: x.get("price", 0), reverse=True)
    elif sort_by == "Name (A-Z)":
        return sorted(products, key=lambda x: x.get("name", ""))
    elif sort_by == "Spice Level":
        return sorted(products, key=lambda x: x.get("spice_level", 0), reverse=True)
    return products


def display_search_results(products: List[Dict]):
    """Display search results in a grid layout"""
    st.subheader(f"🍽️ Search Results ({len(products)} items)")
    if not products:
        st.info("No products found matching your criteria. Try adjusting your filters.")
        return

    items_per_page = 9
    total_pages = (len(products) + items_per_page - 1) // items_per_page
    page_products = products

    if total_pages > 1:
        page = st.number_input("Page", min_value=1, max_value=total_pages, value=1, key="results_page")
        start_idx = (page - 1) * items_per_page
        end_idx = start_idx + items_per_page
        page_products = products[start_idx:end_idx]

    cols_per_row = 3
    for i in range(0, len(page_products), cols_per_row):
        cols = st.columns(cols_per_row)
        for j, product in enumerate(page_products[i:i + cols_per_row]):
            with cols[j]:
                # Use a unique key for each card based on its position and ID
                display_product_card(product, key_prefix=f"page_{i + j}")


# CHANGED: This function is completely rewritten to use native Streamlit components
def display_product_card(product: Dict[str, Any], key_prefix: str):
    """Display a single product card using native Streamlit components."""

    with st.container(border=True):
        # --- TITLE and BADGES ---
        title_cols = st.columns([0.7, 0.3])
        with title_cols[0]:
            st.subheader(product.get('name', ''))
        with title_cols[1]:
            # Display badges using st.markdown for better layout control
            badge_html = ""
            if product.get("chef_special"):
                badge_html += '<span style="background: gold; color: black; padding: 2px 8px; border-radius: 10px; font-size: 0.7em; margin-right: 5px;">Chef Special</span>'
            if product.get("limited_time"):
                badge_html += '<span style="background: red; color: white; padding: 2px 8px; border-radius: 10px; font-size: 0.7em;">Limited</span>'
            st.markdown(f'<div style="text-align: right;">{badge_html}</div>', unsafe_allow_html=True)

        # --- DESCRIPTION and DETAILS ---
        description = product.get('description', '')
        st.caption(f"{product.get('category', '')} | {product.get('calories', 'N/A')} Calories")
        st.write(description[:120] + ('...' if len(description) > 120 else ''))

        # --- PRICE and RATING ---
        metric_cols = st.columns(2)
        with metric_cols[0]:
            st.metric("Price", f"${product.get('price', 0):.2f}")
        with metric_cols[1]:
            st.metric("Popularity", f"⭐ {product.get('popularity_score', 0)}/100")

        # --- EXPANDABLE FULL DETAILS ---
        with st.expander("Full Details"):
            st.write("**Full Description:**")
            st.write(description)

            st.write("**Ingredients:**")
            st.write(", ".join(product.get('ingredients', [])) or "Not specified")

            st.write("**Dietary Tags:**")
            st.write(", ".join(product.get('dietary_tags', [])) or "None specified")

            st.write("**Mood Tags:**")
            st.write(", ".join(product.get('mood_tags', [])) or "None specified")

            st.write("**Allergens:**")
            st.write(", ".join(product.get('allergens', [])) or "None listed")

        # --- ACTION BUTTONS ---
        button_cols = st.columns(2)
        with button_cols[0]:
            if st.button("🛒 Add to Cart", key=f"cart_{key_prefix}_{product['product_id']}", use_container_width=True):
                st.toast(f"Added {product.get('name')} to cart!", icon="🛒")

        with button_cols[1]:
            if st.button("❤️ Favorite", key=f"fav_{key_prefix}_{product['product_id']}", use_container_width=True):
                st.toast(f"Added {product.get('name')} to favorites!", icon="❤️")


# This function is not used in this file but kept for modularity
def get_product_details(product_id: str):
    """Get detailed information about a specific product"""
    try:
        response = requests.get(f"{API_BASE}/products/{product_id}")
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        st.error(f"Error loading product details: {e}")
        return None