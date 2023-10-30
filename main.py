import sqlite3
from bot import Bot
import interactions

db = sqlite3.connect("koneko.db")

client = interactions.Client(token=open("token.txt", "r").read())
bot = Bot(client, db)

client.start()