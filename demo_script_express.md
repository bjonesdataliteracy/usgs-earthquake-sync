# Hex Tutorial Video Script — EXPRESS CUT (~15 minutes)
## "USGS Earthquakes in Hex: Database → AI App in 15 Minutes"
**Target runtime:** 14–16 minutes (about half the full script — see `demo_script.md` for the long version)
**Dataset:** USGS Earthquake data in Supabase Postgres (synced hourly via GitHub Actions)
**Data connection in Hex:** "Supabase - USGS Earthquakes"
**Audience:** Data analysts, BI professionals, data-curious professionals

> **How this cut stays short:** the long script makes ~15 separate agent calls; this one makes ~5 by **batching prompts**. Each agent run has wait time, so fewer, combined prompts is the single biggest lever on runtime. Talking points are trimmed to one or two lines. Every feature from the full script's checklist is still demoed.

---
## PRE-RECORDING CHECKLIST
- [ ] "Supabase - USGS Earthquakes" connection verified
- [ ] **Cell 0** = `!uv pip install pydeck scikit-learn geopy` — run during setup, then collapse it (uv-based packages; no "add package" button)
- [ ] **Chat with App** confirmed visible on the published app (interlocking-circles icon, lower-right; needs Explorer role + "Can Explore")
- [ ] Notifications off, browser at ~125% zoom, no old earthquake project visible

---
## 1. Connect + Map — the cold open (0:00–3:00)
*Features: SQL Cells + Data Connections · Python Cells (pydeck) · Typeahead*

**[TALKING POINT]**
> "I've got live USGS earthquake data — magnitude 2.5+, worldwide — landing in a Supabase Postgres database every hour. Let's go from that database to a map in 90 seconds."

**[ACTION]** New project "Earthquake Explorer". Add a **SQL cell** on the **"Supabase - USGS Earthquakes"** connection. Name its output `earthquakes`:
```sql
select event_id, title, place, magnitude, depth_km,
       latitude, longitude, event_time, alert
from public.earthquakes
where latitude is not null and longitude is not null
  and event_time >= now() - interval '90 days'
order by magnitude desc nulls first
```

**[ACTION]** Add a **Python cell** for the map (mention in one line that **Typeahead** is autocompleting as you type):
```python
import pydeck as pdk
import pandas as pd
df = earthquakes.copy().sort_values("magnitude")   # big dots drawn on top
df["magnitude"] = pd.to_numeric(df["magnitude"], errors="coerce").fillna(0)
df["radius"] = (10 ** (0.35 * df["magnitude"])) * 1500
def mag_color(m):
    if m < 3: return [255, 237, 160, 180]
    if m < 4: return [254, 178,  76, 200]
    if m < 5: return [253, 141,  60, 215]
    if m < 6: return [240,  59,  32, 225]
    return     [189,   0, 110, 245]
df["color"] = df["magnitude"].apply(mag_color)
df["when"]  = pd.to_datetime(df["event_time"]).dt.strftime("%Y-%m-%d %H:%M UTC")
layer = pdk.Layer(
    "ScatterplotLayer", data=df, get_position=["longitude", "latitude"],
    get_radius="radius", get_fill_color="color",
    radius_min_pixels=1.5, radius_max_pixels=60, opacity=0.8,
    stroked=True, get_line_color=[255, 255, 255, 30], line_width_min_pixels=0.3,
    pickable=True,
)
view_state = pdk.ViewState(latitude=20, longitude=0, zoom=1.1, pitch=0)
tooltip = {"html": "<b>{title}</b><br/>Mag <b>{magnitude}</b> · {depth_km} km deep<br/>{place}<br/>{when}",
           "style": {"backgroundColor": "rgba(20,20,20,0.9)", "color": "white", "fontSize": "12px"}}
deck = pdk.Deck(layers=[layer], initial_view_state=view_state,
                map_provider="carto", map_style=pdk.map_styles.DARK, tooltip=tooltip)
deck
```
**[ACTION]** Run it, hover a couple of dots.
> "The Ring of Fire, on a dark map, sized and colored by magnitude — two cells. Now let's let the AI take over."

---
## 2. Notebook Agent — analysis + clustering (3:00–7:00)
*Features: Notebook Agent (multi-cell generation)*

**[TALKING POINT]**
> "Instead of writing more code, I'll just describe what I want."

**[ACTION]** Open the Notebook Agent (CMD+K). Paste these **two** prompts (one at a time):

**Prompt A — quick EDA (one call, two charts):**
```
Using the `earthquakes` dataframe, add two cells, each with a markdown header: (1) a histogram of magnitudes, and (2) a time series of daily earthquake counts.
```

**Prompt B — clustering, the whole sequence in one call:**
```
Group the earthquakes into 6 geographic clusters with K-means on their latitude/longitude (convert lat/lon to 3D unit-sphere coordinates first so the dateline doesn't split the Pacific). Then: plot every quake on a pydeck map colored by cluster, give each cluster a short geographic name based on its place names (e.g. "Andes — South America"), and add a bar chart of counts per cluster using the same colors.
```
**[WAIT — let each finish]**
> "Thirty seconds, and it found the planet's tectonic boundaries — clustered, named, mapped, and charted — without me labeling a thing."

