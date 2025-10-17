"""
Fantasy Football Data Scraper
Fetches real-time data from various fantasy football websites and experts
"""

import requests
import pandas as pd
import time
import logging
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FantasyDataScraper:
    """Main class for scraping fantasy football data from various sources"""
    
    def __init__(self, headless: bool = True, cache_duration: int = 3600):
        """
        Initialize the scraper
        
        Args:
            headless: Run browser in headless mode
            cache_duration: Cache duration in seconds (default 1 hour)
        """
        self.headless = headless
        self.cache_duration = cache_duration
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.driver = None
        self.cache = {}
        
    def _get_driver(self):
        """Initialize and return a Chrome WebDriver"""
        if self.driver is None:
            chrome_options = Options()
            if self.headless:
                chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
        return self.driver
    
    def _get_cached_data(self, key: str) -> Optional[Dict]:
        """Get cached data if it's still valid"""
        if key in self.cache:
            timestamp, data = self.cache[key]
            if datetime.now() - timestamp < timedelta(seconds=self.cache_duration):
                return data
        return None
    
    def _cache_data(self, key: str, data: Dict):
        """Cache data with timestamp"""
        self.cache[key] = (datetime.now(), data)
    
    def scrape_fantasypros_adp(self) -> pd.DataFrame:
        """
        Scrape ADP data from FantasyPros
        Returns DataFrame with columns: rank, name, position, team, adp, tier
        """
        cache_key = "fantasypros_adp"
        cached = self._get_cached_data(cache_key)
        if cached:
            return pd.DataFrame(cached)
        
        try:
            logger.info("Scraping ADP data from FantasyPros...")
            url = "https://www.fantasypros.com/nfl/rankings/consensus-cheatsheets.php"
            
            driver = self._get_driver()
            driver.get(url)
            
            # Wait for the table to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "table"))
            )
            
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            table = soup.find('table', {'class': 'table'})
            
            if not table:
                logger.warning("Could not find ADP table on FantasyPros")
                return pd.DataFrame()
            
            data = []
            rows = table.find_all('tr')[1:]  # Skip header
            
            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 6:
                    rank = cols[0].get_text(strip=True)
                    name = cols[1].get_text(strip=True)
                    position = cols[2].get_text(strip=True)
                    team = cols[3].get_text(strip=True)
                    adp = cols[4].get_text(strip=True)
                    tier = cols[5].get_text(strip=True) if len(cols) > 5 else ""
                    
                    # Clean up ADP (remove '#' and convert to float)
                    adp_clean = re.sub(r'[^\d.]', '', adp)
                    adp_float = float(adp_clean) if adp_clean else 999.0
                    
                    data.append({
                        'rank': int(rank) if rank.isdigit() else 999,
                        'name': name,
                        'position': position,
                        'team': team,
                        'adp': adp_float,
                        'tier': tier
                    })
            
            df = pd.DataFrame(data)
            self._cache_data(cache_key, df.to_dict('records'))
            logger.info(f"Successfully scraped {len(df)} players from FantasyPros")
            return df
            
        except Exception as e:
            logger.error(f"Error scraping FantasyPros ADP: {e}")
            return pd.DataFrame()
    
    def scrape_espn_projections(self) -> pd.DataFrame:
        """
        Scrape player projections from ESPN
        Returns DataFrame with detailed projections
        """
        cache_key = "espn_projections"
        cached = self._get_cached_data(cache_key)
        if cached:
            return pd.DataFrame(cached)
        
        try:
            logger.info("Scraping projections from ESPN...")
            url = "https://www.espn.com/fantasy/football/story/_/id/12345678/fantasy-football-rankings-2024"
            
            # Note: ESPN's actual projections URL structure may vary
            # This is a placeholder - you'd need to find the actual projections page
            
            response = self.session.get(url)
            if response.status_code != 200:
                logger.warning(f"ESPN projections page returned status {response.status_code}")
                return pd.DataFrame()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # This would need to be customized based on ESPN's actual HTML structure
            # For now, return empty DataFrame
            logger.info("ESPN projections scraping not yet implemented")
            return pd.DataFrame()
            
        except Exception as e:
            logger.error(f"Error scraping ESPN projections: {e}")
            return pd.DataFrame()
    
    def scrape_profootballreference_stats(self) -> pd.DataFrame:
        """
        Scrape historical stats from Pro Football Reference
        Returns DataFrame with historical performance data
        """
        cache_key = "pfr_stats"
        cached = self._get_cached_data(cache_key)
        if cached:
            return pd.DataFrame(cached)
        
        try:
            logger.info("Scraping stats from Pro Football Reference...")
            url = "https://www.pro-football-reference.com/years/2023/fantasy.htm"
            
            response = self.session.get(url)
            if response.status_code != 200:
                logger.warning(f"PFR stats page returned status {response.status_code}")
                return pd.DataFrame()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            table = soup.find('table', {'id': 'fantasy'})
            
            if not table:
                logger.warning("Could not find fantasy stats table on PFR")
                return pd.DataFrame()
            
            data = []
            rows = table.find_all('tr')[1:]  # Skip header
            
            for row in rows:
                cols = row.find_all(['td', 'th'])
                if len(cols) >= 15:
                    name = cols[0].get_text(strip=True)
                    team = cols[1].get_text(strip=True)
                    age = cols[2].get_text(strip=True)
                    games = cols[3].get_text(strip=True)
                    passing_yds = cols[4].get_text(strip=True)
                    passing_td = cols[5].get_text(strip=True)
                    rushing_yds = cols[6].get_text(strip=True)
                    rushing_td = cols[7].get_text(strip=True)
                    receptions = cols[8].get_text(strip=True)
                    receiving_yds = cols[9].get_text(strip=True)
                    receiving_td = cols[10].get_text(strip=True)
                    fantasy_points = cols[11].get_text(strip=True)
                    
                    # Clean numeric values
                    def clean_numeric(val):
                        return float(val.replace(',', '')) if val and val != '' else 0.0
                    
                    data.append({
                        'name': name,
                        'team': team,
                        'age': int(age) if age.isdigit() else 0,
                        'games': int(games) if games.isdigit() else 0,
                        'passing_yards': clean_numeric(passing_yds),
                        'passing_tds': clean_numeric(passing_td),
                        'rushing_yards': clean_numeric(rushing_yds),
                        'rushing_tds': clean_numeric(rushing_td),
                        'receptions': clean_numeric(receptions),
                        'receiving_yards': clean_numeric(receiving_yds),
                        'receiving_tds': clean_numeric(receiving_td),
                        'fantasy_points': clean_numeric(fantasy_points)
                    })
            
            df = pd.DataFrame(data)
            self._cache_data(cache_key, df.to_dict('records'))
            logger.info(f"Successfully scraped {len(df)} players from Pro Football Reference")
            return df
            
        except Exception as e:
            logger.error(f"Error scraping Pro Football Reference stats: {e}")
            return pd.DataFrame()
    
    def scrape_rotowire_injuries(self) -> pd.DataFrame:
        """
        Scrape injury news and updates from Rotowire
        Returns DataFrame with injury information
        """
        cache_key = "rotowire_injuries"
        cached = self._get_cached_data(cache_key)
        if cached:
            return pd.DataFrame(cached)
        
        try:
            logger.info("Scraping injury news from Rotowire...")
            url = "https://www.rotowire.com/football/nfl-lineups.php"
            
            driver = self._get_driver()
            driver.get(url)
            
            # Wait for the page to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "lineup"))
            )
            
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            data = []
            # Look for injury indicators in player listings
            player_elements = soup.find_all('div', class_='lineup-player')
            
            for player_elem in player_elements:
                name_elem = player_elem.find('a', class_='player-name')
                if name_elem:
                    name = name_elem.get_text(strip=True)
                    
                    # Check for injury indicators
                    injury_status = "Healthy"
                    injury_notes = ""
                    
                    # Look for injury classes or text
                    if player_elem.find('span', class_='injury'):
                        injury_status = "Injured"
                        injury_elem = player_elem.find('span', class_='injury')
                        injury_notes = injury_elem.get_text(strip=True)
                    elif player_elem.find('span', class_='questionable'):
                        injury_status = "Questionable"
                    elif player_elem.find('span', class_='doubtful'):
                        injury_status = "Doubtful"
                    elif player_elem.find('span', class_='out'):
                        injury_status = "Out"
                    
                    if injury_status != "Healthy":
                        data.append({
                            'name': name,
                            'injury_status': injury_status,
                            'injury_notes': injury_notes,
                            'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        })
            
            df = pd.DataFrame(data)
            self._cache_data(cache_key, df.to_dict('records'))
            logger.info(f"Successfully scraped {len(df)} injury updates from Rotowire")
            return df
            
        except Exception as e:
            logger.error(f"Error scraping Rotowire injuries: {e}")
            return pd.DataFrame()
    
    def scrape_fantasyfootballcalculator_adp(self) -> pd.DataFrame:
        """
        Scrape ADP data from Fantasy Football Calculator
        Returns DataFrame with ADP information
        """
        cache_key = "ffc_adp"
        cached = self._get_cached_data(cache_key)
        if cached:
            return pd.DataFrame(cached)
        
        try:
            logger.info("Scraping ADP data from Fantasy Football Calculator...")
            url = "https://fantasyfootballcalculator.com/adp"
            
            driver = self._get_driver()
            driver.get(url)
            
            # Wait for the table to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "adp-table"))
            )
            
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            table = soup.find('table', {'class': 'adp-table'})
            
            if not table:
                logger.warning("Could not find ADP table on Fantasy Football Calculator")
                return pd.DataFrame()
            
            data = []
            rows = table.find_all('tr')[1:]  # Skip header
            
            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 5:
                    rank = cols[0].get_text(strip=True)
                    name = cols[1].get_text(strip=True)
                    position = cols[2].get_text(strip=True)
                    team = cols[3].get_text(strip=True)
                    adp = cols[4].get_text(strip=True)
                    
                    # Clean up ADP
                    adp_clean = re.sub(r'[^\d.]', '', adp)
                    adp_float = float(adp_clean) if adp_clean else 999.0
                    
                    data.append({
                        'rank': int(rank) if rank.isdigit() else 999,
                        'name': name,
                        'position': position,
                        'team': team,
                        'adp': adp_float
                    })
            
            df = pd.DataFrame(data)
            self._cache_data(cache_key, df.to_dict('records'))
            logger.info(f"Successfully scraped {len(df)} players from Fantasy Football Calculator")
            return df
            
        except Exception as e:
            logger.error(f"Error scraping Fantasy Football Calculator ADP: {e}")
            return pd.DataFrame()
    
    def scrape_expert_rankings(self) -> Dict[str, pd.DataFrame]:
        """
        Scrape expert rankings from multiple sources
        Returns dictionary with expert rankings by source
        """
        cache_key = "expert_rankings"
        cached = self._get_cached_data(cache_key)
        if cached:
            return {k: pd.DataFrame(v) for k, v in cached.items()}
        
        rankings = {}
        
        # Scrape from multiple expert sources
        sources = {
            'fantasypros': self._scrape_fantasypros_rankings,
            'espn': self._scrape_espn_rankings,
            'cbs': self._scrape_cbs_rankings,
            'yahoo': self._scrape_yahoo_rankings
        }
        
        for source_name, scraper_func in sources.items():
            try:
                logger.info(f"Scraping expert rankings from {source_name}...")
                df = scraper_func()
                if not df.empty:
                    rankings[source_name] = df
            except Exception as e:
                logger.error(f"Error scraping {source_name} rankings: {e}")
        
        self._cache_data(cache_key, {k: v.to_dict('records') for k, v in rankings.items()})
        return rankings
    
    def _scrape_fantasypros_rankings(self) -> pd.DataFrame:
        """Scrape expert consensus rankings from FantasyPros"""
        try:
            url = "https://www.fantasypros.com/nfl/rankings/consensus-cheatsheets.php"
            driver = self._get_driver()
            driver.get(url)
            
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "table"))
            )
            
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            table = soup.find('table', {'class': 'table'})
            
            if not table:
                return pd.DataFrame()
            
            data = []
            rows = table.find_all('tr')[1:]
            
            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 4:
                    rank = cols[0].get_text(strip=True)
                    name = cols[1].get_text(strip=True)
                    position = cols[2].get_text(strip=True)
                    team = cols[3].get_text(strip=True)
                    
                    data.append({
                        'rank': int(rank) if rank.isdigit() else 999,
                        'name': name,
                        'position': position,
                        'team': team
                    })
            
            return pd.DataFrame(data)
            
        except Exception as e:
            logger.error(f"Error in FantasyPros rankings: {e}")
            return pd.DataFrame()
    
    def _scrape_espn_rankings(self) -> pd.DataFrame:
        """Scrape rankings from ESPN"""
        # Placeholder - would need ESPN's actual rankings page structure
        return pd.DataFrame()
    
    def _scrape_cbs_rankings(self) -> pd.DataFrame:
        """Scrape rankings from CBS Sports"""
        # Placeholder - would need CBS's actual rankings page structure
        return pd.DataFrame()
    
    def _scrape_yahoo_rankings(self) -> pd.DataFrame:
        """Scrape rankings from Yahoo Sports"""
        # Placeholder - would need Yahoo's actual rankings page structure
        return pd.DataFrame()
    
    def update_all_data_files(self, output_dir: str = "data"):
        """
        Update all data files with fresh scraped data
        
        Args:
            output_dir: Directory to save updated data files
        """
        logger.info("Starting comprehensive data update...")
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Scrape ADP data
        adp_data = self.scrape_fantasypros_adp()
        if not adp_data.empty:
            adp_data.to_csv(f"{output_dir}/adp_updated.csv", index=False)
            logger.info(f"Updated ADP data: {len(adp_data)} players")
        
        # Scrape projections (placeholder for now)
        projections_data = self.scrape_espn_projections()
        if not projections_data.empty:
            projections_data.to_csv(f"{output_dir}/projections_updated.csv", index=False)
            logger.info(f"Updated projections data: {len(projections_data)} players")
        
        # Scrape historical stats
        stats_data = self.scrape_profootballreference_stats()
        if not stats_data.empty:
            stats_data.to_csv(f"{output_dir}/historical_stats.csv", index=False)
            logger.info(f"Updated historical stats: {len(stats_data)} players")
        
        # Scrape injury data
        injury_data = self.scrape_rotowire_injuries()
        if not injury_data.empty:
            injury_data.to_csv(f"{output_dir}/injury_updates.csv", index=False)
            logger.info(f"Updated injury data: {len(injury_data)} players")
        
        # Scrape expert rankings
        expert_rankings = self.scrape_expert_rankings()
        for source, df in expert_rankings.items():
            if not df.empty:
                df.to_csv(f"{output_dir}/rankings_{source}.csv", index=False)
                logger.info(f"Updated {source} rankings: {len(df)} players")
        
        # Create a combined risk profile based on scraped data
        risk_profiles = self._generate_risk_profiles(adp_data, injury_data, stats_data)
        if not risk_profiles.empty:
            risk_profiles.to_csv(f"{output_dir}/risk_profiles_updated.csv", index=False)
            logger.info(f"Updated risk profiles: {len(risk_profiles)} players")
        
        logger.info("Data update completed!")
    
    def _generate_risk_profiles(self, adp_data: pd.DataFrame, injury_data: pd.DataFrame, 
                               stats_data: pd.DataFrame) -> pd.DataFrame:
        """
        Generate risk profiles based on scraped data
        
        Args:
            adp_data: ADP data from various sources
            injury_data: Injury information
            stats_data: Historical performance data
            
        Returns:
            DataFrame with risk profiles
        """
        risk_profiles = []
        
        # Combine data sources to create comprehensive risk profiles
        for _, player in adp_data.iterrows():
            name = player['name']
            
            # Get injury status
            injury_status = "Healthy"
            injury_notes = ""
            if not injury_data.empty:
                player_injury = injury_data[injury_data['name'] == name]
                if not player_injury.empty:
                    injury_status = player_injury.iloc[0]['injury_status']
                    injury_notes = player_injury.iloc[0]['injury_notes']
            
            # Get historical stats
            historical_data = stats_data[stats_data['name'] == name] if not stats_data.empty else pd.DataFrame()
            
            # Calculate risk factors
            risk_factors = []
            risk_score = 0
            
            # Injury risk
            if injury_status != "Healthy":
                risk_factors.append("Current injury")
                risk_score += 3
            
            # Age risk (estimate age from historical data)
            if not historical_data.empty:
                age = historical_data.iloc[0]['age']
                if age > 30:
                    risk_factors.append("Age")
                    risk_score += 2
                elif age > 28:
                    risk_factors.append("Age")
                    risk_score += 1
            
            # ADP volatility risk
            adp = player.get('adp', 999)
            if adp > 100:
                risk_factors.append("Late ADP")
                risk_score += 1
            
            # Position-specific risks
            position = player.get('position', '')
            if position == 'RB' and injury_status != "Healthy":
                risk_factors.append("RB injury risk")
                risk_score += 2
            
            risk_profiles.append({
                'name': name,
                'position': position,
                'team': player.get('team', ''),
                'injury_risk': injury_status,
                'age': historical_data.iloc[0]['age'] if not historical_data.empty else 0,
                'experience_years': 0,  # Would need to calculate from historical data
                'contract_status': 'unknown',
                'team_changes': 'no',
                'coaching_changes': 'no',
                'risk_factors': ', '.join(risk_factors) if risk_factors else 'Low risk',
                'risk_score': min(risk_score, 10),
                'injury_notes': injury_notes
            })
        
        return pd.DataFrame(risk_profiles)
    
    def close(self):
        """Close the WebDriver and clean up resources"""
        if self.driver:
            self.driver.quit()
            self.driver = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def main():
    """Main function to demonstrate the scraper functionality"""
    print("Fantasy Football Data Scraper")
    print("=" * 40)
    
    with FantasyDataScraper(headless=True) as scraper:
        # Update all data files
        scraper.update_all_data_files()
        
        # Show sample of scraped data
        print("\nSample scraped data:")
        print("-" * 20)
        
        # ADP data
        adp_data = scraper.scrape_fantasypros_adp()
        if not adp_data.empty:
            print(f"ADP Data (Top 5):")
            print(adp_data.head())
            print()
        
        # Injury data
        injury_data = scraper.scrape_rotowire_injuries()
        if not injury_data.empty:
            print(f"Injury Updates:")
            print(injury_data.head())
            print()
        
        # Historical stats
        stats_data = scraper.scrape_profootballreference_stats()
        if not stats_data.empty:
            print(f"Historical Stats (Top 5):")
            print(stats_data.head())
            print()


if __name__ == "__main__":
    main() 