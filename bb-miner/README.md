# BB MINER — Telegram Bot Starter

Independent starter project inside the MEME BB repository. All BB MINER files live in this folder.

## Current scope
- Telegram bot: `@BBMiner2026Bot`
- Background points accrual with manual claim
- Level-based sample rates
- SQLite for low-cost local testing
- Basic referral links

**Important:** These are in-app points only. This starter does not mine a blockchain, create a token, promise redemption, or represent a tradable asset.

## Run locally
1. Install Python 3.11 or newer.
2. Create a virtual environment.
3. Install dependencies: `pip install -r requirements.txt`
4. Copy `.env.example` to `.env` and add your BotFather token to `BOT_TOKEN`.
5. Start: `python bot.py`

Never commit `.env` or share your bot token in chat.

## Sample levels
Bronze 1.0, Silver 1.5, Gold 2.0, Platinum 3.0, Diamond 5.0 points/hour. Thresholds and rates are placeholders and must be approved before launch.

## Before public launch
Add admin controls, abuse/rate limiting, database backups, privacy/terms pages, monitoring, tests, and a hosted always-on backend. GitHub Pages cannot run this bot; it only hosts static websites.