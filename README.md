# lotus-bot

Custom Discord bot with cog-based announcement scheduling.

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
