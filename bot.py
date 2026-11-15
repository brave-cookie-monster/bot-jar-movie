import asyncio
import datetime
import json
import os
import random
from typing import Optional

import aiohttp
import discord
from discord.ext import commands
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "")
TMDB_API_KEY = os.getenv("TMDB_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Animated Jar GIF used during the pick animation
JAR_ANIMATION_GIF = os.getenv(
    "JAR_ANIMATION_GIF",
    "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExMGl4bnphdGI4aHpxN3RmcGtyZnlwN3RycG83MmR2d245Nnl3N3U2dyZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/3o7TKtnuHOH6Ix2EPep/giphy.gif"
)

# Persistent database file path
DATA_FILE = "movies_data.json"
LEGACY_FILE = "movies.json"

# Setup bot intents
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


# ==========================================
# 1. DATABASE & PERSISTENCE MANAGEMENT
# ==========================================
def get_default_data():
    return {
        "movies": [
            "Inception",
            "Interstellar",
            "Spirited Away",
            "The Dark Knight",
            "Parasite",
            "Spider-Man: Into the Spider-Verse",
            "Whiplash",
            "Everything Everywhere All at Once"
        ],
        "current_selection": None,
        "history": []
    }


def load_data():
    """Loads all data. Handles legacy movies.json migration seamlessly."""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Ensure all required keys exist
                if "movies" not in data:
                    data["movies"] = []
                if "current_selection" not in data:
                    data["current_selection"] = None
                if "history" not in data:
                    data["history"] = []
                return data
        except Exception as e:
            print(f"Error loading {DATA_FILE}: {e}")

    # Check for legacy movies.json
    if os.path.exists(LEGACY_FILE):
        try:
            with open(LEGACY_FILE, "r", encoding="utf-8") as f:
                legacy = json.load(f)
                data = get_default_data()
                if isinstance(legacy, list):
                    data["movies"] = legacy
                save_data(data)
                return data
        except Exception as e:
            print(f"Error migrating {LEGACY_FILE}: {e}")

    # Fresh setup
    default_data = get_default_data()
    save_data(default_data)
    return default_data


def save_data(data):
    """Safely saves data to JSON so it persists across restarts."""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


# ==========================================
# 2. TMDB API INTEGRATION (Posters & Banners)
# ==========================================
async def fetch_movie_metadata(title: str) -> dict:
    """Fetches movie poster, backdrop banner, synopsis, and rating from TMDB."""
    default_info = {
        "title": title,
        "year": "Unknown",
        "overview": "No synopsis available.",
        "rating": "N/A",
        "poster_url": None,
        "backdrop_url": None,
        "tmdb_url": None,
    }

    if not TMDB_API_KEY or TMDB_API_KEY == "your_tmdb_api_key_here":
        return default_info

    url = "https://api.themoviedb.org/3/search/movie"
    params = {
        "api_key": TMDB_API_KEY,
        "query": title,
        "include_adult": "false"
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    results = data.get("results", [])
                    if results:
                        best = results[0]
                        poster_path = best.get("poster_path")
                        backdrop_path = best.get("backdrop_path")
                        release_date = best.get("release_date", "")
                        year = release_date[:4] if release_date else "Unknown"
                        rating = best.get("vote_average", 0.0)

                        return {
                            "title": best.get("title", title),
                            "year": year,
                            "overview": best.get("overview") or "No synopsis available.",
                            "rating": f"{rating:.1f}/10 ⭐" if rating else "N/A",
                            "poster_url": f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else None,
                            "backdrop_url": f"https://image.tmdb.org/t/p/w1280{backdrop_path}" if backdrop_path else None,
                            "tmdb_url": f"https://www.themoviedb.org/movie/{best.get('id')}",
                        }
    except Exception as e:
        print(f"Error fetching TMDB data for '{title}': {e}")

    return default_info


# ==========================================
# 3. GEMINI AI DISCUSSION GENERATOR
# ==========================================
async def generate_movie_discussion(title: str, year: str, overview: str) -> str:
    """Uses Gemini API to generate spoiler-free discussion starters and trivia."""
    if not GEMINI_API_KEY or GEMINI_API_KEY == "your_gemini_api_key_here":
        return (
            "⚠️ **Gemini API Key not set!**\n"
            "Please add `GEMINI_API_KEY` to your environment variables to enable AI movie discussion starters."
        )

    prompt = (
        f"You are an engaging and passionate host of a Discord movie club.\n"
        f"The group is watching '{title}' ({year}).\n"
        f"Synopsis: {overview}\n\n"
        "Provide:\n"
        "1. 🍿 **The Hook** (1-2 sentences on why this film is special or what vibe to expect, strictly SPOILER-FREE).\n"
        "2. 💡 **Behind-The-Scenes Trivia** (1 fascinating fact about the making or cast).\n"
        "3. 🎙️ **3 Discussion Questions** to ask the group after watching.\n\n"
        "Keep the formatting clean with Discord Markdown, bullet points, and emojis. Keep it concise."
    )

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
    payload = {
        "contents": [
            {
                "parts": [{"text": prompt}]
            }
        ]
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    candidates = result.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        if parts:
                            return parts[0].get("text", "Could not generate discussion points.")
                else:
                    err_text = await resp.text()
                    print(f"Gemini API error ({resp.status}): {err_text}")
    except Exception as e:
        print(f"Error calling Gemini API: {e}")

    return "⚠️ Sorry, could not generate AI discussion at this moment. Please check your API key or network."


# ==========================================
# 4. DISCORD SCHEDULED EVENT CREATOR
# ==========================================
async def schedule_discord_event(guild: discord.Guild, movie: dict) -> tuple[bool, str]:
    """Creates a Discord Scheduled Event with the movie's backdrop banner, title, and overview."""
    # Check permissions
    me = guild.me
    if not me.guild_permissions.manage_events:
        return False, "❌ I don't have the **Manage Events** permission in this server! Please grant it to my bot role."

    # Start time: Scheduled for 2 hours from now (UTC)
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    start_time = now_utc + datetime.timedelta(hours=2)
    end_time = start_time + datetime.timedelta(hours=2, minutes=30)

    # Download backdrop banner bytes for cover art if available
    image_bytes = None
    if movie.get("backdrop_url"):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(movie["backdrop_url"], timeout=aiohttp.ClientTimeout(total=5)) as resp:
                    if resp.status == 200:
                        image_bytes = await resp.read()
        except Exception as e:
            print(f"Could not download banner for event cover: {e}")

    desc = movie.get("overview", "")
    if len(desc) > 900:
        desc = desc[:900] + "..."
    desc = f"⭐ Rating: {movie.get('rating', 'N/A')}\n\n{desc}"

    try:
        event = await guild.create_scheduled_event(
            name=f"🎬 Movie Night: {movie['title']}",
            description=desc,
            start_time=start_time,
            end_time=end_time,
            entity_type=discord.EntityType.external,
            location="🍿 Voice / Watch Party Channel",
            privacy_level=discord.PrivacyLevel.guild_only,
            image=image_bytes
        )
        return True, f"✅ Event **{event.name}** has been scheduled on Discord!\n🔗 Check the **Events** tab in your server."
    except Exception as e:
        print(f"Failed to create Discord event: {e}")
        return False, f"❌ Failed to create event: {e}"


# ==========================================
# 5. UI EMBEDS & VIEWS
# ==========================================
def build_movie_embed(movie: dict, picked_by: str, movies_left: int) -> discord.Embed:
    """Builds a rich embed with TMDB posters, banners, and details."""
    title_str = f"🎬 {movie['title']}"
    if movie.get("year") and movie.get("year") != "Unknown":
        title_str += f" ({movie['year']})"

    embed = discord.Embed(
        title=title_str,
        url=movie.get("tmdb_url") or "",
        description=f"⭐ **Rating:** {movie.get('rating', 'N/A')}\n\n{movie.get('overview', 'No synopsis available.')}",
        color=discord.Color.from_rgb(229, 9, 20),  # Cinematic red
    )

    if movie.get("poster_url"):
        embed.set_thumbnail(url=movie["poster_url"])

    if movie.get("backdrop_url"):
        embed.set_image(url=movie["backdrop_url"])

    embed.set_footer(
        text=f"🫙 Movies remaining: {movies_left} | Drawn by {picked_by}"
    )
    return embed


class MovieResultView(discord.ui.View):
    """Buttons attached to the picked movie result."""

    def __init__(self, movie_data: dict = None):
        super().__init__(timeout=None)
        self.movie_data = movie_data

    @discord.ui.button(
        label="💬 AI Discussion",
        style=discord.ButtonStyle.primary,
        custom_id="btn_ai_discuss",
        emoji="🤖"
    )
    async def ai_discuss_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(thinking=True)

        data = load_data()
        movie = self.movie_data or data.get("current_selection")
        if not movie:
            await interaction.followup.send("❌ No movie selected currently.", ephemeral=True)
            return

        discussion_text = await generate_movie_discussion(
            movie["title"],
            movie.get("year", "Unknown"),
            movie.get("overview", "")
        )

        embed = discord.Embed(
            title=f"🎙️ Movie Club Guide: {movie['title']}",
            description=discussion_text,
            color=discord.Color.teal()
        )
        if movie.get("poster_url"):
            embed.set_thumbnail(url=movie["poster_url"])

        # Try to create a Discord thread under this message for organized discussion
        thread_created = False
        if interaction.channel and hasattr(interaction.channel, "create_thread") and interaction.message:
            try:
                thread_name = f"🎬 Discussion: {movie['title'][:80]}"
                # Check if thread already exists or create new
                thread = await interaction.message.create_thread(
                    name=thread_name,
                    auto_archive_duration=1440
                )
                await thread.send(embed=embed)
                await interaction.followup.send(
                    f"💬 I started a discussion thread for **{movie['title']}** here: {thread.mention}!"
                )
                thread_created = True
            except Exception as e:
                print(f"Could not create thread: {e}")

        if not thread_created:
            await interaction.followup.send(embed=embed)

    @discord.ui.button(
        label="📅 Schedule Event",
        style=discord.ButtonStyle.secondary,
        custom_id="btn_schedule_event",
        emoji="🗓️"
    )
    async def schedule_event_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.guild:
            await interaction.response.send_message("❌ Events can only be created inside a Discord server.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        data = load_data()
        movie = self.movie_data or data.get("current_selection")
        if not movie:
            await interaction.followup.send("❌ No active movie found.", ephemeral=True)
            return

        success, msg = await schedule_discord_event(interaction.guild, movie)
        await interaction.followup.send(msg, ephemeral=True)

    @discord.ui.button(
        label="🎲 Pick Another",
        style=discord.ButtonStyle.green,
        custom_id="btn_reroll_movie",
        emoji="🫙"
    )
    async def reroll_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await execute_movie_pick(interaction)


class MovieJarView(discord.ui.View):
    """Main persistent view with jar options."""

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="🎲 Pick a Movie",
        style=discord.ButtonStyle.green,
        custom_id="jar_pick_btn"
    )
    async def pick_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await execute_movie_pick(interaction)

    @discord.ui.button(
        label="🍿 Current Pick",
        style=discord.ButtonStyle.blurple,
        custom_id="jar_current_btn"
    )
    async def current_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        data = load_data()
        current = data.get("current_selection")
        if not current:
            await interaction.response.send_message(
                "🫙 No movie is currently selected. Click **🎲 Pick a Movie** to draw one!",
                ephemeral=True
            )
            return

        embed = build_movie_embed(current, current.get("picked_by", "Unknown"), len(data["movies"]))
        embed.title = f"🍿 [Current Selection] {current['title']} ({current.get('year', '')})"
        await interaction.response.send_message(
            embed=embed,
            view=MovieResultView(movie_data=current),
            ephemeral=True
        )

    @discord.ui.button(
        label="📜 Draw History",
        style=discord.ButtonStyle.grey,
        custom_id="jar_history_btn"
    )
    async def history_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        data = load_data()
        history = data.get("history", [])
        if not history:
            await interaction.response.send_message("📜 No movies have been drawn yet!", ephemeral=True)
            return

        recent = history[-10:][::-1]  # Last 10 draws, newest first
        desc_lines = []
        for i, item in enumerate(recent, 1):
            date_str = item.get("picked_at", "")[:10]
            desc_lines.append(f"**{i}. {item['title']}** ({item.get('year', 'N/A')}) — *Picked by {item.get('picked_by', 'Someone')} on {date_str}*")

        embed = discord.Embed(
            title="📜 Movie Draw History (Recent)",
            description="\n".join(desc_lines),
            color=discord.Color.dark_teal()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(
        label="📋 View Jar List",
        style=discord.ButtonStyle.grey,
        custom_id="jar_list_btn"
    )
    async def list_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        data = load_data()
        movies = data.get("movies", [])
        if not movies:
            await interaction.response.send_message("🫙 The jar is currently empty. Add movies using `!add <title>`!", ephemeral=True)
            return

        list_str = "\n".join([f"• {m}" for m in movies])
        if len(list_str) > 1900:
            list_str = list_str[:1900] + "\n...and more!"

        embed = discord.Embed(
            title=f"🍿 Movies in the Jar ({len(movies)} Total)",
            description=list_str,
            color=discord.Color.gold()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)


# ==========================================
# 6. ANIMATED DRAW SEQUENCE
# ==========================================
async def execute_movie_pick(interaction: discord.Interaction):
    """Executes the two-step animated jar draw and reveals the TMDB-enriched movie."""
    data = load_data()
    movies = data.get("movies", [])

    if not movies:
        await interaction.response.send_message(
            "🫙 The movie jar is empty! Add movies first with `!add <title>`.",
            ephemeral=True
        )
        return

    # Choose a random title
    chosen_title = random.choice(movies)

    # 1. First Response: Send the Animated Jar GIF
    shaking_embed = discord.Embed(
        title="🫙 Shaking the Movie Jar...",
        description=(
            "✨ *Reaching into the jar for tonight's winning film...*\n"
            "Hold on to your popcorn!"
        ),
        color=discord.Color.gold()
    )
    shaking_embed.set_image(url=JAR_ANIMATION_GIF)
    shaking_embed.set_footer(text=f"Drawing from {len(movies)} possible features...")

    # We send the initial animated message
    if interaction.response.is_done():
        msg = await interaction.followup.send(embed=shaking_embed)
    else:
        await interaction.response.send_message(embed=shaking_embed)
        msg = await interaction.original_response()

    # 2. Asynchronous wait + fetch TMDB data concurrently
    await asyncio.sleep(2.5)  # Let the animation play
    movie_info = await fetch_movie_metadata(chosen_title)

    # 3. Save to persistent storage (current_selection & history)
    user_name = interaction.user.display_name
    record = {
        **movie_info,
        "picked_by": user_name,
        "picked_by_id": interaction.user.id,
        "picked_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }

    data["current_selection"] = record
    data["history"].append(record)
    save_data(data)

    # 4. Reveal the winning movie
    reveal_embed = build_movie_embed(movie_info, user_name, len(movies))
    result_view = MovieResultView(movie_data=record)

    await msg.edit(embed=reveal_embed, view=result_view)


# ==========================================
# 7. BOT COMMANDS & EVENTS
# ==========================================
@bot.event
async def on_ready():
    # Register persistent views so buttons work across bot restarts
    bot.add_view(MovieJarView())
    bot.add_view(MovieResultView())

    print("========================================")
    print(f"Logged in successfully as: {bot.user.name} (ID: {bot.user.id})")
    print(f"TMDB Integration: {'Enabled ✅' if TMDB_API_KEY and TMDB_API_KEY != 'your_tmdb_api_key_here' else 'Disabled ⚠️ (No API Key)'}")
    print(f"Gemini AI:        {'Enabled ✅' if GEMINI_API_KEY and GEMINI_API_KEY != 'your_gemini_api_key_here' else 'Disabled ⚠️ (No API Key)'}")
    print("Movie Jar Bot is online and ready on bot-hosting.com!")
    print("========================================")


@bot.command(name="jar", help="Spawns the interactive Movie Jar message with buttons!")
async def jar_cmd(ctx):
    data = load_data()
    embed = discord.Embed(
        title="🍿 Welcome to the Movie Pick Jar!",
        description=(
            "Can't decide what to watch tonight? Let the jar decide!\n\n"
            "• Click **🎲 Pick a Movie** to draw with animation.\n"
            "• Click **🍿 Current Pick** to see the active film.\n"
            "• Click **📜 Draw History** to see past picks.\n"
            "• Use `!add <movie>` to toss new titles in."
        ),
        color=discord.Color.dark_magenta(),
    )
    embed.set_thumbnail(url=JAR_ANIMATION_GIF)
    embed.set_footer(text=f"Total movies currently in jar: {len(data['movies'])}")
    await ctx.send(embed=embed, view=MovieJarView())


@bot.command(name="add", help="Adds a movie title to the jar. Usage: !add Inception")
async def add_cmd(ctx, *, movie_name: str):
    clean_name = movie_name.strip()
    data = load_data()

    # Check for duplicate (case-insensitive)
    if any(m.lower() == clean_name.lower() for m in data["movies"]):
        await ctx.send(f"⚠️ **{clean_name}** is already in the jar!")
        return

    # Look up TMDB to verify title formatting if available
    meta = await fetch_movie_metadata(clean_name)
    official_title = meta.get("title") or clean_name
    year_str = f" ({meta['year']})" if meta.get("year") and meta.get("year") != "Unknown" else ""

    data["movies"].append(official_title)
    save_data(data)

    embed = discord.Embed(
        title="✅ Movie Added to the Jar!",
        description=f"Added **{official_title}**{year_str}.\nTotal movies in the jar: **{len(data['movies'])}**",
        color=discord.Color.green()
    )
    if meta.get("poster_url"):
        embed.set_thumbnail(url=meta["poster_url"])

    await ctx.send(embed=embed)


@bot.command(name="remove", help="Removes a movie title from the jar. Usage: !remove Inception")
async def remove_cmd(ctx, *, movie_name: str):
    data = load_data()
    match = next((m for m in data["movies"] if m.lower() == movie_name.lower().strip()), None)

    if match:
        data["movies"].remove(match)
        save_data(data)
        await ctx.send(f"🗑️ Removed **{match}** from the jar. (**{len(data['movies'])}** remaining)")
    else:
        await ctx.send(f"❌ Could not find **'{movie_name}'** in the jar.")


@bot.command(name="current", help="Shows the currently selected movie.")
async def current_cmd(ctx):
    data = load_data()
    current = data.get("current_selection")
    if not current:
        await ctx.send("🫙 No movie is currently selected. Use `!jar` to pick one!")
        return

    embed = build_movie_embed(current, current.get("picked_by", "Unknown"), len(data["movies"]))
    embed.title = f"🍿 [Current Selection] {current['title']} ({current.get('year', '')})"
    await ctx.send(embed=embed, view=MovieResultView(movie_data=current))


@bot.command(name="history", help="Displays recent draw history.")
async def history_cmd(ctx):
    data = load_data()
    history = data.get("history", [])
    if not history:
        await ctx.send("📜 No movies have been drawn yet!")
        return

    recent = history[-10:][::-1]
    desc_lines = []
    for i, item in enumerate(recent, 1):
        date_str = item.get("picked_at", "")[:10]
        desc_lines.append(f"**{i}. {item['title']}** ({item.get('year', 'N/A')}) — *Picked by {item.get('picked_by', 'Someone')} on {date_str}*")

    embed = discord.Embed(
        title="📜 Movie Draw History (Recent)",
        description="\n".join(desc_lines),
        color=discord.Color.dark_teal()
    )
    await ctx.send(embed=embed)


@bot.command(name="discuss", help="Starts an AI movie discussion for the current or specified movie.")
async def discuss_cmd(ctx, *, movie_title: Optional[str] = None):
    data = load_data()
    if movie_title:
        meta = await fetch_movie_metadata(movie_title)
    else:
        meta = data.get("current_selection")

    if not meta:
        await ctx.send("❌ No movie specified and no current selection found. Usage: `!discuss Inception` or pick a movie first!")
        return

    async with ctx.typing():
        discussion_text = await generate_movie_discussion(
            meta["title"],
            meta.get("year", "Unknown"),
            meta.get("overview", "")
        )

    embed = discord.Embed(
        title=f"🎙️ AI Discussion Starter: {meta['title']}",
        description=discussion_text,
        color=discord.Color.teal()
    )
    if meta.get("poster_url"):
        embed.set_thumbnail(url=meta["poster_url"])

    msg = await ctx.send(embed=embed)

    # Optional: create a discussion thread
    if hasattr(ctx.channel, "create_thread"):
        try:
            await msg.create_thread(name=f"🎬 Discussion: {meta['title'][:80]}")
        except Exception:
            pass


@bot.command(name="schedule", help="Schedules a Discord server event for the current or specified movie.")
async def schedule_cmd(ctx, *, movie_title: Optional[str] = None):
    data = load_data()
    if movie_title:
        meta = await fetch_movie_metadata(movie_title)
    else:
        meta = data.get("current_selection")

    if not meta:
        await ctx.send("❌ No movie specified and no active pick. Usage: `!schedule Interstellar` or pick a movie with `!jar` first!")
        return

    success, msg = await schedule_discord_event(ctx.guild, meta)
    await ctx.send(msg)


# ==========================================
# 8. START BOT
# ==========================================
if __name__ == "__main__":
    if not DISCORD_TOKEN or DISCORD_TOKEN == "your_discord_bot_token_here":
        print("❌ ERROR: DISCORD_TOKEN is missing!")
        print("Please set your bot token in the .env file or hosting environment variables.")
    else:
        bot.run(DISCORD_TOKEN)
