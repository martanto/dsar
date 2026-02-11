# Standard library imports
import os
from datetime import datetime
from pathlib import Path
from typing import Any

# Third party imports
from obspy import ObsPyReadingError, Stream, Trace, read


class SDS:
    """SeisComP Data Structure (SDS) reader for seismic data.

    Implements the SDS directory structure for reading miniSEED files.
    SDS structure: {sds_dir}/{year}/{network}/{station}/{channel}.D/{nslc}.D.{year}.{julian_day}

    More information: https://www.seiscomp.de/seiscomp3/doc/applications/slarchive/SDS.html

    Args:
        sds_dir (str): Root path to SDS directory.
        station (str): Station code (e.g., "OJN").
        channel (str): Channel code (e.g., "EHZ").
        network (str, optional): Network code. Defaults to "VG".
        location (str, optional): Location code. Defaults to "00".
        verbose (bool, optional): Enable verbose logging. Defaults to False.
        debug (bool, optional): Enable debug logging. Defaults to False.

    Attributes:
        sds_dir (str): Root SDS directory path.
        station (str): Station code (uppercase).
        channel (str): Channel code (uppercase).
        network (str): Network code (uppercase).
        location (str): Location code (uppercase).
        nslc (str): Network.Station.Location.Channel identifier.
        files (list[dict[str, Any]]): Metadata of loaded files.

    Raises:
        FileNotFoundError: If SDS directory does not exist.
        ValueError: If station or channel codes are invalid.

    Examples:
        >>> sds = SDS(sds_dir="/data/sds", station="OJN", channel="EHZ")
        >>> stream = sds.get(datetime(2025, 1, 1))
    """

    def __init__(
        self,
        sds_dir: str,
        station: str,
        channel: str,
        network: str = "VG",
        location: str = "00",
        verbose: bool = False,
        debug: bool = False,
    ):
        # Validate inputs
        if not station or not isinstance(station, str):
            raise ValueError("Station code must be a non-empty string")
        if not channel or not isinstance(channel, str):
            raise ValueError("Channel code must be a non-empty string")

        # Check if SDS directory exists
        sds_path = Path(sds_dir)
        if not sds_path.exists():
            raise FileNotFoundError(f"SDS directory does not exist: {sds_dir}")
        if not sds_path.is_dir():
            raise NotADirectoryError(f"SDS path is not a directory: {sds_dir}")

        self.sds_dir = str(sds_path.resolve())
        self.station = station.upper()
        self.channel = channel.upper()
        self.network = network.upper()
        self.location = location.upper()
        self.verbose = verbose
        self.debug = debug

        self.nslc = f"{self.network}.{self.station}.{self.location}.{self.channel}"
        self.files: list[dict[str, Any]] = []

        if self.verbose:
            print(f"SDS initialized: {self.nslc} from {self.sds_dir}")

    def get_filepath(self, date: datetime) -> str:
        """Construct SDS filepath for a specific date.

        Builds the file path following SDS structure:
        {sds_dir}/{year}/{network}/{station}/{channel}.D/{nslc}.D.{year}.{julian_day}

        Args:
            date (datetime): Date for which to construct the filepath.

        Returns:
            str: Absolute path to the SDS miniSEED file.

        Raises:
            TypeError: If date is not a datetime object.

        Examples:
            >>> sds.get_filepath(datetime(2025, 1, 15))
            '/data/sds/2025/VG/OJN/EHZ.D/VG.OJN.00.EHZ.D.2025.015'
        """
        if not isinstance(date, datetime):
            raise TypeError("Date must be a datetime object")

        year = date.year
        julian_day = date.strftime("%j")  # Day of year as zero-padded decimal (001-366)

        # Construct SDS directory structure
        data_dir = os.path.join(
            self.sds_dir, str(year), self.network, self.station, f"{self.channel}.D"
        )

        if self.debug:
            print(f"Data directory: {data_dir}")

        # Construct filename
        filename = f"{self.nslc}.D.{year}.{julian_day}"
        filepath = os.path.join(data_dir, filename)

        return filepath

    def load_stream(self, filepath: str, date_str: str) -> Stream:
        """Load seismic stream from miniSEED file.

        Reads the miniSEED file using ObsPy and merges any gaps using interpolation.
        Tracks successfully loaded files in self.files.

        Args:
            filepath (str): Absolute path to miniSEED file.
            date_str (str): Date string (YYYY-MM-DD) for logging purposes.

        Returns:
            Stream: ObsPy Stream object, or empty Stream if loading fails.

        Raises:
            None: Returns empty Stream on error instead of raising exceptions.
        """
        try:
            # Read miniSEED file
            stream = read(filepath, format="MSEED")

            # Log file metadata
            file_metadata = {
                "date": date_str,
                "filepath": filepath,
                "n_traces": len(stream),
                "loaded_at": datetime.now().isoformat(),
            }

            # Merge traces if there are gaps (interpolate missing data)
            stream = stream.merge(fill_value="interpolate")

            # Track successfully loaded files
            self.files.append(file_metadata)

            if self.debug:
                print(
                    f"{date_str} :: Loaded {len(stream)} trace(s) from {filepath}"
                )

            return stream

        except ObsPyReadingError as e:
            print(f"{date_str} :: Failed to read miniSEED file: {filepath}")
            print(f"{date_str} :: Error: {e}")
            return Stream()

        except Exception as e:
            print(f"{date_str} :: Unexpected error loading {filepath}: {e}")
            return Stream()

    def get(self, date: datetime) -> Stream:
        """Retrieve seismic stream for a specific date from SDS archive.

        Constructs the SDS filepath, checks if it exists, and loads the stream.
        Returns an empty Stream if the file doesn't exist or can't be loaded.

        Args:
            date (datetime): Date for which to retrieve data.

        Returns:
            Stream: ObsPy Stream object containing seismic data, or empty Stream if unavailable.

        Raises:
            TypeError: If date is not a datetime object.

        Examples:
            >>> stream = sds.get(datetime(2025, 1, 1))
            >>> if len(stream) > 0:
            ...     print(f"Loaded {len(stream[0].data)} samples")
        """
        if not isinstance(date, datetime):
            raise TypeError("Date must be a datetime object")

        date_str = date.strftime("%Y-%m-%d")
        filepath = self.get_filepath(date)

        # Check if file exists
        if not os.path.exists(filepath):
            if self.debug:
                print(f"{date_str} :: miniSEED file not found: {filepath}")
            return Stream()

        # Load stream from file
        stream = self.load_stream(filepath, date_str)

        # Log results
        if len(stream) == 0:
            print(f"{date_str} :: No traces found in {filepath}")
        elif self.verbose:
            trace: Trace = stream[0]
            n_samples = len(trace.data)
            sampling_rate = trace.stats.sampling_rate
            duration = n_samples / sampling_rate if sampling_rate > 0 else 0

            print(f"{date_str} :: Stream loaded successfully")
            print(
                f"{date_str} :: {len(stream)} trace(s), {n_samples} samples, "
                f"{duration:.1f}s duration @ {sampling_rate}Hz"
            )

        return stream
