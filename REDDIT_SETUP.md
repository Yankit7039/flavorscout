# How to Get Reddit API Credentials

> ⚠️ **IMPORTANT - Commercial Use**: If you're using this app for commercial purposes (e.g., for HealthKart), you **must** get explicit written approval from Reddit before using their API. See [REDDIT_COMPLIANCE.md](REDDIT_COMPLIANCE.md) for details.

Follow these steps to create a Reddit app and get your `client_id` and `client_secret`:

## Step 1: Log in to Reddit

1. Go to https://www.reddit.com and **log in** to your account (or create one if needed)

## Step 2: Access Reddit App Preferences

1. Go to: **https://www.reddit.com/prefs/apps**
   - Or navigate: Reddit → User Settings → **"apps"** tab (at the bottom)

## Step 3: Create a New App

1. Scroll down and click the **"create another app..."** or **"create app"** button

2. Fill in the form:
   - **Name**: `Flavor Scout` (or any name you like)
   - **Type**: Select **"script"** for personal/testing use, or **"web app"** if you have commercial approval
     - ⚠️ **Note**: "script" is for personal use only. Commercial use requires approval and may need "web app" type.
   - **Description**: Optional, e.g., "AI flavor recommendation tool"
   - **About URL**: Your production URL (e.g., `https://flavorscout-production.up.railway.app/`) or `http://localhost` for testing
   - **Redirect URI**: Your production URL or `http://localhost` (Reddit requires this even if you won't use OAuth)

3. Click **"create app"**

## Step 4: Get Your Credentials

After creating the app, you'll see a box with your app details:

- **Client ID**: This is the string under your app name (looks like: `abc123def456ghi789`)
  - It's the **short string** next to your app name, NOT the "secret" field
  - Sometimes shown as "personal use script" with a string below it

- **Client Secret**: This is the **"secret"** field (looks like: `xyz789_secret_key_abc123`)
  - It's labeled as "secret" in the app details
  - If you see "secret" with a value, that's your `client_secret`
  - If it says "secret" is blank or "none", you may need to regenerate it (see troubleshooting below)

## Step 5: Update Your secrets.toml

Copy the values into your `.streamlit/secrets.toml` file:

```toml
[reddit]
client_id = "abc123def456ghi789"  # Your actual client ID here
client_secret = "xyz789_secret_key_abc123"  # Your actual secret here
user_agent = "flavor-scout-app"
```

**Important**: 
- Don't share these credentials publicly
- Don't commit `secrets.toml` to Git (it should be in `.gitignore`)

## Troubleshooting

### "secret" field is blank or shows "none"
- Some Reddit apps created as "script" type may not show a secret initially
- Try creating a new app and make sure you select **"script"** type
- The secret should appear immediately after creation

### "Invalid credentials" error
- Double-check you copied the **entire** client_id and client_secret (no extra spaces)
- Make sure the app type is set to **"script"** (not "web app" or "installed app")
- Verify the `user_agent` matches what you set in secrets.toml

### Rate limiting
- Reddit API has rate limits (60 requests per minute for read-only scripts)
- If you hit limits, wait a minute and try again
- The scraper is designed to batch requests to stay within limits

## Visual Guide

When you create the app, you'll see something like this:

```
┌─────────────────────────────────────┐
│  Flavor Scout                       │
│  personal use script                │
│  abc123def456ghi789  ← CLIENT ID    │
│                                     │
│  secret: xyz789_secret...  ← SECRET │
│                                     │
│  http://localhost                   │
└─────────────────────────────────────┘
```

The string next to "personal use script" is your **client_id**.  
The value after "secret:" is your **client_secret**.

## Need Help?

If you're still having issues:
1. Make sure you're logged into Reddit
2. Try creating a new app with type "script"
3. Check that the redirect URI is exactly `http://localhost`
4. Verify there are no extra spaces when copying credentials



