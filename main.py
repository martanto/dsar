from dsar import DSAR, PlotDsar

start_date = "2025-01-01"
end_date = "2025-01-08"
station = "OJN"
channel = "EHZ"
network = "VG"
location = "00"


def plot():
    plot = PlotDsar(
        start_date=start_date,
        end_date=end_date,
        station=station,
        channel=channel,
        network=network,
        location=location,
    )

    df = plot.df

    plot.plot(
        interval_day=7,
        y_min=85,
        y_max=225,
        save=True,
        file_type="jpg",
    )


def main():
    dsar = DSAR(
        input_dir=r"D:\Data\OJN",
        start_date=start_date,
        end_date=end_date,
        station=station,
        channel=channel,
        network=network,
        location=location,
        verbose=True,
        debug=True,
    )

    # "LF": [0.1, 4.5, 8.0]
    dsar.first_bands(
        name="LF",  # Change whatever you want
        first_freq=0.1,
        second_freq=4.5,
        third_freq=8,
    )

    # "HF": [0.1, 8.0, 16.0]
    dsar.second_bands(
        name="HF",  # Change whatever you want
        first_freq=0.1,
        second_freq=8.0,
        third_freq=16,
    )

    dsar.run()


if __name__ == "__main__":
    main()
    plot()
