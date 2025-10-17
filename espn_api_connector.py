"""
ESPN Fantasy Football API Connector

Handles authentication, league data retrieval, and real-time draft monitoring.
"""

import os
import time
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import requests
from espn_api.football import League, Team
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ESPNConnector:
    """Handles ESPN Fantasy Football API interactions."""
    
    def __init__(self):
        self.username = os.getenv('ESPN_USERNAME')
        self.password = os.getenv('ESPN_PASSWORD')
        self.league_id = int(os.getenv('LEAGUE_ID', 0))
        self.team_id = int(os.getenv('TEAM_ID', 0))
        self.league = None
        self.team = None
        
        if not all([self.username, self.password, self.league_id]):
            raise ValueError("Missing required environment variables. Check env_example.txt")
    
    def authenticate(self) -> bool:
        """Authenticate with ESPN Fantasy Football."""
        try:
            logger.info("Authenticating with ESPN...")
            
            # Try to create league connection without authentication first
            try:
                self.league = League(
                    league_id=self.league_id,
                    year=datetime.now().year
                )
                logger.info("Connected to public league data")
            except Exception as e:
                logger.warning(f"Could not connect to public league: {e}")
                # If public connection fails, try with authentication
                self.league = League(
                    league_id=self.league_id,
                    year=datetime.now().year,
                    espn_s2=None,
                    swid=None,
                    username=self.username,
                    password=self.password
                )
                logger.info("Connected with authentication")
            
            # Find our team (skip if team_id is 0 for listing purposes)
            if self.team_id > 0:
                for team in self.league.teams:
                    if team.team_id == self.team_id:
                        self.team = team
                        break
                
                if not self.team:
                    raise ValueError(f"Team ID {self.team_id} not found in league")
            
            if self.team:
                logger.info(f"Successfully authenticated. Team: {self.team.team_name}")
            else:
                logger.info("Successfully authenticated. No specific team selected.")
            return True
            
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return False
    
    def get_league_info(self) -> Dict:
        """Get league information and settings."""
        if not self.league:
            raise ValueError("Not authenticated. Call authenticate() first.")
        
        return {
            'league_name': self.league.settings.name,
            'scoring_type': self.league.settings.scoring_type,
            'num_teams': len(self.league.teams),
            'roster_positions': self.league.settings.roster_positions,
            'scoring_settings': self.league.settings.scoring_settings
        }
    
    def get_current_roster(self) -> List[Dict]:
        """Get current team roster."""
        if not self.team:
            raise ValueError("Team not found. Call authenticate() first.")
        
        roster = []
        for player in self.team.roster:
            roster.append({
                'name': player.name,
                'position': player.position,
                'team': player.proTeam,
                'projected_points': getattr(player, 'projected_points', 0),
                'total_points': getattr(player, 'total_points', 0),
                'rank': getattr(player, 'rank', 0)
            })
        
        return roster
    
    def get_draft_status(self) -> Dict:
        """Get current draft status and information."""
        if not self.league:
            raise ValueError("Not authenticated. Call authenticate() first.")
        
        try:
            # Get draft info
            draft = self.league.draft
            if not draft:
                return {'status': 'no_draft', 'message': 'No active draft found'}
            
            current_pick = draft.get_current_pick()
            if not current_pick:
                return {'status': 'draft_complete', 'message': 'Draft is complete'}
            
            return {
                'status': 'active',
                'current_round': current_pick.round_num,
                'current_pick': current_pick.pick_num,
                'current_team': current_pick.team.team_name,
                'is_my_turn': current_pick.team.team_id == self.team_id,
                'time_remaining': getattr(current_pick, 'time_remaining', None)
            }
            
        except Exception as e:
            logger.error(f"Error getting draft status: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def get_available_players(self, limit: int = 50) -> List[Dict]:
        """Get top available players for drafting."""
        if not self.league:
            raise ValueError("Not authenticated. Call authenticate() first.")
        
        try:
            # Get free agents (available players)
            free_agents = self.league.free_agents()
            
            # Sort by projected points or rank
            sorted_players = sorted(
                free_agents, 
                key=lambda x: getattr(x, 'projected_points', 0) or getattr(x, 'rank', 999),
                reverse=True
            )
            
            available_players = []
            for player in sorted_players[:limit]:
                available_players.append({
                    'name': player.name,
                    'position': player.position,
                    'team': player.proTeam,
                    'projected_points': getattr(player, 'projected_points', 0),
                    'total_points': getattr(player, 'total_points', 0),
                    'rank': getattr(player, 'rank', 0),
                    'injury_status': getattr(player, 'injury_status', 'Active'),
                    'bye_week': getattr(player, 'bye_week', 0)
                })
            
            return available_players
            
        except Exception as e:
            logger.error(f"Error getting available players: {e}")
            return []
    
    def get_draft_history(self) -> List[Dict]:
        """Get complete draft history."""
        if not self.league:
            raise ValueError("Not authenticated. Call authenticate() first.")
        
        try:
            draft = self.league.draft
            if not draft:
                return []
            
            history = []
            for pick in draft:
                history.append({
                    'round': pick.round_num,
                    'pick': pick.pick_num,
                    'team': pick.team.team_name,
                    'player': pick.player.name if pick.player else 'No player selected',
                    'position': pick.player.position if pick.player else None,
                    'timestamp': getattr(pick, 'timestamp', None)
                })
            
            return history
            
        except Exception as e:
            logger.error(f"Error getting draft history: {e}")
            return []
    
    def monitor_draft(self, callback=None, polling_interval: int = 30):
        """Monitor draft in real-time and call callback when it's our turn."""
        logger.info("Starting draft monitoring...")
        
        while True:
            try:
                draft_status = self.get_draft_status()
                
                if draft_status['status'] == 'active' and draft_status['is_my_turn']:
                    logger.info("It's our turn to pick!")
                    
                    if callback:
                        # Get current context for callback
                        context = {
                            'draft_status': draft_status,
                            'current_roster': self.get_current_roster(),
                            'available_players': self.get_available_players(20),
                            'league_info': self.get_league_info()
                        }
                        callback(context)
                
                elif draft_status['status'] == 'draft_complete':
                    logger.info("Draft is complete!")
                    break
                
                elif draft_status['status'] == 'error':
                    logger.error(f"Draft monitoring error: {draft_status['message']}")
                
                time.sleep(polling_interval)
                
            except KeyboardInterrupt:
                logger.info("Draft monitoring stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in draft monitoring: {e}")
                time.sleep(polling_interval)
    
    def get_team_by_id(self, team_id: int) -> Optional[Team]:
        """Get team by team ID."""
        if not self.league:
            return None
        
        for team in self.league.teams:
            if team.team_id == team_id:
                return team
        return None
    
    def get_position_counts(self) -> Dict[str, int]:
        """Get count of players by position on current roster."""
        roster = self.get_current_roster()
        position_counts = {}
        
        for player in roster:
            pos = player['position']
            position_counts[pos] = position_counts.get(pos, 0) + 1
        
        return position_counts
    
    def get_all_teams(self) -> List[Dict]:
        """Get all teams in the league with their IDs and names."""
        if not self.league:
            raise ValueError("Not authenticated. Call authenticate() first.")
        
        teams = []
        for team in self.league.teams:
            teams.append({
                'id': team.team_id,
                'name': team.team_name,
                'owner': getattr(team, 'owner', 'Unknown'),
                'division': getattr(team, 'division_id', 0)
            })
        
        return teams


if __name__ == "__main__":
    # Test the connector
    connector = ESPNConnector()
    if connector.authenticate():
        print("Authentication successful!")
        print(f"League: {connector.get_league_info()}")
        print(f"Current roster: {len(connector.get_current_roster())} players")
        print(f"Draft status: {connector.get_draft_status()}")
    else:
        print("Authentication failed!") 