from pyrogram import Client, filters
from pyrogram.types import Message
import random
import asyncio, time, re
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from motor.motor_asyncio import AsyncIOMotorClient
import dns.resolver
from datetime import datetime, timedelta
from pyrogram.errors import *

dns.resolver.default_resolver = dns.resolver.Resolver(configure=False)
dns.resolver.default_resolver.nameservers = ['8.8.8.8']
Database = AsyncIOMotorClient("mongodb+srv://melon:pokemoon1@cluster0.my4so5r.mongodb.net/?retryWrites=true&w=majority")
db = Database.Bot
gym_leadersdb = db.gym_leaders
trainersdb = db.trainers
pending_requests = {}

app = Client("Realgym_bot", api_id=2912653, api_hash="36a616c83fb35db05d768b40cd18242b", bot_token="6924718259:AAHBWDsVV9DcUjCQFG1uVKGHiyqpouD0cgQ")

admins = [7517384313, 1381668733, 1329157016, 7125783665, 6956868347]
GYM_TYPES = {
    "Kanto": {"Water": "Water Badge", "Fire": "Fire Badge", "Electric": "Electric Badge", "Ground": "Ground Badge"},
    "Johto": {"Fighting": "Fighting Badge", "Steel": "Steel Badge", "Flying": "Flying Badge", "Bug": "Bug Badge"},
    "Hoenn": {"Steel": "Steel Badge", "Fire": "Fire Badge", "Electric": "Electric Badge", "Ground": "Ground Badge"},
    "Sinnoh": {"Dragon": "Dragon Badge", "Dark": "Dark Badge", "Fighting": "Fighting Badge", "Normal": "Normal Badge"},
    "Unova": {"Dragon": "Dragon Badge", "Dark": "Dark Badge", "Psychic": "Psychic Badge", "Water": "Water Badge"},
    "Kalos": {"Dragon": "Dragon Badge", "Fairy": "Fairy Badge", "Fire": "Fire Badge", "Grass": "Grass Badge"},
    "Alola": {"Steel": "Steel Badge", "Fairy": "Fairy Badge", "Dark": "Dark Badge", "Grass": "Grass Badge"},
    "Galar": {"Water": "Water Badge", "Flying": "Flying Badge", "Grass": "Grass Badge", "Ghost": "Ghost Badge"},
}

@app.on_message(filters.command("reset") & filters.reply & filters.user(admins))
async def reset_cmd(client, message):
    region = message.text.split()[1]  # Get the region after the command prefix
    user = message.reply_to_message.from_user
    print(region)
    user_data = await trainersdb.find_one({"trainer_id": user.id})  # Fetch user data
    
    if not user_data:
        await message.reply("User data not found.")
        return
    
    badges = user_data.get("badges", [])
    print(badges)
    badge_found = False

    for badge in badges:
        if badge["region"] == region:
            badge_found = True
            await trainersdb.update_one(
                {"trainer_id": user.id}, 
                {"$pull": {"badges": {"region": region}}}  # Use $pull to remove the badge with the matching region
            )
            break  # Exit loop once the badge is removed
    
    if badge_found:
        await message.reply(f"Badge from region {region} has been removed.")
    else:
        await message.reply(f"No badge found for region {region}.")


@app.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message):
    replied_user = message.from_user
    user_data = await trainersdb.find_one({"trainer_id": replied_user.id})

    if user_data:
        if "badges" not in user_data:
            await trainersdb.update_one(
                {"trainer_id": replied_user.id},
                {"$set": {"badges": []}}
            )
        await message.reply(f"{replied_user.first_name} already started their journey!")
    else:
        await trainersdb.insert_one(
            {"trainer_id": replied_user.id, "badges": []}
        )
        await message.reply(f"{replied_user.first_name} has started their journey with no badges!")


# --------- BROADCAST CODE  --------- #
async def present_in_userbase(user_id : int):
    found = trainersdb.find_one({'_id': user_id})
    if found:
        return True
    else:
        return False

