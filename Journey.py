import re

class Journey:
    def __init__(self, departure_point, arrival_point, asked_departure_time, departure_time, arrival_time, duration, pysical_mode, name, network, trip_short_name, stops):
        self.departure_point = departure_point
        self.arrival_point = arrival_point
        self.asked_departure_time = asked_departure_time
        self.departure_time = departure_time
        self.arrival_time = arrival_time
        self.duration = duration
        self.pysical_mode = pysical_mode
        self.name = name
        self.network = network
        self.trip_short_name = trip_short_name
        self.stops = stops

    def human_readable_date(self, date):
        year = date[:4]
        month = date[4:6]
        day = date[6:8]
        time_tab = re.findall("..?", date[9:])
        time = ''
        for i in time_tab:
            time +=  ':'+i

        date = "{}/{}/{} @ {}".format(year, month, day, time[1:])

        return date
