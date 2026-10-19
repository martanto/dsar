"""Unit tests for DSAR core pipeline.

Uses main.py as the reference for how DSAR is constructed. All tests mock
SDS.get() so no real SDS data directory is needed beyond the tmp_path fixture.
"""

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from obspy import Stream, Trace
from obspy.core import Stats

from dsar import DSAR
from dsar.frequency_bands import FrequencyBands


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_trace(nslc: str = "VG.OJN.00.EHZ", sampling_rate: float = 100.0, duration_s: float = 86400.0) -> Trace:
    """Return a synthetic ObsPy Trace with random data."""
    n_samples = int(sampling_rate * duration_s)
    stats = Stats()
    network, station, location, channel = nslc.split(".")
    stats.network = network
    stats.station = station
    stats.location = location
    stats.channel = channel
    stats.sampling_rate = sampling_rate
    stats.npts = n_samples
    stats.starttime.year = 2025
    data = np.random.default_rng(0).standard_normal(n_samples).astype(np.float32)
    return Trace(data=data, header=stats)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sds_dir(tmp_path: Path) -> Path:
    """Create a minimal SDS directory structure so DSAR.__init__ doesn't raise."""
    d = tmp_path / "sds" / "2025" / "VG" / "OJN" / "EHZ.D"
    d.mkdir(parents=True)
    return tmp_path / "sds"


@pytest.fixture
def dsar_instance(sds_dir: Path, tmp_path: Path) -> DSAR:
    """Return a DSAR instance wired to tmp_path, matching main.py usage."""
    return DSAR(
        input_dir=str(sds_dir),
        start_date="2025-01-01",
        end_date="2025-01-03",
        station="OJN",
        channel="EHZ",
        network="VG",
        location="00",
        output_dir=str(tmp_path / "output"),
    )


# ---------------------------------------------------------------------------
# FrequencyBands
# ---------------------------------------------------------------------------

def test_frequency_bands_validation():
    with pytest.raises(ValueError):
        FrequencyBands("bad", 8.0, 0.1, 16.0)  # out of order


def test_bands_property_defaults(dsar_instance: DSAR):
    assert dsar_instance.bands == {"LF": [0.1, 4.5, 8.0], "HF": [0.1, 8.0, 16.0]}


def test_bands_property_custom(dsar_instance: DSAR):
    dsar_instance.lower_bands("VLP", 0.01, 0.1, 0.5)
    dsar_instance.upper_bands("LP", 0.5, 1.0, 4.0)
    assert dsar_instance.bands == {"VLP": [0.01, 0.1, 0.5], "LP": [0.5, 1.0, 4.0]}


def test_deprecated_band_methods_still_work(dsar_instance: DSAR):
    with pytest.deprecated_call():
        dsar_instance.first_bands("VLP", 0.01, 0.1, 0.5)
    with pytest.deprecated_call():
        dsar_instance.second_bands("LP", 0.5, 1.0, 4.0)
    assert dsar_instance.bands == {"VLP": [0.01, 0.1, 0.5], "LP": [0.5, 1.0, 4.0]}


# ---------------------------------------------------------------------------
# _process_date
# ---------------------------------------------------------------------------

def test_process_date_saves_csv(dsar_instance: DSAR, tmp_path: Path):
    """_process_date writes a CSV when stream data is available."""
    fake_stream = Stream(traces=[_make_trace()])

    with patch.object(dsar_instance.sds, "get", return_value=fake_stream):
        import pandas as pd
        result = dsar_instance._process_date(pd.Timestamp("2025-01-01"))

    assert result is not None
    assert Path(result).exists()


def test_process_date_no_data(dsar_instance: DSAR):
    """_process_date returns None and writes nothing when stream is empty."""
    with patch.object(dsar_instance.sds, "get", return_value=Stream()):
        import pandas as pd
        result = dsar_instance._process_date(pd.Timestamp("2025-01-01"))

    assert result is None


# ---------------------------------------------------------------------------
# run()
# ---------------------------------------------------------------------------

def test_run_processes_all_dates(dsar_instance: DSAR):
    """run() calls _process_date once per date in the date range."""
    with patch.object(dsar_instance, "_process_date", return_value=None) as mock_proc:
        dsar_instance.run()

    # start_date="2025-01-01", end_date="2025-01-03" → 3 dates
    assert mock_proc.call_count == 3


def test_run_sequential_when_n_jobs_1(dsar_instance: DSAR):
    """run() does not use ThreadPoolExecutor when n_jobs=1."""
    assert dsar_instance.n_jobs == 1

    with patch("dsar.core.ThreadPoolExecutor") as mock_pool:
        with patch.object(dsar_instance, "_process_date", return_value=None):
            dsar_instance.run()

    mock_pool.assert_not_called()


def test_run_uses_thread_pool_when_n_jobs_gt_1(dsar_instance: DSAR):
    """run() uses ThreadPoolExecutor with max_workers=n_jobs when n_jobs > 1."""
    dsar_instance.n_jobs = 2

    with patch("dsar.core.ThreadPoolExecutor", wraps=ThreadPoolExecutor) as mock_pool:
        with patch.object(dsar_instance, "_process_date", return_value=None):
            dsar_instance.run()

    mock_pool.assert_called_once_with(max_workers=2)


def test_plot_defaults_network_and_location():
    from dsar import PlotDsar

    plot = PlotDsar(
        start_date="2025-01-01",
        end_date="2025-01-02",
        station="OJN",
        channel="EHZ",
    )

    assert plot.network == "VG"
    assert plot.location == "00"


def test_plot_save_returns_path(tmp_path: Path):
    from dsar import PlotDsar
    import matplotlib.pyplot as plt

    plot = PlotDsar(
        start_date="2025-01-01",
        end_date="2025-01-02",
        station="OJN",
        channel="EHZ",
        figures_dir=str(tmp_path / "figures"),
    )

    fig = plt.figure()
    saved = plot.save(fig, file_type="png")
    assert Path(saved).exists()
    plt.close(fig)
