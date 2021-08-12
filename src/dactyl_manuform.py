import numpy as np
from numpy import pi
import os.path as path
import json
import os

from scipy.spatial import ConvexHull as sphull

def deg2rad(degrees: float) -> float:
    return degrees * pi / 180


def rad2deg(rad: float) -> float:
    return rad * 180 / pi


###############################################
# EXTREMELY UGLY BUT FUNCTIONAL BOOTSTRAP
###############################################

## IMPORT DEFAULT CONFIG IN CASE NEW PARAMETERS EXIST
import generate_configuration as cfg
for item in cfg.shape_config:
    locals()[item] = cfg.shape_config[item]

## LOAD RUN CONFIGURATION FILE AND WRITE TO ANY VARIABLES IN FILE.
with open('run_config.json', mode='r') as fid:
    data = json.load(fid)
for item in data:
    locals()[item] = data[item]

# Really rough setup.  Check for ENGINE, set it not present from configuration.
try:
    print('Found Current Engine in Config = {}'.format(ENGINE))
except Exception:
    print('Engine Not Found in Config')
    ENGINE = 'solid'
    # ENGINE = 'cadquery'
    print('Setting Current Engine = {}'.format(ENGINE))

if save_dir in ['', None, '.']:
    save_path = os.path.join(r"..", "things")
else:
    save_path = os.path.join(r"..", "things", save_dir)

###############################################
# END EXTREMELY UGLY BOOTSTRAP
###############################################

####################################################
# HELPER FUNCTIONS TO MERGE CADQUERY AND OPENSCAD
####################################################

if ENGINE == 'cadquery':
    from helpers_cadquery import *
else:
    from helpers_solid import *

####################################################
# END HELPER FUNCTIONS
####################################################


debug_exports = True
debug_trace = False

def debugprint(info):
    if debug_trace:
        print(info)

def use_joystick():
    return joystick is not None and joystick != "NONE"

def use_oled():
    return oled_mount_type is not None and oled_mount_type != "NONE"

def use_pcb():
    return pcb is not None and pcb != "NONE"

if oled_mount_type is not None and oled_mount_type != "NONE":
    for item in oled_configurations[oled_mount_type]:
        locals()[item] = oled_configurations[oled_mount_type][item]

if nrows > 5:
    column_style = column_style_gt5

centerrow = nrows - centerrow_offset

lastrow = nrows - 1
cornerrow = lastrow - 1
lastcol = ncols - 1


# Derived values
if plate_style in ['NUB', 'HS_NUB']:
    keyswitch_height = nub_keyswitch_height
    keyswitch_width = nub_keyswitch_width
elif plate_style in ['UNDERCUT', 'HS_UNDERCUT', 'NOTCH', 'HS_NOTCH']:
    keyswitch_height = undercut_keyswitch_height
    keyswitch_width = undercut_keyswitch_width
else:
    keyswitch_height = hole_keyswitch_height
    keyswitch_width = hole_keyswitch_width

if 'HS_' in plate_style:
    symmetry = "asymmetric"
    plate_file = path.join("..", "src", r"hot_swap_plate")
    plate_offset = 0.0

mount_width = keyswitch_width + 2 * plate_rim
mount_height = keyswitch_height + 2 * plate_rim
mount_thickness = plate_thickness

if default_1U_cluster:
    double_plate_height = (.7*sa_double_length - mount_height) / 3
else:
    double_plate_height = (.95*sa_double_length - mount_height) / 3

if oled_mount_type is not None and oled_mount_type != "NONE" and not use_joystick():
    left_wall_x_offset = oled_left_wall_x_offset_override
    left_wall_z_offset = oled_left_wall_z_offset_override
    left_wall_lower_y_offset = oled_left_wall_lower_y_offset
    left_wall_lower_z_offset = oled_left_wall_lower_z_offset

cap_top_height = plate_thickness + sa_profile_key_height
row_radius = ((mount_height + extra_height) / 2) / (np.sin(alpha / 2)) + cap_top_height
column_radius = (
                        ((mount_width + extra_width) / 2) / (np.sin(beta / 2))
                ) + cap_top_height
column_x_delta = -1 - column_radius * np.sin(beta)
column_base_angle = beta * (centercol - 2)




teensy_width = 20
teensy_height = 12
teensy_length = 33
teensy2_length = 53
teensy_pcb_thickness = 2
teensy_offset_height = 5
teensy_holder_top_length = 18
teensy_holder_width = 7 + teensy_pcb_thickness
teensy_holder_height = 6 + teensy_width



wire_post_height = 7
wire_post_overhang = 3.5
wire_post_diameter = 2.6

screw_insert_height = 3.8
screw_insert_bottom_radius = 5.31 / 2
screw_insert_top_radius = 5.1 / 2


# save_path = path.join("..", "things", save_dir)
if not path.isdir(save_path):
    os.mkdir(save_path)


def column_offset(column: int) -> list:
    return column_offsets[column]

# column_style='fixed'

if use_pcb():
    pcb_shape = translate(import_file(path.join("..", "src", pcb)), [0, 0, -1.6])

def pcb_clearance_shape(pcb_screw="right"):
    shape = translate(box(19.2, 19.2, 3), [0, 0, -1.6])

    if pcb_screw == "right":
        shape = union([
            shape,
            translate(cylinder(radius=1.1, height=2.5), [9.398, (-2.191 + 0.349) / 2, 0]),
            translate(cylinder(radius=4.7/2, height=5), [9.398, (-2.191 + 0.349) / 2, -5])
        ])
        shape = difference(shape, [
            translate(cylinder(radius=2.4, height=2), [-9.398, (-2.191 + 0.349) / 2, -2])
        ])
    else:
        shape = union([
            shape,
            translate(cylinder(radius=1.1, height=2.5), [-9.398, (-2.191 + 0.349) / 2, 0]),
            translate(cylinder(radius=4.7/2, height=5), [-9.398, (-2.191 + 0.349) / 2, -5])
        ])
        shape = difference(shape, [
            translate(cylinder(radius=2.4, height=2), [9.398, (-2.191 + 0.349) / 2, -2])
        ])

    return shape


def single_plate(cylinder_segments=100, side="right", pcb_screw="right", high_left=False, high_right=False):

    if plate_style in ['NUB', 'HS_NUB']:
        top_wall = box(mount_width, 1.5, plate_thickness)
        top_wall = translate(top_wall, (0, (1.5 / 2) + (keyswitch_height / 2), plate_thickness / 2))

        left_wall = box(1.5, mount_height, plate_thickness)
        left_wall = translate(left_wall, ((1.5 / 2) + (keyswitch_width / 2), 0, plate_thickness / 2))

        side_nub = cylinder(radius=1, height=2.75)
        side_nub = translate(side_nub, (0, 0, -2.75 / 2.0))
        side_nub = rotate(side_nub, (90, 0, 0))
        side_nub = translate(side_nub, (keyswitch_width / 2, 0, 1))
        nub_cube = box(1.5, 2.75, plate_thickness)
        nub_cube = translate(nub_cube, ((1.5 / 2) + (keyswitch_width / 2), 0, plate_thickness / 2))

        side_nub2 = tess_hull(shapes=(side_nub, nub_cube))
        side_nub2 = union([side_nub2, side_nub, nub_cube])

        plate_half1 = union([top_wall, left_wall, side_nub2])
        plate_half2 = plate_half1
        plate_half2 = mirror(plate_half2, 'XZ')
        plate_half2 = mirror(plate_half2, 'YZ')

        plate = union([plate_half1, plate_half2])

    else:  # 'HOLE' or default, square cutout for non-nub designs.
        plate = box(mount_width, mount_height, mount_thickness)
        plate = translate(plate, (0.0, 0.0, mount_thickness / 2.0))

        shape_cut = box(keyswitch_width, keyswitch_height, mount_thickness * 2 +.02)
        shape_cut = translate(shape_cut, (0.0, 0.0, mount_thickness-.01))

        plate = difference(plate, [shape_cut])

    if plate_style in ['UNDERCUT', 'HS_UNDERCUT', 'NOTCH', 'HS_NOTCH']:
        if plate_style in ['UNDERCUT', 'HS_UNDERCUT']:
            undercut = box(
                keyswitch_width + 2 * clip_undercut,
                keyswitch_height + 2 * clip_undercut,
                mount_thickness
            )

        if plate_style in ['NOTCH', 'HS_NOTCH']:
            undercut = box(
                notch_width,
                keyswitch_height + 2 * clip_undercut,
                mount_thickness
            )
            #undercut = union([undercut,
            #    box(
            #        keyswitch_width + 2 * clip_undercut,
            #        notch_width,
            #        mount_thickness
            #    )
            #])

        undercut = translate(undercut, (0.0, 0.0, -clip_thickness + mount_thickness / 2.0))

        if ENGINE=='cadquery' and undercut_transition > 0:
            undercut = undercut.faces("+Z").chamfer(undercut_transition, clip_undercut)

        plate = difference(plate, [undercut])

    if plate_file is not None:
        socket = import_file(plate_file)
        socket = translate(socket, [0, 0, plate_thickness + plate_offset])
        plate = union([plate, socket])


    if plate_holes:
        half_width = plate_holes_width/2.
        half_height = plate_holes_height/2.
        x_off = plate_holes_xy_offset[0]
        y_off = plate_holes_xy_offset[1]
        holes = [
            translate(
                cylinder(radius=plate_holes_diameter/2, height=plate_holes_depth+.01),
                (x_off+half_width, y_off+half_height, plate_holes_depth/2-.01)
            ),
            translate(
                cylinder(radius=plate_holes_diameter / 2, height=plate_holes_depth+.01),
                (x_off-half_width, y_off+half_height, plate_holes_depth/2-.01)
            ),
            translate(
                cylinder(radius=plate_holes_diameter / 2, height=plate_holes_depth+.01),
                (x_off-half_width, y_off-half_height, plate_holes_depth/2-.01)
            ),
            translate(
                cylinder(radius=plate_holes_diameter / 2, height=plate_holes_depth+.01),
                (x_off+half_width, y_off-half_height, plate_holes_depth/2-.01)
            ),
        ]
        plate = difference(plate, holes)

    if side == "left":
        plate = mirror(plate, 'YZ')

    if use_pcb():
        if high_left:
            barrel_height = 0.5
        else:
            barrel_height = 2.5
        if high_right:
            post_height = 3
        else:
            post_height = 5
            
        screw_barrel = cylinder(radius=1.1 + 1.2, height=barrel_height)
        pcb_post = cylinder(radius=2.4/2, height=post_height)
        if pcb_screw == "right":
            #screw_barrel = difference(screw_barrel, [translate(box(1.1 + 1.2, 2 * (1.1 + 1.2), 1.0), [(1.1 + 1.2 + 0.5), 0, -1.0/2 + 2.5])])
            #pcb_post = difference(pcb_post, [translate(box(2.4/2, 2.4, 1.0), [-2.4/4, 0, -1.0/2 + 5])])
            plate = union([plate,
                           translate(pcb_post, [-9.398, (-2.191 + 0.349) / 2, -2]),
                           translate(screw_barrel, [9.398, (-2.191 + 0.349) / 2, 0]),
            ])
        else:
            #screw_barrel = difference(screw_barrel, [translate(box(1.1 + 1.2, 2 * (1.1 + 1.2), 1.0), [-(1.1 + 1.2 + 0.5), 0, -1.0/2 + 2.5])])
            #pcb_post = difference(pcb_post, [translate(box(2.4/2, 2.4, 1.0), [2.4/4, 0, -1.0/2 + 5])])
            plate = union([plate,
                           translate(pcb_post, [9.398, (-2.191 + 0.349) / 2, -2]),
                           translate(screw_barrel, [-9.398, (-2.191 + 0.349) / 2, 0]),
            ])            
        
    return plate

def pcb_post_clip(shape):
    return difference(shape, [rotate(
        translate(
            translate(box(2.4/2, 2.4, 1.5), [-2.4/4 - 0.1, 0, -1.5/2 + 5]),
            [-9.398, (-2.191 + 0.349) / 2, -2]), [0, 0, -90])
    ])

################
## SA Keycaps ##
################




def sa_cap(Usize=1):
    # MODIFIED TO NOT HAVE THE ROTATION.  NEEDS ROTATION DURING ASSEMBLY
    sa_length = 18.25

    if Usize == 1:
        bl2 = 18.5/2
        bw2 = 18.5/2
        m = 17 / 2
        pl2 = 6
        pw2 = 6

    elif Usize == 2:
        bl2 = sa_length
        bw2 = sa_length / 2
        m = 0
        pl2 = 16
        pw2 = 6

    elif Usize == 1.5:
        bl2 = sa_length / 2
        bw2 = 27.94 / 2
        m = 0
        pl2 = 6
        pw2 = 11

    k1 = polyline([(bw2, bl2), (bw2, -bl2), (-bw2, -bl2), (-bw2, bl2), (bw2, bl2)])
    k1 = extrude_poly(outer_poly=k1, height=0.1)
    k1 = translate(k1, (0, 0, 0.05))
    k2 = polyline([(pw2, pl2), (pw2, -pl2), (-pw2, -pl2), (-pw2, pl2), (pw2, pl2)])
    k2 = extrude_poly(outer_poly=k2, height=0.1)
    k2 = translate(k2, (0, 0, 12.0))
    if m > 0:
        m1 = polyline([(m, m), (m, -m), (-m, -m), (-m, m), (m, m)])
        # m1 = cq.Wire.assembleEdges(m1.edges().objects)
        m1 = extrude_poly(outer_poly=m1, height=0.1)
        m1 = translate(m1, (0, 0, 6.0))
        key_cap = hull_from_shapes((k1, k2, m1))
    else:
        key_cap = hull_from_shapes((k1, k2))

    key_cap = translate(key_cap, (0, 0, 5 + plate_thickness))
    # key_cap = key_cap.color((220 / 255, 163 / 255, 163 / 255, 1))

    return key_cap


#########################
## Placement Functions ##
#########################


def rotate_around_x(position, angle):
    # debugprint('rotate_around_x()')
    t_matrix = np.array(
        [
            [1, 0, 0],
            [0, np.cos(angle), -np.sin(angle)],
            [0, np.sin(angle), np.cos(angle)],
        ]
    )
    return np.matmul(t_matrix, position)


def rotate_around_y(position, angle):
    # debugprint('rotate_around_y()')
    t_matrix = np.array(
        [
            [np.cos(angle), 0, np.sin(angle)],
            [0, 1, 0],
            [-np.sin(angle), 0, np.cos(angle)],
        ]
    )
    return np.matmul(t_matrix, position)




