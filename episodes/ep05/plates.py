"""EP05 (epidemia de dança, Estrasburgo 1518) plates — self-contained, built on kit/bl_scenes.py style.
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


# ---------------- medieval assets ----------------
PLASTER = [(0.86, 0.8, 0.68), (0.82, 0.74, 0.6), (0.78, 0.72, 0.64), (0.72, 0.58, 0.44), (0.85, 0.82, 0.75)]
TIMBER = (0.2, 0.12, 0.08)
ROOF = [(0.46, 0.22, 0.15), (0.38, 0.2, 0.16), (0.32, 0.25, 0.22)]


def _beams(cx, cy, fy, w, h, z0, seed=0):
    tb = mat("timber", TIMBER, 0.8)
    t = 0.08
    for x in (-w, w):
        box(f"pst{cx:.1f}{cy:.1f}{x:.1f}{seed}", (cx + x, fy, z0 + h / 2), (t, 0.04, h / 2), tb, 0)
    for z in (z0 + 0.02, z0 + h):
        box(f"rail{cx:.1f}{cy:.1f}{z:.1f}{seed}", (cx, fy, z), (w, 0.04, t), tb, 0)
    zm = z0 + h * 0.52
    box(f"mrail{cx:.1f}{cy:.1f}{seed}", (cx, fy, zm), (w, 0.04, t), tb, 0)
    for sx in (-1, 1):
        box(f"diag{cx:.1f}{cy:.1f}{sx}{seed}", (cx + sx * w * 0.5, fy, z0 + h * 0.26), (t, 0.04, h * 0.3), tb, 0, rot=(R(sx * 32), 0, 0))
    for k in range(3):
        xx = -w * 0.6 + k * w * 0.6
        box(f"stud{cx:.1f}{cy:.1f}{k}{seed}", (cx + xx, fy, zm + h * 0.24), (t, 0.04, h * 0.24), tb, 0)


def house(cx, cy, w=1.6, d=1.6, h=3.2, seed=0, floors=2, face=-1):
    import random
    rs = random.Random(seed)
    pl = mat(f"pl{seed}", PLASTER[seed % len(PLASTER)], 0.85)
    gm = mat("glass_dark", (0.06, 0.07, 0.09), 0.3)
    gl = mat("glass_lit", (1.0, 0.75, 0.35), 0.3, emit=(1.0, 0.7, 0.3), estr=2.2)
    for f in range(floors):
        z0 = f * h
        jut = 0.12 * f
        box(f"wall{seed}{f}", (cx, cy, z0 + h / 2), (w + jut * 0.5, d + jut * 0.5, h / 2), pl, 0.04)
        _beams(cx, cy, cy + face * (d + jut * 0.5 + 0.03), w + jut * 0.5, h, z0, seed * 7 + f)
        for sx in (-1, 1):
            lit = rs.random() < 0.3
            box(f"win{seed}{f}{sx}", (cx + sx * w * 0.42, cy + face * (d + jut * 0.5 + 0.06), f * h + h * 0.55),
                (0.22, 0.04, 0.3), gl if lit else gm, 0.01)
    top = floors * h
    rf = mat(f"rf{seed}", ROOF[seed % len(ROOF)], 0.85)
    rh = w * 1.15
    for sd in (-1, 1):
        box(f"roof{seed}{sd}", (cx, cy + sd * d * 0.5, top + rh * 0.5),
            (w + 0.18, 0.06, rh * 0.62), rf, 0.02, rot=(R(sd * -38), 0, 0))
    for yy in (cy - d, cy + d):
        box(f"gab{seed}{yy:.1f}", (cx, yy, top + rh * 0.3), (w, 0.04, rh * 0.3), pl, 0.02)
    cone(f"chim{seed}", (cx + w * 0.5, cy, top + rh * 0.7), 0.12, 0.12, 0.5, mat("chim", (0.3, 0.16, 0.12), 0.9), verts=8)


def cobbles(size=90, center=(0, 12), z=0.0):
    o = ground((0.4, 0.37, 0.34), size=size, strength=0.05, z=z, name="cob", center=center)
    tx = bpy.data.textures.new("cobt", "VORONOI"); tx.noise_scale = 0.22
    dm = o.modifiers.new("cb", "DISPLACE"); dm.texture = tx; dm.strength = 0.07
    return o


def stage(loc=(0, 0, 0)):
    wood = mat("stgwood", (0.55, 0.38, 0.2), 0.8); dark = mat("stgdark", (0.3, 0.2, 0.11), 0.85)
    objs = []
    w, d, zt = 3.2, 2.4, 0.9
    objs.append(box("stgtop", (0, 0, zt), (w, d, 0.12), wood, 0.03))
    for i in range(9):
        objs.append(box(f"plank{i}", (-w + 0.02 + i * (2 * w / 9), 0, zt + 0.12), (0.03, d, 0.01), dark, 0))
    for sx in (-1, 1):
        for sy in (-1, 1):
            objs.append(cyl(f"leg{sx}{sy}", (sx * (w - 0.3), sy * (d - 0.3), zt / 2), 0.14, zt, dark, verts=8))
    for k in range(2):
        objs.append(box(f"sstep{k}", (0, -d - 0.25 - k * 0.3, zt - 0.3 - k * 0.3), (1.2, 0.25, 0.15), wood, 0.02))
    root = parent_all(objs, "stage"); root.location = loc
    return root


def chapel(loc=(0, 0, 0)):
    stone = mat("chstone", (0.74, 0.71, 0.64), 0.85); roofm = mat("chroof", (0.35, 0.24, 0.2), 0.85)
    objs = []
    objs.append(box("chbody", (0, 0, 1.4), (1.5, 2.2, 1.4), stone, 0.05))
    rh = 1.5
    for sd in (-1, 1):
        objs.append(box(f"chrf{sd}", (sd * 0.78, 0, 2.8 + rh * 0.4), (0.9, 2.3, 0.07), roofm, 0.02, rot=(0, R(sd * 40), 0)))
    for yy in (-2.2, 2.2):
        objs.append(box(f"chg{yy:.1f}", (0, yy, 3.0), (1.45, 0.05, 0.6), stone, 0.02))
    objs.append(box("tower", (0, 2.0, 3.6), (0.55, 0.55, 1.1), stone, 0.04))
    objs.append(cone("spire", (0, 2.0, 5.2), 0.5, 0.0, 1.1, roofm, verts=4, rot=(0, 0, R(45))))
    objs.append(box("chdoor", (0, -2.24, 0.9), (0.4, 0.05, 0.9), mat("chdoor", (0.12, 0.08, 0.05), 0.6), 0.02))
    objs.append(cyl("chdoorarch", (0, -2.24, 1.8), 0.4, 0.06, mat("chdoor2", (0.12, 0.08, 0.05), 0.6), rot=(R(90), 0, 0), verts=16, sc_=(1, 1, 0.5)))
    objs.append(box("chwin", (0, -2.24, 2.1), (0.22, 0.05, 0.5), mat("chwin", (1, 0.8, 0.4), emit=(1, 0.72, 0.3), estr=3.0), 0.01))
    objs.append(box("crx1", (0, -2.3, 3.5), (0.05, 0.03, 0.4), mat("crs", (0.2, 0.13, 0.08), 0.8), 0))
    objs.append(box("crx2", (0, -2.3, 3.55), (0.22, 0.03, 0.05), mat("crs", (0.2, 0.13, 0.08), 0.8), 0))
    root = parent_all(objs, "chapel"); root.location = loc
    return root


def pine(x, y, s=1.0, seed=0):
    cyl(f"ptr{x:.0f}{y:.0f}", (x, y, 0.6 * s), 0.12 * s, 1.2 * s, mat("pbark", (0.28, 0.18, 0.1), 0.9), verts=8)
    gm = mat("pleaf", (0.14, 0.3, 0.16), 0.85)
    for i, (dz, r) in enumerate(((1.3, 1.0), (2.0, 0.78), (2.6, 0.55))):
        cone(f"pl{x:.0f}{y:.0f}{i}", (x, y, dz * s), r * s, 0.0, 1.0 * s, gm, verts=10)


def mountains(center=(0, 40), z=-0.3):
    m = mat("mtn", (0.5, 0.52, 0.56), 0.95)
    for i, (x, y, h, r) in enumerate(((-24, 46, 14, 16), (10, 52, 20, 20), (30, 44, 12, 14), (-6, 58, 24, 22))):
        cone(f"mt{i}", (x, y, h / 2 + z), r, r * 0.15, h, m, verts=7)


def light_cross(kind):
    if kind == "day":
        set_world((0.52, 0.62, 0.78), 0.85); sun((52, 0, -46), 3.6, (1.0, 0.92, 0.78), 2.5)
        area((-10, -14, 12), (55, 0, 25), 300, (1.0, 0.85, 0.6), 8)
    elif kind == "dusk":
        set_world((0.5, 0.36, 0.34), 0.6); sun((80, 0, -24), 3.2, (1.0, 0.62, 0.38), 3)
        area((8, -10, 8), (60, 0, 20), 400, (1.0, 0.55, 0.3), 6)
    elif kind == "dawn":
        set_world((0.62, 0.6, 0.72), 0.85); sun((82, 0, 12), 3.2, (1.0, 0.78, 0.6), 3)


# ---------------- plates ----------------

def P(name):
    if name in ("street", "street_dusk"):
        light_cross("dusk" if name.endswith("dusk") else "day"); cobbles(center=(0, 20))
        for i, cy in enumerate((4, 9, 14, 20, 27)):
            house(-3.6 - i * 0.15, cy, w=1.5, d=1.5, h=3.0, seed=i * 2 + 1, floors=2, face=1)
            house(3.6 + i * 0.15, cy, w=1.5, d=1.5, h=3.0, seed=i * 2 + 2, floors=2, face=-1)
        camera((0.0, -9.5, 3.2), (0, 18, 3.4), 28, None)
    elif name == "square":
        light_cross("day"); cobbles(size=120, center=(0, 20))
        for i, cx in enumerate((-9, -5.5, -2, 2, 5.5, 9)):
            house(cx, 20, w=1.6, d=1.4, h=3.0 + (i % 2) * 0.5, seed=i + 3, floors=2 + (i % 2), face=-1)
        camera((0.0, -12, 3.6), (0, 14, 3.2), 32, None)
    elif name == "stage":
        light_cross("day"); cobbles(size=120, center=(0, 20))
        for i, cx in enumerate((-9, -5.5, -2, 2, 5.5, 9)):
            house(cx, 22, w=1.6, d=1.4, h=3.0 + (i % 2) * 0.5, seed=i + 3, floors=2 + (i % 2), face=-1)
        stage(loc=(0, 8, 0))
        camera((0.0, -10, 3.4), (0, 9, 2.4), 30, None)
    elif name == "shrine":
        light_cross("dawn"); ground((0.4, 0.42, 0.3), size=140, strength=1.6, z=-0.3, center=(0, 22), name="cobhill")
        mountains(center=(0, 55), z=-0.3)
        chapel(loc=(0, 10, 0))
        for x, y, s, sd in ((-6, 4, 1.3, 1), (6, 6, 1.5, 2), (-8, 14, 1.1, 3), (8, 16, 1.2, 4), (-4, 20, 1.0, 5)):
            pine(x, y, s, sd)
        camera((0.0, -7, 3.2), (0, 9, 2.6), 30, None)
    elif name == "shrine_glow":
        set_world((0.18, 0.16, 0.22), 0.5); sun((78, 0, 10), 1.2, (1.0, 0.75, 0.6), 3)
        area((0, -5, 3), (70, 0, 0), 250, (1.0, 0.7, 0.4), 4)
        chapel(loc=(0, 6, 0))
        for x, y, s, sd in ((-5, 2, 1.2, 1), (5, 4, 1.3, 2)):
            pine(x, y, s, sd)
        camera((0.0, -4.2, 2.4), (0, 4, 2.2), 34, None)
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
            m = flat if o.name.startswith(("cob", "ground", "gcob")) else ln
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
