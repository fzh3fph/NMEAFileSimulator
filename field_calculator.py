# ============================================================
# Field Geometry & Path Calculation
# ------------------------------------------------------------
# Utilities for converting GPS coordinates to local metric space,
# generating bounding boxes, parsing XML field definitions, and
# producing driving paths for agricultural machinery.
# ============================================================

import math
import numpy as np
from xml.dom import minidom

# ------------------------------
# Coordinate Conversions
# ------------------------------
def ll_to_m(point_origin, point_reference):
    """
    Convert latitude/longitude points to a distance in meters.
    Uses the haversine formula for spherical distance.
    """
    lat1, lon1 = point_origin
    lat2, lon2 = point_reference

    earth_radius_km = 6378.137
    delta_lat = math.radians(lat2) - math.radians(lat1)
    delta_lon = math.radians(lon2) - math.radians(lon1)

    a = math.sin(delta_lat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(delta_lon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return earth_radius_km * c * 1000.0

# ------------------------------
# Geometric Transformations
# ------------------------------
def rotate_point(point, angle):
    """Rotate a point (x, y) by a given angle (radians)."""
    x, y = point
    return x * np.cos(angle) + y * np.sin(angle), -x * np.sin(angle) + y * np.cos(angle)

def find_center(points):
    """Return the centroid of a list of (x, y) points."""
    x_coords, y_coords = zip(*points)
    return sum(x_coords) / len(points), sum(y_coords) / len(points)

def translate_point(point, translation):
    """Translate a point by a (tx, ty) vector."""
    x, y = point
    tx, ty = translation
    return x - tx, y - ty

# ------------------------------
# Bounding Box Creation
# ------------------------------
def create_bounding_box(points, angle):
    """
    Compute a bounding box for a rotated set of points.
    Returns the bounding box vertices and the calculated width.
    """
    alpha = np.radians(-angle)
    center = find_center(points)

    rotated_points = [translate_point(p, center) for p in points]
    rotated_points = [rotate_point(p, alpha) for p in rotated_points]
    rotated_points = [translate_point(p, (-center[0], -center[1])) for p in rotated_points]

    min_x = min(p[0] for p in rotated_points)
    max_x = max(p[0] for p in rotated_points)
    min_y = min(p[1] for p in rotated_points)
    max_y = max(p[1] for p in rotated_points)

    bounding_box = [(min_x, min_y), (max_x, min_y), (max_x, max_y), (min_x, max_y), (min_x, min_y)]
    field_width = max_x - min_x

    bounding_box = [translate_point(p, center) for p in bounding_box]
    bounding_box = [rotate_point(p, -alpha) for p in bounding_box]
    bounding_box = [translate_point(p, (-center[0], -center[1])) for p in bounding_box]

    return bounding_box, field_width

# ------------------------------
# XML Import
# ------------------------------
def import_xml(xml_file_path: str):
    """
    Parse an XML field definition and return:
    - outer boundary points
    - inner boundary points
    - origin coordinates
    - AB line angle (if defined)
    """
    field_outer_points, field_inner_points = [], []

    xml_file = minidom.parse(xml_file_path)
    xml_points = xml_file.getElementsByTagName('PNT')

    xml_outer_points_list, xml_inner_points_list, xml_ab_points_list = [], [], []
    for point in xml_points:
        a_value = point.parentNode.attributes['A'].value
        coords = [float(point.attributes['C'].value), float(point.attributes['D'].value)]
        if a_value == '1':
            xml_outer_points_list.append(coords)
        elif a_value == '2':
            xml_inner_points_list.append(coords)
        elif a_value == '5':
            xml_ab_points_list.append(coords)

    # Determine origin based on bounding box of outer points
    xml_max_coords = [-1000.0, -1000.0]
    xml_min_coords = [1000.0, 1000.0]
    for point in xml_outer_points_list:
        xml_max_coords = [max(xml_max_coords[0], point[0]), max(xml_max_coords[1], point[1])]
        xml_min_coords = [min(xml_min_coords[0], point[0]), min(xml_min_coords[1], point[1])]
    xml_origin = xml_min_coords

    # Convert outer and inner points to local metric space
    for point in xml_outer_points_list:
        x = ll_to_m(xml_origin, [xml_origin[0], point[1]])
        y = ll_to_m(xml_origin, [point[0], xml_origin[1]])
        field_outer_points.append([x, y])

    if xml_inner_points_list:
        for point in xml_inner_points_list:
            x = ll_to_m(xml_origin, [xml_origin[0], point[1]])
            y = ll_to_m(xml_origin, [point[0], xml_origin[1]])
            field_inner_points.append([x, y])

    # Calculate AB line angle if present
    ab_line_angle = 0
    if len(xml_ab_points_list) > 1:
        ab_x = ll_to_m(xml_ab_points_list[0], [xml_ab_points_list[0][0], xml_ab_points_list[1][1]])
        ab_y = ll_to_m(xml_ab_points_list[0], [xml_ab_points_list[1][0], xml_ab_points_list[0][1]])
        reference_vector = np.array([0, 1])
        ab_vector = np.array([ab_x, ab_y])
        ang1 = np.arctan2(*reference_vector[::-1])
        ang2 = np.arctan2(*ab_vector[::-1])
        ab_line_angle = np.rad2deg((ang1 - ang2) % (2 * np.pi))

    return field_outer_points, field_inner_points, xml_origin, ab_line_angle

# ------------------------------
# Path Calculation
# ------------------------------
def calculate_path(bound_points, passes: int, pass_width: float, speed_kmh: float, angle: float, hz: int):
    """
    Generate a list of path points within the field bounds.
    Supports alternating passes with curved turnarounds.
    """
    path_points = []
    speed_ms = speed_kmh / 3.6
    meters_per_step = speed_ms / hz

    alpha = np.radians(-angle)
    center = find_center(bound_points)

    rotated_bounds = [translate_point(p, center) for p in bound_points]
    rotated_bounds = [rotate_point(p, alpha) for p in rotated_bounds]
    corner_center_coords = rotated_bounds[0]
    rotated_bounds = [translate_point(p, corner_center_coords) for p in rotated_bounds]

    field_length = rotated_bounds[3][1]
    max_distance = (field_length * passes) + ((math.pi * pass_width / 2) * (passes - 1))

    distance_traveled = 0.0
    while distance_traveled < max_distance:
        path_points.append(path_function(distance_traveled, field_length, pass_width))
        distance_traveled += meters_per_step

    # Transform back to original coordinates
    path_points = [translate_point(p, (-corner_center_coords[0], -corner_center_coords[1])) for p in path_points]
    path_points = [rotate_point(p, -alpha) for p in path_points]
    path_points = [translate_point(p, (-center[0], -center[1])) for p in path_points]

    return path_points

# ------------------------------
# Turn Geometry
# ------------------------------
def circle_coordinates_from_distance(distance: float, radius: float):
    """Return (x, y) coordinates along a circle given arc distance."""
    angle = distance / radius
    return radius * math.sin(angle), radius * (1 - math.cos(angle))

# ------------------------------
# Path Progression
# ------------------------------
def path_function(distance_traveled: float, field_length: float, pass_width: float):
    """
    Determine current position along a back-and-forth path
    with semi-circular turnarounds.
    """
    distance_passed = 0
    lengths_passed = 0
    circles_passed = 0

    while True:
        # Straight pass
        if distance_traveled <= distance_passed + field_length:
            current_length_pass = lengths_passed + 1
            result_position = [(current_length_pass - 1) * pass_width + (pass_width / 2), 0]

            if current_length_pass % 2 == 1:
                # Upward pass
                result_position[1] = distance_traveled - distance_passed
            else:
                # Downward pass
                result_position[1] = field_length - (distance_traveled - distance_passed)

            return result_position

        lengths_passed += 1
        distance_passed += field_length

        # Semi-circular turnaround
        if distance_traveled <= distance_passed + math.pi * pass_width / 2:
            current_circle_pass = circles_passed + 1
            distance_in_circle = distance_traveled - distance_passed
            circle_coords = circle_coordinates_from_distance(distance_in_circle, pass_width / 2)
            passes_end_position = [(lengths_passed - 1) * pass_width + (pass_width / 2), 0]

            if current_circle_pass % 2 == 1:
                # Turn at far end
                passes_end_position[1] = field_length
                return [passes_end_position[0] + circle_coords[1],
                        passes_end_position[1] + circle_coords[0]]
            else:
                # Turn at near end
                passes_end_position[1] = 0
                return [passes_end_position[0] + circle_coords[1],
                        passes_end_position[1] - circle_coords[0]]

        circles_passed += 1
        distance_passed += math.pi * pass_width / 2
