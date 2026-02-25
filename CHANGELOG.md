# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- **YouTube Data API Integration**:
    - Backend: New `/get-videos` endpoint using `httpx` to fetch relevant tutorials.
    - Frontend: "Recommended Videos" section in the lightbox with skeleton loading state.
    - Configuration: Added `YOUTUBE_API_KEY` support in `.env`.
- **Search Context Refinement**:
    - Video search now combines the User's Main Topic (e.g., "Python") with the Day's Topic (e.g., "Basics") for highly relevant results.

### Changed
- **Schedule Granularity Logic**:
    - Refined the logic for generating schedule blocks based on duration:
        - **1-30 days**: Daily breakdown.
        - **30-60 days**: 2-day blocks.
        - **60-180 days**: 5-day blocks.
        - **180-365 days**: 10-day blocks.
        - **>365 days**: Monthly breakdown.
- **Dependencies**: Added `httpx` to `requirements.txt`.

### Fixed
- **Video Result Limit**: Strictly enforced a maximum of 5 video results per request in the backend to prevent UI clutter.
