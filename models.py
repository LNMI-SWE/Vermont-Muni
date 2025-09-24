from dataclasses import dataclass
from typing import Any, Dict, Optional
import re


@dataclass
class Town:
    town_id: Optional[int] = None
    town_name: str = ""
    county: str = ""
    population: Optional[int] = None
    square_mi: Optional[float] = None
    altitude: Optional[int] = None
    postal_code: Optional[str] = None
    office_phone: Optional[str] = None
    clerk_email: Optional[str] = None
    url: Optional[str] = None

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Town":
        def get_any(*keys, default=None):
            for k in keys:
                if k in data:
                    return data[k]
            return default

        def norm_postal(pc):
            if pc is None:
                return None
            s = str(pc).strip()
            if not s.isdigit():
                return s
            return s.zfill(5)

        def norm_phone(p):
            if p is None:
                return None
            s = re.sub(r"\D", "", str(p))
            if len(s) != 10:
                return p
            return f"{s[0:3]}-{s[3:6]}-{s[6:10]}"

        return Town(
            town_id=get_any("town_id", "Town_ID"),
            town_name=get_any("town_name", "Town_Name", default=""),
            county=get_any("county", "County", default=""),
            population=get_any("population", "Population"),
            square_mi=get_any("square_mi", "Square_MI"),
            altitude=get_any("altitude", "Altitude"),
            postal_code=norm_postal(get_any("postal_code", "Postal_Code")),
            office_phone=norm_phone(get_any("office_phone", "Office_Phone")),
            clerk_email=get_any("clerk_email", "Clerk_Email"),
            url=get_any("url", "URL"),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "town_id": self.town_id,
            "town_name": self.town_name,
            "county": self.county,
            "population": self.population,
            "square_mi": self.square_mi,
            "altitude": self.altitude,
            "postal_code": (self.postal_code.zfill(5) if isinstance(self.postal_code, str) and self.postal_code.isdigit() else self.postal_code),
            "office_phone": self.office_phone,
            "clerk_email": self.clerk_email,
            "url": self.url,
        }