def apply_key_geometry(
        shape,
        translate_fn,
        rotate_x_fn,
        rotate_y_fn,
        column,
        row,
        column_style=column_style,
):

    debugprint('apply_key_geometry()')

    column_angle = beta * (centercol - column)

    if column_style == "orthographic":
        column_z_delta = column_radius * (1 - np.cos(column_angle))
        shape = translate_fn(shape, [0, 0, -row_radius])
        shape = rotate_x_fn(shape, alpha * (centerrow - row))
        shape = translate_fn(shape, [0, 0, row_radius])
        shape = rotate_y_fn(shape, column_angle)
        shape = translate_fn(
            shape, [-(column - centercol) * column_x_delta, 0, column_z_delta]
        )
        shape = translate_fn(shape, column_offset(column))

    elif column_style == "fixed":
        shape = rotate_y_fn(shape, fixed_angles[column])
        shape = translate_fn(shape, [fixed_x[column], 0, fixed_z[column]])
        shape = translate_fn(shape, [0, 0, -(row_radius + fixed_z[column])])
        shape = rotate_x_fn(shape, alpha * (centerrow - row))
        shape = translate_fn(shape, [0, 0, row_radius + fixed_z[column]])
        shape = rotate_y_fn(shape, fixed_tenting)
        shape = translate_fn(shape, [0, column_offset(column)[1], 0])

    else:
        shape = translate_fn(shape, [0, 0, -row_radius])
        shape = rotate_x_fn(shape, alpha * (centerrow - row))
        shape = translate_fn(shape, [0, 0, row_radius])
        shape = translate_fn(shape, [0, 0, -column_radius])
        shape = rotate_y_fn(shape, column_angle)
        shape = translate_fn(shape, [0, 0, column_radius])
        shape = translate_fn(shape, column_offset(column))

    shape = rotate_y_fn(shape, tenting_angle)
    shape = translate_fn(shape, [0, 0, keyboard_z_offset])

    return shape


def x_rot(shape, angle):
    # debugprint('x_rot()')
    return rotate(shape, [rad2deg(angle), 0, 0])


def y_rot(shape, angle):
    # debugprint('y_rot()')
    return rotate(shape, [0, rad2deg(angle), 0])


def key_place(shape, column, row):
    debugprint('key_place()')
    return apply_key_geometry(shape, translate, x_rot, y_rot, column, row)


def add_translate(shape, xyz):
    debugprint('add_translate()')
    vals = []
    for i in range(len(shape)):
        vals.append(shape[i] + xyz[i])
    return vals


def key_position(position, column, row):
    debugprint('key_position()')
    return apply_key_geometry(
        position, add_translate, rotate_around_x, rotate_around_y, column, row
    )


def key_holes(side="right"):
    debugprint('key_holes()')
    # hole = single_plate()
    holes = []
    clearances = []
    for column in range(ncols):
        for row in range(nrows):
            if (column in [2, 3]) or (not row == lastrow):
                if column == ncols - 1:
                    pcb_screw = "left"
                else:
                    pcb_screw = "right"
                high_left = column in [1, 4]
                high_right = column in [3]
                holes.append(key_place(single_plate(side=side, pcb_screw=pcb_screw, high_left=high_left, high_right=high_right), column, row))
                clearances.append(key_place(pcb_clearance_shape(pcb_screw=pcb_screw), column, row))

    shape = union(holes)
    clearance = union(clearances)

    return (shape, clearance)


def caps():
    caps = None
    for column in range(ncols):
        for row in range(nrows):
            if (column in [2, 3]) or (not row == lastrow):
                if caps is None:
                    caps = key_place(sa_cap(), column, row)
                else:
                    caps = add([caps, key_place(sa_cap(), column, row)])

    return caps


####################
## Web Connectors ##
####################



def web_post():
    debugprint('web_post()')
    post = box(post_size, post_size, web_thickness)
    post = translate(post, (0, 0, plate_thickness - (web_thickness / 2)))
    return post


def web_post_tr(wide=False):
    if wide:
        w_divide = 1.2
    else:
        w_divide = 2.0

    return translate(web_post(), ((mount_width / w_divide) - post_adj, (mount_height / 2) - post_adj, 0))


def web_post_tl(wide=False):
    if wide:
        w_divide = 1.2
    else:
        w_divide = 2.0
    return translate(web_post(), (-(mount_width / w_divide) + post_adj, (mount_height / 2) - post_adj, 0))


def web_post_bl(wide=False):
    if wide:
        w_divide = 1.2
    else:
        w_divide = 2.0
    return translate(web_post(), (-(mount_width / w_divide) + post_adj, -(mount_height / 2) + post_adj, 0))


def web_post_br(wide=False):
    if wide:
        w_divide = 1.2
    else:
        w_divide = 2.0
    return translate(web_post(), ((mount_width / w_divide) - post_adj, -(mount_height / 2) + post_adj, 0))



def connectors():
    debugprint('connectors()')
    hulls = []
    for column in range(ncols - 1):
        for row in range(lastrow):  # need to consider last_row?
            # for row in range(nrows):  # need to consider last_row?
            places = []
            places.append(key_place(web_post_tl(), column + 1, row))
            places.append(key_place(web_post_tr(), column, row))
            places.append(key_place(web_post_bl(), column + 1, row))
            places.append(key_place(web_post_br(), column, row))
            hulls.append(triangle_hulls(places))

    for column in range(ncols):
        # for row in range(nrows-1):
        for row in range(cornerrow):
            places = []
            places.append(key_place(web_post_bl(), column, row))
            places.append(key_place(web_post_br(), column, row))
            places.append(key_place(web_post_tl(), column, row + 1))
            places.append(key_place(web_post_tr(), column, row + 1))
            hulls.append(triangle_hulls(places))

    for column in range(ncols - 1):
        # for row in range(nrows-1):  # need to consider last_row?
        for row in range(cornerrow):  # need to consider last_row?
            places = []
            places.append(key_place(web_post_br(), column, row))
            places.append(key_place(web_post_tr(), column, row + 1))
            places.append(key_place(web_post_bl(), column + 1, row))
            places.append(key_place(web_post_tl(), column + 1, row + 1))
            hulls.append(triangle_hulls(places))
            
    return union(hulls)


############
## Thumbs ##
############


def thumborigin():
    # debugprint('thumborigin()')
    origin = key_position([mount_width / 2, -(mount_height / 2), 0], 1, cornerrow)
    for i in range(len(origin)):
        origin[i] = origin[i] + thumb_offsets[i]
    return origin


def thumb_tr_place(shape):
    debugprint('thumb_tr_place()')
    shape = rotate(shape, [10, -15, 10])
    shape = translate(shape, thumborigin())
    shape = translate(shape, [-13, -16, 3])
    return shape


def thumb_tl_place(shape):
    debugprint('thumb_tl_place()')
    shape = rotate(shape, [7.5, -18, 10])
    shape = translate(shape, thumborigin())
    shape = translate(shape, [-32.5, -14.5, -2.5])
    return shape


def thumb_mr_place(shape):
    debugprint('thumb_mr_place()')
    shape = rotate(shape, [-6, -34, 48])
    shape = translate(shape, thumborigin())
    shape = translate(shape, [-31, -37, -13])
    return shape


def thumb_ml_place(shape):
    debugprint('thumb_ml_place()')
    shape = rotate(shape, [6, -34, 40])
    shape = translate(shape, thumborigin())
    shape = translate(shape, [-51, -23, -12])
    return shape


def thumb_br_place(shape):
    debugprint('thumb_br_place()')
    shape = rotate(shape, [-16, -33, 54])
    shape = translate(shape, thumborigin())
    shape = translate(shape, [-37.8, -55.3, -25.3])
    return shape


def thumb_bl_place(shape):
    debugprint('thumb_bl_place()')
    shape = rotate(shape, [-4, -35, 52])
    shape = translate(shape, thumborigin())
    shape = translate(shape, [-56.3, -43.3, -23.5])
    return shape


def thumb_1x_layout(shape, cap=False):
    debugprint('thumb_1x_layout()')
    
    if cap:
        shape_list = [
            thumb_mr_place(rotate(shape, [0, 0, thumb_plate_mr_rotation])),
            thumb_ml_place(rotate(shape, [0, 0, thumb_plate_ml_rotation])),
            thumb_br_place(rotate(shape, [0, 0, thumb_plate_br_rotation])),
            #thumb_bl_place(rotate(mirror(pcb_post_clip(shape), "XZ"), [0, 0, thumb_plate_bl_rotation])),
            thumb_bl_place(rotate(shape, [0, 0, thumb_plate_bl_rotation])),
        ]

        if default_1U_cluster:
            #shape = mirror(shape, 'XZ')
            #shape_list.append(thumb_tr_place(rotate(rotate(shape, (0, 0, 90)), [0, 0, thumb_plate_tr_rotation])))
            shape_list.append(thumb_tr_place(rotate(shape, [0, 0, thumb_plate_tr_rotation])))
            shape_list.append(thumb_tl_place(rotate(shape, [0, 0, thumb_plate_tl_rotation])))
        shapes = add(shape_list)

    else:
        shape_list = [
                thumb_mr_place(rotate(shape, [0, 0, thumb_plate_mr_rotation])),
                thumb_ml_place(rotate(shape, [0, 0, thumb_plate_ml_rotation])),
                thumb_br_place(rotate(shape, [0, 0, thumb_plate_br_rotation])),
                #thumb_bl_place(rotate(mirror(pcb_post_clip(shape), "XZ"), [0, 0, thumb_plate_bl_rotation])),
                thumb_bl_place(rotate(shape, [0, 0, thumb_plate_bl_rotation])),
            ]
        if default_1U_cluster:
            #shape = mirror(shape, 'XZ')
            #shape_list.append(thumb_tr_place(rotate(rotate(shape, (0, 0, 90)), [0, 0, thumb_plate_tr_rotation])))
            shape_list.append(thumb_tr_place(rotate(shape, [0, 0, thumb_plate_tr_rotation])))
            shape_list.append(thumb_tl_place(rotate(shape, [0, 0, thumb_plate_tl_rotation])))

        shapes = union(shape_list)
    return shapes


def thumb_15x_layout(shape, cap=False, plate=True):
    debugprint('thumb_15x_layout()')
    if plate:
        if cap:
            shape = rotate(shape, (0, 0, 90))
            cap_list = [thumb_tl_place(rotate(shape, [0, 0, thumb_plate_tl_rotation]))]
            cap_list.append(thumb_tr_place(rotate(shape, [0, 0, thumb_plate_tr_rotation])))
            return add(cap_list)
        else:
            shape_list = [thumb_tl_place(rotate(shape, [0, 0, thumb_plate_tl_rotation]))]
            if not default_1U_cluster:
                shape_list.append(thumb_tr_place(rotate(shape, [0, 0, thumb_plate_tr_rotation])))
            return union(shape_list)
    else:
        if cap:
            shape = rotate(shape, (0, 0, 90))
            shape_list = [
                thumb_tl_place(shape),
            ]
            shape_list.append(thumb_tr_place(shape))

            return add(shape_list)
        else:
            shape_list = [
                thumb_tl_place(shape),
            ]
            if not default_1U_cluster:
                shape_list.append(thumb_tr_place(shape))

            return union(shape_list)



def double_plate_half():
    debugprint('double_plate()')
    top_plate = box(mount_width, double_plate_height, web_thickness)
    top_plate = translate(top_plate,
                          [0, (double_plate_height + mount_height) / 2, plate_thickness - (web_thickness / 2)]
                          )
    return top_plate

def double_plate():
    debugprint('double_plate()')
    top_plate = double_plate_half()
    return union((top_plate, mirror(top_plate, 'XZ')))


def thumbcaps():
    if thumb_style == "MINI":
        return mini_thumbcaps()
    elif thumb_style == "CARBONFET":
        return carbonfet_thumbcaps()
    else:
        return default_thumbcaps()


def thumb(side="right"):
    if thumb_style == "MINI":
        return mini_thumb(side)
    elif thumb_style == "CARBONFET":
        return carbonfet_thumb(side)
    else:
        return default_thumb(side)


def thumb_connectors():
    if thumb_style == "MINI":
        return mini_thumb_connectors()
    elif thumb_style == "CARBONFET":
        return carbonfet_thumb_connectors()
    else:
        return default_thumb_connectors()


def default_thumbcaps():
    t1 = thumb_1x_layout(sa_cap(1), cap=True)
    if not default_1U_cluster:
        t1.add(thumb_15x_layout(sa_cap(1.5), cap=True))
    return t1


def default_thumb(side="right"):
    print('thumb()')
    shape = thumb_1x_layout(rotate(single_plate(side=side, pcb_screw="left", high_right=True), (0, 0, -90)))
    clearance = thumb_1x_layout(rotate(pcb_clearance_shape(pcb_screw="left"), (0, 0, -90)))
    if not default_1U_cluster:
        shape = union([shape, thumb_15x_layout(rotate(single_plate(side=side), (0, 0, -90)))])
        clearance = union([clearance, thumb_15x_layout(rotate(pcb_clearance_shape(), (0, 0, -90)))])
        shape = union([shape, thumb_15x_layout(double_plate(), plate=False)])
    #clearance = union([clearance, thumb_15x_layout(pcb_clearance_shape(), plate=False)])

    export_file(shape=shape, fname=path.join(r"..", "things", r"debug_thumb"))

    return (shape, clearance)


def thumb_post_tr():
    debugprint('thumb_post_tr()')
    return translate(web_post(),
                     [(mount_width / 2) - post_adj, ((mount_height/2) + double_plate_height) - post_adj, 0]
                     )


def thumb_post_tl():
    debugprint('thumb_post_tl()')
    return translate(web_post(),
                     [-(mount_width / 2) + post_adj, ((mount_height/2) + double_plate_height) - post_adj, 0]
                     )


def thumb_post_bl():
    debugprint('thumb_post_bl()')
    return translate(web_post(),
                     [-(mount_width / 2) + post_adj, -((mount_height/2) + double_plate_height) + post_adj, 0]
                     )


def thumb_post_br():
    debugprint('thumb_post_br()')
    return translate(web_post(),
                     [(mount_width / 2) - post_adj, -((mount_height/2) + double_plate_height) + post_adj, 0]
                     )


