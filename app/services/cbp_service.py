from datetime import date, datetime, time

import requests

from app.models.cbp import (
    CBPData,
    LaneData,
    CommercialVehicleLanes,
    PassengerVehicleLanes,
    PedestrianLanes,
)


URL = "https://bwt.cbp.gov/api/bwtpublicmod"


class CBPService:

    def get_cbp(self) -> list[CBPData]:
        response = requests.get(
            URL,
            timeout=30,
        )
        response.raise_for_status()

        raw_data = response.json()

        return [
            self._create_cbp_data(port)
            for port in raw_data
        ]

    def _create_cbp_data(self, data: dict) -> CBPData:
        commercial = data["commercial_vehicle_lanes"]
        passenger = data["passenger_vehicle_lanes"]
        pedestrian = data["pedestrian_lanes"]

        return CBPData(
            # Keep as string because port numbers can have leading zeros.
            port_number=str(data["port_number"]),
            border=data["border"],
            port_name=data["port_name"],
            crossing_name=data["crossing_name"],
            hours=data["hours"],

            date=self._to_date(
                data.get("date")
            ),
            time=self._to_time(
                data.get("time")
            ),

            port_status=data["port_status"],

            commercial_vehicle_lanes=CommercialVehicleLanes(
                maximum_lanes=self._to_int(
                    commercial.get("maximum_lanes")
                ),
                cv_automation_type=self._to_string(
                    commercial.get("cv_automation_type")
                ),
                cv_segment_from=self._to_string(
                    commercial.get("cv_segment_from")
                ),
                cv_segment_to=self._to_string(
                    commercial.get("cv_segment_to")
                ),
                cv_standard_tolerance=self._to_int(
                    commercial.get("cv_standard_tolerance")
                ),
                cv_fast_tolerance=self._to_int(
                    commercial.get("cv_fast_tolerance")
                ),

                standard_lanes=self._create_lane_data(
                    commercial.get("standard_lanes")
                ),
                FAST_lanes=self._create_lane_data(
                    commercial.get("FAST_lanes")
                ),
            ),

            passenger_vehicle_lanes=PassengerVehicleLanes(
                maximum_lanes=self._to_int(
                    passenger.get("maximum_lanes")
                ),
                pv_automation_type=self._to_string(
                    passenger.get("pv_automation_type")
                ),
                pv_segment_from=self._to_string(
                    passenger.get("pv_segment_from")
                ),
                pv_segment_to=self._to_string(
                    passenger.get("pv_segment_to")
                ),
                pv_standard_tolerance=self._to_int(
                    passenger.get("pv_standard_tolerance")
                ),
                pv_nexus_sentri_tolerance=self._to_int(
                    passenger.get("pv_nexus_sentri_tolerance")
                ),
                pv_ready_tolerance=self._to_int(
                    passenger.get("pv_ready_tolerance")
                ),

                standard_lanes=self._create_lane_data(
                    passenger.get("standard_lanes")
                ),
                NEXUS_SENTRI_lanes=self._create_lane_data(
                    passenger.get("NEXUS_SENTRI_lanes")
                ),
                ready_lanes=self._create_lane_data(
                    passenger.get("ready_lanes")
                ),
            ),

            pedestrian_lanes=PedestrianLanes(
                maximum_lanes=self._to_int(
                    pedestrian.get("maximum_lanes")
                ),
                ped_automation_type=self._to_string(
                    pedestrian.get("ped_automation_type")
                ),
                ped_segment_from=self._to_string(
                    pedestrian.get("ped_segment_from")
                ),
                ped_segment_to=self._to_string(
                    pedestrian.get("ped_segment_to")
                ),
                ped_standard_tolerance=self._to_int(
                    pedestrian.get("ped_standard_tolerance")
                ),
                ped_ready_tolerance=self._to_int(
                    pedestrian.get("ped_ready_tolerance")
                ),

                standard_lanes=self._create_lane_data(
                    pedestrian.get("standard_lanes")
                ),
                ready_lanes=self._create_lane_data(
                    pedestrian.get("ready_lanes")
                ),
            ),

            construction_notice=self._to_string(
                data.get("construction_notice")
            ),
            automation=self._to_string(
                data.get("automation")
            ),
            automation_enabled=self._to_bool(
                data.get("automation_enabled")
            ),
        )

    @staticmethod
    def _create_lane_data(
        data: dict | None,
    ) -> LaneData | None:
        if not data:
            return None

        return LaneData(
            update_time=CBPService._to_string(
                data.get("update_time")
            ),
            operational_status=CBPService._to_string(
                data.get("operational_status")
            ),
            delay_minutes=CBPService._to_int(
                data.get("delay_minutes")
            ),
            lanes_open=CBPService._to_int(
                data.get("lanes_open")
            ),
        )

    @staticmethod
    def _to_string(value) -> str | None:
        if value is None:
            return None

        value = str(value).strip()

        return value if value else None

    @staticmethod
    def _to_int(value) -> int | None:
        if value is None:
            return None

        if isinstance(value, str):
            value = value.strip()

            if not value or value.upper() == "N/A":
                return None

        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _to_bool(value) -> bool | None:
        if value is None:
            return None

        if isinstance(value, bool):
            return value

        value = str(value).strip().lower()

        if value in {"1", "true", "yes"}:
            return True

        if value in {"0", "false", "no"}:
            return False

        return None

    @staticmethod
    def _to_date(value) -> date | None:
        if not value:
            return None

        try:
            return datetime.strptime(
                value,
                "%m/%d/%Y",
            ).date()
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _to_time(value) -> time | None:
        if not value:
            return None

        try:
            return datetime.strptime(
                value,
                "%H:%M:%S",
            ).time()
        except (TypeError, ValueError):
            return None


# service = CBPService()
# data = service.get_cbp()

# for cbp in data:
#     print(cbp)
#     break