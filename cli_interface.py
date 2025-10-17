"""
Command Line Interface for Fantasy Football Draft AI

Provides a clean, interactive CLI for draft monitoring and recommendations.
"""

import os
import sys
import time
import json
import logging
from typing import Dict, List, Optional
from datetime import datetime
import argparse
from colorama import init, Fore, Back, Style

# Initialize colorama for cross-platform colored output
init()

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from demo_espn_connector import DemoESPNConnector
from ai.demo_gpt_agent import DemoGPTAgent
from prompts.prompt_builder import PromptBuilder
from utils.roster_eval import RosterEvaluator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CLIInterface:
    """Command-line interface for the fantasy draft AI."""
    
    def __init__(self):
        self.espn_connector = None
        self.gpt_agent = None
        self.prompt_builder = None
        self.roster_evaluator = None
        self.is_monitoring = False
        
        # Initialize components
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize all the necessary components."""
        try:
            print(f"{Fore.CYAN}Initializing Fantasy Draft AI...{Style.RESET_ALL}")
            
            # Initialize ESPN connector
            print(f"{Fore.YELLOW}Connecting to ESPN...{Style.RESET_ALL}")
            self.espn_connector = DemoESPNConnector()
            
            # Initialize AI components
            print(f"{Fore.YELLOW}Initializing AI components...{Style.RESET_ALL}")
            self.gpt_agent = DemoGPTAgent()
            self.prompt_builder = PromptBuilder()
            self.roster_evaluator = RosterEvaluator()
            
            print(f"{Fore.GREEN}✓ All components initialized successfully!{Style.RESET_ALL}")
            
        except Exception as e:
            print(f"{Fore.RED}✗ Error initializing components: {e}{Style.RESET_ALL}")
            sys.exit(1)
    
    def authenticate(self) -> bool:
        """Authenticate with ESPN."""
        try:
            print(f"{Fore.CYAN}Authenticating with ESPN...{Style.RESET_ALL}")
            success = self.espn_connector.authenticate()
            
            if success:
                league_info = self.espn_connector.get_league_info()
                print(f"{Fore.GREEN}✓ Successfully authenticated!{Style.RESET_ALL}")
                print(f"{Fore.CYAN}League: {league_info['league_name']}{Style.RESET_ALL}")
                print(f"{Fore.CYAN}Teams: {league_info['num_teams']}{Style.RESET_ALL}")
                print(f"{Fore.CYAN}Scoring: {league_info['scoring_type']}{Style.RESET_ALL}")
                return True
            else:
                print(f"{Fore.RED}✗ Authentication failed!{Style.RESET_ALL}")
                return False
                
        except Exception as e:
            print(f"{Fore.RED}✗ Authentication error: {e}{Style.RESET_ALL}")
            return False
    
    def show_current_status(self):
        """Display current draft status and roster."""
        try:
            # Get current status
            draft_status = self.espn_connector.get_draft_status()
            current_roster = self.espn_connector.get_current_roster()
            league_info = self.espn_connector.get_league_info()
            
            # Display draft status
            print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}DRAFT STATUS{Style.RESET_ALL}")
            print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
            
            if draft_status['status'] == 'active':
                print(f"{Fore.GREEN}Round: {draft_status['current_round']}{Style.RESET_ALL}")
                print(f"{Fore.GREEN}Pick: {draft_status['current_pick']}{Style.RESET_ALL}")
                print(f"{Fore.GREEN}Current Team: {draft_status['current_team']}{Style.RESET_ALL}")
                
                if draft_status['is_my_turn']:
                    print(f"{Fore.YELLOW}🎯 IT'S YOUR TURN TO PICK! 🎯{Style.RESET_ALL}")
                else:
                    print(f"{Fore.BLUE}Waiting for other teams...{Style.RESET_ALL}")
                
                if draft_status.get('time_remaining'):
                    print(f"{Fore.YELLOW}Time Remaining: {draft_status['time_remaining']}{Style.RESET_ALL}")
            
            elif draft_status['status'] == 'draft_complete':
                print(f"{Fore.GREEN}Draft Complete!{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}Draft Status: {draft_status['message']}{Style.RESET_ALL}")
            
            # Display current roster
            print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}CURRENT ROSTER ({len(current_roster)} players){Style.RESET_ALL}")
            print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
            
            if current_roster:
                # Group by position
                position_players = {}
                for player in current_roster:
                    pos = player['position']
                    if pos not in position_players:
                        position_players[pos] = []
                    position_players[pos].append(player)
                
                for pos in ['QB', 'RB', 'WR', 'TE', 'K', 'DEF']:
                    if pos in position_players:
                        print(f"\n{Fore.YELLOW}{pos}s:{Style.RESET_ALL}")
                        for player in position_players[pos]:
                            points = player.get('projected_points', 0)
                            print(f"  • {player['name']} ({player['team']}) - {points:.1f} pts")
            else:
                print(f"{Fore.BLUE}No players drafted yet.{Style.RESET_ALL}")
            
            # Display roster analysis
            if current_roster:
                self._show_roster_analysis(current_roster)
            
        except Exception as e:
            print(f"{Fore.RED}Error getting current status: {e}{Style.RESET_ALL}")
    
    def _show_roster_analysis(self, roster: List[Dict]):
        """Display roster analysis and insights."""
        try:
            analysis = self.roster_evaluator.analyze_roster_composition(roster)
            
            print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}ROSTER ANALYSIS{Style.RESET_ALL}")
            print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
            
            # Position counts
            print(f"{Fore.YELLOW}Position Breakdown:{Style.RESET_ALL}")
            for pos, count in analysis['position_counts'].items():
                print(f"  {pos}: {count}")
            
            # Positional needs
            print(f"\n{Fore.YELLOW}Positional Needs:{Style.RESET_ALL}")
            for pos, need_info in analysis['needs'].items():
                if need_info['deficit'] > 0:
                    print(f"  {Fore.RED}Need {need_info['deficit']} more {pos}(s){Style.RESET_ALL}")
                elif need_info['surplus'] > 0:
                    print(f"  {Fore.GREEN}Have {need_info['surplus']} extra {pos}(s){Style.RESET_ALL}")
                else:
                    print(f"  {Fore.GREEN}{pos}: Balanced{Style.RESET_ALL}")
            
            # Roster strength
            print(f"\n{Fore.YELLOW}Roster Strength Score: {analysis['strength_score']:.1f}{Style.RESET_ALL}")
            
        except Exception as e:
            print(f"{Fore.RED}Error analyzing roster: {e}{Style.RESET_ALL}")
    
    def get_ai_recommendation(self, show_details: bool = True):
        """Get AI recommendation for current draft situation."""
        try:
            print(f"\n{Fore.CYAN}🤖 Getting AI Recommendation...{Style.RESET_ALL}")
            
            # Get current context
            draft_status = self.espn_connector.get_draft_status()
            current_roster = self.espn_connector.get_current_roster()
            available_players = self.espn_connector.get_available_players(20)
            league_info = self.espn_connector.get_league_info()
            
            if draft_status['status'] != 'active':
                print(f"{Fore.RED}No active draft found.{Style.RESET_ALL}")
                return
            
            context = {
                'draft_status': draft_status,
                'current_roster': current_roster,
                'available_players': available_players,
                'league_info': league_info
            }
            
            # Get AI recommendation
            recommendation = self.gpt_agent.generate_draft_recommendation(context)
            
            # Display recommendation
            self._display_recommendation(recommendation, show_details)
            
        except Exception as e:
            print(f"{Fore.RED}Error getting AI recommendation: {e}{Style.RESET_ALL}")
    
    def _display_recommendation(self, recommendation: Dict, show_details: bool):
        """Display the AI recommendation in a formatted way."""
        print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}🤖 AI DRAFT RECOMMENDATION{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        
        # Display top recommendations
        if recommendation.get('recommendations'):
            print(f"\n{Fore.YELLOW}TOP RECOMMENDATIONS:{Style.RESET_ALL}")
            for i, rec in enumerate(recommendation['recommendations'][:5], 1):
                print(f"  {i}. {rec}")
        
        # Display confidence
        confidence = recommendation.get('confidence', 5)
        confidence_color = Fore.GREEN if confidence >= 7 else Fore.YELLOW if confidence >= 5 else Fore.RED
        print(f"\n{Fore.YELLOW}Confidence Level: {confidence_color}{confidence}/10{Style.RESET_ALL}")
        
        # Display strategy notes if detailed view requested
        if show_details and recommendation.get('strategy_notes'):
            print(f"\n{Fore.YELLOW}STRATEGIC ANALYSIS:{Style.RESET_ALL}")
            print(f"{recommendation['strategy_notes']}")
        
        # Display risks if any
        if recommendation.get('risks'):
            print(f"\n{Fore.RED}POTENTIAL RISKS:{Style.RESET_ALL}")
            for risk in recommendation['risks']:
                print(f"  • {risk}")
    
    def show_available_players(self, limit: int = 10):
        """Display top available players."""
        try:
            available_players = self.espn_connector.get_available_players(limit)
            
            print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}TOP {limit} AVAILABLE PLAYERS{Style.RESET_ALL}")
            print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
            
            for i, player in enumerate(available_players, 1):
                points = player.get('projected_points', 0)
                rank = player.get('rank', 0)
                print(f"{i:2d}. {player['name']:<20} ({player['position']}, {player['team']}) - "
                      f"{points:6.1f} pts, Rank: {rank:3d}")
            
        except Exception as e:
            print(f"{Fore.RED}Error getting available players: {e}{Style.RESET_ALL}")
    
    def monitor_draft(self, polling_interval: int = 30):
        """Monitor draft in real-time and provide recommendations."""
        print(f"{Fore.CYAN}Starting draft monitoring...{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Press Ctrl+C to stop monitoring{Style.RESET_ALL}")
        
        self.is_monitoring = True
        
        def draft_callback(context):
            """Callback function called when it's our turn to pick."""
            print(f"\n{Fore.GREEN}{'='*60}{Style.RESET_ALL}")
            print(f"{Fore.GREEN}🎯 IT'S YOUR TURN TO PICK! 🎯{Style.RESET_ALL}")
            print(f"{Fore.GREEN}{'='*60}{Style.RESET_ALL}")
            
            # Show current status
            self.show_current_status()
            
            # Get AI recommendation
            self.get_ai_recommendation(show_details=True)
            
            # Show available players
            self.show_available_players(10)
            
            print(f"\n{Fore.YELLOW}Make your pick on ESPN, then press Enter to continue monitoring...{Style.RESET_ALL}")
            input()
        
        try:
            self.espn_connector.monitor_draft(
                callback=draft_callback,
                polling_interval=polling_interval
            )
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}Draft monitoring stopped.{Style.RESET_ALL}")
            self.is_monitoring = False
    
    def show_draft_history(self):
        """Display complete draft history."""
        try:
            draft_history = self.espn_connector.get_draft_history()
            
            print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}DRAFT HISTORY{Style.RESET_ALL}")
            print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
            
            if not draft_history:
                print(f"{Fore.BLUE}No draft history available.{Style.RESET_ALL}")
                return
            
            # Group by round
            rounds = {}
            for pick in draft_history:
                round_num = pick['round']
                if round_num not in rounds:
                    rounds[round_num] = []
                rounds[round_num].append(pick)
            
            for round_num in sorted(rounds.keys()):
                print(f"\n{Fore.YELLOW}Round {round_num}:{Style.RESET_ALL}")
                for pick in rounds[round_num]:
                    player_name = pick.get('player', 'No player selected')
                    team_name = pick.get('team', 'Unknown')
                    position = pick.get('position', '')
                    
                    if position:
                        print(f"  Pick {pick['pick']}: {player_name} ({position}) - {team_name}")
                    else:
                        print(f"  Pick {pick['pick']}: {player_name} - {team_name}")
            
        except Exception as e:
            print(f"{Fore.RED}Error getting draft history: {e}{Style.RESET_ALL}")
    
    def update_fantasy_data(self):
        """Update fantasy football data from various sources."""
        print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}🔄 UPDATING FANTASY FOOTBALL DATA{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        
        try:
            from utils.data_manager import FantasyDataManager
            
            print(f"{Fore.YELLOW}This will update ADP, projections, injuries, and expert rankings...{Style.RESET_ALL}")
            response = input(f"{Fore.CYAN}Continue? (y/n): {Style.RESET_ALL}").strip().lower()
            
            if response not in ['y', 'yes']:
                print(f"{Fore.YELLOW}Update cancelled.{Style.RESET_ALL}")
                return
            
            with FantasyDataManager() as manager:
                print(f"{Fore.GREEN}Updating all data sources...{Style.RESET_ALL}")
                results = manager.update_all_data(force_update=True)
                
                print(f"\n{Fore.GREEN}✅ Data update completed!{Style.RESET_ALL}")
                
                # Show summary
                for data_type, data in results.items():
                    if isinstance(data, dict):
                        print(f"  {data_type}: {len(data)} sources")
                    else:
                        print(f"  {data_type}: {len(data)} records")
                
                # Show data summary
                summary = manager.get_data_summary()
                print(f"\n{Fore.CYAN}Total records: {summary['total_records']:,}{Style.RESET_ALL}")
                print(f"{Fore.CYAN}Data files: {len(summary['data_files'])}{Style.RESET_ALL}")
        
        except ImportError:
            print(f"{Fore.RED}Data manager not available. Run 'python update_data.py --all' instead.{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}Error updating data: {e}{Style.RESET_ALL}")
    
    def show_help(self):
        """Display help information."""
        help_text = f"""
{Fore.CYAN}FANTASY DRAFT AI - COMMAND HELP{Style.RESET_ALL}

Available Commands:
  status          - Show current draft status and roster
  recommend       - Get AI recommendation for current pick
  players         - Show top available players
  monitor         - Start real-time draft monitoring
  history         - Show complete draft history
  update          - Update fantasy football data
  help            - Show this help message
  quit/exit       - Exit the application

Quick Commands:
  s               - status
  r               - recommend
  p               - players
  m               - monitor
  h               - history
  u               - update
  q               - quit
"""
        print(help_text)
    
    def run_interactive(self):
        """Run the interactive CLI."""
        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}🏈 FANTASY FOOTBALL DRAFT AI 🏈{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        
        # Authenticate first
        if not self.authenticate():
            print(f"{Fore.RED}Authentication failed. Exiting.{Style.RESET_ALL}")
            return
        
        print(f"\n{Fore.GREEN}Type 'help' for available commands{Style.RESET_ALL}")
        
        while True:
            try:
                command = input(f"\n{Fore.CYAN}draft-ai> {Style.RESET_ALL}").strip().lower()
                
                if command in ['quit', 'exit', 'q']:
                    print(f"{Fore.YELLOW}Goodbye!{Style.RESET_ALL}")
                    break
                elif command in ['help', 'h']:
                    self.show_help()
                elif command in ['status', 's']:
                    self.show_current_status()
                elif command in ['recommend', 'r']:
                    self.get_ai_recommendation()
                elif command in ['players', 'p']:
                    self.show_available_players()
                elif command in ['monitor', 'm']:
                    self.monitor_draft()
                elif command in ['history', 'h']:
                    self.show_draft_history()
                elif command in ['update', 'u']:
                    self.update_fantasy_data()
                elif command == '':
                    continue
                else:
                    print(f"{Fore.RED}Unknown command: {command}{Style.RESET_ALL}")
                    print(f"Type 'help' for available commands")
                    
            except KeyboardInterrupt:
                print(f"\n{Fore.YELLOW}Use 'quit' to exit the application{Style.RESET_ALL}")
            except Exception as e:
                print(f"{Fore.RED}Error: {e}{Style.RESET_ALL}")


def main():
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(description='Fantasy Football Draft AI')
    parser.add_argument('--command', '-c', help='Run a single command and exit')
    parser.add_argument('--monitor', '-m', action='store_true', help='Start draft monitoring')
    parser.add_argument('--status', '-s', action='store_true', help='Show current status')
    parser.add_argument('--recommend', '-r', action='store_true', help='Get AI recommendation')
    
    args = parser.parse_args()
    
    cli = CLIInterface()
    
    if args.command:
        # Run single command
        if args.command == 'status':
            cli.show_current_status()
        elif args.command == 'recommend':
            cli.get_ai_recommendation()
        elif args.command == 'monitor':
            cli.monitor_draft()
        else:
            print(f"Unknown command: {args.command}")
    elif args.monitor:
        cli.monitor_draft()
    elif args.status:
        cli.show_current_status()
    elif args.recommend:
        cli.get_ai_recommendation()
    else:
        # Run interactive mode
        cli.run_interactive()


if __name__ == "__main__":
    main() 