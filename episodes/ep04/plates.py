"""EP04 (estátuas gregas coloridas) plates — built from kit/bl_scenes.py. usage: python plates.py <plate> <outdir>
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



# ---------------- EP04 assets ----------------
MARBLE = (0.86, 0.84, 0.79)


def marble(name="marble"):
    if name in MATS: return MATS[name]
    m = mat(name, MARBLE, 0.4)
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Subsurface Weight"].default_value = 0.15; b.inputs["Subsurface Radius"].default_value = (0.3, 0.25, 0.2)
    return m


def pat_mat(name, c1, c2, kind="checker", scale=8.0, emit=False, estr=3.0, base=None, rot=(0, 0, 0)):
    """two-colour pattern (painted ornament). emit=True -> pattern glows (UV-light look) over marble base."""
    if name in MATS: return MATS[name]
    m = bpy.data.materials.new(name); m.use_nodes = True
    n = m.node_tree.nodes; l = m.node_tree.links
    b = n["Principled BSDF"]; b.inputs["Roughness"].default_value = 0.6
    tc = n.new("ShaderNodeTexCoord"); mp = n.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (scale, scale, scale); mp.inputs["Rotation"].default_value = tuple(R(a) for a in rot)
    l.new(tc.outputs["Object"], mp.inputs["Vector"])
    if kind == "checker":
        tx = n.new("ShaderNodeTexChecker"); tx.inputs["Scale"].default_value = 1.0
    elif kind == "wave":
        tx = n.new("ShaderNodeTexWave"); tx.inputs["Scale"].default_value = 1.0; tx.inputs["Distortion"].default_value = 0.0
    else:
        tx = n.new("ShaderNodeTexBrick"); tx.inputs["Scale"].default_value = 1.0
        tx.inputs["Mortar Size"].default_value = 0.08
    l.new(mp.outputs["Vector"], tx.inputs["Vector"])
    fac = tx.outputs["Fac"]
    if kind == "wave":
        ramp = n.new("ShaderNodeMath"); ramp.operation = "GREATER_THAN"; ramp.inputs[1].default_value = 0.55
        l.new(fac, ramp.inputs[0]); fac = ramp.outputs[0]
    mx = n.new("ShaderNodeMix"); mx.data_type = "RGBA"
    mx.inputs["A"].default_value = (*c1, 1); mx.inputs["B"].default_value = (*c2, 1)
    l.new(fac, mx.inputs["Factor"])
    if emit:
        b.inputs["Base Color"].default_value = (*(base or MARBLE), 1)
        l.new(mx.outputs["Result"], b.inputs["Emission Color"]); b.inputs["Emission Strength"].default_value = estr
    else:
        l.new(mx.outputs["Result"], b.inputs["Base Color"])
    MATS[name] = m
    return m


def sphere(name, loc, r, m, scl=(1, 1, 1), seg=32):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=seg // 2, radius=r, location=loc)
    o = bpy.context.object; o.name = name; o.scale = scl; o.data.materials.append(m); bpy.ops.object.shade_smooth()
    return o


def cone(name, loc, r1, r2, d, m, scl=(1, 1, 1), rot=(0, 0, 0), verts=40):
    bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=r1, radius2=r2, depth=d, location=loc, rotation=rot)
    o = bpy.context.object; o.name = name; o.scale = scl; o.data.materials.append(m); bpy.ops.object.shade_smooth()
    return o


def statue_mats(style):
    mb = marble()
    if style == "white":
        return dict(skin=mb, hair=mb, skirt=mb, torso=mb, band=mb, mantle=mb, eye=mb, lip=mb, gold=mb, plinth=mb)
    if style == "paint":
        return dict(skin=mat("skin", (0.86, 0.6, 0.42), 0.5), hair=mat("hair", (0.42, 0.14, 0.05), 0.6),
                    skirt=pat_mat("skirt_p", (0.08, 0.42, 0.33), (0.75, 0.62, 0.12), "wave", 2.2, rot=(0, 90, 0)),
                    torso=pat_mat("torso_p", (0.7, 0.09, 0.05), (0.9, 0.72, 0.2), "checker", 6.0),
                    band=pat_mat("band_p", (0.06, 0.18, 0.7), (0.92, 0.75, 0.2), "checker", 10.0),
                    mantle=mat("mantle", (0.07, 0.2, 0.68), 0.55), eye=mat("eye", (0.03, 0.02, 0.02), 0.3),
                    lip=mat("lip", (0.7, 0.08, 0.06), 0.4), gold=mat("gold", (0.95, 0.65, 0.18), 0.3, 0.8), plinth=mb)
    if style == "uv":
        g1, g2 = (0.0, 0.0, 0.0), (0.45, 0.25, 1.0)
        return dict(skin=mb, hair=pat_mat("hair_u", g1, (0.3, 0.2, 0.9), "checker", 1.0, True, 1.2),
                    skirt=pat_mat("skirt_u", g1, g2, "wave", 2.2, True, 3.0, rot=(0, 90, 0)),
                    torso=pat_mat("torso_u", g1, (0.6, 0.3, 1.0), "checker", 6.0, True, 3.0),
                    band=pat_mat("band_u", g1, (0.2, 0.8, 1.0), "checker", 10.0, True, 4.0),
                    mantle=pat_mat("mantle_u", g1, (0.25, 0.35, 1.0), "brick", 9.0, True, 2.0),
                    eye=mat("eye_u", (0.1, 0.05, 0.2), 0.3, emit=(0.5, 0.3, 1.0), estr=3.0), lip=mb, gold=mb, plinth=mb)


def _statue(style="white", plinth=True):
    M = statue_mats(style)
    if plinth: box("plinth", (0, 0, 0.5), (0.62, 0.62, 0.5), M["plinth"], 0.03)
    cone("skirt", (0, 0, 1.5), 0.44, 0.3, 1.0, M["skirt"], scl=(1, 0.78, 1))
    cyl("band", (0, 0, 1.07), 0.445, 0.14, M["band"], sc_=(1, 0.79, 1))
    box("stripe", (0, -0.29, 1.55), (0.07, 0.02, 0.42), M["band"], 0.01, rot=(R(-7), 0, 0))
    cone("torso", (0, 0, 2.3), 0.3, 0.36, 0.6, M["torso"], scl=(1, 0.7, 1))
    sphere("mantle", (0, 0, 2.6), 0.4, M["mantle"], scl=(1, 0.66, 0.3))
    cyl("neck", (0, 0, 2.72), 0.09, 0.2, M["skin"])
    sphere("head", (0, 0, 2.95), 0.23, M["skin"], scl=(0.9, 1, 1.12))
    sphere("hair", (0, 0.06, 3.0), 0.24, M["hair"], scl=(0.95, 1, 1.12))
    cyl("diadem", (0, 0.0, 3.14), 0.215, 0.06, M["gold"], sc_=(0.95, 1.0, 1))
    for sx in (-1, 1):
        for k in range(3):
            cyl(f"braid{sx}{k}", (sx * (0.12 + k * 0.035), -0.1, 2.62), 0.028, 0.42, M["hair"], verts=10)
        sphere(f"eye{sx}", (sx * 0.075, -0.2, 2.98), 0.03, M["eye"], seg=12)
    sphere("lip", (0, -0.21, 2.83), 0.03, M["lip"], scl=(1.4, 0.6, 0.6), seg=12)
    sphere("nose", (0, -0.225, 2.92), 0.03, M["skin"], scl=(0.7, 0.8, 1.2), seg=12)
    cyl("armL", (-0.38, 0, 2.2), 0.07, 0.75, M["skin"], rot=(0, R(-5), 0), verts=16)
    sphere("handL", (-0.4, 0, 1.8), 0.075, M["skin"], seg=16)
    cyl("armR", (0.38, 0, 2.42), 0.07, 0.36, M["skin"], verts=16)
    cyl("foreR", (0.38, -0.2, 2.27), 0.065, 0.44, M["skin"], rot=(R(80), 0, 0), verts=16)
    sphere("handR", (0.38, -0.44, 2.3), 0.075, M["skin"], seg=16)
    sphere("apple", (0.38, -0.5, 2.37), 0.07, M["gold"] if style != "white" else M["skin"], seg=16)
    for sx in (-1, 1):
        sphere(f"foot{sx}", (sx * 0.12, -0.3, 1.04), 0.08, M["skin"], scl=(0.8, 1.4, 0.5), seg=12)


def statue(style="white", loc=(0, 0, 0), rot=(0, 0, 0), s=1.0, name="statue", plinth=True):
    root = parent_all(new_objs(_statue, style, plinth), name); root.location = loc; root.rotation_euler = rot; root.scale = (s, s, s)
    return root


def ground(col=(0.55, 0.42, 0.28), size=160, strength=0.8, z=0.0, name="ground", center=(0, 30)):
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=160, y_subdivisions=160, size=size, location=(center[0], center[1], z))
    o = bpy.context.object; o.name = name
    tx = bpy.data.textures.new("gt" + name, "CLOUDS"); tx.noise_scale = 3
    dm = o.modifiers.new("d", "DISPLACE"); dm.texture = tx; dm.strength = strength
    o.data.materials.append(mat("g" + name, col, 0.95)); bpy.ops.object.shade_smooth()
    return o


def olive(x, y, s=1.0):
    cyl(f"trunk{x}{y}", (x, y, 1.0 * s), 0.18 * s, 2.0 * s, mat("bark", (0.3, 0.2, 0.12), 0.9), verts=8)
    for i, (dx, dz, r) in enumerate(((0, 2.4, 1.3), (-0.8, 2.1, 0.9), (0.8, 2.2, 1.0))):
        sphere(f"leaf{x}{y}{i}", (x + dx * s, y, dz * s), r * s, mat("leaf", (0.22, 0.35, 0.14), 0.8), seg=12)


def _temple(painted=False):
    mb = marble("tmarble")
    steps = mat("steps", (0.8, 0.77, 0.7), 0.6)
    for k in range(3):
        box(f"step{k}", (0, 0, 0.25 + k * 0.5), (14 - k * 0.6, 7 - k * 0.6, 0.25), steps, 0.03)
    xs = [-12 + i * (24 / 7) for i in range(8)]
    cols = [(x, -5.6) for x in xs] + [(x, 5.6) for x in xs] + [(-12, y) for y in (-1.9, 1.9)] + [(12, y) for y in (-1.9, 1.9)]
    for i, (x, y) in enumerate(cols):
        cone(f"col{i}", (x, y, 1.5 + 3.6), 0.62, 0.5, 7.2, mb, verts=20)
        box(f"cap{i}", (x, y, 8.85), (0.75, 0.75, 0.15), mb, 0.04)
    arch = mat("arch_p", (0.9, 0.85, 0.72), 0.6) if painted else mb
    box("architrave", (0, 0, 9.5), (12.9, 6.5, 0.5), arch, 0.03)
    frieze = pat_mat("frieze_p", (0.06, 0.15, 0.6), (0.7, 0.1, 0.06), "brick", 0.9, rot=(90, 0, 0)) if painted else mb
    box("frieze", (0, 0, 10.45), (12.9, 6.5, 0.45), frieze, 0.02)
    corn = pat_mat("corn_p", (0.7, 0.08, 0.05), (0.1, 0.25, 0.7), "checker", 3.0) if painted else mb
    box("cornice", (0, 0, 11.05), (13.3, 6.9, 0.15), corn, 0.02)
    # pediment (front & back) as triangular prism
    bm = bmesh.new()
    pts = [(-13.3, 0), (13.3, 0), (0, 4.2)]
    for y in (-6.9, 6.9):
        for x, z in pts: bm.verts.new((x, y, 11.2 + z))
    bm.verts.ensure_lookup_table(); v = bm.verts
    bm.faces.new((v[0], v[1], v[2])); bm.faces.new((v[5], v[4], v[3]))
    bm.faces.new((v[0], v[3], v[4], v[1])); bm.faces.new((v[1], v[4], v[5], v[2])); bm.faces.new((v[2], v[5], v[3], v[0]))
    me = bpy.data.meshes.new("ped"); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new("pediment", me); bpy.context.collection.objects.link(o)
    o.data.materials.append(mat("ped_p", (0.1, 0.3, 0.75), 0.6) if painted else mb)
    roof = mat("roof", (0.62, 0.28, 0.16), 0.8)
    for sd in (-1, 1):
        box(f"roof{sd}", (sd * 6.65, 0, 13.38), (7.05, 7.2, 0.14), roof, 0.02, rot=(0, R(sd * 17.6), 0))
    # pediment figures (little statues) — painted
    for i, x in enumerate((-6, -3, 0, 3, 6)):
        h = 2.6 - abs(x) * 0.3
        cyl(f"pf{i}", (x, -6.95, 11.2 + h / 2), 0.32, h, pat_mat("pf_p", (0.75, 0.1, 0.05), (0.92, 0.7, 0.2), "checker", 6) if painted else mb, verts=12)
        sphere(f"pfh{i}", (x, -6.95, 11.25 + h + 0.2), 0.26, mat("skin", (0.86, 0.6, 0.42), 0.5) if painted else mb, seg=12)


def temple(painted=False, loc=(0, 0, 0), rot=(0, 0, 0)):
    root = parent_all(new_objs(_temple, painted), "temple"); root.location = loc; root.rotation_euler = rot
    return root


def relief_slab(loc=(0, 0, 0), w=4.0, h=1.6, name="slab", seed=0, rotz=0.0):
    objs = new_objs(_relief_slab, w, h, name, seed)
    root = parent_all(objs, name + "_root"); root.location = loc; root.rotation_euler = (0, 0, rotz)
    return root


def _relief_slab(w, h, name, seed):
    import random
    loc = (0, 0, 0)
    rs = random.Random(seed)
    mb = marble("slabm")
    o = [box(name, loc, (w / 2, 0.15, h / 2), mb, 0.03)]
    x0, y0, z0 = loc
    for k in range(2):  # two riders
        cx = x0 - w * 0.22 + k * w * 0.45 + rs.uniform(-0.1, 0.1)
        o.append(sphere(f"{name}hb{k}", (cx, y0 - 0.18, z0 - 0.05), 0.5 * h / 1.6, mb, scl=(1.5, 0.35, 0.7)))
        o.append(sphere(f"{name}hh{k}", (cx + 0.75 * h / 1.6, y0 - 0.18, z0 + 0.3 * h / 1.6), 0.22 * h / 1.6, mb, scl=(1.3, 0.4, 0.8)))
        for j, lx in enumerate((-0.5, -0.3, 0.35, 0.55)):
            o.append(cyl(f"{name}hl{k}{j}", (cx + lx * h / 1.6, y0 - 0.17, z0 - 0.45 * h / 1.6), 0.05 * h / 1.6, 0.6 * h / 1.6, mb, rot=(0, R(rs.uniform(-25, 25)), 0), verts=8))
        o.append(cyl(f"{name}rb{k}", (cx, y0 - 0.2, z0 + 0.38 * h / 1.6), 0.13 * h / 1.6, 0.55 * h / 1.6, mb, verts=12))
        o.append(sphere(f"{name}rh{k}", (cx + 0.03, y0 - 0.2, z0 + 0.75 * h / 1.6), 0.12 * h / 1.6, mb))
    return o


def gallery():
    wall = mat("gwall", (0.72, 0.68, 0.6), 0.85); fl = mat("gfloor", (0.35, 0.3, 0.26), 0.5)
    box("gfloor", (0, 15, -0.05), (8, 30, 0.05), fl, 0)
    for sd in (-1, 1):
        box(f"gwall{sd}", (sd * 6, 15, 4), (0.2, 30, 4.2), wall, 0)
        for i in range(7):
            relief_slab((sd * 5.75, 2 + i * 5.2, 2.6), 4.2, 1.5, f"s{sd}{i}", i, R(-90 * sd))
    box("gend", (0, 42, 4), (6, 0.2, 4.2), wall, 0)
    box("sky", (0, 15, 8.3), (6.2, 30, 0.1), mat("skyl", (1, 0.97, 0.9), emit=(1, 0.96, 0.88), estr=0.8), 0)
    for i in range(6):
        bpy.ops.object.light_add(type="AREA", location=(0, 2 + i * 7, 7.8)); a = bpy.context.object.data
        a.energy = 350; a.size = 5; a.color = (1, 0.95, 0.88)


def P(name):
    S = None
    if name == "temple":          # Grécia antiga, templo pintado
        mood("day"); ground((0.62, 0.5, 0.33), strength=1.2, z=-0.3)
        temple(painted=True, rot=(0, 0, R(-18)))
        for x, y, s in ((-22, 6, 1.4), (20, 12, 1.6), (-16, -12, 1.1), (26, -4, 1.2)): olive(x, y, s)
        camera((-6, -42, 7.0), (0, 0, 8.0), 30, None)
    elif name in ("st_paint", "st_white", "st_uv"):
        style = name[3:]
        if style == "uv":
            set_world((0.01, 0.0, 0.03), 0.3)
            area((-2, -4, 4), (55, 0, -25), 300, (0.45, 0.3, 1.0), 3)
        else:
            mood("day")
        statue(style)
        box("pave", (0, 4, -0.05), (12, 12, 0.05), mat("pave", (0.55, 0.5, 0.42), 0.8) if style != "uv" else mat("pave_u", (0.05, 0.04, 0.07), 0.8), 0)
        camera((0.7, -5.2, 1.5), (0, 0, 2.0), 30, None)
    elif name == "ruins":         # Renascimento: estátua desenterrada
        mood("day"); ground((0.5, 0.38, 0.24), strength=1.4, z=-0.2, center=(0, 20))
        statue("white", loc=(-2.0, 1.0, 0.3), rot=(0, R(86), R(10)), name="lying", plinth=False)
        sphere("mound", (-1.05, 1.5, 0.2), 0.75, mat("gground", (0.5, 0.38, 0.24), 0.95), scl=(1.1, 1.3, 0.45))
        mb = marble("rm")
        for i, (x, y, h, tilt) in enumerate(((-4.5, 4, 3.2, 4), (4.5, 6, 1.6, -3), (-2, 10, 4.6, 0), (6.5, 12, 2.4, 6))):
            cone(f"rcol{i}", (x, y, h / 2 - 0.2), 0.62, 0.55, h, mb, rot=(R(tilt), R(tilt * 0.6), 0), verts=20)
        for i, (x, y, a) in enumerate(((-3, -1.5, 30), (2.8, 1.8, -50))):
            cyl(f"drum{i}", (x, y, 0.35), 0.55, 1.0, mb, rot=(0, R(90), R(a)), verts=20)
        camera((-0.4, -4.6, 2.0), (-0.5, 1.0, 0.5), 28, None)
    elif name == "gallery":       # Museu Britânico (1937): galeria com frisos
        mood("interior"); set_world((0.4, 0.38, 0.35), 0.25)
        gallery()
        statue("white", loc=(0, 6, 0), rot=(0, 0, R(-10)), s=1.05)
        camera((1.0, -2.5, 1.8), (0, 12, 2.5), 20, None)
    elif name == "frieze":        # close no relevo do Partenon
        mood("day"); set_world((0.6, 0.6, 0.62), 0.6)
        relief_slab((0, 0, 0), 4.0, 1.6, "fz", 3)
        box("fzwall", (0, 0.3, 0), (6, 0.1, 5), mat("fzw", (0.3, 0.28, 0.27), 0.9), 0)
        camera((0.2, -4.2, 0.2), (0.2, 0, 0.0), 26, None)
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
