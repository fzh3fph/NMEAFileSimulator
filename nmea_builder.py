# ============================================================
# NMEA File Builder
# ------------------------------------------------------------
# Provides utilities to convert calculated navigation paths
# into NMEA-compliant GGA and VTG sentences for simulation.
# Depends on 'pynmea2' for message construction.
# ============================================================

import math
import numpy as np
import pynmea2
import datetime

# ------------------------------
# Main NMEA file generation
# ------------------------------
def build_nmea(path, origin, speed_kmh: float, hz: int, nmea_file_path: str):
    """
    Generate an NMEA file from a path.

    :param path: List of (x, y) points in meters relative to origin
    :param origin: [lat, lon] in degrees
    :param speed_kmh: Speed in kilometers per hour
    :param hz: Output frequency (messages per second)
    :param nmea_file_path: Destination file path
    """
    time = datetime.datetime.now()
    speed_knots = speed_kmh / 1.852
    time_step = 1 / hz

    nmea_file = ''

    path.extend(path[::-1])

    for i, point in enumerate(path):
        gga = create_gga(m_to_ll(point, origin), time.strftime("%H%M%S.%f")[:-4])
        vtg = create_vtg(
            path[max(0, i - 1)],
            path[min(len(path) - 1, i + 1)],
            speed_kmh,
            speed_knots
        )

        nmea_file += str(gga) + '\n'
        nmea_file += str(vtg) + '\n'

        time += datetime.timedelta(seconds=time_step)

    with open(nmea_file_path, 'w') as file:
        file.write(nmea_file)

# ------------------------------
# Coordinate conversion
# ------------------------------
def m_to_ll(offset_m, origin):
    """
    Convert (x, y) offsets in meters to latitude/longitude.

    :param offset_m: Offset in meters [east, north]
    :param origin: [lat, lon] origin in degrees
    :return: [lat, lon] in degrees
    """
    earth_radius_m = 6378137
    new_latitude = origin[0] + (offset_m[1] / earth_radius_m) * (180 / math.pi)
    new_longitude = origin[1] + (offset_m[0] / earth_radius_m) * (180 / math.pi) / math.cos(origin[0] * math.pi / 180)
    return [new_latitude, new_longitude]

# ------------------------------
# GGA sentence creation
# ------------------------------
def create_gga(lat_lon: list, time):
    """
    Create a GGA sentence from coordinates and UTC time.
    :param lat_lon: [lat, lon] in degrees
    :param time: UTC time string (HHMMSS.ss)
    :return: pynmea2.GGA instance
    """
    lat_h, lat_m = divmod(abs(lat_lon[0]) * 60, 60)
    lat_m = f'0{lat_m}' if lat_m < 10 else str(lat_m)
    lat_hm = f"{int(np.sign(lat_lon[0]) * lat_h)}{lat_m}"

    lon_h, lon_m = divmod(abs(lat_lon[1]) * 60, 60)
    lon_m = f'0{lon_m}' if lon_m < 10 else str(lon_m)
    lon_hm = f"{int(np.sign(lat_lon[1]) * lon_h)}{lon_m}"

    return pynmea2.GGA('GP', 'GGA', (
        str(time), lat_hm, 'N', lon_hm, 'E',
        '1', '12', '0.9', '300.00', 'M', '46.9', 'M', '', '0000'
    ))

# ------------------------------
# VTG sentence creation
# ------------------------------
def create_vtg(point_prev, point_after, speed_kmh, speed_knots):
    """
    Create a VTG sentence from two path points and speed data.
    :param point_prev: Previous path point [x, y] in meters
    :param point_after: Next path point [x, y] in meters
    :param speed_kmh: Speed in km/h
    :param speed_knots: Speed in knots
    :return: pynmea2.VTG instance
    """
    reference_vector = np.array([0, 1])
    point_vector = np.array([point_after[0] - point_prev[0],
                              point_after[1] - point_prev[1]])

    ang1 = np.arctan2(*reference_vector[::-1])
    ang2 = np.arctan2(*point_vector[::-1])
    angle = np.rad2deg((ang1 - ang2) % (2 * np.pi))

    return pynmea2.VTG('GP', 'VTG', (
        str(angle), 'T', str(angle), 'M',
        str(speed_knots), 'N', str(speed_kmh), 'K'
    ))