def default_thumb_connectors():
    print('thumb_connectors()')
    hulls = []

    # Top two
    if default_1U_cluster:
        hulls.append(
            triangle_hulls(
                [
                    thumb_tl_place(web_post_tr()),
                    thumb_tl_place(web_post_br()),
                    thumb_tr_place(web_post_tl()),
                    thumb_tr_place(web_post_bl()),
                ]
            )
        )
    else:
        hulls.append(
            triangle_hulls(
                [
                    thumb_tl_place(thumb_post_tr()),
                    thumb_tl_place(thumb_post_br()),
                    thumb_tr_place(thumb_post_tl()),
                    thumb_tr_place(thumb_post_bl()),
                ]
            )
        )

    # bottom two on the right
    hulls.append(
        triangle_hulls(
            [
                thumb_br_place(web_post_tr()),
                thumb_br_place(web_post_br()),
                thumb_mr_place(web_post_tl()),
                thumb_mr_place(web_post_bl()),
            ]
        )
    )

    # bottom two on the left
    hulls.append(
        triangle_hulls(
            [
                thumb_br_place(web_post_tr()),
                thumb_br_place(web_post_br()),
                thumb_mr_place(web_post_tl()),
                thumb_mr_place(web_post_bl()),
            ]
        )
    )
    # centers of the bottom four
    hulls.append(
        triangle_hulls(
            [
                thumb_bl_place(web_post_tr()),
                thumb_bl_place(web_post_br()),
                thumb_ml_place(web_post_tl()),
                thumb_ml_place(web_post_bl()),
            ]
        )
    )

    # top two to the middle two, starting on the left
    hulls.append(
        triangle_hulls(
            [
                thumb_br_place(web_post_tl()),
                thumb_bl_place(web_post_bl()),
                thumb_br_place(web_post_tr()),
                thumb_bl_place(web_post_br()),
                thumb_mr_place(web_post_tl()),
                thumb_ml_place(web_post_bl()),
                thumb_mr_place(web_post_tr()),
                thumb_ml_place(web_post_br()),
            ]
        )
    )

    if default_1U_cluster:
        hulls.append(
            triangle_hulls(
                [
                    thumb_tl_place(web_post_tl()),
                    thumb_ml_place(web_post_tr()),
                    thumb_tl_place(web_post_bl()),
                    thumb_ml_place(web_post_br()),
                    thumb_tl_place(web_post_br()),
                    thumb_mr_place(web_post_tr()),
                    thumb_tr_place(web_post_bl()),
                    thumb_mr_place(web_post_br()),
                    thumb_tr_place(web_post_br()),
                ]
            )
        )
    else:
        # top two to the main keyboard, starting on the left
        hulls.append(
            triangle_hulls(
                [
                    thumb_tl_place(thumb_post_tl()),
                    thumb_ml_place(web_post_tr()),
                    thumb_tl_place(thumb_post_bl()),
                    thumb_ml_place(web_post_br()),
                    thumb_tl_place(thumb_post_br()),
                    thumb_mr_place(web_post_tr()),
                    thumb_tr_place(thumb_post_bl()),
                    thumb_mr_place(web_post_br()),
                    thumb_tr_place(thumb_post_br()),
                ]
            )
        )

    if default_1U_cluster:
        hulls.append(
            triangle_hulls(
                [
                    thumb_tl_place(web_post_tl()),
                    key_place(web_post_bl(), 0, cornerrow),
                    thumb_tl_place(web_post_tr()),
                    key_place(web_post_br(), 0, cornerrow),
                    thumb_tr_place(web_post_tl()),
                    key_place(web_post_bl(), 1, cornerrow),
                    thumb_tr_place(web_post_tr()),
                    key_place(web_post_br(), 1, cornerrow),
                    key_place(web_post_tl(), 2, lastrow),
                    key_place(web_post_bl(), 2, lastrow),
                    thumb_tr_place(web_post_tr()),
                    key_place(web_post_bl(), 2, lastrow),
                    thumb_tr_place(web_post_br()),
                    key_place(web_post_br(), 2, lastrow),
                    key_place(web_post_bl(), 3, lastrow),
                    key_place(web_post_tr(), 2, lastrow),
                    key_place(web_post_tl(), 3, lastrow),
                    key_place(web_post_bl(), 3, cornerrow),
                    key_place(web_post_tr(), 3, lastrow),
                    key_place(web_post_br(), 3, cornerrow),
                    key_place(web_post_bl(), 4, cornerrow),
                ]
            )
        )
    else:
        hulls.append(
            triangle_hulls(
                [
                    thumb_tl_place(thumb_post_tl()),
                    key_place(web_post_bl(), 0, cornerrow),
                    thumb_tl_place(thumb_post_tr()),
                    key_place(web_post_br(), 0, cornerrow),
                    thumb_tr_place(thumb_post_tl()),
                    key_place(web_post_bl(), 1, cornerrow),
                    thumb_tr_place(thumb_post_tr()),
                    key_place(web_post_br(), 1, cornerrow),
                    key_place(web_post_tl(), 2, lastrow),
                    key_place(web_post_bl(), 2, lastrow),
                    thumb_tr_place(thumb_post_tr()),
                    key_place(web_post_bl(), 2, lastrow),
                    thumb_tr_place(thumb_post_br()),
                    key_place(web_post_br(), 2, lastrow),
                    key_place(web_post_bl(), 3, lastrow),
                    key_place(web_post_tr(), 2, lastrow),
                    key_place(web_post_tl(), 3, lastrow),
                    key_place(web_post_bl(), 3, cornerrow),
                    key_place(web_post_tr(), 3, lastrow),
                    key_place(web_post_br(), 3, cornerrow),
                    key_place(web_post_bl(), 4, cornerrow),
                ]
            )
        )

    hulls.append(
        triangle_hulls(
            [
                key_place(web_post_br(), 1, cornerrow),
                key_place(web_post_tl(), 2, lastrow),
                key_place(web_post_bl(), 2, cornerrow),
                key_place(web_post_tr(), 2, lastrow),
                key_place(web_post_br(), 2, cornerrow),
                key_place(web_post_bl(), 3, cornerrow),
            ]
        )
    )

    hulls.append(
        triangle_hulls(
            [
                key_place(web_post_tr(), 3, lastrow),
                key_place(web_post_br(), 3, lastrow),
                key_place(web_post_tr(), 3, lastrow),
                key_place(web_post_bl(), 4, cornerrow),
            ]
        )
    )

    return union(hulls)

############################
# MINI THUMB CLUSTER
############################


def mini_thumb_tr_place(shape):
    shape = rotate(shape, [14, -15, 10])
    shape = translate(shape, thumborigin())
    shape = translate(shape, [-15, -10, 5])
    return shape


def mini_thumb_tl_place(shape):
    shape = rotate(shape, [10, -23, 25])
    shape = translate(shape, thumborigin())
    shape = translate(shape, [-35, -16, -2])
    return shape


def mini_thumb_mr_place(shape):
    shape = rotate(shape, [10, -23, 25])
    shape = translate(shape, thumborigin())
    shape = translate(shape, [-23, -34, -6])
    return shape


def mini_thumb_br_place(shape):
    shape = rotate(shape, [6, -34, 35])
    shape = translate(shape, thumborigin())
    shape = translate(shape, [-39, -43, -16])
    return shape


def mini_thumb_bl_place(shape):
    shape = rotate(shape, [6, -32, 35])
    shape = translate(shape, thumborigin())
    shape = translate(shape, [-51, -25, -11.5])
    return shape


def mini_thumb_1x_layout(shape):
    return union([
        mini_thumb_mr_place(rotate(shape, [0, 0, thumb_plate_mr_rotation])),
        mini_thumb_br_place(rotate(shape, [0, 0, thumb_plate_br_rotation])),
        mini_thumb_tl_place(rotate(shape, [0, 0, thumb_plate_tl_rotation])),
        mini_thumb_bl_place(rotate(shape, [0, 0, thumb_plate_bl_rotation])),
    ])


def mini_thumb_15x_layout(shape):
    return union([mini_thumb_tr_place(rotate(shape, [0, 0, thumb_plate_tr_rotation]))])


def mini_thumbcaps():
    t1 = mini_thumb_1x_layout(sa_cap(1))
    t15 = mini_thumb_15x_layout(rotate(sa_cap(1), [0, 0, rad2deg(pi / 2)]))
    return t1.add(t15)


def mini_thumb(side="right"):

    # shape = thumb_1x_layout(sl.rotate([0.0, 0.0, -90])(single_plate(side=side)))
    # shape += thumb_15x_layout(sl.rotate([0.0, 0.0, -90])(single_plate(side=side)))
    shape = mini_thumb_1x_layout(single_plate(side=side))
    shape = union([shape, mini_thumb_15x_layout(single_plate(side=side))])

    return shape


def mini_thumb_post_tr():
    return translate(web_post(),
        [(mount_width / 2) - post_adj, (mount_height / 2) - post_adj, 0]
    )


def mini_thumb_post_tl():
    return translate(web_post(),
        [-(mount_width / 2) + post_adj, (mount_height / 2) - post_adj, 0]
    )


def mini_thumb_post_bl():
    return translate(web_post(),
        [-(mount_width / 2) + post_adj, -(mount_height / 2) + post_adj, 0]
    )


def mini_thumb_post_br():
    return translate(web_post(),
        [(mount_width / 2) - post_adj, -(mount_height / 2) + post_adj, 0]
    )


def mini_thumb_connectors():
    hulls = []

    # Top two
    hulls.append(
        triangle_hulls(
            [
                mini_thumb_tl_place(web_post_tr()),
                mini_thumb_tl_place(web_post_br()),
                mini_thumb_tr_place(mini_thumb_post_tl()),
                mini_thumb_tr_place(mini_thumb_post_bl()),
            ]
        )
    )

    # bottom two on the right
    hulls.append(
        triangle_hulls(
            [
                mini_thumb_br_place(web_post_tr()),
                mini_thumb_br_place(web_post_br()),
                mini_thumb_mr_place(web_post_tl()),
                mini_thumb_mr_place(web_post_bl()),
            ]
        )
    )

    # bottom two on the left
    hulls.append(
        triangle_hulls(
            [
                mini_thumb_mr_place(web_post_tr()),
                mini_thumb_mr_place(web_post_br()),
                mini_thumb_tr_place(mini_thumb_post_br()),
            ]
        )
    )

    # between top and bottom row
    hulls.append(
        triangle_hulls(
            [
                mini_thumb_br_place(web_post_tl()),
                mini_thumb_bl_place(web_post_bl()),
                mini_thumb_br_place(web_post_tr()),
                mini_thumb_bl_place(web_post_br()),
                mini_thumb_mr_place(web_post_tl()),
                mini_thumb_tl_place(web_post_bl()),
                mini_thumb_mr_place(web_post_tr()),
                mini_thumb_tl_place(web_post_br()),
                mini_thumb_tr_place(web_post_bl()),
                mini_thumb_mr_place(web_post_tr()),
                mini_thumb_tr_place(web_post_br()),
            ]
        )
    )
    # top two to the main keyboard, starting on the left
    hulls.append(
        triangle_hulls(
            [
                mini_thumb_tl_place(web_post_tl()),
                mini_thumb_bl_place(web_post_tr()),
                mini_thumb_tl_place(web_post_bl()),
                mini_thumb_bl_place(web_post_br()),
                mini_thumb_mr_place(web_post_tr()),
                mini_thumb_tl_place(web_post_bl()),
                mini_thumb_tl_place(web_post_br()),
                mini_thumb_mr_place(web_post_tr()),
            ]
        )
    )
    # top two to the main keyboard, starting on the left
    hulls.append(
        triangle_hulls(
            [
                mini_thumb_tl_place(web_post_tl()),
                key_place(web_post_bl(), 0, cornerrow),
                mini_thumb_tl_place(web_post_tr()),
                key_place(web_post_br(), 0, cornerrow),
                mini_thumb_tr_place(mini_thumb_post_tl()),
                key_place(web_post_bl(), 1, cornerrow),
                mini_thumb_tr_place(mini_thumb_post_tr()),
                key_place(web_post_br(), 1, cornerrow),
                key_place(web_post_tl(), 2, lastrow),
                key_place(web_post_bl(), 2, lastrow),
                mini_thumb_tr_place(mini_thumb_post_tr()),
                key_place(web_post_bl(), 2, lastrow),
                mini_thumb_tr_place(mini_thumb_post_br()),
                key_place(web_post_br(), 2, lastrow),
                key_place(web_post_bl(), 3, lastrow),
                key_place(web_post_tr(), 2, lastrow),
                key_place(web_post_tl(), 3, lastrow),
                key_place(web_post_bl(), 3, cornerrow),
                key_place(web_post_tr(), 3, lastrow),
                key_place(web_post_br(), 3, cornerrow),
            ]
        )
    )
    hulls.append(
        triangle_hulls(
            [
                key_place(web_post_tr(), 3, lastrow),
                key_place(web_post_br(), 3, lastrow),
                key_place(web_post_bl(), 4, cornerrow),
            ]
        )
    )

    hulls.append(
        triangle_hulls(
            [
                key_place(web_post_tr(), 3, lastrow),
                key_place(web_post_br(), 3, cornerrow),
                key_place(web_post_bl(), 4, cornerrow),
            ]
        )
    )
    hulls.append(
        triangle_hulls(
            [
                key_place(web_post_br(), 1, cornerrow),
                key_place(web_post_tl(), 2, lastrow),
                key_place(web_post_bl(), 2, cornerrow),
                key_place(web_post_tr(), 2, lastrow),
                key_place(web_post_br(), 2, cornerrow),
                key_place(web_post_bl(), 3, cornerrow),
            ]
        )
    )

    return union(hulls)


############################
# Carbonfet THUMB CLUSTER
############################


def carbonfet_thumb_tl_place(shape):
    shape = rotate(shape, [10, -24, 10])
    shape = translate(shape, thumborigin())
    shape = translate(shape, [-13, -9.8, 4])
    return shape

def carbonfet_thumb_tr_place(shape):
    shape = rotate(shape, [6, -25, 10])
    shape = translate(shape, thumborigin())
    shape = translate(shape, [-7.5, -29.5, 0])
    return shape

def carbonfet_thumb_ml_place(shape):
    shape = rotate(shape, [8, -31, 14])
    shape = translate(shape, thumborigin())
    shape = translate(shape, [-30.5, -17, -6])
    return shape

def carbonfet_thumb_mr_place(shape):
    shape = rotate(shape, [4, -31, 14])
    shape = translate(shape, thumborigin())
    shape = translate(shape, [-22.2, -41, -10.3])
    return shape

def carbonfet_thumb_br_place(shape):
    shape = rotate(shape, [2, -37, 18])
    shape = translate(shape, thumborigin())
    shape = translate(shape, [-37, -46.4, -22])
    return shape

def carbonfet_thumb_bl_place(shape):
    shape = rotate(shape, [6, -37, 18])
    shape = translate(shape, thumborigin())
    shape = translate(shape, [-47, -23, -19])
    return shape


