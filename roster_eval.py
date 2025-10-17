"""
Roster Evaluation Utilities

Provides functions for analyzing roster composition, positional needs, and draft strategy.
"""

import logging
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

logger = logging.getLogger(__name__)


class RosterEvaluator:
    """Evaluates roster composition and provides strategic insights."""
    
    def __init__(self):
        # Standard roster positions for different league types
        self.standard_positions = {
            'QB': 1,
            'RB': 2,
            'WR': 2,
            'TE': 1,
            'K': 1,
            'DEF': 1
        }
        
        # Position tiers for evaluation
        self.position_tiers = {
            'QB': {'elite': 1, 'good': 2, 'average': 3, 'below_average': 4},
            'RB': {'elite': 1, 'good': 2, 'average': 3, 'below_average': 4},
            'WR': {'elite': 1, 'good': 2, 'average': 3, 'below_average': 4},
            'TE': {'elite': 1, 'good': 2, 'average': 3, 'below_average': 4}
        }
    
    def analyze_roster_composition(self, roster: List[Dict]) -> Dict:
        """Analyze current roster composition and identify needs."""
        position_counts = defaultdict(int)
        position_players = defaultdict(list)
        
        # Count players by position
        for player in roster:
            pos = player['position']
            position_counts[pos] += 1
            position_players[pos].append(player)
        
        # Calculate projected points by position
        position_points = {}
        for pos, players in position_players.items():
            total_points = sum(p.get('projected_points', 0) for p in players)
            position_points[pos] = total_points
        
        # Identify positional needs
        needs = self._identify_positional_needs(position_counts)
        
        # Calculate roster strength
        strength_score = self._calculate_roster_strength(roster)
        
        return {
            'position_counts': dict(position_counts),
            'position_players': dict(position_players),
            'position_points': position_points,
            'needs': needs,
            'strength_score': strength_score,
            'total_players': len(roster)
        }
    
    def _identify_positional_needs(self, position_counts: Dict[str, int]) -> Dict[str, Dict]:
        """Identify positional needs based on current roster."""
        needs = {}
        
        for pos, required in self.standard_positions.items():
            current = position_counts.get(pos, 0)
            deficit = max(0, required - current)
            surplus = max(0, current - required)
            
            priority = 'high' if deficit > 0 else 'medium' if current == required else 'low'
            
            needs[pos] = {
                'current': current,
                'required': required,
                'deficit': deficit,
                'surplus': surplus,
                'priority': priority
            }
        
        return needs
    
    def _calculate_roster_strength(self, roster: List[Dict]) -> float:
        """Calculate overall roster strength score."""
        if not roster:
            return 0.0
        
        total_points = sum(p.get('projected_points', 0) for p in roster)
        avg_points = total_points / len(roster)
        
        # Bonus for having players in key positions
        position_bonus = 0
        position_counts = defaultdict(int)
        for player in roster:
            pos = player['position']
            position_counts[pos] += 1
        
        # Bonus for having required positions filled
        for pos, required in self.standard_positions.items():
            if position_counts[pos] >= required:
                position_bonus += 10
        
        return avg_points + position_bonus
    
    def get_positional_scarcity(self, available_players: List[Dict]) -> Dict[str, float]:
        """Calculate positional scarcity based on available players."""
        position_counts = defaultdict(int)
        position_points = defaultdict(list)
        
        for player in available_players:
            pos = player['position']
            position_counts[pos] += 1
            position_points[pos].append(player.get('projected_points', 0))
        
        scarcity_scores = {}
        total_players = len(available_players)
        
        for pos in ['QB', 'RB', 'WR', 'TE']:
            count = position_counts[pos]
            if count == 0:
                scarcity_scores[pos] = 1.0  # Maximum scarcity
            else:
                # Calculate scarcity based on count and quality
                avg_points = sum(position_points[pos]) / count if position_points[pos] else 0
                scarcity_scores[pos] = (1.0 / count) * (avg_points / 100)  # Normalize by expected points
        
        return scarcity_scores
    
    def recommend_draft_strategy(self, roster: List[Dict], available_players: List[Dict], 
                               current_round: int) -> Dict:
        """Recommend draft strategy based on current situation."""
        analysis = self.analyze_roster_composition(roster)
        scarcity = self.get_positional_scarcity(available_players)
        
        # Determine primary strategy
        strategy = self._determine_primary_strategy(analysis, current_round)
        
        # Get position priorities
        position_priorities = self._get_position_priorities(analysis, scarcity, current_round)
        
        # Get strategic insights
        insights = self._get_strategic_insights(analysis, current_round)
        
        return {
            'primary_strategy': strategy,
            'position_priorities': position_priorities,
            'insights': insights,
            'roster_analysis': analysis,
            'scarcity_analysis': scarcity
        }
    
    def _determine_primary_strategy(self, analysis: Dict, current_round: int) -> str:
        """Determine the primary draft strategy."""
        position_counts = analysis['position_counts']
        
        # Early rounds (1-3): Foundation building
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
    
    def _get_position_priorities(self, analysis: Dict, scarcity: Dict, current_round: int) -> List[str]:
        """Get prioritized list of positions to target."""
        needs = analysis['needs']
        priorities = []
        
        # Sort positions by need priority and scarcity
        position_scores = []
        for pos, need_info in needs.items():
            if pos in ['QB', 'RB', 'WR', 'TE']:  # Focus on skill positions
                priority_score = 0
                
                # Need-based scoring
                if need_info['priority'] == 'high':
                    priority_score += 10
                elif need_info['priority'] == 'medium':
                    priority_score += 5
                
                # Scarcity-based scoring
                scarcity_score = scarcity.get(pos, 0.5)
                priority_score += scarcity_score * 5
                
                # Round-based adjustments
                if current_round <= 3 and pos in ['RB', 'WR']:
                    priority_score += 3
                elif current_round <= 6 and pos == 'TE':
                    priority_score += 2
                elif current_round > 8 and pos == 'QB':
                    priority_score += 1
                
                position_scores.append((pos, priority_score))
        
        # Sort by priority score (highest first)
        position_scores.sort(key=lambda x: x[1], reverse=True)
        
        return [pos for pos, score in position_scores]
    
    def _get_strategic_insights(self, analysis: Dict, current_round: int) -> List[str]:
        """Generate strategic insights based on roster analysis."""
        insights = []
        position_counts = analysis['position_counts']
        needs = analysis['needs']
        
        # Early round insights
        if current_round <= 3:
            if position_counts.get('RB', 0) == 0:
                insights.append("Consider Zero RB strategy - focus on elite WRs and TE")
            elif position_counts.get('WR', 0) == 0:
                insights.append("Consider Hero RB strategy - build WR depth around your RB")
        
        # Middle round insights
        elif current_round <= 8:
            if needs.get('TE', {}).get('deficit', 0) > 0:
                insights.append("TE premium - consider elite TE for positional advantage")
            if needs.get('QB', {}).get('deficit', 0) > 0:
                insights.append("QB can wait - focus on RB/WR depth first")
        
        # Late round insights
        else:
            insights.append("Late round strategy - target high-upside players and handcuffs")
        
        # General insights
        if analysis['total_players'] < 5:
            insights.append("Early draft - focus on building foundation with safe picks")
        elif analysis['total_players'] > 10:
            insights.append("Late draft - target high-upside players and sleepers")
        
        # Position-specific insights
        for pos, need_info in needs.items():
            if need_info['deficit'] > 0:
                insights.append(f"Need {need_info['deficit']} more {pos}(s)")
            elif need_info['surplus'] > 0:
                insights.append(f"Have {need_info['surplus']} extra {pos}(s) - consider trading")
        
        return insights
    
    def evaluate_player_fit(self, player: Dict, roster: List[Dict], 
                          available_players: List[Dict]) -> Dict:
        """Evaluate how well a player fits the current roster."""
        analysis = self.analyze_roster_composition(roster)
        player_pos = player['position']
        
        # Calculate fit score
        fit_score = 0
        
        # Position need bonus
        needs = analysis['needs']
        if player_pos in needs:
            if needs[player_pos]['deficit'] > 0:
                fit_score += 20  # High need
            elif needs[player_pos]['current'] == needs[player_pos]['required']:
                fit_score += 10  # Balanced
            else:
                fit_score -= 5   # Surplus
        
        # Quality bonus
        projected_points = player.get('projected_points', 0)
        if projected_points > 250:
            fit_score += 15  # Elite player
        elif projected_points > 200:
            fit_score += 10  # Good player
        elif projected_points > 150:
            fit_score += 5   # Average player
        
        # Scarcity consideration
        scarcity = self.get_positional_scarcity(available_players)
        scarcity_score = scarcity.get(player_pos, 0.5)
        fit_score += scarcity_score * 10
        
        # Roster balance consideration
        position_counts = analysis['position_counts']
        if position_counts.get(player_pos, 0) < 2:  # Don't overstack positions early
            fit_score += 5
        
        return {
            'player': player,
            'fit_score': fit_score,
            'position_need': needs.get(player_pos, {}),
            'scarcity_score': scarcity_score,
            'recommendation': 'strong' if fit_score > 20 else 'moderate' if fit_score > 10 else 'weak'
        }
    
    def get_optimal_lineup(self, roster: List[Dict], scoring_type: str = 'PPR') -> Dict:
        """Calculate optimal starting lineup from current roster."""
        if not roster:
            return {'starters': [], 'bench': [], 'projected_points': 0}
        
        # Sort players by projected points
        sorted_players = sorted(roster, key=lambda x: x.get('projected_points', 0), reverse=True)
        
        # Select starters based on standard lineup
        starters = []
        bench = []
        position_counts = defaultdict(int)
        
        for player in sorted_players:
            pos = player['position']
            required = self.standard_positions.get(pos, 0)
            
            if position_counts[pos] < required:
                starters.append(player)
                position_counts[pos] += 1
            else:
                bench.append(player)
        
        total_points = sum(p.get('projected_points', 0) for p in starters)
        
        return {
            'starters': starters,
            'bench': bench,
            'projected_points': total_points,
            'position_counts': dict(position_counts)
        }


