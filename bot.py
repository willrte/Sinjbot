import discord
import asyncio
import random
import os
from dotenv import load_dotenv

# Note: Make sure to have the required libraries installed:
# pip install discord.py python-dotenv
# Also ensure you have FFmpeg installed and available in your system PATH for audio playback.

# Load environment variables (like the bot token)
load_dotenv()

# Set up necessary Discord intents for voice and message tracking
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
intents.guilds = True
intents.members = True

# === Configuration Constants ===
SOUND_FOLDER = "sounds"  # Folder where .mp3 sound files are stored
COMMAND_TRIGGER = "!gougougaga"  # Command to manually summon the sinj
CMD_ENABLE_AUTO = "!autosinj"    # Enable automatic sinj appearances
CMD_DISABLE_AUTO = "!stopsinj"   # Disable automatic appearances
CMD_HELP = "!helpsinj"           # Show help information
CMD_FAST = "!fastsinj"           # Force a sinj appearance soon
CMD_TIME = "!timesinj"           # Set custom time window for random appearances
SINJ_EMOJI = "🙊"                 # Emoji reaction added to command messages
ENABLE_LOGS = os.getenv("SINJBOT_LOGS", "true").lower() == "true"  # Control logging output
TOKEN = os.getenv("SINJBOT_TOKEN")  # Discord bot token from environment

