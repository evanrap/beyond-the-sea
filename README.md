# Beyond the Sea

![Status: Alpha](https://img.shields.io/badge/status-alpha-orange)
![Built with Claude Code](https://img.shields.io/badge/built%20with-Claude%20Code-blueviolet)

**Face the ocean. Discover what's on the other side.**

Beyond the Sea is a mobile web app that uses your phone's GPS and compass to find the lands, cities, and stories waiting across the water. Point your phone toward the horizon and it traces a line across the ocean to tell you what you're facing.

**[Try it live](https://evanrap.github.io/beyond-the-sea/)**

## How it works

1. Stand near a coastline and tap **Begin**
2. Point your phone toward the water
3. The app casts a ray from your location across the ocean using a high-resolution land/water bitmap
4. When it hits land, it looks up the nearest place via GeoNames and pulls in a Wikipedia summary and photo

## Tech stack

- Single-file HTML/CSS/JS app (no build tools, no frameworks)
- Custom 0.1° resolution land/water bitmap (1800 x 3600 grid, ~116KB)
- Leaflet for the route map
- GeoNames API for place and island identification
- Wikipedia API for summaries and images
- Device Orientation API for compass heading
- Geolocation API for positioning

## Status

This project is in active development. Features may change, break, or behave unexpectedly. Contributions and feedback are welcome.

## Built with Claude Code

This project was built collaboratively with [Claude Code](https://claude.ai/claude-code), Anthropic's AI coding agent. From the bitmap generator to the compass smoothing algorithm to the UI design, the development process was a conversation.
