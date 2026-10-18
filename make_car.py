import bpy
import math

OUT_BLEND = "/home/david/users/david/proggraming/car/car.blend"
OUT_RENDER = "/tmp/opencode/car_preview.png"

# ---------------------------------------------------------------- utils


def clean_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()


def mat(name, color, metallic=0.0, rough=0.5, emission=None, emission_strength=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = rough
    if emission is not None:
        if "Emission Color" in bsdf.inputs:
            bsdf.inputs["Emission Color"].default_value = (*emission, 1.0)
        bsdf.inputs["Emission Strength"].default_value = emission_strength
    return m


def assign(obj, material):
    obj.data.materials.clear()
    obj.data.materials.append(material)


def box(name, dims, loc, material=None, bevel=0.0, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = (dims[0], dims[1], dims[2])
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel > 0:
        mod = obj.modifiers.new("Bevel", "BEVEL")
        mod.width = bevel
        mod.segments = 3
        mod.limit_method = "ANGLE"
        mod.angle_limit = math.radians(40)
    if material:
        assign(obj, material)
    return obj


def mesh_from_verts(name, verts, faces, material=None):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.validate()
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode="OBJECT")
    if material:
        assign(obj, material)
    return obj


def ring(hw, z0, z1, r_top, r_bot, crown, n_arc=3, n_crown=4):
    """Closed rounded-rectangle cross-section (list of (y, z)), bottom->top->mirrored."""
    h = max(z1 - z0, 0.02)
    r_top = max(0.01, min(r_top, hw * 0.9, h * 0.45))
    r_bot = max(0.01, min(r_bot, hw * 0.9, h * 0.45))
    crown = max(0.0, min(crown, r_top * 1.5))
    right = [(0.0, z0), (hw - r_bot, z0)]
    cy = z0 + r_bot
    for i in range(1, n_arc + 1):
        t = -math.pi / 2 + (math.pi / 2) * (i / n_arc)
        right.append((hw - r_bot + r_bot * math.cos(t), cy + r_bot * math.sin(t)))
    right.append((hw, z1 - r_top))
    cx, cz = hw - r_top, z1 - r_top
    for i in range(1, n_arc + 1):
        t = (math.pi / 2) * (i / n_arc)
        right.append((cx + r_top * math.cos(t), cz + r_top * math.sin(t)))
    span = max(hw - r_top, 1e-4)
    for i in range(1, n_crown + 1):
        y = span * (1 - i / n_crown)
        right.append((y, z1 + crown * (1 - (y / span) ** 2)))
    return right[:-1] + [(-y, z) for (y, z) in reversed(right[1:-1])]


def loft_rings(name, stations, material=None, n_arc=3, n_crown=4):
    """stations: (x, hw, z0, z1, r_top, r_bot, crown) front to rear."""
    verts, faces = [], []
    rings = []
    for (x, hw, z0, z1, r_top, r_bot, crown) in stations:
        sec = ring(hw, z0, z1, r_top, r_bot, crown, n_arc, n_crown)
        rings.append(len(sec))
        verts += [(x, y, z) for (y, z) in sec]
    R = rings[0]
    for i in range(len(stations) - 1):
        a, b = i * R, (i + 1) * R
        for j in range(R):
            j2 = (j + 1) % R
            faces.append((a + j, a + j2, b + j2, b + j))
    faces.append(tuple(range(R - 1, -1, -1)))
    last = (len(stations) - 1) * R
    faces.append(tuple(last + j for j in range(R)))
    return mesh_from_verts(name, verts, faces, material)


def smooth(obj, angle=40):
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.shade_smooth()
    try:
        bpy.ops.object.shade_auto_smooth(angle=math.radians(angle))
    except Exception:
        pass


clean_scene()

# ---------------------------------------------------------------- materials
paint = mat("CarPaint", (0.48, 0.008, 0.012), metallic=0.9, rough=0.16)
bsdf = paint.node_tree.nodes.get("Principled BSDF")
if "Coat Weight" in bsdf.inputs:
    bsdf.inputs["Coat Weight"].default_value = 1.0
    bsdf.inputs["Coat Roughness"].default_value = 0.03

glass = mat("Glass", (0.015, 0.02, 0.03), metallic=0.5, rough=0.04)
tire = mat("Tire", (0.012, 0.012, 0.013), rough=0.88)
rim_dark = mat("RimDark", (0.28, 0.29, 0.31), metallic=1.0, rough=0.3)
rim_silver = mat("RimSilver", (0.85, 0.86, 0.88), metallic=1.0, rough=0.12)
brake = mat("Brake", (0.12, 0.12, 0.13), metallic=0.8, rough=0.5)
caliper = mat("Caliper", (0.55, 0.02, 0.02), metallic=0.3, rough=0.4)
dark = mat("DarkTrim", (0.02, 0.02, 0.022), rough=0.5)
chrome = mat("Chrome", (0.9, 0.9, 0.92), metallic=1.0, rough=0.06)
headlight = mat("Headlight", (0.9, 0.92, 1.0), rough=0.08,
                emission=(1.0, 0.97, 0.88), emission_strength=6.0)
taillight = mat("Taillight", (0.5, 0.0, 0.0), rough=0.12,
                emission=(1.0, 0.01, 0.01), emission_strength=4.0)
plate_m = mat("Plate", (0.85, 0.85, 0.82), rough=0.6)
ground_m = mat("Ground", (0.28, 0.29, 0.31), rough=0.45)

parts = []

# ---------------------------------------------------------------- body
# lofted with rounded cross-sections: low tapered nose, sloping hood,
# flat beltline, falling trunk. Radii/crown make it read as sheet metal.
stations = [
    (2.34, 0.58, 0.55, 0.80, 0.10, 0.09, 0.02),
    (2.26, 0.72, 0.48, 0.86, 0.12, 0.10, 0.03),
    (2.10, 0.83, 0.43, 0.93, 0.14, 0.10, 0.035),
    (1.85, 0.90, 0.40, 1.00, 0.16, 0.09, 0.04),
    (1.60, 0.93, 0.39, 1.06, 0.17, 0.09, 0.04),
    (1.48, 0.94, 0.39, 1.10, 0.17, 0.09, 0.04),
    (1.20, 0.95, 0.39, 1.15, 0.17, 0.09, 0.04),
    (0.85, 0.96, 0.39, 1.19, 0.16, 0.09, 0.04),
    (0.58, 0.96, 0.39, 1.21, 0.15, 0.09, 0.04),
    (0.10, 0.97, 0.39, 1.22, 0.14, 0.09, 0.04),
    (-0.50, 0.97, 0.39, 1.22, 0.14, 0.09, 0.04),
    (-1.00, 0.96, 0.39, 1.21, 0.15, 0.09, 0.04),
    (-1.40, 0.95, 0.39, 1.19, 0.16, 0.09, 0.04),
    (-1.62, 0.94, 0.39, 1.16, 0.17, 0.09, 0.04),
    (-1.90, 0.91, 0.40, 1.12, 0.17, 0.09, 0.04),
    (-2.12, 0.84, 0.43, 1.06, 0.15, 0.10, 0.04),
    (-2.28, 0.72, 0.48, 1.00, 0.13, 0.10, 0.035),
    (-2.36, 0.58, 0.55, 0.96, 0.11, 0.09, 0.02),
]
body = loft_rings("Body", stations, paint, n_arc=4, n_crown=5)

cutters = []
for x in (1.48, -1.48):
    for y in (0.86, -0.86):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.52, depth=0.8, location=(x, y, 0.42),
                                            rotation=(math.pi / 2, 0, 0))
        c = bpy.context.active_object
        cutters.append(c)
        mod = body.modifiers.new("Arch", "BOOLEAN")
        mod.object = c
        mod.operation = "DIFFERENCE"
