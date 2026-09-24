"""Lui - Shih Tzu preto e branco com gravatinha amarela.
Rode no Blender: aba Scripting > Open > lui.py > Run Script
"""
import bpy, bmesh, math, sys
from mathutils import Vector

HAIR = "--nohair" not in sys.argv

# ---------- limpar cena ----------
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

def mat(name, color, rough=0.5, spec=0.5, emit=None):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    return m

# ---------- corpo: primitivas unidas por voxel remesh ----------
parts = []
def ell(co, r, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=co, segments=32, ring_count=16,
                                         rotation=tuple(math.radians(a) for a in rot))
    o = bpy.context.active_object; o.scale = r; parts.append(o); return o

# frente do cachorro = -Y, altura em metros "estilizados"
ell((0, 0.10, 0.42), (0.19, 0.36, 0.17))          # tronco
ell((0, -0.19, 0.43), (0.18, 0.16, 0.19))         # peito
ell((0, 0.30, 0.43), (0.18, 0.16, 0.16))          # garupa
ell((0, -0.28, 0.60), (0.13, 0.12, 0.15), (-25, 0, 0))  # pescoço
ell((0, -0.33, 0.80), (0.20, 0.19, 0.18))         # cabeça
ell((0, -0.31, 0.91), (0.17, 0.15, 0.08))         # topete
ell((0, -0.50, 0.745), (0.105, 0.085, 0.07))      # focinho
ell((0, -0.47, 0.63), (0.11, 0.08, 0.10))         # barba
for s in (-1, 1):
    ell((s*0.07, -0.50, 0.70), (0.075, 0.07, 0.075))              # bochechas/bigode
    ell((s*0.185, -0.30, 0.69), (0.055, 0.08, 0.16), (0, s*-10, 0))  # orelhas
    ell((s*0.10, -0.20, 0.17), (0.065, 0.065, 0.18))              # pata dianteira
    ell((s*0.10, -0.235, 0.035), (0.07, 0.09, 0.045))             # pé dianteiro
    ell((s*0.11, 0.32, 0.32), (0.09, 0.13, 0.13))                 # coxa
    ell((s*0.11, 0.37, 0.15), (0.062, 0.062, 0.15))               # pata traseira
    ell((s*0.11, 0.345, 0.035), (0.07, 0.09, 0.045))              # pé traseiro
# rabo em pluma enrolado sobre as costas
N = 14
for i in range(N):
    t = i / (N - 1)
    a = math.radians(-60 + 230 * t)
    y = 0.40 + 0.13 * math.cos(a) - 0.10 * t
    z = 0.62 + 0.13 * math.sin(a)
    r = 0.075 - 0.02 * t
    ell((0.04 * t, y, z), (r, r, r))

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

# ---------- pintura da pelagem (atributo de cor) ----------
WHITE = (0.93, 0.92, 0.88)
CREAM = (0.80, 0.74, 0.62)
BLACK = (0.006, 0.006, 0.007)
GREY  = (0.035, 0.035, 0.038)

def lerp(a, b, t): return tuple(a[i] + (b[i]-a[i])*t for i in range(3))
def smooth(e0, e1, x):
    t = max(0.0, min(1.0, (x - e0) / (e1 - e0))); return t*t*(3-2*t)

