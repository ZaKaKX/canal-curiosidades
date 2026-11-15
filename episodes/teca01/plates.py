"""TECA 01 — Perdido na Colômbia: placas 3D. uso: python plates.py <placa> <outdir>
Reaproveita os helpers de kit/bl_scenes.py (mat, box, cyl, mood, camera, render...)."""
import os, sys, math, random
KIT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "kit")
src = open(os.path.join(KIT, "bl_scenes.py"), encoding="utf-8").read()
helpers = src.split("# ---------------- interiors / props ----------------")[0]
rend = "def render(name):" + src.split("def render(name):")[1].replace("\nrender(PLATE)", "")
exec(helpers)
exec(rend)
import bpy
from mathutils import Vector
random.seed(7)


def mix_mat(name, c1, c2, scale=6.0, rough=0.8, bump=0.0):
    if name in MATS: return MATS[name]
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; n = nt.nodes; l = nt.links; b = n["Principled BSDF"]
    b.inputs["Roughness"].default_value = rough
    nz = n.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = scale; nz.inputs["Detail"].default_value = 6
    cr = n.new("ShaderNodeValToRGB"); cr.color_ramp.elements[0].color = (*c1, 1); cr.color_ramp.elements[1].color = (*c2, 1)
    cr.color_ramp.elements[0].position = 0.35; cr.color_ramp.elements[1].position = 0.65
    l.new(nz.outputs["Fac"], cr.inputs["Fac"]); l.new(cr.outputs["Color"], b.inputs["Base Color"])
    if bump:
        bp = n.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = bump
        l.new(nz.outputs["Fac"], bp.inputs["Height"]); l.new(bp.outputs["Normal"], b.inputs["Normal"])
    MATS[name] = m
    return m


def terrain(name, loc, size, strength, nscale, m, sub=140):
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=sub, y_subdivisions=sub, size=size, location=loc)
    o = bpy.context.object; o.name = name
    tx = bpy.data.textures.new(name + "tx", "CLOUDS"); tx.noise_scale = nscale; tx.noise_depth = 4
    d = o.modifiers.new("d", "DISPLACE"); d.texture = tx; d.strength = strength; d.texture_coords = "GLOBAL"
    bpy.ops.object.shade_smooth(); o.data.materials.append(m)
    return o


def ground(name, loc, size, m):
    bpy.ops.mesh.primitive_plane_add(size=size, location=loc); o = bpy.context.object; o.name = name
    o.data.materials.append(m); return o


def blob(name, loc, r, m, sc_=(1, 1, 1), lump=0.35):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=r, location=loc)
    o = bpy.context.object; o.name = name; o.scale = sc_
    tx = bpy.data.textures.new(name + "t", "CLOUDS"); tx.noise_scale = r * 0.6
    d = o.modifiers.new("d", "DISPLACE"); d.texture = tx; d.strength = r * lump; d.texture_coords = "GLOBAL"
    bpy.ops.object.shade_smooth(); o.data.materials.append(m)
    return o


def mountain(name, loc, r, h, m, lump=0.25):
    bpy.ops.mesh.primitive_cone_add(vertices=64, radius1=r, radius2=r * 0.04, depth=h, location=(loc[0], loc[1], loc[2] + h / 2))
    o = bpy.context.object; o.name = name
    md = o.modifiers.new("s", "SUBSURF"); md.levels = 3; md.render_levels = 3
    tx = bpy.data.textures.new(name + "t", "CLOUDS"); tx.noise_scale = r * 0.25; tx.noise_depth = 4
    d = o.modifiers.new("d", "DISPLACE"); d.texture = tx; d.strength = r * lump; d.texture_coords = "GLOBAL"
    bpy.ops.object.shade_smooth(); o.data.materials.append(m)
    return o


def volcano(name, loc, r, h, m):
    bpy.ops.mesh.primitive_cone_add(vertices=64, radius1=r, radius2=r * 0.16, depth=h, location=(loc[0], loc[1], loc[2] + h / 2))
    o = bpy.context.object; o.name = name
    md = o.modifiers.new("s", "SUBSURF"); md.levels = 3; md.render_levels = 3
    tx = bpy.data.textures.new(name + "t", "CLOUDS"); tx.noise_scale = r * 0.18
    d = o.modifiers.new("d", "DISPLACE"); d.texture = tx; d.strength = r * 0.12; d.texture_coords = "GLOBAL"
    bpy.ops.object.shade_smooth(); o.data.materials.append(m)
    return o


