from datetime import datetime
from database import db

playersdb = db.players


async def create_player(player_id, player_name):
    player_id = int(player_id)
    joining_date = datetime.now()
    real_joining_date = joining_date.strftime("%d/%m/%y")
    dic = {
        "player_id": player_id,
        "player_name": player_name,
        "current_weapon": None,
        "joining_date": real_joining_date,
        "region": None,
        "gold": 0,
        "titles": ["The First Men"],
        "weapons": {},
        "armours": {},
        "place": None,
        "level": 0,
        "exp": 0
    }
    await playersdb.insert_one(dic)
    return

async def get_player(user_id):
	player = await playersdb.find_one({'player_id': user_id})
	return player