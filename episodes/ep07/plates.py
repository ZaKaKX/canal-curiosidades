"""EP07 (Torre Eiffel) plates — self-contained, built on kit/bl_scenes.py style.
usage: python plates.py <plate> <outdir>  -> <plate>.png + _nrm.png + _id.png (line passes)."""
import bpy, bmesh, math, sys, time, os

PLATE, OUTD = sys.argv[-2], sys.argv[-1]
PCT = int(os.environ.get("BL_PCT", "75"))
R = math.radians

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"
sc.cycles.samples = int(os.environ.get("BL_SAMPLES", "40")); sc.cycles.use_denoising = True
sc.render.resolution_x, sc.render.resolution_y = 1080, 1920
sc.render.resolution_percentage = PCT
sc.render.film_transparent = True
sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Punchy"
MATS = {}


def mat(name, color, rough=0.55, metal=0.0, emit=None, estr=0.0, alpha=1.0):
    if name in MATS: return MATS[name]
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough; b.inputs["Metallic"].default_value = metal
    if emit:
        b.inputs["Emission Color"].default_value = (*emit, 1); b.inputs["Emission Strength"].default_value = estr
    MATS[name] = m
    return m


def box(name, loc, scale, m, bevel=0.05, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(location=loc, rotation=rot)
    o = bpy.context.object; o.name = name; o.scale = scale
    bpy.ops.object.transform_apply(scale=True)
    if bevel:
        md = o.modifiers.new("b", "BEVEL"); md.width = bevel; md.segments = 2
    o.data.materials.append(m)
    return o


def cyl(name, loc, r, d, m, rot=(0, 0, 0), sc_=(1, 1, 1), verts=32):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=d, location=loc, rotation=rot, vertices=verts)
    o = bpy.context.object; o.name = name; o.scale = sc_; o.data.materials.append(m)
    bpy.ops.object.shade_smooth()
    return o


def sphere(name, loc, r, m, scl=(1, 1, 1), seg=32):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=seg // 2, radius=r, location=loc)
    o = bpy.context.object; o.name = name; o.scale = scl; o.data.materials.append(m); bpy.ops.object.shade_smooth()
    return o


def cone(name, loc, r1, r2, d, m, scl=(1, 1, 1), rot=(0, 0, 0), verts=40):
    bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=r1, radius2=r2, depth=d, location=loc, rotation=rot)
    o = bpy.context.object; o.name = name; o.scale = scl; o.data.materials.append(m); bpy.ops.object.shade_smooth()
    return o


def parent_all(objs, name):
    bpy.ops.object.empty_add(location=(0, 0, 0)); root = bpy.context.object; root.name = name
    for o in objs:
        o.parent = root
    return root


def set_world(col, strength):
    w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True
    bg = w.node_tree.nodes["Background"]; bg.inputs["Color"].default_value = (*col, 1); bg.inputs["Strength"].default_value = strength


def sun(rot, energy, col, angle=2):
    bpy.ops.object.light_add(type="SUN", rotation=tuple(R(a) for a in rot))
    l = bpy.context.object.data; l.energy = energy; l.color = col; l.angle = R(angle)


def area(loc, rot, energy, col, size=5):
    bpy.ops.object.light_add(type="AREA", location=loc, rotation=tuple(R(a) for a in rot))
    a = bpy.context.object.data; a.energy = energy; a.color = col; a.size = size


def camera(loc, target, lens=35, fstop=None, shift_y=0.0):
    bpy.ops.object.empty_add(location=target); tgt = bpy.context.object; tgt.name = "TGT"
    bpy.ops.object.camera_add(location=loc); cam = bpy.context.object; sc.camera = cam
    c = cam.constraints.new("TRACK_TO"); c.target = tgt; c.track_axis = "TRACK_NEGATIVE_Z"; c.up_axis = "UP_Y"
    cam.data.lens = lens; cam.data.shift_y = shift_y; cam.data.clip_end = 2000
    if fstop:
        cam.data.dof.use_dof = True; cam.data.dof.focus_object = tgt; cam.data.dof.aperture_fstop = fstop
    return cam


