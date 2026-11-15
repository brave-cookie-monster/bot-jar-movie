"""Main entry point for bot-hosting.com / local execution."""
import os
import bot

if __name__ == "__main__":
    token = os.getenv("DISCORD_TOKEN", bot.DISCORD_TOKEN)
    if not token or token == "your_discord_bot_token_here":
        print("❌ ERROR: DISCORD_TOKEN is missing!")
        print("Please set your bot token in the .env file or bot-hosting.com startup variables.")
    else:
        bot.bot.run(token)
