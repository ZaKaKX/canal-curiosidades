"""Blender 3D plate builder for EP01. usage: python bl_scenes.py <plate> <outdir> [pct]
Renders <plate>.png (beauty, transparent sky), <plate>_nrm.png, <plate>_id.png (line passes)."""
import bpy, bmesh, math, sys, time
from mathutils import Vector

PLATE, OUTD = sys.argv[-2], sys.argv[-1]
import os
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


def win_mat(name, base, lit, scale=1.0, bw=0.6, rh=0.42, mortar=0.17, wcol=(1, 0.42, 0.1), dark=(0.08, 0.1, 0.13)):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; n = nt.nodes; l = nt.links
    b = n["Principled BSDF"]; b.inputs["Roughness"].default_value = 0.5
    tc = n.new("ShaderNodeTexCoord"); mp = n.new("ShaderNodeMapping"); mp.inputs["Rotation"].default_value = (R(90), 0, 0)
    br = n.new("ShaderNodeTexBrick"); br.offset = 0.0
    br.inputs["Scale"].default_value = scale; br.inputs["Brick Width"].default_value = bw
    br.inputs["Row Height"].default_value = rh; br.inputs["Mortar Size"].default_value = mortar
    br.inputs["Color1"].default_value = (*(wcol if lit else dark), 1); br.inputs["Color2"].default_value = (*(wcol if lit else dark), 1)
    br.inputs["Mortar"].default_value = (*base, 1)
    l.new(tc.outputs["Object"], mp.inputs["Vector"]); l.new(mp.outputs["Vector"], br.inputs["Vector"])
    l.new(br.outputs["Color"], b.inputs["Base Color"])
    if lit:
        mx = n.new("ShaderNodeMix"); mx.data_type = "RGBA"
        mx.inputs["A"].default_value = (0, 0, 0, 1); mx.inputs["B"].default_value = (*wcol, 1)
        inv = n.new("ShaderNodeMath"); inv.operation = "SUBTRACT"; inv.inputs[0].default_value = 1.0
        l.new(br.outputs["Fac"], inv.inputs[1]); l.new(inv.outputs[0], mx.inputs["Factor"])
        l.new(mx.outputs["Result"], b.inputs["Emission Color"]); b.inputs["Emission Strength"].default_value = 2.2
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


def parent_all(objs, name):
    bpy.ops.object.empty_add(location=(0, 0, 0)); root = bpy.context.object; root.name = name
    for o in objs:
        o.parent = root
    return root


def new_objs(fn, *a, **k):
    before = set(bpy.data.objects)
    fn(*a, **k)
    return [o for o in bpy.data.objects if o not in before]


# ---------------- assets ----------------

