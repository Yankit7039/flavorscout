# Railway Deployment Guide

This guide will walk you through deploying Flavor Scout to Railway.

## Prerequisites

1. A Railway account (sign up at [railway.app](https://railway.app))
2. A GitHub account (to connect your repository)
3. Your API credentials:
   - Reddit API credentials (client_id, client_secret)
   - Either Anthropic API key OR OpenAI API key

## Deployment Steps

### 1. Prepare Your Repository

Make sure your code is pushed to a GitHub repository. The following files should be in your repo:
- `app.py`
- `requirements.txt`
- `Procfile`
- `railway.json`
- All module files in the `modules/` directory
- All prompt files in the `prompts/` directory

**Important**: Do NOT commit `.streamlit/secrets.toml` - it's in `.gitignore`.

### 2. Create a New Project on Railway

1. Go to [railway.app](https://railway.app) and sign in
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Authorize Railway to access your GitHub account
5. Select the `flavorscout` repository

### 3. Configure Environment Variables

Railway will automatically detect Python and install dependencies from `requirements.txt`. Now you need to add your API credentials as environment variables.

#### Option A: Using Railway Dashboard

1. In your Railway project, click on your service
2. Go to the "Variables" tab
3. Add the following environment variables:

**Required - Reddit API:**
```
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
REDDIT_USER_AGENT=flavor-scout-app
```

**Required - Choose ONE LLM provider:**
```
# Option 1: Anthropic (Claude)
ANTHROPIC_API_KEY=your_anthropic_api_key
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022

# OR Option 2: OpenAI (GPT)
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4
```

#### Option B: Using Railway CLI

If you have Railway CLI installed:

```bash
railway variables set REDDIT_CLIENT_ID=your_reddit_client_id
railway variables set REDDIT_CLIENT_SECRET=your_reddit_client_secret
railway variables set REDDIT_USER_AGENT=flavor-scout-app
railway variables set ANTHROPIC_API_KEY=your_anthropic_api_key
railway variables set ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
```

### 4. Deploy

Railway will automatically:
1. Detect the Python runtime
2. Install dependencies from `requirements.txt`
3. Run the app using the command in `Procfile`
4. Expose the app on a public URL

### 5. Access Your App

Once deployment completes:
1. Railway will provide a public URL (e.g., `https://your-app-name.up.railway.app`)
2. Click on the URL or go to your service's "Settings" tab to find it
3. Your app should be live!

## Environment Variables Reference

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `REDDIT_CLIENT_ID` | Yes | Reddit API client ID | `abc123xyz` |
| `REDDIT_CLIENT_SECRET` | Yes | Reddit API client secret | `secret_abc123` |
| `REDDIT_USER_AGENT` | No | Reddit API user agent | `flavor-scout-app` (default) |
| `ANTHROPIC_API_KEY` | Yes* | Anthropic API key | `sk-ant-...` |
| `ANTHROPIC_MODEL` | No | Anthropic model name | `claude-3-5-sonnet-20241022` (default) |
| `OPENAI_API_KEY` | Yes* | OpenAI API key | `sk-...` |
| `OPENAI_MODEL` | No | OpenAI model name | `gpt-4` (default) |

*You need either Anthropic OR OpenAI credentials, not both.

## Troubleshooting

### App won't start

1. Check the Railway logs (in the "Deployments" tab)
2. Verify all required environment variables are set
3. Ensure `Procfile` exists and contains: `web: streamlit run app.py --server.port=$PORT --server.address=0.0.0.0`

### Environment variables not working

1. Make sure variables are set in Railway (not just locally)
2. Redeploy after adding new variables
3. Check variable names match exactly (case-sensitive)

### Build fails

1. Check `requirements.txt` for any typos
2. Verify Python version compatibility
3. Check Railway build logs for specific error messages

### Data persistence

Note: Railway's ephemeral filesystem means data stored in the `data/` directory will be lost when the app restarts. For production, consider:
- Using Railway's PostgreSQL or MySQL plugin for persistent storage
- Integrating with external storage (S3, etc.)
- Using Railway volumes (if available in your plan)

## Updating Your Deployment

Every time you push to your connected GitHub repository, Railway will automatically:
1. Detect the changes
2. Build a new deployment
3. Deploy the updated version

You can also manually trigger deployments from the Railway dashboard.

## Cost Considerations

Railway offers a free tier with $5 credit per month. Monitor your usage:
- Build time
- Runtime hours
- Data transfer

For production apps with heavy usage, consider upgrading to a paid plan.

## Additional Resources

- [Railway Documentation](https://docs.railway.app)
- [Streamlit Cloud Deployment](https://docs.streamlit.io/streamlit-community-cloud) (alternative option)
- [Railway Discord](https://discord.gg/railway) for support