async def add_to_userbase(user_id: int):
    trainersdb.insert_one({'trainer_id': user_id})
    return

async def get_users():
    user_docs = trainersdb.find()
    user_ids = []
    for doc in user_docs:
        user_ids.append(doc['trainer_id'])
        
    return user_ids
    
async def del_from_userbase(user_id: int):
    trainersdb.delete_one({'trainer_id': user_id})
    return

@app.on_message(filters.private & filters.command('broadcast') & filters.user(admins) & filters.reply)
async def broadcast(client, message):
       broadcast_msg = message.reply_to_message
       txt = await message.reply(text = 'Staring....')        
       user_ids = await get_users()
       success = 0
       deleted = 0
       blocked = 0     
       await txt.edit(text = 'Broadcasting message, Please wait', reply_markup = None)   
       for user_id in user_ids:
          try:
            broadcast_msg = await broadcast_msg.copy(
            chat_id =user_id ,
            reply_to_message_id = broadcast_msg.message_id
            )
            success += 1
            time.sleep(3)
          except FloodWait as e:
            await asyncio.sleep(e.x)
            success += 1
          except UserIsBlocked:
            blocked += 1
          except InputUserDeactivated:
            deleted += 1                       
       text = f"""<b>Broadcast Completed</b>    
Total users: {str(len(user_ids))}
Deleted accounts: {str(deleted)} """
       await message.reply(text=text)


@app.on_message(filters.command("setgym") & filters.reply & filters.user(admins))
async def set_gym_leader(client: Client, message: Message):
    try:
        _, region, gym_name = message.text.split(" ", 2)
    except ValueError:
        await message.reply("Usage: /setgym {region_name} {gym_name}\nExample: /setgym Kanto Water")
        return

    region = region.lower()
    gym_name = gym_name.lower()

    matching_region = next((r for r in GYM_TYPES.keys() if r.lower() == region), None)
    if not matching_region:
        await message.reply(f"Invalid region: {region}.")
        return

    matching_gym = next((g for g in GYM_TYPES[matching_region].keys() if g.lower() == gym_name), None)
    if not matching_gym:
        await message.reply(f"Invalid gym name for {matching_region}. Available gyms: {', '.join(GYM_TYPES[matching_region].keys())}.")
        return

    replied_user = message.reply_to_message.from_user
    badge = GYM_TYPES[matching_region][matching_gym]

    await gym_leadersdb.update_many(
        {"leader_id": replied_user.id},
        {"$unset": {"leader_id": "", "leader_name": ""}}
    )

    await gym_leadersdb.update_one(
        {"region": matching_region, "gym_name": matching_gym},
        {"$set": {"leader_id": replied_user.id, "leader_name": replied_user.first_name}},
        upsert=True
    )

    await message.reply(f"{replied_user.first_name} has been set as the leader of {matching_region} {matching_gym} Gym ({badge}).")
    await client.send_message(-1002461455117, f"{replied_user.first_name} has been set as the leader of {matching_region} {matching_gym} Gym ({badge}) by {message.from_user.first_name}.")


@app.on_message(filters.command("awardbadge") & filters.reply)
async def award_badge(client: Client, message: Message):
    leader = await gym_leadersdb.find_one({"leader_id": message.from_user.id})
    if not leader:
        await message.reply("You are not a registered gym leader.")
        return

    badge = GYM_TYPES[leader['region']][leader['gym_name']]
    replied_user = message.reply_to_message.from_user

    await trainersdb.update_one(
        {"trainer_id": replied_user.id},
        {"$addToSet": {"badges": {"badge": badge, "region": leader['region']}}},
        upsert=True
    )

    await message.reply(f"{replied_user.first_name} has been awarded the {leader['region']} {badge}.")
    await client.send_message(-1002461455117, f"• Name: {replied_user.first_name}\n• ID: {replied_user.id}\n\n**Has been awarded the {leader['region']} {badge}.**")


