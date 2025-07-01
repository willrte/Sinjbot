# 🐒 SinjBot

A Discord bot that randomly joins a voice channel, plays a monkey scream, and leaves.  

---

##  Features

- 🎲 Random automatic appearances (every 5 to 60 minutes)
- 🔊 Custom Random monkey sound playback from a `/sounds/` folder
- 👤 Manual summon with `!gougougaga`
- ⏱️ `!fastsinj` triggers a scream in under 5 minutes
- 🔁 `!autosinj` / `!stopsinj` to enable/disable auto mode
- 🐵 Reacts with a monkey emoji when commands are used
- ⚙️ `!timesinj [min]m [max]m` allows custom bot delay ranges (e.g. `!timesinj 3m 90m`)
- 🧾 `!helpsinj` shows a clean help message in Discord
- 🛠️ Optional logs (enabled by default, configurable)

---

##  Quick Setup

⚠️ Requirements ⚠️

- Python 3.8+
- ffmpeg installed and added to system PATH (required for audio playback)

---

1. Clone or download this repository

2. Add `.mp3` files to the `sounds/` directory

3. Install the required Python libraries:
   - `discord.py`
   - `python-dotenv`

   You can install them using:
   pip install -U discord.py python-dotenv

4.  Fill in your bot token in `.env` under `SINJBOT_TOKEN=`your token

5. Run the bot:
   python bot.py

---

##  Folder Structure

sinjbot/  
├── bot.py  
├── .env  
└── sounds/  
  ├── sound1.mp3  
  ├── sound2.mp3  
  └── ...

---

##  Available Commands

| Command        | Description                          |
|----------------|--------------------------------------|
| `!gougougaga`  | Instantly summon the bot          |
| `!autosinj`    | Enable automatic random visits       |
| `!stopsinj`    | Disable automatic visits             |
| `!fastsinj`    | Force bot to come in <5 minutes   |
| `!timesinj [min]m [max]m`   | Set custom bot delay range in minutes (e.g. `!timesinj 2m 120m`) |
| `!helpsinj`    | Display all available commands       |

---


##  Notes

- Auto mode is enabled by default when the bot starts
- To disable logs, set `SINJBOT_LOGS=false` in your `.env`
- Never share your Discord bot token
