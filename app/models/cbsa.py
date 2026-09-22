from dataclasses import dataclass
from datetime import datetime

@dataclass
class CBSAData:
    port_name: str
    crossing_name: str
    commercial_flow: int | None = None
    travellers_flow: int | None = None
    updated: datetime | None = None
