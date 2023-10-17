from datetime import datetime
from typing import Any


class Dates(list[tuple[datetime, datetime]]):
    def __init__(self, date_value: str):
        """
        assumes date_value is a list of either 'YYYY-MM-DD' or {'from': 'YYYY-MM-DD', 'to': 'YYYY-MM-DD'}
        returns a list of tuples with from-to dates
        """
        if date_value == "":
            return

        dates = eval(date_value)
        if dates is None:
            return

        if isinstance(dates, list):
            if len(dates) == 0:
                return

            # at this point 'dates' should be a list of either:
            #   'YYYY-MM-DD'
            #   {'from': 'YYYY-MM-DD', 'to': 'YYYY-MM-DD'}
            super().__init__(self._date_intervals(dates))

    def remove_past_dates(self):
        now = datetime.now()
        today = datetime(now.year, now.month, now.day)

        dates_to_keep: list[tuple[datetime, datetime]] = list()
        for date_interval in self:
            if date_interval[1] >= today:
                dates_to_keep.append(date_interval)

        self.clear()
        self.extend(dates_to_keep)

    def _date_intervals(
        self,
        dates: list[str | dict[str, str]],
    ) -> list[tuple[datetime, datetime]]:
        """
        assumes dates is a list of either 'YYYY-MM-DD' or {'from': 'YYYY-MM-DD', 'to': 'YYYY-MM-DD'}
        returns a list of tuples with from-to dates
        """
        date_intervals: list[tuple[datetime, datetime]] = list()

        for date in dates:
            if isinstance(date, str):  # YYYY-MM-DD
                parsed = datetime(int(date[0:4]), int(date[5:7]), int(date[8:10]))
                date_intervals.append((parsed, parsed))

            elif isinstance(date, dict):  # {'from': 'YYYY-MM-DD', 'to': 'YYYY-MM-DD'}
                parsed_from = datetime(
                    int(date["from"][0:4]),
                    int(date["from"][5:7]),
                    int(date["from"][8:10]),
                )
                parsed_to = datetime(
                    int(date["to"][0:4]),
                    int(date["to"][5:7]),
                    int(date["to"][8:10]),
                )
                date_intervals.append((parsed_from, parsed_to))

        return date_intervals

    def date_intervals(
        self,
    ) -> None | list[str | dict[str, str]]:
        """object format for ui.date:[{'from': 'YYYY-MM-DD', 'to': 'YYYY-MM-DD'}, 'YYYY-MM-DD', ...]"""
        if len(self) == 0:
            return None

        output: list[str | dict[str, str]] = list()

        for from_date, to_date in self:
            if from_date == to_date:
                output.append(
                    f"{from_date.year:04}-{from_date.month:02}-{from_date.day:02}"
                )
                continue

            output.append(
                {
                    "from": f"{from_date.year:04}-{from_date.month:02}-{from_date.day:02}",
                    "to": f"{to_date.year:04}-{to_date.month:02}-{to_date.day:02}",
                }
            )

        return output

    def __str__(
        self,
    ) -> str:
        """[{'from': 'YYYY-MM-DD', 'to': 'YYYY-MM-DD'}, 'YYYY-MM-DD', ...]"""
        return str(self.date_intervals())
