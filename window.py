# ============================================================
# DF Nav - NMEA File Simulator
# ------------------------------------------------------------
# GUI-based application for importing field geometry data,
# calculating navigation paths, and exporting NMEA simulation files.
# Integrates with 'field_calculator' and 'nmea_builder' modules.
#
# PRIMARY SOFTWARE ENTRY - RUN THIS FILE
# ============================================================

import math
import numpy as np

import field_calculator
import nmea_builder

from tkinter import *
from tkinter.ttk import Progressbar
from tkinter.filedialog import askopenfilename, asksaveasfilename

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib.patches import Polygon

from ctypes import windll

windll.shcore.SetProcessDpiAwareness(1)

# ------------------------------
# Window setup
# ------------------------------
window_root = Tk()
window_root.title('DF Nav - NMEA File Simulator')

window_frame = Frame(window_root)
window_frame.pack()

# Application icon (base64-encoded PNG)
icon_base_64 = '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'
window_root.iconphoto(True, PhotoImage(data=icon_base_64))

# Disable window resizing
window_root.resizable(False, False)

# ------------------------------
# UI Layout Frames
# ------------------------------
input_frame = Frame(window_frame)
input_frame.grid(row=0, column=1, padx=10, pady=10, sticky=N)

button_frame = Frame(input_frame)
button_frame.grid(row=0, column=0, columnspan=2)

# ------------------------------
# Field Data Defaults
# ------------------------------
# Note: first and last coordinate pairs must be identical to close the polygon
field_outer_points = [
    [0.0, 53.21071659997794],
    [35.695682164164396, 110.98553232069932],
    [121.49564841863935, 58.108774193713565],
    [86.08958639528272, 0.0],
    [0.0, 53.21071659997794]
]

field_inner_points = []   # Optional inner cutouts
field_bound_points = []   # Calculated bounding box
field_origin = [49.42631, 7.751717]
path_points = []

ab_line_angle = 31.6
field_width = 0.0
last_input_was_passes = True
hz = 10  # Simulation frequency

# ------------------------------
# Core calculation and plotting
# ------------------------------
def update_bound_and_path(*input):
    """Recalculate bounding box and navigation path based on user inputs."""
    global field_bound_points, path_points, field_width

    field_bound_points, field_width = field_calculator.create_bounding_box(
        field_outer_points,
        float(custom_direction_entry.get())
    )

    # Update path based on last changed input type
    if last_input_was_passes:
        passes_enter(suppress_update=True)
    else:
        pass_width_enter(suppress_update=True)

    path_points = field_calculator.calculate_path(
        field_bound_points,
        int(passes_entry.get()),
        float(passes_width_entry.get()),
        float(speed_entry.get()),
        float(custom_direction_entry.get()),
        hz
    )

    plot()

def angle_between(reference_vector, point_vector):
    """Calculate angle in degrees between two 2D vectors."""
    ang1 = np.arctan2(*reference_vector[::-1])
    ang2 = np.arctan2(*point_vector[::-1])
    return np.rad2deg((ang1 - ang2) % (2 * np.pi))

# ------------------------------
# Import Field Data
# ------------------------------
def import_field():
    """Load field geometry from an XML file."""
    global field_outer_points, field_inner_points, field_origin, ab_line_angle

    xml_file_path = askopenfilename(
        initialdir="/",
        title="Select Field File",
        filetypes=[("XML Files", "*.XML")]
    )

    field_outer_points, field_inner_points, field_origin, ab_line_angle = field_calculator.import_xml(xml_file_path)
    direction_option_change()
    update_bound_and_path()

import_button = Button(button_frame, text='Import XML', command=import_field)
import_button.grid(row=0, column=0, padx=25, pady=50)

# ------------------------------
# Export NMEA Path
# ------------------------------
def export_nmea(*input):
    """Save calculated path as an NMEA simulation file."""
    nmea_file_path = asksaveasfilename(
        initialfile='simulated_path',
        initialdir="/",
        title="Select NMEA File location",
        filetypes=[("NMEA Files", "*.nmea")]
    ) + '.nmea'

    nmea_builder.build_nmea(path_points, field_origin, float(speed_entry.get()), hz, nmea_file_path)

