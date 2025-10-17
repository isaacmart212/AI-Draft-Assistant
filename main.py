"""
Main Entry Point for Fantasy Football Draft AI

Supports both command-line and web interfaces.
"""

import os
import sys
import argparse
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def check_environment():
    """Check if all required environment variables are set."""
    required_vars = [
        'ESPN_USERNAME',
        'ESPN_PASSWORD', 
        'OPENAI_API_KEY',
        'LEAGUE_ID',
        'TEAM_ID'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease create a .env file based on .env.example")
        return False
    
    # Check if required directories exist
    required_dirs = ['data', 'prompts', 'ai', 'utils', 'ui']
    for dir_name in required_dirs:
        if not os.path.exists(dir_name):
            print(f"❌ Required directory '{dir_name}' not found.")
            return False
    
    # Check if data files exist
    data_files = ['data/adp.csv', 'data/projections.csv', 'data/risk_profiles.csv']
    missing_files = [f for f in data_files if not os.path.exists(f)]
    if missing_files:
        print(f"⚠️  Some data files missing: {', '.join(missing_files)}")
        print("   Run 'python update_data.py --all' to fetch fresh data.")
    
    return True


def run_cli():
    """Run the command-line interface."""
    try:
        from ui.cli_interface import CLIInterface
        cli = CLIInterface()
        cli.run_interactive()
    except ImportError as e:
        print(f"❌ Error importing CLI interface: {e}")
        print("Make sure all dependencies are installed: pip install -r requirements.txt")
    except Exception as e:
        print(f"❌ Error running CLI: {e}")


def run_web():
    """Run the web interface using Streamlit."""
    try:
        import streamlit as st
        from ui.streamlit_ui import run_streamlit_app
        run_streamlit_app()
    except ImportError as e:
        print(f"❌ Error importing Streamlit: {e}")
        print("Install Streamlit: pip install streamlit")
    except Exception as e:
        print(f"❌ Error running web interface: {e}")


def run_test():
    """Run a test to verify all components are working."""
    print("🧪 Running system test...")
    
    try:
        # Test ESPN connector
        print("Testing ESPN connector...")
        from demo_espn_connector import DemoESPNConnector
        connector = DemoESPNConnector()
        print("✓ ESPN connector initialized")
        
        # Test GPT agent
        print("Testing GPT agent...")
        from ai.gpt_agent import GPTAgent
        agent = GPTAgent()
        print("✓ GPT agent initialized")
        
        # Test prompt builder
        print("Testing prompt builder...")
        from prompts.prompt_builder import PromptBuilder
        builder = PromptBuilder()
        print("✓ Prompt builder initialized")
        
        # Test roster evaluator
        print("Testing roster evaluator...")
        from utils.roster_eval import RosterEvaluator
        evaluator = RosterEvaluator()
        print("✓ Roster evaluator initialized")
        
        print("✅ All components working correctly!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    
    return True


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='AI-Powered Fantasy Football Draft Assistant',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                    # Run interactive CLI
  python main.py --web              # Run web interface
  python main.py --test             # Run system test
  python main.py --cli --status     # Show current status
  python main.py --cli --monitor    # Start draft monitoring
        """
    )
    
    parser.add_argument(
        '--mode', '-m',
        choices=['cli', 'web'],
        default='cli',
        help='Interface mode (default: cli)'
    )
    
    parser.add_argument(
        '--web', '-w',
        action='store_true',
        help='Run web interface (same as --mode web)'
    )
    
    parser.add_argument(
        '--cli', '-c',
        action='store_true',
        help='Run CLI interface (same as --mode cli)'
    )
    
    parser.add_argument(
        '--test', '-t',
        action='store_true',
        help='Run system test to verify all components'
    )
    
    parser.add_argument(
        '--status', '-s',
        action='store_true',
        help='Show current draft status (CLI only)'
    )
    
    parser.add_argument(
        '--monitor', '-M',
        action='store_true',
        help='Start draft monitoring (CLI only)'
    )
    
    parser.add_argument(
        '--recommend', '-r',
        action='store_true',
        help='Get AI recommendation (CLI only)'
    )
    
    args = parser.parse_args()
    
    # Determine mode
    if args.web:
        mode = 'web'
    elif args.cli:
        mode = 'cli'
    else:
        mode = args.mode
    
    # Check environment variables
    if not check_environment():
        sys.exit(1)
    
    # Run test if requested
    if args.test:
        if run_test():
            print("✅ System test passed!")
        else:
            print("❌ System test failed!")
            sys.exit(1)
        return
    
    # Run CLI with specific commands
    if mode == 'cli' and (args.status or args.monitor or args.recommend):
        try:
            from ui.cli_interface import CLIInterface
            cli = CLIInterface()
            
            if args.status:
                cli.show_current_status()
            elif args.monitor:
                cli.monitor_draft()
            elif args.recommend:
                cli.get_ai_recommendation()
                
        except Exception as e:
            print(f"❌ Error running CLI command: {e}")
            sys.exit(1)
        return
    
    # Run main interface
    if mode == 'cli':
        print("🏈 Starting Fantasy Football Draft AI (CLI Mode)")
        run_cli()
    elif mode == 'web':
        print("🏈 Starting Fantasy Football Draft AI (Web Mode)")
        run_web()
    else:
        print(f"❌ Unknown mode: {mode}")
        sys.exit(1)


if __name__ == "__main__":
    main() 