def _liner(kind="titanic", lit=False, damage=False):
    white = kind == "britannic"
    hull_base = (0.93, 0.93, 0.9) if white else (0.025, 0.025, 0.03)
    hull_m = win_mat(f"hull_{kind}_{lit}", hull_base, lit, scale=1.0, bw=0.55, rh=0.5, mortar=0.38,
                     wcol=(1, 0.5, 0.15) if lit else ((0.25, 0.3, 0.35) if white else (0.75, 0.72, 0.62)))
    sup_m = win_mat(f"sup_{kind}_{lit}", (0.92, 0.9, 0.85), lit, scale=1.0, bw=0.6, rh=0.42, mortar=0.17)
    buff = mat("buff", (0.85, 0.52, 0.15), 0.45); black = mat("blk", (0.015, 0.015, 0.015), 0.5)
    deck = mat("deck", (0.55, 0.4, 0.26), 0.7); lbm = mat("lbm", (0.96, 0.95, 0.92), 0.5)
    red = mat("redbot", (0.45, 0.06, 0.04), 0.6)
    h = box("hull", (0, 0, 0.6), (13, 1.5, 1.4), hull_m, 0)
    bpy.context.view_layer.objects.active = h; bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.subdivide(number_cuts=14); bpy.ops.object.mode_set(mode="OBJECT")
    for v in h.data.vertices:
        x = v.co.x
        if x > 7.5:
            k = (x - 7.5) / 5.5
            v.co.y *= max(0.04, 1 - k ** 1.7 * 0.96)
            if v.co.z > 0: v.co.z += k ** 2 * 0.45
            if v.co.z < 0: v.co.x -= k * 0.8
        if x < -10:
            k = (-10 - x) / 3
            v.co.y *= max(0.4, 1 - k ** 2 * 0.6)
            if v.co.z < 0: v.co.x += k * 1.2
    md = h.modifiers.new("b", "BEVEL"); md.width = 0.1; md.segments = 2
    box("redbot", (0, 0, -0.55), (12.4, 1.42, 0.3), red, 0.1)
    if white:
        box("green", (-0.3, 0, 0.75), (12.5, 1.53, 0.09), mat("green", (0.12, 0.45, 0.2), 0.5), 0)
        rc = mat("redx", (0.75, 0.05, 0.04), 0.5, emit=(0.75, 0.05, 0.04), estr=0.3)
        for x in (-6, 0, 6):
            for sd in (-1, 1):
                box(f"rx{x}{sd}", (x, sd * 1.53, 0.35), (0.16, 0.03, 0.85), rc, 0)
                box(f"ry{x}{sd}", (x, sd * 1.53, 0.35), (0.85, 0.03, 0.16), rc, 0)
    else:
        box("sheer", (-0.2, 0, 1.78), (12.3, 1.53, 0.05), mat("wl", (0.9, 0.86, 0.75), 0.4), 0)
    box("deck1", (-0.5, 0, 2.3), (10.5, 1.38, 0.42), sup_m, 0.05)
    box("deck2", (-0.6, 0, 3.0), (9.6, 1.22, 0.33), sup_m, 0.05)
    box("deck3", (-0.8, 0, 3.48), (7.6, 1.04, 0.16), deck, 0.03)
    box("bridge", (7.6, 0, 3.4), (0.9, 1.15, 0.35), sup_m, 0.04)
    for i, x in enumerate((-5.2, -2.0, 1.2, 4.4)):
        cyl(f"fun{i}", (x, 0, 5.4), 0.62, 3.8, buff, rot=(0, R(-8), 0), sc_=(1, 0.8, 1))
        cyl(f"top{i}", (x + 0.27, 0, 7.3), 0.645, 0.75, black, rot=(0, R(-8), 0), sc_=(1, 0.81, 1))
        box(f"fb{i}", (x - 0.1, 0, 3.6), (0.75, 0.6, 0.12), deck, 0.03)
    for x in (-11.5, 10.8):
        cyl(f"mast{x}", (x, 0, 6.2), 0.09, 10.5, black, verts=12)
    for side in (-1, 1):
        for i in range(8):
            box(f"lb{side}{i}", (-7.2 + i * 1.75, side * 1.0, 3.82), (0.6, 0.2, 0.17), lbm, 0.05)
    if damage:
        dm = mat("dmg", (0.0, 0.0, 0.0), 0.9)
        box("hole", (-9, -1.52, 0.9), (1.1, 0.06, 0.8), dm, 0.02, rot=(0, R(18), 0))
        for i in range(6):
            box(f"shard{i}", (-9.6 + i * 0.25, -1.62, 0.4 + (i % 3) * 0.35), (0.25, 0.04, 0.06), hull_m, 0, rot=(R(30 * i), R(15), R(40 - i * 12)))


def liner(kind="titanic", lit=False, damage=False, loc=(0, 0, 0), rot=(0, 0, 0), name=None):
    objs = new_objs(_liner, kind, lit, damage)
    root = parent_all(objs, name or kind)
    root.location = loc; root.rotation_euler = rot
    return root