bpy.context.view_layer.objects.active = body
body.select_set(True)
for mod in list(body.modifiers):
    bpy.ops.object.modifier_apply(modifier=mod.name)
for c in cutters:
    bpy.data.objects.remove(c, do_unlink=True)
smooth(body, 50)
parts.append(body)

# ---------------------------------------------------------------- greenhouse
g_stations = [
    (0.66, 0.86, 1.12, 1.22, 0.05, 0.05, 0.01),
    (0.42, 0.84, 1.12, 1.46, 0.08, 0.05, 0.015),
    (0.18, 0.82, 1.12, 1.62, 0.09, 0.05, 0.02),
    (-0.08, 0.81, 1.12, 1.71, 0.10, 0.05, 0.025),
    (-0.55, 0.80, 1.12, 1.73, 0.10, 0.05, 0.025),
    (-0.82, 0.81, 1.12, 1.71, 0.10, 0.05, 0.025),
    (-1.02, 0.82, 1.12, 1.58, 0.09, 0.05, 0.02),
    (-1.18, 0.84, 1.12, 1.36, 0.08, 0.05, 0.015),
    (-1.30, 0.86, 1.12, 1.22, 0.05, 0.05, 0.01),
]
greenhouse = loft_rings("Greenhouse", g_stations, glass, n_arc=3, n_crown=3)
smooth(greenhouse, 50)
parts.append(greenhouse)

