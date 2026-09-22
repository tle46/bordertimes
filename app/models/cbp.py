from dataclasses import dataclass
from datetime import date, time


@dataclass
class LaneData:
    update_time: str | None = None
    operational_status: str | None = None
    delay_minutes: int | None = None
    lanes_open: int | None = None


@dataclass
class CommercialVehicleLanes:
    maximum_lanes: int | None = None
    cv_automation_type: str | None = None
    cv_segment_from: str | None = None
    cv_segment_to: str | None = None
    cv_standard_tolerance: int | None = None
    cv_fast_tolerance: int | None = None

    standard_lanes: LaneData | None = None
    FAST_lanes: LaneData | None = None


@dataclass
class PassengerVehicleLanes:
    maximum_lanes: int | None = None
    pv_automation_type: str | None = None
    pv_segment_from: str | None = None
    pv_segment_to: str | None = None
    pv_standard_tolerance: int | None = None
    pv_nexus_sentri_tolerance: int | None = None
    pv_ready_tolerance: int | None = None

    standard_lanes: LaneData | None = None
    NEXUS_SENTRI_lanes: LaneData | None = None
    ready_lanes: LaneData | None = None


@dataclass
class PedestrianLanes:
    maximum_lanes: int | None = None
    ped_automation_type: str | None = None
    ped_segment_from: str | None = None
    ped_segment_to: str | None = None
    ped_standard_tolerance: int | None = None
    ped_ready_tolerance: int | None = None

    standard_lanes: LaneData | None = None
    ready_lanes: LaneData | None = None


@dataclass
class CBPData:
    port_number: str
    border: str
    port_name: str
    crossing_name: str
    hours: str

    date: date | None
    time: time | None

    port_status: str

    commercial_vehicle_lanes: CommercialVehicleLanes
    passenger_vehicle_lanes: PassengerVehicleLanes
    pedestrian_lanes: PedestrianLanes

    construction_notice: str | None = None
    automation: str | None = None
    automation_enabled: bool | None = None
