import streamlit as st
import pandas as pd
from datetime import datetime

def generate_analytics():
    """
    Generate analytics data from session state
    
    Returns:
        dict: Analytics data formatted for display
    """
    analytics_data = {}
    
    # Get session duration
    start_time = st.session_state.analytics.get('session_start', datetime.now())
    current_time = datetime.now()
    duration = current_time - start_time
    hours, remainder = divmod(duration.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    analytics_data['session_duration'] = f"{hours}h {minutes}m {seconds}s"
    
    # Popular topics
    if st.session_state.analytics['common_topics']:
        # Sort topics by frequency
        sorted_topics = dict(sorted(
            st.session_state.analytics['common_topics'].items(), 
            key=lambda x: x[1], 
            reverse=True
        ))
        
        # Create a DataFrame for display
        analytics_data['topics_df'] = pd.DataFrame({
            'Topic': list(sorted_topics.keys()),
            'Frequency': list(sorted_topics.values())
        }).head(5)  # Top 5 topics
        
        analytics_data['common_topics'] = sorted_topics
    else:
        analytics_data['topics_df'] = pd.DataFrame(columns=['Topic', 'Frequency'])
        analytics_data['common_topics'] = {}
    
    # Interaction counts
    analytics_data['general_count'] = st.session_state.analytics['general_interactions']
    analytics_data['document_count'] = st.session_state.analytics['document_interactions']
    analytics_data['total_count'] = analytics_data['general_count'] + analytics_data['document_count']
    
    # Calculate percentages for charts
    if analytics_data['total_count'] > 0:
        analytics_data['general_percent'] = (analytics_data['general_count'] / analytics_data['total_count']) * 100
        analytics_data['document_percent'] = (analytics_data['document_count'] / analytics_data['total_count']) * 100
    else:
        analytics_data['general_percent'] = 0
        analytics_data['document_percent'] = 0
    
    return analytics_data

def get_term_frequencies(min_count=2):
    """
    Get term frequencies from analytics
    
    Args:
        min_count (int): Minimum count to include a term
        
    Returns:
        dict: Dictionary of terms and their frequencies
    """
    term_freq = {}
    
    for term, count in st.session_state.analytics['term_frequency'].items():
        if count >= min_count:
            term_freq[term] = count
    
    # Sort by frequency
    term_freq = dict(sorted(term_freq.items(), key=lambda x: x[1], reverse=True))
    
    return term_freq