"""
Streamlit Web Interface for Fantasy Football Draft AI

Provides a modern web interface for draft monitoring and recommendations.
"""

import streamlit as st
import pandas as pd
import time
import json
from datetime import datetime
from typing import Dict, List, Optional

# Add parent directory to path for imports
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from espn_api_connector import ESPNConnector
from ai.gpt_agent import GPTAgent
from prompts.prompt_builder import PromptBuilder
from utils.roster_eval import RosterEvaluator


def run_streamlit_app():
    """Main Streamlit application."""
    st.set_page_config(
        page_title="Fantasy Football Draft AI",
        page_icon="🏈",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS
    st.markdown("""
    <style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        color: #1f77b4;
        margin-bottom: 2rem;
    }
    .status-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .recommendation-card {
        background-color: #e8f4fd;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
        border-left: 4px solid #1f77b4;
    }
    .player-card {
        background-color: #f9f9f9;
        padding: 0.5rem;
        border-radius: 0.3rem;
        margin: 0.5rem 0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown('<h1 class="main-header">🏈 Fantasy Football Draft AI</h1>', unsafe_allow_html=True)
    
    # Initialize session state
    if 'initialized' not in st.session_state:
        st.session_state.initialized = False
        st.session_state.espn_connector = None
        st.session_state.gpt_agent = None
        st.session_state.prompt_builder = None
        st.session_state.roster_evaluator = None
        st.session_state.authenticated = False
        st.session_state.monitoring = False
    
    # Sidebar
    with st.sidebar:
        st.header("🎮 Controls")
        
        # Authentication section
        st.subheader("🔐 Authentication")
        if not st.session_state.authenticated:
            if st.button("🔑 Authenticate with ESPN"):
                with st.spinner("Authenticating..."):
                    try:
                        st.session_state.espn_connector = ESPNConnector()
                        if st.session_state.espn_connector.authenticate():
                            st.session_state.authenticated = True
                            st.success("✅ Authenticated successfully!")
                        else:
                            st.error("❌ Authentication failed!")
                    except Exception as e:
                        st.error(f"❌ Authentication error: {e}")
        else:
            st.success("✅ Authenticated")
            if st.button("🔓 Disconnect"):
                st.session_state.authenticated = False
                st.session_state.espn_connector = None
                st.rerun()
        
        # Initialize AI components
        if st.session_state.authenticated and not st.session_state.initialized:
            if st.button("🤖 Initialize AI"):
                with st.spinner("Initializing AI components..."):
                    try:
                        st.session_state.gpt_agent = GPTAgent()
                        st.session_state.prompt_builder = PromptBuilder()
                        st.session_state.roster_evaluator = RosterEvaluator()
                        st.session_state.initialized = True
                        st.success("✅ AI components ready!")
                    except Exception as e:
                        st.error(f"❌ AI initialization error: {e}")
        
        # Monitoring controls
        if st.session_state.initialized:
            st.subheader("📡 Draft Monitoring")
            
            if not st.session_state.monitoring:
                if st.button("▶️ Start Monitoring"):
                    st.session_state.monitoring = True
                    st.rerun()
            else:
                if st.button("⏹️ Stop Monitoring"):
                    st.session_state.monitoring = False
                    st.rerun()
            
            # Manual refresh
            if st.button("🔄 Refresh Now"):
                st.rerun()
    
    # Main content
    if not st.session_state.authenticated:
        st.info("👆 Please authenticate with ESPN in the sidebar to get started.")
        return
    
    if not st.session_state.initialized:
        st.info("🤖 Please initialize AI components in the sidebar to get recommendations.")
        return
    
    # Create tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Draft Status", "🤖 AI Recommendations", "👥 Available Players", "📈 Roster Analysis"])
    
    with tab1:
        display_draft_status()
    
    with tab2:
        display_ai_recommendations()
    
    with tab3:
        display_available_players()
    
    with tab4:
        display_roster_analysis()
    
    # Auto-refresh if monitoring
    if st.session_state.monitoring:
        time.sleep(30)  # Refresh every 30 seconds
        st.rerun()


def display_draft_status():
    """Display current draft status."""
    st.header("📊 Draft Status")
    
    try:
        draft_status = st.session_state.espn_connector.get_draft_status()
        current_roster = st.session_state.espn_connector.get_current_roster()
        league_info = st.session_state.espn_connector.get_league_info()
        
        # Draft status card
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if draft_status['status'] == 'active':
                st.metric("Round", draft_status.get('current_round', 'Unknown'))
            else:
                st.metric("Status", draft_status['status'].title())
        
        with col2:
            if draft_status['status'] == 'active':
                st.metric("Pick", draft_status.get('current_pick', 'Unknown'))
            else:
                st.metric("Players Drafted", len(current_roster))
        
        with col3:
            if draft_status['status'] == 'active':
                if draft_status.get('is_my_turn'):
                    st.metric("Status", "🎯 YOUR TURN!", delta="Make your pick!")
                else:
                    st.metric("Current Team", draft_status.get('current_team', 'Unknown'))
            else:
                st.metric("League", league_info.get('league_name', 'Unknown'))
        
        # Current roster
        st.subheader("👥 Current Roster")
        
        if current_roster:
            # Group by position
            position_players = {}
            for player in current_roster:
                pos = player['position']
                if pos not in position_players:
                    position_players[pos] = []
                position_players[pos].append(player)
            
            # Display by position
            cols = st.columns(3)
            col_idx = 0
            
            for pos in ['QB', 'RB', 'WR', 'TE', 'K', 'DEF']:
                if pos in position_players:
                    with cols[col_idx % 3]:
                        st.subheader(f"{pos}s ({len(position_players[pos])})")
                        for player in position_players[pos]:
                            points = player.get('projected_points', 0)
                            st.markdown(f"""
                            <div class="player-card">
                                <strong>{player['name']}</strong><br>
                                {player['team']} • {points:.1f} pts
                            </div>
                            """, unsafe_allow_html=True)
                    col_idx += 1
        else:
            st.info("No players drafted yet.")
        
        # League info
        with st.expander("ℹ️ League Information"):
            st.write(f"**League Name:** {league_info.get('league_name', 'Unknown')}")
            st.write(f"**Teams:** {league_info.get('num_teams', 'Unknown')}")
            st.write(f"**Scoring:** {league_info.get('scoring_type', 'Unknown')}")
        
    except Exception as e:
        st.error(f"Error getting draft status: {e}")


def display_ai_recommendations():
    """Display AI recommendations."""
    st.header("🤖 AI Recommendations")
    
    try:
        # Get current context
        draft_status = st.session_state.espn_connector.get_draft_status()
        current_roster = st.session_state.espn_connector.get_current_roster()
        available_players = st.session_state.espn_connector.get_available_players(20)
        league_info = st.session_state.espn_connector.get_league_info()
        
        if draft_status['status'] != 'active':
            st.info("No active draft found.")
            return
        
        # Get recommendation
        if st.button("🎯 Get AI Recommendation"):
            with st.spinner("🤖 Analyzing draft situation..."):
                context = {
                    'draft_status': draft_status,
                    'current_roster': current_roster,
                    'available_players': available_players,
                    'league_info': league_info
                }
                
                recommendation = st.session_state.gpt_agent.generate_draft_recommendation(context)
                
                # Display recommendation
                st.markdown('<div class="recommendation-card">', unsafe_allow_html=True)
                
                # Confidence meter
                confidence = recommendation.get('confidence', 5)
                st.metric("Confidence Level", f"{confidence}/10")
                
                # Top recommendations
                if recommendation.get('recommendations'):
                    st.subheader("🏆 Top Recommendations")
                    for i, rec in enumerate(recommendation['recommendations'][:5], 1):
                        st.write(f"{i}. {rec}")
                
                # Strategy notes
                if recommendation.get('strategy_notes'):
                    st.subheader("📋 Strategic Analysis")
                    st.write(recommendation['strategy_notes'])
                
                # Risks
                if recommendation.get('risks'):
                    st.subheader("⚠️ Potential Risks")
                    for risk in recommendation['risks']:
                        st.write(f"• {risk}")
                
                st.markdown('</div>', unsafe_allow_html=True)
        
        # Quick analysis
        st.subheader("📊 Quick Analysis")
        
        # Roster analysis
        if current_roster:
            analysis = st.session_state.roster_evaluator.analyze_roster_composition(current_roster)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Position Breakdown:**")
                for pos, count in analysis['position_counts'].items():
                    st.write(f"• {pos}: {count}")
            
            with col2:
                st.write("**Positional Needs:**")
                for pos, need_info in analysis['needs'].items():
                    if need_info['deficit'] > 0:
                        st.write(f"• {pos}: Need {need_info['deficit']} more")
                    elif need_info['surplus'] > 0:
                        st.write(f"• {pos}: Have {need_info['surplus']} extra")
                    else:
                        st.write(f"• {pos}: Balanced")
        
    except Exception as e:
        st.error(f"Error getting AI recommendations: {e}")


def display_available_players():
    """Display available players."""
    st.header("👥 Available Players")
    
    try:
        available_players = st.session_state.espn_connector.get_available_players(50)
        
        if not available_players:
            st.info("No players available.")
            return
        
        # Filter options
        col1, col2, col3 = st.columns(3)
        
        with col1:
            position_filter = st.selectbox(
                "Filter by Position",
                ["All", "QB", "RB", "WR", "TE", "K", "DEF"]
            )
        
        with col2:
            sort_by = st.selectbox(
                "Sort by",
                ["Projected Points", "Rank", "Name"]
            )
        
        with col3:
            limit = st.slider("Show top", 10, 50, 20)
        
        # Filter and sort players
        filtered_players = available_players
        if position_filter != "All":
            filtered_players = [p for p in available_players if p['position'] == position_filter]
        
        if sort_by == "Projected Points":
            filtered_players.sort(key=lambda x: x.get('projected_points', 0), reverse=True)
        elif sort_by == "Rank":
            filtered_players.sort(key=lambda x: x.get('rank', 999))
        else:  # Name
            filtered_players.sort(key=lambda x: x['name'])
        
        # Display players
        players_to_show = filtered_players[:limit]
        
        # Create DataFrame for better display
        df_data = []
        for player in players_to_show:
            df_data.append({
                'Name': player['name'],
                'Position': player['position'],
                'Team': player['team'],
                'Projected Points': round(player.get('projected_points', 0), 1),
                'Rank': player.get('rank', 0),
                'Injury Status': player.get('injury_status', 'Active')
            })
        
        df = pd.DataFrame(df_data)
        st.dataframe(df, use_container_width=True)
        
        # Player details on click
        st.subheader("🔍 Player Details")
        selected_player = st.selectbox(
            "Select a player for detailed analysis",
            [p['name'] for p in players_to_show]
        )
        
        if selected_player:
            player = next((p for p in players_to_show if p['name'] == selected_player), None)
            if player:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Name:** {player['name']}")
                    st.write(f"**Position:** {player['position']}")
                    st.write(f"**Team:** {player['team']}")
                
                with col2:
                    st.write(f"**Projected Points:** {player.get('projected_points', 0):.1f}")
                    st.write(f"**Rank:** {player.get('rank', 0)}")
                    st.write(f"**Status:** {player.get('injury_status', 'Active')}")
                
                # Evaluate player fit
                if st.button("📊 Evaluate Player Fit"):
                    current_roster = st.session_state.espn_connector.get_current_roster()
                    fit_analysis = st.session_state.roster_evaluator.evaluate_player_fit(
                        player, current_roster, available_players
                    )
                    
                    st.write(f"**Fit Score:** {fit_analysis['fit_score']}")
                    st.write(f"**Recommendation:** {fit_analysis['recommendation'].title()}")
                    st.write(f"**Scarcity Score:** {fit_analysis['scarcity_score']:.2f}")
        
    except Exception as e:
        st.error(f"Error getting available players: {e}")


def display_roster_analysis():
    """Display detailed roster analysis."""
    st.header("📈 Roster Analysis")
    
    try:
        current_roster = st.session_state.espn_connector.get_current_roster()
        
        if not current_roster:
            st.info("No players drafted yet.")
            return
        
        # Comprehensive analysis
        analysis = st.session_state.roster_evaluator.analyze_roster_composition(current_roster)
        
        # Metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Players", analysis['total_players'])
        
        with col2:
            st.metric("Roster Strength", f"{analysis['strength_score']:.1f}")
        
        with col3:
            total_points = sum(analysis['position_points'].values())
            st.metric("Total Projected Points", f"{total_points:.1f}")
        
        with col4:
            avg_points = total_points / analysis['total_players'] if analysis['total_players'] > 0 else 0
            st.metric("Average Points/Player", f"{avg_points:.1f}")
        
        # Position analysis
        st.subheader("📊 Position Analysis")
        
        # Create position chart
        position_data = []
        for pos, points in analysis['position_points'].items():
            position_data.append({
                'Position': pos,
                'Total Points': points,
                'Player Count': analysis['position_counts'].get(pos, 0)
            })
        
        if position_data:
            df = pd.DataFrame(position_data)
            st.bar_chart(df.set_index('Position')['Total Points'])
        
        # Position breakdown table
        st.subheader("📋 Position Breakdown")
        
        breakdown_data = []
        for pos, count in analysis['position_counts'].items():
            points = analysis['position_points'].get(pos, 0)
            avg_points = points / count if count > 0 else 0
            breakdown_data.append({
                'Position': pos,
                'Count': count,
                'Total Points': round(points, 1),
                'Avg Points/Player': round(avg_points, 1)
            })
        
        breakdown_df = pd.DataFrame(breakdown_data)
        st.dataframe(breakdown_df, use_container_width=True)
        
        # Needs analysis
        st.subheader("🎯 Positional Needs")
        
        needs_data = []
        for pos, need_info in analysis['needs'].items():
            needs_data.append({
                'Position': pos,
                'Current': need_info['current'],
                'Required': need_info['required'],
                'Deficit': need_info['deficit'],
                'Surplus': need_info['surplus'],
                'Priority': need_info['priority']
            })
        
        needs_df = pd.DataFrame(needs_data)
        st.dataframe(needs_df, use_container_width=True)
        
        # Optimal lineup
        st.subheader("🏆 Optimal Starting Lineup")
        
        optimal = st.session_state.roster_evaluator.get_optimal_lineup(current_roster)
        
        if optimal['starters']:
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Starters:**")
                for player in optimal['starters']:
                    st.write(f"• {player['name']} ({player['position']}) - {player.get('projected_points', 0):.1f} pts")
            
            with col2:
                st.write("**Bench:**")
                for player in optimal['bench']:
                    st.write(f"• {player['name']} ({player['position']}) - {player.get('projected_points', 0):.1f} pts")
            
            st.metric("Projected Starting Points", f"{optimal['projected_points']:.1f}")
        
    except Exception as e:
        st.error(f"Error analyzing roster: {e}")


if __name__ == "__main__":
    run_streamlit_app() 