export_button = Button(button_frame, text='Export NMEA', command=export_nmea)
export_button.grid(row=0, column=1, padx=25, pady=50)

# ------------------------------
# Passes & Pass Width Inputs
# ------------------------------
def passes_enter(*input, suppress_update=False):
    """Recalculate pass width from number of passes."""
    global last_input_was_passes
    last_input_was_passes = True

    pass_width = math.ceil((field_width / int(passes_entry.get())) * 100) / 100
    passes_width_entry.delete(0, END)
    passes_width_entry.insert(0, str(pass_width))

    if not suppress_update:
        update_bound_and_path()

passes_label = Label(input_frame, text='Passes:')
passes_label.grid(row=1, column=0, padx=25, pady=10)

passes_entry = Entry(input_frame, justify='right', width=10)
passes_entry.grid(row=1, column=1, padx=25, pady=10)
passes_entry.bind("<Return>", passes_enter)
passes_entry.insert(0, '8')

def pass_width_enter(*input, suppress_update=False):
    """Recalculate number of passes from pass width."""
    global last_input_was_passes
    last_input_was_passes = False

    passes = str(int(math.ceil(field_width / float(passes_width_entry.get()))))
    passes_entry.delete(0, END)
    passes_entry.insert(0, passes)

    if not suppress_update:
        update_bound_and_path()

passes_width_label = Label(input_frame, text='Pass Width (m):')
passes_width_label.grid(row=2, column=0, padx=25, pady=10)

passes_width_entry = Entry(input_frame, justify='right', width=10)
passes_width_entry.grid(row=2, column=1, padx=25, pady=10)
passes_width_entry.bind("<Return>", pass_width_enter)
passes_width_entry.insert(0, '15.2')

# ------------------------------
# Speed Input
# ------------------------------
speed_label = Label(input_frame, text='Speed (km/h):')
speed_label.grid(row=3, column=0, padx=25, pady=10)

speed_entry = Entry(input_frame, justify='right', width=10)
speed_entry.grid(row=3, column=1, padx=25, pady=10)
speed_entry.bind("<Return>", update_bound_and_path)
speed_entry.insert(0, '30.0')

# ------------------------------
# Direction Selection
# ------------------------------
def direction_option_change(*input):
    """Update custom direction based on preset selection."""
    if direction_variable.get() == 'Custom':
        return

    custom_direction_entry.delete(0, END)
    reference_vector = [0, 1]

    mapping = {
        'AB Line': ab_line_angle,
        'North': 0,
        'East': 90,
        'South': 180,
        'West': 270
    }
    if direction_variable.get() in mapping:
        custom_direction_entry.insert(0, str(round(mapping[direction_variable.get()], 5)))
    elif direction_variable.get() == 'Side A':
        point_vector = [
            field_outer_points[1][0] - field_outer_points[0][0],
            field_outer_points[1][1] - field_outer_points[0][1]
        ]
        custom_direction_entry.insert(0, str(round(angle_between(reference_vector, point_vector), 5)))
    elif direction_variable.get() == 'Side B':
        point_vector = [
            field_outer_points[2][0] - field_outer_points[1][0],
            field_outer_points[2][1] - field_outer_points[1][1]
        ]
        custom_direction_entry.insert(0, str(round(angle_between(reference_vector, point_vector), 5)))

    update_bound_and_path()

direction_label = Label(input_frame, text='Direction:')
direction_label.grid(row=4, column=0, padx=25, pady=10)

direction_options = ['Custom', 'AB Line', 'North', 'East', 'South', 'West', 'Side A', 'Side B']
direction_variable = StringVar(input_frame)
direction_variable.set(direction_options[0])