def _warship():
    g = mat("grey", (0.32, 0.35, 0.38), 0.5); gd = mat("greyd", (0.2, 0.22, 0.24), 0.5); black = mat("blk", (0.015, 0.015, 0.015), 0.5)
    h = box("whull", (0, 0, 0.3), (9, 1.1, 0.95), g, 0)
    bpy.context.view_layer.objects.active = h; bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.subdivide(number_cuts=10); bpy.ops.object.mode_set(mode="OBJECT")
    for v in h.data.vertices:
        if v.co.x > 5:
            k = (v.co.x - 5) / 4
            v.co.y *= max(0.05, 1 - k ** 1.5 * 0.95)
            if v.co.z < 0: v.co.x += k * 1.4   # ram bow pushes forward below waterline
    box("wsup", (-0.5, 0, 1.5), (5, 0.8, 0.35), gd, 0.04)
    for x in (-2.2, 0.6):
        cyl(f"wf{x}", (x, 0, 2.8), 0.45, 2.4, gd, sc_=(1, 0.75, 1))
        cyl(f"wft{x}", (x, 0, 4.0), 0.47, 0.3, black, sc_=(1, 0.76, 1))
    for x in (-6, 4.5):
        cyl(f"tur{x}", (x, 0, 1.45), 0.6, 0.45, gd)
        cyl(f"gun{x}", (x + (1.0 if x > 0 else -1.0), 0, 1.5), 0.08, 2.0, black, rot=(0, R(90), 0), verts=12)
    for x in (-3.5, 2.5):
        cyl(f"wm{x}", (x, 0, 4.2), 0.07, 6, black, verts=10)


def warship(loc=(0, 0, 0), rot=(0, 0, 0)):
    root = parent_all(new_objs(_warship), "warship"); root.location = loc; root.rotation_euler = rot
    return root


def iceberg(loc, s=1.0):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=6 * s, location=loc)
    o = bpy.context.object; o.name = "iceberg"
    o.scale = (1.2, 0.9, 1.5)
    tx = bpy.data.textures.new("icet", "VORONOI"); tx.noise_scale = 1.4 * s
    dm = o.modifiers.new("d", "DISPLACE"); dm.texture = tx; dm.strength = 2.2 * s
    o.modifiers.new("dec", "DECIMATE").ratio = 0.35
    m = bpy.data.materials.new("ice"); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0.75, 0.88, 0.98, 1); b.inputs["Roughness"].default_value = 0.35
    b.inputs["Subsurface Weight"].default_value = 0.4; b.inputs["Subsurface Radius"].default_value = (0.3, 0.6, 1.0)
    o.data.materials.append(m)
    return o


def lifeboat(loc=(0, 0, 0), rot=(0, 0, 0), lantern=False):
    wood = mat("lbwood", (0.95, 0.94, 0.9), 0.5); trim = mat("lbtrim", (0.45, 0.28, 0.14), 0.6)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=1, location=(0, 0, 0))
    o = bpy.context.object; o.scale = (3.2, 1.0, 0.75)
    bpy.ops.object.transform_apply(scale=True)
    bm = bmesh.new(); bm.from_mesh(o.data)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z > 0.05], context="VERTS")
    bm.to_mesh(o.data); bm.free()
    so = o.modifiers.new("s", "SOLIDIFY"); so.thickness = 0.08
    o.data.materials.append(wood); bpy.ops.object.shade_smooth()
    objs = [o]
    for x in (-1.6, 0, 1.6):
        objs.append(box(f"seat{x}", (x, 0, -0.05), (0.18, 0.9, 0.04), trim, 0.02))
    objs.append(box("rim", (0, 0, 0.02), (3.15, 0.04, 0.05), trim, 0.02))
    if lantern:
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.18, location=(2.4, 0, 0.6))
        l = bpy.context.object; l.data.materials.append(mat("lant", (1, 0.7, 0.3), emit=(1, 0.6, 0.2), estr=40)); objs.append(l)
        bpy.ops.object.light_add(type="POINT", location=(2.4, 0, 0.7)); pl = bpy.context.object
        pl.data.energy = 60; pl.data.color = (1, 0.65, 0.3); objs.append(pl)
    root = parent_all(objs, "lifeboat"); root.location = loc; root.rotation_euler = rot
    return root


