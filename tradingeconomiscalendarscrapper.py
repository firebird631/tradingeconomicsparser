# Basic Scrapper only for Economic Calendar
# Example here filtered for US only
# MIT Licence

import pytz
from datetime import datetime

import requests
from html.parser import HTMLParser



NEWS_TYPE = [
    "pmi", "manufacturing", "rate", "mortgage", "gas", "oil", "building", "permis", "mom", "auction", "bill", "fed", "yoy", "services",
    "michigan", "speech", "housing", "index", "industrial", "production", "stocks", "jobless", "prices", "import", "export", 
    "retail", "consumer", "credit", "car", "10-year", "15-year", "20-year", "25-year", "30-year", "ism", "final", "s&p", "non-farm",
    "ppi", "core", "government", "payrolls", "non", "inflation"]


# todo detect keyword and add a code
CODES = {
    "non farm payrolls": "NFP",
    "30 year mortgage rate": "30Y-R",
    # complete
    }

UTC = pytz.timezone('UTC')


def detect_code(events):
    if events in CODES:
        return CODES[events]

    return None


class TEHTMLParser(HTMLParser):
    """
    date : 'date' format YYYY-MM-DD HH:MM in UTC timezone
    number of star 1,2,3 : 'level'
    keys words of the event : 'event'
    filtered event simplified code : 'code'
    """

    def __init__(self):
        super().__init__()

        self._detect_day = 0
        self._in_new = False
        self._in_time = 0

        self._current_day = ""

        self._news = []
        self._current = {}

        self._actual = False
        self._previous = False
        self._forecast = False

        self._i = 0

    @property
    def news(self):
        return self._news

    def handle_starttag(self, tag, attrs):

        if tag == "thead":
            self._detect_day = 1

        elif tag == "tr" and self._detect_day == 1:
            self._detect_day = 2

        elif tag == "th" and self._detect_day == 2:
            self._detect_day = 3

        if tag == "tr":
            for attr in attrs:
                if attr[0] == "data-url" and attr[1].startswith("/united-states/"):
                    self._in_new = True
                    self._current = {}

                    self._i = 1
                    # print("Encountered a start tag:", tag)

                if attr[0] == "data-event" and self._in_new:
                    self._current['event'] = attr[1]
                    self._current['code'] = detect_code(attr[1])
                    return


        if tag == "span" and self._in_new:
            for attr in attrs:
                if attr[0] == "class" and attr[1].startswith("calendar-date-"):
                    try:
                        self._in_time = int(attr[1][-1])
                        self._current['level'] = self._in_time
                        # print('in time')
                    except ValueError:
                        pass
                elif attr[0] == "id" and attr[1] == "actual":
                    self._actual = True
                elif attr[0] == "id" and attr[1] == "previous":
                    self._previous = True
                elif attr[0] == "id" and attr[1] == "forecast":
                    self._forecast = True

        if self._in_new:
            self._i += 1
 
    def handle_endtag(self, tag):
        if self._in_time:
            self._in_time = False

        if self._in_new and self._i > 0:
            self._i -= 1

        if tag == "tr" and self._in_new and self._i == 0:
            self._in_new = False
            self._news.append(self._current)
            self._current = {}

        if tag == "span":
            if self._actual:
                self._actual = False
            elif self._previous:
                self._previous = False
            elif self._forecast:
                self._forecast = False

        if tag == "th" and self._detect_day == 3:
            self._detect_day = 0


    def handle_data(self, data):
        if self._in_new:
            if self._in_time:
                try:
                    d = self.clean_value(data)

                    # print("Datetime :", d)
                    if d.endswith('AM'):
                        hour = int(d[0:2])
                        minute = int(d[3:5])

                        dt = self._current_day.replace(hour=hour, minute=minute)
                        self._current['date'] = dt.strftime("%Y-%m-%d %H:%M")
                        # print(dt)
         
                    if d.endswith('PM'):
                        hour = int(d[0:2])
                        minute = int(d[3:5])

                        if hour < 12:
                            hour += 12

                        dt = self._current_day.replace(hour=hour, minute=minute)
                        self._current['date'] = dt.strftime("%Y-%m-%d %H:%M")
                        # print(dt)

                except ValueError:
                    pass

            elif self._actual:
                d = self.clean_value(data)
                self._current['actual'] = d
                
            elif self._previous:
                d = self.clean_value(data)
                self._current['previous'] = d

            elif self._forecast:
                d = self.clean_value(data)
                self._current['forecast'] = d

        if self._detect_day == 3:
            self._current_day = self.parse_date(data)

    @staticmethod
    def clean_value(data):
        d = ""
        for c in data:
            if c in (chr(10), chr(13), chr(32)):
                continue
            d += c

        return d

    @staticmethod
    def parse_date(data):
        parts = data.split(' ')
        date = []

        for p in parts:
            p = TEHTMLParser.clean_value(p)

            if len(p) < 2:
                continue

            date.append(p)

        try:
            dt = datetime.strptime(" ".join(date), "%A %B %d %Y").replace(tzinfo=UTC)
            return dt
        except:
            pass

        return ""



def query_economic_calendar(country_name):
    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'
    }

    params = {}

    url = "https://tradingeconomics.com/%s/calendar" % country_name
    response = requests.get(url, params=params, headers=headers)

    parser = TEHTMLParser()
    parser.feed(response.content.decode('utf8'))

    return parser.news


# example : query_economic_calendar("united-states")
if __name__ == "__main__":
    news = query_economic_calendar("united-states")

    if news:
        for new in news:
            print(new)
