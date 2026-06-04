# Hex Tutorial Video Script (v2)
## "From Question to App in 30 Minutes: AI-First Analytics with USGS Earthquake Data"
**Total runtime target:** 28–32 minutes
**Dataset:** USGS Earthquake data in Supabase Postgres (synced hourly via GitHub Actions)
**Data connection in Hex:** "Supabase - USGS Earthquakes" (Powered by Data org)
**Audience:** Data analysts, BI professionals, data-curious professionals
---
## PRE-RECORDING CHECKLIST
- [ ] Hex account logged in, clean workspace visible
- [ ] "Supabase - USGS Earthquakes" data connection verified (run a quick test query)
- [ ] **Cell 0** added as the first cell: `!uv pip install pydeck scikit-learn geopy` — run it during setup so the kernel is warm, then collapse/hide it (this workspace uses uv-based package management; there is no "add package" button)
- [ ] No existing earthquake project visible (archive your prototype before recording)
- [ ] Browser zoomed to ~125% for screen readability
- [ ] Notifications silenced
- [ ] Have this script open on a second monitor or printed
---
## ACT 1: "CONNECT AND EXPLORE" — THE PROJECT
**Duration:** ~10 minutes
**Goal:** Show the enterprise workflow — connect to a real database, query it with SQL, and produce a stunning map in under 5 minutes. Then let the AI agent take over.
---
### Step 1: Cold Open — Create a Project and Connect to Data (0:00–3:00)
**[TALKING POINT]**
> "I've got a Postgres database in Supabase that's being refreshed every hour with live earthquake data from the US Geological Survey. Magnitude 2.5 and above, worldwide. Let me show you how fast we can go from a database connection to real insights."
**[ACTION]** Create a new Hex project. Name it "Earthquake Explorer".
**[SETUP — do this before recording, then collapse the cell]** Make the very first cell a package install. This workspace installs Python packages via uv (no "add package" button), so this is how `pydeck` and `scikit-learn` get in:
```python
!uv pip install pydeck scikit-learn geopy
```
Run it once during setup so the kernel is warm and uv has cached the downloads. Keep it as the **top cell** (Run All executes it first, before any imports) and collapse it so it stays out of the shot. On a cold kernel it re-runs in seconds thanks to the uv cache. (You can leave `geopy` out here if you'd rather install it live in Step 4 as a teaching beat — see note there.)
**[ACTION]** Add a **SQL cell**. In the connection dropdown, select **"Supabase - USGS Earthquakes"**.
**[TALKING POINT]**
> "This is how most enterprise teams work — you've got a data warehouse or a Postgres database, and you need to connect to it and start exploring. Hex makes this dead simple. I'll select my Supabase connection, and now I can write SQL directly against my earthquake table."
**[ACTION]** Type the SQL query. Set the output dataframe name to `earthquakes`:
```sql
select event_id, title, place, magnitude, depth_km,
       latitude, longitude, event_time, alert
from public.earthquakes
where latitude is not null
  and longitude is not null
order by magnitude asc nulls first   -- draw the big ones on top
```
**[ACTION]** Run the cell.
**[TALKING POINT]**
> "So we've got around [X thousand] earthquakes, each one with a magnitude, depth, location, and timestamp. This data is refreshed hourly — it's not a snapshot from last year, it's as current as it gets. But a table of numbers doesn't tell you much. Let's put this on a map."
---
### Step 2: The Map — First Wow Moment (3:00–6:00)
**[ACTION]** Add a **Python cell** below the SQL cell. Type (or paste) the pydeck code:
```python
import pydeck as pdk
import pandas as pd
df = earthquakes.copy()
df["magnitude"] = pd.to_numeric(df["magnitude"], errors="coerce").fillna(0)
df["radius"] = (10 ** (0.35 * df["magnitude"])) * 1500
def mag_color(m):
    if m < 3: return [255, 237, 160, 180]    # pale yellow
    if m < 4: return [254, 178,  76, 200]    # orange
    if m < 5: return [253, 141,  60, 215]    # deep orange
    if m < 6: return [240,  59,  32, 225]    # red
    return     [189,   0, 110, 245]           # magenta
df["color"] = df["magnitude"].apply(mag_color)
df["when"]  = pd.to_datetime(df["event_time"]).dt.strftime("%Y-%m-%d %H:%M UTC")
layer = pdk.Layer(
    "ScatterplotLayer", data=df,
    get_position=["longitude", "latitude"],
    get_radius="radius", get_fill_color="color",
    radius_min_pixels=1.5, radius_max_pixels=60, opacity=0.8,
    stroked=True, get_line_color=[255, 255, 255, 30],
    line_width_min_pixels=0.3, pickable=True,
)
view_state = pdk.ViewState(latitude=20, longitude=0, zoom=1.1, pitch=0)
tooltip = {
    "html": "<b>{title}</b><br/>Mag <b>{magnitude}</b> · {depth_km} km deep"
            "<br/>{place}<br/>{when}",
    "style": {"backgroundColor": "rgba(20,20,20,0.9)", "color": "white",
              "fontSize": "12px"},
}
deck = pdk.Deck(
    layers=[layer], initial_view_state=view_state,
    map_provider="carto", map_style=pdk.map_styles.DARK, tooltip=tooltip,
)
deck
```
**[ACTION]** Run the cell. Give the audience a moment to take in the map.
**[TALKING POINT]**
> "Now we're looking at every significant earthquake on Earth over the past year and a half — on a dark basemap, sized and colored by magnitude. You can see the Ring of Fire wrapping around the Pacific. Those big red and magenta dots? Those are the major events. Hover over any one and you get the details."
**[ACTION]** Hover over a few dots — show the tooltip with magnitude, depth, location, and date.
> "Two cells. One SQL query, one Python visualization. Database to map in about 90 seconds. But I didn't come here to write code — I came here to show you what the AI can do. Let's hand the wheel over to the Notebook Agent."
**[TALKING POINT — point out Typeahead if you typed any of the Python manually]**
> "Quick aside — as I was typing that, notice Hex was offering code completions? That's Typeahead — it's watching the context of your notebook and suggesting what comes next."
---
### Step 3: Notebook Agent Builds Your Analysis (6:00–10:00)
**[TALKING POINT]**
> "Now here's where it gets fun. Instead of writing more code myself, I'm going to describe what I want in plain English and let the Notebook Agent build it for me. Watch."
**[ACTION]** Open the Notebook Agent (CMD+K or the agent icon). Type:
**[PROMPT FOR NOTEBOOK AGENT]**
```
Using the `earthquakes` dataframe, create 3 visualizations with markdown headers before each one:
1. A histogram of earthquake magnitudes — what's the distribution?
2. Group the earthquakes into 6 geographic clusters using K-means on their latitude/longitude, then plot every quake on a map (or a lon-vs-lat scatter) colored by cluster — which tectonic regions emerge? Convert lat/lon to 3D unit-sphere coordinates before clustering so the dateline doesn't split the Pacific.
3. A time series showing daily earthquake counts — are quakes becoming more or less frequent?
```
**[WAIT — let the agent create multiple cells]**
**[TALKING POINT — while agent works]**
> "The Notebook Agent isn't just generating a single code snippet. It's building multiple cells — the charts, the markdown narrative, the data transformations — and it understands the flow of the notebook. It knows that `earthquakes` is a dataframe from my SQL cell above."
**[AFTER CELLS ARE CREATED, scroll through them]**
> "In about 30 seconds, I've got a complete exploratory analysis — distribution, geographic clusters, time trends — with narrative text explaining each one. Look at that clustering map: the agent found the Ring of Fire, the Andes, the Mediterranean belt — the planet's tectonic boundaries — without me labeling a single point. Now let's build something people can actually use."
---
## ACT 2: "BUILD SOMETHING REAL" — THE PROXIMITY FINDER
**Duration:** ~10 minutes
**Goal:** Use the Notebook Agent to build an interactive earthquake proximity finder with geocoding, distance calculations, and a map.
---
### Step 4: Install the Geocoding Library (10:00–11:00)
**[TALKING POINT]**
> "Here's what I want to build: an app where anyone can type in their city and see the closest recent earthquakes on a map. To do that, I need to convert a city name into coordinates — that's called geocoding. Let me install a library for that."
**[ACTION]** Add a Python cell (this is the live "watch me add a capability" beat — skip it if you already installed geopy in the Cell 0 setup):
```python
!uv pip install geopy
```
**[ACTION]** Run the cell.
> "Now I've got `geopy` available. I could write the proximity logic myself, but why would I when I can ask the agent?"
---
### Step 5: Notebook Agent Builds the Proximity Finder (11:00–15:00)
**[ACTION]** Open the Notebook Agent. Type:
**[PROMPT FOR NOTEBOOK AGENT]**
```
Build an earthquake proximity finder. Create these cells:
1. Three input parameters: a text input called `city_name` (default "Seattle, WA"), a numeric input called `num_results` (default 25), and a date range input for start and end dates.
2. A Python cell that uses geopy (already installed) to geocode the city name to lat/long, then calculates the geodesic distance from that city to every earthquake in the `earthquakes` dataframe. Return a dataframe called `nearest_quakes` sorted by distance (closest first), limited to the top X results. Include columns: title, magnitude, depth_km, distance_miles, latitude, longitude, event_time, place.
3. A pydeck map (dark CARTO basemap, no Mapbox token) centered on the user's city, showing a blue marker for the city and circle markers for each nearby earthquake — sized and colored by magnitude.
4. A clean table displaying `nearest_quakes`.
```
**[WAIT — agent builds all cells]**
**[TALKING POINT — while agent works]**
> "I just described what I want in plain English, and the agent is building input parameters, geocoding logic, distance calculations, an interactive map, and a data table. This would normally take an experienced developer 30 to 45 minutes. Let's see how it does."
**[KNOWN-GOOD PROXIMITY CELL — from the "Earthquake Proximity Finder" project]**
If the agent's version misbehaves on camera, paste this proven cell (label it "Compute nearest quakes"). It geocodes the city with Nominatim and computes great-circle distance to every quake with a vectorized haversine:
```python
import numpy as np
from geopy.geocoders import Nominatim
from geopy.distance import geodesic

geolocator = Nominatim(user_agent="hex-earthquake-proximity")
location = geolocator.geocode(city_name)
city_lat, city_lon = location.latitude, location.longitude

filtered = earthquakes.copy()
if date_range_start is not None:
    filtered = filtered[filtered["date"] >= pd.Timestamp(date_range_start)]
if date_range_end is not None:
    filtered = filtered[filtered["date"] < pd.Timestamp(date_range_end) + pd.Timedelta(days=1)]

lat1 = np.radians(city_lat)
lon1 = np.radians(city_lon)
lat2 = np.radians(filtered["latitude"].to_numpy())
lon2 = np.radians(filtered["longitude"].to_numpy())
dlat = lat2 - lat1
dlon = lon2 - lon1
a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
filtered = filtered.assign(distance_miles=2 * 3958.7613 * np.arcsin(np.sqrt(a)))

nearest_quakes = (
    filtered.sort_values("distance_miles")
    .head(int(num_results))
    [["title", "magnitude", "depth_km", "distance_miles", "latitude", "longitude", "date", "place"]]
    .reset_index(drop=True)
)
nearest_quakes
```
> **⚠️ Column note:** this cell expects a datetime **`date`** column, but the Step 1 SQL outputs `event_time`. Reconcile one of two ways before running: (a) add `event_time as date` to the SQL `select`, or (b) add one prep line first — `earthquakes["date"] = pd.to_datetime(earthquakes["event_time"])`. Without this, the date-range filter throws a `KeyError: 'date'`.
**[AFTER CELLS ARE CREATED, RUN ALL]**
**[TALKING POINT]**
> "Let me change the city to somewhere fun..."
**[ACTION]** Change the city input to "Tokyo, Japan" and re-run. Then try "Los Angeles, CA".
> "Every time I change the city, the whole notebook reruns — fresh geocoding, new distances, a recentered map. This is already a working application. But right now only I can see it."
---
### Step 6: Quick Fix with Agent (15:00–16:30)
**[TALKING POINT]**
> "Now, real talk — things don't always work perfectly on the first try. Let me show you what happens when something breaks."
**[ACTION]** If a natural error occurred, great — use it. If not, intentionally introduce a small bug (e.g., rename a column reference) and run the cell.
**[ACTION]** Click **"Fix with Agent"** on the error.
**[TALKING POINT]**
> "See that? I didn't have to read the traceback and debug the code myself. The agent read the error, understood the context of the notebook, and fixed it. This is what AI-first really means — it's not just generating code, it's maintaining it."
---
## ACT 3: "SHARE IT WITH THE WORLD" — PUBLISHING, THREADS, AND CHAT
**Duration:** ~12 minutes
**Goal:** Publish the app, then show two AI-powered ways to interact with it: Threads and Chat with App.
---
### Step 7: Build and Publish the App (16:30–20:00)
**[TALKING POINT]**
> "Everything I've built so far lives in a notebook — great for building, but I want to share this with people who don't want to see any code. Let's turn it into a clean, interactive app."
**[ACTION]** Switch to the **App Builder** view (the layout/app tab).
**[TALKING POINT]**
> "In the app view, I drag cells into a layout. Inputs at the top, the map front and center, the data table below."
**[ACTION]** Arrange the layout:
- Top row: city_name input, num_results slider, date range
- Center: the pydeck proximity map (make it large)
- Bottom: the nearest_quakes table
- Optionally: also include the cluster-colored map from Step 3 as a second "global view" tab
**[ALTERNATIVELY — use the Notebook Agent]**
**[PROMPT FOR NOTEBOOK AGENT]**
```
Add the city_name input, num_results input, date range inputs, the earthquake proximity map, and the nearest_quakes table to the published app. Inputs at the top, map prominently in the center, table below.
```
**[TALKING POINT]**
> "I can drag and drop manually, or I can ask the agent to configure the app layout for me."
**[ACTION]** Click **Publish**. Show the clean, shareable URL.
> "And there's the exclamation point: a live, shareable app that answers one irresistibly personal question — *what are the biggest earthquakes near MY city?* Type in any city on Earth and it geocodes it, measures the distance to every recent quake, and drops the closest ones on the map. No code visible, no login required — just type a city and explore."
---
### Step 8: Threads — Conversational Exploration (20:00–24:00)
**[TALKING POINT]**
> "Now I want to show you a completely different way to interact with this same data. Instead of building something, what if you just want to ask a question?"
**[ACTION]** Navigate to **Threads**. Start a new Thread.
**[PROMPT TO TYPE IN THREADS]**
```
What were the 10 largest earthquakes in the past year? Show me the location, magnitude, and depth for each one.
```
**[WAIT]** Let the agent query the Supabase connection, execute SQL, and return a table.
**[TALKING POINT]**
> "No project, no notebook, no code. I just asked a question in plain English and Hex queried my database and gave me the answer. Let's keep going."
**[PROMPT TO TYPE]**
```
Show me that as a bar chart, sorted by magnitude descending.
```
**[WAIT, THEN:]**
**[PROMPT TO TYPE]**
```
Show me the monthly trend of magnitude 5+ earthquakes. Is earthquake frequency increasing, decreasing, or staying flat?
```
**[TALKING POINT — while agent works]**
> "Notice I'm typing my next question while it's still working on the current one. That's prompt queuing — your follow-ups get picked up automatically."
**[AFTER RESULT]**
**[PROMPT TO TYPE]**
```
Group these earthquakes into 6 geographic clusters using K-means on their coordinates, then plot them on a map with each cluster in a different color. Which cluster has the highest average magnitude?
```
**[TALKING POINT]**
> "Watch what just happened — the agent switched from SQL to Python on its own. It decided SQL wasn't the right tool for clustering, so it reached for K-means and built the colored map in Python. It chose the right tool for the job without me telling it to. That's the difference between a chatbot and an agent."
> "(Live riff, if you want it: the Andes / South America cluster usually comes out with the highest average magnitude — around 4.5 — while the Tonga–Fiji subduction zone has the deepest quakes on Earth, over 180 km on average.)"
**[PROMPT TO TYPE]**
```
For each cluster, show the distribution of magnitudes and tell me which region is the most seismically active.
```
**[TALKING POINT]**
> "We just went from 'show me a bar chart' to unsupervised machine learning — colored clusters on a world map and a per-region magnitude breakdown — in a single conversation. No imports, no environment setup — just questions and answers. Now let me show you one more thing."
---
### Step 9: Chat with Your Published App (24:00–27:00)
**[TALKING POINT]**
> "This is the feature that really sets Hex apart. Remember that app we published? Watch this."
**[ACTION]** Navigate back to the published app. Click **"Chat with App"**.
**[PROMPT TO TYPE IN CHAT WITH APP]**
```
Summarize the key findings from this earthquake proximity analysis for Seattle.
```
**[WAIT FOR RESPONSE]**
**[TALKING POINT]**
> "The agent just read my entire app — the data, the map, the parameters, the logic — and generated a narrative summary. It understands the context of what this app does. But it gets better."
**[PROMPT TO TYPE]**
```
Were any of these earthquakes felt by people? Which one caused the most shaking?
```
**[WAIT FOR RESPONSE]**
**[PROMPT TO TYPE]**
```
Compare earthquake activity near Seattle to what it looks like near San Francisco. Which city has had more significant seismic activity in the past year?
```
**[TALKING POINT]**
> "That question went beyond what's displayed on screen. The agent used the app's underlying logic — the database connection, the distance calculation — to go get new data and answer a question I never explicitly built the app to answer. This isn't a static dashboard. It's a living, conversational experience."
---
### Step 10: The Closeout (27:00–29:00)
**[TALKING POINT]**
> "Let me take a step back and recap what we just did in under 30 minutes."
> "We connected to a live Postgres database and wrote a SQL query. Two cells later, we had every significant earthquake on Earth on a dark-map visualization."
> "Then we asked the Notebook Agent to build a complete proximity finder — geocoding, distance math, interactive inputs, a map — all from a plain English description."
> "We published it as an app anyone can use. We explored the same data conversationally in Threads — going from bar charts to machine learning in a single conversation. And then we had a conversation with the published app itself, asking questions that went beyond what we originally built."
> "Database to published, AI-powered application in 30 minutes. That's Hex."
**[ACTION]** Show the published app URL one more time.
> "If you want to try this yourself, Hex has a free tier. The earthquake data I used comes from the US Geological Survey — it's public domain, free, and updated constantly. Everything I showed you, you can recreate."
> "Thanks for watching. If you found this useful, subscribe and let me know in the comments which city's earthquake data surprised you the most."
---
## BACKUP PROMPTS — IF THINGS GO SIDEWAYS
If the SQL cell doesn't connect, verify the connection name "Supabase - USGS Earthquakes" in the dropdown. If the table is empty, check that the GitHub Actions sync has run at least once.
If the pydeck map doesn't render, make sure the Cell 0 `!uv pip install pydeck ...` cell has run (re-run it, then Run All). Also verify the last line of the cell is just `deck` with no print() wrapping it.
If the K-means clustering errors with `ModuleNotFoundError: sklearn` (or pydeck/geopy aren't found), it means the Cell 0 install didn't run before the import. Re-run the top `!uv pip install pydeck scikit-learn geopy` cell, then Run All — this workspace has no "add package" button; uv-in-the-first-cell is the only install path. The Threads agent will fall back to a pure-numpy K-means automatically, but a notebook cell won't — so make sure that first cell has executed. If the cluster map looks wrong (the Pacific gets split down the dateline), tell the agent: "Convert lat/lon to 3D unit-sphere coordinates before clustering so the antimeridian doesn't split clusters."
If Threads gives a weak answer on the first question, try:
```
Query the earthquakes table for the 10 largest earthquakes by magnitude. Show title, magnitude, depth_km, place, and event_time.
```
If the clustering result looks uninteresting or you need a quick filler, pivot to:
```
Show me earthquake frequency by hour of the day — are earthquakes more common at certain times?
```
If geocoding fails on a city name, it's usually the Nominatim service (geopy) being rate-limited or blocked by network egress — retry once, then fall back to hardcoding these coordinates:
- Seattle: 47.6062, -122.3321
- Tokyo: 35.6762, 139.6503
- Los Angeles: 34.0522, -118.2437
- San Francisco: 37.7749, -122.4194
If the Notebook Agent creates broken code, don't panic — use it as the "Fix with Agent" demo moment. This is honest and relatable.
---
## FEATURE CHECKLIST — MAKE SURE YOU DEMO THESE
| Feature | Where in Script | Hex Feature Name |
|---|---|---|
| Database connection + SQL | Step 1 | **SQL Cells + Data Connections** |
| Python visualization (pydeck) | Step 2 | **Python Cells** |
| AI code completion | Step 2 | **Typeahead** |
| Multi-cell generation | Steps 3 & 5 | **Notebook Agent** |
| Interactive inputs | Step 5 | **Input Parameters** |
| Error diagnosis | Step 6 | **Fix with Agent** |
| Agent builds app layout | Step 7 | **Agent configures published apps** |
| Dashboard publishing | Step 7 | **Published Apps** |
| Conversational data Q&A | Step 8 | **Threads** |
| Prompt queuing | Step 8 | **Queue Prompts in Threads** |
| Python in Threads | Step 8 | **Python in Threads** |
| Talk to your dashboard | Step 9 | **Chat with App** |
| Agent goes beyond the app | Step 9 | **Chat with App (expanded context)** |
---
## PRODUCTION NOTES
**Pacing:** Act 1 should feel fast and visual — database to map in under 3 minutes. Act 2 is where you slow down and teach. Act 3 builds to the Threads and Chat with App wow moments. Don't cut or speed up the agent's work — the audience watching it think and build in real time IS the content.
**Tone:** Channel your Fred Rogers energy. You're not selling — you're showing something genuinely cool and letting the audience decide. "Watch this" is more powerful than "this is amazing."
**The pydeck map is your thumbnail.** When you export/screenshot the video, use the dark-basemap global earthquake map — or, even better, the K-means cluster-colored version where each tectonic region pops in its own color. Both are visually striking and immediately communicate what the video is about.
**If you run long:** Cut Step 6 (Fix with Agent) — it's nice but not essential. You can also trim the Threads section (Step 8) to 2–3 prompts instead of 5.
**If you run short:** Add an Explore cell demo between Steps 3 and 4 — show the no-code drag-and-drop charting interface as the "middle ground" between SQL/Python and AI.
**SQL cell output name:** Double-check that the SQL cell's output DataFrame is named `earthquakes` (not the default `dataframe_1` or similar). Both the pydeck cell and the Notebook Agent prompts reference it by that name.