def sea(z=0.35, kind="day", rough=0.06, chop=0.55, size=260, center=(0, 60)):
    cols = {"day": (0.02, 0.12, 0.2), "night": (0.003, 0.01, 0.025), "sunset": (0.02, 0.07, 0.11),
            "storm": (0.03, 0.05, 0.06), "dawn": (0.04, 0.06, 0.1)}
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=500, y_subdivisions=500, size=size, location=(center[0], center[1], z))
    oc = bpy.context.object; oc.name = "SEA"
    tx = bpy.data.textures.new("wv", "CLOUDS"); tx.noise_scale = 1.6; tx.noise_depth = 3
    dm = oc.modifiers.new("d", "DISPLACE"); dm.texture = tx; dm.strength = chop; dm.texture_coords = "GLOBAL"
    bpy.ops.object.shade_smooth()
    m = bpy.data.materials.new("sea"); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*cols[kind], 1); b.inputs["Roughness"].default_value = rough
    oc.data.materials.append(m)
    return oc


def set_world(col, strength):
    w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True
    bg = w.node_tree.nodes["Background"]; bg.inputs["Color"].default_value = (*col, 1); bg.inputs["Strength"].default_value = strength


def sun(rot, energy, col, angle=2):
    bpy.ops.object.light_add(type="SUN", rotation=tuple(R(a) for a in rot))
    l = bpy.context.object.data; l.energy = energy; l.color = col; l.angle = R(angle)


def area(loc, rot, energy, col, size=5):
    bpy.ops.object.light_add(type="AREA", location=loc, rotation=tuple(R(a) for a in rot))
    a = bpy.context.object.data; a.energy = energy; a.color = col; a.size = size


def mood(kind):
    if kind == "day":
        set_world((0.55, 0.7, 0.9), 0.9); sun((50, 0, -40), 4.0, (1.0, 0.93, 0.82))
    elif kind == "night":
        set_world((0.03, 0.05, 0.12), 1.2); sun((70, 0, -140), 1.3, (0.6, 0.72, 1.0), 1)
        area((6, -12, 7), (65, 0, 30), 700, (1, 0.65, 0.35), 6)
    elif kind == "sunset":
        set_world((0.9, 0.5, 0.3), 0.6); sun((80, 0, -30), 4.5, (1.0, 0.68, 0.42), 3)
    elif kind == "dawn":
        set_world((0.6, 0.55, 0.75), 0.7); sun((84, 0, 10), 3.5, (1.0, 0.72, 0.55), 3)
    elif kind == "storm":
        set_world((0.25, 0.28, 0.32), 0.9); sun((55, 0, -60), 1.2, (0.75, 0.8, 0.9), 6)
    elif kind == "under":
        set_world((0.05, 0.3, 0.42), 1.4); sun((10, 0, 0), 3.0, (0.6, 0.9, 1.0), 8)
    elif kind == "interior":
        set_world((0.1, 0.07, 0.05), 0.4)


def camera(loc, target, lens=35, fstop=None, shift_y=0.0):
    bpy.ops.object.empty_add(location=target); tgt = bpy.context.object; tgt.name = "TGT"
    bpy.ops.object.camera_add(location=loc); cam = bpy.context.object; sc.camera = cam
    c = cam.constraints.new("TRACK_TO"); c.target = tgt; c.track_axis = "TRACK_NEGATIVE_Z"; c.up_axis = "UP_Y"
    cam.data.lens = lens; cam.data.shift_y = shift_y; cam.data.clip_end = 2000
    if fstop:
        cam.data.dof.use_dof = True; cam.data.dof.focus_object = tgt; cam.data.dof.aperture_fstop = fstop
    return cam