---
## 3. Build + fix the proximity app (7:00–10:30)
*Features: Input Parameters · Notebook Agent · Fix with Agent*

**[TALKING POINT]**
> "Now something anyone can use: type a city, see the nearest quakes. (`geopy` is already installed.)"

**[ACTION]** Notebook Agent — **one** combined prompt:
```
Build an earthquake proximity finder: (1) a text input `city_name` (default "Seattle, WA"), a numeric input `radius_miles` (default 300), and a date range input; (2) a Python cell using geopy to geocode `city_name`, compute each earthquake's distance in miles, and keep those within `radius_miles` as a dataframe `nearest_quakes` sorted closest-first (columns: title, magnitude, depth_km, distance_miles, latitude, longitude, event_time, place); (3) a pydeck map on a dark CARTO basemap with place labels, a blue dot for the city, and the nearby quakes as small pixel-sized circles colored by magnitude with a tooltip; (4) a clean table of `nearest_quakes`.
```
**[WAIT]** Run all, then change `city_name` to **"Tokyo, Japan"** and drag `radius_miles` to show it recompute.
> "Inputs, geocoding, distance math, a map, a table — from one description."

**[ACTION — Fix with Agent, ~30 sec]** Introduce a tiny bug (e.g., rename a column reference) or use a natural error, then click **"Fix with Agent."**
> "It read the traceback and fixed it. AI-first isn't just writing code — it's maintaining it."

*(If the map shows giant blobs or errors, see the known-good proximity map snippet in `demo_script.md` — the fix is sizing dots in pixels, not meters.)*

---
## 4. Publish the app (10:30–11:30)
*Features: Published Apps · Agent configures app layout*

**[ACTION]** App Builder. Either drag cells, or ask the agent:
```
Lay out the published app: inputs on top, the proximity map in the center, the nearest_quakes table below.
```
**[ACTION]** Click **Publish**, show the URL.
> "A live, shareable app — what are the biggest earthquakes near *your* city? No code, no login."

---
## 5. Threads — ask, don't build (11:30–13:30)
*Features: Threads · Queue Prompts · Python in Threads*

**[ACTION]** Open **Threads**. Type the first, and while it runs, **queue** the second (call out prompt queuing):
```
What were the 10 largest earthquakes in the past year? Show location, magnitude, and depth.
```
```
Now show the monthly trend of magnitude 5+ earthquakes — increasing, decreasing, or flat?
```
**[ACTION]** Then one more that forces Python:
```
Cluster these earthquakes by region with k-means and show the magnitude distribution per cluster.
```
> "No project, no code — and it switched from SQL to Python on its own for the clustering. Bar chart to machine learning in one conversation."

---
## 6. Chat with App (13:30–15:00)
*Features: Chat with App · Chat with App (expanded context)*

**[ACTION]** Back on the published app, click the **interlocking-circles chat icon (lower-right)**:
```
Summarize the key findings of this proximity analysis for Seattle.
```
**[ACTION]** Then a question that goes beyond the screen:
```
Compare earthquake activity near Seattle to San Francisco — which has had more significant seismic activity?
```
> "It read the whole app, then used the app's own logic and database connection to answer something I never explicitly built. A living, conversational dashboard."

**[OPTIONAL BONUS, +60 sec — Hex Connector for Claude]** In Claude (Code/Desktop), with the Hex connector enabled (`Settings → Connectors → "Hex" → https://app.hex.tech/mcp`):
```
Search my Hex projects for earthquakes, then tell me the 10 largest quakes in the last 90 days.
```
> "Same Hex agent, driven from my coding assistant — it streams its thinking and charts right into Claude."

---
## 7. Closeout (15:00)
> "Database to a published, AI-powered app — analysis, clustering, an interactive app, conversational Q&A — in about fifteen minutes. The data's public-domain USGS, refreshed hourly. Hex has a free tier; you can recreate all of it. Thanks for watching."

---
## WHAT WAS CUT vs. THE FULL SCRIPT (`demo_script.md`)
- **Batched agent prompts:** EDA (was 4 prompts → 1), clustering (was 4 → 1), proximity (was 4 → 1). Fewer agent runs = the biggest time savings.
- **Dropped beats:** histogram bin-size tweak, the April 2 outlier drill-down, the second per-cluster Threads follow-up, and most of the repeated "here's why this is cool" narration.
- **Trimmed talking points** to one or two lines each.
- **Kept every feature** on the checklist: SQL + connections, Python/pydeck, Typeahead, Notebook Agent, Input Parameters, Fix with Agent, app layout + Published Apps, Threads (+ queuing + Python), Chat with App (+ expanded context), and the Claude connector as an optional bonus.

## IF YOU NEED TO GO EVEN SHORTER (~10 min)
Cut **Fix with Agent** (Step 3) and the **Bonus connector** (Step 6), and trim Threads to the first two prompts.
