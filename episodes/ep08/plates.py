"""EP08 (Enchente de melaço, Boston 1919) plates — self-contained, built on kit/bl_scenes.py style.
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



# ---------------- EP08 assets: Boston 1919 waterfront, molasses tank ----------------
TANKC = (0.30, 0.17, 0.08)   # tank painted brown
MOLC = (0.055, 0.022, 0.008)


def molasses_mat():
    return mat("molasses", MOLC, 0.12, 0.0)


def tank(loc=(0, 0, 0), r=6.75, h=7.5, leaks=True):
    """2.5M-gallon tank (~27 m wide x 15 m tall, scale 1u = 2 m)."""
    tm = mat("tank", TANKC, 0.6, 0.35); rv = mat("rivet", (0.2, 0.11, 0.05), 0.5, 0.5)
    objs = [cyl("tankw", (0, 0, h / 2), r, h, tm, verts=96)]
    objs.append(cone("tankroof", (0, 0, h + 0.55), r + 0.08, 0.6, 1.1, tm, verts=96))
    for k in range(1, 5):  # horizontal riveted seams
        bpy.ops.mesh.primitive_torus_add(major_radius=r + 0.02, minor_radius=0.05, location=(0, 0, k * h / 5), major_segments=96)
        bpy.context.object.data.materials.append(rv); objs.append(bpy.context.object)
    for k in range(10):  # vertical seams
        a = 2 * math.pi * k / 10
        objs.append(box(f"vs{k}", (math.cos(a) * (r + 0.02), math.sin(a) * (r + 0.02), h / 2), (0.04, 0.04, h / 2), rv, 0, rot=(0, 0, a)))
    # stair spiral (simple steps) + rail
    sm = mat("stair", (0.15, 0.13, 0.12), 0.5, 0.6)
    for k in range(26):
        a = R(-120 + k * 7.5); z = 0.3 + k * h / 26
        objs.append(box(f"st{k}", (math.cos(a) * (r + 0.35), math.sin(a) * (r + 0.35), z), (0.35, 0.18, 0.04), sm, 0, rot=(0, 0, a)))
    if leaks:
        lk = molasses_mat()
        for k, (a, z0, ln) in enumerate(((-100, 1.5, 2.2), (-80, 3.0, 3.5), (-65, 0.8, 1.6), (-110, 4.5, 4.0), (-90, 5.5, 2.5))):
            aa = R(a); zz = z0 - ln / 2 + 0.6
            objs.append(box(f"leak{k}", (math.cos(aa) * (r + 0.04), math.sin(aa) * (r + 0.04), max(ln / 2, zz)), (0.06, 0.05, ln / 2), lk, 0.03, rot=(0, 0, aa)))
    # concrete base ring
    objs.append(cyl("tankbase", (0, 0, 0.12), r + 0.4, 0.24, mat("conc", (0.55, 0.53, 0.5), 0.9), verts=96))
    root = parent_all(objs, "tank"); root.location = loc
    return root


def tank_burst(loc=(0, 0, 0), r=6.75, h=7.5):
    tm = mat("tank", TANKC, 0.6, 0.35); mol = molasses_mat()
    n = 11
    for k in range(n):
        a0 = 2 * math.pi * k / n + 0.05; a1 = 2 * math.pi * (k + 1) / n - 0.05
        me = bpy.data.meshes.new(f"pan{k}"); bm = bmesh.new(); seg = 8
        ring = []
        hk = h * (0.45 + 0.5 * ((k * 7) % 5) / 5)
        for j in range(seg + 1):
            a = a0 + (a1 - a0) * j / seg
            v0 = bm.verts.new((math.cos(a) * r, math.sin(a) * r, 0)); v1 = bm.verts.new((math.cos(a) * r, math.sin(a) * r, hk * (1 - 0.2 * abs(j / seg - 0.5))))
            ring.append((v0, v1))
        for (a, b), (c, d) in zip(ring, ring[1:]):
            bm.faces.new((a, c, d, b))
        bm.to_mesh(me); bm.free()
        o = bpy.data.objects.new(f"pan{k}", me); bpy.context.collection.objects.link(o)
        sm = o.modifiers.new("s", "SOLIDIFY"); sm.thickness = 0.12
        o.data.materials.append(tm)
        am = (a0 + a1) / 2
        # pivot at base, tilt outward
        bpy.context.view_layer.objects.active = o
        o.select_set(True)
        bpy.context.scene.cursor.location = (math.cos(am) * r, math.sin(am) * r, 0)
        bpy.ops.object.origin_set(type="ORIGIN_CURSOR"); o.select_set(False)
        tilt = R(25 + 55 * ((k * 3) % 4) / 3)
        o.rotation_mode = "ZXY"
        o.rotation_euler = (0, 0, 0)
        ax = (-math.sin(am), math.cos(am), 0)  # tangent
        import mathutils
        o.rotation_euler = mathutils.Matrix.Rotation(-tilt, 4, ax).to_euler("ZXY")
        o.location = (loc[0] + math.cos(am) * (r + 1.2 * k % 3), loc[1] + math.sin(am) * (r + 1.2 * k % 3), loc[2])
    # molasses dome bursting out + spreading sheet
    d = sphere("SEA_dome", (loc[0], loc[1], 1.0), r * 1.05, mol, scl=(1.15, 1.15, 0.62), seg=64)
    tx = bpy.data.textures.new("mt", "CLOUDS"); tx.noise_scale = 1.2
    dm = d.modifiers.new("d", "DISPLACE"); dm.texture = tx; dm.strength = 1.2
    sub = d.modifiers.new("ss", "SUBSURF"); sub.levels = 1
    molasses_sheet(loc, 30, 0.35)


def molasses_sheet(loc, size, z, strength=0.5, name="SEA_mol"):
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=160, y_subdivisions=160, size=size, location=(loc[0], loc[1], z))
    o = bpy.context.object; o.name = name
    tx = bpy.data.textures.new("ms" + name, "CLOUDS"); tx.noise_scale = 1.6
    dm = o.modifiers.new("d", "DISPLACE"); dm.texture = tx; dm.strength = strength
    o.data.materials.append(molasses_mat()); bpy.ops.object.shade_smooth()
    return o


def brick_block(name, x, y, w, d, floors=4, col=(0.5, 0.2, 0.13), rot=0):
    br = mat("brick" + str(col), col, 0.9); wn = mat("bwin", (0.1, 0.11, 0.13), 0.3); tr = mat("btrim", (0.75, 0.7, 0.6), 0.8)
    fh = 1.6; hgt = floors * fh + 0.4
    objs = [box(name + "b", (0, 0, hgt / 2), (w / 2, d / 2, hgt / 2), br, 0.03)]
    objs.append(box(name + "c", (0, 0, hgt + 0.12), (w / 2 + 0.12, d / 2 + 0.12, 0.12), tr, 0.02))
    n = max(2, int(w / 1.3))
    for f in range(floors):
        z = 0.9 + f * fh
        for i in range(n):
            xx = -w / 2 + (i + 0.5) * w / n
            objs.append(box(name + f"w{f}{i}", (xx, -d / 2 - 0.02, z + 0.2), (0.26, 0.03, 0.48), wn, 0))
            objs.append(box(name + f"s{f}{i}", (xx, -d / 2 - 0.05, z - 0.32), (0.32, 0.05, 0.04), tr, 0))
    root = parent_all(objs, name); root.location = (x, y, 0); root.rotation_euler = (0, 0, R(rot))
    return root


def elevated(y=0, x0=-40, x1=40, z=4.2, bent_at=None):
    """Boston Elevated (Atlantic Ave) — steel posts + box girders + rails, running along x."""
    st = mat("elsteel", (0.16, 0.18, 0.17), 0.55, 0.6)
    import mathutils
    xs = list(range(int(x0), int(x1) + 1, 5))
    for k, x in enumerate(xs):
        for sy in (-1, 1):
            p = box(f"post{k}{sy}", (x, y + sy * 1.6, z / 2), (0.16, 0.16, z / 2), st, 0.02)
            if bent_at is not None and abs(x - bent_at) < 3:
                p.rotation_euler = (R(sy * 14), R(-18), 0); p.location.z -= 0.4
        box(f"cap{k}", (x, y, z + 0.1), (0.2, 1.9, 0.18), st, 0.02)
    for sy in (-1, 1):
        if bent_at is None:
            box(f"gird{sy}", ((x0 + x1) / 2, y + sy * 1.1, z + 0.5), ((x1 - x0) / 2, 0.08, 0.35), st, 0)
            box(f"rail{sy}", ((x0 + x1) / 2, y + sy * 0.6, z + 0.95), ((x1 - x0) / 2, 0.04, 0.05), st, 0)
        else:  # sagging girder: split in segments with a dip
            nseg = 24
            for j in range(nseg):
                xa = x0 + (x1 - x0) * j / nseg; xb = x0 + (x1 - x0) * (j + 1) / nseg; xm = (xa + xb) / 2
                dip = -1.8 * math.exp(-((xm - bent_at) / 4.0) ** 2)
                dip2 = -1.8 * math.exp(-((xb - bent_at) / 4.0) ** 2) - (-1.8 * math.exp(-((xa - bent_at) / 4.0) ** 2))
                ang = math.atan2(dip2, xb - xa)
                box(f"gird{sy}{j}", (xm, y + sy * 1.1 + 0.4 * math.exp(-((xm - bent_at) / 4.0) ** 2) * sy, z + 0.5 + dip), ((xb - xa) / 2 + 0.05, 0.08, 0.35), st, 0, rot=(0, -ang, 0))
                box(f"rail{sy}{j}", (xm, y + sy * 0.6, z + 0.95 + dip), ((xb - xa) / 2 + 0.05, 0.04, 0.05), st, 0, rot=(0, -ang, 0))
    # cross ties
    for k in range(int((x1 - x0) / 1.0)):
        x = x0 + k * 1.0
        dip = 0 if bent_at is None else -1.8 * math.exp(-((x - bent_at) / 4.0) ** 2)
        box(f"tie{k}", (x, y, z + 0.88 + dip), (0.1, 1.0, 0.04), mat("tie", (0.25, 0.17, 0.1), 0.9), 0)


def barrel(name, loc, m=None, rot=(0, 0, 0)):
    wd = m or mat("barrel", (0.45, 0.28, 0.14), 0.8); hp = mat("hoop", (0.2, 0.2, 0.2), 0.5, 0.7)
    o = cyl(name, loc, 0.45, 1.1, wd, rot=rot, verts=24)
    o.scale = (1, 1, 1)
    return o


def cart(name, loc, rot=0, tilt=0):
    wd = mat("cartw", (0.42, 0.3, 0.18), 0.85); dk = mat("cartd", (0.15, 0.1, 0.06), 0.8)
    objs = [box(name + "bed", (0, 0, 1.0), (1.6, 0.8, 0.08), wd, 0.02)]
    for sx in (-1, 1):
        objs.append(box(name + f"sd{sx}", (0, sx * 0.78, 1.3), (1.6, 0.04, 0.3), wd, 0.01))
        objs.append(cyl(name + f"wh{sx}", (0.4, sx * 0.9, 0.6), 0.6, 0.1, dk, rot=(R(90), 0, 0), verts=20))
    objs.append(box(name + "sh", (2.6, 0, 0.9), (1.2, 0.04, 0.04), wd, 0))
    for k in range(3):
        objs.append(barrel(name + f"br{k}", (-0.9 + k * 0.85, 0, 1.6)))
    root = parent_all(objs, name); root.location = loc; root.rotation_euler = (R(tilt), 0, R(rot))
    return root


def waterfront(flood=False, bent=False, front=True, row=False):
    ground((0.42, 0.4, 0.38), size=260, strength=0.02, center=(0, 40), name="ground")
    # harbor water behind
    bpy.ops.mesh.primitive_plane_add(size=400, location=(0, 230, 0.05)); w = bpy.context.object; w.name = "SEA_harbor"
    w.data.materials.append(mat("harbor", (0.12, 0.2, 0.26), 0.25))
    box("road", (0, 2, 0.03), (60, 3.2, 0.03), mat("cobble", (0.33, 0.31, 0.3), 0.9), 0)
    elevated(y=2, x0=-45, x1=45, bent_at=(2.0 if bent else None))
    # wharf + warehouses near the tank
    box("wharf", (20, 26, 0.3), (14, 8, 0.3), mat("wharfw", (0.4, 0.3, 0.2), 0.9), 0.02)
    box("wh1", (24, 24, 2.2), (6, 3.5, 2.2), mat("whw", (0.55, 0.45, 0.32), 0.85), 0.04)
    cone("wh1r", (24, 24, 4.9), 6.4, 0.5, 1.0, mat("whr", (0.25, 0.25, 0.27), 0.7), verts=4, rot=(0, 0, R(45)), scl=(1, 0.58, 1))
    cols = [(0.5, 0.2, 0.13), (0.56, 0.26, 0.16), (0.45, 0.19, 0.14), (0.6, 0.42, 0.3)]
    for k, x in enumerate((-34, -25, -16)):
        brick_block(f"nb{k}", x, 12, 8, 7, 3 + k % 2, cols[k % 4])
    if front:
        for k, x in enumerate((-30, -20, -10, 12, 22, 32)):
            brick_block(f"fb{k}", x, -9, 9, 6, 3 + (k % 3), cols[(k + 1) % 4], rot=180)
    if row:
        for k, x in enumerate((-10, 0, 10, 20, 30)):
            brick_block(f"rb{k}", x, 10, 9, 5, 3 + (k % 2), cols[(k + 2) % 4])
    if flood:
        molasses_sheet((0, 5), 120, 0.55, 0.45)
        cart("cart1", (-6, 4, 0.35), rot=25, tilt=10)
        for k, (x, y) in enumerate(((3, -1), (-2, 6), (8, 3), (-12, 1))):
            barrel(f"fb{k}", (x, y, 0.75), rot=(R(90), 0, R(30 * k)))


def lab():
    ground((0.3, 0.28, 0.27), size=40, strength=0.0, center=(0, 0), name="floor")
    box("wall", (0, 4, 3), (8, 0.1, 3), mat("labwall", (0.7, 0.72, 0.68), 0.9), 0)
    box("table", (0, 0.5, 0.9), (2.6, 1.3, 0.05), mat("ltab", (0.25, 0.25, 0.27), 0.5), 0.02)
    for sx in (-1, 1):
        for sy in (-1, 1):
            box(f"tl{sx}{sy}", (sx * 2.4, 0.5 + sy * 1.1, 0.45), (0.05, 0.05, 0.45), mat("tleg", (0.6, 0.6, 0.62), 0.4, 0.8), 0)
    # scale model of the North End on a board (tilted ramp)
    brd = box("board", (-0.4, 0.5, 1.02), (1.5, 0.9, 0.04), mat("brd", (0.85, 0.82, 0.75), 0.8), 0.01)
    cols = [(0.6, 0.3, 0.2), (0.7, 0.6, 0.45), (0.55, 0.28, 0.2)]
    for i in range(10):
        x = -1.6 + (i % 5) * 0.45; y = -0.1 + (i // 5) * 1.0
        box(f"mb{i}", (x, y, 1.06 + 0.1 + 0.05 * (i % 3)), (0.16, 0.2, 0.1 + 0.05 * (i % 3)), mat(f"mbc{i%3}", cols[i % 3], 0.8), 0.005)
    cyl("mtank", (0.75, 0.9, 1.2), 0.22, 0.32, mat("tank", TANKC, 0.6, 0.35), verts=32)
    # syrup flowing over the model
    s = sphere("SEA_syrup", (0.3, 0.45, 1.06), 0.5, mat("syrup", (0.55, 0.3, 0.06), 0.08), scl=(1.6, 0.9, 0.08))
    # beakers + thermometer
    gl = mat("glass", (0.85, 0.9, 0.95), 0.05)
    for k, (x, hh) in enumerate(((1.6, 0.5), (2.05, 0.35))):
        cyl(f"bk{k}", (x, 0.6, 0.95 + hh / 2), 0.17, hh, gl, verts=32)
        cyl(f"bkm{k}", (x, 0.6, 0.95 + hh * 0.3), 0.16, hh * 0.55, mat("syrup", (0.55, 0.3, 0.06), 0.08), verts=32)
    box("board2", (1.2, 3.85, 2.6), (1.6, 0.03, 0.9), mat("chalk", (0.12, 0.2, 0.16), 0.9), 0.01)
    sphere("lamp", (-1.5, 1.2, 3.0), 0.18, mat("lampe", (1, 0.95, 0.8), emit=(1, 0.95, 0.85), estr=8))


def light(kind):
    if kind == "winter":
        set_world((0.62, 0.68, 0.76), 1.0); sun((58, 0, -35), 3.3, (1.0, 0.95, 0.88), 3)
    elif kind == "noon":
        set_world((0.6, 0.7, 0.85), 0.9); sun((40, 0, -30), 4.0, (1.0, 0.93, 0.82))
    elif kind == "dusk":
        set_world((0.3, 0.33, 0.45), 0.8); sun((78, 0, -60), 2.8, (0.9, 0.75, 0.65), 4)
    elif kind == "lab":
        set_world((0.2, 0.2, 0.22), 0.6)
        area((-2, -3, 4), (45, 0, -30), 400, (1.0, 0.95, 0.88), 3)
        area((3, -2, 3), (60, 0, 40), 120, (0.7, 0.8, 1.0), 2)


def P(name):
    if name == "harbor":
        light("winter"); waterfront(front=False); tank((4, 26, 0))
        camera((-3, -3, 7.5), (4, 26, 4.5), 30)
    elif name == "tank_low":
        light("noon"); waterfront(); tank((4, 26, 0))
        camera((-1.5, 14.5, 0.6), (4, 26, 6.2), 18)
    elif name == "burst":
        light("noon"); waterfront(front=False); tank_burst((4, 26, 0))
        camera((-3, -3, 7.5), (4, 26, 3.2), 30)
    elif name == "street":
        light("winter"); waterfront(row=True)
        tank((4, 46, 0))
        camera((-34, -3.2, 1.7), (10, 2.0, 4.0), 24)
    elif name == "flood":
        light("winter"); waterfront(flood=True, bent=True, row=True)
        camera((-34, -3.2, 2.0), (10, 2.0, 3.4), 24)
    elif name == "bent":
        light("winter"); waterfront(flood=True, bent=True, row=True)
        camera((-9, -4.0, 1.6), (2, 2, 4.0), 22)
    elif name == "lab":
        light("lab"); lab()
        camera((0.4, -3.4, 2.6), (0.0, 0.6, 1.1), 30)
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
