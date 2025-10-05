import streamlit as st
import requests
import json
from typing import Dict, Any, List
import uuid

# Backend API URL
API_BASE = "http://localhost:8000"


def render_chat_interface():
    """Render the main chat interface"""

    st.title("🍔 FoodieBot - AI Food Assistant")
    st.markdown("Welcome! I'm here to help you find the perfect food. Tell me what you're craving!")

    # Initialize session state
    if "conversation_id" not in st.session_state:
        st.session_state.conversation_id = None
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "interest_score" not in st.session_state:
        st.session_state.interest_score = 0
    if "recommendations" not in st.session_state:
        st.session_state.recommendations = []
    if "button_counter" not in st.session_state:
        st.session_state.button_counter = 0

    # Sidebar for conversation info
    with st.sidebar:
        st.header("Conversation Info")

        # Interest Score Display
        st.metric("Interest Score", f"{st.session_state.interest_score}%")

        if st.session_state.interest_score > 0:
            # Visual interest score bar
            progress_bar = st.progress(st.session_state.interest_score / 100)

            # Color coding
            if st.session_state.interest_score >= 80:
                st.success("🔥 High Interest!")
            elif st.session_state.interest_score >= 60:
                st.warning("👀 Good Interest")
            elif st.session_state.interest_score >= 40:
                st.info("🤔 Some Interest")
            else:
                st.error("😐 Low Interest")

        # Conversation ID
        if st.session_state.conversation_id:
            st.text(f"Chat ID: {st.session_state.conversation_id[:8]}...")

        # Generate products button
        st.markdown("---")
        if st.button("🎲 Generate Products"):
            with st.spinner("Generating 100 fast food products..."):
                try:
                    response = requests.post(f"{API_BASE}/generate-products")
                    if response.status_code == 200:
                        result = response.json()
                        st.success(f"✅ {result['message']}")
                    else:
                        st.error("Failed to generate products")
                except Exception as e:
                    st.error(f"Error: {e}")

        # New conversation button
        if st.button("🔄 New Conversation"):
            st.session_state.conversation_id = None
            st.session_state.messages = []
            st.session_state.interest_score = 0
            st.session_state.recommendations = []
            st.session_state.button_counter = 0
            st.rerun()

    # Chat messages container
    chat_container = st.container()

    with chat_container:
        # Display conversation history
        for msg_idx, message in enumerate(st.session_state.messages):
            if message["role"] == "user":
                with st.chat_message("user"):
                    st.write(message["content"])
            else:
                with st.chat_message("assistant"):
                    st.write(message["content"])

                    # Display recommendations if available
                    if "recommendations" in message and message["recommendations"]:
                        st.markdown("### 🍽️ Recommended for you:")
                        display_recommendations(message["recommendations"], context=f"history_{msg_idx}")

    # Chat input
    if prompt := st.chat_input("What are you craving today?"):
        # Add user message to chat
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Display user message
        with st.chat_message("user"):
            st.write(prompt)

        # Get bot response
        with st.chat_message("assistant"):
            with st.spinner("FoodieBot is thinking..."):
                response = get_bot_response(prompt)

                if response:
                    # Update session state
                    st.session_state.conversation_id = response.get("conversation_id")
                    st.session_state.interest_score = response.get("interest_score", 0)
                    st.session_state.recommendations = response.get("recommendations", [])

                    # Display bot response
                    bot_message = response.get("bot_response", "Sorry, I couldn't process that.")
                    st.write(bot_message)

                    # Add bot message to chat history
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": bot_message,
                        "recommendations": response.get("recommendations", [])
                    })

                    # Display recommendations
                    recommendations = response.get("recommendations", [])
                    if recommendations:
                        st.markdown("### 🍽️ Recommended for you:")
                        display_recommendations(recommendations, context="current")

                    # Display engagement factors
                    engagement_factors = response.get("engagement_factors", [])
                    if engagement_factors:
                        with st.expander("🔍 Conversation Analysis"):
                            st.write("**Detected Engagement Factors:**")
                            for factor in engagement_factors:
                                st.write(f"• {factor}")

                            score_change = response.get("interest_score_change", 0)
                            if score_change > 0:
                                st.success(f"Interest Score increased by +{score_change}")
                            elif score_change < 0:
                                st.error(f"Interest Score decreased by {score_change}")
                            else:
                                st.info("Interest Score remained the same")
                else:
                    st.error("Failed to get response from FoodieBot")

        # Auto-scroll to bottom
        st.rerun()


def get_bot_response(message: str) -> Dict[str, Any]:
    """Get response from the bot API"""
    try:
        payload = {
            "message": message,
            "conversation_id": st.session_state.conversation_id
        }

        response = requests.post(
            f"{API_BASE}/chat",
            params=payload,
            timeout=30
        )

        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API Error: {response.status_code}")
            return None

    except requests.exceptions.RequestException as e:
        st.error(f"Connection error: {e}")
        return None
    except Exception as e:
        st.error(f"Unexpected error: {e}")
        return None


def display_recommendations(recommendations: List[Dict[str, Any]], context: str = "default"):
    """Display product recommendations in cards"""

    if not recommendations:
        return

    # Create columns for recommendation cards
    cols = st.columns(min(len(recommendations), 3))

    for i, rec in enumerate(recommendations):
        with cols[i % 3]:
            # Product card
            with st.container():
                # Safely get values with defaults
                name = str(rec.get('name', 'Unknown Item'))
                category = str(rec.get('category', 'Unknown Category'))
                description = str(rec.get('description', 'No description available'))
                price = rec.get('price', 0)
                product_id = rec.get('product_id', f'product_{i}')
                score = rec.get('recommendation_score', 0)

                st.markdown(f"""
                <div style="
                    border: 1px solid #ddd; 
                    border-radius: 10px; 
                    padding: 15px; 
                    margin: 10px 0;
                    background: white;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                ">
                    <h4 style="margin: 0 0 10px 0; color: #333;">{name}</h4>
                    <p style="color: #666; font-size: 0.9em; margin: 5px 0;">{category}</p>
                    <p style="font-size: 0.8em; margin: 10px 0;">{description[:100]}...</p>
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-weight: bold; color: #2e8b57;">${price}</span>
                        <span style="font-size: 0.8em; color: #888;">Score: {score:.1f}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # Recommendation reasons
                reasons = rec.get('reasons', [])
                if reasons:
                    with st.expander(f"Why recommended? ({name[:20]}...)"):
                        for reason in reasons:
                            st.write(f"• {reason}")

                # Generate truly unique button key
                st.session_state.button_counter += 1
                button_key = f"add_cart_{context}_{product_id}_{i}_{st.session_state.button_counter}_{uuid.uuid4().hex[:8]}"

                if st.button(f"🛒 Add to Cart", key=button_key):
                    st.success(f"Added {name} to cart!")