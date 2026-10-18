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


def loft(name, stations, material=None):
    """stations: list of (x, half_width, z_top, z_bottom) from front to rear."""
    verts, faces = [], []
    for (x, hw, zt, zb) in stations:
        verts += [(x, -hw, zb), (x, hw, zb), (x, hw, zt), (x, -hw, zt)]
    for i in range(len(stations) - 1):
        a, b = i * 4, (i + 1) * 4
        faces.append((a + 0, b + 0, b + 1, a + 1))
        faces.append((a + 1, b + 1, b + 2, a + 2))
        faces.append((a + 2, b + 2, b + 3, a + 3))
        faces.append((a + 3, b + 3, b + 0, a + 0))
    faces.append((0, 1, 2, 3))
    last = (len(stations) - 1) * 4
    faces.append((last + 3, last + 2, last + 1, last + 0))
    return mesh_from_verts(name, verts, faces, material)


def smooth(obj, angle=35):
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.shade_smooth()
    try:
        bpy.ops.object.shade_auto_smooth(angle=math.radians(angle))
    except Exception:
        pass


clean_scene()


# ---------------------------------------------------------------- materials
paint = mat("CarPaint", (0.72, 0.02, 0.03), metallic=0.85, rough=0.22)
bsdf = paint.node_tree.nodes.get("Principled BSDF")
if "Coat Weight" in bsdf.inputs:
    bsdf.inputs["Coat Weight"].default_value = 1.0
    bsdf.inputs["Coat Roughness"].default_value = 0.05

glass = mat("Glass", (0.02, 0.03, 0.05), metallic=0.4, rough=0.05)
tire = mat("Tire", (0.015, 0.015, 0.015), metallic=0.0, rough=0.92)
rim = mat("Rim", (0.75, 0.77, 0.80), metallic=1.0, rough=0.18)
dark = mat("DarkTrim", (0.03, 0.03, 0.03), metallic=0.2, rough=0.55)
chrome = mat("Chrome", (0.9, 0.9, 0.9), metallic=1.0, rough=0.08)
headlight = mat("Headlight", (1.0, 1.0, 0.9), emission=(1.0, 0.95, 0.75), emission_strength=8.0)
taillight = mat("Taillight", (0.6, 0.0, 0.0), emission=(1.0, 0.02, 0.02), emission_strength=5.0)
ground_m = mat("Ground", (0.32, 0.33, 0.35), rough=0.85)

parts = []

# ---------------------------------------------------------------- body
# lofted profile: nose is low and narrow, hood slopes up to the windshield,
# beltline is flat under the cabin, trunk slopes down to the tail.
stations = [
    (2.25, 0.76, 0.90, 0.46),   # nose face
    (2.08, 0.89, 0.99, 0.40),
    (1.75, 0.93, 1.04, 0.40),
    (1.45, 0.95, 1.08, 0.40),   # front axle
    (0.95, 0.95, 1.14, 0.40),
    (0.58, 0.95, 1.17, 0.40),   # windshield base
    (-0.90, 0.95, 1.17, 0.40),  # beltline under cabin
    (-1.45, 0.94, 1.14, 0.40),  # rear axle
    (-1.95, 0.90, 1.08, 0.40),
    (-2.25, 0.76, 1.00, 0.46),  # tail face
]
body = loft("Body", stations, paint)

cutters = []
for x in (1.45, -1.45):
    for y in (0.85, -0.85):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.5, depth=0.7, location=(x, y, 0.42),
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

bev = body.modifiers.new("Bevel", "BEVEL")
bev.width = 0.06
bev.segments = 4
bev.limit_method = "ANGLE"
bev.angle_limit = math.radians(40)
parts.append(body)

# ---------------------------------------------------------------- greenhouse
zb, zt = 1.10, 1.72
b_x0, b_x1 = -0.98, 0.62
t_x0, t_x1 = -0.72, 0.30
b_y, t_y = 0.86, 0.76
verts = [
    (b_x0, -b_y, zb), (b_x1, -b_y, zb), (b_x1, b_y, zb), (b_x0, b_y, zb),
    (t_x0, -t_y, zt), (t_x1, -t_y, zt), (t_x1, t_y, zt), (t_x0, t_y, zt),
]
faces = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (2, 3, 7, 6), (1, 2, 6, 5), (0, 4, 7, 3)]
glass_obj = mesh_from_verts("Greenhouse", verts, faces, glass)
gbev = glass_obj.modifiers.new("Bevel", "BEVEL")
gbev.width = 0.03
gbev.segments = 2
parts.append(glass_obj)

# roof cap (paint)
roof = box("Roof", (1.52, 1.56, 0.08), ((t_x0 + t_x1) / 2, 0, zt + 0.02), paint, bevel=0.03)
parts.append(roof)