def coat(p):
    x, y, z = p
    ax = abs(x)
    # rabo
    if y > 0.28 and z > 0.56:
        return BLACK
    # orelhas
    if ax > 0.145 and -0.42 < y < -0.17 and 0.5 < z < 0.9:
        return BLACK
    # barba e boca
    if y < -0.40 and z < 0.69:
        return lerp(CREAM, WHITE, 0.55)
    # cabeça: máscara preta, listra branca fina, topo branco
    if z > 0.64 and y < -0.17:
        col = BLACK
        blaze = smooth(0.035, 0.018, ax) * smooth(0.79, 0.82, z)
        brows = smooth(0.10, 0.06, ax) * smooth(0.89, 0.92, z)
        crown = smooth(0.95, 0.985, z) * smooth(0.19, 0.12, ax)
        col = lerp(col, WHITE, max(blaze, brows, crown))
        muz = smooth(-0.49, -0.52, y) * smooth(0.765, 0.74, z)
        col = lerp(col, lerp(CREAM, WHITE, 0.4), muz)
        col = lerp(col, lerp(CREAM, WHITE, 0.55), smooth(0.70, 0.66, z) * smooth(-0.36, -0.42, y))
        return col
    # nuca preta que desce do pescoço
    nape = smooth(0.54, 0.60, z) * smooth(-0.08, -0.16, y) * smooth(-0.40, -0.32, y) \
         * smooth(-0.30, -0.22, y + 0.0 * ax)
    back = smooth(0.46, 0.53, z) * smooth(-0.22, -0.10, y)
    col = lerp(WHITE, GREY, back)
    return lerp(col, BLACK, nape)

me = lui.data
attr = me.color_attributes.new("Pelagem", 'FLOAT_COLOR', 'POINT')
for v in me.vertices:
    c = coat(v.co)
    attr.data[v.index].color = (*c, 1.0)
me.color_attributes.active_color = attr

# UV simples (o pelo lê a cor pelo atributo)
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(island_margin=0.01)
bpy.ops.object.mode_set(mode='OBJECT')

# material da pele
skin = bpy.data.materials.new("Pelagem"); skin.use_nodes = True
nt = skin.node_tree; bsdf = nt.nodes["Principled BSDF"]
ca = nt.nodes.new("ShaderNodeVertexColor"); ca.layer_name = "Pelagem"
nt.links.new(ca.outputs["Color"], bsdf.inputs["Base Color"])
bsdf.inputs["Roughness"].default_value = 0.9
lui.data.materials.append(skin)

# assa as cores num mapa de textura (o pelo lê a cor pela UV do corpo)
img = bpy.data.images.new("Lui_Pelagem", 1024, 1024)
tex = nt.nodes.new("ShaderNodeTexImage"); tex.image = img
nt.nodes.active = tex
scene.render.engine = 'CYCLES'; scene.cycles.samples = 1
scene.render.bake.margin = 8
bpy.ops.object.select_all(action='DESELECT'); lui.select_set(True)
bpy.context.view_layer.objects.active = lui
bpy.ops.object.bake(type='DIFFUSE', pass_filter={'COLOR'})
img.pack()

# ---------- pelo ----------
# grupos de vértices controlam onde o pelo é mais longo / mais denso
vg_len = lui.vertex_groups.new(name="PeloComprimento")
vg_den = lui.vertex_groups.new(name="PeloDensidade")
eyes_c = [Vector((s*0.083, -0.478, 0.835)) for s in (-1, 1)]
nose_c = Vector((0, -0.582, 0.772))
for v in me.vertices:
    x, y, z = v.co; ax = abs(x)
    L = 0.3
    if z > 0.64 and y < -0.17: L = 0.55                       # cabeça
    if ax > 0.145 and -0.42 < y < -0.17 and 0.5 < z < 0.9: L = 1.0   # orelhas
    if y < -0.40 and z < 0.76: L = 0.8                        # barba/bigode
    if z > 0.95: L = 0.8                                       # topete
    if y > 0.28 and z > 0.56: L = 1.0                          # rabo
    if z < 0.08: L = 0.25                                      # pés
    vg_len.add([v.index], L, 'REPLACE')
    d = min(min((v.co - e).length for e in eyes_c) - 0.045, (v.co - nose_c).length - 0.035)
    vg_den.add([v.index], smooth(0.0, 0.03, d), 'REPLACE')

