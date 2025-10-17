"""
GPT-4 AI Agent for Fantasy Football Draft Recommendations

Handles strategic reasoning and provides intelligent pick recommendations.
"""

import os
import json
import logging
from typing import Dict, List, Optional, Tuple
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)


class GPTAgent:
    """AI agent for fantasy football draft recommendations."""
    
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OpenAI API key not found in environment variables")
        
        self.client = OpenAI(api_key=self.api_key)
        self.model = "gpt-4"
        self.max_tokens = 1000
        self.temperature = 0.7
    
    def generate_draft_recommendation(self, context: Dict) -> Dict:
        """
        Generate AI-powered draft recommendation based on current context.
        
        Args:
            context: Dictionary containing draft context including:
                - draft_status: Current draft information
                - current_roster: Team's current players
                - available_players: Top available players
                - league_info: League settings and configuration
        
        Returns:
            Dictionary with recommendation details
        """
        try:
            prompt = self._build_draft_prompt(context)
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            recommendation_text = response.choices[0].message.content
            return self._parse_recommendation(recommendation_text, context)
            
        except Exception as e:
            logger.error(f"Error generating recommendation: {e}")
            return self._get_fallback_recommendation(context)
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt that defines the AI's role and capabilities."""
        return """You are an expert fantasy football draft strategist with deep knowledge of:
- Player evaluation and projections
- Draft strategies (Zero RB, Hero RB, Elite TE, etc.)
- Positional scarcity and value-based drafting
- League-specific scoring systems and roster requirements
- Risk assessment and injury considerations

Your role is to analyze the current draft situation and provide:
1. A ranked list of the top 3-5 recommended picks
2. Strategic reasoning for each recommendation
3. Risk assessment and confidence levels
4. Positional needs analysis
5. Alternative strategies to consider

Always consider:
- Current roster composition and needs
- Available players and their projected value
- Draft round and pick position
- League scoring settings
- Positional scarcity and ADP value

Provide clear, actionable advice that helps make the best possible pick."""
    
    def _build_draft_prompt(self, context: Dict) -> str:
        """Build a comprehensive prompt for the AI based on current draft context."""
        draft_status = context['draft_status']
        current_roster = context['current_roster']
        available_players = context['available_players']
        league_info = context['league_info']
        
        # Build roster summary
        roster_summary = self._format_roster_summary(current_roster)
        
        # Build available players list
        players_list = self._format_available_players(available_players[:10])
        
        # Build league context
        league_context = self._format_league_context(league_info)
        
        prompt = f"""
FANTASY FOOTBALL DRAFT RECOMMENDATION REQUEST

DRAFT CONTEXT:
- Round: {draft_status.get('current_round', 'Unknown')}
- Pick: {draft_status.get('current_pick', 'Unknown')}
- League Type: {league_context}

CURRENT ROSTER:
{roster_summary}

TOP AVAILABLE PLAYERS:
{players_list}

Please provide a comprehensive draft recommendation including:
1. Top 3-5 recommended picks in order of preference
2. Strategic reasoning for each recommendation
3. Positional needs analysis
4. Risk assessment and confidence level (1-10)
5. Alternative strategies to consider

Format your response as a structured analysis that clearly explains the reasoning behind each recommendation.
"""
        return prompt
    
    def _format_roster_summary(self, roster: List[Dict]) -> str:
        """Format current roster for the prompt."""
        if not roster:
            return "No players drafted yet."
        
        position_counts = {}
        for player in roster:
            pos = player['position']
            position_counts[pos] = position_counts.get(pos, 0) + 1
        
        summary = "Current Roster:\n"
        for pos, count in position_counts.items():
            summary += f"- {pos}: {count} players\n"
        
        summary += "\nDetailed Roster:\n"
        for player in roster:
            summary += f"- {player['name']} ({player['position']}, {player['team']}) - Proj: {player['projected_points']:.1f}\n"
        
        return summary
    
    def _format_available_players(self, players: List[Dict]) -> str:
        """Format available players list for the prompt."""
        if not players:
            return "No players available."
        
        formatted = ""
        for i, player in enumerate(players, 1):
            formatted += f"{i}. {player['name']} ({player['position']}, {player['team']}) - "
            formatted += f"Proj: {player['projected_points']:.1f}, Rank: {player['rank']}\n"
        
        return formatted
    
    def _format_league_context(self, league_info: Dict) -> str:
        """Format league information for the prompt."""
        return f"{league_info.get('num_teams', 'Unknown')}-team {league_info.get('scoring_type', 'Standard')} league"
    
    def _parse_recommendation(self, response: str, context: Dict) -> Dict:
        """Parse the AI response into a structured recommendation."""
        try:
            # Try to extract structured information from the response
            recommendation = {
                'raw_response': response,
                'recommendations': [],
                'confidence': 7,  # Default confidence
                'strategy_notes': '',
                'positional_needs': {},
                'risks': []
            }
            
            # Extract recommendations (look for numbered lists)
            lines = response.split('\n')
            for line in lines:
                line = line.strip()
                if line and (line[0].isdigit() or line.startswith('-') or line.startswith('•')):
                    if any(pos in line.upper() for pos in ['QB', 'RB', 'WR', 'TE', 'K', 'DEF']):
                        recommendation['recommendations'].append(line)
            
            # Extract confidence level
            if 'confidence' in response.lower():
                import re
                confidence_match = re.search(r'confidence[:\s]*(\d+)', response.lower())
                if confidence_match:
                    recommendation['confidence'] = int(confidence_match.group(1))
            
            # Extract strategy notes
            if 'strategy' in response.lower() or 'reasoning' in response.lower():
                recommendation['strategy_notes'] = response
            
            return recommendation
            
        except Exception as e:
            logger.error(f"Error parsing recommendation: {e}")
            return {
                'raw_response': response,
                'recommendations': [response],
                'confidence': 5,
                'strategy_notes': response,
                'positional_needs': {},
                'risks': []
            }
    
    def _get_fallback_recommendation(self, context: Dict) -> Dict:
        """Provide a fallback recommendation when AI fails."""
        available_players = context['available_players']
        
        if not available_players:
            return {
                'raw_response': 'No players available for recommendation',
                'recommendations': [],
                'confidence': 0,
                'strategy_notes': 'Unable to generate recommendation',
                'positional_needs': {},
                'risks': []
            }
        
        # Simple fallback: pick highest projected player
        top_player = max(available_players, key=lambda x: x.get('projected_points', 0))
        
        return {
            'raw_response': f'Fallback recommendation: {top_player["name"]}',
            'recommendations': [f'1. {top_player["name"]} ({top_player["position"]}) - Highest projected points'],
            'confidence': 3,
            'strategy_notes': f'Fallback pick based on highest projected points: {top_player["name"]}',
            'positional_needs': {},
            'risks': ['AI recommendation failed, using fallback logic']
        }
    
    def analyze_positional_scarcity(self, context: Dict) -> Dict:
        """Analyze positional scarcity in the current draft."""
        try:
            draft_history = context.get('draft_history', [])
            current_round = context['draft_status'].get('current_round', 1)
            
            # Count players drafted by position
            position_counts = {}
            for pick in draft_history:
                if pick.get('position'):
                    pos = pick['position']
                    position_counts[pos] = position_counts.get(pos, 0) + 1
            
            # Calculate scarcity scores
            scarcity_scores = {}
            total_picks = len(draft_history)
            
            for pos in ['QB', 'RB', 'WR', 'TE']:
                drafted = position_counts.get(pos, 0)
                scarcity_scores[pos] = {
                    'drafted': drafted,
                    'percentage': (drafted / total_picks * 100) if total_picks > 0 else 0,
                    'scarcity_level': 'high' if drafted < total_picks * 0.2 else 'medium' if drafted < total_picks * 0.4 else 'low'
                }
            
            return scarcity_scores
            
        except Exception as e:
            logger.error(f"Error analyzing positional scarcity: {e}")
            return {}
    
    def get_strategy_insights(self, context: Dict) -> List[str]:
        """Generate strategic insights based on current draft situation."""
        insights = []
        
        try:
            current_roster = context['current_roster']
            draft_status = context['draft_status']
            current_round = draft_status.get('current_round', 1)
            
            # Analyze roster composition
            position_counts = {}
            for player in current_roster:
                pos = player['position']
                position_counts[pos] = position_counts.get(pos, 0) + 1
            
            # Generate insights based on round and roster
            if current_round <= 3:
                if position_counts.get('RB', 0) == 0:
                    insights.append("Consider Zero RB strategy - you haven't drafted any RBs yet")
                elif position_counts.get('WR', 0) == 0:
                    insights.append("Consider Hero WR strategy - focus on elite WRs early")
            
            elif current_round <= 6:
                if position_counts.get('TE', 0) == 0:
                    insights.append("TE premium - consider elite TE if available")
                if position_counts.get('QB', 0) == 0:
                    insights.append("QB can wait - focus on RB/WR depth")
            
            elif current_round > 10:
                insights.append("Late round strategy - target high-upside players and handcuffs")
            
            # Add general insights
            if len(current_roster) < 5:
                insights.append("Early draft - focus on building foundation with safe, high-floor players")
            elif len(current_roster) > 10:
                insights.append("Late draft - target high-upside players and sleepers")
            
        except Exception as e:
            logger.error(f"Error generating strategy insights: {e}")
            insights.append("Unable to generate strategy insights")
        
        return insights


if __name__ == "__main__":
    # Test the GPT agent
    agent = GPTAgent()
    
    # Mock context for testing
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
    
    recommendation = agent.generate_draft_recommendation(test_context)
    print("AI Recommendation:")
    print(json.dumps(recommendation, indent=2)) 