LEAF = None


def tree(loc, h=6.0, kind="round", seed=0):
    rr = random.Random(seed)
    bark = mat("bark", (0.16, 0.1, 0.06), 0.9)
    leaf = mix_mat("leaf", (0.05, 0.16, 0.04), (0.16, 0.32, 0.07), 3.0, 0.75)
    leaf2 = mix_mat("leaf2", (0.02, 0.09, 0.03), (0.08, 0.2, 0.05), 3.0, 0.8)
    x, y, z = loc
    cyl(f"tr{seed}", (x, y, z + h * 0.35), h * 0.045, h * 0.7, bark, verts=10)
    if kind == "round":
        for k in range(4):
            blob(f"lf{seed}_{k}", (x + rr.uniform(-1, 1) * h * 0.18, y + rr.uniform(-1, 1) * h * 0.18, z + h * (0.68 + rr.uniform(-0.1, 0.15))),
                 h * rr.uniform(0.2, 0.3), leaf if k % 2 else leaf2)
    elif kind == "tall":  # eucalipto
        for k in range(5):
            blob(f"lf{seed}_{k}", (x + rr.uniform(-1, 1) * h * 0.1, y + rr.uniform(-1, 1) * h * 0.1, z + h * (0.55 + k * 0.1)),
                 h * rr.uniform(0.12, 0.17), leaf2 if k % 2 else leaf, sc_=(1, 1, 1.3))
    elif kind == "palm":
        for k in range(7):
            a = k / 7 * math.tau
            blob(f"lf{seed}_{k}", (x + math.cos(a) * h * 0.22, y + math.sin(a) * h * 0.22, z + h * 0.68), h * 0.14, leaf, sc_=(1.8, 0.6, 0.35), lump=0.2)


def bush(loc, r=0.8, seed=0):
    leaf2 = mix_mat("leaf2", (0.02, 0.09, 0.03), (0.08, 0.2, 0.05), 3.0, 0.8)
    blob(f"bu{seed}", loc, r, leaf2, sc_=(1.3, 1, 0.8))


def house_col(name, loc, w, d, h, wall, roof=(0.45, 0.13, 0.06), door=(0.25, 0.12, 0.05), rot=0, lit=False):
    x, y, z = loc
    wm = mat(name + "w", wall, 0.85)
    box(name, (x, y, z + h / 2), (w / 2, d / 2, h / 2), wm, 0.03, rot=(0, 0, R(rot)))
    bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=1, radius2=0, depth=1, location=(x, y, z + h + 0.45), rotation=(0, 0, R(45 + rot)))
    o = bpy.context.object; o.scale = (w * 0.78, d * 0.78, 0.9); o.data.materials.append(mat("roof", roof, 0.7))
    dm = mat("door", door, 0.6)
    win = mat("winl" if lit else "wind", (0.9, 0.6, 0.3) if lit else (0.06, 0.07, 0.09), 0.3, emit=(1, 0.6, 0.25) if lit else None, estr=3 if lit else 0)
    c, s_ = math.cos(R(rot)), math.sin(R(rot))
    def at(dx, dz):
        return (x + c * dx - s_ * (-d / 2 - 0.02), y + s_ * dx + c * (-d / 2 - 0.02), z + dz)
    box(name + "dr", at(0, 1.0), (0.45, 0.04, 1.0), dm, 0.02, rot=(0, 0, R(rot)))
    for dx in (-w * 0.32, w * 0.32):
        if abs(dx) > 0.9:
            box(name + f"wn{dx:.1f}", at(dx, 1.6), (0.4, 0.04, 0.45), win, 0.02, rot=(0, 0, R(rot)))
            box(name + f"sh{dx:.1f}", at(dx, 1.12), (0.5, 0.06, 0.05), mat("trim", (0.9, 0.88, 0.8), 0.6), 0.01, rot=(0, 0, R(rot)))