def holdout(o):
    o.is_holdout = True


# ---------------- interiors / props ----------------

def cabin():
    wood = mat("wood", (0.33, 0.18, 0.09), 0.45); wood2 = mat("wood2", (0.22, 0.12, 0.06), 0.5)
    brass = mat("brass", (0.8, 0.55, 0.2), 0.25, 1.0)
    box("floor", (0, 0, -0.05), (6, 6, 0.05), mat("carpet", (0.35, 0.06, 0.06), 0.9), 0)
    box("back", (0, 3, 2.5), (6, 0.1, 2.6), wood, 0)
    box("left", (-4, 0, 2.5), (0.1, 6, 2.6), wood, 0)
    for x in (-3, -1, 1, 3):
        box(f"pan{x}", (x, 2.88, 2.2), (0.8, 0.05, 1.5), wood2, 0.04)
    box("rail", (0, 2.85, 1.0), (6, 0.08, 0.06), wood2, 0.02)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.7, minor_radius=0.12, location=(1.8, 2.86, 3.0), rotation=(R(90), 0, 0))
    bpy.context.object.data.materials.append(brass); bpy.ops.object.shade_smooth()
    cyl("glass", (1.8, 2.9, 3.0), 0.66, 0.02, mat("glass", (0.4, 0.7, 0.9), emit=(0.35, 0.65, 0.95), estr=3.0), rot=(R(90), 0, 0))
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.28, location=(-2.2, 2.6, 3.4))
    bpy.context.object.data.materials.append(mat("lamp", (1, 0.8, 0.5), emit=(1, 0.7, 0.35), estr=25))
    bpy.ops.object.light_add(type="POINT", location=(-2.2, 2.3, 3.4)); bpy.context.object.data.energy = 350; bpy.context.object.data.color = (1, 0.7, 0.4)
    box("bed", (-2.5, 1.2, 0.45), (1.4, 1.8, 0.45), mat("sheet", (0.92, 0.9, 0.84), 0.8), 0.15)
    box("bedframe", (-2.5, 1.2, 0.2), (1.5, 1.9, 0.22), wood2, 0.05)
    area((1.8, 1.5, 3), (90, 0, 180), 120, (0.6, 0.8, 1.0), 1.5)


def hull_wall(lit=False, hole=False):
    hm = mat("hwall", (0.03, 0.03, 0.035), 0.4)
    box("wall", (0, 0, 3), (12, 0.2, 6), hm, 0)
    riv = mat("rivet", (0.08, 0.08, 0.09), 0.3, 0.6)
    for z in range(0, 12):
        for x in range(-22, 23, 2):
            bpy.ops.mesh.primitive_uv_sphere_add(segments=8, ring_count=4, radius=0.05, location=(x * 0.5, -0.2, z * 0.6))
            bpy.context.object.data.materials.append(riv)
    for z in range(1, 12, 3):
        box(f"seam{z}", (0, -0.21, z * 0.6 - 0.3), (12, 0.01, 0.015), riv, 0)
    if lit:
        for x in range(-5, 6, 2):
            for zz in (2.0, 3.6):
                cyl(f"pt{x}{zz}", (x, -0.22, zz), 0.28, 0.06, mat("porthole", (1, 0.6, 0.25), emit=(1, 0.55, 0.2), estr=6), rot=(R(90), 0, 0))
                bpy.ops.mesh.primitive_torus_add(major_radius=0.32, minor_radius=0.05, location=(x, -0.24, zz), rotation=(R(90), 0, 0))
                bpy.context.object.data.materials.append(mat("brass", (0.8, 0.55, 0.2), 0.25, 1.0))
    if hole:
        bpy.ops.mesh.primitive_circle_add(vertices=18, radius=2.2, fill_type="NGON", location=(0.3, -0.25, 3.2), rotation=(R(90), 0, 0))
        o = bpy.context.object
        for i, v in enumerate(o.data.vertices):
            f = 0.55 + 0.45 * ((i * 7) % 5) / 4
            v.co.x *= f; v.co.y *= f * 1.2
        o.data.materials.append(mat("void", (0, 0, 0), 1.0))
        for i in range(10):
            a = i / 10 * 6.28
            box(f"pl{i}", (0.3 + math.cos(a) * 2.1, -0.5, 3.2 + math.sin(a) * 2.4), (0.6, 0.04, 0.25), hm, 0.02,
                rot=(R(60 + i * 13), R(i * 29), a))


