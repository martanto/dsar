class FrequencyBands:
    def __init__(self,
                 label: str,
                 first_frequency: float,
                 second_frequency: float,
                 third_frequency: float,):
        self.label = label
        self.first_frequency = first_frequency
        self.second_frequency = second_frequency
        self.third_frequency = third_frequency

        assert self.first_frequency <= self.second_frequency <= self.third_frequency, \
            f"❌ The frequencies must have values first_frequency <= second_frequency <= third_frequency"

    def __repr__(self):
        return (f"FrequencyBands('{self.label}', {self.first_frequency}, {self.second_frequency}, "
                f"{self.third_frequency})")

    @property
    def frequencies(self) -> list[float]:
        return [self.first_frequency, self.second_frequency, self.third_frequency]

    def to_dict(self) -> dict[str, list[float]]:
        return {
            self.label: self.frequencies,
        }