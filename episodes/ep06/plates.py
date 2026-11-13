"""EP06 (Mecanismo de Anticítera) plates — self-contained, built on kit/bl_scenes.py style.
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


# ---------------- Anticítera assets ----------------
BRONZE = (0.62, 0.42, 0.2)
VERDIGRIS = (0.22, 0.42, 0.34)
WOOD = (0.45, 0.28, 0.14)


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


def gear(name, r, teeth, thick, m, spokes=4, loc=(0, 0, 0), rot=(R(90), 0, 0)):
    """flat gear in XY plane (axis Z) then rotated; default rot faces -Y (camera on -Y)."""
    rim = cyl(name + "rim", (0, 0, 0), r, thick, m, verts=96)
    cut = cyl(name + "cut", (0, 0, 0), r * 0.8, thick * 3, m, verts=64)
    apply_bool(rim, cut)
    parts = [rim]
    parts.append(cyl(name + "hub", (0, 0, 0), r * 0.16, thick * 1.6, m, verts=32))
    for k in range(spokes):
        a = math.pi * 2 * k / spokes
        sp = box(name + f"sp{k}", (math.cos(a) * r * 0.45, math.sin(a) * r * 0.45, 0), (r * 0.42, r * 0.06, thick / 2), m, 0, rot=(0, 0, a))
        parts.append(sp)
    tw = math.pi * 2 * r / teeth * 0.26
    for k in range(teeth):
        a = math.pi * 2 * k / teeth
        t = box(name + f"t{k}", (math.cos(a) * r * 1.02, math.sin(a) * r * 1.02, 0), (r * 0.05, tw, thick / 2), m, 0, rot=(0, 0, a))
        parts.append(t)
    g = join(parts, name)
    bpy.ops.object.shade_flat()
    g.location = loc; g.rotation_euler = rot
    return g


def amphora(name, loc, s=1.0, col=(0.62, 0.32, 0.18), tilt=(0, 0, 0)):
    m = mat("amph" + str(col), col, 0.85)
    objs = [sphere(name + "b", (0, 0, 0.55 * s), 0.32 * s, m, scl=(1, 1, 1.45)),
            cyl(name + "n", (0, 0, 1.1 * s), 0.09 * s, 0.4 * s, m, verts=16),
            cone(name + "f", (0, 0, 0.0), 0.02 * s, 0.12 * s, 0.25 * s, m, verts=16)]
    for sx in (-1, 1):
        objs.append(box(name + f"h{sx}", (sx * 0.14 * s, 0, 1.1 * s), (0.03 * s, 0.03 * s, 0.14 * s), m, 0, rot=(0, R(sx * 25), 0)))
    root = parent_all(objs, name); root.location = loc; root.rotation_euler = tilt
    return root


def ancient_ship(loc=(0, 0, 0), rot=(0, 0, 0), sail=True, cargo=True):
    hullm = mat("hull", (0.36, 0.22, 0.12), 0.75); dk = mat("deck", (0.55, 0.38, 0.22), 0.8)
    sl = mat("sailc", (0.9, 0.84, 0.7), 0.9); rp = mat("rope", (0.25, 0.18, 0.1), 0.9)
    objs = []
    h = sphere("hullb", (0, 0, 1.2), 1.0, hullm, scl=(6.0, 1.8, 1.5), seg=48)
    cutter = box("hcut", (0, 0, 2.7), (8, 3, 1.5), hullm, 0)
    apply_bool(h, cutter); objs.append(h)
    objs.append(box("deckp", (0, 0, 1.18), (5.4, 1.55, 0.06), dk, 0.02))
    # wale stripes
    for z in (0.75, 1.0):
        objs.append(box(f"wale{z}", (0, 0, z), (5.2, 1.62, 0.04), mat("wale", (0.2, 0.12, 0.07), 0.8), 0))
    # stern post curling up (back = +x), bow post
    objs.append(cone("stern", (6.0, 0, 2.2), 0.3, 0.08, 2.4, hullm, rot=(0, R(-35), 0), verts=12))
    objs.append(cone("bow", (-6.1, 0, 1.8), 0.25, 0.1, 1.4, hullm, rot=(0, R(30), 0), verts=12))
    objs.append(box("cabin", (3.8, 0, 1.7), (1.1, 1.2, 0.5), dk, 0.05))
    # steering oars
    for sy in (-1, 1):
        objs.append(box(f"soar{sy}", (5.3, sy * 1.75, 1.0), (0.08, 0.08, 1.4), rp, 0, rot=(0, R(25), 0)))
    if sail:
        objs.append(cyl("mast", (0, 0, 4.6), 0.12, 7.0, hullm, verts=12))
        objs.append(cyl("yard", (0, 0, 7.5), 0.08, 7.5, hullm, rot=(R(90), 0, 0), verts=10))
        s = box("sail", (0.15, 0, 5.4), (0.05, 3.5, 2.1), sl, 0.02)
        objs.append(s)
        for sy in (-1, 1):
            objs.append(box(f"stay{sy}", (0, sy * 1.0, 4.2), (0.02, 0.02, 3.4), rp, 0, rot=(R(sy * 16), 0, 0)))
    if cargo:
        for i, x in enumerate((-3.4, -2.6, -1.8, 1.4, 2.2)):
            for sy in (-0.6, 0.6):
                a = amphora(f"ca{i}{sy}", (x, sy, 1.2), 0.75); objs.append(a)
    root = parent_all(objs, "ship"); root.location = loc; root.rotation_euler = rot
    return root


def sea(z=0.35, kind="day", rough=0.06, chop=0.55, size=260, center=(0, 60)):
    cols = {"day": (0.02, 0.14, 0.22), "sunset": (0.03, 0.07, 0.11), "storm": (0.03, 0.05, 0.06)}
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=400, y_subdivisions=400, size=size, location=(center[0], center[1], z))
    oc = bpy.context.object; oc.name = "SEA"
    tx = bpy.data.textures.new("wv", "CLOUDS"); tx.noise_scale = 1.6; tx.noise_depth = 3
    dm = oc.modifiers.new("d", "DISPLACE"); dm.texture = tx; dm.strength = chop; dm.texture_coords = "GLOBAL"
    bpy.ops.object.shade_smooth()
    m = bpy.data.materials.new("sea"); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*cols[kind], 1); b.inputs["Roughness"].default_value = rough
    oc.data.materials.append(m)
    return oc


def island(loc=(0, 60, 0), s=1.0):
    rk = mat("isl", (0.5, 0.44, 0.32), 0.95); gr = mat("islg", (0.36, 0.42, 0.22), 0.95)
    for i, (x, y, h, r, m) in enumerate(((0, 0, 9, 22, rk), (-14, 4, 6, 14, gr), (12, 6, 7, 15, gr), (4, 10, 12, 18, rk))):
        o = cone(f"isl{i}", (loc[0] + x * s, loc[1] + y * s, h * s / 2 - 1), r * s, r * s * 0.25, h * s, m, verts=9)
        tx = bpy.data.textures.new(f"it{i}", "CLOUDS"); tx.noise_scale = 2
        bpy.context.view_layer.objects.active = o
        sub = o.modifiers.new("s", "SUBSURF"); sub.levels = 2
        dm = o.modifiers.new("d", "DISPLACE"); dm.texture = tx; dm.strength = 1.5 * s


def rowboat(loc=(0, 0, 0), rot=(0, 0, 0)):
    hm = mat("rowb", (0.62, 0.3, 0.16), 0.7); tm = mat("rowt", (0.85, 0.8, 0.68), 0.7)
    h = sphere("rbh", (0, 0, 0.4), 1.0, hm, scl=(2.4, 0.9, 0.7), seg=32)
    cut = box("rbcut", (0, 0, 1.0), (3, 2, 0.6), hm, 0); apply_bool(h, cut)
    objs = [h, box("rbrim", (0, 0, 0.42), (2.3, 0.86, 0.04), tm, 0.01)]
    for x in (-0.8, 0.6):
        objs.append(box(f"rbs{x}", (x, 0, 0.3), (0.15, 0.8, 0.04), tm, 0.01))
    for sy in (-1, 1):
        objs.append(box(f"oar{sy}", (0.2, sy * 1.5, 0.3), (0.05, 1.0, 0.05), tm, 0, rot=(R(sy * 15), 0, R(sy * 20))))
    root = parent_all(objs, "rowboat"); root.location = loc; root.rotation_euler = rot
    return root


def lump(name, loc, s=1.0, with_gear=True):
    m = mat("lump", VERDIGRIS, 0.95)
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=4, radius=0.5 * s, location=loc)
    o = bpy.context.object; o.name = name; o.scale = (1.3, 0.55, 0.9); o.data.materials.append(m)
    tx = bpy.data.textures.new(name + "t", "CLOUDS"); tx.noise_scale = 0.25
    dm = o.modifiers.new("d", "DISPLACE"); dm.texture = tx; dm.strength = 0.18 * s
    objs = [o]
    if with_gear:
        g = gear(name + "g", 0.3 * s, 28, 0.05 * s, mat("gearold", (0.42, 0.36, 0.2), 0.7, 0.5), spokes=4,
                 loc=(loc[0] + 0.1 * s, loc[1] - 0.3 * s, loc[2] + 0.05 * s), rot=(R(80), R(10), 0))
        objs.append(g)
    return objs


def statue(loc, s=1.0, rot=0):
    m = mat("marble", (0.82, 0.8, 0.74), 0.6)
    objs = [box("ped", (0, 0, 0.3 * s), (0.5 * s, 0.5 * s, 0.3 * s), m, 0.03),
            box("tor", (0, 0, 1.2 * s), (0.32 * s, 0.2 * s, 0.6 * s), m, 0.12),
            sphere("hd", (0, 0, 2.05 * s), 0.24 * s, m),
            box("arm", (0.42 * s, 0, 1.25 * s), (0.08 * s, 0.08 * s, 0.5 * s), m, 0.05, rot=(0, R(-20), 0))]
    root = parent_all(objs, "statue"); root.location = loc; root.rotation_euler = (R(8), R(-60), rot)
    return root


def seabed():
    sand = mat("sand", (0.42, 0.38, 0.28), 1.0)
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=120, y_subdivisions=120, size=120, location=(0, 10, -2.2))
    o = bpy.context.object; o.name = "bed"
    tx = bpy.data.textures.new("bt", "CLOUDS"); tx.noise_scale = 4
    dm = o.modifiers.new("d", "DISPLACE"); dm.texture = tx; dm.strength = 0.35
    o.data.materials.append(sand); bpy.ops.object.shade_smooth()
    rk = mat("rock", (0.2, 0.22, 0.2), 0.9)
    for i, (x, y, r) in enumerate(((-9, 6, 1.4), (8, 9, 1.1), (10, 3, 0.8), (-6, 14, 1.8))):
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=r, location=(x, y, -1.8)); bpy.context.object.data.materials.append(rk)
    # wreck ribs
    rib = mat("rib", (0.5, 0.36, 0.22), 0.9)
    for k in range(6):
        y = 6 + k * 1.3
        for sx in (-1, 1):
            box(f"rib{k}{sx}", (sx * 1.6, y, -1.0), (0.12, 0.12, 1.2), rib, 0.02, rot=(0, R(sx * 28), 0))
    box("keel", (0, 9.5, -1.9), (0.2, 4.5, 0.15), rib, 0.02)
    for i, (x, y, tilt) in enumerate(((-2.6, 3.0, 70), (-1.6, 4.2, 20), (2.3, 3.4, 85), (3.4, 5.5, 40), (-3.6, 6.0, 0), (0.8, 7.6, 60))):
        amphora(f"sa{i}", (x, y, -1.75), 0.9, tilt=(R(tilt), 0, R(i * 50)))
    statue((-4.2, 9, -1.9), 1.0)
    gold = mat("gold", (1.0, 0.72, 0.28), 0.3, 1.0)
    for i in range(10):
        cyl(f"coin{i}", (1.0 + (i % 4) * 0.35, 2.2 + (i // 4) * 0.3, -1.65), 0.12, 0.03, gold, rot=(R(10 * i), 0, 0), verts=16)
    lump("bronzelump", (0.3, 1.6, -1.45), 1.2, with_gear=False)


def lab():
    wood = mat("table", (0.42, 0.26, 0.14), 0.7); wall = mat("labwall", (0.55, 0.48, 0.38), 0.9)
    box("tabletop", (0, 0, 0.9), (2.2, 1.1, 0.06), wood, 0.02)
    for sx in (-1, 1):
        for sy in (-1, 1):
            box(f"tl{sx}{sy}", (sx * 2.0, sy * 0.95, 0.45), (0.06, 0.06, 0.45), wood, 0)
    box("wall", (0, 3.2, 2.5), (6, 0.1, 2.5), wall, 0)
    box("floor", (0, 0, 0), (6, 6, 0.02), mat("labfloor", (0.3, 0.22, 0.15), 0.8), 0)
    for z in (1.9, 2.8):
        box(f"shelf{z}", (2.5, 3.0, z), (1.6, 0.2, 0.04), wood, 0)
        for k in range(4):
            amphora(f"sh{z}{k}", (1.4 + k * 0.7, 3.0, z + 0.04), 0.5)
    lump("labl", (0.0, -0.1, 1.2), 0.9, with_gear=True)
    # oil lamp glow
    sphere("lampg", (-1.4, 0.4, 1.2), 0.15, mat("lampe", (1, 0.8, 0.4), emit=(1, 0.7, 0.3), estr=12))
    cyl("lampb", (-1.4, 0.4, 1.0), 0.12, 0.2, mat("brass", (0.7, 0.5, 0.2), 0.4, 0.8))


def mechanism(loc=(0, 0, 0), rot=(0, 0, 0)):
    wood = mat("mbox", WOOD, 0.7); br = mat("bronze", BRONZE, 0.35, 0.9); dk = mat("bronzedk", (0.35, 0.22, 0.1), 0.4, 0.9)
    objs = [box("mbody", (0, 0.45, 0), (1.0, 0.45, 1.7), wood, 0.03)]
    objs.append(box("mplate", (0, -0.02, 0), (0.92, 0.03, 1.6), dk, 0.01))
    # big dial ring + zodiac ticks
    ring = cyl("dring", (0, -0.06, 0.15), 0.8, 0.04, br, rot=(R(90), 0, 0), verts=96)
    rc = cyl("drc", (0, -0.06, 0.15), 0.66, 0.2, br, rot=(R(90), 0, 0), verts=96); apply_bool(ring, rc)
    objs.append(ring)
    for k in range(36):
        a = math.pi * 2 * k / 36
        objs.append(box(f"tick{k}", (math.cos(a) * 0.73, -0.09, 0.15 + math.sin(a) * 0.73), (0.008, 0.01, 0.05), dk, 0, rot=(0, -a + math.pi / 2, 0)))
    objs.append(gear("mgear", 0.6, 72, 0.03, br, spokes=4, loc=(0, -0.08, 0.15)))
    objs.append(gear("mg2", 0.22, 24, 0.03, br, spokes=4, loc=(-0.55, -0.11, -1.2)))
    objs.append(gear("mg3", 0.28, 30, 0.03, br, spokes=4, loc=(0.42, -0.11, -1.15)))
    # pointers: sun (gold ball) + moon (silver/black ball)
    objs.append(box("ptr1", (0.0, -0.13, 0.5), (0.015, 0.01, 0.38), mat("gold", (1.0, 0.72, 0.28), 0.3, 1.0), 0, rot=(0, R(30), 0)))
    objs.append(box("ptr2", (0.0, -0.15, 0.4), (0.012, 0.01, 0.28), mat("silver", (0.8, 0.8, 0.82), 0.3, 1.0), 0, rot=(0, R(-60), 0)))
    objs.append(sphere("sunball", (0.33, -0.17, 0.72), 0.06, mat("gold", (1.0, 0.72, 0.28), 0.3, 1.0)))
    objs.append(sphere("moonball", (-0.47, -0.18, 0.43), 0.05, mat("moonb", (0.15, 0.15, 0.16), 0.4)))
    objs.append(cyl("hubc", (0, -0.15, 0.15), 0.05, 0.08, br, rot=(R(90), 0, 0)))
    # side crank (+x)
    objs.append(cyl("crank_ax", (1.08, 0.45, 0.15), 0.04, 0.2, br, rot=(0, R(90), 0)))
    objs.append(box("crank_arm", (1.18, 0.45, -0.05), (0.03, 0.04, 0.22), br, 0.01))
    objs.append(cyl("crank_h", (1.26, 0.45, -0.24), 0.04, 0.18, wood, rot=(0, R(90), 0)))
    root = parent_all(objs, "mech"); root.location = loc; root.rotation_euler = rot
    return root


def ct_room():
    wh = mat("ctw", (0.9, 0.92, 0.94), 0.4); gr = mat("ctg", (0.55, 0.6, 0.66), 0.5)
    ring = cyl("ctring", (0, 2, 1.6), 1.6, 0.9, wh, rot=(R(90), 0, 0), verts=96)
    hole = cyl("cthole", (0, 2, 1.6), 0.75, 2.0, wh, rot=(R(90), 0, 0), verts=64); apply_bool(ring, hole)
    box("ctbase", (0, 2, 0.4), (1.2, 0.5, 0.4), gr, 0.05)
    box("cttable", (0, -0.6, 1.0), (0.45, 2.6, 0.06), mat("ctt", (0.3, 0.55, 0.75), 0.4), 0.03)
    box("cttleg", (0, -1.8, 0.5), (0.3, 0.3, 0.5), gr, 0.03)
    box("ctfloor", (0, 0, 0), (10, 10, 0.02), mat("ctf", (0.75, 0.78, 0.8), 0.5), 0)
    box("ctwall", (0, 5, 3), (10, 0.1, 3), mat("ctwl", (0.62, 0.72, 0.8), 0.8), 0)
    lump("ctl", (0, -0.4, 1.25), 0.7, with_gear=True)
    sphere("ctlight", (0, 2, 2.62), 0.05, mat("ctle", (0.4, 0.8, 1), emit=(0.3, 0.8, 1), estr=8))


def clocktower():
    st = mat("tstone", (0.72, 0.66, 0.56), 0.85); rf = mat("troof", (0.24, 0.3, 0.38), 0.7)
    box("tower", (0, 0, 7), (2.2, 2.2, 7), st, 0.06)
    cone("troofc", (0, 0, 16.2), 3.0, 0.0, 4.4, rf, verts=4, rot=(0, 0, R(45)))
    face = cyl("tface", (0, -2.25, 9.5), 1.6, 0.1, mat("tfacec", (0.12, 0.2, 0.42), 0.6), rot=(R(90), 0, 0), verts=64)
    rim = cyl("trim", (0, -2.28, 9.5), 1.75, 0.08, mat("gold", (1.0, 0.72, 0.28), 0.3, 1.0), rot=(R(90), 0, 0), verts=64)
    rc = cyl("trc", (0, -2.28, 9.5), 1.6, 0.3, st, rot=(R(90), 0, 0), verts=64); apply_bool(rim, rc)
    inner = cyl("tin", (0, -2.33, 9.5), 0.9, 0.05, mat("tinc", (0.8, 0.6, 0.25), 0.4, 0.8), rot=(R(90), 0, 0), verts=64)
    gold = mat("gold", (1.0, 0.72, 0.28), 0.3, 1.0)
    for k in range(12):
        a = math.pi * 2 * k / 12
        box(f"hr{k}", (math.cos(a) * 1.35, -2.36, 9.5 + math.sin(a) * 1.35), (0.06, 0.02, 0.14), gold, 0, rot=(0, -a + math.pi / 2, 0))
    box("hand1", (0.3, -2.42, 9.9), (0.05, 0.02, 0.6), gold, 0, rot=(0, R(35), 0))
    sphere("hsun", (0.62, -2.45, 10.4), 0.16, gold)
    box("door", (0, -2.22, 1.2), (0.7, 0.05, 1.2), mat("tdoor", (0.25, 0.15, 0.08), 0.7), 0.02)
    for z in (5.0, 13.0):
        box(f"twin{z}", (0, -2.22, z), (0.35, 0.05, 0.7), mat("twin", (0.1, 0.1, 0.12), 0.4), 0.01)
    # neighbouring gabled houses
    pl = [mat(f"hpl{i}", c, 0.85) for i, c in enumerate(((0.86, 0.8, 0.68), (0.78, 0.6, 0.45), (0.82, 0.76, 0.66)))]
    rr = mat("hroof", (0.46, 0.22, 0.15), 0.85)
    for i, x in enumerate((-6.5, -4.0, 4.0, 6.5)):
        hh = 3.5 + (i % 2) * 1.2
        box(f"hs{i}", (x, 0.5, hh), (1.2, 1.6, hh), pl[i % 3], 0.04)
        cone(f"hsr{i}", (x, 0.5, 2 * hh + 1.1), 1.75, 0.0, 2.2, rr, verts=4, rot=(0, 0, R(45)))
        for z in (hh * 0.6, hh * 1.4):
            box(f"hw{i}{z:.1f}", (x, -1.12, z), (0.3, 0.04, 0.4), mat("hwin", (0.1, 0.1, 0.12), 0.4), 0.01)
    ground((0.42, 0.4, 0.36), size=120, strength=0.05, center=(0, 20), name="ground")


def light(kind):
    if kind == "day":
        set_world((0.55, 0.7, 0.9), 0.9); sun((50, 0, -40), 4.0, (1.0, 0.93, 0.82))
    elif kind == "sunset":
        set_world((0.9, 0.5, 0.3), 0.6); sun((80, 0, -30), 4.5, (1.0, 0.68, 0.42), 3)
    elif kind == "under":
        set_world((0.05, 0.3, 0.42), 1.4); sun((10, 0, 0), 3.0, (0.6, 0.9, 1.0), 8)
    elif kind == "lamp":
        set_world((0.12, 0.08, 0.05), 0.5)
        area((-2, -3, 3), (55, 0, -30), 260, (1.0, 0.75, 0.45), 2.5)
        area((3, -2, 2.5), (60, 0, 40), 80, (0.6, 0.7, 1.0), 2)
    elif kind == "studio":
        set_world((0.1, 0.09, 0.08), 0.5)
        area((-2.5, -4, 3), (55, 0, -30), 420, (1.0, 0.85, 0.65), 3)
        area((3, -3, 1), (75, 0, 45), 160, (0.6, 0.75, 1.0), 2)
    elif kind == "clinic":
        set_world((0.7, 0.8, 0.9), 0.8); area((0, -3, 5), (30, 0, 0), 700, (0.9, 0.95, 1.0), 6)


def hide(root_name):
    for o in bpy.data.objects:
        q = o
        while q is not None:
            if q.name == root_name:
                o.hide_render = True; break
            q = q.parent


def P(name):
    if name in ("ship_sea", "ship_layer"):
        light("sunset"); S = sea(kind="sunset", chop=0.5)
        ancient_ship(loc=(0, 0, 0), rot=(0, 0, R(-25)))
        camera((4, -22, 2.4), (0, 0, 3.4), 30, None)
        if name == "ship_layer": S.is_holdout = True
        else: hide("ship")
    elif name == "island":
        light("day"); sea(kind="day", chop=0.35)
        island(loc=(-6, 70, 0), s=1.0)
        rowboat(loc=(2.5, -4, 0.3), rot=(0, 0, R(20)))
        camera((0, -16, 2.4), (0, 30, 3.0), 30, None)
    elif name == "seabed":
        light("under"); seabed()
        camera((1.2, -6.0, 1.6), (0, 5, -1.6), 26, None)
    elif name == "lab":
        light("lamp"); lab()
        camera((0.6, -3.4, 2.0), (0, 0.2, 1.3), 34, None)
    elif name == "mech":
        light("studio")
        box("table", (0, 0, -1.75), (6, 6, 0.05), mat("mtable", (0.3, 0.2, 0.12), 0.6), 0)
        mechanism(loc=(0, 0, 0), rot=(0, 0, R(-18)))
        camera((1.3, -5.6, 0.9), (0.15, 0, 0.0), 34, None)
    elif name in ("gear_big", "gear_small"):
        light("studio")
        if name == "gear_big":
            gear("G", 1.0, 72, 0.06, mat("bronze", BRONZE, 0.35, 0.9), spokes=4)
        else:
            gear("G", 1.0, 24, 0.08, mat("bronze2", (0.7, 0.5, 0.25), 0.35, 0.9), spokes=4)
        camera((0, -6.2, 0), (0, 0, 0), 50, None)
    elif name == "ct":
        light("clinic"); ct_room()
        camera((3.4, -5.2, 2.4), (0, 0.6, 1.4), 30, None)
    elif name == "clocktower":
        light("day"); clocktower()
        camera((0, -20, 3.0), (0, 0, 8.5), 30, None)
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
            m = flat if o.name.startswith(("SEA", "bed", "ground", "floor", "ctfloor", "table")) else ln
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