@app.on_message(filters.command("mycard"))
async def show_profile(client, msg):
    user_data = await trainersdb.find_one({"trainer_id": msg.from_user.id})
    if not user_data:
        await msg.reply("You haven't started me in private yet!")
        return

    badges = user_data.get("badges", [])

    region_badges = {r: [] for r in GYM_TYPES.keys()}
    for b in badges:
        region_badges[b['region']].append(b['badge'])

    earned = 0
    total = 0
    summaries = []

    for region, earned_badges in region_badges.items():
        count = len(earned_badges)
        max_badges = len(GYM_TYPES[region])
        total += max_badges
        earned += count

        summaries.append(f"{region} ({count}/{max_badges})")

    completion = (earned / total) * 100 if total > 0 else 0
    profile_text = (
        f"**☉ Name**: {msg.from_user.first_name}\n"
        f"**☉ Trainer ID**: {msg.from_user.id}\n\n"
        f"🎖️ **Badges Earned**: {earned}/{total}\n"
        f"🌟 **Completion**: {completion:.2f}%\n\n"
        f"**🗺️ Badges by Region**:\n"
    )

    summary_lines = [", ".join(summaries[i:i + 2]) for i in range(0, len(summaries), 2)]
    profile_text += "\n".join(summary_lines)

    buttons = [
        [InlineKeyboardButton(r, callback_data=f"show_{r}_{msg.from_user.id}") for r in GYM_TYPES.keys()][:4],
        [InlineKeyboardButton(r, callback_data=f"show_{r}_{msg.from_user.id}") for r in GYM_TYPES.keys()][4:8],
    ]
    markup = InlineKeyboardMarkup(buttons)

    await msg.reply_photo(
        photo="https://i.imgur.com/mXtoOdV.jpeg",
        caption=profile_text,
        reply_markup=markup
    )



cooldowns = {}

@app.on_callback_query(filters.regex(r"^show_(\w+)_(\d+)$"))
async def show_region(client, query):
    original_user_id = int(query.data.split("_")[2])
    user_id = query.from_user.id
    
    if user_id != original_user_id:
        await query.answer("This is not your button! You cannot interact with it.", show_alert=True)
        return

    now = datetime.now()

    if user_id in cooldowns and now - cooldowns[user_id] < timedelta(seconds=3):
        await query.answer("Please wait a few seconds before trying again.", show_alert=True)
        return

    cooldowns[user_id] = now

    region = query.data.split("_")[1]

    if region not in GYM_TYPES:
        await query.answer("Invalid region!", show_alert=True)
        return

    user_data = await trainersdb.find_one({"trainer_id": user_id})
    if not user_data:
        await query.message.edit("You haven't started your journey yet. Begin earning badges by challenging gym leaders!")
        return

    badges = user_data.get("badges", [])
    earned_badges = [b['badge'] for b in badges if b['region'] == region]
    total_badges = len(GYM_TYPES[region])
    earned_count = len(earned_badges)

    badge_icons = {
        "Water Badge": "💧",
        "Fire Badge": "🔥",
        "Electric Badge": "⚡",
        "Ground Badge": "⛰️",
        "Fighting Badge": "🥊",
        "Steel Badge": "⚙️",
        "Flying Badge": "🕊️",
        "Bug Badge": "🐞",
        "Dragon Badge": "🐉",
        "Dark Badge": "🌑",
        "Normal Badge": "⚪",
        "Psychic Badge": "🔮",
        "Fairy Badge": "🧚‍♀️",
        "Grass Badge": "🌿",
        "Ghost Badge": "👻",
    }

    badge_list = (
        "\n".join([f"{badge_icons.get(b, '🏅')} {b}" for b in earned_badges])
        if earned_count > 0
        else "No badges earned yet."
    )

    region_text = f"**{region} Region Badges**\n\nTotal Badges: {earned_count}/{total_badges}\n\n{badge_list}"

    back_btn = InlineKeyboardButton("Back to Profile", callback_data=f"send_profile_{original_user_id}")

    await query.message.edit(
        text=region_text,
        reply_markup=InlineKeyboardMarkup([[back_btn]])
    )
    await query.answer()