def calculate_adp_value(player: Dict, current_pick: int) -> float:
    """Calculate ADP value relative to current pick position."""
    player_rank = player.get('rank', 999)
    if player_rank == 0:
        return 0.0
    
    # Calculate value as difference between expected pick and current pick
    expected_pick = player_rank
    value = expected_pick - current_pick
    
    # Normalize to a 0-10 scale
    if value > 0:
        return min(10.0, value / 10.0)  # Positive value (steal)
    else:
        return max(-5.0, value / 10.0)  # Negative value (reach)


def get_player_tier(player: Dict) -> str:
    """Determine player tier based on projected points."""
    projected_points = player.get('projected_points', 0)
    
    if projected_points > 250:
        return 'elite'
    elif projected_points > 200:
        return 'good'
    elif projected_points > 150:
        return 'average'
    else:
        return 'below_average'


if __name__ == "__main__":
    # Test the roster evaluator
    evaluator = RosterEvaluator()
    
    test_roster = [
        {'name': 'Christian McCaffrey', 'position': 'RB', 'projected_points': 280.5},
        {'name': 'Tyreek Hill', 'position': 'WR', 'projected_points': 265.2}
    ]
    
    test_available = [
        {'name': 'Travis Kelce', 'position': 'TE', 'projected_points': 245.8, 'rank': 15},
        {'name': 'Saquon Barkley', 'position': 'RB', 'projected_points': 235.2, 'rank': 18},
        {'name': 'Stefon Diggs', 'position': 'WR', 'projected_points': 230.1, 'rank': 20}
    ]
    
    analysis = evaluator.analyze_roster_composition(test_roster)
    strategy = evaluator.recommend_draft_strategy(test_roster, test_available, 3)
    
    print("Roster Analysis:")
    print(analysis)
    print("\nDraft Strategy:")
    print(strategy) 