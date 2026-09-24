"""Lui - Shih Tzu (versão realista).
Blender 4.x/5.x: aba Scripting > Open > lui_realista.py > Run Script (leva ~1 min).
"""
import bpy, math, sys
import numpy as np
from mathutils import Vector, Euler
from mathutils.kdtree import KDTree

N_FIOS = int(next((a.split("=")[1] for a in sys.argv if a.startswith("fios=")), 260000))
rng = np.random.default_rng(7)

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

def smooth(e0, e1, x):
    t = max(0.0, min(1.0, (x - e0) / (e1 - e0))); return t*t*(3-2*t)
def lerp(a, b, t): return tuple(a[i] + (b[i]-a[i])*t for i in range(3))

# ---------- corpo: primitivas unidas por voxel remesh ----------
parts = []
def ell(co, r, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=co, segments=32, ring_count=16,
                                         rotation=tuple(math.radians(a) for a in rot))
    o = bpy.context.active_object; o.scale = r; parts.append(o); return o

# frente do cachorro = -Y, altura em metros "estilizados"
ell((0, 0.11, 0.42), (0.23, 0.40, 0.20))           # tronco (mais longo e gordinho)
ell((0, 0.10, 0.35), (0.205, 0.31, 0.15))          # barriguinha
ell((0, -0.19, 0.43), (0.21, 0.17, 0.20))         # peito
ell((0, 0.34, 0.42), (0.21, 0.17, 0.18))          # garupa
ell((0, -0.28, 0.60), (0.13, 0.12, 0.15), (-25, 0, 0))  # pescoço
ell((0, -0.33, 0.80), (0.20, 0.19, 0.18))         # cabeça
ell((0, -0.31, 0.91), (0.17, 0.15, 0.08))         # topete
ell((0, -0.50, 0.745), (0.105, 0.085, 0.07))      # focinho
ell((0, -0.47, 0.63), (0.11, 0.08, 0.10))         # barba
for s in (-1, 1):
    ell((s*0.07, -0.50, 0.70), (0.075, 0.07, 0.075))              # bochechas/bigode
    ell((s*0.185, -0.30, 0.69), (0.055, 0.08, 0.16), (0, s*-10, 0))  # orelhas
    ell((s*0.115, -0.20, 0.17), (0.07, 0.07, 0.18))              # pata dianteira
    ell((s*0.115, -0.235, 0.035), (0.07, 0.09, 0.045))             # pé dianteiro
    ell((s*0.125, 0.36, 0.32), (0.105, 0.14, 0.14))                 # coxa
    ell((s*0.125, 0.40, 0.15), (0.068, 0.068, 0.15))               # pata traseira
    ell((s*0.125, 0.38, 0.035), (0.07, 0.09, 0.045))              # pé traseiro
# rabo em pluma enrolado sobre as costas
TAIL = []
N = 14
for i in range(N):
    t = i / (N - 1)
    a = math.radians(-60 + 230 * t)
    y = 0.44 + 0.13 * math.cos(a) - 0.10 * t
    z = 0.66 + 0.13 * math.sin(a)
    r = 0.075 - 0.02 * t
    ell((0.04 * t, y, z), (r, r, r)); TAIL.append(((0.04*t, y, z), r))

bpy.ops.object.select_all(action='DESELECT')
for o in parts: o.select_set(True)
bpy.context.view_layer.objects.active = parts[0]
bpy.ops.object.join()
lui = bpy.context.active_object; lui.name = "Lui"
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
rm = lui.modifiers.new("Remesh", 'REMESH'); rm.mode = 'VOXEL'; rm.voxel_size = 0.009
bpy.ops.object.modifier_apply(modifier="Remesh")
sm = lui.modifiers.new("Smooth", 'LAPLACIANSMOOTH'); sm.lambda_factor = 0.8; sm.iterations = 12
bpy.ops.object.modifier_apply(modifier="Smooth")
bpy.ops.object.shade_smooth()

# ---------- cores da pelagem ----------
WHITE = (0.80, 0.78, 0.72)
CREAM = (0.66, 0.58, 0.45)
BLACK = (0.005, 0.0045, 0.0045)
GREY  = (0.03, 0.029, 0.029)

def lerp(a, b, t): return tuple(a[i] + (b[i]-a[i])*t for i in range(3))
def smooth(e0, e1, x):
    t = max(0.0, min(1.0, (x - e0) / (e1 - e0))); return t*t*(3-2*t)

def is_tail(p):
    return any((Vector(p) - Vector(c)).length < r + 0.035 for c, r in TAIL)

