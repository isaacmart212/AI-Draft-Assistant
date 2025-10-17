#!/usr/bin/env python3
"""
Fantasy Football Data Update Tool
Command-line interface for updating fantasy football data from various sources
"""

import argparse
import sys
import os
from datetime import datetime
from utils.data_manager import FantasyDataManager

def print_banner():
    """Print the tool banner"""
    print("=" * 60)
    print("🏈 Fantasy Football Data Update Tool 🏈")
    print("=" * 60)
    print("Updates ADP, projections, injuries, and expert rankings")
    print("from multiple fantasy football websites and experts")
    print("=" * 60)

def update_specific_data(manager: FantasyDataManager, data_type: str, force: bool = False):
    """Update specific data type"""
    print(f"\n🔄 Updating {data_type} data...")
    
    try:
        if data_type == "adp":
            data = manager.update_adp_data(force_update=force)
            print(f"✅ ADP data updated: {len(data)} players")
        elif data_type == "projections":
            data = manager.update_projections_data(force_update=force)
            print(f"✅ Projections data updated: {len(data)} players")
        elif data_type == "injuries":
            data = manager.update_injury_data(force_update=force)
            print(f"✅ Injury data updated: {len(data)} players")
        elif data_type == "stats":
            data = manager.update_historical_stats(force_update=force)
            print(f"✅ Historical stats updated: {len(data)} players")
        elif data_type == "rankings":
            data = manager.update_expert_rankings(force_update=force)
            print(f"✅ Expert rankings updated: {len(data)} sources")
        else:
            print(f"❌ Unknown data type: {data_type}")
            return False
        
        return True
    except Exception as e:
        print(f"❌ Error updating {data_type} data: {e}")
        return False

def show_data_summary(manager: FantasyDataManager):
    """Show summary of current data"""
    print("\n📊 Current Data Summary:")
    print("-" * 40)
    
    summary = manager.get_data_summary()
    
    print(f"Total records: {summary['total_records']:,}")
    print(f"Data files: {len(summary['data_files'])}")
    
    if summary['metadata']:
        print("\n📅 Last Updates:")
        for data_type, info in summary['metadata'].items():
            last_update = info.get('last_update', 'Unknown')
            record_count = info.get('record_count', 0)
            source = info.get('source', 'Unknown')
            print(f"  {data_type.title()}: {record_count:,} records ({source}) - {last_update[:10]}")
    
    if summary['data_files']:
        print("\n📁 Data Files:")
        for filename, info in summary['data_files'].items():
            records = info['records']
            last_modified = info['last_modified'][:10]
            print(f"  {filename}: {records:,} records (modified: {last_modified})")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="Update fantasy football data from various sources",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python update_data.py --all                    # Update all data
  python update_data.py --adp --force            # Force update ADP data
  python update_data.py --summary                # Show data summary
  python update_data.py --cleanup                # Clean up old data files
        """
    )
    
    # Data update options
    parser.add_argument('--all', action='store_true', 
                       help='Update all data types')
    parser.add_argument('--adp', action='store_true', 
                       help='Update ADP (Average Draft Position) data')
    parser.add_argument('--projections', action='store_true', 
                       help='Update player projections')
    parser.add_argument('--injuries', action='store_true', 
                       help='Update injury data')
    parser.add_argument('--stats', action='store_true', 
                       help='Update historical statistics')
    parser.add_argument('--rankings', action='store_true', 
                       help='Update expert rankings')
    
    # Other options
    parser.add_argument('--summary', action='store_true', 
                       help='Show current data summary')
    parser.add_argument('--force', action='store_true', 
                       help='Force update even if data is fresh')
    parser.add_argument('--cleanup', action='store_true', 
                       help='Clean up old data files')
    parser.add_argument('--data-dir', default='data', 
                       help='Data directory (default: data)')
    parser.add_argument('--cache-duration', type=int, default=3600, 
                       help='Cache duration in seconds (default: 3600)')
    
    args = parser.parse_args()
    
    # Show banner
    print_banner()
    
    # Initialize data manager
    try:
        manager = FantasyDataManager(
            data_dir=args.data_dir,
            cache_duration=args.cache_duration
        )
    except Exception as e:
        print(f"❌ Error initializing data manager: {e}")
        sys.exit(1)
    
    try:
        # Handle different commands
        if args.summary:
            show_data_summary(manager)
        
        elif args.cleanup:
            print("\n🧹 Cleaning up old data files...")
            manager.cleanup_old_data()
            print("✅ Cleanup completed")
        
        elif args.all:
            print("\n🚀 Updating all data sources...")
            start_time = datetime.now()
            
            results = manager.update_all_data(force_update=args.force)
            
            end_time = datetime.now()
            duration = end_time - start_time
            
            print(f"\n✅ All data updated in {duration.total_seconds():.1f} seconds")
            
            # Show results summary
            for data_type, data in results.items():
                if isinstance(data, dict):
                    print(f"  {data_type}: {len(data)} sources")
                else:
                    print(f"  {data_type}: {len(data)} records")
        
        else:
            # Update specific data types
            data_types = []
            if args.adp:
                data_types.append("adp")
            if args.projections:
                data_types.append("projections")
            if args.injuries:
                data_types.append("injuries")
            if args.stats:
                data_types.append("stats")
            if args.rankings:
                data_types.append("rankings")
            
            if not data_types:
                print("\n❌ No data types specified. Use --help for options.")
                show_data_summary(manager)
                return
            
            success_count = 0
            for data_type in data_types:
                if update_specific_data(manager, data_type, args.force):
                    success_count += 1
            
            print(f"\n✅ Successfully updated {success_count}/{len(data_types)} data types")
        
        # Show final summary
        if not args.summary:
            show_data_summary(manager)
    
    except KeyboardInterrupt:
        print("\n\n⏹️  Update interrupted by user")
    except Exception as e:
        print(f"\n❌ Error during update: {e}")
        sys.exit(1)
    finally:
        manager.close()

if __name__ == "__main__":
    main() 