@app.on_callback_query(filters.regex(r"^send_profile_(\d+)$"))
async def show_profile(client, query):
    user_id = query.from_user.id
    original_user_id = int(query.data.split("_")[2])
    now = datetime.now()

    if user_id != original_user_id:
        await query.answer("This is not your button! You cannot interact with it.", show_alert=True)
        return
        
    if user_id in cooldowns and now - cooldowns[user_id] < timedelta(seconds=3):
        await query.answer("Please wait a few seconds before trying again.", show_alert=True)
        return

    cooldowns[user_id] = now

    user_data = await trainersdb.find_one({"trainer_id": user_id})
    badges = user_data.get("badges", [])
    if not user_data:
        await query.message.edit("It seems like you haven't started your journey yet. Begin earning badges by challenging gym leaders!")
        return

    region_badges = {r: [] for r in GYM_TYPES.keys()}
    for b in badges:
        region_badges[b['region']].append(b['badge'])

    earned = 0
    total = 0
    summaries = []

    for region, earned_list in region_badges.items():
        count = len(earned_list)
        max_badges = len(GYM_TYPES[region])
        total += max_badges
        earned += count

        summaries.append(f"{region} ({count}/{max_badges})")

    completion = (earned / total) * 100 if total > 0 else 0
    profile_text = (
        f"**☉ Name**: {query.from_user.first_name}\n"
        f"**☉ Trainer ID**: {user_id}\n\n"
        f"🎖️ **Badges Earned**: {earned}/{total}\n"
        f"🌟 **Completion**: {completion:.2f}%\n\n"
        f"**🗺️ Badges by Region**:\n"
    )

    summary_lines = [", ".join(summaries[i:i + 2]) for i in range(0, len(summaries), 2)]
    profile_text += "\n".join(summary_lines)

    buttons = [
        [InlineKeyboardButton(r, callback_data=f"show_{r}_{original_user_id}") for r in GYM_TYPES.keys()][:4],
        [InlineKeyboardButton(r, callback_data=f"show_{r}_{original_user_id}") for r in GYM_TYPES.keys()][4:8],
    ]
    markup = InlineKeyboardMarkup(buttons)

    await query.message.edit(
        profile_text,
        reply_markup=markup
    )
    await query.answer()


REGIONAL_GYM_GROUP_IDS = {
    'Kanto': {'Water': -1002196284122, 'Fire': -1002161589171, 'Electric': -1002181116918, 'Ground': -1002157916998},
    'Johto': {'Fighting': -1002222758420, 'Steel': -1002152985894, 'Flying': -1002202454764, 'Bug': -1002200940186},
    'Hoenn': {'Steel': -1002156351842, 'Fire': -1002051289482, 'Electric': -1002249880562, 'Ground': -1002192991914},
    'Sinnoh': {'Dragon': -1002189150064, 'Dark': -1002169713159, 'Fighting': -1002164860224, 'Normal': -1002216762699},
    'Unova': {'Dragon': -1002161287420, 'Dark': -1002192366312, 'Psychic': -1002202246549, 'Water': -1002160332263},
    'Kalos': {'Dragon': -1002184516776, 'Fairy': -1002179177838, 'Fire': -1002225583350, 'Grass': -1002209149505},
    'Alola': {'Steel': -1002223737707, 'Fairy': -1002224968377, 'Dark': -1002183886906, 'Grass': -1002165482489},
    'Galar': {'Water': -1002149038371, 'Flying': -1002226029849, 'Grass': -1002157923242, 'Ghost': -1002203503024}
}