# greenhouse front is closed by glass; interior omitted (glass is opaque)

# roof cap in body color
roof_st = [
    (-0.02, 0.78, 1.66, 1.735, 0.05, 0.04, 0.02),
    (-0.55, 0.79, 1.66, 1.755, 0.05, 0.04, 0.02),
    (-0.88, 0.78, 1.66, 1.735, 0.05, 0.04, 0.02),
]
roof = loft_rings("Roof", roof_st, paint, n_arc=3, n_crown=3)
smooth(roof, 50)
parts.append(roof)

# pillars
parts.append(box("APillar", (0.07, 0.09, 0.92), (0.28, 0.77, 1.44), paint, bevel=0.015,
                 rot=(0, math.radians(-56), 0)))
parts.append(box("APillar", (0.07, 0.09, 0.92), (0.28, -0.77, 1.44), paint, bevel=0.015,
                 rot=(0, math.radians(-56), 0)))
parts.append(box("BPillar", (0.06, 0.09, 0.64), (-0.42, 0.80, 1.44), paint, bevel=0.012))
parts.append(box("BPillar", (0.06, 0.09, 0.64), (-0.42, -0.80, 1.44), paint, bevel=0.012))
parts.append(box("CPillar", (0.08, 0.10, 0.80), (-1.02, 0.80, 1.42), paint, bevel=0.015,
                 rot=(0, math.radians(38), 0)))
parts.append(box("CPillar", (0.08, 0.10, 0.80), (-1.02, -0.80, 1.42), paint, bevel=0.015,
                 rot=(0, math.radians(38), 0)))

# ---------------------------------------------------------------- details
# bumpers (slightly darker valances)
parts.append(box("ValanceF", (0.22, 1.44, 0.22), (2.26, 0, 0.52), dark, bevel=0.06))
parts.append(box("ValanceR", (0.22, 1.48, 0.22), (-2.28, 0, 0.56), dark, bevel=0.06))

# grille with chrome slats
parts.append(box("Grille", (0.06, 0.80, 0.18), (2.30, 0, 0.72), dark, bevel=0.02))
for z in (0.67, 0.72, 0.77):
    parts.append(box("Slat", (0.03, 0.76, 0.015), (2.33, 0, z), chrome))

# side skirts / rocker trim
parts.append(box("SkirtL", (2.4, 0.06, 0.10), (0, 0.94, 0.40), dark))
parts.append(box("SkirtR", (2.4, 0.06, 0.10), (0, -0.94, 0.40), dark))

