from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable
from zoneinfo import ZoneInfo
import json

from app.models.observation import Observation, to_utc


class ObservationService:
    """
    Joins CBP and CBSA data using bordermapping.json.

    CBP:
        US -> Canada

    CBSA:
        Canada -> US

    CBSA flow fields are delay times in minutes:

        travellers_flow -> canus_passenger_delay
        commercial_flow -> canus_commercial_delay

    All datetimes exposed by Observation are UTC.
    """

    CBP_TIMEZONE = ZoneInfo("America/New_York")

    def __init__(self, mapping_file: str | Path):
        self.mapping_file = Path(mapping_file)
        self.mappings = self._load_mappings()

        self.by_us_port_number = {
            self._normalize(border["us_port_number"]): border
            for border in self.mappings
            if border.get("us_port_number")
        }

        self.by_cbsa_key = {
            (
                self._normalize(border["can_port_name"]),
                self._normalize(border["can_crossing_name"]),
            ): border
            for border in self.mappings
            if border.get("can_port_name")
            and border.get("can_crossing_name")
        }

    def build_observations(
        self,
        cbp_list: Iterable,
        cbsa_list: Iterable,
        observation_time: datetime | None = None,
    ) -> list[Observation]:

        if observation_time is None:
            observation_time = datetime.now(timezone.utc)
        else:
            observation_time = to_utc(observation_time)

        observations: dict[str, Observation] = {}

        # ----------------------------------------------------------
        # CBP: US -> Canada
        # ----------------------------------------------------------

        for cbp in cbp_list:
            mapping = self._find_cbp_mapping(cbp)

            if mapping is None:
                continue

            border_id = str(mapping["border_id"])
            border_name = str(mapping["name"])

            observation = observations.setdefault(
                border_id,
                Observation(
                    border_id=border_id,
                    border_name=border_name,
                    observation_time=observation_time,
                ),
            )

            self._apply_cbp(observation, cbp)

        # ----------------------------------------------------------
        # CBSA: Canada -> US
        # ----------------------------------------------------------

        for cbsa in cbsa_list:
            mapping = self._find_cbsa_mapping(cbsa)

            if mapping is None:
                continue

            border_id = str(mapping["border_id"])
            border_name = str(mapping["name"])

            observation = observations.setdefault(
                border_id,
                Observation(
                    border_id=border_id,
                    border_name=border_name,
                    observation_time=observation_time,
                ),
            )

            self._apply_cbsa(observation, cbsa)

        return sorted(
            observations.values(),
            key=lambda observation: int(observation.border_id),
        )

    # --------------------------------------------------------------
    # CBP matching
    # --------------------------------------------------------------

    def _find_cbp_mapping(self, cbp):
        port_number = self._normalize(
            getattr(cbp, "port_number", None)
        )

        if not port_number:
            return None

        return self.by_us_port_number.get(port_number)

    # --------------------------------------------------------------
    # CBSA matching
    # --------------------------------------------------------------

    def _find_cbsa_mapping(self, cbsa):
        port_name = self._normalize(
            getattr(cbsa, "port_name", None)
        )

        crossing_name = self._normalize(
            getattr(cbsa, "crossing_name", None)
        )

        key = (port_name, crossing_name)

        mapping = self.by_cbsa_key.get(key)

        if mapping is not None:
            return mapping

        # Fallback to crossing name if port-name formatting changes.
        if crossing_name:
            for border in self.mappings:
                if self._normalize(
                    border.get("can_crossing_name")
                ) == crossing_name:
                    return border

        return None

    # --------------------------------------------------------------
    # CBP -> Observation
    # --------------------------------------------------------------

    def _apply_cbp(
        self,
        observation: Observation,
        cbp,
    ):
        passenger = getattr(
            cbp,
            "passenger_vehicle_lanes",
            None,
        )

        commercial = getattr(
            cbp,
            "commercial_vehicle_lanes",
            None,
        )

        passenger_standard = self._get(
            passenger,
            "standard_lanes",
        )

        commercial_standard = self._get(
            commercial,
            "standard_lanes",
        )

        observation.uscan_passenger_lanes = self._get(
            passenger_standard,
            "lanes_open",
        )

        observation.uscan_passenger_delay = self._get(
            passenger_standard,
            "delay_minutes",
        )

        observation.uscan_commercial_lanes = self._get(
            commercial_standard,
            "lanes_open",
        )

        observation.uscan_commercial_delay = self._get(
            commercial_standard,
            "delay_minutes",
        )

        # CBP provides date and time separately.
        #
        # The CBP timestamp is interpreted as America/New_York
        # and then converted to UTC by Observation.
        date = getattr(cbp, "date", None)
        time = getattr(cbp, "time", None)

        if date is not None and time is not None:
            cbp_datetime = datetime.combine(
                date,
                time,
                tzinfo=self.CBP_TIMEZONE,
            )

            observation.uscan_updated = to_utc(cbp_datetime)

    # --------------------------------------------------------------
    # CBSA -> Observation
    # --------------------------------------------------------------

    def _apply_cbsa(
        self,
        observation: Observation,
        cbsa,
    ):
        """
        CBSA flow values are delay times in minutes.

        travellers_flow:
            passenger delay in minutes

        commercial_flow:
            commercial delay in minutes

        CBSA does not provide lane counts, so the lane fields
        remain None.
        """

        observation.canus_passenger_delay = getattr(
            cbsa,
            "travellers_flow",
            None,
        )

        observation.canus_commercial_delay = getattr(
            cbsa,
            "commercial_flow",
            None,
        )

        cbsa_updated = getattr(
            cbsa,
            "updated",
            None,
        )

        observation.canus_updated = to_utc(
            cbsa_updated
        )

    # --------------------------------------------------------------
    # Helpers
    # --------------------------------------------------------------

    def _load_mappings(self) -> list[dict]:
        with self.mapping_file.open(
            "r",
            encoding="utf-8",
        ) as file:
            return json.load(file)

    @staticmethod
    def _normalize(value) -> str:
        if value is None:
            return ""

        return " ".join(
            str(value).strip().split()
        ).casefold()

    @staticmethod
    def _get(
        obj,
        attribute,
        default=None,
    ):
        if obj is None:
            return default

        return getattr(
            obj,
            attribute,
            default,
        )


def build_observations(
    cbp_list: Iterable,
    cbsa_list: Iterable,
    mapping_file: str | Path = "bordermapping.json",
    observation_time: datetime | None = None,
) -> list[Observation]:

    service = ObservationService(mapping_file)

    return service.build_observations(
        cbp_list=cbp_list,
        cbsa_list=cbsa_list,
        observation_time=observation_time,
    )
