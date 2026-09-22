from dataclasses import dataclass, field

@dataclass
class BorderCrossing:
    border_id: str

    name: str
    us_port_number: str = ""
    us_port_name: str = ""
    us_crossing_name: str = ""
    can_port_name: str = ""
    can_crossing_name: str = ""