def coat(p):
    x, y, z = p
    ax = abs(x)
    # rabo
    if is_tail(p):
        return BLACK
    # orelhas
    if ax > 0.145 and -0.42 < y < -0.17 and 0.5 < z < 0.9:
        return BLACK
    # barba e boca
    if y < -0.40 and z < 0.69:
        return lerp(CREAM, WHITE, 0.55)
    # boca / lábio escuro logo abaixo do nariz
    if y < NOSE_Y + 0.045 and ax < 0.05 and NOSE_Z - 0.075 < z < NOSE_Z - 0.022:
        return lerp(lerp(BLACK, GREY, 0.5), lerp(CREAM, WHITE, 0.5), smooth(0.03, 0.05, ax))
    # cabeça: máscara preta, listra branca fina, topo branco
    if z > 0.64 and y < -0.17:
        col = BLACK
        blaze = smooth(0.035, 0.018, ax) * smooth(0.79, 0.82, z)
        brows = smooth(0.10, 0.06, ax) * smooth(0.89, 0.92, z)
        crown = smooth(0.95, 0.985, z) * smooth(0.19, 0.12, ax)
        col = lerp(col, WHITE, max(blaze, brows, crown))
        muz = smooth(-0.44, -0.48, y) * smooth(0.795, 0.765, z) * smooth(0.15, 0.11, ax)
        col = lerp(col, lerp(CREAM, WHITE, 0.4), muz)
        col = lerp(col, lerp(CREAM, WHITE, 0.55), smooth(0.70, 0.66, z) * smooth(-0.36, -0.42, y))
        return col
    # nuca preta que desce do pescoço
    nape = smooth(0.54, 0.60, z) * smooth(-0.08, -0.16, y) * smooth(-0.40, -0.32, y) \
         * smooth(-0.30, -0.22, y + 0.0 * ax)
    back = smooth(0.46, 0.53, z) * smooth(-0.22, -0.10, y)
    col = lerp(WHITE, GREY, back)
    return lerp(col, BLACK, nape)


# encontra a superfície real do focinho para encaixar o nariz
_hit, _loc, _n, _i = lui.ray_cast(Vector((0, -2, 0.775)), Vector((0, 1, 0)))
NOSE_Y = _loc.y - 0.012 if _hit else -0.60
NOSE_Z = 0.775
print("focinho em y =", NOSE_Y)
me = lui.data
attr = me.color_attributes.new("Pelagem", 'FLOAT_COLOR', 'POINT')
for v in me.vertices:
    attr.data[v.index].color = (*coat(v.co), 1.0)

skin = bpy.data.materials.new("Pele"); skin.use_nodes = True
nt = skin.node_tree; bsdf = nt.nodes["Principled BSDF"]
ca = nt.nodes.new("ShaderNodeVertexColor"); ca.layer_name = "Pelagem"
dark = nt.nodes.new("ShaderNodeMix"); dark.data_type = 'RGBA'; dark.blend_type = 'MULTIPLY'
dark.inputs["Factor"].default_value = 1.0; dark.inputs["B"].default_value = (0.55, 0.5, 0.48, 1)
nt.links.new(ca.outputs["Color"], dark.inputs["A"])
nt.links.new(dark.outputs["Result"], bsdf.inputs["Base Color"])
bsdf.inputs["Roughness"].default_value = 0.9
me.materials.append(skin)

# ---------- olhos (globo com íris, córnea e pálpebras) ----------
from mathutils import Matrix
EYES = [Vector((s*0.083, -0.478, 0.835)) for s in (-1, 1)]
NOSE = Vector((0, NOSE_Y, 0.775))
EYE_R = 0.045

def eye_frame(sx):
    g = Vector((sx*0.22, -1.0, 0.10)).normalized()          # olhar p/ frente, levemente p/ fora e p/ cima
    xa = Vector((0, 0, 1)).cross(g).normalized()
    ya = g.cross(xa)
    return Matrix((xa, ya, g)).transposed().to_4x4(), g
# olhos um pouco mais para dentro da órbita
EYES = [c - eye_frame(-1 if c.x < 0 else 1)[1] * 0.012 for c in EYES]