ELITE_GYM_GROUP_IDS = {
    "Kanto": {
        "Elite 1": -1002444392254,
        "Elite 2": -1002220442828,
        "Elite 3": -1002177362651,
        "Elite 4": -1002191365623,
    },
    "Johto": {
        "Elite 5": -1002163927111,
        "Elite 6": -1002219435624,
        "Elite 7": -1002175236488,
        "Elite 8": -1002210012100,
    },
    "Hoenn": {
        "Elite 9": -1002166290654,
        "Elite 10": -1002163972788,
        "Elite 11": -1002183483012,
        "Elite 12": -1002159312685,
    },
    "Sinnoh": {
        "Elite 13": -1002204584511,
        "Elite 14": -1002219693468,
        "Elite 15": -1002158711145,
        "Elite 16": -1002194308183,
    },
    "Unova": {
        "Elite 17": -1002228060157,
        "Elite 18": -1002183039868,
        "Elite 19": -1002238440245,
        "Elite 20": -1002249536117,
    },
    "Kalos": {
        "Elite 21": -1002243435018,
        "Elite 22": -1002229758906,
        "Elite 23": -1002172104216,
        "Elite 24": -1002150423767,
    },
    "Alola": {
        "Elite 25": -1002223766908,
        "Elite 26": -1002213403982,
        "Elite 27": -1002186574200,
        "Elite 28": -1002206271124,
    },
    "Galar": {
        "Elite 29": -1002202062709,
        "Elite 30": -1002236697813,
        "Elite 31": -1002223870226,
        "Elite 32": -1002206134270,
    },
}

@app.on_message(filters.command("joingym") & (filters.private | filters.chat(-1002023272364)))
async def challenge_gym(client, message):
    original_user_id = message.from_user.id  # Store the original user's ID

    await message.reply_photo(
        photo="https://graph.org/file/a52abd9ccb2be555e399b-89a794a27058b94855.jpg",  # Replace with actual file path or URL
        caption="Select a region to challenge a Gym Leader:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Kanto", callback_data=f"region_Kanto_{original_user_id})"             InlineKeyboardButton("Johto", callback_data=f"region_Johto_{original_user_id}"),
             InlineKeyboardButton("Hoenn", callback_data=f"region_Hoenn_{original_user_id}"),
             InlineKeyboardButton("Sinnoh", callback_data=f"region_Sinnoh_{original_user_id}")],
            [InlineKeyboardButton("Unova", callback_data=f"region_Unova_{original_user_id}"),
             InlineKeyboardButton("Kalos", callback_data=f"region_Kalos_{original_user_id}"),
             InlineKeyboardButton("Alola", callback_data=f"region_Alola_{original_user_id}"),
             InlineKeyboardButton("Galar", callback_data=f"region_Galar_{original_user_id}")]
        ])
    )


