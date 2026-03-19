"""
Configuration file for César attendance bot.

Copy this file to config.py and fill in your details.
"""

# Discord webhook URL
# Create one in Discord: Server Settings > Integrations > Webhooks > New Webhook
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/YOUR_WEBHOOK_URL_HERE"

# César credentials
# WARNING: Consider using environment variables for security
CESAR_USERNAME = ""
CESAR_PASSWORD = ""

# Schedule settings
START_HOUR = 9
START_MINUTE = 14
AFTERNOON_HOUR = 13
AFTERNOON_MINUTE = 43
CHECK_INTERVAL = 60  # seconds between checks during active monitoring
