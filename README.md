#  Displacement Seismic Amplitude Ratio (DSAR)

## How to Use
### Install using pip:
```python
pip install dsar
```

### Import `dsar` module
```python
from dsar import DSAR, PlotDsar
```

### Initiate DSAR
```python
dsar = DSAR(
    input_dir="G:\\Output\\Converted\\SDS",
    directory_structure='SDS',
    start_date="2024-01-01",
    end_date="2024-04-22",
    station="RUA3",
    channel="EHZ",
    resample="10min" # default
)
```

See https://github.com/martanto/magma-converter for supported `directory_structure`.

### Run DSAR
```python
dsar.run()
```

### Results/Output directory
Output directory would be as the same folder where DSAR code is running. It will create `output` directory.

### Plot DSAR
Initiate DSAR plot
```python
plot = PlotDsar(
    start_date="2024-01-01",
    end_date="2024-04-22",
    station="RUA3",
    channel="EHZ"
)
```

### Get combined dataframe to plot
```python
df = plot.df
```
The output of dataframe will be saved as CSV:
```text
✅ Saved to D:\Project\dsar\output\dsar\VG.RUA3.00.EHZ\combined_10min_VG.RUA3.00.EHZ.csv
```

Plot DSAR:
```python
plot.plot(
    interval_day=7,
    y_min=85,
    y_max=225,
    save=True,
    file_type='jpg',
)
```
Output:
```text
✅ Saved to D:\Project\dsar\output\dsar\VG.RUA3.00.EHZ\combined_10min_VG.RUA3.00.EHZ.csv
📷 Figure saved to: D:\Project\dsar\output\figures\dsar\VG.RUA3.00.EHZ\VG.RUA3.00.EHZ_10min_2024-01-01-2024-04-22.jpg
```
![output.png](https://github.com/martanto/dsar/blob/master/examples/figures/output.png?raw=true)


## References
> Caudron, C., et al., 2019, Change in seismic attenuation as a long-term precursor of gas-driven
eruptions: Geology, https://doi.org/10.1130/G46107.1  
> 
> Chardot, L., Jolly, A. D., Kennedy, B. M., Fournier, N., & Sherburn, S. (2015). Using volcanic tremor for eruption forecasting at White Island volcano (Whakaari), New Zealand. Journal of Volcanology and Geothermal Research, 302, 11–23. https://doi.org/10.1016/j.jvolgeores.2015.06.001
