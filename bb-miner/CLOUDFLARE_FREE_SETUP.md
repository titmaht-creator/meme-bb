# Deploy BB MINER on Cloudflare Workers Free

This runtime uses Telegram webhooks and Cloudflare Workers + Workers KV. It does not need an always-on server.

## Free-plan notes
Cloudflare currently lists 100,000 Worker requests/day and 10 ms CPU time/request on Workers Free. Workers KV Free currently lists 100,000 reads/day, 1,000 writes/day, and 1 GB storage. Limits can change; check the official pages before launch:
- https://developers.cloudflare.com/workers/platform/limits/
- https://developers.cloudflare.com/kv/platform/limits/

The bot writes a user's record when they interact. If usage exceeds KV free write limits, some updates can fail. This is a small beta starter, not a high-scale production database.

## Dashboard setup (mobile-friendly)
1. Sign in to Cloudflare and open Workers & Pages.
2. Create a KV namespace named `BB_MINER_USERS`.
3. Open the namespace details and copy its ID.
4. In this repository, edit `wrangler.toml` and replace `REPLACE_WITH_YOUR_KV_NAMESPACE_ID` with that ID.
5. Create a Worker named `bb-miner-bot` and deploy the contents of `worker.js` (or connect this GitHub repository if that option is available).
6. In Worker Settings → Variables and Secrets, add:
   - Secret `BOT_TOKEN`: the token from BotFather
   - Secret `WEBHOOK_SECRET`: create a long random string; do not share it
7. Bind the KV namespace to the Worker using variable name `USERS`.
8. Deploy and copy the Worker URL, e.g. `https://bb-miner-bot.<your-subdomain>.workers.dev`.

## Register Telegram webhook
Open this URL in a browser after replacing the placeholders. Do not share the resulting URL because it contains the bot token and webhook secret:

`https://api.telegram.org/bot<BOT_TOKEN>/setWebhook?url=https://<WORKER_HOST>/webhook/<WEBHOOK_SECRET>`

A successful response contains `"ok":true`.

To verify, open:
`https://api.telegram.org/bot<BOT_TOKEN>/getWebhookInfo`

## Important
- Never put the BotFather token in GitHub, source code, or chat.
- Points are internal demo points only. No blockchain mining, token issuance, cash value, or redemption is implemented.
- Current referral links are informational only; referral rewards are not enabled.
- The sample level rates are placeholders.
- Test with a private account before inviting users.
- Keep account spending limits at zero/disabled for paid usage where possible; do not enable a paid plan.
