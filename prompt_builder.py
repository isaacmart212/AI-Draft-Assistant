"""
Prompt Builder for Fantasy Football Draft AI

Creates sophisticated, context-aware prompts for different draft scenarios and strategies.
"""

import os
from typing import Dict, List, Optional
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()


class PromptBuilder:
    """Builds sophisticated prompts for fantasy football draft recommendations."""
    
    def __init__(self):
        self.draft_strategy = os.getenv('DRAFT_STRATEGY', 'balanced')
        self.risk_tolerance = os.getenv('RISK_TOLERANCE', 'medium')
        
        # Strategy templates
        self.strategy_templates = {
            'zero_rb': self._get_zero_rb_template(),
            'hero_rb': self._get_hero_rb_template(),
            'elite_te': self._get_elite_te_template(),
            'balanced': self._get_balanced_template(),
            'aggressive': self._get_aggressive_template(),
            'conservative': self._get_conservative_template()
        }
    
    def build_draft_prompt(self, context: Dict) -> str:
        """Build a comprehensive draft recommendation prompt."""
        draft_status = context['draft_status']
        current_roster = context['current_roster']
        available_players = context['available_players']
        league_info = context['league_info']
        
        # Determine the best strategy based on current situation
        strategy = self._determine_strategy(context)
        
        # Build the prompt components
        system_prompt = self._build_system_prompt(strategy)
        context_section = self._build_context_section(context)
        strategy_section = self._build_strategy_section(strategy, context)
        analysis_request = self._build_analysis_request(context)
        
        full_prompt = f"""
{system_prompt}

{context_section}

{strategy_section}

{analysis_request}
"""
        return full_prompt
    
    def _determine_strategy(self, context: Dict) -> str:
        """Determine the best draft strategy based on current situation."""
        current_roster = context['current_roster']
        draft_status = context['draft_status']
        current_round = draft_status.get('current_round', 1)
        
        # Count current positions
        position_counts = {}
        for player in current_roster:
            pos = player['position']
            position_counts[pos] = position_counts.get(pos, 0) + 1
        
        # Early rounds (1-3): Focus on foundation
        if current_round <= 3:
            if position_counts.get('RB', 0) == 0:
                return 'zero_rb'
            elif position_counts.get('WR', 0) == 0:
                return 'hero_rb'
            else:
                return 'balanced'
        
        # Middle rounds (4-8): Position-specific strategies
        elif current_round <= 8:
            if position_counts.get('TE', 0) == 0:
                return 'elite_te'
            elif position_counts.get('QB', 0) == 0:
                return 'balanced'
            else:
                return 'balanced'
        
        # Late rounds (9+): Value-based drafting
        else:
            return 'balanced'
    
    def _build_system_prompt(self, strategy: str) -> str:
        """Build the system prompt based on the chosen strategy."""
        base_prompt = """You are an expert fantasy football draft strategist with deep knowledge of:
- Player evaluation and projections
- Draft strategies and positional value
- League-specific scoring systems
- Risk assessment and injury considerations
- Value-based drafting principles

Your expertise includes:
- Advanced analytics and statistical modeling
- Understanding of positional scarcity and ADP value
- Knowledge of player injury history and risk factors
- Strategic thinking for different draft positions and league sizes
- Real-time adaptation to changing draft dynamics

Current Strategy Focus: {strategy.upper()}
"""
        
        strategy_details = self.strategy_templates.get(strategy, "")
        
        return base_prompt + strategy_details
    
    def _build_context_section(self, context: Dict) -> str:
        """Build the context section of the prompt."""
        draft_status = context['draft_status']
        current_roster = context['current_roster']
        available_players = context['available_players']
        league_info = context['league_info']
        
        # Format roster
        roster_summary = self._format_roster_summary(current_roster)
        
        # Format available players
        players_list = self._format_available_players(available_players[:15])
        
        # Format league info
        league_context = self._format_league_context(league_info)
        
        return f"""
DRAFT CONTEXT:
==============
Round: {draft_status.get('current_round', 'Unknown')}
Pick: {draft_status.get('current_pick', 'Unknown')}
League: {league_context}
Time Remaining: {draft_status.get('time_remaining', 'Unknown')}

CURRENT ROSTER:
===============
{roster_summary}

TOP AVAILABLE PLAYERS:
======================
{players_list}
"""
    
    def _build_strategy_section(self, strategy: str, context: Dict) -> str:
        """Build the strategy-specific section of the prompt."""
        current_roster = context['current_roster']
        draft_status = context['draft_status']
        current_round = draft_status.get('current_round', 1)
        
        # Analyze current situation
        position_counts = {}
        for player in current_roster:
            pos = player['position']
            position_counts[pos] = position_counts.get(pos, 0) + 1
        
        strategy_analysis = f"""
STRATEGIC ANALYSIS:
==================
Current Round: {current_round}
Roster Composition: {position_counts}
Strategy: {strategy.upper()}

Key Considerations:
"""
        
        # Add strategy-specific considerations
        if strategy == 'zero_rb':
            strategy_analysis += """
- You have not drafted any RBs yet
- Focus on elite WRs and potentially an elite TE
- Consider QB early if value presents itself
- Plan to load up on RBs in middle rounds
- Target high-upside RB handcuffs later
"""
        elif strategy == 'hero_rb':
            strategy_analysis += """
- You have one elite RB as your foundation
- Focus on building WR depth and quality
- Consider elite TE if available
- Target RB2 in rounds 4-6
- Balance risk and upside for remaining RBs
"""
        elif strategy == 'elite_te':
            strategy_analysis += """
- TE premium strategy - elite TEs provide significant advantage
- Focus on building WR and RB depth
- Consider QB if value presents itself
- Target high-upside players at other positions
"""
        else:  # balanced
            strategy_analysis += """
- Value-based drafting approach
- Consider best player available
- Balance positional needs with value
- Adapt to draft flow and positional scarcity
"""
        
        return strategy_analysis
    
    def _build_analysis_request(self, context: Dict) -> str:
        """Build the analysis request section."""
        return """
ANALYSIS REQUEST:
================
Please provide a comprehensive draft recommendation including:

1. TOP 3-5 RECOMMENDATIONS:
   - Rank players in order of preference
   - Include projected points and ADP value
   - Explain strategic reasoning for each

2. POSITIONAL NEEDS ANALYSIS:
   - Identify immediate roster needs
   - Consider positional scarcity
   - Plan for future rounds

3. RISK ASSESSMENT:
   - Evaluate injury risk and upside potential
   - Consider age and situation changes
   - Provide confidence level (1-10)

4. STRATEGIC INSIGHTS:
   - Alternative approaches to consider
   - Players to target in upcoming rounds
   - Potential trade-up or trade-down scenarios

5. VALUE ANALYSIS:
   - Compare projected value vs. ADP
   - Identify potential steals or reaches
   - Consider league-specific scoring impact

Format your response clearly with numbered sections and bullet points for easy reading.
"""
    
    def _format_roster_summary(self, roster: List[Dict]) -> str:
        """Format current roster for the prompt."""
        if not roster:
            return "No players drafted yet."
        
        position_counts = {}
        for player in roster:
            pos = player['position']
            position_counts[pos] = position_counts.get(pos, 0) + 1
        
        summary = "Position Counts:\n"
        for pos, count in position_counts.items():
            summary += f"- {pos}: {count} players\n"
        
        summary += "\nDetailed Roster:\n"
        for player in roster:
            summary += f"- {player['name']} ({player['position']}, {player['team']}) - "
            summary += f"Proj: {player['projected_points']:.1f} pts\n"
        
        return summary
    
    def _format_available_players(self, players: List[Dict]) -> str:
        """Format available players list for the prompt."""
        if not players:
            return "No players available."
        
        formatted = ""
        for i, player in enumerate(players, 1):
            formatted += f"{i:2d}. {player['name']:<20} ({player['position']}, {player['team']}) - "
            formatted += f"Proj: {player['projected_points']:6.1f}, Rank: {player['rank']:3d}\n"
        
        return formatted
    
    def _format_league_context(self, league_info: Dict) -> str:
        """Format league information for the prompt."""
        return f"{league_info.get('num_teams', 'Unknown')}-team {league_info.get('scoring_type', 'Standard')} league"
    
    def _get_zero_rb_template(self) -> str:
        """Get the Zero RB strategy template."""
        return """
ZERO RB STRATEGY FOCUS:
- Prioritize elite WRs and potentially elite TE early
- Avoid RBs in the first 3-4 rounds
- Target high-upside RBs in middle rounds
- Focus on pass-catching RBs in PPR leagues
- Consider QB early if exceptional value presents itself
- Plan for RB depth and handcuffs in later rounds
"""
    
    def _get_hero_rb_template(self) -> str:
        """Get the Hero RB strategy template."""
        return """
HERO RB STRATEGY FOCUS:
- Build around one elite RB as foundation
- Prioritize WR depth and quality
- Target RB2 in rounds 4-6 for balance
- Consider elite TE if available
- Focus on high-floor players for consistency
- Plan for RB handcuffs and depth
"""
    
    def _get_elite_te_template(self) -> str:
        """Get the Elite TE strategy template."""
        return """
ELITE TE STRATEGY FOCUS:
- Target elite TE early for positional advantage
- Build WR and RB depth around TE
- Consider QB if value presents itself
- Focus on high-upside players at other positions
- Plan for TE premium scoring impact
- Target backup TE in later rounds
"""
    
    def _get_balanced_template(self) -> str:
        """Get the balanced strategy template."""
        return """
BALANCED STRATEGY FOCUS:
- Value-based drafting approach
- Consider best player available
- Balance positional needs with value
- Adapt to draft flow and positional scarcity
- Focus on high-floor, consistent players
- Plan for depth at all positions
"""
    
    def _get_aggressive_template(self) -> str:
        """Get the aggressive strategy template."""
        return """
AGGRESSIVE STRATEGY FOCUS:
- Target high-upside, boom-or-bust players
- Consider trading up for desired players
- Focus on young players with breakout potential
- Accept higher risk for higher reward
- Target players in new situations or systems
- Plan for potential busts with depth
"""
    
    def _get_conservative_template(self) -> str:
        """Get the conservative strategy template."""
        return """
CONSERVATIVE STRATEGY FOCUS:
- Target high-floor, consistent players
- Avoid players with injury history
- Focus on proven veterans
- Prioritize safe picks over upside
- Plan for depth and handcuffs
- Avoid boom-or-bust players
"""
    
    def build_quick_prompt(self, context: Dict) -> str:
        """Build a quick, simplified prompt for fast recommendations."""
        draft_status = context['draft_status']
        available_players = context['available_players'][:5]
        
        return f"""
Quick Draft Recommendation - Round {draft_status.get('current_round', '?')}, Pick {draft_status.get('current_pick', '?')}

Top 5 Available Players:
{self._format_available_players(available_players)}

Provide top 3 recommendations with brief reasoning and confidence level (1-10).
"""
    
    def build_positional_prompt(self, context: Dict, target_position: str) -> str:
        """Build a prompt focused on a specific position."""
        available_players = [p for p in context['available_players'] if p['position'] == target_position]
        
        return f"""
Position-Specific Analysis - {target_position}

Available {target_position}s:
{self._format_available_players(available_players[:10])}

Analyze the best {target_position} options considering:
- Projected points and ADP value
- Risk assessment and upside potential
- Fit with current roster
- Positional scarcity

Provide top 3 recommendations with detailed reasoning.
"""


if __name__ == "__main__":
    # Test the prompt builder
    builder = PromptBuilder()
    
    test_context = {
        'draft_status': {
            'current_round': 3,
            'current_pick': 25,
            'is_my_turn': True
        },
        'current_roster': [
            {'name': 'Christian McCaffrey', 'position': 'RB', 'team': 'SF', 'projected_points': 280.5},
            {'name': 'Tyreek Hill', 'position': 'WR', 'team': 'MIA', 'projected_points': 265.2}
        ],
        'available_players': [
            {'name': 'Travis Kelce', 'position': 'TE', 'team': 'KC', 'projected_points': 245.8, 'rank': 15},
            {'name': 'Saquon Barkley', 'position': 'RB', 'team': 'PHI', 'projected_points': 235.2, 'rank': 18},
            {'name': 'Stefon Diggs', 'position': 'WR', 'team': 'HOU', 'projected_points': 230.1, 'rank': 20}
        ],
        'league_info': {
            'num_teams': 12,
            'scoring_type': 'PPR'
        }
    }
    
    prompt = builder.build_draft_prompt(test_context)
    print("Generated Prompt:")
    print(prompt) 