def pickup(name, loc, rot=0, col=(0.012, 0.012, 0.014), lights=False):
    body = mat(name + "b", col, 0.18, 0.6)
    glass = mat("cglass", (0.02, 0.025, 0.03), 0.05, 0.2)
    tire = mat("tire", (0.015, 0.015, 0.015), 0.85)
    rim = mat("rim", (0.5, 0.5, 0.52), 0.3, 1.0)
    objs = []
    objs.append(box(name + "low", (0, 0, 0.75), (2.6, 0.95, 0.38), body, 0.12))
    objs.append(box(name + "cab", (0.55, 0, 1.45), (1.05, 0.88, 0.38), body, 0.14))
    objs.append(box(name + "ws", (-0.42, 0, 1.45), (0.06, 0.8, 0.3), glass, 0.04, rot=(0, R(-28), 0)))
    for sy in (-1, 1):
        objs.append(box(name + f"sw{sy}", (0.55, sy * 0.89, 1.48), (0.85, 0.02, 0.27), glass, 0.02))
        objs.append(box(name + f"bw{sy}", (2.0, sy * 0.92, 1.25), (0.6, 0.05, 0.14), body, 0.03))
        for wx in (-1.6, 1.7):
            objs.append(cyl(name + f"t{sy}{wx}", (wx, sy * 0.92, 0.45), 0.45, 0.32, tire, rot=(R(90), 0, 0), verts=24))
            objs.append(cyl(name + f"r{sy}{wx}", (wx, sy * 1.07, 0.45), 0.24, 0.03, rim, rot=(R(90), 0, 0), verts=16))
    objs.append(box(name + "gr", (-2.62, 0, 0.85), (0.03, 0.7, 0.2), mat("chrome", (0.6, 0.6, 0.62), 0.2, 1.0), 0.02))
    hl = mat("hl_on" if lights else "hl", (1, 0.95, 0.85), 0.2, emit=(1, 0.95, 0.85) if lights else None, estr=20 if lights else 0)
    for sy in (-1, 1):
        objs.append(box(name + f"hl{sy}", (-2.6, sy * 0.68, 0.98), (0.03, 0.18, 0.08), hl, 0.01))
    root = parent_all(objs, name)
    root.location = loc; root.rotation_euler = (0, 0, R(rot))
    return root


def police_car(name, loc, rot=0):
    white = mat("pwhite", (0.85, 0.86, 0.84), 0.25, 0.3)
    green = mat("pgreen", (0.05, 0.25, 0.1), 0.3, 0.3)
    glass = mat("cglass", (0.02, 0.025, 0.03), 0.05, 0.2)
    tire = mat("tire", (0.015, 0.015, 0.015), 0.85)
    objs = [box(name + "low", (0, 0, 0.62), (2.3, 0.9, 0.3), white, 0.14),
            box(name + "stripe", (0, 0, 0.58), (2.32, 0.92, 0.1), green, 0.02),
            box(name + "cab", (0.15, 0, 1.15), (1.15, 0.82, 0.3), white, 0.18),
            box(name + "win", (0.15, 0, 1.17), (1.18, 0.83, 0.2), glass, 0.1),
            box(name + "bar", (0.15, 0, 1.52), (0.35, 0.6, 0.06), mat("barbase", (0.1, 0.1, 0.1), 0.4), 0.02)]
    objs.append(box(name + "red", (0.15, -0.3, 1.6), (0.3, 0.28, 0.06), mat("lred", (1, 0.1, 0.1), 0.2, emit=(1, 0.05, 0.05), estr=30), 0.02))
    objs.append(box(name + "blue", (0.15, 0.3, 1.6), (0.3, 0.28, 0.06), mat("lblue", (0.1, 0.3, 1), 0.2, emit=(0.1, 0.3, 1), estr=30), 0.02))
    for sy in (-1, 1):
        for wx in (-1.45, 1.45):
            objs.append(cyl(name + f"t{sy}{wx}", (wx, sy * 0.86, 0.36), 0.36, 0.28, tire, rot=(R(90), 0, 0), verts=24))
        objs.append(box(name + f"hl{sy}", (-2.3, sy * 0.62, 0.75), (0.03, 0.18, 0.07), mat("hl_on", (1, 0.95, 0.85), 0.2, emit=(1, 0.95, 0.85), estr=20), 0.01))
    root = parent_all(objs, name); root.location = loc; root.rotation_euler = (0, 0, R(rot))
    return root


