# Part 1 research: Live Hotel Search and Map

## Current project baseline

Expedia Lite currently has a Vue 3 view, FastAPI backend, SQLite-backed city stay search, and a backend-only Geoapify ZIP lookup. The ZIP route accepts a five-digit string and returns a `ZipLocation`. The project does not yet call Geoapify Places or use Leaflet. Part 1 should extend the existing Vue → FastAPI → controller pattern without putting the Geoapify key in Vue or replacing unrelated search and booking behavior.

## Recommended interaction pattern

1. The user enters a ZIP code in a text field so leading zeros are preserved.
2. Vue validates exactly five ASCII digits, clears stale results, disables Search, and shows a loading state.
3. FastAPI independently validates the ZIP and asks the geocoding controller to resolve it.
4. The backend accepts only an exact U.S. postcode match with finite coordinates.
5. The backend passes those coordinates to a Places controller and requests hotels within 5 km.
6. One backend response returns the resolved location and a normalized hotel list. Vue renders the list and map from the same array.
7. A single reactive `selectedHotelId` synchronizes list selection and marker selection.
8. Empty, invalid, unresolved, no-results, and provider-failure states are mutually exclusive and shown in the results region.

Submitting the form with Enter should behave like clicking Search. A new search should clear the old selection, list, map markers, and errors before the request begins. The last submitted ZIP, rather than partially typed input, should label the results.

## Geoapify Geocoding API

Geoapify forward geocoding supports postcode results and recommends a country filter because postcodes are only unique within a country. For this application, the backend request should use:

```text
GET https://api.geoapify.com/v1/geocode/search
  ?postcode=02108
  &type=postcode
  &filter=countrycode:us
  &format=json
  &apiKey=<backend-only key>
```

The ZIP must remain a string. Both Vue and FastAPI should require `^[0-9]{5}$`; converting to an integer would corrupt a ZIP such as `02108`. The controller should accept a result only when its returned `postcode` equals the submitted ZIP, its `country_code` is `us` case-insensitively, and its latitude and longitude are finite and in range. City/locality and state may be absent, so the response model should keep those fields optional.

Adopted decision: reuse the existing `backend/config.py`, `backend/zip_controller.py`, and `ZipLocation` model. Keep the key and full provider URL out of responses and error text. Distinguish invalid input, unresolved postcode, missing configuration, and provider failure.

