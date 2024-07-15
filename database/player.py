from datetime import datetime
from database import db

playersdb = db.players

async def CreatePlayer(player_id):
    player_id = int(player_id)
    joining_date = datetime.now()
    real_joining_date = joining_date.strftime("%m/%d/%y")
    dic = {
        "player_id": player_id,
        "player_name": None,
        "current_weapon": None,
        "joining_date": real_joining_date,
        "region": None,
        "place": None,
        "level": 0,
        "exp": 0
    }
    await playersdb.insert_one(dic)
    return
    
    
async def InsertName(message, player_id):
    command_parts = message.text.split()
    if len(command_parts) >= 2:
        name = command_parts[1]
        if len(name) <= 14:
            await playersdb.update_one({"player_id": player_id}, {"$set": {"player_name": name}})
            await message.reply(f"Your name has been set to {name}!")
        else:
            await message.reply("**The Guide Guy**: Buddy, that's too long to remember.")
    else:
        await message.reply("**The Guide Guy**: Dude, stop joking and tell me what's your name?")