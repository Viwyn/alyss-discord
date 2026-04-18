# lotus-bot

Custom Discord bot with cog-based announcement scheduling.

## Features

- Cog-based architecture using `discord.py`
- Per-server announcement channel
- Add custom announcement times on specific weekdays
- Per-server UTC offset for schedule timing
- Persistent storage in `data/announcement_times.json`

## Setup

1. Create and activate a virtual environment
2. Install dependencies
3. Set your bot token in `DISCORD_TOKEN`
4. Run the bot

### Install

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Run

```powershell
$env:DISCORD_TOKEN="YOUR_BOT_TOKEN"
python bot.py
```

Optional prefix override:

```powershell
$env:BOT_PREFIX="!"
```

## Commands

- `!setannouncementchannel #channel`
- `!setannouncementtimezone <offset>` where offset is `-12` to `14`
- `!addannouncementtime <HH:MM> <days> <message>` where days can be `all` or comma-separated weekdays like `thu` or `mon,wed,fri`
- `!setannouncementdays <id> <days>`
- `!listannouncementtimes`
- `!removeannouncementtime <id>`

## Example

```text
!setannouncementchannel #announcements
!setannouncementtimezone 8
!addannouncementtime 09:00 thu Weekly Thursday reminder
!addannouncementtime 18:30 mon,wed,fri Event starts in 30 minutes
!setannouncementdays 1 all
!listannouncementtimes
```
