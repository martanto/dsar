# Displacement Seismic Amplitude Ratio (DSAR)

Python package for computing Displacement Seismic Amplitude Ratio (DSAR) from miniSEED
seismic data stored in SeisComP Data Structure (SDS) archives. DSAR is used in volcanology
as a long-term precursor for detecting changes in seismic attenuation related to volcanic
unrest.

## Requirements

- Python ≥ 3.10

## Installation

### Using uv (recommended)

[uv](https://docs.astral.sh/uv/) is the recommended environment and package manager for
this project.

```bash
# Install uv (if not already installed)
pip install uv

# Create a virtual environment and install dsar
uv venv
uv pip install dsar
```

To run scripts inside the uv-managed environment:

```bash
uv run python main.py
```

### Using pip

```bash
pip install dsar
```

---

## How to Use

### 1. Prepare your SDS data directory

`input_dir` must follow the SeisComP Data Structure (SDS) layout:

```
{input_dir}/
└── {year}/
    └── {network}/
        └── {station}/
            └── {channel}.D/
                └── {network}.{station}.{location}.{channel}.D.{year}.{julian_day}
```

Example file path:
```
D:\Data\OJN\2025\VG\OJN\EHZ.D\VG.OJN.00.EHZ.D.2025.001
```

The NSLC identifier (`{network}.{station}.{location}.{channel}`) is used throughout for
naming output files and directories.

---

### 2. Calculate DSAR

#### Import

```python
from dsar import DSAR, PlotDsar
```

#### Initialize

```python
dsar = DSAR(
    input_dir="D:\\Data\\OJN",
    start_date="2025-01-01",
    end_date="2025-01-08",
    station="OJN",
    channel="EHZ",
    network="VG",
    location="00",
    resample="10min",   # optional, default "10min"
    verbose=True,       # optional, default False
    debug=False,        # optional, default False
)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `input_dir` | `str` | required | Path to the SDS root directory |
| `start_date` | `str` | required | Start date in `YYYY-MM-DD` format |
| `end_date` | `str` | required | End date in `YYYY-MM-DD` format |
| `station` | `str` | required | Station code (e.g. `"OJN"`) |
| `channel` | `str` | required | Channel code (e.g. `"EHZ"`) |
| `network` | `str` | required | Network code (e.g. `"VG"`) |
| `location` | `str` | required | Location code (e.g. `"00"`) |
| `resample` | `str` | `"10min"` | Pandas offset alias for the resampling interval |
| `output_dir` | `str` | `None` | Custom output directory; defaults to `<cwd>/output/dsar` |
| `verbose` | `bool` | `False` | Print detailed stream information |
| `debug` | `bool` | `False` | Print debug-level path and trace information |

#### Set custom frequency bands (optional)

The default bands are **LF** `[0.1, 4.5, 8.0] Hz` and **HF** `[0.1, 8.0, 16.0] Hz`.
Each band is defined by three frequencies `[high_pass, bandpass_low, bandpass_high]`.

```python
dsar.first_bands(name="LF", first_freq=0.1, second_freq=4.5, third_freq=8.0)
dsar.second_bands(name="HF", first_freq=0.1, second_freq=8.0, third_freq=16.0)
```

`first_bands` is the **numerator** and `second_bands` is the **denominator** of the DSAR
ratio. Both methods return `self`, so they can be chained:

```python
dsar.first_bands("LF", 0.1, 4.5, 8.0).second_bands("HF", 0.1, 8.0, 16.0)
```

#### Run

```python
dsar.run()
```

`run()` iterates day by day across the date range, loads each day's miniSEED data from the
SDS archive, processes both frequency bands, computes the DSAR ratio, and saves the result
as a daily CSV.

**Output files:**
```
output/dsar/{NSLC}/{resample}/{NSLC}_{YYYY-MM-DD}.csv
```

Each CSV contains:

| Column | Description |
|---|---|
| `datetime` | Timestamp (index) |
| `LF` | Low-frequency band amplitude |
| `HF` | High-frequency band amplitude |
| `DSAR_{resample}` | Raw DSAR ratio (`LF / HF`) |
| `DSAR_6h_median` | 6-hour centered rolling median |
| `DSAR_24h_median` | 24-hour centered rolling median |

---

### 3. Plot DSAR

#### Initialize

```python
plot = PlotDsar(
    start_date="2025-01-01",
    end_date="2025-01-08",
    station="OJN",
    channel="EHZ",
    network="VG",
    location="00",
    resample="10min",   # must match the resample used in DSAR
)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `start_date` | `str` | required | Start date in `YYYY-MM-DD` format |
| `end_date` | `str` | required | End date in `YYYY-MM-DD` format |
| `station` | `str` | required | Station code |
| `channel` | `str` | required | Channel code |
| `network` | `str` | `"VG"` | Network code |
| `location` | `str` | `"00"` | Location code |
| `resample` | `str` | `"10min"` | Must match the interval used when running DSAR |
| `dsar_dir` | `str` | `None` | Custom DSAR CSV directory; defaults to `<cwd>/output/dsar` |
| `figures_dir` | `str` | `None` | Custom figures directory; defaults to `<cwd>/output/figures/dsar` |

#### Get the combined DataFrame

```python
df = plot.df
```

`plot.df` reads all daily CSVs for the NSLC, concatenates them, removes duplicates, and
saves a combined CSV:

```
output/dsar/{NSLC}/combined_{resample}_{NSLC}.csv
```

You can use `df` directly for further analysis:

```python
print(df.head())
print(df.columns.tolist())
```

#### Plot

```python
fig = plot.plot(
    interval_day=7,     # x-axis tick interval in days
    y_min=85,           # optional y-axis minimum
    y_max=225,          # optional y-axis maximum
    save=True,          # save figure to disk
    file_type="jpg",    # output format: "png", "jpg", etc.
)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `interval_day` | `int` | `3` | X-axis major tick interval in days |
| `title` | `str` | `None` | Custom plot title; defaults to `"DSAR - {NSLC}"` |
| `y_min` | `float` | `None` | Y-axis minimum (auto-scaled if not set) |
| `y_max` | `float` | `None` | Y-axis maximum (auto-scaled if not set) |
| `save` | `bool` | `True` | Save the figure to disk |
| `file_type` | `str` | `"png"` | Output file format |

**Output figure:**
```
output/figures/dsar/{NSLC}/{NSLC}_{resample}_{start_date}-{end_date}.{file_type}
```

---

### 4. Add eruption markers (optional)

Use the utility functions to annotate eruption events on an existing axes:

```python
from dsar.utilities import plot_eruptions

fig = plot.plot(save=False)
ax = fig.axes[0]

plot_eruptions(
    ax,
    axvspans=[["2025-01-03", "2025-01-05"]],   # continuous eruption intervals
    axvlines=["2025-01-07"],                     # discrete eruption events
)
fig.savefig("output.png", dpi=300)
```

---

### 5. Load a combined CSV directly

If you already have a combined CSV file and just want to load it:

```python
from dsar.utilities import get_combined_csv

df = get_combined_csv(
    directory="output/dsar",
    station="VG.OJN.00.EHZ",
    resample="10min",
)
```

---

## Complete example

```python
from dsar import DSAR, PlotDsar

# --- Calculate ---
dsar = DSAR(
    input_dir="D:\\Data\\OJN",
    start_date="2025-01-01",
    end_date="2025-01-08",
    station="OJN",
    channel="EHZ",
    network="VG",
    location="00",
    verbose=True,
)
dsar.first_bands(name="LF", first_freq=0.1, second_freq=4.5, third_freq=8.0)
dsar.second_bands(name="HF", first_freq=0.1, second_freq=8.0, third_freq=16.0)
dsar.run()

# --- Plot ---
plot = PlotDsar(
    start_date="2025-01-01",
    end_date="2025-01-08",
    station="OJN",
    channel="EHZ",
    network="VG",
    location="00",
)
plot.plot(interval_day=2, y_min=50, y_max=300, save=True, file_type="png")
```

---

## References

> Caudron, C., et al., 2019, Change in seismic attenuation as a long-term precursor of
> gas-driven eruptions: Geology, https://doi.org/10.1130/G46107.1

> Chardot, L., Jolly, A. D., Kennedy, B. M., Fournier, N., & Sherburn, S. (2015). Using
> volcanic tremor for eruption forecasting at White Island volcano (Whakaari), New Zealand.
> Journal of Volcanology and Geothermal Research, 302, 11–23.
> https://doi.org/10.1016/j.jvolgeores.2015.06.001