def carbonfet_thumb_1x_layout(shape):
    return union([
        carbonfet_thumb_tr_place(rotate(shape, [0, 0, thumb_plate_tr_rotation])),
        carbonfet_thumb_mr_place(rotate(shape, [0, 0, thumb_plate_mr_rotation])),
        carbonfet_thumb_br_place(rotate(shape, [0, 0, thumb_plate_br_rotation])),
        carbonfet_thumb_tl_place(rotate(shape, [0, 0, thumb_plate_tl_rotation])),
    ])


def carbonfet_thumb_15x_layout(shape, plate=True):
    if plate:
        return union([
            carbonfet_thumb_bl_place(rotate(shape, [0, 0, thumb_plate_bl_rotation])),
            carbonfet_thumb_ml_place(rotate(shape, [0, 0, thumb_plate_ml_rotation]))
        ])
    else:
        return union([
            carbonfet_thumb_bl_place(shape),
            carbonfet_thumb_ml_place(shape)
        ])


def carbonfet_thumbcaps():
    t1 = carbonfet_thumb_1x_layout(sa_cap(1))
    t15 = carbonfet_thumb_15x_layout(rotate(sa_cap(1.5), [0, 0, rad2deg(pi / 2)]))
    return t1.add(t15)


def carbonfet_thumb(side="right"):
    shape = carbonfet_thumb_1x_layout(single_plate(side=side))
    shape = union([shape, carbonfet_thumb_15x_layout(double_plate_half(), plate=False)])
    shape = union([shape, carbonfet_thumb_15x_layout(single_plate(side=side))])

    return shape

def carbonfet_thumb_post_tr():
    return translate(web_post(),
        [(mount_width / 2) - post_adj, (mount_height / 1.15) - post_adj, 0]
    )


def carbonfet_thumb_post_tl():
    return translate(web_post(),
        [-(mount_width / 2) + post_adj, (mount_height / 1.15) - post_adj, 0]
    )


def carbonfet_thumb_post_bl():
    return translate(web_post(),
        [-(mount_width / 2) + post_adj, -(mount_height / 1.15) + post_adj, 0]
    )


def carbonfet_thumb_post_br():
    return translate(web_post(),
        [(mount_width / 2) - post_adj, -(mount_height / 2) + post_adj, 0]
    )

def carbonfet_thumb_connectors():
    hulls = []

    # Top two
    hulls.append(
        triangle_hulls(
            [
                carbonfet_thumb_tl_place(web_post_tl()),
                carbonfet_thumb_tl_place(web_post_bl()),
                carbonfet_thumb_ml_place(carbonfet_thumb_post_tr()),
                carbonfet_thumb_ml_place(web_post_br()),
            ]
        )
    )

    hulls.append(
        triangle_hulls(
            [
                carbonfet_thumb_ml_place(carbonfet_thumb_post_tl()),
                carbonfet_thumb_ml_place(web_post_bl()),
                carbonfet_thumb_bl_place(carbonfet_thumb_post_tr()),
                carbonfet_thumb_bl_place(web_post_br()),
            ]
        )
    )

    # bottom two on the right
    hulls.append(
        triangle_hulls(
            [
                carbonfet_thumb_br_place(web_post_tr()),
                carbonfet_thumb_br_place(web_post_br()),
                carbonfet_thumb_mr_place(web_post_tl()),
                carbonfet_thumb_mr_place(web_post_bl()),
            ]
        )
    )

    # bottom two on the left
    hulls.append(
        triangle_hulls(
            [
                carbonfet_thumb_mr_place(web_post_tr()),
                carbonfet_thumb_mr_place(web_post_br()),
                carbonfet_thumb_tr_place(web_post_tl()),
                carbonfet_thumb_tr_place(web_post_bl()),
            ]
        )
    )
    hulls.append(
        triangle_hulls(
            [
                carbonfet_thumb_tr_place(web_post_br()),
                carbonfet_thumb_tr_place(web_post_bl()),
                carbonfet_thumb_mr_place(web_post_br()),
            ]
        )
    )

    # between top and bottom row
    hulls.append(
        triangle_hulls(
            [
                carbonfet_thumb_br_place(web_post_tl()),
                carbonfet_thumb_bl_place(web_post_bl()),
                carbonfet_thumb_br_place(web_post_tr()),
                carbonfet_thumb_bl_place(web_post_br()),
                carbonfet_thumb_mr_place(web_post_tl()),
                carbonfet_thumb_ml_place(web_post_bl()),
                carbonfet_thumb_mr_place(web_post_tr()),
                carbonfet_thumb_ml_place(web_post_br()),
                carbonfet_thumb_tr_place(web_post_tl()),
                carbonfet_thumb_tl_place(web_post_bl()),
                carbonfet_thumb_tr_place(web_post_tr()),
                carbonfet_thumb_tl_place(web_post_br()),
            ]
        )
    )
    # top two to the main keyboard, starting on the left
    hulls.append(
        triangle_hulls(
            [
                carbonfet_thumb_ml_place(carbonfet_thumb_post_tl()),
                key_place(web_post_bl(), 0, cornerrow),
                carbonfet_thumb_ml_place(carbonfet_thumb_post_tr()),
                key_place(web_post_br(), 0, cornerrow),
                carbonfet_thumb_tl_place(web_post_tl()),
                key_place(web_post_bl(), 1, cornerrow),
                carbonfet_thumb_tl_place(web_post_tr()),
                key_place(web_post_br(), 1, cornerrow),
                key_place(web_post_tl(), 2, lastrow),
                key_place(web_post_bl(), 2, lastrow),
                carbonfet_thumb_tl_place(web_post_tr()),
                key_place(web_post_bl(), 2, lastrow),
                carbonfet_thumb_tl_place(web_post_br()),
                key_place(web_post_br(), 2, lastrow),
                key_place(web_post_bl(), 3, lastrow),
                carbonfet_thumb_tl_place(web_post_br()),
                carbonfet_thumb_tr_place(web_post_tr()),
            ]
        )
    )

    hulls.append(
        triangle_hulls(
            [
                key_place(web_post_tr(), 3, lastrow),
                key_place(web_post_br(), 3, cornerrow),
                key_place(web_post_tl(), 3, lastrow),
                key_place(web_post_bl(), 3, cornerrow),
            ]
        )
    )

    hulls.append(
        triangle_hulls(
            [
                key_place(web_post_tr(), 2, lastrow),
                key_place(web_post_br(), 2, lastrow),
                key_place(web_post_tl(), 3, lastrow),
                key_place(web_post_bl(), 3, lastrow),
            ]
        )
    )

    hulls.append(
        triangle_hulls(
            [
                carbonfet_thumb_tr_place(web_post_br()),
                carbonfet_thumb_tr_place(web_post_tr()),
                key_place(web_post_bl(), 3, lastrow),
            ]
        )
    )

    hulls.append(
        triangle_hulls(
            [
                key_place(web_post_br(), 1, cornerrow),
                key_place(web_post_tl(), 2, lastrow),
                key_place(web_post_bl(), 2, cornerrow),
                key_place(web_post_tr(), 2, lastrow),
                key_place(web_post_br(), 2, cornerrow),
                key_place(web_post_tl(), 3, lastrow),
                key_place(web_post_bl(), 3, cornerrow),
            ]
        )
    )

    hulls.append(
        triangle_hulls(
            [
                key_place(web_post_tr(), 3, lastrow),
                key_place(web_post_br(), 3, lastrow),
                key_place(web_post_bl(), 4, cornerrow),
            ]
        )
    )

    hulls.append(
        triangle_hulls(
            [
                key_place(web_post_tr(), 3, lastrow),
                key_place(web_post_br(), 3, cornerrow),
                key_place(web_post_bl(), 4, cornerrow),
            ]
        )
    )

    return union(hulls)


##########
## Case ##
##########


def bottom_hull(p, height=0.001):
    debugprint("bottom_hull()")
    if ENGINE == 'cadquery':
        shape = None
        for item in p:
            # proj = sl.projection()(p)
            # t_shape = sl.linear_extrude(height=height, twist=0, convexity=0, center=True)(
            #      proj
            # )
            vertices = []
            verts = item.faces('<Z').vertices()
            for vert in verts.objects:
                v0 = vert.toTuple()
                v1 = [v0[0], v0[1], -10]
                vertices.append(np.array(v0))
                vertices.append(np.array(v1))

            t_shape = hull_from_points(vertices)

            # t_shape = translate(t_shape, [0, 0, height / 2 - 10])

            if shape is None:
                shape = t_shape

            for shp in (*p, shape, t_shape):
                try:
                    shp.vertices()
                except:
                    0
            shape = union([shape, hull_from_shapes((shape, t_shape))])

        return shape

    else:
        shape = None
        for item in p:
            proj = sl.projection()(p)
            t_shape = sl.linear_extrude(height=height, twist=0, convexity=0, center=True)(
                proj
            )
            t_shape = sl.translate([0, 0, height / 2 - 10])(t_shape)
            if shape is None:
                shape = t_shape
            shape = sl.hull()(p, shape, t_shape)
        return shape


def left_key_position(row, direction, low_corner=False):
    debugprint("left_key_position()")
    pos = np.array(
        key_position([-mount_width * 0.5, direction * mount_height * 0.5, 0], 0, row)
    )
    if low_corner:
        y_offset = left_wall_lower_y_offset
        z_offset = left_wall_lower_z_offset
    else:
        y_offset = 0.0
        z_offset = 0.0

    return list(pos - np.array([left_wall_x_offset, -y_offset, left_wall_z_offset + z_offset]))


def left_key_place(shape, row, direction, low_corner=False):
    debugprint("left_key_place()")
    pos = left_key_position(row, direction, low_corner=low_corner)
    return translate(shape, pos)


def wall_locate1(dx, dy):
    debugprint("wall_locate1()")
    return [dx * wall_thickness, dy * wall_thickness, -1]


def wall_locate2(dx, dy):
    debugprint("wall_locate2()")
    return [dx * wall_x_offset, dy * wall_y_offset, -wall_z_offset]


def wall_locate3(dx, dy, back=False):
    debugprint("wall_locate3()")
    if back:
        return [
            dx * (wall_x_offset + wall_base_x_thickness),
            dy * (wall_y_offset + wall_base_back_thickness),
            -wall_z_offset,
        ]
    else:
        return [
            dx * (wall_x_offset + wall_base_x_thickness),
            dy * (wall_y_offset + wall_base_y_thickness),
            -wall_z_offset,
        ]
    # return [
    #     dx * (wall_xy_offset + wall_thickness),
    #     dy * (wall_xy_offset + wall_thickness),
    #     -wall_z_offset,
    # ]


def wall_brace(place1, dx1, dy1, post1, place2, dx2, dy2, post2, back=False):
    debugprint("wall_brace()")
    hulls = []

    hulls.append(place1(post1))
    hulls.append(place1(translate(post1, wall_locate1(dx1, dy1))))
    hulls.append(place1(translate(post1, wall_locate2(dx1, dy1))))
    hulls.append(place1(translate(post1, wall_locate3(dx1, dy1, back))))

    hulls.append(place2(post2))
    hulls.append(place2(translate(post2, wall_locate1(dx2, dy2))))
    hulls.append(place2(translate(post2, wall_locate2(dx2, dy2))))
    hulls.append(place2(translate(post2, wall_locate3(dx2, dy2, back))))
    shape1 = hull_from_shapes(hulls)

    hulls = []
    hulls.append(place1(translate(post1, wall_locate2(dx1, dy1))))
    hulls.append(place1(translate(post1, wall_locate3(dx1, dy1, back))))
    hulls.append(place2(translate(post2, wall_locate2(dx2, dy2))))
    hulls.append(place2(translate(post2, wall_locate3(dx2, dy2, back))))
    shape2 = bottom_hull(hulls)

    return union([shape1, shape2])
    # return shape1


def key_wall_brace(x1, y1, dx1, dy1, post1, x2, y2, dx2, dy2, post2, back=False):
    debugprint("key_wall_brace()")
    return wall_brace(
        (lambda shape: key_place(shape, x1, y1)),
        dx1,
        dy1,
        post1,
        (lambda shape: key_place(shape, x2, y2)),
        dx2,
        dy2,
        post2,
        back
    )


def back_wall():
    print("back_wall()")
    x = 0
    shape = union([key_wall_brace(x, 0, 0, 1, web_post_tl(), x, 0, 0, 1, web_post_tr(), back=True)])
    for i in range(ncols - 1):
        x = i + 1
        shape = union([shape, key_wall_brace(x, 0, 0, 1, web_post_tl(), x, 0, 0, 1, web_post_tr(), back=True)])
        shape = union([shape, key_wall_brace(
            x, 0, 0, 1, web_post_tl(), x - 1, 0, 0, 1, web_post_tr(), back=True
        )])
    shape = union([shape, key_wall_brace(
        lastcol, 0, 0, 1, web_post_tr(), lastcol, 0, 1, 0, web_post_tr(), back=True
    )])
    return shape


def right_wall():
    print("right_wall()")
    y = 0
    shape = union([
        key_wall_brace(
            lastcol, y, 1, 0, web_post_tr(), lastcol, y, 1, 0, web_post_br()
        )
    ])

    for i in range(lastrow - 1):
        y = i + 1
        shape = union([shape,key_wall_brace(
            lastcol, y - 1, 1, 0, web_post_br(), lastcol, y, 1, 0, web_post_tr()
        )])

        shape = union([shape,key_wall_brace(
            lastcol, y, 1, 0, web_post_tr(), lastcol, y, 1, 0, web_post_br()
        )])
        #STRANGE PARTIAL OFFSET

    shape = union([
        shape,
        key_wall_brace(lastcol, cornerrow, 0, -1, web_post_br(), lastcol, cornerrow, 1, 0, web_post_br())
    ])
    return shape


def left_wall():
    print('left_wall()')
    #shape = union([wall_brace(
    #    (lambda sh: key_place(sh, 0, 0)), 0, 1, web_post_tl(),
    #    (lambda sh: left_key_place(sh, 0, 1)), 0, 1, web_post(),
    #)])

    #shape = union([shape, wall_brace(
    #    (lambda sh: left_key_place(sh, 0, 1)), 0, 1, web_post(),
    #    (lambda sh: left_key_place(sh, 0, 1)), -1, 0, web_post(),
    #)])

    #export_file(shape=shape, fname=path.join(r"..", "things", r"debug_left_wall1"))
    
    for i in range(lastrow):
        y = i
        low = (y == (lastrow-1))
        temp_shape1 = wall_brace(
            (lambda sh: left_key_place(sh, y, 1,)), -1, 0, web_post(),
            (lambda sh: left_key_place(sh, y, -1, low_corner=low)), -1, 0, web_post(),
        )
        temp_shape2 = hull_from_shapes((
            key_place(web_post_tl(), 0, y),
            key_place(web_post_bl(), 0, y),
            left_key_place(web_post(), y, 1),
            left_key_place(web_post(), y, -1, low_corner=low),
        ))
        #shape = temp_shape1 # union([shape, temp_shape1])
        if i == 0:
            shape = temp_shape2
        else:
            shape = union([shape, temp_shape2])

    for i in range(lastrow - 1):
        y = i + 1
        low = (y == (lastrow-1))
        temp_shape1 = wall_brace(
            (lambda sh: left_key_place(sh, y - 1, -1)), -1, 0, web_post(),
            (lambda sh: left_key_place(sh, y, 1)), -1, 0, web_post(),
        )
        temp_shape2 = hull_from_shapes((
            key_place(web_post_tl(), 0, y),
            key_place(web_post_bl(), 0, y - 1),
            left_key_place(web_post(), y, 1),
            left_key_place(web_post(), y - 1, -1),
        ))
        #shape = union([shape, temp_shape1])
        shape = union([shape, temp_shape2])

    export_file(shape=shape, fname=path.join(r"..", "things", r"debug_left_wall"))
        
    return shape


