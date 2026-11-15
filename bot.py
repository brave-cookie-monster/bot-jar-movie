import json
import os
import random
import discord
from discord.ext import commands

# 1. Setup Intents
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# 2. Database Handling (JSON file to persist movies)
DATA_FILE = "movies.json"


def load_movies():
  if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r") as f:
      return json.load(f)
  # Default starter movies if file doesn't exist yet
  default_movies = [
      "Inception",
      "Interstellar",
      "Spirited Away",
      "The Dark Knight",
      "Parasite",
  ]
  save_movies(default_movies)
  return default_movies


def save_movies(movies):
  with open(DATA_FILE, "w") as f:
    json.dump(movies, f, indent=4)


# 3. Interactive View with Buttons
class MovieJarView(discord.ui.View):

  def __init__(self):
    super().__init__(timeout=None)  # Buttons won't expire

  @discord.ui.button(
      label="🎲 Pick a Movie",
      style=discord.ButtonStyle.green,
      custom_id="pick_movie_btn",
  )
  async def pick_movie_callback(
      self, interaction: discord.Interaction, button: discord.ui.Button
  ):
    movies = load_movies()
    if not movies:
      await interaction.response.send_message(
          "🫙 The movie jar is empty! Add some movies first.", ephemeral=True
      )
      return

    chosen = random.choice(movies)
    embed = discord.Embed(
        title="🎬 The Movie Jar Has Spoken!",
        description=f"Tonight's winning feature film is:\n\n# **{chosen}**",
        color=discord.Color.blurple(),
    )
    embed.set_footer(
        text=f"Total movies in jar: {len(movies)} | Picked for"
        f" {interaction.user.display_name}"
    )
    await interaction.response.send_message(embed=embed)

  @discord.ui.button(
      label="📋 View Jar List",
      style=discord.ButtonStyle.grey,
      custom_id="view_movies_btn",
  )
  async def view_movies_callback(
      self, interaction: discord.Interaction, button: discord.ui.Button
  ):
    movies = load_movies()
    if not movies:
      await interaction.response.send_message(
          "🫙 The movie jar is currently empty.", ephemeral=True
      )
      return

    movie_list_str = "\n".join([f"• {m}" for m in movies])
    if len(movie_list_str) > 1900:
      movie_list_str = movie_list_str[:1900] + "\n...and more!"

    embed = discord.Embed(
        title="🍿 Current Movie Jar Contents",
        description=movie_list_str,
        color=discord.Color.gold(),
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


# 4. Bot Events & Commands
@bot.event
async def on_ready():
  print(f"Logged in successfully as {bot.user.name} (ID: {bot.user.id})")
  print("Movie Jar Bot is online and ready!")


@bot.command(name="jar", help="Spawns the interactive Movie Jar message with buttons!")
async def jar(ctx):
  embed = discord.Embed(
      title="🍿 Welcome to the Movie Pick Jar!",
      description=(
          "Click **Pick a Movie** to draw a random title, or use `!add` to toss"
          " a new film into the jar!"
      ),
      color=discord.Color.dark_magenta(),
  )
  embed.set_footer(text="Powered by your custom Discord bot hosting container.")
  
  # Send message with interactive buttons attached
  await ctx.send(embed=embed, view=MovieJarView())


@bot.command(name="add", help="Adds a movie. Usage: !add Movie Title")
async def add(ctx, *, movie_name: str):
  movies = load_movies()
  clean_name = movie_name.strip()
  
  if clean_name in movies:
    await ctx.send(f"⚠️ **{clean_name}** is already in the jar!")
    return

  movies.append(clean_name)
  save_movies(movies)
  
  await ctx.send(
      f"✅ Added **{clean_name}** to the jar! There are now **{len(movies)}**"
      " movies waiting."
  )


@bot.command(name="remove", help="Removes a movie. Usage: !remove Movie Title")
async def remove(ctx, *, movie_name: str):
  movies = load_movies()
  match = next((m for m in movies if m.lower() == movie_name.lower()), None)
  
  if match:
    movies.remove(match)
    save_movies(movies)
    await ctx.send(f"🗑️ Removed **{match}** from the jar.")
  else:
    await ctx.send(f"❌ Could not find '{movie_name}' in the jar.")


# 5. Run the Bot (Replace with your token or use environment variables)
TOKEN = os.getenv("DISCORD_TOKEN", "YOUR_DISCORD_BOT_TOKEN_HERE")
bot.run(TOKEN)