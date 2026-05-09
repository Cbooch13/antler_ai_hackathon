from dataclasses import dataclass


@dataclass(frozen=True)
class IntegrationRegistry:
    socrata_enabled: bool = False
    arcgis_enabled: bool = False
    apify_enabled: bool = False
    mapbox_enabled: bool = False
    google_maps_enabled: bool = False
    autohdr_enabled: bool = False

    @classmethod
    def stage_zero(cls) -> "IntegrationRegistry":
        return cls()