def front_wall():
    print('front_wall()')
    shape = union([
        key_wall_brace(
            lastcol, 0, 0, 1, web_post_tr(), lastcol, 0, 1, 0, web_post_tr()
        )
    ])
    shape = union([shape,key_wall_brace(
        3, lastrow, 0, -1, web_post_bl(), 3, lastrow, 0.5, -1, web_post_br()
    )])
    shape = union([shape,key_wall_brace(
        3, lastrow, 0.5, -1, web_post_br(), 4, cornerrow, 1, -1, web_post_bl()
    )])
    for i in range(ncols - 4):
        x = i + 4
        shape = union([shape,key_wall_brace(
            x, cornerrow, 0, -1, web_post_bl(), x, cornerrow, 0, -1, web_post_br()
        )])
    for i in range(ncols - 5):
        x = i + 5
        shape = union([shape, key_wall_brace(
            x, cornerrow, 0, -1, web_post_bl(), x - 1, cornerrow, 0, -1, web_post_br()
        )])

    return shape

def thumb_walls():
    if thumb_style == "MINI":
        return mini_thumb_walls()
    elif thumb_style == "CARBONFET":
        return carbonfet_thumb_walls()
    else:
        return default_thumb_walls()

def thumb_connection():
    if thumb_style == "MINI":
        return mini_thumb_connection()
    elif thumb_style == "CARBONFET":
        return carbonfet_thumb_connection()
    else:
        return default_thumb_connection()

def default_thumb_walls():
    print('thumb_walls()')
    # thumb, walls
    if default_1U_cluster:
        shape = union([wall_brace(thumb_mr_place, 0, -1, web_post_br(), thumb_tr_place, 0, -1, web_post_br())])
    else:
        shape = union([wall_brace(thumb_mr_place, 0, -1, web_post_br(), thumb_tr_place, 0, -1, thumb_post_br())])
    shape = union([shape, wall_brace(thumb_mr_place, 0, -1, web_post_br(), thumb_mr_place, 0, -1, web_post_bl())])
    shape = union([shape, wall_brace(thumb_br_place, 0, -1, web_post_br(), thumb_br_place, 0, -1, web_post_bl())])
    #shape = union([shape, wall_brace(thumb_ml_place, -0.3, 1, web_post_tr(), thumb_ml_place, 0, 1, web_post_tl())])
    #shape = union([shape, wall_brace(thumb_bl_place, 0, 1, web_post_tr(), thumb_bl_place, 0, 1, web_post_tl())])
    shape = union([shape, wall_brace(thumb_br_place, -1, 0, web_post_tl(), thumb_br_place, -1, 0, web_post_bl())])
    shape = union([shape, wall_brace(thumb_bl_place, -1, 0, web_post_tl(), thumb_bl_place, -1, 0, web_post_bl())])
    # thumb, corners
    shape = union([shape, wall_brace(thumb_br_place, -1, 0, web_post_bl(), thumb_br_place, 0, -1, web_post_bl())])
    #shape = union([shape, wall_brace(thumb_bl_place, -1, 0, web_post_tl(), thumb_bl_place, 0, 1, web_post_tl())])
    # thumb, tweeners
    shape = union([shape, wall_brace(thumb_mr_place, 0, -1, web_post_bl(), thumb_br_place, 0, -1, web_post_br())])
    #shape = union([shape, wall_brace(thumb_ml_place, 0, 1, web_post_tl(), thumb_bl_place, 0, 1, web_post_tr())])
    shape = union([shape, wall_brace(thumb_bl_place, -1, 0, web_post_bl(), thumb_br_place, -1, 0, web_post_tl())])
    if default_1U_cluster:
        shape = union([shape, wall_brace(thumb_tr_place, 0, -1, web_post_br(), (lambda sh: key_place(sh, 3, lastrow)), 0, -1, web_post_bl())])
    else:
        shape = union([shape, wall_brace(thumb_tr_place, 0, -1, thumb_post_br(), (lambda sh: key_place(sh, 3, lastrow)), 0, -1, web_post_bl())])

    return shape


def default_thumb_connection():
    print('thumb_connection()')
    # clunky bit on the top left thumb connection  (normal connectors don't work well)
    shape = union([bottom_hull(
        [
            left_key_place(translate(web_post(), wall_locate2(-1, 0)), cornerrow, -1, low_corner=True),
            left_key_place(translate(web_post(), wall_locate3(-1, 0)), cornerrow, -1, low_corner=True),
            thumb_ml_place(translate(web_post_tr(), wall_locate2(-0.3, 1))),
            thumb_ml_place(translate(web_post_tr(), wall_locate3(-0.3, 1))),
        ]
    )])

    shape = union([shape,
        hull_from_shapes(
            [
                left_key_place(translate(web_post(), wall_locate2(-1, 0)), cornerrow, -1, low_corner=True),
                left_key_place(translate(web_post(), wall_locate3(-1, 0)), cornerrow, -1, low_corner=True),
                thumb_ml_place(translate(web_post_tr(), wall_locate2(-0.3, 1))),
                thumb_ml_place(translate(web_post_tr(), wall_locate3(-0.3, 1))),
                thumb_tl_place(thumb_post_tl()),
            ]
        )
    ])  # )

    shape = union([shape, hull_from_shapes(
        [
            left_key_place(translate(web_post(), wall_locate1(-1, 0)), cornerrow, -1, low_corner=True),
            left_key_place(translate(web_post(), wall_locate2(-1, 0)), cornerrow, -1, low_corner=True),
            left_key_place(translate(web_post(), wall_locate3(-1, 0)), cornerrow, -1, low_corner=True),
            thumb_tl_place(thumb_post_tl()),
        ]
    )])

    shape = union([shape, hull_from_shapes(
        [
            left_key_place(web_post(), cornerrow, -1, low_corner=True),
            left_key_place(translate(web_post(), wall_locate1(-1, 0)), cornerrow, -1, low_corner=True),
            key_place(web_post_bl(), 0, cornerrow),
            thumb_tl_place(thumb_post_tl()),
        ]
    )])

    shape = union([shape, hull_from_shapes(
        [
            thumb_ml_place(web_post_tr()),
            thumb_ml_place(translate(web_post_tr(), wall_locate1(-0.3, 1))),
            thumb_ml_place(translate(web_post_tr(), wall_locate2(-0.3, 1))),
            thumb_ml_place(translate(web_post_tr(), wall_locate3(-0.3, 1))),
            thumb_tl_place(thumb_post_tl()),
        ]
    )])

    return shape

def mini_thumb_walls():
    # thumb, walls
    shape = union([wall_brace(mini_thumb_mr_place, 0, -1, web_post_br(), mini_thumb_tr_place, 0, -1, mini_thumb_post_br())])
    shape = union([shape, wall_brace(mini_thumb_mr_place, 0, -1, web_post_br(), mini_thumb_mr_place, 0, -1, web_post_bl())])
    shape = union([shape, wall_brace(mini_thumb_br_place, 0, -1, web_post_br(), mini_thumb_br_place, 0, -1, web_post_bl())])
    shape = union([shape, wall_brace(mini_thumb_bl_place, 0, 1, web_post_tr(), mini_thumb_bl_place, 0, 1, web_post_tl())])
    shape = union([shape, wall_brace(mini_thumb_br_place, -1, 0, web_post_tl(), mini_thumb_br_place, -1, 0, web_post_bl())])
    shape = union([shape, wall_brace(mini_thumb_bl_place, -1, 0, web_post_tl(), mini_thumb_bl_place, -1, 0, web_post_bl())])
    # thumb, corners
    shape = union([shape, wall_brace(mini_thumb_br_place, -1, 0, web_post_bl(), mini_thumb_br_place, 0, -1, web_post_bl())])
    shape = union([shape, wall_brace(mini_thumb_bl_place, -1, 0, web_post_tl(), mini_thumb_bl_place, 0, 1, web_post_tl())])
    # thumb, tweeners
    shape = union([shape, wall_brace(mini_thumb_mr_place, 0, -1, web_post_bl(), mini_thumb_br_place, 0, -1, web_post_br())])
    shape = union([shape, wall_brace(mini_thumb_bl_place, -1, 0, web_post_bl(), mini_thumb_br_place, -1, 0, web_post_tl())])
    shape = union([shape, wall_brace(mini_thumb_tr_place, 0, -1, mini_thumb_post_br(), (lambda sh: key_place(sh, 3, lastrow)), 0, -1, web_post_bl())])

    return shape

def mini_thumb_connection():
    # clunky bit on the top left thumb connection  (normal connectors don't work well)
    shape = union([bottom_hull(
        [
            left_key_place(translate(web_post(), wall_locate2(-1, 0)), cornerrow, -1, low_corner=True),
            left_key_place(translate(web_post(), wall_locate3(-1, 0)), cornerrow, -1, low_corner=True),
            mini_thumb_bl_place(translate(web_post_tr(), wall_locate2(-0.3, 1))),
            mini_thumb_bl_place(translate(web_post_tr(), wall_locate3(-0.3, 1))),
        ]
    )])

    shape = union([shape,
        hull_from_shapes(
        [
            left_key_place(translate(web_post(), wall_locate2(-1, 0)), cornerrow, -1, low_corner=True),
            left_key_place(translate(web_post(), wall_locate3(-1, 0)), cornerrow, -1, low_corner=True),
            mini_thumb_bl_place(translate(web_post_tr(), wall_locate2(-0.3, 1))),
            mini_thumb_bl_place(translate(web_post_tr(), wall_locate3(-0.3, 1))),
            mini_thumb_tl_place(web_post_tl()),
        ]
    )])

    shape = union([shape,
        hull_from_shapes(
        [
            left_key_place(web_post(), cornerrow, -1, low_corner=True),
            left_key_place(translate(web_post(), wall_locate1(-1, 0)), cornerrow, -1, low_corner=True),
            left_key_place(translate(web_post(), wall_locate2(-1, 0)), cornerrow, -1, low_corner=True),
            left_key_place(translate(web_post(), wall_locate3(-1, 0)), cornerrow, -1, low_corner=True),
            mini_thumb_tl_place(web_post_tl()),
        ]
    )])

    shape = union([shape,
        hull_from_shapes(
        [
            left_key_place(web_post(), cornerrow, -1, low_corner=True),
            left_key_place(translate(web_post(), wall_locate1(-1, 0)), cornerrow, -1, low_corner=True),
            key_place(web_post_bl(), 0, cornerrow),
            mini_thumb_tl_place(web_post_tl()),
        ]
    )])

    shape = union([shape,
        hull_from_shapes(
        [
            mini_thumb_bl_place(web_post_tr()),
            mini_thumb_bl_place(translate(web_post_tr(), wall_locate1(-0.3, 1))),
            mini_thumb_bl_place(translate(web_post_tr(), wall_locate2(-0.3, 1))),
            mini_thumb_bl_place(translate(web_post_tr(), wall_locate3(-0.3, 1))),
            mini_thumb_tl_place(web_post_tl()),
        ]
    )])

    return shape



def carbonfet_thumb_walls():
    # thumb, walls
    shape = union([wall_brace(carbonfet_thumb_mr_place, 0, -1, web_post_br(), carbonfet_thumb_tr_place, 0, -1, web_post_br())])
    shape = union([shape, wall_brace(carbonfet_thumb_mr_place, 0, -1, web_post_br(), carbonfet_thumb_mr_place, 0, -1.15, web_post_bl())])
    shape = union([shape, wall_brace(carbonfet_thumb_br_place, 0, -1, web_post_br(), carbonfet_thumb_br_place, 0, -1, web_post_bl())])
    shape = union([shape, wall_brace(carbonfet_thumb_bl_place, -.3, 1, thumb_post_tr(), carbonfet_thumb_bl_place, 0, 1, thumb_post_tl())])
    shape = union([shape, wall_brace(carbonfet_thumb_br_place, -1, 0, web_post_tl(), carbonfet_thumb_br_place, -1, 0, web_post_bl())])
    shape = union([shape, wall_brace(carbonfet_thumb_bl_place, -1, 0, thumb_post_tl(), carbonfet_thumb_bl_place, -1, 0, web_post_bl())])
    # thumb, corners
    shape = union([shape, wall_brace(carbonfet_thumb_br_place, -1, 0, web_post_bl(), carbonfet_thumb_br_place, 0, -1, web_post_bl())])
    shape = union([shape, wall_brace(carbonfet_thumb_bl_place, -1, 0, thumb_post_tl(), carbonfet_thumb_bl_place, 0, 1, thumb_post_tl())])
    # thumb, tweeners
    shape = union([shape, wall_brace(carbonfet_thumb_mr_place, 0, -1.15, web_post_bl(), carbonfet_thumb_br_place, 0, -1, web_post_br())])
    shape = union([shape, wall_brace(carbonfet_thumb_bl_place, -1, 0, web_post_bl(), carbonfet_thumb_br_place, -1, 0, web_post_tl())])
    shape = union([shape, wall_brace(carbonfet_thumb_tr_place, 0, -1, web_post_br(), (lambda sh: key_place(sh, 3, lastrow)), 0, -1, web_post_bl())])
    return shape