def dock():
    pl = mat("plank", (0.45, 0.3, 0.17), 0.8); pl2 = mat("plank2", (0.36, 0.23, 0.13), 0.8)
    for i in range(14):
        box(f"pk{i}", (0, -14 + i * 0.62, 0.9), (14, 0.28, 0.08), pl if i % 2 else pl2, 0.02)
    for x in (-5, 0, 5):
        cyl(f"bol{x}", (x, -6.2, 1.25), 0.25, 0.6, mat("iron", (0.05, 0.05, 0.05), 0.4, 0.5))
    for x in range(-12, 13, 4):
        cyl(f"pile{x}", (x, -5.7, 0.3), 0.22, 2.2, pl2)


def mine_obj(loc=(0, 0, 0)):
    im = mat("mine", (0.08, 0.09, 0.1), 0.35, 0.7)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, location=loc); bpy.context.object.data.materials.append(im); bpy.ops.object.shade_smooth()
    for i in range(10):
        th = i * 2.399; z = 1 - 2 * (i + 0.5) / 10; r = math.sqrt(1 - z * z)
        d = Vector((math.cos(th) * r, math.sin(th) * r, z))
        p = Vector(loc) + d * 1.05
        bpy.ops.mesh.primitive_cone_add(radius1=0.14, radius2=0.06, depth=0.45, location=p)
        o = bpy.context.object; o.rotation_mode = "QUATERNION"; o.rotation_quaternion = d.to_track_quat("Z", "Y")
        o.data.materials.append(im)
    cyl("chain", (loc[0], loc[1], loc[2] - 6), 0.05, 10, im, verts=8)


def propeller(loc=(0, 0, 0), rot=(0, 0, 0)):
    br = mat("bronze", (0.75, 0.5, 0.2), 0.3, 1.0)
    objs = [cyl("hub", (0, 0, 0), 0.4, 0.8, br, rot=(0, R(90), 0))]
    for i in range(3):
        a = i * 120
        bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(0, 0, 0)); o = bpy.context.object
        o.scale = (0.1, 0.55, 1.4); bpy.ops.object.transform_apply(scale=True)
        o.location = (0, math.sin(R(a)) * 1.4, math.cos(R(a)) * 1.4)
        o.rotation_euler = (R(-a), R(25), 0); o.data.materials.append(br); bpy.ops.object.shade_smooth()
        objs.append(o)
    root = parent_all(objs, "prop"); root.location = loc; root.rotation_euler = rot
    return root


# ---------------- plates ----------------