def ground(col=(0.55, 0.42, 0.28), size=160, strength=0.8, z=0.0, name="ground", center=(0, 30)):
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=160, y_subdivisions=160, size=size, location=(center[0], center[1], z))
    o = bpy.context.object; o.name = name
    tx = bpy.data.textures.new("gt" + name, "CLOUDS"); tx.noise_scale = 3
    dm = o.modifiers.new("d", "DISPLACE"); dm.texture = tx; dm.strength = strength
    o.data.materials.append(mat("g" + name, col, 0.95)); bpy.ops.object.shade_smooth()
    return o


def apply_bool(o, cutter, op="DIFFERENCE"):
    md = o.modifiers.new("bo", "BOOLEAN"); md.object = cutter; md.operation = op
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.modifier_apply(modifier="bo")
    bpy.data.objects.remove(cutter, do_unlink=True)


def join(objs, name):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join(); o = bpy.context.object; o.name = name
    return o




# ---------------- Torre Eiffel assets ----------------
IRON = (0.40, 0.27, 0.17)
HW = [(0, 6.25), (2.5, 4.9), (5.7, 3.6), (8.5, 2.7), (11.5, 2.0), (16, 1.3), (20, 0.9), (24, 0.6), (27.6, 0.45), (30, 0.32)]


def interp(tab, z):
    for (z0, a), (z1, b) in zip(tab, tab[1:]):
        if z <= z1:
            return a + (b - a) * (z - z0) / (z1 - z0)
    return tab[-1][1]


