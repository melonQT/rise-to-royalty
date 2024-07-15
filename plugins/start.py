from pyrogram import (
    Client as app, 
    filters, 
    enums,
    types
)
from pyrogram.types import (
    InlineKeyboardButton, 
    InlineKeyboardMarkup
)
import random
from database import helper_functions as hp

@app.on_message(filters.command("start"))
async def start(client, message):
    user = message.from_user
    name = user.first_name
    user_id = user.id
    player = await hp.get_player(user_id)
    if player is None:
        await hp.create_player(user_id, name)
    txt = f"**{name}**, you've entered a world of death and betrayal. Trust only your blood, conquer your enemies, find allies, join or build your clan. Explore vast horizons and forge your legend. The choices are yours."

    buttons = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("Official Group", url="https://t.me/+33y03BR7Eb8wMTRl"),
                InlineKeyboardButton("Updates Channel", url="https://t.me/JoJoBotUpdates"),
            ],
            [
                InlineKeyboardButton("Add me", url="https://telegram.me/ValorsEndBot?startgroup=true"),
            ]
        ]
    )

    await message.reply_video("https://te.legra.ph/file/fa2cdddde18b7c169ccdc.mp4", caption=txt, reply_markup=buttons)