if HAIR:
    ps_mod = lui.modifiers.new("Pelo", 'PARTICLE_SYSTEM')
    ps = ps_mod.particle_system.settings
    ps.type = 'HAIR'
    ps.count = 9000
    ps.hair_length = 0.05
    ps_mod.particle_system.vertex_group_length = "PeloComprimento"
    ps_mod.particle_system.vertex_group_density = "PeloDensidade"
    ps.use_advanced_hair = True
    ps.child_type = 'INTERPOLATED'
    ps.child_percent = 10
    ps.rendered_child_count = 12
    ps.clump_factor = 0.4
    ps.roughness_2 = 0.02
    ps.roughness_endpoint = 0.02
    ps.factor_random = 0.01
    ps.hair_length = 0.05
    ps.use_hair_bspline = True
    ps.display_step = 3; ps.render_step = 4
    ps.root_radius = 0.6
    ps.radius_scale = 0.005
    ps.effector_weights.gravity = 1.0
    # material do pelo usa a cor da pele (Cycles interpola do emissor)
    hm = bpy.data.materials.new("PeloMat"); hm.use_nodes = True
    hn = hm.node_tree; hn.nodes.remove(hn.nodes["Principled BSDF"])
    hb = hn.nodes.new("ShaderNodeBsdfHairPrincipled")
    hb.parametrization = 'COLOR'
    hc = hn.nodes.new("ShaderNodeTexImage"); hc.image = img
    huv = hn.nodes.new("ShaderNodeTexCoord")
    hn.links.new(huv.outputs["UV"], hc.inputs["Vector"])
    hn.links.new(hc.outputs["Color"], hb.inputs["Color"])
    hb.inputs["Roughness"].default_value = 0.4
    hn.links.new(hb.outputs[0], hn.nodes["Material Output"].inputs["Surface"])
    lui.data.materials.append(hm)
    ps.material = 2

# ---------- olhos ----------
eye_m = mat("Olho", (0.006, 0.004, 0.003), rough=0.03)
for s in (-1, 1):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.043, location=(s*0.083, -0.478, 0.835),
                                         segments=32, ring_count=16)
    e = bpy.context.active_object; e.name = f"Olho_{'E' if s<0 else 'D'}"
    e.scale = (1, 0.8, 1); bpy.ops.object.shade_smooth()
    e.data.materials.append(eye_m)
    e.parent = lui

# ---------- nariz ----------
nose_m = mat("Nariz", (0.01, 0.01, 0.01), rough=0.35)
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.03, location=(0, -0.582, 0.772))
n = bpy.context.active_object; n.name = "Nariz"; n.scale = (1.25, 0.8, 0.85)
bpy.ops.object.shade_smooth(); n.data.materials.append(nose_m); n.parent = lui

# ---------- gravatinha amarela de bolinhas ----------
bow_m = bpy.data.materials.new("Gravatinha"); bow_m.use_nodes = True
bn = bow_m.node_tree; bb = bn.nodes["Principled BSDF"]
bb.inputs["Roughness"].default_value = 0.45
tc = bn.nodes.new("ShaderNodeTexCoord")
vor = bn.nodes.new("ShaderNodeTexVoronoi"); vor.inputs["Scale"].default_value = 18
vor.feature = 'F1'; vor.inputs["Randomness"].default_value = 0.6
bn.links.new(tc.outputs["Object"], vor.inputs["Vector"])
dot = bn.nodes.new("ShaderNodeMath"); dot.operation = 'LESS_THAN'
dot.inputs[1].default_value = 0.3
bn.links.new(vor.outputs["Distance"], dot.inputs[0])
ramp = bn.nodes.new("ShaderNodeValToRGB")   # cores aleatórias das bolinhas
el = ramp.color_ramp.elements
el[0].color = (0.85, 0.05, 0.05, 1); el[1].color = (0.05, 0.25, 0.8, 1)
e2 = el.new(0.33); e2.color = (0.1, 0.55, 0.15, 1)
e3 = el.new(0.66); e3.color = (0.35, 0.1, 0.5, 1)
ramp.color_ramp.interpolation = 'CONSTANT'
bn.links.new(vor.outputs["Color"], ramp.inputs["Fac"])
mix = bn.nodes.new("ShaderNodeMix"); mix.data_type = 'RGBA'
mix.inputs["A"].default_value = (1.0, 0.45, 0.0, 1)
bn.links.new(dot.outputs[0], mix.inputs["Factor"])
bn.links.new(ramp.outputs["Color"], mix.inputs["B"])
bn.links.new(mix.outputs["Result"], bb.inputs["Base Color"])

