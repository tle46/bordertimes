import re
from datetime import datetime
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup

from app.models.cbsa import CBSAData


URL = "https://www.cbsa-asfc.gc.ca/bwt-taf/menu-eng.html"


class CBSAService:
    def get_cbsa(self) -> list[CBSAData]:
        response = requests.get(
            URL,
            timeout=30,
            headers={
                "User-Agent": "Mozilla/5.0",
            },
        )
        response.raise_for_status()

        return self._parse(response.text)

    def _parse(self, html: str) -> list[CBSAData]:
        soup = BeautifulSoup(html, "html.parser")

        table = soup.find("table", id="bwttaf")

        if table is None:
            raise RuntimeError(
                "Could not find the CBSA border wait-time table."
            )

        tbody = table.find("tbody")

        if tbody is None:
            raise RuntimeError(
                "Could not find the CBSA border wait-time table body."
            )

        results: list[CBSAData] = []

        for row in tbody.find_all("tr"):
            cells = row.find_all(["th", "td"])

            if len(cells) != 4:
                continue

            port_cell = cells[0]

            # Get only the text inside <b>.
            port_name_tag = port_cell.find("b")

            if port_name_tag:
                port_name = self._clean_text(
                    port_name_tag.get_text(" ", strip=True)
                )
            else:
                port_name = ""

            # Remove traffic-type annotations.
            # Keep annotations such as "(Ferry Point Bridge)".
            port_name = re.sub(
                r"\s*\((Travellers and Commercial|Travellers only)\)\s*$",
                "",
                port_name,
                flags=re.IGNORECASE,
            ).strip()

            # Get the crossing name by removing the port name
            # from the full text of the first cell.
            crossing_name = self._clean_text(
                port_cell.get_text(" ", strip=True).replace(
                    port_name_tag.get_text(" ", strip=True)
                    if port_name_tag
                    else "",
                    "",
                    1,
                )
            )

            commercial_flow = self._parse_flow(
                cells[1].get_text(" ", strip=True)
            )

            travellers_flow = self._parse_flow(
                cells[2].get_text(" ", strip=True)
            )

            time_tag = cells[3].find("time")

            if time_tag:
                # Prefer the machine-readable datetime attribute.
                updated_value = time_tag.get("datetime", "").strip()

                # Fall back to the displayed value if necessary.
                if not updated_value:
                    updated_value = self._clean_text(
                        time_tag.get_text(" ", strip=True)
                    )
            else:
                updated_value = self._clean_text(
                    cells[3].get_text(" ", strip=True)
                )

            updated = self._parse_datetime(updated_value)

            # Port name and crossing name are reversed in the CBSA markup.
            results.append(
                CBSAData(
                    port_name=crossing_name,
                    crossing_name=port_name,
                    commercial_flow=commercial_flow,
                    travellers_flow=travellers_flow,
                    updated=updated,
                )
            )

        return results

    @staticmethod
    def _parse_flow(value: str) -> int | None:
        """
        Examples:
            "No Delay"        -> 0
            "1 minute"        -> 1
            "12 minutes"      -> 12
            "Not Applicable" -> None
        """
        value = " ".join(value.split()).strip()

        if value.lower() == "no delay":
            return 0

        if value.lower() == "not applicable":
            return None

        match = re.search(r"\d+", value)

        if match:
            return int(match.group())

        return None

    @staticmethod
    def _parse_datetime(value: str) -> datetime | None:
        """
        Parse CBSA timestamps.

        Supported formats include:

            2026-09-10T23:46:00-03:00
            2026-09-10T22:26:00-04:00
            2026-09-10 23:46 ADT
            2026-09-10 22:26 EDT

        Returns a timezone-aware datetime whenever the timezone
        information is available.
        """
        if not value:
            return None

        value = " ".join(value.split()).strip()

        # First try ISO-8601.
        #
        # This handles values such as:
        #   2026-09-10T23:46:00-03:00
        #   2026-09-10T22:26:00-04:00
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            pass

        # Fall back to CBSA's displayed format:
        #
        #   2026-09-10 23:46 ADT
        #   2026-09-10 22:26 EDT
        try:
            date_time, timezone = value.rsplit(" ", 1)
        except ValueError:
            return None

        timezone_name = {
            "ADT": "America/Halifax",
            "AST": "America/Halifax",
            "EDT": "America/Toronto",
            "EST": "America/Toronto",
            "CDT": "America/Winnipeg",
            "CST": "America/Winnipeg",
            "MDT": "America/Edmonton",
            "MST": "America/Edmonton",
            "PDT": "America/Vancouver",
            "PST": "America/Vancouver",
        }.get(timezone.upper())

        if timezone_name is None:
            return None

        try:
            naive_datetime = datetime.strptime(
                date_time,
                "%Y-%m-%d %H:%M",
            )
        except ValueError:
            return None

        return naive_datetime.replace(
            tzinfo=ZoneInfo(timezone_name)
        )

    @staticmethod
    def _clean_text(value: str) -> str:
        return " ".join(value.split())

# service = CBSAService()
# data = service.get_cbsa()

# for cbsa in data:
#     if "Thousand Islands Bridge" in cbsa.crossing_name:
#         print(cbsa)