# material do globo: pupila, íris castanha com estrias, anel escuro, esclera
eye_m = bpy.data.materials.new("Olho"); eye_m.use_nodes = True
en = eye_m.node_tree; ebsdf = en.nodes["Principled BSDF"]
uvn = en.nodes.new("ShaderNodeUVMap")
sep = en.nodes.new("ShaderNodeSeparateXYZ"); en.links.new(uvn.outputs["UV"], sep.inputs[0])
inv = en.nodes.new("ShaderNodeMath"); inv.operation = 'SUBTRACT'; inv.inputs[0].default_value = 1.0
en.links.new(sep.outputs["Y"], inv.inputs[1])                  # 0 = centro da pupila
ramp = en.nodes.new("ShaderNodeValToRGB"); cr = ramp.color_ramp
cr.elements[0].position = 0.0;  cr.elements[0].color = (0.003, 0.002, 0.002, 1)   # pupila
cr.elements[1].position = 0.13; cr.elements[1].color = (0.006, 0.004, 0.003, 1)
for pos, col in ((0.15, (0.022, 0.010, 0.005, 1)),     # borda interna da íris
                 (0.20, (0.048, 0.022, 0.009, 1)),        # íris castanho-escura
                 (0.245, (0.03, 0.014, 0.006, 1)),
                 (0.268, (0.012, 0.007, 0.005, 1)),    # anel escuro (limbo)
                 (0.30, (0.30, 0.22, 0.19, 1)),        # esclera (pouco visível, levemente pigmentada)
                 (0.45, (0.42, 0.33, 0.30, 1))):
    e_ = cr.elements.new(pos); e_.color = col
en.links.new(inv.outputs[0], ramp.inputs["Fac"])
# estrias radiais da íris
smap = en.nodes.new("ShaderNodeCombineXYZ")
mu = en.nodes.new("ShaderNodeMath"); mu.operation = 'MULTIPLY'; mu.inputs[1].default_value = 70
en.links.new(sep.outputs["X"], mu.inputs[0]); en.links.new(mu.outputs[0], smap.inputs["X"])
mv = en.nodes.new("ShaderNodeMath"); mv.operation = 'MULTIPLY'; mv.inputs[1].default_value = 9
en.links.new(sep.outputs["Y"], mv.inputs[0]); en.links.new(mv.outputs[0], smap.inputs["Y"])
nz = en.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 1.0; nz.inputs["Detail"].default_value = 6
en.links.new(smap.outputs[0], nz.inputs["Vector"])
st = en.nodes.new("ShaderNodeMapRange"); st.inputs["To Min"].default_value = 0.55; st.inputs["To Max"].default_value = 1.6
en.links.new(nz.outputs["Fac"], st.inputs["Value"])
mask = en.nodes.new("ShaderNodeMapRange"); mask.interpolation_type = 'SMOOTHSTEP'
mask.inputs["From Min"].default_value = 0.13; mask.inputs["From Max"].default_value = 0.16
en.links.new(inv.outputs[0], mask.inputs["Value"])
mask2 = en.nodes.new("ShaderNodeMapRange"); mask2.interpolation_type = 'SMOOTHSTEP'
mask2.inputs["From Min"].default_value = 0.27; mask2.inputs["From Max"].default_value = 0.24
en.links.new(inv.outputs[0], mask2.inputs["Value"])
mm = en.nodes.new("ShaderNodeMath"); mm.operation = 'MULTIPLY'
en.links.new(mask.outputs[0], mm.inputs[0]); en.links.new(mask2.outputs[0], mm.inputs[1])
mixs = en.nodes.new("ShaderNodeMix"); mixs.data_type = 'RGBA'; mixs.blend_type = 'MULTIPLY'
en.links.new(mm.outputs[0], mixs.inputs["Factor"])
en.links.new(ramp.outputs["Color"], mixs.inputs["A"])
gray = en.nodes.new("ShaderNodeCombineColor")
for ch in ("Red", "Green", "Blue"): en.links.new(st.outputs[0], gray.inputs[ch])
en.links.new(gray.outputs[0], mixs.inputs["B"])
en.links.new(mixs.outputs["Result"], ebsdf.inputs["Base Color"])
ebsdf.inputs["Roughness"].default_value = 0.3

# córnea transparente (dá o brilho molhado e a profundidade)
cor_m = bpy.data.materials.new("Cornea"); cor_m.use_nodes = True
cb = cor_m.node_tree.nodes["Principled BSDF"]
cb.inputs["Base Color"].default_value = (1, 1, 1, 1)
cb.inputs["Transmission Weight"].default_value = 1.0
cb.inputs["Roughness"].default_value = 0.0
cb.inputs["IOR"].default_value = 1.376
cor_m.blend_method = 'BLEND' if hasattr(cor_m, "blend_method") else None