bow_parts = []
for s in (-1, 1):   # laços
    bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=0.055, depth=0.1,
                                    location=(s*0.055, -0.425, 0.53), rotation=(0, math.radians(90*s), 0))
    bow_parts.append(bpy.context.active_object)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(s*0.028, -0.43, 0.45),
                                    rotation=(0, math.radians(-10*s), 0))
    t = bpy.context.active_object; t.scale = (0.035, 0.012, 0.1); bow_parts.append(t)  # pontas
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.022, location=(0, -0.437, 0.53))
bow_parts.append(bpy.context.active_object)
for o in bow_parts:
    o.select_set(True)
bpy.context.view_layer.objects.active = bow_parts[0]
bpy.ops.object.select_all(action='DESELECT')
for o in bow_parts: o.select_set(True)
bpy.ops.object.join()
bow = bpy.context.active_object; bow.name = "Gravatinha"
bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
bow.scale = (1.35, 0.45, 1.35)
bow.location.y -= 0.075; bow.location.z += 0.02
bow.rotation_euler.x = math.radians(-12)
bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
bev = bow.modifiers.new("Bevel", 'BEVEL'); bev.width = 0.006; bev.segments = 3
bow.data.materials.append(bow_m); bow.parent = lui

# ---------- chão de madeira, luz, câmera ----------
bpy.ops.mesh.primitive_plane_add(size=60, location=(0, 0, 0))
floor = bpy.context.active_object; floor.name = "Piso"
fm = bpy.data.materials.new("Piso"); fm.use_nodes = True
fn = fm.node_tree; fb = fn.nodes["Principled BSDF"]
wave = fn.nodes.new("ShaderNodeTexWave"); wave.inputs["Scale"].default_value = 0.6
wave.inputs["Distortion"].default_value = 6; wave.inputs["Detail"].default_value = 4
wr = fn.nodes.new("ShaderNodeValToRGB")
wr.color_ramp.elements[0].color = (0.33, 0.25, 0.18, 1)
wr.color_ramp.elements[1].color = (0.55, 0.45, 0.35, 1)
fn.links.new(wave.outputs["Fac"], wr.inputs["Fac"])
fn.links.new(wr.outputs["Color"], fb.inputs["Base Color"])
fb.inputs["Roughness"].default_value = 0.55
floor.data.materials.append(fm)

world = bpy.data.worlds.new("Mundo"); scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.8, 0.82, 0.85, 1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.6

bpy.ops.object.light_add(type='AREA', location=(1.2, -1.8, 2.4))
key = bpy.context.active_object; key.data.energy = 250; key.data.size = 2
key.rotation_euler = (math.radians(45), 0, math.radians(35))
bpy.ops.object.light_add(type='AREA', location=(-1.6, -0.8, 1.2))
fill = bpy.context.active_object; fill.data.energy = 80; fill.data.size = 2
fill.rotation_euler = (math.radians(70), 0, math.radians(-60))

bpy.ops.object.camera_add(location=(0.6, -1.9, 1.25))
cam = bpy.context.active_object; scene.camera = cam
cam.data.lens = 55
tgt = bpy.data.objects.new("Alvo", None); scene.collection.objects.link(tgt)
tgt.location = (0, -0.05, 0.45)
tr = cam.constraints.new('TRACK_TO'); tr.target = tgt
tr.track_axis = 'TRACK_NEGATIVE_Z'; tr.up_axis = 'UP_Y'

scene.render.engine = 'CYCLES'
scene.cycles.samples = 48
scene.cycles.use_denoising = True
scene.render.resolution_x = 900
scene.render.resolution_y = 1000
scene.view_settings.view_transform = 'AgX'
scene.view_settings.look = 'AgX - Punchy'
