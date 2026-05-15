"""Extract EXIF metadata from a JPEG: date, GPS, camera model."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from PIL import Image, ExifTags

_DATE_FMT = "%Y:%m:%d %H:%M:%S"


@dataclass(frozen=True)
class ExifData:
    date: Optional[datetime]
    lat: Optional[float]
    lon: Optional[float]
    camera: Optional[str]

    @property
    def is_usable(self) -> bool:
        """A photo is processable when it has date AND GPS."""
        return self.date is not None and self.lat is not None and self.lon is not None


def _dms_to_decimal(dms: tuple, ref: str) -> float:
    deg, minutes, seconds = dms
    value = float(deg) + float(minutes) / 60.0 + float(seconds) / 3600.0
    if ref in ("S", "W"):
        value = -value
    return value


def extract(path: Path) -> Optional[ExifData]:
    """Return an ExifData for `path`, or None if the file has no EXIF at all."""
    with Image.open(path) as img:
        raw = img.getexif()
        if not raw:
            return None

        # Resolve tag IDs to names so we can read by name.
        tags = {ExifTags.TAGS.get(t, t): v for t, v in raw.items()}

        date = None
        raw_date = raw.get_ifd(ExifTags.IFD.Exif).get(ExifTags.Base.DateTimeOriginal)
        if raw_date:
            try:
                date = datetime.strptime(raw_date, _DATE_FMT)
            except (ValueError, TypeError):
                date = None

        camera = tags.get("Model")
        if isinstance(camera, bytes):
            camera = camera.decode("ascii", errors="replace").strip("\x00").strip()

        lat = lon = None
        gps = raw.get_ifd(ExifTags.IFD.GPSInfo)
        if gps:
            gps_named = {ExifTags.GPSTAGS.get(t, t): v for t, v in gps.items()}
            if all(k in gps_named for k in ("GPSLatitude", "GPSLatitudeRef",
                                            "GPSLongitude", "GPSLongitudeRef")):
                lat = _dms_to_decimal(gps_named["GPSLatitude"], gps_named["GPSLatitudeRef"])
                lon = _dms_to_decimal(gps_named["GPSLongitude"], gps_named["GPSLongitudeRef"])

    return ExifData(date=date, lat=lat, lon=lon, camera=camera)
