# 🍿 Discord Movie Pick Jar Bot

An interactive, feature-packed Discord bot for movie nights. Features an animated jar reveal, TMDB posters & banners, persistent selection & draw history, AI-powered movie discussion guides, and automatic Discord event scheduling.

Designed to run seamlessly on [bot-hosting.com](https://bot-hosting.com) and local environments.

---

## ✨ Features

1. **🫙 Animated Jar Reveal**: Clicking **"🎲 Pick a Movie"** plays a dynamic animated jar GIF for 2.5 seconds before unveiling the winning film.
2. **🎬 TMDB Posters & Banners**: Automatically fetches high-resolution movie posters, cinematic backdrop banners, release year, synopsis, and ratings from The Movie Database (TMDB).
3. **💾 Persistent State & Draw History**:
   - Saves current active movie selection and full draw history to `movies_data.json`.
   - Never loses your movie night pick or jar contents if the bot or server restarts.
4. **🤖 AI Movie Discussion Starter**:
   - Uses Google Gemini to generate spoiler-free movie hooks, interesting behind-the-scenes trivia, and 3 post-watch discussion questions.
   - Automatically opens a dedicated **Discord Thread** under the movie draw for your community.
5. **📅 Discord Scheduled Events**:
   - Create a Discord server scheduled event in 1-click using the **"📅 Schedule Event"** button or `!schedule`.
   - Automatically attaches the movie banner as the event cover art, synopsis, and schedules it.

---

## 🚀 Setup & Environment Variables

Create a `.env` file (or set these in the **Startup / Environment Variables** section on **bot-hosting.com**):

```env
# 1. Discord Bot Token (Required)
# From Discord Developer Portal -> Bot -> Token
DISCORD_TOKEN=your_discord_token_here

# 2. TMDB API Key (Recommended for posters & banners)
# Free from https://www.themoviedb.org/settings/api
TMDB_API_KEY=your_tmdb_api_key_here

# 3. Google Gemini API Key (Recommended for AI discussion starter)
# Free from https://aistudio.google.com/
GEMINI_API_KEY=your_gemini_api_key_here

# 4. Optional: Custom Animated Jar GIF
JAR_ANIMATION_GIF=https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExMGl4bnphdGI4aHpxN3RmcGtyZnlwN3RycG83MmR2d245Nnl3N3U2dyZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/3o7TKtnuHOH6Ix2EPep/giphy.gif
```

---

## ⚙️ Discord Bot Permissions Required

In the [Discord Developer Portal](https://discord.com/developers/applications):
1. **Bot Tab -> Privileged Gateway Intents**:
   - Turn **ON** `Message Content Intent`.
2. **Bot Permissions** when inviting to your server:
   - `Send Messages`
   - `Embed Links`
   - `Attach Files`
   - `Create Public Threads` / `Send Messages in Threads`
   - `Manage Events` (Required to schedule Discord events)

---

## 🕹️ Commands & Buttons

| Command | Description |
|---|---|
| `!jar` | Spawns the interactive Movie Jar panel with interactive buttons. |
| `!add <movie>` | Adds a new movie title to the jar (verifies with TMDB). |
| `!remove <movie>` | Removes a title from the jar. |
| `!current` | Shows the active movie selection, poster, and action buttons. |
| `!history` | Displays recent movie draw history. |
| `!discuss [movie]` | Generates AI discussion points & opens a Discord thread. |
| `!schedule [movie]` | Schedules a Discord server event for the movie. |

### Interactive Buttons:
* **🎲 Pick a Movie**: Plays the animated jar sequence and reveals tonight's movie.
* **🍿 Current Pick**: Pulls up the active movie selection.
* **📜 Draw History**: Shows the last 10 drawn titles and who picked them.
* **📋 View Jar List**: Displays all titles currently waiting in the jar.
* **💬 AI Discussion**: Generates discussion questions and opens a Discord thread.
* **📅 Schedule Event**: Creates an official Discord event for the film.