def loft(name, rings, m, thick):
    """rings: list of (z, cx, cy, half) -> square lattice column (triangulated + wireframe)."""
    me = bpy.data.meshes.new(name); bm = bmesh.new(); prev = None
    for z, cx, cy, h in rings:
        vs = [bm.verts.new((cx + sx * h, cy + sy * h, z)) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
        if prev:
            for k in range(4):
                bm.faces.new((prev[k], prev[(k + 1) % 4], vs[(k + 1) % 4], vs[k]))
        prev = vs
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(o)
    w = o.modifiers.new("w", "WIREFRAME"); w.thickness = thick; w.use_even_offset = True
    o.data.materials.append(m)
    return o


def eiffel(maxz=31.5, loc=(0, 0, 0), antenna=True):
    m = mat("iron", IRON, 0.6, 0.3); pl = mat("platf", (0.33, 0.22, 0.14), 0.7)
    objs = []
    # 4 legs up to the 2nd platform
    for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        rings = []
        z = 0.0
        while z <= min(11.5, maxz) + 1e-6:
            hw = interp(HW, z); lw = 1.25 + (1.0 - 1.25) * (z / 11.5)
            c = hw - lw
            rings.append((z, sx * c, sy * c, lw)); z += 0.72
        if len(rings) > 1:
            objs.append(loft(f"leg{sx}{sy}", rings, m, 0.09))
    if maxz > 11.5:
        rings = []; z = 11.5
        while z <= min(30.0, maxz) + 1e-6:
            rings.append((z, 0, 0, interp(HW, z))); z += 0.8
        objs.append(loft("shaft", rings, m, 0.07))
    # arches under the 1st platform
    if maxz >= 5.7:
        for k, rot in enumerate((0, 90, 180, 270)):
            bpy.ops.mesh.primitive_torus_add(major_radius=3.0, minor_radius=0.12, location=(0, 0, 0))
            t = bpy.context.object; t.data.materials.append(m)
            t.rotation_euler = (R(90), 0, 0); t.scale = (1.0, 1.0, 1.0)
            bpy.ops.object.transform_apply(rotation=True)
            cut = box("tcut", (0, 0, -2.0), (4, 1, 2), m, 0); apply_bool(t, cut)
            t.location = (0, -4.15, 2.2); t.scale = (1.1, 1, 1.0)
            par = parent_all([t], f"arch{k}"); par.rotation_euler = (0, 0, R(rot)); objs.append(par)
        objs.append(box("p1", (0, 0, 5.7), (3.95, 3.95, 0.32), pl, 0.04))
        for k in range(16):  # railing posts / gallery rhythm
            a = k / 16
        objs.append(box("p1b", (0, 0, 6.15), (3.85, 3.85, 0.12), m, 0.02))
    if maxz >= 11.5:
        objs.append(box("p2", (0, 0, 11.5), (2.25, 2.25, 0.25), pl, 0.03))
        objs.append(box("p2b", (0, 0, 11.9), (2.15, 2.15, 0.1), m, 0.02))
    if maxz >= 27.6:
        objs.append(box("p3", (0, 0, 27.6), (0.7, 0.7, 0.18), pl, 0.02))
        objs.append(box("cab", (0, 0, 28.3), (0.5, 0.5, 0.5), mat("cab", (0.5, 0.36, 0.22), 0.6), 0.03))
        objs.append(cyl("lant", (0, 0, 29.4), 0.3, 1.2, m, verts=16))
        objs.append(cone("cap", (0, 0, 30.3), 0.36, 0.08, 0.6, m, verts=16))
        if antenna:
            objs.append(cyl("ant", (0, 0, 31.6), 0.05, 2.6, mat("antm", (0.2, 0.2, 0.22), 0.4, 0.8), verts=8))
            objs.append(sphere("antb", (0, 0, 32.95), 0.11, mat("antr", (0.9, 0.15, 0.1), 0.4)))
    root = parent_all(objs, "tower"); root.location = loc
    return root


def scaffold(z0, z1, hw):
    wd = mat("scaf", (0.62, 0.48, 0.3), 0.85)
    for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        for k in range(4):
            box(f"sc{sx}{sy}{k}", (sx * (hw + 0.2), sy * (hw + 0.2) + k * 0.0, z0 + (z1 - z0) * k / 3), (0.6, 0.6, 0.05), wd, 0)
        box(f"scp{sx}{sy}", (sx * (hw + 0.6), sy * (hw + 0.6), (z0 + z1) / 2), (0.06, 0.06, (z1 - z0) / 2), wd, 0)
    # crane on top
    cm = mat("crane", (0.25, 0.22, 0.2), 0.6, 0.4)
    box("cr_m", (1.0, 0, z1 + 1.4), (0.08, 0.08, 1.4), cm, 0)
    box("cr_j", (1.8, 0, z1 + 2.8), (1.4, 0.06, 0.06), cm, 0)
    box("cr_r", (3.0, 0, z1 + 2.0), (0.02, 0.02, 0.8), cm, 0)


def haussmann(name, x, y, w, d, floors=5, col=(0.86, 0.8, 0.68), rot=0):
    st = mat("stone" + str(col), col, 0.85); rf = mat("zinc", (0.32, 0.36, 0.42), 0.6, 0.3)
    wn = mat("hwin", (0.12, 0.13, 0.16), 0.3); bal = mat("bal", (0.12, 0.12, 0.13), 0.5, 0.6)
    fh = 0.9; hgt = floors * fh + 0.5
    objs = [box(name + "b", (0, 0, hgt / 2), (w / 2, d / 2, hgt / 2), st, 0.03)]
    rb = box(name + "r", (0, 0, hgt + 0.55), (w / 2 - 0.05, d / 2 - 0.05, 0.55), rf, 0.02)
    objs.append(rb)
    # mansard taper via scale of top verts not needed: add slanted roof slabs front
    objs.append(box(name + "rf", (0, -d / 2 + 0.25, hgt + 0.5), (w / 2, 0.06, 0.6), rf, 0.01, rot=(R(-20), 0, 0)))
    n = max(2, int(w / 0.9))
    for f in range(floors):
        z = 0.6 + f * fh + 0.35
        for i in range(n):
            xx = -w / 2 + (i + 0.5) * w / n
            objs.append(box(name + f"w{f}{i}", (xx, -d / 2 - 0.02, z), (0.17, 0.03, 0.3), wn, 0))
        if f in (1, 4):
            objs.append(box(name + f"bl{f}", (0, -d / 2 - 0.12, z - 0.3), (w / 2, 0.12, 0.03), bal, 0))
    for i in range(n):  # dormers
        xx = -w / 2 + (i + 0.5) * w / n
        objs.append(box(name + f"dm{i}", (xx, -d / 2 + 0.15, hgt + 0.6), (0.14, 0.1, 0.22), wn, 0))
    objs.append(box(name + "shop", (0, -d / 2 - 0.03, 0.35), (w / 2 - 0.1, 0.03, 0.3), mat("shop", (0.18, 0.28, 0.24), 0.5), 0))
    root = parent_all(objs, name); root.location = (x, y, 0); root.rotation_euler = (0, 0, R(rot))
    return root


def street():
    ground((0.48, 0.45, 0.4), size=200, strength=0.02, center=(0, 40), name="ground")
    box("road", (0, 6, 0.02), (3.2, 40, 0.02), mat("cobble", (0.36, 0.34, 0.33), 0.9), 0)
    cols = [(0.88, 0.82, 0.7), (0.84, 0.77, 0.64), (0.9, 0.85, 0.74)]
    for side in (-1, 1):
        for k in range(6):
            y = -2 + k * 6.4
            haussmann(f"hs{side}{k}", side * 7.5, y, 6.2, 6.0, 5 + (k % 2), cols[k % 3], rot=-side * 90)
    # lamp posts
    lm = mat("lamp", (0.1, 0.12, 0.1), 0.5, 0.6); gl = mat("lampg", (1, 0.9, 0.6), emit=(1, 0.85, 0.5), estr=3)
    for side in (-1, 1):
        for k in range(4):
            y = -1 + k * 8
            cyl(f"lp{side}{k}", (side * 3.8, y, 1.4), 0.05, 2.8, lm, verts=8)
            sphere(f"lg{side}{k}", (side * 3.8, y, 2.9), 0.18, gl)


def pantheon(loc, s=1.0):
    st = mat("pstone", (0.86, 0.82, 0.72), 0.8); dm = mat("pdome", (0.62, 0.66, 0.68), 0.6, 0.2)
    objs = [box("pbase", (0, 0, 1.5 * s), (4 * s, 4 * s, 1.5 * s), st, 0.05),
            box("pport", (0, -4.6 * s, 1.4 * s), (2.6 * s, 0.8 * s, 1.4 * s), st, 0.03),
            cyl("pdrum", (0, 0, 4.0 * s), 1.9 * s, 2.2 * s, st, verts=48)]
    for k in range(20):
        a = math.pi * 2 * k / 20
        objs.append(cyl(f"pc{k}", (math.cos(a) * 2.1 * s, math.sin(a) * 2.1 * s, 4.0 * s), 0.1 * s, 2.0 * s, st, verts=10))
    objs.append(cyl("pring", (0, 0, 5.15 * s), 2.25 * s, 0.2 * s, st, verts=48))
    objs.append(sphere("pdomes", (0, 0, 5.2 * s), 1.85 * s, dm, scl=(1, 1, 1.1)))
    objs.append(cyl("plant", (0, 0, 7.6 * s), 0.3 * s, 0.9 * s, st, verts=16))
    objs.append(cone("plc", (0, 0, 8.25 * s), 0.34 * s, 0.05 * s, 0.5 * s, dm, verts=16))
    root = parent_all(objs, "pantheon"); root.location = loc
    return root


def chimney_scene():
    br = mat("brick", (0.55, 0.24, 0.16), 0.9); dk = mat("brickdk", (0.25, 0.12, 0.08), 0.9)
    cone("chim", (0, 0, 12), 1.6, 0.9, 24, br, verts=24)
    for z in (4, 9, 14, 19, 23.5):
        cyl(f"chb{z}", (0, 0, z), 1.6 - (z / 24) * 0.7 + 0.08, 0.35, dk, verts=24)
    box("fact", (-6, 3, 3), (4.5, 3, 3), mat("factw", (0.5, 0.3, 0.22), 0.9), 0.05)
    for i in range(4):
        cone(f"saw{i}", (-9.4 + i * 2.3, 3, 7.0), 1.6, 0.0, 2.0, mat("factr", (0.25, 0.26, 0.28), 0.7), verts=3, rot=(R(90), 0, 0))
    for i in range(5):
        box(f"fw{i}", (-9.5 + i * 1.8, -0.02, 3.2), (0.4, 0.04, 0.9), mat("fwin", (0.15, 0.15, 0.18), 0.3), 0)
    ground((0.4, 0.37, 0.33), size=200, strength=0.05, center=(0, 30), name="ground")


def radio_room():
    wall = mat("rwall", (0.48, 0.5, 0.42), 0.9); wood = mat("rdesk", (0.38, 0.24, 0.13), 0.7)
    blk = mat("ebon", (0.1, 0.09, 0.08), 0.4); br = mat("brass", (0.75, 0.55, 0.22), 0.3, 0.9)
    box("floor", (0, 0, 0), (6, 6, 0.02), mat("rfloor", (0.3, 0.22, 0.15), 0.8), 0)
    box("wall", (0, 3.0, 2.5), (6, 0.1, 2.5), wall, 0)
    box("desk", (0, 0.6, 0.9), (2.4, 0.9, 0.06), wood, 0.02)
    for sx in (-1, 1):
        box(f"dl{sx}", (sx * 2.2, 0.6, 0.45), (0.08, 0.8, 0.45), wood, 0)
    # big receiver box with dials
    box("rbox", (-0.6, 1.1, 1.55), (1.2, 0.45, 0.6), wood, 0.03)
    box("rpanel", (-0.6, 0.64, 1.55), (1.1, 0.02, 0.52), blk, 0.01)
    for i, x in enumerate((-1.3, -0.6, 0.1)):
        cyl(f"dial{i}", (x, 0.6, 1.62), 0.2, 0.06, br, rot=(R(90), 0, 0), verts=32)
        cyl(f"knob{i}", (x, 0.55, 1.62), 0.07, 0.08, blk, rot=(R(90), 0, 0), verts=16)
    for i in range(3):
        cyl(f"tube{i}", (-1.1 + i * 0.5, 1.1, 2.35), 0.09, 0.32, mat("glass", (0.9, 0.7, 0.4), 0.1, emit=(1, 0.6, 0.2), estr=4), verts=16)
    # coil
    cyl("coil", (1.4, 1.2, 1.4), 0.35, 0.9, mat("copper", (0.8, 0.42, 0.2), 0.35, 0.9), verts=32)
    for k in range(9):
        bpy.ops.mesh.primitive_torus_add(major_radius=0.37, minor_radius=0.025, location=(1.4, 1.2, 1.0 + k * 0.1))
        bpy.context.object.data.materials.append(br)
    # telegraph key
    box("kbase", (0.6, 0.0, 1.0), (0.25, 0.15, 0.04), wood, 0.01)
    box("klever", (0.6, 0.0, 1.1), (0.22, 0.03, 0.02), br, 0)
    cyl("kknob", (0.4, 0.0, 1.16), 0.05, 0.06, blk, verts=12)
    # papers
    box("paper", (-0.4, 0.0, 0.97), (0.3, 0.22, 0.005), mat("paper", (0.95, 0.92, 0.82), 0.9), 0)
    # wall map
    box("map", (1.8, 2.88, 2.6), (1.0, 0.02, 0.7), mat("mapc", (0.85, 0.78, 0.58), 0.9), 0.01)
    sphere("lampg", (-2.0, 0.8, 2.2), 0.16, mat("lampe", (1, 0.8, 0.4), emit=(1, 0.75, 0.35), estr=10))


def light(kind):
    if kind == "day":
        set_world((0.55, 0.7, 0.9), 0.9); sun((50, 0, -40), 4.0, (1.0, 0.93, 0.82))
    elif kind == "gold":
        set_world((0.85, 0.6, 0.4), 0.7); sun((70, 0, -50), 4.2, (1.0, 0.78, 0.55), 3)
    elif kind == "lamp":
        set_world((0.12, 0.1, 0.08), 0.5)
        area((-2, -3, 3.5), (55, 0, -30), 300, (1.0, 0.78, 0.5), 2.5)
        area((3, -2, 2.5), (60, 0, 40), 90, (0.6, 0.7, 1.0), 2)


def P(name):
    if name == "tower":
        light("day"); eiffel(); ground((0.45, 0.5, 0.3), size=300, strength=0.05, center=(0, 40))
        for k, x in enumerate((-26, -17, 17, 26)):
            haussmann(f"bg{k}", x, 22, 8, 6, 6)
        camera((4, -43, 2.6), (0, 0, 13.8), 30)
    elif name == "tower_build":
        light("gold"); eiffel(maxz=9.0, antenna=False); scaffold(6.2, 9.0, 2.6)
        ground((0.5, 0.44, 0.34), size=300, strength=0.05, center=(0, 40))
        for k, x in enumerate((-30, -20, 20, 30)):
            haussmann(f"bg{k}", x, 30, 8, 6, 6)
        camera((4, -34, 2.6), (0, 0, 7.5), 30)
    elif name == "tower_top":
        light("day"); eiffel()
        camera((5.5, -13, 24.0), (0, 0, 28.6), 35)
    elif name == "street":
        light("gold"); street()
        camera((0.8, -9, 1.7), (0, 12, 3.2), 28)
    elif name == "skyline":
        light("gold"); eiffel(loc=(-11, 40, 0))
        pantheon((7.5, 12, 0), 1.6)
        ground((0.45, 0.48, 0.32), size=400, strength=0.05, center=(0, 40))
        for k in range(10):
            haussmann(f"sk{k}", -24 + k * 5.4, -2 + (k % 3) * 2, 4.6, 4, 2 + k % 2, [(0.88, 0.82, 0.7), (0.84, 0.77, 0.64)][k % 2])
        camera((0, -36, 7), (0, 15, 9.0), 30)
    elif name == "chimney":
        light("gold"); chimney_scene()
        camera((6, -34, 4), (-2, 0, 12.5), 30)
    elif name == "radio":
        light("lamp"); radio_room()
        camera((0.8, -3.6, 2.1), (-0.1, 0.8, 1.55), 32)
    else:
        raise SystemExit("unknown plate " + name)
def render(name):
    P(name)
    t0 = time.time()
    sc.render.filepath = f"{OUTD}/{name}.png"; bpy.ops.render.render(write_still=True)
    ln = bpy.data.materials.new("ln"); ln.use_nodes = True; nt = ln.node_tree; nt.nodes.clear()
    geo = nt.nodes.new("ShaderNodeNewGeometry"); oi = nt.nodes.new("ShaderNodeObjectInfo")
    vm = nt.nodes.new("ShaderNodeVectorMath"); vm.operation = "MULTIPLY_ADD"
    vm.inputs[1].default_value = (0.5, 0.5, 0.5); vm.inputs[2].default_value = (0.5, 0.5, 0.5)
    nt.links.new(geo.outputs["Normal"], vm.inputs[0])
    em = nt.nodes.new("ShaderNodeEmission"); mo = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(vm.outputs[0], em.inputs["Color"]); nt.links.new(em.outputs[0], mo.inputs["Surface"])
    flat = bpy.data.materials.new("flat"); flat.use_nodes = True; fn = flat.node_tree; fn.nodes.clear()
    fe = fn.nodes.new("ShaderNodeEmission"); fe.inputs["Color"].default_value = (0.5, 0.5, 1, 1)
    fo = fn.nodes.new("ShaderNodeOutputMaterial"); fn.links.new(fe.outputs[0], fo.inputs["Surface"])
    for o in bpy.data.objects:
        if o.type == "MESH":
            m = flat if o.name.startswith(("SEA", "bed", "ground", "floor", "ctfloor", "table", "road")) else ln
            if not o.data.materials: o.data.materials.append(m)
            for i in range(len(o.data.materials)): o.data.materials[i] = m
        if o.type == "LIGHT": o.hide_render = True
    sc.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0
    sc.cycles.samples = 12; sc.cycles.use_denoising = False; sc.cycles.filter_width = 0.8
    sc.render.dither_intensity = 0
    sc.view_settings.view_transform = "Standard"; sc.view_settings.look = "None"
    if sc.camera.data.dof: sc.camera.data.dof.use_dof = False
    sc.render.filepath = f"{OUTD}/{name}_nrm.png"; bpy.ops.render.render(write_still=True)
    nt.links.new(oi.outputs["Random"], em.inputs["Color"])
    sc.render.filepath = f"{OUTD}/{name}_id.png"; bpy.ops.render.render(write_still=True)
    print("PLATE", name, round(time.time() - t0, 1), "s")


render(PLATE)
