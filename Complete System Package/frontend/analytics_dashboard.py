import streamlit as st
import requests
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import time
from datetime import datetime, timedelta

# Backend API URL
API_BASE = "http://localhost:8000"

def render_analytics_dashboard():
    """Render the analytics dashboard"""
    
    st.title("📊 FoodieBot Analytics Dashboard")
    st.markdown("Real-time insights into conversations, products, and system performance")
    
    # Auto-refresh option
    auto_refresh = st.sidebar.checkbox("Auto-refresh (30s)", value=False)
    if auto_refresh:
        time.sleep(30)
        st.rerun()
    
    # Manual refresh button
    if st.sidebar.button("🔄 Refresh Data"):
        st.rerun()
    
    # Tab layout
    tab1, tab2, tab3, tab4 = st.tabs(["📈 Conversations", "🍔 Products", "🎯 Interest Scores", "⚡ Real-time"])
    
    with tab1:
        render_conversation_analytics()
    
    with tab2:
        render_product_analytics()
    
    with tab3:
        render_interest_score_analytics()
    
    with tab4:
        render_realtime_metrics()

def render_conversation_analytics():
    """Render conversation analytics tab"""
    
    st.header("📈 Conversation Analytics")
    
    try:
        response = requests.get(f"{API_BASE}/analytics/conversations")
        if response.status_code == 200:
            analytics = response.json()
            
            # Overview metrics
            st.subheader("Overview")
            overview = analytics.get("overview", {})
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric(
                    "Total Conversations", 
                    overview.get("total_conversations", 0),
                    delta=None
                )
            with col2:
                st.metric(
                    "Active Conversations", 
                    overview.get("active_conversations", 0)
                )
            with col3:
                st.metric(
                    "Total Interactions", 
                    overview.get("total_interactions", 0)
                )
            with col4:
                st.metric(
                    "Avg Interactions/Chat", 
                    overview.get("avg_interactions_per_conversation", 0)
                )
            
            # Recent activity
            st.subheader("Recent Activity (24h)")
            recent = analytics.get("recent_activity", {})
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric(
                    "New Conversations", 
                    recent.get("conversations_last_24h", 0)
                )
            with col2:
                st.metric(
                    "New Interactions", 
                    recent.get("interactions_last_24h", 0)
                )
            
            # Interest score distribution
            st.subheader("Interest Score Distribution")
            score_dist = analytics.get("interest_score_distribution", {})
            
            if score_dist:
                # Create a bar chart
                df_scores = pd.DataFrame(
                    list(score_dist.items()), 
                    columns=['Score Range', 'Count']
                )
                
                fig = px.bar(
                    df_scores, 
                    x='Score Range', 
                    y='Count',
                    title="Distribution of Interest Scores",
                    color='Count',
                    color_continuous_scale='viridis'
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # Top engagement factors
            st.subheader("Top Engagement Factors")
            engagement_factors = analytics.get("top_engagement_factors", [])
            
            if engagement_factors:
                df_factors = pd.DataFrame(engagement_factors)
                
                fig = px.bar(
                    df_factors, 
                    x='total_score', 
                    y='factor',
                    orientation='h',
                    title="Most Impactful Engagement Factors",
                    color='total_score',
                    color_continuous_scale='blues'
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
            
            # Conversation duration stats
            st.subheader("Conversation Duration Statistics")
            duration_stats = analytics.get("conversation_durations", {})
            
            if duration_stats.get("total_conversations_analyzed", 0) > 0:
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric(
                        "Avg Duration", 
                        f"{duration_stats.get('avg_duration_minutes', 0):.1f} min"
                    )
                with col2:
                    st.metric(
                        "Max Duration", 
                        f"{duration_stats.get('max_duration_minutes', 0):.1f} min"
                    )
                with col3:
                    st.metric(
                        "Min Duration", 
                        f"{duration_stats.get('min_duration_minutes', 0):.1f} min"
                    )
            
        else:
            st.error("Failed to load conversation analytics")
            
    except Exception as e:
        st.error(f"Error loading conversation analytics: {e}")

def render_product_analytics():
    """Render product analytics tab"""
    
    st.header("🍔 Product Analytics")
    
    try:
        response = requests.get(f"{API_BASE}/analytics/products")
        if response.status_code == 200:
            analytics = response.json()
            
            # Overview metrics
            st.subheader("Product Overview")
            overview = analytics.get("overview", {})
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Products", overview.get("total_products", 0))
            with col2:
                st.metric("Average Price", f"${overview.get('avg_price', 0):.2f}")
            with col3:
                st.metric("Chef Specials", overview.get("chef_specials", 0))
            with col4:
                st.metric("Limited Time", overview.get("limited_time_offers", 0))
            
            # Price range
            price_range = overview.get("price_range", {})
            st.info(f"Price Range: ${price_range.get('min', 0):.2f} - ${price_range.get('max', 0):.2f}")
            
            # Category distribution
            st.subheader("Category Distribution")
            category_dist = analytics.get("category_distribution", {})
            
            if category_dist:
                df_categories = pd.DataFrame(
                    list(category_dist.items()), 
                    columns=['Category', 'Count']
                )
                
                fig = px.pie(
                    df_categories, 
                    values='Count', 
                    names='Category',
                    title="Products by Category"
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # Top products by popularity
            st.subheader("Top Products by Popularity")
            top_products = analytics.get("top_products_by_popularity", [])
            
            if top_products:
                df_top = pd.DataFrame(top_products)
                
                fig = px.bar(
                    df_top, 
                    x='popularity_score', 
                    y='name',
                    orientation='h',
                    title="Most Popular Products",
                    color='price',
                    color_continuous_scale='greens',
                    hover_data=['category', 'price']
                )
                fig.update_layout(height=600)
                st.plotly_chart(fig, use_container_width=True)
            
            # Most recommended products
            st.subheader("Most Recommended Products")
            most_recommended = analytics.get("most_recommended_products", [])
            
            if most_recommended:
                df_recommended = pd.DataFrame(most_recommended)
                
                fig = px.bar(
                    df_recommended, 
                    x='recommendation_count', 
                    y='name',
                    orientation='h',
                    title="Products Recommended Most Often",
                    color='price',
                    color_continuous_scale='oranges',
                    hover_data=['category', 'price']
                )
                fig.update_layout(height=500)
                st.plotly_chart(fig, use_container_width=True)
            
            # Dietary tags distribution
            st.subheader("Dietary Tags Distribution")
            dietary_tags = analytics.get("dietary_tags_distribution", {})
            
            if dietary_tags:
                df_dietary = pd.DataFrame(
                    list(dietary_tags.items()), 
                    columns=['Tag', 'Count']
                ).head(10)  # Show top 10
                
                fig = px.bar(
                    df_dietary, 
                    x='Count', 
                    y='Tag',
                    orientation='h',
                    title="Most Common Dietary Tags",
                    color='Count',
                    color_continuous_scale='purples'
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
            
            # Spice level distribution
            st.subheader("Spice Level Distribution")
            spice_dist = analytics.get("spice_level_distribution", {})
            
            if spice_dist:
                df_spice = pd.DataFrame(
                    list(spice_dist.items()), 
                    columns=['Spice Level', 'Count']
                )
                df_spice['Spice Level'] = df_spice['Spice Level'].astype(int)
                df_spice = df_spice.sort_values('Spice Level')
                
                fig = px.bar(
                    df_spice, 
                    x='Spice Level', 
                    y='Count',
                    title="Products by Spice Level (0=Mild, 10=Extremely Hot)",
                    color='Count',
                    color_continuous_scale='reds'
                )
                st.plotly_chart(fig, use_container_width=True)
        
        else:
            st.error("Failed to load product analytics")
            
    except Exception as e:
        st.error(f"Error loading product analytics: {e}")

def render_interest_score_analytics():
    """Render interest score analytics tab"""
    
    st.header("🎯 Interest Score Analytics")
    
    try:
        response = requests.get(f"{API_BASE}/analytics/interest-scores")
        if response.status_code == 200:
            analytics = response.json()
            
            # Score change patterns
            st.subheader("Score Change Patterns")
            change_patterns = analytics.get("score_change_patterns", {})
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(
                    "Positive Changes", 
                    change_patterns.get("positive_changes", 0),
                    delta=f"+{change_patterns.get('avg_positive_change', 0):.1f} avg"
                )
            with col2:
                st.metric(
                    "Negative Changes", 
                    change_patterns.get("negative_changes", 0),
                    delta=f"{change_patterns.get('avg_negative_change', 0):.1f} avg"
                )
            with col3:
                st.metric(
                    "Neutral Changes", 
                    change_patterns.get("neutral_changes", 0)
                )
            
            # Create a donut chart for change distribution
            labels = ['Positive', 'Negative', 'Neutral']
            values = [
                change_patterns.get("positive_changes", 0),
                change_patterns.get("negative_changes", 0),
                change_patterns.get("neutral_changes", 0)
            ]
            
            if sum(values) > 0:
                fig = go.Figure(data=[go.Pie(
                    labels=labels, 
                    values=values, 
                    hole=0.3,
                    marker_colors=['green', 'red', 'gray']
                )])
                fig.update_layout(title="Interest Score Change Distribution")
                st.plotly_chart(fig, use_container_width=True)
            
            # High scoring conversations
            st.subheader("High-Scoring Conversations")
            high_score_convs = analytics.get("high_scoring_conversations", [])
            
            if high_score_convs:
                df_high_score = pd.DataFrame(high_score_convs)
                
                fig = px.scatter(
                    df_high_score,
                    x='total_interactions',
                    y='interest_score',
                    title="High-Scoring Conversations (80%+ Interest)",
                    hover_data=['conversation_id'],
                    color='interest_score',
                    color_continuous_scale='viridis',
                    size='total_interactions'
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Display top conversations table
                st.subheader("Top Conversations")
                display_df = df_high_score[['conversation_id', 'interest_score', 'total_interactions', 'started_at']].copy()
                display_df['conversation_id'] = display_df['conversation_id'].str[:8] + "..."
                st.dataframe(display_df, use_container_width=True)
            
            # Conversation progressions
            st.subheader("Interest Score Progressions")
            progressions = analytics.get("conversation_progressions", {})
            
            if progressions:
                # Create line chart for score progressions
                fig = go.Figure()
                
                for conv_id, progression in list(progressions.items())[:5]:  # Show top 5
                    scores = [p['score'] for p in progression]
                    timestamps = [p['timestamp'] for p in progression]
                    
                    fig.add_trace(go.Scatter(
                        x=list(range(len(scores))),
                        y=scores,
                        mode='lines+markers',
                        name=f"Chat {conv_id[:8]}...",
                        line=dict(width=2),
                        marker=dict(size=6)
                    ))
                
                fig.update_layout(
                    title="Interest Score Progression Over Interactions",
                    xaxis_title="Interaction Number",
                    yaxis_title="Interest Score",
                    height=400
                )
                st.plotly_chart(fig, use_container_width=True)
            
        else:
            st.error("Failed to load interest score analytics")
            
    except Exception as e:
        st.error(f"Error loading interest score analytics: {e}")

def render_realtime_metrics():
    """Render real-time metrics tab"""
    
    st.header("⚡ Real-time Metrics")
    
    # Auto-refresh for real-time data
    placeholder = st.empty()
    
    try:
        response = requests.get(f"{API_BASE}/analytics/conversations")
        realtime_response = requests.get(f"{API_BASE}/analytics/interest-scores")
        
        if response.status_code == 200:
            analytics = response.json()
            
            with placeholder.container():
                # Current metrics
                st.subheader("📊 Current System Status")
                
                overview = analytics.get("overview", {})
                recent = analytics.get("recent_activity", {})
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric(
                        "🗣️ Active Conversations", 
                        overview.get("active_conversations", 0),
                        delta=recent.get("conversations_last_24h", 0)
                    )
                
                with col2:
                    st.metric(
                        "💬 Recent Interactions", 
                        recent.get("interactions_last_24h", 0)
                    )
                
                with col3:
                    st.metric(
                        "🎯 Avg Interest Score", 
                        f"{overview.get('avg_interest_score', 0):.1f}%"
                    )
                
                with col4:
                    st.metric(
                        "📈 Total Conversations", 
                        overview.get("total_conversations", 0)
                    )
                
                # System health indicators
                st.subheader("🔍 System Health")
                
                # Calculate some health metrics
                total_convs = overview.get("total_conversations", 0)
                active_convs = overview.get("active_conversations", 0)
                avg_interactions = overview.get("avg_interactions_per_conversation", 0)
                avg_interest = overview.get("avg_interest_score", 0)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # Engagement health
                    if avg_interest >= 70:
                        st.success(f"🟢 High Engagement ({avg_interest:.1f}%)")
                    elif avg_interest >= 50:
                        st.warning(f"🟡 Medium Engagement ({avg_interest:.1f}%)")
                    else:
                        st.error(f"🔴 Low Engagement ({avg_interest:.1f}%)")
                
                with col2:
                    # Activity health
                    activity_ratio = active_convs / max(total_convs, 1) * 100
                    if activity_ratio >= 20:
                        st.success(f"🟢 High Activity ({activity_ratio:.1f}%)")
                    elif activity_ratio >= 10:
                        st.warning(f"🟡 Medium Activity ({activity_ratio:.1f}%)")
                    else:
                        st.info(f"🔵 Low Activity ({activity_ratio:.1f}%)")
                
                # Recent activity timeline
                st.subheader("📅 Activity Timeline")
                
                # Create a simple timeline visualization
                timeline_data = {
                    "Metric": ["New Conversations", "New Interactions"],
                    "Last 24h": [
                        recent.get("conversations_last_24h", 0),
                        recent.get("interactions_last_24h", 0)
                    ]
                }
                
                df_timeline = pd.DataFrame(timeline_data)
                
                fig = px.bar(
                    df_timeline,
                    x="Metric",
                    y="Last 24h",
                    title="Activity in Last 24 Hours",
                    color="Last 24h",
                    color_continuous_scale="blues"
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Live updates indicator
                st.subheader("🔄 Live Updates")
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                st.info(f"Last updated: {current_time}")
                
                # Auto-refresh countdown
                if st.checkbox("Enable auto-refresh"):
                    for i in range(30, 0, -1):
                        time.sleep(1)
                        st.write(f"Refreshing in {i} seconds...")
                    st.rerun()
        
        else:
            st.error("Failed to load real-time metrics")
            
    except Exception as e:
        st.error(f"Error loading real-time metrics: {e}")

# Utility functions for the analytics dashboard

def format_timestamp(timestamp_str):
    """Format timestamp for display"""
    try:
        dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        return dt.strftime("%Y-%m-%d %H:%M")
    except:
        return timestamp_str

def calculate_trend(current, previous):
    """Calculate trend percentage"""
    if previous == 0:
        return 0
    return ((current - previous) / previous) * 100
