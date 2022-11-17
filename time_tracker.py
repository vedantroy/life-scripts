import csv
import datetime
from dateutil import parser
import glob
from pathlib import Path

import humanize
import matplotlib.pyplot as plt

csv_files = glob.glob("timesheets/*.csv")


def time_to_ints(time):
    return time.hour, time.minute


def make_chart(path):
    # split path on - and get the last part
    date = path.split("-")[-1][: -len(".csv")].strip()
    date = date.replace("_", "-")

    # read csv
    with open(path, "r") as f:
        reader = csv.reader(f)
        data = list(reader)

        headers = data[0]
        name = {name: idx for idx, name in enumerate(headers)}

        category_to_time = {}
        end = None
        untracked = None
        for idx, row in enumerate(data[1:]):

            def safe_parse(s):
                try:
                    return parser.parse(s)
                except Exception as e:
                    raise ValueError(
                        f'Error parsing "{s}" in {path} at row {idx}, with message: {e}'
                    )

            start_s, end_s = row[name["Start"]], row[name["End"]]

            # if there's no start but an end, then use the previous end as the start
            if start_s == "" and end_s != "":
                start = end
            else:
                start = safe_parse(start_s)

                # We only have untracked time if there's a start time, b/c
                # otherwise our start time is the previous end time
                if end:
                    untracked_cur = start - end
                    untracked = (
                        untracked + untracked_cur if untracked else untracked_cur
                    )

            end = safe_parse(end_s)
            delta = end - start

            if end < start:
                delta += datetime.timedelta(days=1)

            category = row[name["Category"]].strip()
            if delta > datetime.timedelta(hours=5):
                print(
                    f'Warning: {delta} is a long time for {category} in {path} at row {idx}. Start: "{start_s}", End: "{end_s}"'
                )

            if category in category_to_time:
                category_to_time[category] += delta
            else:
                category_to_time[category] = delta

        labels = []
        times = []
        print("==Summary==")
        total_tracked = sum(x.total_seconds() for x in category_to_time.values())
        print(f"Total tracked: {humanize.precisedelta(total_tracked)}")
        if untracked:
            print(
                f"Total untracked: {humanize.precisedelta(untracked.total_seconds())}"
            )

        print("==Chart===")
        for category, delta in category_to_time.items():
            labels.append(f"{category} ({humanize.naturaldelta(delta)})")
            times.append(delta.total_seconds())
            print(f"{category}: {humanize.precisedelta(delta)}")

        Path("charts").mkdir(parents=True, exist_ok=True)
        plt.pie(times, labels=labels)
        plt.savefig(f"charts/{date}.png")


for path in csv_files:
    make_chart(path)
