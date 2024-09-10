from obspy import read, Stream
from .frequency_bands import FrequencyBands


class DSAR:
    def __init__(self,
                 stream: Stream,
                 resample: str  = None):
        self.stream = stream

        self.resample = resample
        if resample is None:
            self.resample = '10min'

    def first_bands(self, frequency_bands: FrequencyBands):
        return frequency_bands.to_dict()

    def second_bands(self, frequency_bands: FrequencyBands):
        return frequency_bands.to_dict()