def sun_golden(az=-35, el=12, e=4.5):
    sun((90 - el, 0, az), e * 1.25, (1.0, 0.66, 0.38), 2)


def out_world(k=0.45):
    set_world((0.42, 0.48, 0.62), k)


# ------------------------------------------------------------------ plates

def P(name):
    grass = mix_mat("grass", (0.08, 0.2, 0.04), (0.2, 0.33, 0.08), 0.6, 0.9, 0.3)
    dirt = mix_mat("dirt", (0.24, 0.15, 0.08), (0.36, 0.25, 0.14), 1.2, 0.95, 0.4)
    hillm = mix_mat("hill", (0.06, 0.17, 0.05), (0.18, 0.28, 0.08), 0.08, 0.9)
    rock = mix_mat("rock", (0.18, 0.16, 0.15), (0.3, 0.27, 0.24), 0.1, 0.9)

    if name == "quadra":  # quadra da escola, fim de tarde entrando pela janela
        mood("interior"); set_world((0.5, 0.42, 0.35), 0.35)
        floor = mix_mat("wood_floor", (0.55, 0.3, 0.12), (0.7, 0.42, 0.18), 3, 0.35)
        ground("floor", (0, 6, 0), 40, floor)
        wall = mix_mat("gymwall", (0.45, 0.2, 0.12), (0.55, 0.28, 0.16), 14, 0.85, 0.2)
        box("back", (0, 14, 6), (20, 0.2, 6), wall, 0)
        box("stripe", (0, 13.8, 2.0), (20, 0.05, 0.35), mat("gstripe", (0.1, 0.16, 0.32), 0.6), 0)
        for x in (-9, -5, 5, 9):
            box(f"win{x}", (x, 13.75, 7.5), (1.4, 0.05, 1.8), mat("gwin", (1, 0.85, 0.6), 0.2, emit=(1, 0.7, 0.4), estr=1.5), 0)
        # cesta
        box("pole", (0, 12.8, 2.5), (0.12, 0.12, 2.5), mat("pole", (0.2, 0.2, 0.22), 0.4, 0.8), 0)
        box("arm", (0, 12.2, 4.9), (0.08, 0.6, 0.08), mat("pole", (0.2, 0.2, 0.22)), 0)
        box("board", (0, 11.6, 5.6), (1.2, 0.05, 0.75), mat("board", (0.95, 0.95, 0.95), 0.3), 0.02)
        box("sq", (0, 11.55, 5.35), (0.4, 0.02, 0.3), mat("sqr", (0.85, 0.2, 0.15), 0.4), 0)
        bpy.ops.mesh.primitive_torus_add(major_radius=0.32, minor_radius=0.03, location=(0, 11.15, 4.95))
        bpy.context.object.data.materials.append(mat("rimo", (0.95, 0.35, 0.05), 0.3, 0.7))
        for i in range(4):  # arquibancada
            box(f"blch{i}", (-12 + 0, 10 - i * 0.0, 0.4 + i * 0.6), (3, 0.6 + i * 0.0, 0.3), mat("bl", (0.35, 0.22, 0.12), 0.6), 0.03)
        line = mat("cline", (0.95, 0.95, 0.95), 0.4)
        box("l1", (0, 6, 0.005), (20, 0.05, 0.005), line, 0)
        sun((62, 0, 160), 6.0, (1.0, 0.78, 0.5), 1.5)
        area((0, 0, 9), (0, 0, 0), 900, (1, 0.9, 0.8), 10)
        camera((0.0, -3.5, 1.6), (0, 10, 3.2), lens=28)

    elif name == "pasto":  # cidade andina, casas coloridas, igreja, vulcão atrás
        out_world(0.5); sun_golden(-60, 14, 4.8)
        ground("praca", (0, 4, 0), 60, mix_mat("pedra", (0.42, 0.38, 0.33), (0.55, 0.5, 0.44), 4, 0.8, 0.3))
        cols = [(0.85, 0.55, 0.25), (0.75, 0.82, 0.86), (0.9, 0.82, 0.55), (0.55, 0.7, 0.55), (0.88, 0.6, 0.55), (0.95, 0.93, 0.85)]
        for i, x in enumerate((-11, -6.8, -2.6, 6.8, 11)):
            house_col(f"h{i}", (x, 13 + (i % 2) * 0.6, 0), 4.0, 4, 4.2 + (i % 3) * 0.6, cols[i % len(cols)])
        # igreja
        wch = mat("church", (0.93, 0.9, 0.82), 0.8)
        box("nave", (2.2, 18, 3.5), (2.4, 3, 3.5), wch, 0.04)
        for sx in (-1, 1):
            box(f"tw{sx}", (2.2 + sx * 2.0, 15.6, 5.0), (0.8, 0.8, 5.0), wch, 0.04)
            bpy.ops.mesh.primitive_uv_sphere_add(radius=0.9, location=(2.2 + sx * 2.0, 15.6, 10.2))
            o = bpy.context.object; o.scale = (1, 1, 1.25); o.data.materials.append(mat("dome", (0.35, 0.5, 0.6), 0.4, 0.4)); bpy.ops.object.shade_smooth()
        box("cdoor", (2.2, 14.95, 1.4), (0.8, 0.05, 1.4), mat("door", (0.25, 0.12, 0.05)), 0.02)
        for x in (-4.5, 9):
            tree((x, 8, 0), 4.5, "round", seed=int(x * 10))
        mountain("m1", (-60, 100, 0), 38, 30, hillm, 0.25); mountain("m2", (35, 100, 0), 42, 34, hillm, 0.25)
        volcano("galeras", (-26, 150, 0), 55, 52, rock)
        camera((0.8, -14, 1.7), (1.5, 40, 7.0), lens=26)

    elif name == "trilha":  # trilha na montanha, eucaliptos, vale
        out_world(0.5); sun_golden(-50, 12, 5.0)
        terrain("chao", (0, 10, -0.2), 50, 0.6, 3.0, grass)
        bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 8, 0.12)); o = bpy.context.object; o.scale = (2.2, 26, 1); o.rotation_euler = (0, 0, R(8))
        o.data.materials.append(dirt)
        for k in range(10):
            x = random.choice([-1, 1]) * random.uniform(4, 13); y = random.uniform(4, 30)
            tree((x, y, 0), random.uniform(7, 11), "tall", seed=k)
        for k in range(8):
            bush((random.choice([-1, 1]) * random.uniform(2.8, 7), random.uniform(2, 20), 0.2), random.uniform(0.5, 1.0), seed=k)
        terrain("vale", (0, 90, -10), 260, 22, 35, hillm, 120)
        mountain("m1", (-50, 170, 0), 60, 50, hillm); mountain("m2", (60, 190, 0), 70, 60, hillm)
        volcano("galeras", (0, 230, 0), 60, 55, rock)
        camera((0, -5, 1.8), (0, 30, 4.5), lens=26)

    elif name == "mato":  # mato fechado, raios de luz
        set_world((0.35, 0.42, 0.3), 0.9); sun_golden(-100, 45, 5.0)
        terrain("chao", (0, 10, -0.2), 50, 0.5, 2.5, mix_mat("forestfloor", (0.07, 0.1, 0.03), (0.2, 0.15, 0.06), 1.0, 0.95, 0.3))
        for k in range(22):
            x = random.uniform(-12, 12); y = random.uniform(5, 40)
            if abs(x) < 2.0 and y < 15: x += 4 * (1 if x >= 0 else -1)
            tree((x, y, 0), random.uniform(8, 14), random.choice(["round", "tall", "palm"]), seed=100 + k)
        for k in range(16):
            bush((random.uniform(-9, 9), random.uniform(3, 25), 0.2), random.uniform(0.6, 1.4), seed=200 + k)
        camera((0, -5, 1.7), (0, 25, 3.5), lens=26)

    elif name in ("casa", "casa_close"):  # casinha no mato com caminhonetes pretas, entardecer
        out_world(0.35); sun_golden(-120, 8, 4.0)
        terrain("chao", (0, 10, -0.3), 60, 0.5, 3, grass)
        bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 6, 0.1)); o = bpy.context.object; o.scale = (9, 9, 1); o.data.materials.append(dirt)
        house_col("casa", (0, 14, 0), 8.0, 5.5, 3.4, (0.82, 0.76, 0.62), roof=(0.4, 0.14, 0.07), lit=True)
        box("porch", (0, 10.9, 0.15), (4.2, 0.9, 0.15), mat("porchw", (0.3, 0.18, 0.1), 0.7), 0.02)
        for x in (-3.8, 3.8):
            cyl(f"post{x}", (x, 10.2, 1.7), 0.09, 3.2, mat("porchw", (0.3, 0.18, 0.1)), verts=8)
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.12, location=(0.9, 11.05, 2.6))
        bpy.context.object.data.materials.append(mat("bulb", (1, 0.8, 0.5), emit=(1, 0.75, 0.4), estr=40))
        bpy.ops.object.light_add(type="POINT", location=(0.9, 10.6, 2.5)); bpy.context.object.data.energy = 250; bpy.context.object.data.color = (1, 0.7, 0.4)
        pickup("pk1", (-4.6, 7.0, 0), rot=-30); pickup("pk2", (4.8, 7.4, 0), rot=205); pickup("pk3", (7.6, 12.5, 0), rot=160)
        for k in range(14):
            x = random.choice([-1, 1]) * random.uniform(8, 20); y = random.uniform(12, 40)
            tree((x, y, 0), random.uniform(8, 13), random.choice(["round", "palm", "tall"]), seed=300 + k)
        for k in range(5):
            tree((random.uniform(-8, 8), random.uniform(22, 34), 0), random.uniform(9, 13), "round", seed=400 + k)
        if name == "casa":
            camera((0, -2.5, 1.6), (0, 14, 3.4), lens=26)
        else:
            camera((0.6, 4.5, 1.65), (0.2, 14, 1.8), lens=32)

    elif name == "estrada":  # estrada de terra ao entardecer, caminhão lá no fim
        out_world(0.75); sun_golden(150, 9, 4.5)
        terrain("chao", (0, 20, -0.3), 90, 0.6, 3, grass)
        bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 30, 0.08)); o = bpy.context.object; o.scale = (3.2, 70, 1); o.data.materials.append(dirt)
        for k in range(18):
            side = 1 if k % 2 else -1
            tree((side * random.uniform(5, 14), random.uniform(5, 60), 0), random.uniform(8, 13), random.choice(["tall", "round", "palm"]), seed=500 + k)
        # caminhão no fim da estrada
        tr = mat("truck", (0.35, 0.08, 0.05), 0.4, 0.2)
        box("tcab", (0.6, 52, 1.6), (1.3, 1.2, 1.2), tr, 0.15)
        box("tbox", (0.6, 56, 2.0), (1.4, 3.0, 1.7), mat("tbox", (0.75, 0.73, 0.68), 0.7), 0.06)
        pickup("pkr", (-2.5, 47, 0), rot=95)
        mountain("m1", (-40, 160, 0), 60, 45, hillm); mountain("m2", (50, 170, 0), 55, 40, hillm)
        camera((0.2, -4, 1.6), (0.3, 40, 2.2), lens=30)

    elif name == "rio":  # barranco + rio
        out_world(0.4); sun_golden(-130, 10, 4.5)
        water = bpy.data.materials.new("water"); water.use_nodes = True
        b = water.node_tree.nodes["Principled BSDF"]; b.inputs["Base Color"].default_value = (0.04, 0.12, 0.12, 1); b.inputs["Roughness"].default_value = 0.08
        bpy.ops.mesh.primitive_grid_add(x_subdivisions=200, y_subdivisions=200, size=80, location=(0, 20, 0.0))
        o = bpy.context.object; o.name = "SEA"
        tx = bpy.data.textures.new("rw", "CLOUDS"); tx.noise_scale = 0.8
        d = o.modifiers.new("d", "DISPLACE"); d.texture = tx; d.strength = 0.12; d.texture_coords = "GLOBAL"; bpy.ops.object.shade_smooth()
        o.data.materials.append(water)
        for sx in (-1, 1):
            terrain(f"bank{sx}", (sx * 10.5, 20, -0.2), 16, 3.5, 4.0, grass, 100)
            box(f"slope{sx}", (sx * 4.8, 20, 0.0), (1.2, 30, 1.6), dirt, 0.6, rot=(0, R(sx * 35), 0))
            for k in range(8):
                tree((sx * random.uniform(8, 18), random.uniform(6, 40), 1.0), random.uniform(8, 12), random.choice(["round", "palm"]), seed=600 + k + (sx > 0) * 20)
        for k in range(6):
            blob(f"rk{k}", (random.uniform(-4, 4), random.uniform(3, 15), 0.0), random.uniform(0.3, 0.7), rock, sc_=(1.2, 1, 0.6))
        camera((0, -3, 2.2), (0, 25, 2.2), lens=26)

    elif name == "viatura":  # beira do rio, viatura parada
        out_world(0.4); sun_golden(-60, 9, 4.0)
        terrain("chao", (0, 15, -0.3), 70, 0.4, 3, grass)
        bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 10, 0.08)); o = bpy.context.object; o.scale = (40, 3.2, 1); o.data.materials.append(dirt)
        police_car("pol", (1.0, 10.0, 0), rot=180)
        for k in range(14):
            tree((random.uniform(-20, 20), random.uniform(16, 45), 0), random.uniform(8, 13), random.choice(["round", "palm", "tall"]), seed=700 + k)
        camera((-1.2, 3.0, 1.4), (0.6, 12, 1.5), lens=30)

    elif name == "delegacia":  # delegacia simples, luz quente, café
        mood("interior"); set_world((0.35, 0.3, 0.25), 0.3)
        ground("floor", (0, 5, 0), 30, mix_mat("tile", (0.45, 0.43, 0.4), (0.55, 0.53, 0.5), 8, 0.4))
        wall = mat("dwall", (0.62, 0.68, 0.58), 0.85)
        box("back", (0, 9, 3), (10, 0.15, 3), wall, 0)
        box("rodape", (0, 8.85, 0.5), (10, 0.05, 0.5), mat("rod", (0.25, 0.32, 0.25), 0.6), 0)
        box("desk", (0.5, 6.3, 0.75), (2.2, 0.8, 0.05), mat("deskw", (0.35, 0.2, 0.1), 0.5), 0.02)
        box("deskb", (0.5, 6.6, 0.38), (2.1, 0.45, 0.36), mat("deskw", (0.35, 0.2, 0.1)), 0.02)
        for x, c in ((-0.4, (0.95, 0.95, 0.92)), (0.0, (0.85, 0.3, 0.2)), (1.2, (0.95, 0.95, 0.92))):
            cyl(f"cup{x}", (x, 6.0, 0.88), 0.06, 0.13, mat(f"cup{x}", c, 0.3), verts=20)
        box("garrafa", (1.7, 6.2, 1.0), (0.1, 0.1, 0.22), mat("thermos", (0.15, 0.15, 0.17), 0.3, 0.6), 0.04)
        box("cork", (-3.2, 8.82, 2.1), (1.2, 0.04, 0.8), mat("cork", (0.55, 0.38, 0.2), 0.9), 0.02)
        for k in range(6):
            box(f"paper{k}", (-3.9 + (k % 3) * 0.6, 8.78, 2.4 - (k // 3) * 0.6), (0.2, 0.01, 0.25), mat("paper", (0.95, 0.93, 0.85), 0.8), 0)
        box("flagY", (3.2, 8.82, 2.6), (0.9, 0.02, 0.3), mat("fy", (0.95, 0.8, 0.05), 0.6), 0)
        box("flagB", (3.2, 8.82, 2.22), (0.9, 0.02, 0.15), mat("fb", (0.05, 0.15, 0.55), 0.6), 0)
        box("flagR", (3.2, 8.82, 1.99), (0.9, 0.02, 0.15), mat("fr", (0.75, 0.08, 0.1), 0.6), 0)
        box("win", (0.6, 8.8, 2.3), (1.0, 0.03, 0.7), mat("dwin", (1, 0.85, 0.6), 0.2, emit=(1, 0.65, 0.35), estr=1.2), 0)
        bpy.ops.object.light_add(type="POINT", location=(0.5, 5.0, 2.7)); bpy.context.object.data.energy = 500; bpy.context.object.data.color = (1, 0.78, 0.55)
        area((0.6, 8.0, 2.3), (-90, 0, 0), 200, (1, 0.8, 0.55), 2)
        camera((0.3, -0.5, 1.45), (0.4, 9, 1.55), lens=28)
    return None


render(PLATE)