def carbonfet_thumb_connection():
    # clunky bit on the top left thumb connection  (normal connectors don't work well)
    shape = bottom_hull(
        [
            left_key_place(translate(web_post(), wall_locate2(-1, 0)), cornerrow, -1, low_corner=True),
            left_key_place(translate(web_post(), wall_locate3(-1, 0)), cornerrow, -1, low_corner=True),
            carbonfet_thumb_bl_place(translate(thumb_post_tr(), wall_locate2(-0.3, 1))),
            carbonfet_thumb_bl_place(translate(thumb_post_tr(), wall_locate3(-0.3, 1))),
        ]
    )

    shape = union([shape,
        hull_from_shapes(
        [
            left_key_place(translate(web_post(), wall_locate2(-1, 0)), cornerrow, -1, low_corner=True),
            left_key_place(translate(web_post(), wall_locate3(-1, 0)), cornerrow, -1, low_corner=True),
            carbonfet_thumb_bl_place(translate(thumb_post_tr(), wall_locate2(-0.3, 1))),
            carbonfet_thumb_bl_place(translate(thumb_post_tr(), wall_locate3(-0.3, 1))),
            carbonfet_thumb_ml_place(thumb_post_tl()),
        ]
    )])

    shape = union([shape,
        hull_from_shapes(
        [
            left_key_place(web_post(), cornerrow, -1, low_corner=True),
            left_key_place(translate(web_post(), wall_locate1(-1, 0)), cornerrow, -1, low_corner=True),
            left_key_place(translate(web_post(), wall_locate2(-1, 0)), cornerrow, -1, low_corner=True),
            left_key_place(translate(web_post(), wall_locate3(-1, 0)), cornerrow, -1, low_corner=True),
            carbonfet_thumb_ml_place(thumb_post_tl()),
        ]
    )])

    shape = union([shape,
        hull_from_shapes(
        [
            left_key_place(web_post(), cornerrow, -1, low_corner=True),
            left_key_place(translate(web_post(), wall_locate1(-1, 0)), cornerrow, -1, low_corner=True),
            key_place(web_post_bl(), 0, cornerrow),
            carbonfet_thumb_ml_place(thumb_post_tl()),
        ]
    )])

    shape = union([shape,
        hull_from_shapes(
        [
            carbonfet_thumb_bl_place(thumb_post_tr()),
            carbonfet_thumb_bl_place(translate(thumb_post_tr(), wall_locate1(-0.3, 1))),
            carbonfet_thumb_bl_place(translate(thumb_post_tr(), wall_locate2(-0.3, 1))),
            carbonfet_thumb_bl_place(translate(thumb_post_tr(), wall_locate3(-0.3, 1))),
            carbonfet_thumb_ml_place(thumb_post_tl()),
        ]
    )])

    return shape

def case_walls():
    print('case_walls()')
    return (
        union([
            back_wall(),
            left_wall(),
            right_wall(),
            front_wall(),
            thumb_walls(),
            #thumb_connection(),
            joystick_wall()
        ])
    )


rj9_start = list(
    np.array([0, -3, 0])
    + np.array(
        key_position(
            list(np.array(wall_locate3(0, 1)) + np.array([0, (mount_height / 2), 0])),
            0,
            0,
        )
    )
)

rj9_position = (rj9_start[0], rj9_start[1], 11)


def rj9_cube():
    debugprint('rj9_cube()')
    shape = box(14.78, 13, 22.38)

    return shape


def rj9_space():
    debugprint('rj9_space()')
    return translate(rj9_cube(), rj9_position)


def rj9_holder():
    print('rj9_holder()')
    shape = union([translate(box(10.78, 9, 18.38), (0, 2, 0)), translate(box(10.78, 13, 5), (0, 0, 5))])
    shape = difference(rj9_cube(), [shape])
    shape = translate(shape, rj9_position)

    return shape


usb_holder_position = key_position(
    list(np.array(wall_locate2(0, 1)) + np.array([0, (mount_height / 2), 0])), 1, 0
)
usb_holder_size = [6.5, 10.0, 13.6]
usb_holder_thickness = 4


def usb_holder():
    print('usb_holder()')
    shape = box(
        usb_holder_size[0] + usb_holder_thickness,
        usb_holder_size[1],
        usb_holder_size[2] + usb_holder_thickness,
    )
    shape = translate(shape,
        (
            usb_holder_position[0],
            usb_holder_position[1],
            (usb_holder_size[2] + usb_holder_thickness) / 2,
        )
    )
    return shape


def usb_holder_hole():
    debugprint('usb_holder_hole()')
    shape = box(*usb_holder_size)
    shape = translate(shape,
        (
            usb_holder_position[0],
            usb_holder_position[1],
            (usb_holder_size[2] + usb_holder_thickness) / 2,
        )
    )
    return shape


external_start = list(
    # np.array([0, -3, 0])
    np.array([external_holder_width / 2, 0, 0])
    + np.array(
        key_position(
            list(np.array(wall_locate3(0, 1)) + np.array([0, (mount_height / 2), 0])),
            0,
            0,
        )
    )
)

def external_mount_hole():
    print('external_mount_hole()')
    shape = box(external_holder_width, 20.0, external_holder_height+.1)
    shape = translate(shape,
        (
            external_start[0] + external_holder_xoffset,
            external_start[1],
            external_holder_height / 2-.05,
        )
    )
    return shape

if oled_mount_type is not None and oled_mount_type != "NONE" and oled_center_row is not None:
    base_pt1 = key_position(
        list(np.array([-mount_width/2, 0, 0]) + np.array([0, (mount_height / 2), 0])), 0, oled_center_row-1
    )
    base_pt2 = key_position(
        list(np.array([-mount_width/2, 0, 0]) + np.array([0, (mount_height / 2), 0])), 0, oled_center_row+1
    )
    base_pt0 = key_position(
        list(np.array([-mount_width / 2, 0, 0]) + np.array([0, (mount_height / 2), 0])), 0, oled_center_row
    )

    oled_mount_location_xyz = (np.array(base_pt1)+np.array(base_pt2))/2. + np.array(((-left_wall_x_offset/2), 0, 0)) + np.array(oled_translation_offset)
    oled_mount_location_xyz[2] = (oled_mount_location_xyz[2] + base_pt0[2])/2

    angle_x = np.arctan2(base_pt1[2] - base_pt2[2], base_pt1[1] - base_pt2[1])
    angle_z = np.arctan2(base_pt1[0] - base_pt2[0], base_pt1[1] - base_pt2[1])

    oled_mount_rotation_xyz = (rad2deg(angle_x), 0, -rad2deg(angle_z)) + np.array(oled_rotation_offset)


def oled_sliding_mount_frame():
    mount_ext_width = oled_mount_width + 2 * oled_mount_rim
    mount_ext_height = (
            oled_mount_height + 2 * oled_edge_overlap_end
            + oled_edge_overlap_connector + oled_edge_overlap_clearance
            + 2 * oled_mount_rim
    )
    mount_ext_up_height = oled_mount_height + 2 * oled_mount_rim
    top_hole_start = -mount_ext_height / 2.0 + oled_mount_rim + oled_edge_overlap_end + oled_edge_overlap_connector
    top_hole_length = oled_mount_height

    hole = box(mount_ext_width, mount_ext_up_height, oled_mount_cut_depth + .01)
    hole = translate(hole, (0., top_hole_start + top_hole_length / 2, 0.))

    hole_down = box(mount_ext_width, mount_ext_height, oled_mount_depth + oled_mount_cut_depth / 2)
    hole_down = translate(hole_down, (0., 0., -oled_mount_cut_depth / 4))
    hole = union([hole, hole_down])

    shape = box(mount_ext_width, mount_ext_height, oled_mount_depth)

    conn_hole_start = -mount_ext_height / 2.0 + oled_mount_rim
    conn_hole_length = (
            oled_edge_overlap_end + oled_edge_overlap_connector
            + oled_edge_overlap_clearance + oled_thickness
    )
    conn_hole = box(oled_mount_width, conn_hole_length + .01, oled_mount_depth)
    conn_hole = translate(conn_hole, (
        0,
        conn_hole_start + conn_hole_length / 2,
        -oled_edge_overlap_thickness
    ))

    end_hole_length = (
            oled_edge_overlap_end + oled_edge_overlap_clearance
    )
    end_hole_start = mount_ext_height / 2.0 - oled_mount_rim - end_hole_length
    end_hole = box(oled_mount_width, end_hole_length + .01, oled_mount_depth)
    end_hole = translate(end_hole, (
        0,
        end_hole_start + end_hole_length / 2,
        -oled_edge_overlap_thickness
    ))

    top_hole_start = -mount_ext_height / 2.0 + oled_mount_rim + oled_edge_overlap_end + oled_edge_overlap_connector
    top_hole_length = oled_mount_height
    top_hole = box(oled_mount_width, top_hole_length, oled_edge_overlap_thickness + oled_thickness - oled_edge_chamfer)
    top_hole = translate(top_hole, (
        0,
        top_hole_start + top_hole_length / 2,
        (oled_mount_depth - oled_edge_overlap_thickness - oled_thickness - oled_edge_chamfer) / 2.0
    ))

    top_chamfer_1 = box(
        oled_mount_width,
        top_hole_length,
        0.01
    )
    top_chamfer_2 = box(
        oled_mount_width + 2 * oled_edge_chamfer,
        top_hole_length + 2 * oled_edge_chamfer,
        0.01
    )
    top_chamfer_1 = translate(top_chamfer_1, (0, 0, -oled_edge_chamfer - .05))

    # top_chamfer_1 = sl.hull()(top_chamfer_1, top_chamfer_2)
    top_chamfer_1 = hull_from_shapes([top_chamfer_1, top_chamfer_2])

    top_chamfer_1 = translate(top_chamfer_1, (
        0,
        top_hole_start + top_hole_length / 2,
        oled_mount_depth / 2.0 + .05
    ))

    top_hole = union([top_hole, top_chamfer_1])

    shape = difference(shape, [conn_hole, top_hole, end_hole])

    shape = rotate(shape, oled_mount_rotation_xyz)
    shape = translate(shape,
        (
            oled_mount_location_xyz[0],
            oled_mount_location_xyz[1],
            oled_mount_location_xyz[2],
        )
    )

    hole = rotate(hole, oled_mount_rotation_xyz)
    hole = translate(hole,
        (
            oled_mount_location_xyz[0],
            oled_mount_location_xyz[1],
            oled_mount_location_xyz[2],
        )
    )
    return hole, shape


def oled_clip_mount_frame():
    mount_ext_width = oled_mount_width + 2 * oled_mount_rim
    mount_ext_height = (
            oled_mount_height + 2 * oled_clip_thickness
            + 2 * oled_clip_undercut + 2 * oled_clip_overhang + 2 * oled_mount_rim
    )
    hole = box(mount_ext_width, mount_ext_height, oled_mount_cut_depth + .01)

    shape = box(mount_ext_width, mount_ext_height, oled_mount_depth)
    shape = difference(shape, [box(oled_mount_width, oled_mount_height, oled_mount_depth + .1)])

    clip_slot = box(
        oled_clip_width + 2 * oled_clip_width_clearance,
        oled_mount_height + 2 * oled_clip_thickness + 2 * oled_clip_overhang,
        oled_mount_depth + .1
    )

    shape = difference(shape, [clip_slot])

    clip_undercut = box(
        oled_clip_width + 2 * oled_clip_width_clearance,
        oled_mount_height + 2 * oled_clip_thickness + 2 * oled_clip_overhang + 2 * oled_clip_undercut,
        oled_mount_depth + .1
    )

    clip_undercut = translate(clip_undercut, (0., 0., oled_clip_undercut_thickness))
    shape = difference(shape, [clip_undercut])

    plate = box(
        oled_mount_width + .1,
        oled_mount_height - 2 * oled_mount_connector_hole,
        oled_mount_depth - oled_thickness
    )
    plate = translate(plate, (0., 0., -oled_thickness / 2.0))
    shape = union([shape, plate])

    shape = rotate(shape, oled_mount_rotation_xyz)
    shape = translate(shape,
        (
            oled_mount_location_xyz[0],
            oled_mount_location_xyz[1],
            oled_mount_location_xyz[2],
        )
    )

    hole = rotate(hole, oled_mount_rotation_xyz)
    hole = translate(hole,
        (
            oled_mount_location_xyz[0],
            oled_mount_location_xyz[1],
            oled_mount_location_xyz[2],
        )
    )

    return hole, shape


def oled_clip():
    mount_ext_width = oled_mount_width + 2 * oled_mount_rim
    mount_ext_height = (
            oled_mount_height + 2 * oled_clip_thickness + 2 * oled_clip_overhang
            + 2 * oled_clip_undercut + 2 * oled_mount_rim
    )

    oled_leg_depth = oled_mount_depth + oled_clip_z_gap

    shape = box(mount_ext_width - .1, mount_ext_height - .1, oled_mount_bezel_thickness)
    shape = translate(shape, (0., 0., oled_mount_bezel_thickness / 2.))

    hole_1 = box(
        oled_screen_width + 2 * oled_mount_bezel_chamfer,
        oled_screen_length + 2 * oled_mount_bezel_chamfer,
        .01
    )
    hole_2 = box(oled_screen_width, oled_screen_length, 2.05 * oled_mount_bezel_thickness)
    hole = hull_from_shapes([hole_1, hole_2])

    shape = difference(shape, [translate(hole, (0., 0., oled_mount_bezel_thickness))])

    clip_leg = box(oled_clip_width, oled_clip_thickness, oled_leg_depth)
    clip_leg = translate(clip_leg, (
        0.,
        0.,
        # (oled_mount_height+2*oled_clip_overhang+oled_clip_thickness)/2,
        -oled_leg_depth / 2.
    ))

    latch_1 = box(
        oled_clip_width,
        oled_clip_overhang + oled_clip_thickness,
        .01
    )
    latch_2 = box(
        oled_clip_width,
        oled_clip_thickness / 2,
        oled_clip_extension
    )
    latch_2 = translate(latch_2, (
        0.,
        -(-oled_clip_thickness / 2 + oled_clip_thickness + oled_clip_overhang) / 2,
        -oled_clip_extension / 2
    ))
    latch = hull_from_shapes([latch_1, latch_2])
    latch = translate(latch, (
        0.,
        oled_clip_overhang / 2,
        -oled_leg_depth
    ))

    clip_leg = union([clip_leg, latch])

    clip_leg = translate(clip_leg, (
        0.,
        (oled_mount_height + 2 * oled_clip_overhang + oled_clip_thickness) / 2 - oled_clip_y_gap,
        0.
    ))

    shape = union([shape, clip_leg, mirror(clip_leg, 'XZ')])

    return shape


def oled_undercut_mount_frame():
    mount_ext_width = oled_mount_width + 2 * oled_mount_rim
    mount_ext_height = oled_mount_height + 2 * oled_mount_rim
    hole = box(mount_ext_width, mount_ext_height, oled_mount_cut_depth + .01)

    shape = box(mount_ext_width, mount_ext_height, oled_mount_depth)
    shape = difference(shape, [box(oled_mount_width, oled_mount_height, oled_mount_depth + .1)])
    undercut = box(
        oled_mount_width + 2 * oled_mount_undercut,
        oled_mount_height + 2 * oled_mount_undercut,
        oled_mount_depth)
    undercut = translate(undercut, (0., 0., -oled_mount_undercut_thickness))
    shape = difference(shape, [undercut])

    shape = rotate(shape, oled_mount_rotation_xyz)
    shape = translate(shape, (
            oled_mount_location_xyz[0],
            oled_mount_location_xyz[1],
            oled_mount_location_xyz[2],
        )
    )

    hole = rotate(hole, oled_mount_rotation_xyz)
    hole = translate(hole, (
            oled_mount_location_xyz[0],
            oled_mount_location_xyz[1],
            oled_mount_location_xyz[2],
        )
    )

    return hole, shape