lid_m = bpy.data.materials.new("Palpebra"); lid_m.use_nodes = True
lb = lid_m.node_tree.nodes["Principled BSDF"]
lb.inputs["Base Color"].default_value = (0.014, 0.010, 0.010, 1)
lb.inputs["Roughness"].default_value = 0.3

import bmesh as _bm
AX, AY_UP, AY_DN = 0.80, 0.60, 0.68        # abertura do olho (arredondada, pálpebra de cima um pouco baixa)
for i, c in enumerate(EYES):
    sx = -1 if c.x < 0 else 1
    M, g = eye_frame(sx)
    # globo
    bpy.ops.mesh.primitive_uv_sphere_add(radius=EYE_R, segments=64, ring_count=32, location=(0, 0, 0))
    e = bpy.context.active_object; e.name = f"Olho_{i}"
    e.data.transform(M); e.location = c
    bpy.ops.object.shade_smooth(); e.data.materials.append(eye_m)
    # córnea com leve abaulamento sobre a íris
    bpy.ops.mesh.primitive_uv_sphere_add(radius=EYE_R*1.012, segments=64, ring_count=32, location=(0, 0, 0))
    co_ = bpy.context.active_object; co_.name = f"Cornea_{i}"
    for v in co_.data.vertices:
        d = v.co.normalized()
        bulge = max(0.0, d.z - 0.55) / 0.45
        v.co = d * EYE_R * (1.012 + 0.07 * bulge * bulge)
    co_.data.transform(M); co_.location = c
    bpy.ops.object.shade_smooth(); co_.data.materials.append(cor_m)
    # pálpebras: casca com abertura amendoada, borda encostada no olho
    bpy.ops.mesh.primitive_uv_sphere_add(radius=EYE_R*1.02, segments=96, ring_count=48, location=(0, 0, 0))
    lid = bpy.context.active_object; lid.name = f"Palpebra_{i}"
    bm_ = _bm.new(); bm_.from_mesh(lid.data)
    def inside(p):
        d = p.normalized()
        if d.z <= 0: return False
        ay = AY_UP if d.y > 0 else AY_DN
        return (d.x / AX) ** 2 + (d.y / ay) ** 2 < 1.0
    _bm.ops.delete(bm_, geom=[f for f in bm_.faces if inside(f.calc_center_median())], context='FACES')
    for v in bm_.verts:                       # borda encosta no globo
        if v.is_boundary: v.co = v.co.normalized() * EYE_R * 1.012
    bm_.to_mesh(lid.data); bm_.free()
    lid.data.transform(M); lid.location = c
    sol = lid.modifiers.new("Espessura", 'SOLIDIFY'); sol.thickness = 0.0025; sol.offset = 1.0; sol.use_rim = True
    sub_ = lid.modifiers.new("Suave", 'SUBSURF'); sub_.levels = 1; sub_.render_levels = 2
    bpy.ops.object.shade_smooth(); lid.data.materials.append(lid_m)

# ---------- nariz (couro com textura e narinas) ----------
bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=NOSE, segments=48, ring_count=24)
nose = bpy.context.active_object; nose.name = "Nariz"; nose.scale = (0.044, 0.021, 0.029)
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
bm_nose = nose.data
for v in bm_nose.vertices:        # achata a frente e marca as narinas
    p = v.co
    if p.y < -0.012: p.y = -0.012 + (p.y + 0.012) * 0.35
    for s in (-1, 1):          # narinas em vírgula, abertas p/ os lados
        nx, nz_ = p.x - s*0.0145, p.z + 0.004 + 0.25*(p.x - s*0.0145)*s
        dd = ((nx / 1.0)**2 + (nz_ / 0.6)**2) ** 0.5
        if dd < 0.009 and p.y < -0.004:
            p.y += 0.012 * (1 - dd/0.009) ** 0.7
    if abs(p.x) < 0.002 and p.z < 0.004: p.y += 0.003 * (1 - abs(p.x)/0.002)   # sulco central
bpy.ops.object.shade_smooth()
nm = bpy.data.materials.new("Nariz"); nm.use_nodes = True
nn = nm.node_tree; nb = nn.nodes["Principled BSDF"]
nb.inputs["Base Color"].default_value = (0.006, 0.005, 0.005, 1)
nb.inputs["Roughness"].default_value = 0.42
vo = nn.nodes.new("ShaderNodeTexVoronoi"); vo.inputs["Scale"].default_value = 500
bump = nn.nodes.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.6
nn.links.new(vo.outputs["Distance"], bump.inputs["Height"])
nn.links.new(bump.outputs["Normal"], nb.inputs["Normal"])
nose.data.materials.append(nm)
narina = bpy.data.materials.new("Narina"); narina.use_nodes = True
narina.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.0, 0.0, 0.0, 1)
narina.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 1.0
nose.data.materials.append(narina)
for poly in nose.data.polygons:
    p = poly.center
    for s_ in (-1, 1):
        nx, nz_ = p.x - s_*0.0145, p.z + 0.004 + 0.25*(p.x - s_*0.0145)*s_
        if ((nx)**2 + (nz_/0.6)**2) ** 0.5 < 0.0055 and p.y < -0.002:
            poly.material_index = 1

