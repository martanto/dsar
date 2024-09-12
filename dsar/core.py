from obspy import read, Stream
from .frequency_bands import FrequencyBands, default_bands
from typing_extensions import Dict, List, Self


class DSAR:
    resample: str = '10min'

    def __init__(self,
                 stream: Stream,
                 resample: str = None,
                 station: str = None,
                 channel: str = None,
                 network: str = None,
                 location: str = None,):
        self.stream = stream
        self.resample = resample if resample is not None else self.resample
        self.station = '*' if station is None else station
        self.channel = '*' if channel is None else channel
        self.network = '*' if network is None else network
        self.location = '*' if location is None else location

        self.nslc = f"{self.network}.{self.station}.{self.location}.{self.channel}"

        self._first_label: str | None = None
        self._first_bands: dict[str, List[float]] | None = None

        self._second_label: str | None = None
        self._second_bands: dict[str, List[float]] | None = None

    def __repr__(self):
        return (f"DSAR(stream={self.stream}, resample={self.resample}), first_bands={self._first_bands}, "
                f"second_bands={self._second_bands}, bands={self.bands}")

    def first_bands(self,
                    name: str,
                    first_freq: float,
                    second_freq: float,
                    third_freq: float) -> Self:
        self._first_bands = FrequencyBands(name, first_freq, second_freq, third_freq).to_dict()
        self._first_label = name
        return self

    def second_bands(self,
                     name: str,
                     first_freq: float,
                     second_freq: float,
                     third_freq: float):
        self._second_bands = FrequencyBands(name, first_freq, second_freq, third_freq).to_dict()
        self._second_label = name
        return self

    @property
    def bands(self) -> dict[str, list[float]]:
        bands: dict[str, list[float]] = default_bands

        if self._first_bands is not None and self._second_bands is not None:
            bands = {}
            bands.update(self._first_bands)
            bands.update(self._second_bands)

        return bands

    @staticmethod
    def process(stream: Stream, band_frequencies: list[float]) -> Stream:
        assert len(band_frequencies) == 3, (f"❌ Length of band_frequencies must equal 3. "
                                            f"Example [0.1, 8.0, 16.0]")
        stream.merge(fill_value=0)
        stream.detrend('demean')
        stream.filter('highpass', freq=band_frequencies[0])
        stream.integrate()
        stream.filter('highpass', freq=band_frequencies[1])
        stream.filter('lowpass', freq=band_frequencies[2])
        return stream

    def run(self):
        stream: Stream = self.stream.select(
            station=self.station,
            channel=self.channel,
            network=self.network,
            location=self.location
        )

        if stream.count() > 0:
            for band_name, band_frequencies in self.bands.items():
                stream = self.process(stream, band_frequencies)

