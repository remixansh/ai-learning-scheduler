# Changelog

All notable changes to this project will be documented in this file.

## [2.0.0] - 2026-02-26

### Added

- **Progress Tracking**:
    - Desktop pill-shaped navigation with **Schedule** and **Progress** tabs.
    - Mobile fixed bottom navigation bar with the same tabs.
    - "Mark as my routine" button appears after schedule generation.
    - Routines saved to `localStorage` with expandable accordion cards in the Progress tab.
    - SVG circular progress rings showing routine completion percentage.
    - Per-task and per-exercise custom checkboxes with optimistic UI updates.
    - Delete routines with toast-based confirmation feedback.
    - Empty state for the Progress tab.

- **Pomodoro Timer**:
    - **Floating Action Button (FAB)** in the center of mobile bottom navigation (raised, separated).
    - **Desktop timer button** fixed in the top-right corner.
    - **Fullscreen overlay** with fluid expanding-circle animation in coral accent color.
    - **Tactile time picker**: `-` and `+` buttons adjust duration in 5-minute intervals (5–120 min).
    - **Countdown state**: SVG circular progress ring with remaining time and "Focusing" label.
    - **Pause/Resume** toggle during countdown.
    - **Timeout state**: Radial red gradient background with "Time's Up!" message and Done button.

- **To-Do List**:
    - Standalone To-Do mode, fully separate from the AI Scheduler.
    - **Mode toggle**: Desktop (top-left corner) / Mobile (below header) pill button to switch views.
    - Toggle state persisted in `localStorage` — survives page refresh.
    - Button label dynamically switches between "To Do" and "AI Scheduler".
    - **Vanish effect**: Scale + blur + fade transition when switching views.
    - **Add Task**: Coral `+` FAB (bottom-right), opens slide-up input overlay.
    - Click-outside-to-dismiss for the input overlay.
    - Enter key support for quick task entry.
    - **Circular checkboxes** with coral fill animation on check.
    - Checked tasks get strikethrough and move to a **"Completed"** section after 5 seconds.
    - **Delete** button (✕) per task, appears on hover (always visible on mobile).
    - Tasks persisted in `localStorage`.
    - Empty state message when no tasks exist.

- **Video Links in Progress Tab**:
    - Each day in a saved routine has a small coral "Videos" button.
    - Fetches YouTube recommendations on-demand via `/get-videos`.
    - Displays results as **title-only text links** — no thumbnails, minimalist design.
    - Toggle on/off by clicking the Videos button again.

### Changed

- **UI/UX Overhaul**:
    - Replaced all emoji with SVG icons throughout the interface.
    - Replaced native `confirm()` and `alert()` dialogs with custom toast notifications.
    - Maintained minimalist design aesthetic with warm coral accents.
    - Smooth animations and tactile feedback for all interactive elements.

---

## [1.0.0] - Unreleased

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