# ---------- gravatinha de tecido amarela de bolinhas ----------
bow_m = bpy.data.materials.new("Gravatinha"); bow_m.use_nodes = True
bn = bow_m.node_tree; bb = bn.nodes["Principled BSDF"]
bb.inputs["Roughness"].default_value = 0.6
bb.inputs["Sheen Weight"].default_value = 0.4
tc = bn.nodes.new("ShaderNodeTexCoord")
vor = bn.nodes.new("ShaderNodeTexVoronoi"); vor.inputs["Scale"].default_value = 45
bn.links.new(tc.outputs["Object"], vor.inputs["Vector"])
dot = bn.nodes.new("ShaderNodeMath"); dot.operation = 'LESS_THAN'; dot.inputs[1].default_value = 0.22
bn.links.new(vor.outputs["Distance"], dot.inputs[0])
ramp = bn.nodes.new("ShaderNodeValToRGB"); el = ramp.color_ramp.elements
el[0].color = (0.7, 0.03, 0.03, 1); el[1].color = (0.03, 0.15, 0.6, 1)
el.new(0.33).color = (0.05, 0.4, 0.1, 1); el.new(0.66).color = (0.25, 0.05, 0.4, 1)
ramp.color_ramp.interpolation = 'CONSTANT'
bn.links.new(vor.outputs["Color"], ramp.inputs["Fac"])
mix = bn.nodes.new("ShaderNodeMix"); mix.data_type = 'RGBA'
mix.inputs["A"].default_value = (0.95, 0.5, 0.02, 1)
bn.links.new(dot.outputs[0], mix.inputs["Factor"])
bn.links.new(ramp.outputs["Color"], mix.inputs["B"])
bn.links.new(mix.outputs["Result"], bb.inputs["Base Color"])

bow_parts = []
for s in (-1, 1):
    bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=0.055, depth=0.1,
                                    location=(s*0.055, -0.425, 0.53), rotation=(0, math.radians(90*s), 0))
    bow_parts.append(bpy.context.active_object)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(s*0.028, -0.43, 0.45), rotation=(0, math.radians(-10*s), 0))
    t = bpy.context.active_object; t.scale = (0.035, 0.008, 0.1); bow_parts.append(t)
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.022, location=(0, -0.437, 0.53))
bow_parts.append(bpy.context.active_object)
bpy.ops.object.select_all(action='DESELECT')
for o in bow_parts: o.select_set(True)
bpy.context.view_layer.objects.active = bow_parts[0]
bpy.ops.object.join()
bow = bpy.context.active_object; bow.name = "Gravatinha"
bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
bow.scale = (1.6, 0.5, 1.45)
bow.location = (0, -0.53, 0.47)
bow.rotation_euler.x = math.radians(-12)
bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
bpy.ops.object.shade_smooth()
sub = bow.modifiers.new("Sub", 'SUBSURF'); sub.levels = 2; sub.render_levels = 2
bow.data.materials.append(bow_m)

# ---------- PELO: fios individuais penteados ----------
me.calc_loop_triangles()
tris = np.array([t.vertices[:] for t in me.loop_triangles])
vco = np.array([v.co[:] for v in me.vertices])
vno = np.array([v.normal[:] for v in me.vertices])
A, B, C = vco[tris[:, 0]], vco[tris[:, 1]], vco[tris[:, 2]]
area = 0.5 * np.linalg.norm(np.cross(B - A, C - A), axis=1)
M = int(N_FIOS * 1.15)
ti = rng.choice(len(tris), M, p=area / area.sum())
r1, r2 = rng.random(M), rng.random(M)
sq = np.sqrt(r1); u, v, w = 1 - sq, sq * (1 - r2), sq * r2
root = u[:, None]*A[ti] + v[:, None]*B[ti] + w[:, None]*C[ti]
nrm = u[:, None]*vno[tris[ti, 0]] + v[:, None]*vno[tris[ti, 1]] + w[:, None]*vno[tris[ti, 2]]
nrm /= np.linalg.norm(nrm, axis=1, keepdims=True)
# sem pelo em cima dos olhos e do nariz
keep = np.ones(M, bool)
for c in EYES: keep &= np.linalg.norm(root - np.array(c), axis=1) > 0.051
keep &= np.linalg.norm(root - np.array(NOSE), axis=1) > 0.036
root, nrm = root[keep][:N_FIOS], nrm[keep][:N_FIOS]
N = len(root)
x, y, z = root[:, 0], root[:, 1], root[:, 2]
ax = np.abs(x); sx = np.sign(x) + (x == 0)