# pillars: A (raked), B (straight), C (raked)
for x, z, w, tilt in ((0.66, 1.40, 0.10, -30), (-0.10, 1.41, 0.08, 0), (-1.00, 1.40, 0.10, 26)):
    p = box("Pillar", (w, 1.76, 0.66), (x, 0, z), paint, bevel=0.015,
            rot=(0, math.radians(tilt), 0))
    parts.append(p)

# ---------------------------------------------------------------- details
parts.append(box("BumperF", (0.30, 1.62, 0.26), (2.18, 0, 0.52), dark, bevel=0.05))
parts.append(box("BumperR", (0.30, 1.68, 0.26), (-2.18, 0, 0.54), dark, bevel=0.05))
parts.append(box("Grille", (0.08, 0.86, 0.20), (2.24, 0, 0.74), dark, bevel=0.02))
parts.append(box("SkirtL", (2.5, 0.08, 0.12), (0, 0.94, 0.42), dark))
parts.append(box("SkirtR", (2.5, 0.08, 0.12), (0, -0.94, 0.42), dark))

# mirrors
for y in (1.02, -1.02):
    parts.append(box("Mirror", (0.18, 0.10, 0.13), (0.52, y, 1.24), paint, bevel=0.02))

# lights (follow the nose/tail taper)
for y in (0.50, -0.50):
    parts.append(box("Headlight", (0.12, 0.40, 0.15), (2.20, y, 0.82), headlight, bevel=0.02,
                     rot=(0, math.radians(-6), 0)))
    parts.append(box("Taillight", (0.10, 0.42, 0.14), (-2.20, y, 0.88), taillight, bevel=0.02,
                     rot=(0, math.radians(6), 0)))

# exhausts
for y in (0.40, -0.40):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.06, depth=0.18, location=(-2.30, y, 0.44),
                                        rotation=(0, math.pi / 2, 0))
    ex = bpy.context.active_object
    ex.name = "Exhaust"
    assign(ex, chrome)
    smooth(ex)
    parts.append(ex)

# ---------------------------------------------------------------- wheels
for wx, wy in [(1.45, 0.88), (1.45, -0.88), (-1.45, 0.88), (-1.45, -0.88)]:
    side = 1 if wy > 0 else -1
    bpy.ops.mesh.primitive_cylinder_add(radius=0.42, depth=0.32, location=(wx, wy, 0.42),
                                        rotation=(math.pi / 2, 0, 0), vertices=48)
    t = bpy.context.active_object
    t.name = "Tire"
    assign(t, tire)
    smooth(t)
    parts.append(t)

    bpy.ops.mesh.primitive_cylinder_add(radius=0.25, depth=0.34, location=(wx, wy, 0.42),
                                        rotation=(math.pi / 2, 0, 0), vertices=32)
    r = bpy.context.active_object
    r.name = "Rim"
    assign(r, rim)
    smooth(r)
    parts.append(r)

    bpy.ops.mesh.primitive_cylinder_add(radius=0.08, depth=0.38, location=(wx, wy, 0.42),
                                        rotation=(math.pi / 2, 0, 0), vertices=24)
    hub = bpy.context.active_object
    hub.name = "Hub"
    assign(hub, chrome)
    smooth(hub)
    parts.append(hub)

    for i in range(5):
        ang = i * 2 * math.pi / 5
        sx = wx + 0.13 * math.sin(ang)
        sz = 0.42 + 0.13 * math.cos(ang)
        bpy.ops.mesh.primitive_cube_add(size=1, location=(sx, wy + side * 0.175, sz))
        sp = bpy.context.active_object
        sp.name = "Spoke"
        sp.scale = (0.05, 0.03, 0.17)
        sp.rotation_euler[1] = ang
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        assign(sp, rim)
        parts.append(sp)

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
bg.inputs[0].default_value = (0.55, 0.65, 0.80, 1.0)
bg.inputs[1].default_value = 0.7

bpy.ops.object.light_add(type="SUN", location=(4, -3, 8))
sun = bpy.context.active_object
sun.data.energy = 4.0
sun.data.angle = math.radians(8)
sun.rotation_euler = (math.radians(45), math.radians(10), math.radians(35))

bpy.ops.object.light_add(type="AREA", location=(-4, 4, 5))
fill = bpy.context.active_object
fill.data.energy = 400
fill.data.size = 6
fill.rotation_euler = (math.radians(-35), math.radians(-25), 0)

bpy.ops.object.camera_add(location=(6.8, -6.2, 3.4))
cam = bpy.context.active_object
bpy.context.scene.camera = cam
bpy.ops.object.empty_add(type="PLAIN_AXES", location=(0, 0, 0.75))
target = bpy.context.active_object
target.name = "CamTarget"
con = cam.constraints.new("TRACK_TO")
con.target = target
con.track_axis = "TRACK_NEGATIVE_Z"
con.up_axis = "UP_Y"

# ---------------------------------------------------------------- render
scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 960
scene.render.resolution_y = 640
scene.render.image_settings.file_format = "PNG"
scene.render.filepath = OUT_RENDER
try:
    scene.eevee.taa_render_samples = 48
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