direction_entry = OptionMenu(input_frame, direction_variable, *direction_options, command=direction_option_change)
direction_entry.config(width=8)
direction_entry.grid(row=4, column=1, padx=25, pady=10)

# ------------------------------
# Custom Direction Input
# ------------------------------
def custom_direction_enter(input):
    """Switch to custom heading mode and recalc."""
    direction_variable.set(direction_options[0])
    update_bound_and_path()

custom_direction_label = Label(input_frame, text='Heading (°N)')
custom_direction_label.grid(row=5, column=0, padx=25, pady=10)

custom_direction_entry = Entry(input_frame, justify='right', width=10)
custom_direction_entry.grid(row=5, column=1, padx=25, pady=10)
custom_direction_entry.bind("<Return>", custom_direction_enter)
custom_direction_entry.insert(0, '0')

# ------------------------------
# Application Exit Handling
# ------------------------------
def exit_call():
    """Cleanup UI before exit."""
    window_root.geometry(window_root.winfo_geometry())
    field_frame.pack_forget()
    field_frame.destroy()
    input_frame.grid_forget()
    input_frame.destroy()

    msg = Label(window_frame,
                text='\nNMEA File Simulator\n'
                     '\nRPTU Kaiserslautern\nDigital Farming\n'
                     '\nFrederick Phillips\n'
                     '\nIcon from Flaticon.com\n\n')
    msg.pack()

    pb = Progressbar(window_frame, mode="indeterminate")
    pb.pack()
    pb.start(3)
    window_root.after(800, window_root.quit)

window_root.protocol('WM_DELETE_WINDOW', exit_call)

# ------------------------------
# Plotting Setup
# ------------------------------
field_frame = Frame(window_frame)
field_frame.grid(row=0, column=0)

fig = Figure(figsize=(4.5, 4.5), dpi=100)
ax = fig.add_subplot()

canvas = FigureCanvasTkAgg(fig, master=field_frame)
canvas.get_tk_widget().pack(side=LEFT, fill=BOTH, expand=1)

def plot():
    """Render field geometry, boundaries, and navigation path."""
    ax.clear()
    ax.set(aspect='equal', box_aspect=1)
    ax.grid(linewidth=0.1)
    ax.set_xlabel('Meters East')
    ax.set_ylabel('Meters North', rotation=0)
    ax.yaxis.set_label_coords(0.0, 1.02)

    # Draw outer field
    if len(field_outer_points) > 3:
        ax.add_patch(Polygon(field_outer_points, facecolor='blue', alpha=0.5, edgecolor='None', label='Field'))

    # Draw cutout if present
    if len(field_inner_points) > 3:
        ax.add_patch(Polygon(field_inner_points, color='white'))

    # Draw bounding box
    if field_bound_points:
        ax.plot([p[0] for p in field_bound_points], [p[1] for p in field_bound_points],
                color='gray', linestyle='solid', alpha=0.5, label='Bound')

    # Draw navigation path
    if path_points:
        x_values, y_values = zip(*path_points)
        ax.plot(x_values, y_values, color='r', linestyle='dashed', label='Path')
        ax.plot(x_values[0], y_values[0], color='r', marker="o", linestyle='None')

        point_angle = -float(custom_direction_entry.get())
        if int(passes_entry.get()) % 2 == 0:
            point_angle += 180

        ax.plot(x_values[-1], y_values[-1], color='r', marker=(3, 0, point_angle), markersize=8, linestyle='None')

    canvas.draw()

    # Align X ticks to Y spacing for visual consistency
    y_spacing = ax.get_yticks()[1] - ax.get_yticks()[0]
    x_low = y_spacing * math.ceil(ax.get_xbound()[0] / y_spacing)
    x_high = y_spacing * math.ceil(ax.get_xbound()[-1] / y_spacing)
    ax.xaxis.set_ticks(np.arange(x_low, x_high, y_spacing))
    canvas.draw()

# Initial calculation and display
update_bound_and_path()

# ------------------------------
# Application main loop
# ------------------------------
window_root.mainloop()