tail  = np.array([is_tail(p) for p in root])
ears  = (ax > 0.145) & (y > -0.42) & (y < -0.17) & (z > 0.5) & (z < 0.9) & ~tail
beard = (y < -0.40) & (z < 0.69) & ~ears
head  = (z > 0.64) & (y < -0.17) & ~ears & ~beard
muzz  = head & (y < -0.45) & (z < 0.83)
crown = head & (z > 0.93)
legs  = (z < 0.27) & ~tail
feet  = z < 0.07
body  = ~(tail | ears | beard | head | legs)

# comprimento (unidades do modelo; o Lui aqui tem ~1 m, ~4x o tamanho real)
L = np.full(N, 0.075)
L[legs] = 0.07; L[feet] = 0.045
L[head] = 0.05; L[crown] = 0.08; L[muzz] = 0.09
L[beard] = 0.11; L[ears] = 0.22; L[tail] = 0.21
L[body & (z < 0.33)] = 0.10          # franja da barriga um pouco mais longa
nn_ = np.linalg.norm(root - np.array(NOSE), axis=1) < 0.085
L[nn_] = np.minimum(L[nn_], 0.04)
nearbow = np.linalg.norm(root - np.array((0, -0.43, 0.45)), axis=1) < 0.12
L[nearbow] = np.minimum(L[nearbow], 0.045)
L *= rng.uniform(0.7, 1.15, N)

# direção do penteado
G = np.zeros((N, 3))
G[:] = np.stack([sx*0.35, np.full(N, 0.55), np.full(N, -0.75)], 1)       # corpo: p/ trás e p/ baixo
G[legs] = (0, 0.05, -1)
G[head] = np.stack([sx[head]*0.7, np.full(head.sum(), 0.35), np.full(head.sum(), -0.4)], 1)
fore = head & (y < -0.40) & (z > 0.82)   # testa/sobrancelha: penteada p/ cima e p/ trás
G[fore] = np.stack([sx[fore]*0.35, np.full(fore.sum(), 0.6), np.full(fore.sum(), 0.55)], 1)
mz = root[muzz] - np.array(NOSE); mz[:, 2] = mz[:, 2]*0.3 - 0.06
G[muzz] = mz
G[muzz, 1] += 0.35   # afasta do nariz, p/ os lados e p/ trás
G[beard] = (0, -0.25, -1)
G[ears] = np.stack([sx[ears]*0.15, np.full(ears.sum(), 0.05), np.full(ears.sum(), -1)], 1)
G[tail] = np.stack([sx[tail]*0.4 + rng.normal(0, 0.3, tail.sum()), np.full(tail.sum(), 0.2), np.full(tail.sum(), -0.8)], 1)
# pelo perto dos olhos: curto e penteado para longe do olho
for c in EYES:
    de = root - np.array(c); dist = np.linalg.norm(de, axis=1)
    ne = (dist < 0.11) & ~ears
    away = de[ne] / dist[ne, None]; away[:, 2] += 0.35; away[:, 1] += 0.3
    G[ne] = away
    L[ne] = np.minimum(L[ne], 0.03 + 0.4 * (dist[ne] - 0.051))
    # sobrancelhas: tufo acima do olho, p/ cima e p/ fora
    brow = (dist > 0.058) & (dist < 0.12) & (root[:, 2] > c[2] + 0.03) & ~ears
    G[brow] = np.stack([sx[brow]*0.55, np.full(brow.sum(), -0.25), np.full(brow.sum(), 1.0)], 1)
    L[brow] = rng.uniform(0.05, 0.075, brow.sum())
# ponte do focinho: pelo cresce p/ cima e p/ os lados (padrão "crisântemo")
bridge = (ax < 0.05) & (y < -0.49) & (z > 0.79) & (z < 0.87)
G[bridge] = np.stack([sx[bridge]*0.6, np.full(bridge.sum(), 0.1), np.full(bridge.sum(), 1.0)], 1)
L[bridge] = rng.uniform(0.035, 0.05, bridge.sum())
G /= np.linalg.norm(G, axis=1, keepdims=True)
tang = G - (G*nrm).sum(1, keepdims=True)*nrm
tl = np.linalg.norm(tang, axis=1, keepdims=True)
tang = np.where(tl > 0.05, tang/np.maximum(tl, 1e-6), G)