@app.on_callback_query(filters.regex(r"^region_(\w+)_(\d+)$"))
async def select_region(client, callback_query):
    region, original_user_id = re.match(r"^region_(\w+)_(\d+)$", callback_query.data).groups()

    if int(original_user_id) != callback_query.from_user.id:
        await callback_query.answer("This button is not for you!", show_alert=True)
        return

    user_data = await trainersdb.find_one({"trainer_id": callback_query.from_user.id})
    if not user_data:
        await callback_query.answer("You haven't started your journey yet. Begin earning badges by challenging gym leaders!", show_alert=True)
        return

    region_order = ["Kanto", "Johto", "Hoenn", "Sinnoh", "Unova", "Kalos", "Alola", "Galar"]
    current_index = region_order.index(region)

    if current_index > 0:
        previous_region = region_order[current_index - 1]
        badges = user_data.get("badges", [])
        previous_region_badges = [badge for badge in badges if badge['region'] == previous_region]
        if len(previous_region_badges) < 4:
            await callback_query.answer(f"You haven't completed {previous_region}!", show_alert=True)
            return

    region_badges = {r: [] for r in REGIONAL_GYM_GROUP_IDS.keys()}
    badges = user_data.get("badges", [])
    for badge in badges:
        if badge['region'] in region_badges:
            region_badges[badge['region']].append(badge['badge'])

    gyms = REGIONAL_GYM_GROUP_IDS[region]
    keyboard = [
        [InlineKeyboardButton(gym, callback_data=f"gym_{region}_{gym}") for gym in list(gyms.keys())[:2]],
        [InlineKeyboardButton(gym, callback_data=f"gym_{region}_{gym}") for gym in list(gyms.keys())[2:]],
    ]

    if len(region_badges.get(region, [])) >= 4:
        keyboard.append([InlineKeyboardButton("Elite", callback_data=f"elite_{region}")])

    keyboard.append([InlineKeyboardButton("Back", callback_data=f"back_to_regions_{original_user_id}")])

    await callback_query.message.edit_text(
        f"Select a Gym in **{region}:**",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    await callback_query.answer()


@app.on_callback_query(filters.regex(r"^back_to_regions_(\d+)$"))
async def back_to_regions(client, callback_query):
    original_user_id = re.match(r"^back_to_regions_(\d+)$", callback_query.data).group(1)

    # Ensure that the original user is interacting with the button
    if int(original_user_id) != callback_query.from_user.id:
        await callback_query.answer("This button is not for you!", show_alert=True)
        return

    await callback_query.message.edit_text(


@app.on_callback_query(filters.regex(r"^gym_(.+)_(.+)$"))
async def challenge_gym_leader(client, callback_query):
    match = re.match(r"^gym_(.+)_(.+)$", callback_query.data)
    if not match:
        await callback_query.answer("Invalid gym data!", show_alert=True)
        return

    region, gym = match.groups()
    group_id = REGIONAL_GYM_GROUP_IDS.get(region, {}).get(gym)
    if not group_id:
        await callback_query.answer("Gym not found!", show_alert=True)
        return

    user = callback_query.from_user
    username = f"@{user.username}" if user.username else "None"

    if group_id not in pending_requests:
        pending_requests[group_id] = []

    if user.id in pending_requests[group_id]:
        await callback_query.answer("You already have a pending request for this gym! Please wait for a response.", show_alert=True)
        return

    pending_requests[group_id].append(user.id)

    await client.send_message(
        chat_id=group_id,
        text=f"**➤ [ NEW CHALLENGE ]**\n• Name: {user.first_name}\n• ID: {user.id}\n• Username: {username}\n\n>Do you accept the challenge?",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Accept", callback_data=f"accept_{user.id}_{group_id}"),
             InlineKeyboardButton("❌ Decline", callback_data=f"decline_{user.id}_{group_id}")]
        ])
    )

    await callback_query.message.edit_text(
        "Your request has been sent to the Gym Leader. Please wait patiently for a response."
    )

    await callback_query.answer("Challenge sent!")



@app.on_callback_query(filters.regex(r"^challenge_elite_(.+)_(.+)$"))
async def challenge_elite(client, callback_query):
    match = re.match(r"^challenge_elite_(.+)_(.+)$", callback_query.data)
    region, elite = match.groups()

    user_data = await trainersdb.find_one({"trainer_id": callback_query.from_user.id})
    if not user_data:
        await callback_query.answer("You haven't started your journey yet. Begin earning badges by challenging gym leaders!", show_alert=True)
        return

    badges = user_data.get("badges")
    if not badges or not isinstance(badges, list):
        await callback_query.answer("You haven't earned any badges yet. Start earning them by defeating gym leaders!", show_alert=True)
        return

    region_badges = {r: [] for r in ELITE_GYM_GROUP_IDS.keys()}
    for badge in badges:
        if badge['region'] in region_badges:
            region_badges[badge['region']].append(badge['badge'])

    if len(region_badges.get(region, [])) < 4:
        await callback_query.answer(f"You need at least 4 badges from the {region} region to challenge the Elite!", show_alert=True)
        return

    elites = ELITE_GYM_GROUP_IDS.get(region)
    if not elites or elite not in elites:
        await callback_query.answer(f"No Elite member named {elite} found in the {region} region.", show_alert=True)
        return

    group_id = elites[elite]
    user = callback_query.from_user
    username = f"@{user.username}" if user.username else "None"

    await client.send_message(
        chat_id=group_id,
        text=f"**➤ [ NEW CHALLENGE ]**\n• Name: {user.first_name}\n• ID: {user.id}\n• Username: {username}\n\n>Do you accept the challenge?",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Accept", callback_data=f"accept_{user.id}_{group_id}"),
             InlineKeyboardButton("❌ Decline", callback_data=f"decline_{user.id}_{group_id}")]
        ])
    )
    await callback_query.answer(f"Challenge to {elite} sent!")



