class FrequencyBands:
    """Define a frequency band triplet for DSAR processing.

    A frequency band is defined by three frequencies used in sequential filtering:
    a high-pass filter frequency, a bandpass lower corner, and a bandpass upper corner.

    Attributes:
        default_first_bands (dict[str, list[float]]): Default LF band
            ``{"LF": [0.1, 4.5, 8.0]}``.
        default_second_bands (dict[str, list[float]]): Default HF band
            ``{"HF": [0.1, 8.0, 16.0]}``.
        default_bands (dict[str, list[float]]): Combined default LF and HF bands.

    Example:
        >>> band = FrequencyBands("LF", 0.1, 4.5, 8.0)
        >>> band.to_dict()
        {'LF': [0.1, 4.5, 8.0]}
    """

    default_first_bands: dict[str, list[float]] = {"LF": [0.1, 4.5, 8.0]}

    default_second_bands: dict[str, list[float]] = {"HF": [0.1, 8.0, 16.0]}

    default_bands: dict[str, list[float]] = {}
    default_bands.update(default_first_bands)
    default_bands.update(default_second_bands)

    def __init__(
        self,
        name: str,
        first_frequency: float,
        second_frequency: float,
        third_frequency: float,
    ):
        """Initialize a FrequencyBands instance.

        Args:
            name (str): Label for the frequency band (e.g., ``"LF"`` or ``"HF"``).
            first_frequency (float): High-pass filter frequency in Hz applied
                before integration.
            second_frequency (float): Lower corner frequency of the bandpass
                filter in Hz.
            third_frequency (float): Upper corner frequency of the bandpass
                filter in Hz.

        Raises:
            AssertionError: If frequencies are not in non-decreasing order
                (``first_frequency <= second_frequency <= third_frequency``).

        Example:
            >>> band = FrequencyBands("LF", 0.1, 4.5, 8.0)
        """
        self.name = name
        self.first_frequency = first_frequency
        self.second_frequency = second_frequency
        self.third_frequency = third_frequency

        assert (
            self.first_frequency <= self.second_frequency <= self.third_frequency
        ), (
            f"\u274c Frequencies must satisfy "
            f"first_frequency <= second_frequency <= third_frequency. "
            f"Got {first_frequency}, {second_frequency}, {third_frequency}."
        )

    def __repr__(self) -> str:
        """Return a string representation of the FrequencyBands instance.

        Returns:
            str: A string in the format ``FrequencyBands('name', f1, f2, f3)``.
        """
        return (
            f"FrequencyBands('{self.name}', {self.first_frequency}, "
            f"{self.second_frequency}, {self.third_frequency})"
        )

    @property
    def frequencies(self) -> list[float]:
        """Return the three filter frequencies as a list.

        Returns:
            list[float]: Frequency triplet
                ``[first_frequency, second_frequency, third_frequency]``.
        """
        return [self.first_frequency, self.second_frequency, self.third_frequency]

    def to_dict(self) -> dict[str, list[float]]:
        """Return the band as a dictionary mapping the band name to its frequencies.

        Returns:
            dict[str, list[float]]: Single-entry dictionary,
                e.g. ``{"LF": [0.1, 4.5, 8.0]}``.

        Example:
            >>> FrequencyBands("LF", 0.1, 4.5, 8.0).to_dict()
            {'LF': [0.1, 4.5, 8.0]}
        """
        return {
            self.name: self.frequencies,
        }


default_bands: dict[str, list[float]] = FrequencyBands.default_bands
