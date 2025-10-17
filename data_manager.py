"""
Fantasy Football Data Manager
Manages data updates, caching, and integration with the main system
"""

import pandas as pd
import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from .data_scraper import FantasyDataScraper

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FantasyDataManager:
    """Manages fantasy football data from multiple sources"""
    
    def __init__(self, data_dir: str = "data", cache_duration: int = 3600):
        """
        Initialize the data manager
        
        Args:
            data_dir: Directory to store data files
            cache_duration: Cache duration in seconds (default 1 hour)
        """
        self.data_dir = data_dir
        self.cache_duration = cache_duration
        self.scraper = None
        self.metadata_file = os.path.join(data_dir, "data_metadata.json")
        
        # Ensure data directory exists
        os.makedirs(data_dir, exist_ok=True)
        
        # Load metadata
        self.metadata = self._load_metadata()
    
    def _load_metadata(self) -> Dict:
        """Load data metadata from file"""
        if os.path.exists(self.metadata_file):
            try:
                with open(self.metadata_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading metadata: {e}")
        return {}
    
    def _save_metadata(self):
        """Save data metadata to file"""
        try:
            with open(self.metadata_file, 'w') as f:
                json.dump(self.metadata, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving metadata: {e}")
    
    def _get_scraper(self) -> FantasyDataScraper:
        """Get or create scraper instance"""
        if self.scraper is None:
            self.scraper = FantasyDataScraper(headless=True, cache_duration=self.cache_duration)
        return self.scraper
    
    def _is_data_fresh(self, data_type: str) -> bool:
        """Check if data is fresh based on cache duration"""
        if data_type not in self.metadata:
            return False
        
        last_update = self.metadata[data_type].get('last_update')
        if not last_update:
            return False
        
        try:
            last_update_dt = datetime.fromisoformat(last_update)
            return datetime.now() - last_update_dt < timedelta(seconds=self.cache_duration)
        except Exception:
            return False
    
    def _update_metadata(self, data_type: str, record_count: int, source: str = "web_scraper"):
        """Update metadata for a data type"""
        self.metadata[data_type] = {
            'last_update': datetime.now().isoformat(),
            'record_count': record_count,
            'source': source,
            'file_path': f"{data_type}.csv"
        }
        self._save_metadata()
    
    def update_adp_data(self, force_update: bool = False) -> pd.DataFrame:
        """
        Update ADP (Average Draft Position) data
        
        Args:
            force_update: Force update even if data is fresh
            
        Returns:
            DataFrame with ADP data
        """
        if not force_update and self._is_data_fresh('adp'):
            logger.info("ADP data is fresh, loading from cache")
            return self.load_adp_data()
        
        logger.info("Updating ADP data...")
        scraper = self._get_scraper()
        
        # Try multiple sources for ADP data
        adp_data = pd.DataFrame()
        
        # Try FantasyPros first
        try:
            adp_data = scraper.scrape_fantasypros_adp()
            if not adp_data.empty:
                logger.info(f"Successfully scraped {len(adp_data)} players from FantasyPros")
        except Exception as e:
            logger.error(f"Error scraping FantasyPros ADP: {e}")
        
        # Fallback to Fantasy Football Calculator
        if adp_data.empty:
            try:
                adp_data = scraper.scrape_fantasyfootballcalculator_adp()
                if not adp_data.empty:
                    logger.info(f"Successfully scraped {len(adp_data)} players from Fantasy Football Calculator")
            except Exception as e:
                logger.error(f"Error scraping Fantasy Football Calculator ADP: {e}")
        
        # Save data if we got any
        if not adp_data.empty:
            file_path = os.path.join(self.data_dir, "adp_updated.csv")
            adp_data.to_csv(file_path, index=False)
            self._update_metadata('adp', len(adp_data), 'fantasypros')
            logger.info(f"ADP data saved to {file_path}")
        else:
            logger.warning("No ADP data could be scraped, using fallback data")
            adp_data = self.load_fallback_adp_data()
        
        return adp_data
    
    def update_projections_data(self, force_update: bool = False) -> pd.DataFrame:
        """
        Update player projections data
        
        Args:
            force_update: Force update even if data is fresh
            
        Returns:
            DataFrame with projections data
        """
        if not force_update and self._is_data_fresh('projections'):
            logger.info("Projections data is fresh, loading from cache")
            return self.load_projections_data()
        
        logger.info("Updating projections data...")
        scraper = self._get_scraper()
        
        # Try to get projections from ESPN
        projections_data = scraper.scrape_espn_projections()
        
        if not projections_data.empty:
            file_path = os.path.join(self.data_dir, "projections_updated.csv")
            projections_data.to_csv(file_path, index=False)
            self._update_metadata('projections', len(projections_data), 'espn')
            logger.info(f"Projections data saved to {file_path}")
        else:
            logger.warning("No projections data could be scraped, using fallback data")
            projections_data = self.load_fallback_projections_data()
        
        return projections_data
    
    def update_injury_data(self, force_update: bool = False) -> pd.DataFrame:
        """
        Update injury data
        
        Args:
            force_update: Force update even if data is fresh
            
        Returns:
            DataFrame with injury data
        """
        if not force_update and self._is_data_fresh('injuries'):
            logger.info("Injury data is fresh, loading from cache")
            return self.load_injury_data()
        
        logger.info("Updating injury data...")
        scraper = self._get_scraper()
        
        injury_data = scraper.scrape_rotowire_injuries()
        
        if not injury_data.empty:
            file_path = os.path.join(self.data_dir, "injury_updates.csv")
            injury_data.to_csv(file_path, index=False)
            self._update_metadata('injuries', len(injury_data), 'rotowire')
            logger.info(f"Injury data saved to {file_path}")
        else:
            logger.warning("No injury data could be scraped")
            injury_data = pd.DataFrame()
        
        return injury_data
    
    def update_historical_stats(self, force_update: bool = False) -> pd.DataFrame:
        """
        Update historical statistics data
        
        Args:
            force_update: Force update even if data is fresh
            
        Returns:
            DataFrame with historical stats
        """
        if not force_update and self._is_data_fresh('historical_stats'):
            logger.info("Historical stats data is fresh, loading from cache")
            return self.load_historical_stats()
        
        logger.info("Updating historical stats...")
        scraper = self._get_scraper()
        
        stats_data = scraper.scrape_profootballreference_stats()
        
        if not stats_data.empty:
            file_path = os.path.join(self.data_dir, "historical_stats.csv")
            stats_data.to_csv(file_path, index=False)
            self._update_metadata('historical_stats', len(stats_data), 'pro_football_reference')
            logger.info(f"Historical stats saved to {file_path}")
        else:
            logger.warning("No historical stats could be scraped")
            stats_data = pd.DataFrame()
        
        return stats_data
    
    def update_expert_rankings(self, force_update: bool = False) -> Dict[str, pd.DataFrame]:
        """
        Update expert rankings from multiple sources
        
        Args:
            force_update: Force update even if data is fresh
            
        Returns:
            Dictionary of DataFrames with expert rankings by source
        """
        if not force_update and self._is_data_fresh('expert_rankings'):
            logger.info("Expert rankings data is fresh, loading from cache")
            return self.load_expert_rankings()
        
        logger.info("Updating expert rankings...")
        scraper = self._get_scraper()
        
        rankings = scraper.scrape_expert_rankings()
        
        if rankings:
            for source, df in rankings.items():
                if not df.empty:
                    file_path = os.path.join(self.data_dir, f"rankings_{source}.csv")
                    df.to_csv(file_path, index=False)
                    logger.info(f"{source} rankings saved to {file_path}")
            
            # Update metadata
            total_rankings = sum(len(df) for df in rankings.values())
            self._update_metadata('expert_rankings', total_rankings, 'multiple_sources')
        else:
            logger.warning("No expert rankings could be scraped")
        
        return rankings
    
    def update_all_data(self, force_update: bool = False) -> Dict[str, pd.DataFrame]:
        """
        Update all data sources
        
        Args:
            force_update: Force update even if data is fresh
            
        Returns:
            Dictionary with all updated data
        """
        logger.info("Starting comprehensive data update...")
        
        results = {}
        
        # Update each data type
        results['adp'] = self.update_adp_data(force_update)
        results['projections'] = self.update_projections_data(force_update)
        results['injuries'] = self.update_injury_data(force_update)
        results['historical_stats'] = self.update_historical_stats(force_update)
        results['expert_rankings'] = self.update_expert_rankings(force_update)
        
        # Generate updated risk profiles
        risk_profiles = self._generate_updated_risk_profiles(results)
        if not risk_profiles.empty:
            file_path = os.path.join(self.data_dir, "risk_profiles_updated.csv")
            risk_profiles.to_csv(file_path, index=False)
            self._update_metadata('risk_profiles', len(risk_profiles), 'generated')
            results['risk_profiles'] = risk_profiles
            logger.info(f"Updated risk profiles saved to {file_path}")
        
        logger.info("Comprehensive data update completed!")
        return results
    
    def _generate_updated_risk_profiles(self, data_dict: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """Generate updated risk profiles based on all available data"""
        scraper = self._get_scraper()
        return scraper._generate_risk_profiles(
            data_dict.get('adp', pd.DataFrame()),
            data_dict.get('injuries', pd.DataFrame()),
            data_dict.get('historical_stats', pd.DataFrame())
        )
    
    def load_adp_data(self) -> pd.DataFrame:
        """Load ADP data from file"""
        file_path = os.path.join(self.data_dir, "adp_updated.csv")
        if os.path.exists(file_path):
            return pd.read_csv(file_path)
        return self.load_fallback_adp_data()
    
    def load_projections_data(self) -> pd.DataFrame:
        """Load projections data from file"""
        file_path = os.path.join(self.data_dir, "projections_updated.csv")
        if os.path.exists(file_path):
            return pd.read_csv(file_path)
        return self.load_fallback_projections_data()
    
    def load_injury_data(self) -> pd.DataFrame:
        """Load injury data from file"""
        file_path = os.path.join(self.data_dir, "injury_updates.csv")
        if os.path.exists(file_path):
            return pd.read_csv(file_path)
        return pd.DataFrame()
    
    def load_historical_stats(self) -> pd.DataFrame:
        """Load historical stats from file"""
        file_path = os.path.join(self.data_dir, "historical_stats.csv")
        if os.path.exists(file_path):
            return pd.read_csv(file_path)
        return pd.DataFrame()
    
    def load_expert_rankings(self) -> Dict[str, pd.DataFrame]:
        """Load expert rankings from files"""
        rankings = {}
        for file in os.listdir(self.data_dir):
            if file.startswith("rankings_") and file.endswith(".csv"):
                source = file.replace("rankings_", "").replace(".csv", "")
                file_path = os.path.join(self.data_dir, file)
                rankings[source] = pd.read_csv(file_path)
        return rankings
    
    def load_risk_profiles(self) -> pd.DataFrame:
        """Load risk profiles from file"""
        file_path = os.path.join(self.data_dir, "risk_profiles_updated.csv")
        if os.path.exists(file_path):
            return pd.read_csv(file_path)
        return self.load_fallback_risk_profiles()
    
    def load_fallback_adp_data(self) -> pd.DataFrame:
        """Load fallback ADP data"""
        file_path = os.path.join(self.data_dir, "adp.csv")
        if os.path.exists(file_path):
            return pd.read_csv(file_path)
        logger.warning("No ADP data available")
        return pd.DataFrame()
    
    def load_fallback_projections_data(self) -> pd.DataFrame:
        """Load fallback projections data"""
        file_path = os.path.join(self.data_dir, "projections.csv")
        if os.path.exists(file_path):
            return pd.read_csv(file_path)
        logger.warning("No projections data available")
        return pd.DataFrame()
    
    def load_fallback_risk_profiles(self) -> pd.DataFrame:
        """Load fallback risk profiles"""
        file_path = os.path.join(self.data_dir, "risk_profiles.csv")
        if os.path.exists(file_path):
            return pd.read_csv(file_path)
        logger.warning("No risk profiles available")
        return pd.DataFrame()
    
    def get_data_summary(self) -> Dict:
        """Get summary of all available data"""
        summary = {
            'metadata': self.metadata,
            'data_files': {},
            'total_records': 0
        }
        
        for file in os.listdir(self.data_dir):
            if file.endswith('.csv'):
                file_path = os.path.join(self.data_dir, file)
                try:
                    df = pd.read_csv(file_path)
                    summary['data_files'][file] = {
                        'records': len(df),
                        'columns': list(df.columns),
                        'last_modified': datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
                    }
                    summary['total_records'] += len(df)
                except Exception as e:
                    logger.error(f"Error reading {file}: {e}")
        
        return summary
    
    def cleanup_old_data(self, days_to_keep: int = 7):
        """Clean up old data files"""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        for file in os.listdir(self.data_dir):
            if file.endswith('.csv') and file != 'adp.csv' and file != 'projections.csv' and file != 'risk_profiles.csv':
                file_path = os.path.join(self.data_dir, file)
                file_date = datetime.fromtimestamp(os.path.getmtime(file_path))
                
                if file_date < cutoff_date:
                    try:
                        os.remove(file_path)
                        logger.info(f"Removed old data file: {file}")
                    except Exception as e:
                        logger.error(f"Error removing {file}: {e}")
    
    def close(self):
        """Close the scraper and clean up resources"""
        if self.scraper:
            self.scraper.close()
            self.scraper = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def main():
    """Main function to demonstrate the data manager"""
    print("Fantasy Football Data Manager")
    print("=" * 40)
    
    with FantasyDataManager() as manager:
        # Get data summary
        summary = manager.get_data_summary()
        print(f"Current data summary:")
        print(f"Total records: {summary['total_records']}")
        print(f"Data files: {len(summary['data_files'])}")
        
        # Update all data
        print("\nUpdating all data...")
        results = manager.update_all_data(force_update=True)
        
        # Show results
        for data_type, df in results.items():
            if isinstance(df, dict):
                print(f"{data_type}: {len(df)} sources")
            else:
                print(f"{data_type}: {len(df)} records")
        
        # Show updated summary
        summary = manager.get_data_summary()
        print(f"\nUpdated data summary:")
        print(f"Total records: {summary['total_records']}")
        print(f"Data files: {len(summary['data_files'])}")


if __name__ == "__main__":
    main() 