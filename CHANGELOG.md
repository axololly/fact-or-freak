# Changelog

## v1.0.0 - The Start

> Submitted on 18/12/2024

- First working version
- Allows the user to play _Truth or Dare_ (soon to be renamed _Fact or Freak_) in a turn-based game
- Features a lives system where, after 3 lives are gone, a player is removed from the game
- Features an ending screen where the leaderboard of players is displayed
- The owner (yes, me) gets a custom _Developer_ badge whenever they join any lobbies
- Features a lobby system where multiple users can create and host their own games


## v1.0.1 - Statistics

> Submitted on 21/12/2024

- Organised classes and utilities into separate files
- Added the first `/statistics` menu - incomplete
- Added a `statistics` table that tracks various aspects of the game
- Added new art for the hearts in the game


## v1.0.2 - Bug fixes

> Submitted on 15/1/2025

- Fixed the Token Failed Error
    - This occured because Discord deletes interactions after 15 minutes has passed.

- Added a `?source` command to get where the source code of different commands is stored.


## v2.0.0 - Rebrand

> Submitted on 18/1/2025

- Merged this bot with my Personal Assistant bot, adding commands like `/docs` to it.

- Updated the profile picture to one of my old bots (more info in commit message)

## v2.0.1 - Custom Prefixes

> Submitted on 19/1/2025

- Custom prefixes are now in the bot (more info at `?guide prefix`)

- Custom handwritten guides like the PyDis tags
    - These use the same `frontmatter` package and layout, which was a neat touch.

***

### 📅 v2.1.0 is soon to come

1. New game - One Sentence Each

2. Refactored codebase (again) to something more usable and readable

3. New fully-fledged out help command (first of its kind)