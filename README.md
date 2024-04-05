#  Displacement Seismic Amplitude Ratio (DSAR)

## How to Use

1. All the seismic data must have SDS Directory as an input. See an example in [input directory](input).
2. Inside `main.py` or `main.ipynb` change those parameters:
```bash
network = "VG"
station = "PSAG"
location = "00"
channel = "EHZ"

sds_directory = r"D:\Projects\dsar\input"
output_directory = 'output'

start_date = "2017-12-01"
end_date = "2017-12-03"

bands: dict[str, list[float]] = {
    'HF' : [0.1, 8.0, 16.0],
    'LF' : [0.1, 4.5, 8.0],
}

resample_rule: str = '10min'
```
3. Run the `main.py` or `main.ipynb`.
4. The output of this code would be saved into `output` directory and will be used as an input of `dsar.py`.
5. Run `dsar.py` to get the calculated _dsar_ CSV and plot the result.

## References
> Caudron, C., et al., 2019, Change in seismic attenuation as a long-term precursor of gas-driven
eruptions: Geology, https://doi.org/10.1130/G46107.1  
> 
> Chardot, L., Jolly, A. D., Kennedy, B. M., Fournier, N., & Sherburn, S. (2015). Using volcanic tremor for eruption forecasting at White Island volcano (Whakaari), New Zealand. Journal of Volcanology and Geothermal Research, 302, 11–23. https://doi.org/10.1016/j.jvolgeores.2015.06.001