def P(name):
    S = None
    if name == "night_titanic":
        mood("night"); S = sea(kind="night")
        liner("titanic", lit=True, rot=(0, 0, R(-20)))
        camera((16, -40, 5.5), (0, 0, 4), 40, 6, 0.08)
    elif name == "storm":
        mood("storm"); S = sea(kind="storm", chop=1.4, rough=0.15)
        liner("olympic", loc=(-12, 34, 0), rot=(R(3), 0, R(-10)))
        liner("britannic", loc=(16, 52, 0), rot=(R(-3), 0, R(-200)))
        camera((0, -22, 5), (0, 40, 3), 38, None, 0.05)
    elif name == "cabin":
        mood("interior"); cabin()
        camera((2.5, -5.5, 2.3), (-0.5, 2.8, 2.6), 26, 3)
    elif name == "liner_day":
        mood("day"); S = sea(kind="day")
        liner("olympic", rot=(0, 0, R(-25)))
        camera((22, -46, 6), (0, 0, 4), 36, 8, 0.05)
    elif name == "olympic_hero":
        mood("day"); S = sea(kind="day")
        liner("olympic", rot=(0, 0, R(-35)))
        camera((10, -27, 2.2), (1, 0, 5.5), 28, 5)
    elif name in ("crash_sea", "crash_olympic", "crash_warship"):
        mood("day"); S = sea(kind="day")
        if name != "crash_warship": liner("olympic", loc=(-2, 0, 0), damage=False)
        if name == "crash_warship": warship(loc=(-7, -9.5, 0), rot=(0, 0, R(75)))
        if name == "crash_olympic": pass
        camera((0, -44, 6), (-5, -3, 2.5), 42, None, 0.04)
        if name != "crash_sea": holdout(S)
        if name == "crash_sea":
            for o in [o for o in bpy.data.objects if o.parent and o.parent.name == "olympic"] + [bpy.data.objects["olympic"]]:
                o.hide_render = True
    elif name == "hull_hole":
        mood("day"); hull_wall(hole=True); S = sea(kind="day", z=0.6, size=60, center=(0, -10))
        camera((0.3, -9, 3.0), (0.3, 0, 3.3), 30, None)
    elif name == "dock":
        mood("day"); S = sea(kind="day", z=0.0)
        dock(); liner("olympic", loc=(0, 20, 0), rot=(0, 0, R(180)), damage=True)
        camera((2, -16, 2.0), (0, 10, 3.5), 30, 6)
    elif name == "sisters":
        mood("day"); S = sea(kind="day")
        liner("olympic", loc=(-16, 34, 0), rot=(0, 0, R(-15)))
        liner("titanic", loc=(10, 6, 0), rot=(0, 0, R(-22)))
        camera((4, -40, 5), (0, 15, 4), 34, 10, 0.06)
    elif name == "unsinkable":
        mood("sunset"); S = sea(kind="sunset")
        liner("titanic", rot=(0, 0, R(-28)))
        camera((7, -25, 1.4), (0, 0, 6.0), 26, 6)
    elif name == "bow":
        mood("sunset"); S = sea(kind="sunset")
        liner("titanic", rot=(0, 0, R(-15)))
        camera((21, -20, 1.6), (8, 0, 4.2), 28, 8)
    elif name in ("ice_sea", "ice_ship"):
        mood("night"); S = sea(kind="night")
        iceberg((22, 12, 1), 1.0)
        if name == "ice_ship":
            liner("titanic", lit=True, loc=(2, 10, 0), rot=(0, 0, R(5))); holdout(S)
            bpy.data.objects["iceberg"].is_holdout = True
        camera((4, -42, 5), (12, 10, 5), 38, None, 0.06)
    elif name == "lifeboat_hull":
        mood("night"); hull_wall(lit=True); S = sea(kind="night", z=-0.2, size=80, center=(0, -20))
        camera((0, -12, 3.2), (0, 0, 3.6), 28, None)
    elif name == "lifeboat_layer":
        mood("night"); lifeboat(rot=(0, 0, 0))
        camera((0, -8, 3.8), (0, 0, 0), 32, None)
    elif name == "deck_night":
        mood("night")
        liner("titanic", lit=True, loc=(0, 3.5, -2.5), rot=(0, 0, 0))
        camera((3, -2.0, 1.7), (-6, 3.0, 2.2), 24, 3)
    elif name == "dark_sea":
        mood("night"); S = sea(kind="night", chop=0.25, rough=0.04)
        for i, (x, y) in enumerate(((-14, 40), (-4, 55), (9, 35), (18, 62))):
            lifeboat(loc=(x, y, 0.5), rot=(0, 0, R(30 * i)), lantern=True)
        camera((0, -20, 3), (0, 40, 1), 40, None, 0.12)
    elif name == "dawn":
        mood("dawn"); S = sea(kind="dawn", chop=0.3)
        lifeboat(loc=(0, 0, 0.55), rot=(0, 0, R(10)))
        camera((0.5, -7.5, 3.4), (0, 0, 0.3), 30, 6, 0.0)
    elif name == "rescue":
        mood("day"); S = sea(kind="day", chop=0.4)
        lifeboat(loc=(0, 0, 0.55), rot=(0, 0, R(-5)))
        camera((0.5, -7.5, 3.4), (0, 0, 0.3), 30, 6, 0.0)
    elif name == "nurse_bg":
        mood("day"); S = sea(kind="day")
        liner("britannic", rot=(0, 0, R(-22)))
        camera((14, -36, 3), (0, 0, 4), 32, 3)
    elif name == "britannic":
        mood("day"); S = sea(kind="day")
        liner("britannic", rot=(0, 0, R(-30)))
        camera((12, -30, 2.4), (0, 0, 4.8), 30, 6)
    elif name == "mine":
        mood("under"); mine_obj((0, 0, 0))
        camera((0, -9, -0.5), (0, 0, 0.8), 30, None)
    elif name == "hull_below":
        mood("under"); liner("britannic", rot=(0, 0, 0))
        camera((0, -14, -5), (0, 0, 0.5), 24, None)
    elif name in ("sink_sea", "sink_ship"):
        mood("day"); S = sea(kind="day")
        liner("britannic", loc=(0, 0, -1.5), rot=(0, R(10), R(-20)))
        camera((14, -40, 5), (0, 0, 2), 36, None, 0.06)
        if name == "sink_ship": holdout(S)
        else:
            for o in bpy.data.objects:
                if o.name == "britannic" or (o.parent and o.parent.name == "britannic"): o.hide_render = True
    elif name == "stern":
        mood("day"); S = sea(kind="day", chop=0.8)
        liner("britannic", loc=(0, 0, -2), rot=(0, R(-14), R(180)))
        camera((-14, -16, 2.5), (-11, 0, 3.5), 26, None)
    elif name == "prop_layer":
        mood("day"); propeller(rot=(0, 0, 0))
        camera((8, 0, 0), (0, 0, 0), 50, None)
    elif name in ("tri_olympic", "tri_titanic", "tri_britannic"):
        mood("sunset"); liner(name[4:], rot=(0, 0, 0))
        camera((0, -80, 3.5), (0, 0, 3.2), 50, None)
    else:
        raise SystemExit("unknown plate " + name)
    return S


def render(name):
    S = P(name)
    t0 = time.time()
    sc.render.filepath = f"{OUTD}/{name}.png"; bpy.ops.render.render(write_still=True)
    # line passes: swap materials
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
            m = flat if o.name in ("SEA", "glass") else ln
            if not o.data.materials: o.data.materials.append(m)
            for i in range(len(o.data.materials)): o.data.materials[i] = m
        if o.type == "LIGHT": o.hide_render = True
    sc.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0
    sc.cycles.samples = 12; sc.cycles.use_denoising = False; sc.cycles.filter_width = 0.8
    sc.render.dither_intensity = 0
    sc.view_settings.view_transform = "Standard"; sc.view_settings.look = "None"
    sc.camera.data.dof.use_dof = False
    sc.render.filepath = f"{OUTD}/{name}_nrm.png"; bpy.ops.render.render(write_still=True)
    nt.links.new(oi.outputs["Random"], em.inputs["Color"])
    sc.render.filepath = f"{OUTD}/{name}_id.png"; bpy.ops.render.render(write_still=True)
    print("PLATE", name, round(time.time() - t0, 1), "s")


render(PLATE)
