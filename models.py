from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Apartment:
    source: str                      # np. "degewo", "gewobag", itd.
    title: str
    address: str
    district: str
    rooms: Optional[float]
    area_m2: Optional[float]
    warm_rent: Optional[float]
    cold_rent: Optional[float]
    available_from: Optional[str]
    wbs_required: bool
    wbs_type: Optional[str]          # np. "WBS 160", "WBS 220", "besonderer Wohnbedarf"
    url: str
    extra: dict = field(default_factory=dict)

    def __str__(self):
        wbs_info = f"[WBS: {self.wbs_type or 'wymagany'}]" if self.wbs_required else "[Bez WBS]"
        return (
            f"{self.source.upper()} | {self.rooms} pok. | {self.area_m2} m² | "
            f"{self.warm_rent} € (ciepły) | {self.address} | {wbs_info} | {self.url}"
        )
