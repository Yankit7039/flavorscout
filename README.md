## Flavor Scout – AI-Powered Flavor Recommendation Dashboard

Flavor Scout is a Streamlit-based dashboard that analyzes social media chatter (starting with Reddit) to recommend new product flavors for HealthKart brands using an AI/LLM engine.

### Quick Start

1. **Create and activate a virtual environment (recommended)**

```bash
python -m venv .venv
.venv\Scripts\activate
```

2. **Install dependencies**

```bash
pip install -r requirements.txt
```

3. **Configure API keys**

- Create a `.streamlit` directory at the project root.
- Create a `secrets.toml` file:
- **Need help getting Reddit credentials?** See [REDDIT_SETUP.md](REDDIT_SETUP.md) for step-by-step instructions.

```toml
[reddit]
client_id = "your_client_id"
client_secret = "your_client_secret"
user_agent = "flavor-scout-app"

# Choose one: Anthropic (Claude) or OpenAI (GPT)
[anthropic]
api_key = "your_claude_api_key"
model = "claude-3-5-sonnet-20241022"  # Optional, defaults to this

# OR
[openai]
api_key = "your_openai_api_key"
model = "gpt-4"  # Optional, defaults to gpt-4
```

4. **Run the app**

```bash
streamlit run app.py
```

### ⚠️ Important: Reddit API Compliance

**Commercial Use Requires Approval**: This application uses Reddit data for commercial purposes (HealthKart product development). According to Reddit's [Responsible Builder Policy](https://support.reddithelp.com/hc/en-us/articles/42728983564564-Responsible-Builder-Policy), you **must obtain explicit written approval from Reddit** before using their API commercially.

**See [REDDIT_COMPLIANCE.md](REDDIT_COMPLIANCE.md) for:**
- Detailed compliance requirements
- Steps to request commercial API access
- Alternative approaches if approval isn't granted
- Compliance checklist

**Do not use this application commercially until you have Reddit's approval.**

### 🚀 Quick Alternative: Amazon Reviews (No Approval Needed!)

**Want to skip Reddit approval?** Use Amazon product reviews instead! 

✅ **No approval needed** - Just sign up for RapidAPI  
✅ **Commercial use allowed**  
✅ **Better data quality** - Reviews specifically mention flavors  
✅ **15-30 minute setup** - Much faster than Reddit approval  

**See [QUICK_START_AMAZON.md](QUICK_START_AMAZON.md) for step-by-step instructions.**

The app now supports both Reddit and Amazon Reviews - choose your data source in the sidebar!

### Project Structure

```text
flavor_scout/
├── app.py
├── requirements.txt
├── data/
│   ├── raw_comments.json
│   └── processed_data.json
├── modules/
│   ├── scraper.py
│   ├── analyzer.py
│   ├── scorer.py
│   └── visualizer.py
├── prompts/
│   └── ai_prompts.py
└── .streamlit/
    └── secrets.toml  (gitignored)
```

### Features

1. **Data Collection**: Scrapes Reddit posts and comments from fitness/nutrition subreddits
2. **Data Cleaning**: Filters spam and extracts basic flavor mentions using regex
3. **AI Analysis**: Uses LLM (Claude or GPT) to:
   - Extract flavor preferences and complaints
   - Analyze sentiment (positive/negative/neutral)
   - Determine brand fit (MuscleBlaze, HK Vitals, TrueBasics)
   - Generate business-friendly explanations
4. **Scoring Engine**: Ranks flavors by:
   - Frequency (how often mentioned)
   - Sentiment (positive vs negative)
   - Recency (trending up?)
   - Brand fit alignment
5. **Dashboard**: Displays:
   - Golden Candidate (top recommendation)
   - Top 5 recommendations with detailed breakdowns
   - Rejected ideas (low-scoring flavors)
   - Raw data preview

### Usage Workflow

1. **Fetch Data**: Click "Fetch latest Reddit data" in the sidebar
2. **Run Analysis**: Click "Run AI Analysis" to process comments with LLM
3. **Review Results**: Explore the Golden Candidate and top recommendations

### Notes

- Do **not** commit real API keys; use `secrets.toml` or environment variables.
- In local development you can also set `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET`, `REDDIT_USER_AGENT`, `ANTHROPIC_API_KEY`, or `OPENAI_API_KEY` env vars as an alternative to Streamlit secrets.
- AI analysis may take several minutes depending on the number of comments and batch size.
- The analyzer processes comments in batches to avoid token limits and rate limits.

### Deployment

#### Deploy to Railway

See [RAILWAY_DEPLOYMENT.md](RAILWAY_DEPLOYMENT.md) for detailed instructions on deploying to Railway.

**Quick steps:**
1. Push your code to GitHub
2. Create a new project on [Railway](https://railway.app)
3. Connect your GitHub repository
4. Add environment variables in Railway dashboard:
   - `REDDIT_CLIENT_ID`
   - `REDDIT_CLIENT_SECRET`
   - `REDDIT_USER_AGENT` (optional)
   - `ANTHROPIC_API_KEY` or `OPENAI_API_KEY`
   - `ANTHROPIC_MODEL` or `OPENAI_MODEL` (optional)
5. Railway will automatically deploy your app!