lift = np.full(N, 0.45); lift[beard | ears | tail] = 0.25; lift[muzz] = 0.5
grav = np.clip(L/0.22, 0, 1) * 0.35
grav[body] *= np.clip(1 - nrm[body, 2], 0, 1)     # no dorso a gravidade não empurra p/ dentro

K = 8
pts = np.zeros((N, K, 3)); pts[:, 0] = root
d = nrm*lift[:, None] + tang
d /= np.linalg.norm(d, axis=1, keepdims=True)
d += rng.normal(0, 0.18, (N, 3)); d /= np.linalg.norm(d, axis=1, keepdims=True)
seg = L / (K - 1)
down = np.array([0, 0, -1.0])
for k in range(1, K):
    d = d*(1 - grav[:, None]) + (tang*0.5 + down*0.5)*grav[:, None]
    d += rng.normal(0, 0.06, (N, 3))
    d /= np.linalg.norm(d, axis=1, keepdims=True)
    pts[:, k] = pts[:, k-1] + d*seg[:, None]

# mechas: cada fio é puxado em direção a uma "mecha guia" próxima
NG = N // 40
gi = rng.choice(N, NG, replace=False)
kd = KDTree(NG)
for j, g in enumerate(gi): kd.insert(root[g], j)
kd.balance()
near = np.array([kd.find(p)[1] for p in root])
guide = pts[gi[near]]
clump = np.full(N, 0.45); clump[ears | beard | tail] = 0.75; clump[muzz | crown] = 0.6
sk = (np.arange(K)/(K-1))**0.9
offs = (root - guide[:, 0])[:, None, :]
target = guide + offs*(1 - sk[None, :, None]*0.85)
pts = pts + (target - pts)*(clump[:, None, None]*sk[None, :, None])

# cor por fio
cols = np.array([coat(Vector(p)) for p in root])
cols *= rng.uniform(0.85, 1.12, (N, 1))
white = cols.mean(1) > 0.3
cols[white] *= np.array([1.0, 0.97, 0.92])          # leve tom creme nos brancos
cols[~white] += np.array([0.012, 0.008, 0.005])*rng.random((np.sum(~white), 1))  # reflexos acastanhados

hc = bpy.data.hair_curves.new("PeloLui")
hc.add_curves([K]*N)
hc.position_data.foreach_set("vector", pts.astype(np.float32).ravel())
rad = hc.attributes.new("radius", 'FLOAT', 'POINT')
rr = np.tile(np.linspace(0.0011, 0.00025, K), N).astype(np.float32)
rad.data.foreach_set("value", rr)
ccol = hc.attributes.new("cor", 'FLOAT_COLOR', 'CURVE')
c4 = np.concatenate([cols, np.ones((N, 1))], 1).astype(np.float32)
ccol.data.foreach_set("color", c4.ravel())
pelo = bpy.data.objects.new("PeloLui", hc)
scene.collection.objects.link(pelo)

hm = bpy.data.materials.new("Pelo"); hm.use_nodes = True
hn = hm.node_tree; hn.nodes.remove(hn.nodes["Principled BSDF"])
hb = hn.nodes.new("ShaderNodeBsdfHairPrincipled"); hb.parametrization = 'COLOR'
hat = hn.nodes.new("ShaderNodeAttribute"); hat.attribute_name = "cor"
hn.links.new(hat.outputs["Color"], hb.inputs["Color"])
hb.inputs["Roughness"].default_value = 0.3
hb.inputs["Radial Roughness"].default_value = 0.6
hb.inputs["Random Roughness"].default_value = 0.3
hn.links.new(hb.outputs[0], hn.nodes["Material Output"].inputs["Surface"])
hc.materials.append(hm)