def teensy_holder():
    print('teensy_holder()')
    teensy_top_xy = key_position(wall_locate3(-1, 0), 0, centerrow - 1)
    teensy_bot_xy = key_position(wall_locate3(-1, 0), 0, centerrow + 1)
    teensy_holder_length = teensy_top_xy[1] - teensy_bot_xy[1]
    teensy_holder_offset = -teensy_holder_length / 2
    teensy_holder_top_offset = (teensy_holder_top_length / 2) - teensy_holder_length

    s1 = box(3, teensy_holder_length, 6 + teensy_width)
    s1 = translate(s1, [1.5, teensy_holder_offset, 0])

    s2 = box(teensy_pcb_thickness, teensy_holder_length, 3)
    s2 = translate(s2,
                   (
                       (teensy_pcb_thickness / 2) + 3,
                       teensy_holder_offset,
                       -1.5 - (teensy_width / 2),
                   )
                   )

    s3 = box(teensy_pcb_thickness, teensy_holder_top_length, 3)
    s3 = translate(s3,
                   [
                       (teensy_pcb_thickness / 2) + 3,
                       teensy_holder_top_offset,
                       1.5 + (teensy_width / 2),
                   ]
                   )

    s4 = box(4, teensy_holder_top_length, 4)
    s4 = translate(s4,
                   [teensy_pcb_thickness + 5, teensy_holder_top_offset, 1 + (teensy_width / 2)]
                   )

    shape = union((s1, s2, s3, s4))

    shape = translate(shape, [-teensy_holder_width, 0, 0])
    shape = translate(shape, [-1.4, 0, 0])
    shape = translate(shape,
                      [teensy_top_xy[0], teensy_top_xy[1] - 1, (6 + teensy_width) / 2]
                      )

    return shape


def screw_insert_shape(bottom_radius, top_radius, height):
    debugprint('screw_insert_shape()')
    if bottom_radius == top_radius:
        base = translate(cylinder(radius=bottom_radius, height=height),
            (0, 0, -height / 2)
        )
    else:
        base = translate(cone(r1=bottom_radius, r2=top_radius, height=height), (0, 0, -height / 2))

    shape = union((
        base,
        translate(sphere(top_radius), (0, 0, height / 2)),
    ))
    return shape


def screw_insert(column, row, bottom_radius, top_radius, height):
    debugprint('screw_insert()')
    shift_right = column == lastcol
    shift_left = column == 0
    shift_up = (not (shift_right or shift_left)) and (row == 0)
    shift_down = (not (shift_right or shift_left)) and (row >= lastrow)

    if screws_offset == 'INSIDE':
        # debugprint('Shift Inside')
        shift_left_adjust = wall_base_x_thickness
        shift_right_adjust = -wall_base_x_thickness/2
        shift_down_adjust = -wall_base_y_thickness/2
        shift_up_adjust = -wall_base_y_thickness/3

    elif screws_offset == 'OUTSIDE':
        debugprint('Shift Outside')
        shift_left_adjust = 0
        shift_right_adjust = wall_base_x_thickness/2
        shift_down_adjust = wall_base_y_thickness*2/3
        shift_up_adjust = wall_base_y_thickness*2/3

    else:
        # debugprint('Shift Origin')
        shift_left_adjust = 0
        shift_right_adjust = 0
        shift_down_adjust = 0
        shift_up_adjust = 0

    if shift_up:
        position = key_position(
            list(np.array(wall_locate2(0, 1)) + np.array([0, (mount_height / 2) + shift_up_adjust, 0])),
            column,
            row,
        )
    elif shift_down:
        position = key_position(
            list(np.array(wall_locate2(0, -1)) - np.array([0, (mount_height / 2) + shift_down_adjust, 0])),
            column,
            row,
        )
    elif shift_left:
        position = list(
            np.array(left_key_position(row, 0)) + np.array(wall_locate3(-1, 0)) + np.array((shift_left_adjust,0,0))
        )
    else:
        position = key_position(
            list(np.array(wall_locate2(1, 0)) + np.array([(mount_height / 2), 0, 0]) + np.array((shift_right_adjust,0,0))
                 ),
            column,
            row,
        )


    shape = screw_insert_shape(bottom_radius, top_radius, height)
    shape = translate(shape, [position[0], position[1], height / 2])

    return shape

def screw_insert_thumb(bottom_radius, top_radius, height):
    if thumb_style == 'MINI':
        position = thumborigin()
        position = list(np.array(position) + np.array([-29, -51, -16]))
        position[2] = 0

    elif thumb_style == 'CARBONFET':
        position = thumborigin()
        position = list(np.array(position) + np.array([-48, -37, 0]))
        position[2] = 0

    else:
        position = thumborigin()
        position = list(np.array(position) + np.array([-21, -58, 0]))
        position[2] = 0

    shape = screw_insert_shape(bottom_radius, top_radius, height)
    shape = translate(shape, [position[0], position[1], height / 2])
    return shape

def screw_insert_all_shapes(bottom_radius, top_radius, height, offset=0):
    print('screw_insert_all_shapes()')
    shapes = [
        translate(screw_insert(3, lastrow, bottom_radius, top_radius, height), (0, 0, offset)),
        translate(screw_insert(3, 0, bottom_radius, top_radius, height), (0,0, offset)),
        translate(screw_insert(lastcol, 0, bottom_radius, top_radius, height), (0, 0, offset)),
        translate(screw_insert(lastcol, lastrow-1, bottom_radius, top_radius, height), (0, 0, offset)),
        translate(screw_insert_thumb(bottom_radius, top_radius, height), (0, 0, offset)),
    ]

    if use_joystick():
        shapes.append(translate(screw_insert(0, 0, bottom_radius, top_radius, height), (0, 10, offset)))    
        shapes.append(translate(screw_insert_joystick(bottom_radius, top_radius, height), (0, 0, offset)))
    else:
        shapes.extend([
            translate(screw_insert(0, 0, bottom_radius, top_radius, height), (0, 0, offset)),
            translate(screw_insert(0, lastrow-1, bottom_radius, top_radius, height), (0, left_wall_lower_y_offset, offset)),
        ])
    return shapes

def screw_insert_holes():
    return screw_insert_all_shapes(
        screw_insert_bottom_radius, screw_insert_top_radius, screw_insert_height+.02, offset=-.01
    )

def screw_insert_outers():
    return screw_insert_all_shapes(
        screw_insert_bottom_radius + 1.6,
        screw_insert_top_radius + 1.6,
        screw_insert_height + 1.5,
    )

def screw_insert_screw_holes():
    return screw_insert_all_shapes(1.7, 1.7, 350)




def wire_post(direction, offset):
    debugprint('wire_post()')
    s1 = box(
        wire_post_diameter, wire_post_diameter, wire_post_height
    )
    s1 = translate(s1, [0, -wire_post_diameter * 0.5 * direction, 0])

    s2 = box(
        wire_post_diameter, wire_post_overhang, wire_post_diameter
    )
    s2 = translate(s2,
                   [0, -wire_post_overhang * 0.5 * direction, -wire_post_height / 2]
                   )

    shape = union((s1, s2))
    shape = translate(shape, [0, -offset, (-wire_post_height / 2) + 3])
    shape = rotate(shape, [-alpha / 2, 0, 0])
    shape = translate(shape, (3, -mount_height / 2, 0))

    return shape


def wire_posts():
    debugprint('wire_posts()')
    shape = thumb_ml_place(wire_post(1, 0).translate([-5, 0, -2]))
    shape = union([shape, thumb_ml_place(wire_post(-1, 6).translate([0, 0, -2.5]))])
    shape = union([shape, thumb_ml_place(wire_post(1, 0).translate([5, 0, -2]))])

    for column in range(lastcol):
        for row in range(lastrow - 1):
            shape = union([
                shape,
                key_place(wire_post(1, 0).translate([-5, 0, 0]), column, row),
                key_place(wire_post(-1, 6).translate([0, 0, 0]), column, row),
                key_place(wire_post(1, 0).translate([5, 0, 0]), column, row),
            ])
    return shape

def model_side(side="right"):
    print('model_right()')
    clearances = []
    shape, clearance = union([key_holes(side=side)])
    clearances.append(clearance)
    if debug_exports:
        export_file(shape=shape, fname=path.join(r"..", "things", r"debug_key_plates"))
    connector_shape = connectors()
    shape = union([shape, connector_shape])
    if debug_exports:
        export_file(shape=shape, fname=path.join(r"..", "things", r"debug_connector_shape"))
    thumb_shape, clearance = thumb(side=side)
    clearances.append(clearance)
    if debug_exports:
        export_file(shape=thumb_shape, fname=path.join(r"..", "things", r"debug_thumb_shape"))
    shape = union([shape, thumb_shape])
    if use_joystick():
        shape = union([shape, joystick_shape()])
        clearances.append(joystick_prox_cutout())
    thumb_connector_shape = thumb_connectors()
    shape = union([shape, thumb_connector_shape])
    if debug_exports:
        export_file(shape=shape, fname=path.join(r"..", "things", r"debug_thumb_connector_shape"))
    walls_shape = case_walls()
    if debug_exports:
        export_file(shape=walls_shape, fname=path.join(r"..", "things", r"debug_walls_shape"))
    s2 = union([walls_shape])
    s2 = union([s2, *screw_insert_outers()])

    if controller_mount_type in ['RJ9_USB_TEENSY', 'USB_TEENSY']:
        s2 = union([s2, teensy_holder()])

    if controller_mount_type in ['RJ9_USB_TEENSY', 'RJ9_USB_WALL', 'USB_WALL', 'USB_TEENSY']:
        s2 = union([s2, usb_holder()])
        s2 = difference(s2, [usb_holder_hole()])

    if controller_mount_type in ['RJ9_USB_TEENSY', 'RJ9_USB_WALL']:
        s2 = difference(s2, [rj9_space()])

    if controller_mount_type in ['EXTERNAL']:
        s2 = difference(s2, [external_mount_hole()])

    if controller_mount_type in ['None']:
        0 # do nothing, only here to expressly state inaction.

    s2 = difference(s2, [union(screw_insert_holes())])
    shape = union([shape, s2])

    if controller_mount_type in ['RJ9_USB_TEENSY', 'RJ9_USB_WALL']:
        shape = union([shape, rj9_holder()])

    if not use_joystick():
        if oled_mount_type == "UNDERCUT":
            hole, frame = oled_undercut_mount_frame()
            shape = difference(shape, [hole])
            shape = union([shape, frame])

        elif oled_mount_type == "SLIDING":
            hole, frame = oled_sliding_mount_frame()
            shape = difference(shape, [hole])
            shape = union([shape, frame])

        elif oled_mount_type == "CLIP":
            hole, frame = oled_clip_mount_frame()
            shape = difference(shape, [hole])
            shape = union([shape, frame])

    shape = difference(shape, clearances)
            
    block = box(350, 350, 40)
    block = translate(block, (0, 0, -20))
    shape = difference(shape, [block])

    if show_caps:
        shape = add([shape, thumbcaps()])
        shape = add([shape, caps()])

    if side == "left":
        shape = mirror(shape, 'YZ')

    return shape


# NEEDS TO BE SPECIAL FOR CADQUERY
def baseplate(wedge_angle=None):
    if ENGINE == 'cadquery':
        # shape = mod_r
        shape = union([case_walls(), *screw_insert_outers()])
        # tool = translate(screw_insert_screw_holes(), [0, 0, -10])
        tool = screw_insert_all_shapes(screw_hole_diameter/2., screw_hole_diameter/2., 350)
        for item in tool:
            item = translate(item, [0, 0, -10])
            shape = difference(shape, [item])

        shape = translate(shape, (0, 0, -0.01))

        square = cq.Workplane('XY').rect(1000, 1000)
        for wire in square.wires().objects:
            plane = cq.Workplane('XY').add(cq.Face.makeFromWires(wire))
        shape = intersect(shape, plane)

        outside = shape.vertices(cq.DirectionMinMaxSelector(cq.Vector(1, 0, 0), True)).objects[0]
        sizes = []
        max_val = 0
        inner_index = 0
        base_wires = shape.wires().objects
        for i_wire, wire in enumerate(base_wires):
            is_outside = False
            for vert in wire.Vertices():
                if vert.toTuple() == outside.toTuple():
                    outer_wire = wire
                    outer_index = i_wire
                    is_outside = True
                    sizes.append(0)
            if not is_outside:
                sizes.append(len(wire.Vertices()))
            if sizes[-1]>max_val:
                inner_index = i_wire
                max_val = sizes[-1]
        debugprint(sizes)
        inner_wire = base_wires[inner_index]

        # inner_plate = cq.Workplane('XY').add(cq.Face.makeFromWires(inner_wire))
        if wedge_angle is not None:
            cq.Workplane('XY').add(cq.Solid.revolve(outerWire, innerWires, angleDegrees, axisStart, axisEnd))
        else:
            inner_shape = cq.Workplane('XY').add(cq.Solid.extrudeLinear(outerWire=inner_wire, innerWires=[], vecNormal=cq.Vector(0, 0, base_thickness)))
            inner_shape = translate(inner_shape, (0, 0, -base_rim_thickness))

            holes = []
            for i in range(len(base_wires)):
                if i not in [inner_index, outer_index]:
                    holes.append(base_wires[i])
            cutout = [*holes, inner_wire]

            shape = cq.Workplane('XY').add(cq.Solid.extrudeLinear(outer_wire, cutout, cq.Vector(0, 0, base_rim_thickness)))
            hole_shapes=[]
            for hole in holes:
                loc = hole.Center()
                hole_shapes.append(
                    translate(
                        cylinder(screw_cbore_diameter, screw_cbore_depth),
                        (loc.x, loc.y, 0)
                        # (loc.x, loc.y, screw_cbore_depth/2)
                    )
                )
            shape = difference(shape, hole_shapes)
            shape = translate(shape, (0, 0, -base_rim_thickness))
            shape = union([shape, inner_shape])


        return shape
    else:

        shape = union([
            case_walls(),
            *screw_insert_outers()
        ])

        tool = translate(union(screw_insert_screw_holes()), [0, 0, -10])

        shape = shape - tool

        shape = translate(shape, [0, 0, -0.01])

        return sl.projection(cut=True)(shape)