# door seams + handles
for y in (0.968, -0.968):
    for x in (0.55, -0.42, -1.12):
        parts.append(box("Seam", (0.014, 0.012, 0.72), (x, y, 0.80), dark))
    for x in (0.18, -0.78):
        parts.append(box("Handle", (0.14, 0.03, 0.035), (x, y, 1.06), chrome, bevel=0.01))

# mirrors: stalk + housing
for y in (1.0, -1.0):
    s = 1 if y > 0 else -1
    parts.append(box("MirrorStalk", (0.05, 0.10, 0.04), (0.52, y - s * 0.02, 1.24), dark))
    parts.append(box("Mirror", (0.16, 0.09, 0.11), (0.50, y + s * 0.05, 1.27), paint, bevel=0.03))

# headlights (rounded, on the fender corner)
for y in (0.46, -0.46):
    parts.append(box("Headlight", (0.16, 0.40, 0.15), (2.18, y, 0.80), headlight, bevel=0.045,
                     rot=(0, math.radians(-8), 0)))
    parts.append(box("Fog", (0.06, 0.14, 0.07), (2.28, y * 1.35, 0.50), headlight, bevel=0.02))

# full-width taillight bar + plate recess
parts.append(box("Taillight", (0.10, 1.30, 0.13), (-2.26, 0, 0.90), taillight, bevel=0.04))
parts.append(box("PlateR", (0.02, 0.36, 0.15), (-2.39, 0, 0.58), plate_m))
parts.append(box("PlateF", (0.02, 0.36, 0.15), (2.37, 0, 0.55), plate_m))

# trunk lip spoiler
parts.append(box("Lip", (0.16, 1.40, 0.035), (-2.05, 0, 1.10), paint, bevel=0.012,
                 rot=(0, math.radians(-8), 0)))

# exhaust tips
for y in (0.38, -0.38):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.055, depth=0.2, location=(-2.34, y, 0.48),
                                        rotation=(0, math.pi / 2, 0))
    ex = bpy.context.active_object
    ex.name = "Exhaust"
    assign(ex, chrome)
    smooth(ex)
    parts.append(ex)

# ---------------------------------------------------------------- wheels
for wx, wy in [(1.48, 0.88), (1.48, -0.88), (-1.48, 0.88), (-1.48, -0.88)]:
    side = 1 if wy > 0 else -1

    bpy.ops.mesh.primitive_cylinder_add(radius=0.42, depth=0.34, location=(wx, wy, 0.42),
                                        rotation=(math.pi / 2, 0, 0), vertices=64)
    t = bpy.context.active_object
    t.name = "Tire"
    tb = t.modifiers.new("Bevel", "BEVEL")
    tb.width = 0.07
    tb.segments = 5
    tb.limit_method = "ANGLE"
    tb.angle_limit = math.radians(40)
    assign(t, tire)
    smooth(t, 45)
    parts.append(t)

    bpy.ops.mesh.primitive_cylinder_add(radius=0.30, depth=0.06, location=(wx, wy + side * 0.10, 0.42),
                                        rotation=(math.pi / 2, 0, 0), vertices=48)
    d = bpy.context.active_object
    d.name = "RimDish"
    assign(d, rim_dark)
    smooth(d, 45)
    parts.append(d)

    bpy.ops.mesh.primitive_torus_add(major_radius=0.27, minor_radius=0.025,
                                     location=(wx, wy + side * 0.155, 0.42),
                                     rotation=(math.pi / 2, 0, 0),
                                     major_segments=48, minor_segments=12)
    lip = bpy.context.active_object
    lip.name = "RimLip"
    assign(lip, rim_silver)
    smooth(lip, 60)
    parts.append(lip)

    bpy.ops.mesh.primitive_cylinder_add(radius=0.075, depth=0.05,
                                        location=(wx, wy + side * 0.16, 0.42),
                                        rotation=(math.pi / 2, 0, 0), vertices=24)
    cap = bpy.context.active_object
    cap.name = "HubCap"
    assign(cap, chrome)
    smooth(cap, 45)
    parts.append(cap)

    for i in range(5):
        ang = i * 2 * math.pi / 5
        sx = wx + 0.15 * math.sin(ang)
        sz = 0.42 + 0.15 * math.cos(ang)
        bpy.ops.mesh.primitive_cube_add(size=1, location=(sx, wy + side * 0.155, sz))
        sp = bpy.context.active_object
        sp.name = "Spoke"
        sp.scale = (0.055, 0.035, 0.21)
        sp.rotation_euler[1] = ang
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        sb = sp.modifiers.new("Bevel", "BEVEL")
        sb.width = 0.012
        sb.segments = 2
        assign(sp, rim_silver)
        parts.append(sp)

    bpy.ops.mesh.primitive_cylinder_add(radius=0.19, depth=0.03,
                                        location=(wx, wy - side * 0.05, 0.42),
                                        rotation=(math.pi / 2, 0, 0), vertices=32)
    disc = bpy.context.active_object
    disc.name = "BrakeDisc"
    assign(disc, brake)
    smooth(disc, 45)
    parts.append(disc)

    parts.append(box("Caliper", (0.07, 0.05, 0.14), (wx + 0.14, wy - side * 0.05, 0.52),
                     caliper, bevel=0.015))

