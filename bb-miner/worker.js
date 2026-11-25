const LEVELS = [
  ["Bronze", 0, 1.0],
  ["Silver", 500, 1.5],
  ["Gold", 2500, 2.0],
  ["Platinum", 10000, 3.0],
  ["Diamond", 50000, 5.0],
];
const CAP_SECONDS = 24 * 60 * 60;

function levelFor(points) {
  let chosen = LEVELS[0];
  for (const item of LEVELS) if (points >= item[1]) chosen = item;
  return chosen;
}
function esc(s="") {
  return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");
}
async function telegram(env, method, body) {
  const r = await fetch(`https://api.telegram.org/bot${env.BOT_TOKEN}/${method}`, {
    method: "POST", headers: {"content-type":"application/json"}, body: JSON.stringify(body)
  });
  return r.json();
}
async function loadUser(env, id, username, referrer) {
  const key = `user:${id}`;
  const now = Math.floor(Date.now()/1000);
  let u = await env.USERS.get(key, "json");
  if (!u) {
    u = {id, username: username || "", points:0, pending:0, last_tick:now,
      invited_by: referrer && Number(referrer)!==Number(id) ? Number(referrer) : null};
  } else {
    u.username = username || u.username || "";
    const elapsed = Math.max(0, Math.min(now-u.last_tick, CAP_SECONDS));
    const rate = levelFor(u.points + u.pending)[2];
    u.pending += elapsed / 3600 * rate;
    u.last_tick = now;
  }
  await env.USERS.put(key, JSON.stringify(u));
  return u;
}
async function reply(env, chatId, text, keyboard) {
  return telegram(env, "sendMessage", {
    chat_id: chatId, text, parse_mode:"HTML",
    reply_markup: keyboard || {keyboard:[
      [{text:"⛏️ Claim points"},{text:"👤 My account"}],
      [{text:"🤝 Invite friends"}]
    ], resize_keyboard:true}
  });
}
async function handleUpdate(update, env) {
  const msg = update.message;
  if (!msg || !msg.from || !msg.chat) return;
  const id = msg.from.id;
  const text = (msg.text || "").trim();
  let ref = null;
  if (text.startsWith("/start")) {
    const payload = text.split(/\s+/)[1] || "";
    if (payload.startsWith("ref_")) ref = payload.slice(4);
  }
  const u = await loadUser(env, id, msg.from.username, ref);
  const chat = msg.chat.id;
  if (text.startsWith("/start")) {
    await reply(env, chat,
      "⛏️ <b>Welcome to BB MINER</b>\n\n" +
      "Earn in-app points over time and claim them manually.\n\n" +
      "⚠️ These are demo points only, not cryptocurrency, not tradable, and have no guaranteed cash value or redemption.");
  } else if (text === "/help") {
    await reply(env, chat, "Commands:\n/start — Start\n/balance — Account\n/claim — Claim points\n/invite — Invite link");
  } else if (text === "/balance" || text === "👤 My account") {
    const lvl = levelFor(u.points + u.pending);
    await reply(env, chat,
      `👤 <b>BB MINER account</b>\n💰 Claimed: ${u.points.toFixed(2)}\n⏳ Available to claim: ${u.pending.toFixed(2)}\n🏅 Level: ${lvl[0]}\n⚡ Rate: ${lvl[2].toFixed(1)} points/hour`);
  } else if (text === "/claim" || text === "⛏️ Claim points") {
    const amount = u.pending;
    u.points += amount;
    u.pending = 0;
    await env.USERS.put(`user:${id}`, JSON.stringify(u));
    await reply(env, chat, `✅ Claimed: <b>${amount.toFixed(2)} points</b>\n💰 Total: ${u.points.toFixed(2)}\n🏅 Level: ${levelFor(u.points)[0]}`);
  } else if (text === "/invite" || text === "🤝 Invite friends") {
    const me = await telegram(env, "getMe", {});
    const username = me?.result?.username || "BBMiner2026Bot";
    await reply(env, chat, `🤝 Your invite link:\nhttps://t.me/${username}?start=ref_${id}\n\nReferral rewards are not enabled yet.`);
  } else {
    await reply(env, chat, "Use /start, /balance, /claim or /invite.");
  }
}
export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (url.pathname === "/") return new Response("BB MINER webhook is ready.");
    if (url.pathname !== `/webhook/${env.WEBHOOK_SECRET}`) return new Response("Not found", {status:404});
    if (request.method !== "POST") return new Response("Method not allowed", {status:405});
    let update;
    try { update = await request.json(); } catch { return new Response("Bad request",{status:400}); }
    try { await handleUpdate(update, env); return new Response("OK"); }
    catch (e) { return new Response("Temporary error", {status:500}); }
  }
};