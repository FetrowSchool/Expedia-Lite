# Part 1 early mockup: Live Hotel Search and Map

This is an annotated planning mockup, not implemented UI. It extends the existing Expedia Lite visual language while keeping live Geoapify hotels separate from sample SQLite hotel stays.

## Results-state layout

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│ [E] Expedia Lite               Search stays   Bookings   Account      Menu │
├─────────────────────────────────────────────────────────────────────────────┤
│ LIVE HOTEL SEARCH                                                        │
│ Find hotels within 5 km of a five-digit U.S. ZIP code.                   │
│                                                                           │
│ ZIP Code                                                                 │
│ ┌──────────────────────────────┐  ┌──────────────┐                        │
│ │ 16802                        │  │ Search       │                        │
│ └──────────────────────────────┘  └──────────────┘                        │
│                                                                           │
│ Location: State College, PA                                               │
│ ZIP 16802 · Latitude 40.8032 · Longitude -77.8614                        │
│                                                                           │
│ 12 hotels found within 5 km                                               │
│ ┌───────────────────────────────┐  ┌────────────────────────────────────┐ │
│ │ Hotel results                 │  │ Leaflet map                       │ │
│ │                               │  │                                    │ │
│ │ ┌───────────────────────────┐ │  │       ○  marker                    │ │
│ │ │ Hotel name               │ │  │              ★ selected marker    │ │
│ │ │ Address when available   │ │  │    ○                               │ │
│ │ │ Distance when available  │ │  │                       ○            │ │
│ │ └───────────────────────────┘ │  │                                    │ │
│ │ ┌───────────────────────────┐ │  │  [ + ]                             │ │
│ │ │ SELECTED HOTEL           │◀├──┼──▶ highlighted marker + popup       │ │
│ │ │ Address when available   │ │  │  [ − ]        map attribution      │ │
│ │ └───────────────────────────┘ │  └────────────────────────────────────┘ │
│ └───────────────────────────────┘                                        │
│                                                                           │
│ Prices, ratings, availability, and booking details are not provided.      │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Selection behavior

- Each hotel card is a real button or contains a clearly labeled Select control.
- Selecting a list item sets `selectedHotelId`, applies a visible selected style, pans to and raises/restyles the corresponding marker, and opens a plain-text popup.
- Selecting a marker sets the same `selectedHotelId`, applies the same list highlight, and scrolls the matching list card into view.
- Only one hotel is selected at a time. Starting a new search clears the selection.
- List and marker keys use a stable provider ID; array position is not treated as identity.

## Required UI states

### Initial

```text
ZIP Code [_____]
[Search]

Enter a five-digit U.S. ZIP code to find hotels within 5 km.
[Map placeholder: Search to view hotel locations]
```

No stale location, hotels, markers, or error is visible.

### Loading

```text
ZIP Code [16802]  [Searching… disabled]
Loading location and nearby hotels…
[Skeleton list]                 [Map placeholder / busy state]
```

The submitted ZIP remains visible. Previous results and selection are cleared. The results region uses `aria-live`/status feedback.

### Results

Use the two-column list/map layout above. On narrow screens, stack the location summary, list, and map. Fit the map to all valid hotel markers. Show only fields supplied by the backend.

### Invalid ZIP input

```text
ZIP Code [12A]
Error: Enter a ZIP code using exactly 5 numeric digits.
```

Focus remains associated with the ZIP field. No provider request is sent.

### ZIP could not be resolved

```text
ZIP Code [99999]
No location could be resolved for ZIP 99999. Check the ZIP and try again.
```

No hotel list or map markers are shown.

### No hotels within 5 km

```text
Location: <provider-backed locality/state when available>
No hotels were found within 5 km of ZIP 16802.
[Map centered on the resolved ZIP point with no hotel markers]
```

Do not imply that hotels do not exist; this means the provider returned no matching hotel POIs for this request.

### Request/API failure

```text
We could not load hotel locations right now. Please try again.
[Try again]
```

The message must not include an API key, full provider URL, raw exception, or provider response body. Missing backend configuration may use a separate safe message for local setup.

## Field rules

| Display field | Rule |
|---|---|
| ZIP code | Exact submitted/resolved five-digit string; preserve leading zero |
| City/locality | Show only when returned |
| State | Show only when returned |
| Latitude/longitude | Show validated values, rounded only for display |
| Hotel name | Show only provider data; otherwise state “Name unavailable” |
| Address | Show only when returned |
| Distance | Show only when returned or correctly calculated and labeled |
| Price/rating/availability/booking | Do not display unless a future authoritative source provides it |

**Never invent missing hotel data.** The early mockup intentionally contains no price, star rating, room availability, fake booking action, or sample SQLite value for a live hotel.