joystick_oled_rim = 10
joystick_plate_thickness = 8 #plate_thickness
joystick_z_height = 30 # Space under plate for gimbal mechanism.

def joystick_origin():
    origin = thumborigin()
    offset = [-85, 20, -20, 0]
    for i in range(0, 3):
        origin[i] += offset[i]
    origin[2] = joystick_z_height + joystick_plate_thickness/2
    return origin
    
def joystick_shape():
    y_offset = 0
    top = box(65, 65, joystick_plate_thickness)

    if use_oled():
        mount_plate = translate(box(65, joystick_oled_rim, joystick_plate_thickness), [0, 65./2 + 5, 0])
        top = union([top, mount_plate])
        oled_mount_location_xyz[0] = 0
        oled_mount_location_xyz[1] = 65./2 + 1
        oled_mount_location_xyz[2] = joystick_plate_thickness / 2 - oled_mount_depth / 2
        oled_mount_rotation_xyz[0] = 0
        oled_mount_rotation_xyz[1] = 0
        oled_mount_rotation_xyz[2] = 90

        if oled_mount_type == "UNDERCUT":
            oled_hole, oled_frame = oled_undercut_mount_frame()
        elif oled_mount_type == "SLIDING":
            oled_hole, oled_frame = oled_sliding_mount_frame()
        elif oled_mount_type == "CLIP":
            oled_hole, oled_frame = oled_clip_mount_frame()

        top = difference(top, [oled_hole])
        top = union([top, oled_frame])

    cutout = translate(cylinder(radius=24.25, height=2*joystick_plate_thickness), [0, y_offset, -joystick_plate_thickness/2])
    screwhole = translate(cylinder(radius=1.6, height=2*joystick_plate_thickness), [0, 0, -joystick_plate_thickness/2])
    corner_clearance = translate(cylinder(radius=5, height=5), [0, 0, -joystick_plate_thickness/2 - 5])
    countersink = translate(cylinder(radius=5.7/2, height=3.1), [0, 0, joystick_plate_thickness/2 - 3.1])
    screw_clearance = translate(cylinder(radius=5.7/2, height=20), [0, 0, joystick_plate_thickness/2])
    screw_dist = 54
    cutouts = [cutout]
    locator = translate(cylinder(radius=5.6/2, height=2.5), [0, 0, -joystick_plate_thickness/2])
    for i in range(-1, 2, 2):
        for j in range(-1, 2, 2):
            cutouts.append(translate(screwhole, [i * screw_dist/2.0, j * screw_dist/2.0 + y_offset, 0]))
            cutouts.append(translate(locator, [i * screw_dist/2.0, j * screw_dist/2.0 + y_offset, 0]))
            cutouts.append(translate(corner_clearance, [i * screw_dist/2.0, j * screw_dist/2.0 + y_offset, 0])) # Gimbal top plate corners
            cutouts.append(translate(countersink, [i * screw_dist/2.0, j * screw_dist/2.0 + y_offset, 0]))
            cutouts.append(translate(screw_clearance, [i * screw_dist/2.0, j * screw_dist/2.0 + y_offset, 0]))
    cutouts.append(translate(box(60, 57, 10), [0, y_offset, -joystick_plate_thickness/2 -10.0/2])) # Gimbal top plate
    cutout = union(cutouts)
    #top = difference(top, cutouts)
    if debug_exports:
        export_file(shape=top, fname=path.join(r"..", "things", r"debug_joystick"))
        
    shape = translate(top, joystick_origin())
    cutout = translate(cutout, joystick_origin())
    shape = union([shape, joystick_connection()])
    shape = difference(shape, [cutout])
    if show_caps:
        stick = translate(cylinder(radius=4, height=28), [0, y_offset, -joystick_plate_thickness/2 + 3.2])
        stick = translate(stick, joystick_origin())
        shape = union([shape, stick])

        # Also show the daughterboard PCB for fit purposes.
        gimbal_pcb = import_file(path.join("..", "src", "gimbal_daughterboard"))
        gimbal_pcb = rotate(gimbal_pcb, [90, 0, 0])
        gimbal_pcb = translate(gimbal_pcb, joystick_origin())
        gimbal_pcb = translate(gimbal_pcb, [1, 35, -21])
        shape = union([shape, gimbal_pcb])
        
    return shape

def joystick_prox_cutout():
    prox_cutout = joystick_prox_cutout_shape()
    #prox_cutout = rotate(prox_cutout, [0, 0, 45])
    prox_cutout = translate(prox_cutout, joystick_origin())
    prox_cutout = translate(prox_cutout, [20 + 10, -24 + 10, 1])
    return prox_cutout

def joystick_corners():
    origin = joystick_origin()
    size = 65./2
    for i in range(-1, 2, 2):
        for j in range(-1, 2, 2):
            yield [origin[0] + i * size, origin[1] + j * size, origin[2]]

joystick_z_offset = plate_thickness - joystick_plate_thickness / 2
            
def joystick_tl_place(shape):
    place = joystick_origin()
    size = 65./2
    place[0] -= size
    place[1] += size
    if use_oled():
        place[1] += joystick_oled_rim
    place[2] -= joystick_z_offset
    return translate(shape, place)

def joystick_bl_place(shape):
    place = joystick_origin()
    size = 65./2
    place[0] -= size
    place[1] -= size
    place[2] -= joystick_z_offset
    return translate(shape, place)

def joystick_bm_place(shape):
    place = joystick_origin()
    size = 65./2
    place[0] -= 5
    place[1] -= size
    place[2] -= joystick_z_offset
    return translate(shape, place)

def joystick_bm2_place(shape):
    place = joystick_origin()
    size = 65./2
    place[0] -= 5
    place[1] -= size + 4.5
    place[2] -= joystick_z_offset + 1
    return translate(shape, place)

def joystick_tr_place(shape): 
    place = joystick_origin()
    size = 65./2
    place[0] += size
    place[1] += size
    if use_oled():
        place[1] += joystick_oled_rim
    place[2] -= joystick_z_offset
    return translate(shape, place)   

def joystick_br_place(shape): 
    place = joystick_origin()
    size = 65./2
    place[0] += size
    place[1] -= size
    place[2] -= joystick_z_offset
    return translate(shape, place)   

def joystick_connection():
    joystick_x_offset = -8
    joystick_x, joystick_y, joystick_z = joystick_origin()
    joystick_z -= joystick_z_offset
    shapes = []
    for i in range(lastrow):
        y = i
        low = (y == (lastrow-1))
        (x, y, z) = left_key_position(i, 1)
        (x2, y2, z2) = left_key_position(i, -1, low_corner=low)
        x2 = x2 + joystick_x_offset if not low else joystick_origin()[0] + 65./2
        outer_x_offset = joystick_x_offset if i > 0 else joystick_x_offset + 1
        outer_z = joystick_z if i > 0 else joystick_z - 1
        shapes.append(hull_from_shapes([
            left_key_place(web_post(), i, 1),
            left_key_place(web_post(), i, -1, low_corner=low),
            #key_place(web_post_tl(), 0, i),
            #key_place(web_post_bl(), 0, i),
            translate(web_post(), (x + outer_x_offset, y, outer_z)),
            translate(web_post(), (x2, y2, joystick_z))
            ]))

    for i in range(lastrow - 1):
        y = i + 1
        low = (y == (lastrow-1))
        (x1, y1, z1) = left_key_position(y, 1)
        (x2, y2, z2) = left_key_position(y - 1, -1, low_corner=low)
        shapes.append(hull_from_shapes([
            left_key_place(web_post(), y, 1),
            left_key_place(web_post(), y - 1, -1),
            translate(web_post(), (x1 + joystick_x_offset, y1, joystick_z)),
            translate(web_post(), (x2 + joystick_x_offset, y2, joystick_z)),
        ]))

    i = lastrow - 1
    (x2, y2, z2) = left_key_position(i, -1, low_corner=True)
    x2 = joystick_origin()[0] + 65./2
    shapes.append(hull_from_shapes([
        left_key_place(web_post(), i, -1),
        translate(web_post(), (x2, y2, joystick_z)),
        thumb_tl_place(web_post_tl())]))
    shapes.append(hull_from_shapes([
        translate(web_post(), (x2, y2, joystick_z)),
        thumb_tl_place(web_post_tl()),
        joystick_br_place(web_post())
    ]))
    shapes.append(hull_from_shapes([
        thumb_tl_place(web_post_tl()),
        joystick_br_place(web_post()),
        thumb_ml_place(web_post_tr())
    ]))
    shapes.append(hull_from_shapes([
        joystick_br_place(web_post()),
        joystick_bm_place(web_post()),
        joystick_bm2_place(web_post()),
        thumb_ml_place(web_post_tr())
    ]))
    shapes.append(hull_from_shapes([
        thumb_ml_place(web_post_tl()),
        thumb_ml_place(web_post_tr()),
        joystick_bm2_place(web_post())
    ]))
    shapes.append(hull_from_shapes([
        thumb_ml_place(web_post_tl()),
        joystick_bm2_place(web_post()),
        thumb_bl_place(web_post_tr())
    ]))
    shapes.append(hull_from_shapes([
        thumb_bl_place(web_post_tl()),
        joystick_bm2_place(web_post()),
        thumb_bl_place(web_post_tr())
    ]))
    #shapes.append(hull_from_shapes([
    #    thumb_bl_place(web_post_tl()),
    #    joystick_bm_place(web_post()),
    #    joystick_bl_place(web_post())
    #]))
    shapes.append(hull_from_shapes([
        thumb_tl_place(web_post_tl()),
        left_key_place(web_post(), lastrow - 1, -1, low_corner=True),
        key_place(web_post_bl(), 0, lastrow - 1)
    ]))
    
    return union(shapes)
    
def joystick_wall():
    return union([
        #wall_brace(joystick_tl_place, 0, 0, web_post(), joystick_bl_place, 0, 0, web_post()), # tl bl
        #wall_brace(joystick_tl_place, 0, 0, web_post(), joystick_tr_place, 0, 0, web_post()), # tl tr
        #wall_brace(joystick_bl_place, 0, -1, web_post(), thumb_bl_place, -1, 0, web_post_tl()), # bl bl
        wall_brace(joystick_bm_place, 0, -1, web_post(), thumb_bl_place, -1, 0, web_post_tl()), # bl bl
        wall_brace(joystick_bm_place, 0, -1, web_post(), joystick_bl_place, 0, -1, web_post()), # bl bl
        wall_brace(joystick_bl_place, -1, 0, web_post(), joystick_bl_place, 0, -1, web_post()),
        wall_brace(joystick_bl_place, -1, 0, web_post(), joystick_tl_place, -1, 0, web_post()),
        wall_brace(joystick_tl_place, -1, 0, web_post(), joystick_tl_place, 0, 1, web_post()),
        #wall_brace(joystick_tl_place, 0, 1, web_post(), joystick_tr_place, -2, 1, web_post()),
        wall_brace(joystick_tl_place, 0, 1, web_post(), joystick_tr_place, -0.4, 1, web_post()),
        wall_brace(
            # Was             (lambda sh: left_key_place(sh, 0, 1,)), -1, 1.3, web_post(),
            (lambda sh: left_key_place(sh, 0, 1,)), -0.5, 0.9, web_post(),
            # joystick_tr_place, -2, 1, web_post()
            joystick_tr_place, -0.4, 1, web_post()
        ),
        wall_brace(
            # Was (lambda sh: left_key_place(sh, 0, 1,)), -1, 1.3, web_post(),
            (lambda sh: left_key_place(sh, 0, 1,)), -0.5, 0.9, web_post(),
            (lambda sh: key_place(sh, 0, 0,)), 0, 1, web_post_tl(),
        )

    ])

def screw_insert_joystick(bottom_radius, top_radius, height):
    shape = screw_insert_shape(bottom_radius, top_radius, height)
    size = 65./2
    place = joystick_origin()
    place[0] -= 5
    place[1] -= size + 4
    place[2] = height / 2
    shapes = []
    shapes.append(translate(shape, place))
    place = joystick_origin()
    place[0] -= size - 4
    place[1] += size + 4
    if use_oled():
        place[1] += joystick_oled_rim
    place[2] = height / 2
    shapes.append(translate(shape, place))
    place = joystick_origin()
    place[0] -= size + 3
    if use_oled():
        place[1] += joystick_oled_rim/2
    else:
        place[1] -= 5
    place[2] = height / 2
    shapes.append(translate(shape, place))
    return union(shapes)

def joystick_prox_cutout_shape():
    shape1 = translate(box(3.94 + 0.2, 2.36 + 0.2, 10), [0, 0, 5])
    shape2 = translate(box(25, 18, 10), [25./2 - 4 - 2.36/2, 0, -5])
    return union([shape1, shape2])

def run():

    mod_r = model_side(side="right")
    export_file(shape=mod_r, fname=path.join(save_path, config_name + r"_right"))

    if symmetry == "asymmetric":
        mod_l = model_side(side="left")
        export_file(shape=mod_l, fname=path.join(save_path, config_name + r"_left"))

    else:
        export_file(shape=mirror(mod_r, 'YZ'), fname=path.join(save_path, config_name + r"_left"))


    base = baseplate()
    export_file(shape=base, fname=path.join(save_path, config_name + r"_right_plate"))
    export_dxf(shape=base, fname=path.join(save_path, config_name + r"_right_plate"))

    lbase = mirror(base, 'YZ')
    export_file(shape=lbase, fname=path.join(save_path, config_name + r"_left_plate"))
    export_dxf(shape=lbase, fname=path.join(save_path, config_name + r"_left_plate"))

    if oled_mount_type == 'UNDERCUT':
        export_file(shape=oled_undercut_mount_frame()[1], fname=path.join(save_path, config_name + r"_oled_undercut_test"))

    if oled_mount_type == 'SLIDING':
        export_file(shape=oled_sliding_mount_frame()[1], fname=path.join(save_path, config_name + r"_oled_sliding_test"))

    if oled_mount_type == 'CLIP':
        oled_mount_location_xyz = (0.0, 0.0, -oled_mount_depth / 2)
        oled_mount_rotation_xyz = (0.0, 0.0, 0.0)
        export_file(shape=oled_clip(), fname=path.join(save_path, config_name + r"_oled_clip"))
        export_file(shape=oled_clip_mount_frame()[1],
                            fname=path.join(save_path, config_name + r"_oled_clip_test"))
        export_file(shape=union((oled_clip_mount_frame()[1], oled_clip())),
                            fname=path.join(save_path, config_name + r"_oled_clip_assy_test"))

# base = baseplate()
# export_file(shape=base, fname=path.join(save_path, config_name + r"_plate"))
if __name__ == '__main__':
    run()
