"""EP09 (Tsutomu Yamaguchi, Hiroshima e Nagasaki 1945) plates — self-contained, built on kit/bl_scenes.py style.
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




# ---------------- EP09 assets: Japanese city 1945, shipyard, drafting office, ruins, train, shelter ----------------
import random
WOOD = (0.42, 0.3, 0.2); ROOF = (0.17, 0.2, 0.27); PLASTER = (0.82, 0.78, 0.68)


def jhouse(name, x, y, w=3.0, d=2.4, h=1.6, rot=0, burnt=False):
    wl = mat("plaster_b" if burnt else "plaster", (0.12, 0.1, 0.09) if burnt else PLASTER, 0.9)
    wd = mat("woodb" if burnt else "wood", (0.08, 0.06, 0.05) if burnt else WOOD, 0.85)
    objs = []
    if burnt:
        # charred frame: posts + a couple of beams, no walls/roof
        for sx, sy in ((-1, -1), (1, 1)):
            if True:
                hh = h * (0.4 + 0.6 * random.random())
                objs.append(box(name + f"p{sx}{sy}", (sx * w / 2, sy * d / 2, hh / 2), (0.07, 0.07, hh / 2), wd, 0, rot=(R(random.uniform(-12, 12)), R(random.uniform(-12, 12)), 0)))
        objs.append(box(name + "bm", (0, -d / 2, h * 0.7), (w / 2, 0.06, 0.06), wd, 0, rot=(0, R(random.uniform(-15, 15)), 0)))
        for k in range(2):
            objs.append(box(name + f"rb{k}", (random.uniform(-w / 2, w / 2), random.uniform(-d / 2, d / 2), 0.1), (random.uniform(0.2, 0.6), 0.12, 0.08), wd if k % 2 else mat("rubble", (0.35, 0.32, 0.3), 0.95), 0.02, rot=(0, 0, R(random.uniform(0, 180)))))
    else:
        objs.append(box(name + "w", (0, 0, h / 2), (w / 2, d / 2, h / 2), wl, 0.02))
        for sx in (-1, 0, 1):
            objs.append(box(name + f"b{sx}", (sx * w / 2.02, -d / 2 - 0.02, h / 2), (0.06, 0.03, h / 2), wd, 0))
        objs.append(box(name + "sh", (0, -d / 2 - 0.03, h * 0.45), (w / 2.6, 0.02, h * 0.28), mat("shoji", (0.93, 0.9, 0.8), 0.9), 0))
        # hip roof: flattened 4-sided cone with eaves
        r = cone(name + "r", (0, 0, h + 0.55), 1.0, 0.25, 1.1, mat("roof", ROOF, 0.55, 0.2), verts=4, rot=(0, 0, R(45)), scl=((w + 0.9) / 1.414, (d + 0.9) / 1.414, 0.8))
        bpy.ops.object.shade_flat(); objs.append(r)
    root = parent_all(objs, name); root.location = (x, y, 0); root.rotation_euler = (0, 0, R(rot))
    return root


def dome_hall(x, y, ruined=False):
    """generic 1940s concrete hall with a dome (Western-style public building)."""
    cw = mat("hall", (0.78, 0.72, 0.6) if not ruined else (0.45, 0.42, 0.38), 0.85); wn = mat("hwin", (0.1, 0.12, 0.14), 0.4)
    objs = [box("hallb", (0, 0, 2.6), (4.5, 3.0, 2.6), cw, 0.04)]
    for i in range(7):
        for f in range(2):
            objs.append(box(f"hw{i}{f}", (-3.6 + i * 1.2, -3.02, 1.4 + f * 2.2), (0.3, 0.03, 0.6), wn, 0))
    objs.append(cyl("drum", (0, 0, 6.0), 2.0, 1.6, cw, verts=48))
    if ruined:
        st = mat("domesteel", (0.12, 0.1, 0.09), 0.5, 0.6)
        for k in range(12):
            a = 2 * math.pi * k / 12
            bpy.ops.mesh.primitive_torus_add(major_radius=2.0, minor_radius=0.05, location=(0, 0, 6.8), rotation=(R(90), 0, a), major_segments=48)
            o = bpy.context.object; o.data.materials.append(st); objs.append(o)
        bpy.ops.mesh.primitive_torus_add(major_radius=1.4, minor_radius=0.06, location=(0, 0, 8.2), major_segments=48)
        bpy.context.object.data.materials.append(st); objs.append(bpy.context.object)
        # cut away the top half of the hall walls irregularly
        for k in range(10):
            objs.append(box(f"deb{k}", (random.uniform(-6, 6), random.uniform(-5, 2), 0.3), (random.uniform(0.3, 0.9), random.uniform(0.3, 0.7), 0.3), cw, 0.05, rot=(R(random.uniform(-20, 20)), 0, R(random.uniform(0, 90)))))
    else:
        s = sphere("dome", (0, 0, 6.8), 2.0, mat("domeg", (0.25, 0.42, 0.36), 0.4, 0.5), scl=(1, 1, 0.85))
        objs.append(s)
    root = parent_all(objs, "hall"); root.location = (x, y, 0)
    return root


def hills(y=90, col=(0.22, 0.34, 0.2), n=7, hmax=26):
    for k in range(n):
        x = -90 + k * 30 + random.uniform(-6, 6)
        sphere(f"hill{k}", (x, y + random.uniform(-8, 8), -4), 22, mat("hill", col, 0.95), scl=(1.4, 1, hmax / 22 * random.uniform(0.7, 1.0)), seg=24)


def city(ruined=False, river=True):
    random.seed(7)
    ground((0.5, 0.46, 0.38) if not ruined else (0.32, 0.29, 0.26), size=260, strength=0.05, center=(0, 60), name="ground")
    if river:
        bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 26, 0.06)); rv = bpy.context.object; rv.name = "SEA_river"
        rv.scale = (200, 7, 1); rv.data.materials.append(mat("river", (0.2, 0.32, 0.38), 0.2))
        # bridge (T-shaped Aioi-like silhouette avoided: simple flat bridge)
        box("bridge", (-8, 26, 0.6), (1.6, 8.5, 0.15), mat("brconc", (0.6, 0.58, 0.55), 0.8), 0.02)
    dome_hall(10, 36, ruined)
    box("road", (2, 0, 0.04), (1.6, 22, 0.03), mat("dirt", (0.55, 0.48, 0.38) if not ruined else (0.3, 0.27, 0.24), 0.95), 0)
    for gx in range(-9, 10):
        for gy in range(-3, 9):
            yy = gy * 5.0 + (0 if gy < 4 else 4) + random.uniform(-0.6, 0.6)
            if 21 < yy < 32: continue
            xx = gx * 4.4 + random.uniform(-0.8, 0.8)
            if abs(xx - 10) < 7 and abs(yy - 36) < 6: continue
            if yy < -4 and abs(xx) < 6: continue
            if abs(xx - 2) < 2.6: continue  # main street
            jhouse(f"h{gx}_{gy}", xx, yy, random.uniform(2.6, 3.6), random.uniform(2.2, 2.8), random.uniform(1.4, 2.0), rot=random.choice((0, 90, 0, 0)) + random.uniform(-4, 4), burnt=ruined)
    hills(110, (0.24, 0.3, 0.2) if not ruined else (0.2, 0.2, 0.18), hmax=20)


def ship_hull(loc, ln=26, bm=4.0, hh=3.2, done=0.8):
    hm = mat("hull", (0.42, 0.18, 0.12), 0.6, 0.3)  # red primer
    me = bpy.data.meshes.new("hull"); bm_ = bmesh.new()
    secs = 18; rings = []
    for i in range(secs + 1):
        u = i / secs; x = -ln / 2 + ln * u
        taper = min(1.0, (1 - u) * 4.5) if u > 0.75 else min(1.0, u * 6 + 0.35)
        w = bm / 2 * max(0.08, taper)
        ring = [bm_.verts.new((x, -w, hh)), bm_.verts.new((x, -w * 0.95, hh * 0.35)), bm_.verts.new((x, -w * 0.6, 0)),
                bm_.verts.new((x, w * 0.6, 0)), bm_.verts.new((x, w * 0.95, hh * 0.35)), bm_.verts.new((x, w, hh))]
        rings.append(ring)
    for a, b in zip(rings, rings[1:]):
        for j in range(5):
            bm_.faces.new((a[j], b[j], b[j + 1], a[j + 1]))
    bm_.to_mesh(me); bm_.free()
    o = bpy.data.objects.new("hull", me); bpy.context.collection.objects.link(o); o.data.materials.append(hm)
    sm = o.modifiers.new("s", "SOLIDIFY"); sm.thickness = 0.1
    o.location = loc; o.rotation_euler = (0, R(-3), 0)
    # scaffolding ribs
    sc_ = mat("scaff", (0.35, 0.28, 0.2), 0.9)
    for i in range(10):
        x = loc[0] - ln / 2 + 2 + i * 2.5
        for sy in (-1, 1):
            box(f"sc{i}{sy}", (x, loc[1] + sy * (bm / 2 + 0.9), hh / 2 + 1.0), (0.06, 0.06, hh / 2 + 1.0), sc_, 0)
    return o


def crane(x, y, h=14, rot=0):
    st = mat("crane", (0.2, 0.22, 0.25), 0.5, 0.6)
    objs = []
    for sx in (-1, 1):
        for sy in (-1, 1):
            objs.append(box(f"cl{sx}{sy}", (sx * 0.7, sy * 0.7, h / 2), (0.1, 0.1, h / 2), st, 0))
    for k in range(int(h / 2)):
        objs.append(box(f"cb{k}", (0, -0.7, 1 + k * 2), (0.7, 0.05, 0.05), st, 0, rot=(0, R(30 if k % 2 else -30), 0)))
    objs.append(box("jib", (5, 0, h + 0.3), (8, 0.25, 0.25), st, 0))
    objs.append(box("cab", (0, 0, h - 0.5), (1.0, 1.0, 0.6), mat("cabc", (0.55, 0.18, 0.12), 0.6), 0.03))
    objs.append(box("cable", (10, 0, h - 3), (0.02, 0.02, 3.2), st, 0))
    root = parent_all(objs, "crane"); root.location = (x, y, 0); root.rotation_euler = (0, 0, R(rot))


def shipyard():
    random.seed(3)
    ground((0.45, 0.43, 0.4), size=200, strength=0.02, center=(0, 20), name="ground")
    bpy.ops.mesh.primitive_plane_add(size=400, location=(0, 236, 0.02)); w = bpy.context.object; w.name = "SEA_bay"
    w.data.materials.append(mat("bay", (0.12, 0.24, 0.3), 0.2))
    box("slip", (0, 20, 0.2), (18, 4.5, 0.2), mat("slipw", (0.4, 0.32, 0.24), 0.9), 0.02)
    ship_hull((0, 20, 0.6))
    crane(-14, 26, 15, 20); crane(16, 15, 13, 160)
    for k, x in enumerate((-30, -20, 26, 36)):
        box(f"shed{k}", (x, 8, 2.5), (4, 6, 2.5), mat("shed", (0.5, 0.46, 0.4), 0.85), 0.03)
        cone(f"shedr{k}", (x, 8, 5.6), 5.7, 0.3, 1.2, mat("shedroof", (0.28, 0.28, 0.3), 0.7), verts=4, rot=(0, 0, R(45)), scl=(0.72, 1.06, 1)); bpy.ops.object.shade_flat()
    # hills across the bay (Nagasaki is ringed by hills)
    for k in range(8):
        sphere(f"hill{k}", (-110 + k * 32, 120 + random.uniform(-10, 10), -6), 26, mat("hill", (0.22, 0.36, 0.22), 0.95), scl=(1.3, 1, random.uniform(0.9, 1.4)), seg=24)
    for k in range(40):  # houses on the hillside
        jhouse(f"hh{k}", random.uniform(-90, 90), random.uniform(95, 110), 3, 2.5, 1.6, rot=random.uniform(-10, 10))


def office(window_flash=False):
    ground((0.35, 0.27, 0.2), size=30, strength=0.0, center=(0, 0), name="floor")
    wl = mat("owall", (0.78, 0.74, 0.64), 0.9)
    box("wallb", (0, 5, 3), (9, 0.1, 3), wl, 0)
    # big window frame on back wall (sky shows through: wall split)
    box("wallL", (-6.2, 4.9, 3), (2.8, 0.12, 3), wl, 0)
    wf = mat("wframe", (0.3, 0.22, 0.15), 0.7)
    for k in range(4):
        box(f"wfv{k}", (-6.8 + k * 1.2, 4.8, 3.2), (0.05, 0.06, 1.4), wf, 0)
    box("wfh", (-5, 4.8, 3.2), (2.0, 0.06, 0.05), wf, 0)
    box("wpane", (-5, 4.85, 3.2), (1.9, 0.01, 1.35), mat("pane", (0.75, 0.85, 0.95), 0.05, emit=(0.8, 0.9, 1.0), estr=1.2), 0)
    dk = mat("desk", (0.38, 0.25, 0.14), 0.6)
    for k, (x, y) in enumerate(((-2.5, 1.5), (2.5, 1.5), (0, -1.0))):
        box(f"desk{k}", (x, y, 1.0), (1.4, 0.8, 0.05), dk, 0.02, rot=(R(-12) if k == 2 else 0, 0, 0))
        for sx in (-1, 1):
            for sy in (-1, 1):
                box(f"dl{k}{sx}{sy}", (x + sx * 1.3, y + sy * 0.7, 0.5), (0.05, 0.05, 0.5), dk, 0)
        box(f"paper{k}", (x, y, 1.07), (0.9, 0.55, 0.01), mat("paper", (0.82, 0.88, 0.95), 0.9), 0, rot=(R(-12) if k == 2 else 0, 0, R(5)))
    sphere("lamp", (2.5, 1.5, 2.2), 0.25, mat("lampe", (1, 0.95, 0.8), emit=(1, 0.95, 0.85), estr=5))
    box("cab", (6.5, 4.2, 1.2), (1.2, 0.5, 1.2), mat("cabw", (0.3, 0.22, 0.14), 0.7), 0.02)
    box("shelf", (6.5, 4.2, 2.6), (1.2, 0.5, 0.05), dk, 0)


def train():
    random.seed(11)
    ground((0.4, 0.5, 0.3), size=300, strength=0.6, center=(0, 40), name="ground")
    box("ballast", (0, 0, 0.12), (120, 1.6, 0.12), mat("ballast", (0.4, 0.38, 0.36), 0.95), 0)
    st = mat("rail", (0.3, 0.3, 0.32), 0.4, 0.8)
    for sy in (-0.7, 0.7):
        box(f"rail{sy}", (0, sy, 0.32), (120, 0.06, 0.08), st, 0)
    for k in range(160):
        box(f"tie{k}", (-120 + k * 1.5, 0, 0.24), (0.15, 1.2, 0.05), mat("tie", (0.25, 0.18, 0.12), 0.9), 0)
    bk = mat("loco", (0.06, 0.06, 0.07), 0.4, 0.5); rd = mat("locored", (0.5, 0.1, 0.08), 0.5, 0.2)
    # locomotive
    cyl("boiler", (4.5, 0, 2.1), 1.0, 6.0, bk, rot=(0, R(90), 0), verts=40)
    box("cabl", (0.6, 0, 2.3), (1.2, 1.25, 1.5), bk, 0.04)
    box("cabroof", (0.6, 0, 3.9), (1.5, 1.45, 0.1), bk, 0.02)
    cyl("stack", (6.8, 0, 3.4), 0.35, 1.2, bk, verts=24)
    cyl("dome1", (4.2, 0, 3.15), 0.45, 0.6, bk, verts=24)
    box("frame", (3.5, 0, 0.9), (4.2, 1.1, 0.25), rd, 0.02)
    for k, x in enumerate((1.5, 3.2, 4.9)):
        for sy in (-1, 1):
            cyl(f"wh{k}{sy}", (x, sy * 1.05, 0.95), 0.75, 0.15, rd, rot=(R(90), 0, 0), verts=28)
    # carriages
    cw = mat("carr", (0.3, 0.2, 0.12), 0.7)
    for c in range(3):
        x = -7 - c * 10
        box(f"car{c}", (x, 0, 2.2), (4.6, 1.3, 1.3), cw, 0.06)
        box(f"carroof{c}", (x, 0, 3.6), (4.7, 1.4, 0.15), bk, 0.06)
        for i in range(7):
            box(f"cw{c}{i}", (x - 3.6 + i * 1.2, -1.32, 2.5), (0.35, 0.02, 0.4), mat("cwin", (0.85, 0.75, 0.5), 0.4, emit=(1, 0.8, 0.5), estr=0.4), 0)
        for sx in (-3, 3):
            for sy in (-1, 1):
                cyl(f"cwh{c}{sx}{sy}", (x + sx, sy * 1.0, 0.6), 0.45, 0.12, rd, rot=(R(90), 0, 0), verts=20)
    for k in range(20):
        x = random.uniform(-100, 100); y = random.uniform(8, 60)
        cone(f"tree{k}", (x, y, 2.5), 1.6, 0, 5, mat("tree", (0.15, 0.3, 0.14), 0.9), verts=10)
    hills(120, (0.25, 0.38, 0.24), hmax=30)


def shelter():
    random.seed(5)
    ground((0.35, 0.28, 0.2), size=60, strength=0.3, center=(0, 0), name="ground")
    # earthen mound with timber-framed entrance
    m = sphere("mound", (0, 3, -1.0), 4.5, mat("earth", (0.3, 0.24, 0.17), 0.95), scl=(1.4, 1, 0.7), seg=40)
    tx = bpy.data.textures.new("mnd", "CLOUDS"); tx.noise_scale = 0.8
    dm = m.modifiers.new("d", "DISPLACE"); dm.texture = tx; dm.strength = 0.4
    tw = mat("timber", (0.3, 0.2, 0.12), 0.9)
    box("door_dark", (0, -0.75, 1.0), (0.9, 0.3, 1.0), mat("dark", (0.01, 0.01, 0.01), 1.0), 0)
    for sx in (-1, 1):
        box(f"post{sx}", (sx * 1.0, -1.05, 1.1), (0.12, 0.12, 1.1), tw, 0.02)
    box("lintel", (0, -1.05, 2.25), (1.3, 0.15, 0.14), tw, 0.02)
    for k in range(5):
        box(f"bag{k}", (-2.6 + k * 0.4 if k < 2 else 1.8 + (k - 2) * 0.4, -1.3, 0.25), (0.25, 0.4, 0.2), mat("sandbag", (0.55, 0.48, 0.35), 0.95), 0.08)
    for k in range(8):
        box(f"deb{k}", (random.uniform(-6, 6), random.uniform(-6, -2), 0.1), (random.uniform(0.2, 0.7), 0.1, 0.06), mat("woodb", (0.08, 0.06, 0.05), 0.9), 0.01, rot=(0, 0, R(random.uniform(0, 180))))


def light(kind):
    if kind == "summer":
        set_world((0.62, 0.74, 0.9), 1.0); sun((48, 0, -35), 4.2, (1.0, 0.95, 0.86), 2)
    elif kind == "ash":
        set_world((0.55, 0.45, 0.38), 0.9); sun((60, 0, -50), 2.6, (1.0, 0.75, 0.55), 4)
    elif kind == "dusk":
        set_world((0.3, 0.26, 0.32), 0.8); sun((80, 0, -60), 2.4, (1.0, 0.6, 0.4), 4)
    elif kind == "office":
        set_world((0.35, 0.35, 0.38), 0.7)
        area((-3, -3, 5), (40, 0, -30), 500, (1.0, 0.95, 0.88), 4)
        area((-5, 4, 3.2), (-80, 0, 0), 200, (0.8, 0.9, 1.0), 3)


def P(name):
    if name == "city":
        light("summer"); city()
        camera((-6, -16, 11), (4, 30, 1.5), 28)
    elif name == "ruins":
        light("ash"); city(ruined=True)
        camera((-6, -16, 11), (4, 30, 1.5), 28)
    elif name == "street":
        light("summer"); city()
        camera((1.6, -6, 1.7), (2.6, 30, 3.2), 24)
    elif name == "yard":
        light("summer"); shipyard()
        camera((-12, 0, 9.0), (2, 22, 1.8), 24)
    elif name == "office":
        light("office"); office()
        camera((0.0, -6.0, 2.4), (-1.8, 2.5, 2.1), 26)
    elif name == "train":
        light("dusk"); train()
        camera((14, -10, 1.8), (-2, 0, 2.2), 26)
    elif name == "shelter":
        light("dusk"); shelter()
        camera((1.8, -9.5, 1.6), (0, 1, 1.6), 30)
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