@app.on_callback_query(filters.regex(r"^elite_(.+)$"))
async def challenge_elite(client, callback_query):
    match = re.match(r"^elite_(.+)$", callback_query.data)
    region = match.group(1)

    user_data = await trainersdb.find_one({"trainer_id": callback_query.from_user.id})
    if not user_data:
        await callback_query.answer("You haven't started your journey yet. Begin earning badges by challenging gym leaders!", show_alert=True)
        return

    badges = user_data.get("badges")
    if not badges or not isinstance(badges, list):
        await callback_query.answer("You haven't earned any badges yet. Start earning them by defeating gym leaders!", show_alert=True)
        return

    region_badges = {r: [] for r in ELITE_GYM_GROUP_IDS.keys()}
    for badge in badges:
        if badge['region'] in region_badges:
            region_badges[badge['region']].append(badge['badge'])

    if len(region_badges.get(region, [])) < 4:
        await callback_query.answer(f"You need at least 4 badges from the {region} region to challenge the Elite!", show_alert=True)
        return

    elites = ELITE_GYM_GROUP_IDS.get(region)
    if not elites:
        await callback_query.answer("No Elite members found for this region.", show_alert=True)
        return

    keyboard = [
        [InlineKeyboardButton(elite, callback_data=f"challenge_elite_{region}_{elite}") for elite in list(elites.keys())[:2]],
        [InlineKeyboardButton(elite, callback_data=f"challenge_elite_{region}_{elite}") for elite in list(elites.keys())[2:]],
        [InlineKeyboardButton("Back", callback_data="back_to_regions")]
    ]

    await callback_query.message.edit_text(
        f"Select an Elite member to challenge in **{region}**:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    await callback_query.answer()


@app.on_callback_query(filters.regex(r"^accept_(.+)_(.+)$"))
async def accept_challenge(client, callback_query):
    match = re.match(r"^accept_(.+)_(.+)$", callback_query.data)
    user_id, group_id = match.groups()

    chat_member = await client.get_chat_member(group_id, callback_query.from_user.id)
    status = str(chat_member.status)
    if status not in ["ChatMemberStatus.ADMINISTRATOR", "ChatMemberStatus.OWNER"]:
        await callback_query.answer("You do not have the [ Authority ]", show_alert=True)
        return

    expiration_time = datetime.now() + timedelta(minutes=5)

    invite_link = await client.create_chat_invite_link(
        chat_id=group_id,
        expire_date=expiration_time,
        member_limit=1
    )

    await callback_query.message.edit_text(f"The challenge has been accepted!")

    await client.send_message(
        chat_id=int(user_id),
        text=(
            f"Your challenge has been accepted!\n"
            f"Here's a temporary link to join the group (valid for 5 minutes):\n\n{invite_link.invite_link}"
        )
    )
    
    if group_id in pending_requests and user_id in pending_requests[group_id]:
        pending_requests[group_id].remove(user_id)

    await callback_query.answer("Challenge accepted!")


@app.on_callback_query(filters.regex(r"^decline_(\d+)_(.+)$"))
async def decline_challenge(client, callback_query):
    match = re.match(r"^decline_(\d+)_(.+)$", callback_query.data)
    user_id, group_id = match.groups()
    print(callback_query.data)
    
    chat_member = await client.get_chat_member(group_id, callback_query.from_user.id)
    status = str(chat_member.status)
    if status not in ["ChatMemberStatus.ADMINISTRATOR", "ChatMemberStatus.OWNER"]:
        await callback_query.answer("You do not have the [Authority]", show_alert=True)
        return

    await callback_query.message.edit_text(f"The challenge has been declined.")
    await client.send_message(chat_id=int(user_id), text=f"Your challenge has been declined.")
    if group_id in pending_requests and user_id in pending_requests[group_id]:
        pending_requests[group_id].remove(user_id)

app.run()
