# AI-Powered Fantasy Football Draft Assistant

An intelligent draft companion that monitors ESPN fantasy football drafts in real-time and provides AI-powered recommendations for optimal player selection.

## 🎯 Features

- **Live ESPN Draft Integration**: Connects to your ESPN fantasy league and monitors draft progress
- **AI-Powered Recommendations**: Uses GPT-4 to analyze available players and provide strategic picks
- **Real-time Monitoring**: Automatically detects when it's your turn to pick
- **Strategic Analysis**: Considers roster needs, positional scarcity, and fantasy football strategies
- **Multiple Interfaces**: Command-line interface and Streamlit web UI
- **Data Integration**: Pulls ADP, projections, and player statistics
- **Real-time Data Scraping**: Fetches fresh data from FantasyPros, ESPN, Rotowire, and other sources

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- ESPN Fantasy Football account
- OpenAI API key

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd fantasy-draft-ai
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your ESPN credentials and OpenAI API key
```

### Configuration

Create a `.env` file with the following variables:
```
ESPN_USERNAME=your_espn_username
ESPN_PASSWORD=your_espn_password
OPENAI_API_KEY=your_openai_api_key
LEAGUE_ID=your_league_id
TEAM_ID=your_team_id
```

### Usage

#### Update Fantasy Football Data
```bash
# Update all data sources (ADP, projections, injuries, etc.)
python update_data.py --all

# Update specific data types
python update_data.py --adp --projections --injuries

# Check data status
python update_data.py --summary
```

#### Command Line Interface
```bash
python main.py --mode cli
```

#### Streamlit Web Interface
```bash
streamlit run main.py --mode web
```

## 📁 Project Structure

```
fantasy-draft-ai/
├── main.py                 # Main application entry point
├── espn_api_connector.py   # ESPN API integration
├── data/                   # Data storage
│   ├── adp.csv
│   ├── projections.csv
│   ├── risk_profiles.csv
│   ├── adp_updated.csv
│   ├── projections_updated.csv
│   ├── injury_updates.csv
│   ├── historical_stats.csv
│   └── data_metadata.json
├── prompts/               # AI prompt templates
│   └── prompt_builder.py
├── ai/                    # AI reasoning layer
│   └── gpt_agent.py
├── utils/                 # Utility functions
│   ├── roster_eval.py
│   ├── data_scraper.py
│   └── data_manager.py
├── ui/                    # User interface components
│   ├── cli_interface.py
│   └── streamlit_ui.py
└── requirements.txt
```

## 🧠 AI Strategy

The AI analyzes:
- Current roster composition
- Available players and their ADP
- Positional scarcity
- League scoring settings
- Draft round and pick position
- Historical fantasy success patterns

## 📊 Data Sources

The system integrates data from multiple fantasy football sources:

### Real-time Data (via Web Scraping)
- **FantasyPros**: ADP rankings and expert consensus
- **ESPN**: Player projections and rankings
- **Rotowire**: Injury updates and player status
- **Pro Football Reference**: Historical statistics
- **Fantasy Football Calculator**: Real-time ADP data

### Data Types
- **ADP (Average Draft Position)**: Consensus rankings from multiple sources
- **Player Projections**: Fantasy point projections for the season
- **Injury Data**: Current injury status and updates
- **Historical Stats**: Past performance data
- **Expert Rankings**: Rankings from fantasy football experts
- **Risk Profiles**: Player risk assessment based on multiple factors

### Data Management
- **Automatic Updates**: Fresh data fetched before each draft
- **Caching**: Intelligent caching to avoid excessive requests
- **Fallback Data**: Sample data provided for testing
- **Data Validation**: Quality checks and error handling

For detailed information about data sources and web scraping, see [WEB_SCRAPING_GUIDE.md](WEB_SCRAPING_GUIDE.md).

## 🔧 Configuration Options

- **Draft Strategy**: Zero RB, Hero RB, Elite TE prioritization
- **Risk Tolerance**: Conservative vs. aggressive drafting
- **Position Preferences**: Custom position priorities
- **League Settings**: PPR, standard, or custom scoring

## 📊 Data Sources

- ESPN Fantasy API for live draft data
- FantasyPros for ADP and projections
- Pro Football Reference for historical stats
- OpenAI GPT-4 for strategic reasoning

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## ⚠️ Disclaimer

This tool is for educational and entertainment purposes. Fantasy football involves risk, and past performance does not guarantee future results. 