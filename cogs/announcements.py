import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import discord
from discord.ext import commands, tasks

class AnnouncementTimeConverter(commands.Converter):
    async def convert(self, ctx: commands.Context, argument: str) -> str:
        try:
            parsed = datetime.strptime(argument, "%H:%M")
        except ValueError as exc:
            raise commands.BadArgument("Time must use 24-hour format HH:MM") from exc
        return parsed.strftime("%H:%M")

WEEKDAY_MAP = {
    "mon": 0,
    "monday": 0,
    "tue": 1,
    "tues": 1,
    "tuesday": 1,
    "wed": 2,
    "wednesday": 2,
    "thu": 3,
    "thur": 3,
    "thurs": 3,
    "thursday": 3,
    "fri": 4,
    "friday": 4,
    "sat": 5,
    "saturday": 5,
    "sun": 6,
    "sunday": 6,
}

WEEKDAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

class Announcements(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.storage_path = Path("data") / "announcement_times.json"
        self.data = self._load_data()
        self._normalize_data()
        self.dispatch_announcements.start()

    def cog_unload(self) -> None:
        self.dispatch_announcements.cancel()

    def _load_data(self) -> dict[str, Any]:
        if not self.storage_path.exists():
            return {"guilds": {}}
        with self.storage_path.open("r", encoding="utf-8") as handle:
            try:
                payload = json.load(handle)
                if isinstance(payload, dict) and isinstance(payload.get("guilds"), dict):
                    return payload
            except json.JSONDecodeError:
                pass
        return {"guilds": {}}

    def _save_data(self) -> None:
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        with self.storage_path.open("w", encoding="utf-8") as handle:
            json.dump(self.data, handle, indent=2)

    def _normalize_data(self) -> None:
        changed = False
        guilds = self.data.get("guilds", {})
        if not isinstance(guilds, dict):
            self.data["guilds"] = {}
            self._save_data()
            return
        for record in guilds.values():
            announcements = record.get("announcements", [])
            if not isinstance(announcements, list):
                record["announcements"] = []
                changed = True
                continue
            for entry in announcements:
                days = entry.get("days")
                if days is None:
                    entry["days"] = list(range(7))
                    changed = True
                    continue
                if not isinstance(days, list):
                    entry["days"] = list(range(7))
                    changed = True
                    continue
                cleaned: list[int] = []
                for value in days:
                    try:
                        idx = int(value)
                    except (TypeError, ValueError):
                        continue
                    if 0 <= idx <= 6 and idx not in cleaned:
                        cleaned.append(idx)
                if not cleaned:
                    cleaned = list(range(7))
                if cleaned != days:
                    entry["days"] = cleaned
                    changed = True
        if changed:
            self._save_data()

    def _parse_days(self, raw_days: str) -> list[int]:
        tokens = [part.strip().lower() for part in raw_days.split(",") if part.strip()]
        if not tokens:
            raise commands.BadArgument(
                "Provide weekdays like thu or mon,wed,fri or use all"
            )
        if len(tokens) == 1 and tokens[0] == "all":
            return list(range(7))
        days: list[int] = []
        for token in tokens:
            idx = WEEKDAY_MAP.get(token)
            if idx is None:
                raise commands.BadArgument(f"Unknown weekday: {token}")
            if idx not in days:
                days.append(idx)
        return sorted(days)

    def _format_days(self, days: list[int]) -> str:
        cleaned = sorted({d for d in days if 0 <= d <= 6})
        if cleaned == list(range(7)):
            return "Every day"
        return ",".join(WEEKDAY_NAMES[d] for d in cleaned)

    def _guild_record(self, guild_id: int) -> dict[str, Any]:
        guilds = self.data.setdefault("guilds", {})
        record = guilds.setdefault(
            str(guild_id),
            {
                "channel_id": None,
                "timezone_offset": 0,
                "next_id": 1,
                "announcements": [],
            },
        )
        record.setdefault("channel_id", None)
        record.setdefault("timezone_offset", 0)
        record.setdefault("next_id", 1)
        record.setdefault("announcements", [])
        return record

    @tasks.loop(seconds=20)
    async def dispatch_announcements(self) -> None:
        changed = False
        for guild_id, record in self.data.get("guilds", {}).items():
            channel_id = record.get("channel_id")
            if channel_id is None:
                continue
            try:
                offset = int(record.get("timezone_offset", 0))
            except (TypeError, ValueError):
                offset = 0
            now = datetime.now(timezone.utc) + timedelta(hours=offset)
            current_time = now.strftime("%H:%M")
            current_date = now.date().isoformat()
            current_weekday = now.weekday()

            channel = self.bot.get_channel(channel_id)
            if channel is None:
                guild = self.bot.get_guild(int(guild_id))
                if guild is not None:
                    channel = guild.get_channel(channel_id)

            if channel is None or not isinstance(channel, discord.TextChannel):
                continue

            for announcement in record.get("announcements", []):
                if announcement.get("time") != current_time:
                    continue
                raw_days = announcement.get("days", list(range(7)))
                try:
                    days = [int(d) for d in raw_days]
                except (TypeError, ValueError):
                    days = list(range(7))
                if current_weekday not in days:
                    continue
                if announcement.get("last_sent") == current_date:
                    continue
                try:
                    await channel.send(announcement.get("message", "Announcement"))
                    announcement["last_sent"] = current_date
                    changed = True
                except discord.DiscordException:
                    continue

        if changed:
            self._save_data()

    @dispatch_announcements.before_loop
    async def before_dispatch(self) -> None:
        await self.bot.wait_until_ready()

    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    @commands.command(name="setannouncementchannel")
    async def set_announcement_channel(
        self, ctx: commands.Context, channel: discord.TextChannel
    ) -> None:
        record = self._guild_record(ctx.guild.id)
        record["channel_id"] = channel.id
        self._save_data()
        await ctx.send(f"Announcement channel set to {channel.mention}")

    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    @commands.command(name="setannouncementtimezone")
    async def set_announcement_timezone(self, ctx: commands.Context, utc_offset: int) -> None:
        if utc_offset < -12 or utc_offset > 14:
            await ctx.send("Timezone offset must be between -12 and 14")
            return
        record = self._guild_record(ctx.guild.id)
        record["timezone_offset"] = utc_offset
        self._save_data()
        await ctx.send(f"Announcement timezone offset set to UTC{utc_offset:+d}")

    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    @commands.command(name="addannouncementtime")
    async def add_announcement_time(
        self,
        ctx: commands.Context,
        time_value: AnnouncementTimeConverter,
        days: str,
        *,
        message: str = "Announcement",
    ) -> None:
        parsed_days = self._parse_days(days)
        record = self._guild_record(ctx.guild.id)
        item_id = int(record.get("next_id", 1))
        record["next_id"] = item_id + 1
        record["announcements"].append(
            {
                "id": item_id,
                "time": time_value,
                "days": parsed_days,
                "message": message,
                "last_sent": None,
            }
        )
        self._save_data()
        await ctx.send(
            f"Added announcement #{item_id} at {time_value} on {self._format_days(parsed_days)}"
        )

    @commands.guild_only()
    @commands.command(name="listannouncementtimes")
    async def list_announcement_times(self, ctx: commands.Context) -> None:
        record = self._guild_record(ctx.guild.id)
        announcements = record.get("announcements", [])
        if not announcements:
            await ctx.send("No announcement times configured")
            return

        lines = [
            f"Timezone: UTC{int(record.get('timezone_offset', 0)):+d}",
            f"Channel ID: {record.get('channel_id')}",
            "Announcement schedule:",
        ]
        for entry in sorted(announcements, key=lambda x: x.get("time", "")):
            entry_days = entry.get("days", list(range(7)))
            if not isinstance(entry_days, list):
                entry_days = list(range(7))
            lines.append(
                f"#{entry.get('id')} - {entry.get('time')} - {self._format_days(entry_days)} - {entry.get('message')}"
            )

        await ctx.send("\n".join(lines))

    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    @commands.command(name="removeannouncementtime")
    async def remove_announcement_time(self, ctx: commands.Context, item_id: int) -> None:
        record = self._guild_record(ctx.guild.id)
        announcements = record.get("announcements", [])
        updated = [entry for entry in announcements if entry.get("id") != item_id]

        if len(updated) == len(announcements):
            await ctx.send(f"Announcement #{item_id} not found")
            return

        record["announcements"] = updated
        self._save_data()
        await ctx.send(f"Removed announcement #{item_id}")

    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    @commands.command(name="setannouncementdays")
    async def set_announcement_days(
        self, ctx: commands.Context, item_id: int, days: str
    ) -> None:
        parsed_days = self._parse_days(days)
        record = self._guild_record(ctx.guild.id)
        announcements = record.get("announcements", [])
        for entry in announcements:
            if entry.get("id") == item_id:
                entry["days"] = parsed_days
                self._save_data()
                await ctx.send(
                    f"Updated announcement #{item_id} days to {self._format_days(parsed_days)}"
                )
                return
        await ctx.send(f"Announcement #{item_id} not found")

# i hate working with time, someone end me

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Announcements(bot))
