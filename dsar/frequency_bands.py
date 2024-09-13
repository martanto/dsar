class FrequencyBands:
    default_first_bands: dict[str, list[float]] = {
        'LF': [0.1, 4.5, 8.0]
    }

    default_second_bands: dict[str, list[float]] = {
        'HF': [0.1, 8.0, 16.0]
    }

    default_bands: dict[str, list[float]] = {}
    default_bands.update(default_first_bands)
    default_bands.update(default_second_bands)

    def __init__(self,
                 name: str,
                 first_frequency: float,
                 second_frequency: float,
                 third_frequency: float, ):
        self.name = name
        self.first_frequency = first_frequency
        self.second_frequency = second_frequency
        self.third_frequency = third_frequency

        assert self.first_frequency <= self.second_frequency <= self.third_frequency, \
            f"❌ The frequencies must have values first_frequency <= second_frequency <= third_frequency"

    def __repr__(self):
        return (f"FrequencyBands('{self.name}', {self.first_frequency}, {self.second_frequency}, "
                f"{self.third_frequency})")

    @property
    def frequencies(self) -> list[float]:
        return [self.first_frequency, self.second_frequency, self.third_frequency]

    def to_dict(self) -> dict[str, list[float]]:
        return {
            self.name: self.frequencies,
        }


default_bands: dict[str, list[float]] = FrequencyBands.default_bands
