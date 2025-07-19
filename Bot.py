import os
from pyrogram import Client, filters
from pymongo import MongoClient
from dotenv import load_dotenv

# Charger les variables .env
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
MONGO_URI = os.getenv("MONGO_URI")

# Initialisation du bot Pyrogram
app = Client("genlink_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Connexion à la base MongoDB
mongo = MongoClient(MONGO_URI)
db = mongo["genlink"]
users_col = db["users"]

# Dictionnaire temporaire pour stocker les messages batch
custom_batches = {}

@app.on_message(filters.command("start"))
async def start_command(_, message):
    uid = message.from_user.id
    if not users_col.find_one({"user_id": uid}):
        users_col.insert_one({"user_id": uid})
    await message.reply("🤖 Bienvenue ! Envoie /genlink ou /custom_batch.")

@app.on_message(filters.command("genlink"))
async def genlink(_, message):
    if not message.reply_to_message:
        return await message.reply("❗ Réponds à un message avec /genlink.")
    m = message.reply_to_message
    link = f"https://t.me/{m.chat.username or m.chat.id}/{m.message_id}"
    await message.reply(f"🔗 Lien généré :\n{link}")

@app.on_message(filters.command("custom_batch"))
async def custom_batch(_, message):
    custom_batches[message.from_user.id] = []
    await message.reply("📥 Envoie jusqu'à 10 messages à stocker, puis tape /done.")

@app.on_message(filters.command("done"))
async def done_batch(_, message):
    uid = message.from_user.id
    batch = custom_batches.get(uid, [])
    if not batch:
        return await message.reply("❌ Aucun message reçu.")
    links = [f"https://t.me/{m.chat.username or m.chat.id}/{m.message_id}" for m in batch]
    custom_batches.pop(uid, None)
    await message.reply("📦 Voici tes liens :\n\n" + "\n".join(links))

@app.on_message(filters.private & (filters.text | filters.photo | filters.document | filters.video | filters.audio))
async def catch_batch(_, message):
    uid = message.from_user.id
    if uid in custom_batches and len(custom_batches[uid]) < 10:
        custom_batches[uid].append(message)
        await message.reply("✅ Message ajouté.")

app.run()