# ---------- piso laminado (como nas fotos) ----------
bpy.ops.mesh.primitive_plane_add(size=30, location=(0, 0, 0))
floor = bpy.context.active_object; floor.name = "Piso"
fm = bpy.data.materials.new("Piso"); fm.use_nodes = True
fn = fm.node_tree; fb = fn.nodes["Principled BSDF"]
ftc = fn.nodes.new("ShaderNodeTexCoord")
fmap = fn.nodes.new("ShaderNodeMapping"); fmap.inputs["Rotation"].default_value = (0, 0, math.radians(58))
fn.links.new(ftc.outputs["Object"], fmap.inputs["Vector"])
brick = fn.nodes.new("ShaderNodeTexBrick")
brick.offset = 0.5; brick.offset_frequency = 1
brick.inputs["Scale"].default_value = 1.0
brick.inputs["Brick Width"].default_value = 2.2
brick.inputs["Row Height"].default_value = 0.5
brick.inputs["Mortar Size"].default_value = 0.004
brick.inputs["Mortar Smooth"].default_value = 0.5
brick.inputs["Bias"].default_value = 0.0
brick.inputs["Color1"].default_value = (0.30, 0.25, 0.20, 1)
brick.inputs["Color2"].default_value = (0.40, 0.34, 0.27, 1)
brick.inputs["Mortar"].default_value = (0.15, 0.12, 0.10, 1)
fn.links.new(fmap.outputs["Vector"], brick.inputs["Vector"])
grain_map = fn.nodes.new("ShaderNodeMapping"); grain_map.inputs["Scale"].default_value = (0.4, 6.0, 1)
fn.links.new(fmap.outputs["Vector"], grain_map.inputs["Vector"])
grain = fn.nodes.new("ShaderNodeTexNoise"); grain.inputs["Scale"].default_value = 3
grain.inputs["Detail"].default_value = 8; grain.inputs["Distortion"].default_value = 1.5
fn.links.new(grain_map.outputs["Vector"], grain.inputs["Vector"])
gr = fn.nodes.new("ShaderNodeMix"); gr.data_type = 'RGBA'; gr.blend_type = 'MULTIPLY'
gr.inputs["Factor"].default_value = 0.45
g2 = fn.nodes.new("ShaderNodeValToRGB")
g2.color_ramp.elements[0].color = (0.75, 0.72, 0.68, 1); g2.color_ramp.elements[1].color = (1.15, 1.1, 1.05, 1)
fn.links.new(grain.outputs["Fac"], g2.inputs["Fac"])
fn.links.new(brick.outputs["Color"], gr.inputs["A"])
fn.links.new(g2.outputs["Color"], gr.inputs["B"])
fn.links.new(gr.outputs["Result"], fb.inputs["Base Color"])
fb.inputs["Roughness"].default_value = 0.4
fbump = fn.nodes.new("ShaderNodeBump"); fbump.inputs["Strength"].default_value = 0.15
fn.links.new(brick.outputs["Fac"], fbump.inputs["Height"])
fn.links.new(fbump.outputs["Normal"], fb.inputs["Normal"])
floor.data.materials.append(fm)

# ---------- luz de ambiente interno ----------
world = bpy.data.worlds.new("Mundo"); scene.world = world; world.use_nodes = True
bg = world.node_tree.nodes["Background"]
bg.inputs["Color"].default_value = (0.75, 0.78, 0.85, 1); bg.inputs["Strength"].default_value = 0.2
bpy.ops.object.light_add(type='AREA', location=(0.3, -0.4, 3.2))
top = bpy.context.active_object; top.data.energy = 120; top.data.size = 3.0
bpy.ops.object.light_add(type='AREA', location=(-2.5, -1.8, 1.6))
win = bpy.context.active_object; win.data.energy = 90; win.data.size = 2.0
win.data.color = (1.0, 0.97, 0.92)
win.rotation_euler = (math.radians(65), 0, math.radians(-54))

# ---------- câmera (ângulo de celular, de cima, como na foto) ----------
bpy.ops.object.camera_add(location=(0.1, -1.55, 1.75))
cam = bpy.context.active_object; scene.camera = cam; cam.data.lens = 38
tgt = bpy.data.objects.new("Alvo", None); scene.collection.objects.link(tgt)
tgt.location = (0, -0.2, 0.55)
tr = cam.constraints.new('TRACK_TO'); tr.target = tgt
tr.track_axis = 'TRACK_NEGATIVE_Z'; tr.up_axis = 'UP_Y'
cam.data.dof.use_dof = True; cam.data.dof.focus_object = tgt; cam.data.dof.aperture_fstop = 2.8

scene.render.engine = 'CYCLES'
scene.cycles.samples = 64
scene.cycles.use_denoising = True
scene.cycles_curves.shape = 'THICK'
scene.cycles_curves.subdivisions = 2
scene.render.resolution_x = 900
scene.render.resolution_y = 1200
scene.view_settings.view_transform = 'AgX'
scene.view_settings.look = 'AgX - Medium High Contrast'