class SinjBot(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        # Keeps track of running sinj tasks per voice channel
        self.channel_tasks = {}
        # Whether automatic mode is enabled per server
        self.guild_auto_enabled = {}
        # Whether fast mode is scheduled per channel
        self.fast_mode = {}
        # Per-server min/max wait durations (in seconds)
        self.guild_time_ranges = {}

    def log(self, msg):
        # Print log messages only if logging is enabled
        if ENABLE_LOGS:
            print(msg)

    def get_random_sound(self):
        # Selects a random .mp3 file from the sound folder
        files = [f for f in os.listdir(SOUND_FOLDER) if f.endswith(".mp3")]
        return os.path.join(SOUND_FOLDER, random.choice(files)) if files else None

    async def on_ready(self):
        # Called when the bot is ready and connected
        self.log(f"[READY] Logged in as {self.user}")
        for guild in self.guilds:
            self.guild_auto_enabled[guild.id] = True  # Auto mode on by default
            self.guild_time_ranges[guild.id] = (300, 3600)  # Default wait: 5min–60min
            self.log(f"[INFO] Auto mode ENABLED by default for {guild.name}")
            self.log("[INFO] Waiting for users to join voice channels to schedule sinj tasks.")

    async def on_voice_state_update(self, member, before, after):
        # Triggered when a user joins/leaves/moves voice channels
        if member.bot:
            return

        guild = member.guild
        if not self.guild_auto_enabled.get(guild.id, False):
            return

        for channel in guild.voice_channels:
            real_users = [m for m in channel.members if not m.bot]
            task_exists = channel.id in self.channel_tasks

            if real_users and not task_exists:
                # Schedule a new sinj task for this active voice channel
                task = asyncio.create_task(self.sinj_routine(channel))
                self.channel_tasks[channel.id] = task
                self.log(f"[AUTO] Scheduled sinj task for {channel.name} ({guild.name})")

            elif not real_users and task_exists:
                # Cancel any existing sinj task if the channel is now empty
                self.channel_tasks[channel.id].cancel()
                del self.channel_tasks[channel.id]
                self.log(f"[AUTO] Cancelled sinj task for {channel.name} ({guild.name})")

    async def sinj_routine(self, channel):
        # Main scheduling routine that plays a sound in a loop until stopped
        guild_id = channel.guild.id
        try:
            while True:
                min_delay, max_delay = self.guild_time_ranges.get(guild_id, (300, 3600))

                if self.fast_mode.get(channel.id, False):
                    wait_time = random.randint(30, 300)
                    self.fast_mode[channel.id] = False
                    self.log(f"[FAST MODE] Sinj will appear on {channel.name} in {round(wait_time / 60, 2)} minutes")
                else:
                    wait_time = random.randint(min_delay, max_delay)
                    self.log(f"[SCHEDULED] Sinj will strike {channel.name} in {round(wait_time / 60, 2)} minutes")

                await asyncio.sleep(wait_time)

                # Skip playback if the channel is now empty
                if len([m for m in channel.members if not m.bot]) == 0:
                    self.log(f"[ABORTED] No humans in {channel.name}, skipping intervention")
                    break

                await self.play_sinj_sound(channel, triggered_by="auto")

                # Schedule the next round
                wait_time = random.randint(min_delay, max_delay)
                self.log(f"[RESCHEDULED] Next sinj appearance on {channel.name} in {round(wait_time / 60, 2)} minutes")
                await asyncio.sleep(wait_time)

        except asyncio.CancelledError:
            self.log(f"[CANCELLED] Sinj routine stopped for {channel.name}")

    async def play_sinj_sound(self, channel, triggered_by="unknown"):
        # Connect to the channel, play the sound, and disconnect
        sound = self.get_random_sound()
        if not sound:
            self.log(f"[ERROR] No sound file found in {SOUND_FOLDER}")
            return
        try:
            vc = await channel.connect()
            vc.play(discord.FFmpegPCMAudio(sound))
            self.log(f"[PLAY] Sinj triggered ({triggered_by}) on {channel.name} using {os.path.basename(sound)}")
            while vc.is_playing():
                await asyncio.sleep(0.5)
            await vc.disconnect()
        except Exception as e:
            self.log(f"[ERROR] Playback failed: {e}")

    async def react(self, message):
        # Add a monkey emoji reaction to the user's message
        try:
            await message.add_reaction(SINJ_EMOJI)
        except:
            pass

    async def on_message(self, message):
        # Handle incoming commands sent via text
        if message.author.bot:
            return

        content = message.content.strip().lower()
        guild_id = message.guild.id if message.guild else None

        if content == COMMAND_TRIGGER:
            # Manually trigger sinj if user is in a voice channel
            if message.author.voice and message.author.voice.channel:
                await self.react(message)
                await self.play_sinj_sound(message.author.voice.channel, triggered_by="manual command")
            else:
                self.log(f"[IGNORED] {message.author} used !gougougaga outside voice")

        elif content == CMD_ENABLE_AUTO:
            # Enable auto mode for this guild
            self.guild_auto_enabled[guild_id] = True
            await self.react(message)
            self.log(f"[ENABLED] Auto mode ON for {message.guild.name}")
            self.log("[INFO] Waiting for users to join voice channels to schedule sinj tasks.")
            for vc in message.guild.voice_channels:
                await self.on_voice_state_update(message.author, None, message.author.voice)

        elif content == CMD_DISABLE_AUTO:
            # Disable auto mode and cancel existing tasks
            self.guild_auto_enabled[guild_id] = False
            await self.react(message)
            self.log(f"[DISABLED] Auto mode OFF for {message.guild.name}")
            for cid, task in list(self.channel_tasks.items()):
                if self.get_channel(cid).guild.id == guild_id:
                    task.cancel()
                    del self.channel_tasks[cid]

        elif content == CMD_FAST:
            # Force a sinj appearance soon for the user's channel
            if message.author.voice and message.author.voice.channel:
                channel_id = message.author.voice.channel.id
                self.fast_mode[channel_id] = True
                delay = random.randint(30, 300)
                self.log(f"[FAST MODE] Fast sinj mode activated for {message.author.voice.channel.name}, appearance in {round(delay / 60, 2)} minutes")
                await self.react(message)
            else:
                self.log(f"[IGNORED] {message.author} used !fastsinj outside voice")

        elif content.startswith(CMD_TIME):
            # Adjust the min/max time window for sinj routine
            try:
                parts = content.split()
                if len(parts) == 3 and parts[1].endswith("m") and parts[2].endswith("m"):
                    min_minutes = int(parts[1][:-1])
                    max_minutes = int(parts[2][:-1])
                    if min_minutes < 1 or max_minutes < min_minutes:
                        raise ValueError
                    self.guild_time_ranges[guild_id] = (min_minutes * 60, max_minutes * 60)
                    await self.react(message)
                    await message.channel.send(f"✅ New sinj delay range: {min_minutes}–{max_minutes} minutes")
                    self.log(f"[CUSTOM RANGE] New sinj timer range for {message.guild.name}: {min_minutes}m to {max_minutes}m")
                else:
                    raise ValueError
            except:
                await message.channel.send("❌ Usage: `!timesinj [min]m [max]m` (e.g. `!timesinj 2m 120m`)")
                self.log("[ERROR] Invalid !timesinj format or values")

        elif content == CMD_HELP:
            # Send help message to the Discord channel
            await self.react(message)
            min_s, max_s = self.guild_time_ranges.get(guild_id, (300, 3600))
            help_text = (
                "**🙊 SinjBot Commands:**\n"
                f"`{COMMAND_TRIGGER}` – Summon the sinj in your current voice channel\n"
                f"`{CMD_ENABLE_AUTO}` – Enable automatic sinj appearances\n"
                f"`{CMD_DISABLE_AUTO}` – Disable automatic appearances\n"
                f"`{CMD_FAST}` – Trigger a sinj appearance within the next 30s to 5min\n"
                f"`{CMD_TIME} [min]m [max]m` – Set custom delay range in minutes (e.g., 2m 120m)\n"
                f"`{CMD_HELP}` – Show this help message\n"
                f"\nCurrent auto delay: {int(min_s/60)}m to {int(max_s/60)}m"
            )
            await message.channel.send(help_text)



# Ensure the bot token is set in the environment variables
if not TOKEN:
    raise ValueError("Please set the SINJBOT_TOKEN environment variable with your bot token.")

# Ensure the sound folder exists
if not os.path.exists(SOUND_FOLDER):
    raise FileNotFoundError(f"Sound folder '{SOUND_FOLDER}' does not exist. Please create it and add sound files.")

# Start the bot
bot = SinjBot()
bot.run(TOKEN)