Official documentation: [Geoapify Geocoding API](https://apidocs.geoapify.com/docs/geocoding/).

## Geoapify Places API

The Places API searches categorized points of interest and supports a circle filter measured in meters. After geocoding, the backend should use the hotel category, a hard 5 km boundary, and proximity ordering:

```text
GET https://api.geoapify.com/v2/places
  ?categories=accommodation.hotel
  &filter=circle:<longitude>,<latitude>,5000
  &bias=proximity:<longitude>,<latitude>
  &limit=<documented project limit>
  &apiKey=<backend-only key>
```

`filter` enforces the 5 km maximum; `bias` only controls ordering and must not replace the filter. Longitude comes before latitude in Geoapify spatial parameters. The controller should normalize only supported fields such as a stable provider/place ID, name when present, formatted address when present, coordinates, and provider-reported distance when present. Deduplicate by a stable ID when available and reject results without valid coordinates.

Adopted decision: add a separate Places/hotel-search controller later. FastAPI will combine the resolved location and hotel results into an explicit response model. Vue will never call Geoapify directly.

Official documentation: [Geoapify Places API](https://apidocs.geoapify.com/docs/places/) and [nearest place by category](https://apidocs.geoapify.com/how-to/place-discovery/nearest-place-by-category/).

## Leaflet

Leaflet provides maps, tile layers, markers, popups, events, `fitBounds`, and marker z-index controls. The planned Vue map component should:

- initialize one Leaflet map after its container is mounted;
- use an attributed tile layer and retain the provider attribution;
- create one marker per hotel with valid coordinates;
- keep a marker registry keyed by the same stable hotel ID used by the list;
- call `fitBounds` after results change, with a reasonable maximum zoom for one marker;
- remove obsolete markers and event handlers before rendering a new result set;
- render external text safely rather than injecting unsanitized provider HTML.

List click: set `selectedHotelId`, visually select the row/card, raise or restyle its marker, pan it into view, and open its popup. Marker click: set the same ID, highlight the corresponding list item, and scroll/focus that item without stealing keyboard access unexpectedly. Keyboard-operable list controls should provide the same behavior as mouse clicks.

Official documentation: [Leaflet quick start](https://leafletjs.com/examples/quick-start/), [Leaflet API reference](https://leafletjs.com/reference), and [Leaflet tutorials](https://leafletjs.com/examples/).

## FastAPI

FastAPI treats non-path function arguments as query parameters. String validation should preserve the ZIP as text. Pydantic response models should constrain the public location/hotel shape, and `HTTPException` should translate known controller errors into concise JSON without leaking credentials or raw provider exceptions.

Adopted decision: use one thin hotel-search route that validates the ZIP, calls geocoding and Places controllers, and returns a typed combined response. Keep HTTP concerns in `backend/main.py` and external-provider logic in controllers.

Official documentation: [query parameters](https://fastapi.tiangolo.com/tutorial/query-params/), [query string validation](https://fastapi.tiangolo.com/tutorial/query-params-str-validations/), [response models](https://fastapi.tiangolo.com/tutorial/response-model/), and [error handling](https://fastapi.tiangolo.com/tutorial/handling-errors/).

## Vue

Vue Composition API `ref()` state fits the existing application. Planned state includes `zipInput`, `submittedZip`, `location`, `hotels`, `selectedHotelId`, `isLoading`, and `errorKind`. `v-if`/`v-else-if` can make the UI states exclusive, while `v-for` renders the normalized list. The map should receive hotel and selected-ID props and emit a selection event rather than owning a second selection state.

Adopted decision: retain the existing API module and Vite `/api` proxy convention. Keep request state in the parent search view and map lifecycle code in a focused component when implementation begins.

Official documentation: [Vue reactivity fundamentals](https://vuejs.org/guide/essentials/reactivity-fundamentals), [conditional rendering](https://vuejs.org/guide/essentials/conditional), and [watchers](https://vuejs.org/guide/essentials/watchers).

## Weaknesses and limitations

- Geoapify Places is a point-of-interest dataset, not live hotel inventory.
- A hotel may have no name, incomplete address data, duplicated/stale data, or missing optional properties.
- Results may be limited or paginated and should not be described as every hotel in the area.
- The postcode coordinate is a representative point, not the user's exact location or the full postcode boundary.
- A 5 km circle from that point can include hotels outside the postal boundary and omit hotels inside distant parts of the boundary.
- Provider distance or ordering may be absent; distance should only be displayed when returned or correctly calculated and labeled.
- Leaflet supplies map interaction, not tile data. The selected tile provider's usage policy and attribution must be honored.
- Provider quotas, latency, rate limits, network errors, and incomplete coverage require clear loading, failure, and retry behavior.
- Hotel results may not contain prices, ratings, room availability, booking links, photos, amenities, or booking information.

**The application must never invent missing hotel data.** If a field is absent, omit it or label it clearly as unavailable. Do not substitute values from the existing sample `Hotel` model, because those rows and prices are unrelated to live Geoapify Places results.

## Decisions adopted for Part 1

- Search by an exact five-digit U.S. ZIP stored as a string.
- Keep all Geoapify requests and the API key in FastAPI controllers.
- Resolve the ZIP first; search `accommodation.hotel` within a strict 5,000-meter circle second.
- Return one normalized, typed response containing optional location fields and hotels with valid coordinates.
- Use one stable selected-hotel ID shared by list and map.
- Show only provider-backed fields and explicitly avoid fabricated price, rating, availability, or booking data.
- Preserve existing functionality and keep live search results separate from SQLite sample hotels.
- Cover success, invalid ZIP, unresolved ZIP, empty hotels, configuration failure, provider failure, and malformed provider data with mocked backend tests.