# ---------------------------------------------------------------- root + env
bpy.ops.object.empty_add(type="PLAIN_AXES", location=(0, 0, 0))
car_root = bpy.context.active_object
car_root.name = "Car"
for p in parts:
    p.parent = car_root

bpy.ops.mesh.primitive_plane_add(size=40, location=(0, 0, 0))
ground = bpy.context.active_object
ground.name = "Ground"
assign(ground, ground_m)

world = bpy.data.worlds.new("World")
bpy.context.scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
bg.inputs[0].default_value = (0.50, 0.58, 0.70, 1.0)
bg.inputs[1].default_value = 0.55

bpy.ops.object.light_add(type="SUN", location=(5, -4, 9))
sun = bpy.context.active_object
sun.data.energy = 3.0
sun.data.angle = math.radians(4)
sun.rotation_euler = (math.radians(48), math.radians(8), math.radians(30))

bpy.ops.object.light_add(type="AREA", location=(-5, 5, 6))
fill = bpy.context.active_object
fill.data.energy = 500
fill.data.size = 8
fill.rotation_euler = (math.radians(-40), math.radians(-30), 0)

bpy.ops.object.light_add(type="AREA", location=(2, -7, 4))
riml = bpy.context.active_object
riml.data.energy = 300
riml.data.size = 5
riml.rotation_euler = (math.radians(60), 0, math.radians(15))

bpy.ops.object.camera_add(location=(7.0, -5.6, 2.5))
cam = bpy.context.active_object
cam.data.lens = 55
bpy.context.scene.camera = cam
bpy.ops.object.empty_add(type="PLAIN_AXES", location=(0, 0, 0.72))
target = bpy.context.active_object
target.name = "CamTarget"
con = cam.constraints.new("TRACK_TO")
con.target = target
con.track_axis = "TRACK_NEGATIVE_Z"
con.up_axis = "UP_Y"

# ---------------------------------------------------------------- render
scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 1280
scene.render.resolution_y = 720
scene.render.image_settings.file_format = "PNG"
scene.render.filepath = OUT_RENDER
try:
    scene.eevee.taa_render_samples = 64
except Exception:
    pass
try:
    scene.eevee.use_raytracing = True
except Exception:
    pass

bpy.ops.wm.save_as_mainfile(filepath=OUT_BLEND)
bpy.ops.render.render(write_still=True)
print("SAVED:", OUT_BLEND)
print("RENDERED:", OUT_RENDER)
