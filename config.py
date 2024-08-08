import os

from dotenv import load_dotenv

load_dotenv()

TOKEN = str(os.getenv("BOT_TOKEN"))
DATABASE_URL = os.getenv('DATABASE_URL')
photo_posts = 'AgACAgIAAxkBAAMoZrShJzFy1XyZSgABSfOg5p7xb_FHAAIx3TEbrP-hSV37wC-ICrkvAQADAgADeQADNQQ'