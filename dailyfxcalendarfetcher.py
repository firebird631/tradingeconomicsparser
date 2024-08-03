import os
import time
import copy
import requests
import pathlib

from datetime import datetime, timedelta

delta = timedelta(days=1)


def fetch_calendar_events():
    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'
    }

    params = {}

    today = datetime.now()

    # no data before 2013
    begin = today.replace(year=2013, month=1, day=1, hour=0, minute=0)

    # until today or a fixed date
    # end = today.replace(year=2013, month=12, day=31, hour=0, minute=0)
    end = copy.copy(today)

    curr = copy.copy(begin)

    cwd = pathlib.Path(os.getcwd())
    output_path = cwd.joinpath("dailyfx", "economic-calendar")


    if not output_path.exists():
        output_path.mkdir(parents=True)

    while curr <= end:
        url = 'https://www.dailyfx.com/economic-calendar/events/%s' % curr.strftime("%Y-%m-%d")
        response = requests.get(url, params=params, headers=headers)
        if response.status_code == 200:
            # print(output_path.joinpath("%s.json" % curr.strftime("%Y%m%d")))
            data = response.json()
            with open(output_path.joinpath("%s.json" % curr.strftime("%Y%m%d")), "w") as f:
                f.write(response.content.decode('utf8'))
                # print(data)
                print("Done %s" % curr)
        curr = curr + delta
        time.sleep(1)


if __name__ == "__main__":
    fetch_calendar_events()
