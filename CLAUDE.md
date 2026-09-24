# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

"Passeio do Lui" — a browser 3D game starring Lui, a Shih Tzu modeled in Blender from photos. Two loosely coupled halves:

- `blender/*.py` — Blender scripts that generate the dog (body, coat, eyes, nose, bow tie, fur, armature, animations) procedurally from scratch.
- `index.html` — the whole game: HUD, three.js scene, shell-fur shader, physics, and the animated model embedded as base64.

No build step, no package manager, no tests, no CI. Deployed via GitHub Pages (`main` / root) at ramirorudiger.github.io/jogo-do-lui.

## Conventions

Everything user-facing and in-code is **pt-BR**: UI strings, comments, Blender object/material/bone names (`Pele`, `Olho`, `Gravatinha`, `cabeca`, `orelha.L`), commit messages. Keep it that way — the three.js code matches on those exact Portuguese material names.

## Running and editing

Open `index.html` directly in a browser (`file://` works — the model is inline; only three.js and the Google font come over the network). Nothing to install.

**`index.html` is 6.2 MB but only ~840 lines** — one single ~6.15 MB line holds the base64 GLB. Never read or grep that line; the Read tool will choke on it. Find it and work around it:

```bash
N=$(grep -n 'lui-glb' index.html | cut -d: -f1)   # the GLB line (251 as of this writing)
sed -n "1,$((N-1))p" index.html                  # HTML, CSS, HUD, analytics
sed -n "$((N+1)),\$p" index.html                 # all game JS
```

Edits to the JS are safe with normal string-replace edits as long as the match isn't on the GLB line. `git diff` on this file is unusable — the GLB shows up as context; review with `sed` ranges instead.

### Regenerating the model in Blender

```bash
blender -b -P blender/lui_animado.py -- fios=150000   # rigged + animated (~2 min)
blender -b -P blender/lui_realista.py -- fios=260000  # portrait render scene
blender -b -P blender/lui_gerar_modelo.py -- --nohair # first stylized version
```

`fios=N` (hair strand count) and `--nohair` are parsed straight out of `sys.argv`, so they work with or without the `--` separator. Interactively: *Scripting* tab → Open → Run Script. The committed `.blend` files ship ~50k strands to stay under GitHub's upload limit; the scripts default to 150k–260k.

### Re-embedding the model into the game

The base64 is byte-identical to `blender/Lui_animado.glb`. To swap in a new model, replace that line with a `<script id="lui-glb" type="application/octet-stream">` tag wrapping the base64 of the new `.glb` (one line, no wrapping — the loader does `atob` on the tag's `textContent`).

**Important gap:** the committed scripts do *not* export the `.glb`, and they do *not* create the `_FURLEN` vertex attribute that the game's fur shader reads. That step was done outside these scripts. Re-exporting straight from `lui_animado.py` output yields a model whose fur silently disappears (every shell fragment gets discarded because `_furlen` reads as 0). If you regenerate the GLB, you must also author `_FURLEN` per vertex (the per-strand length field the script computes as `L`) before exporting.

## Architecture of the game (`index.html`)

Single IIFE, ~580 lines, plain globals — **no ES modules**. three.js **r147** from jsDelivr, using the legacy `examples/js/` global-script builds (`GLTFLoader.js`, `RoomEnvironment.js`). Those files were removed in r148 and the legacy color API used here (`outputEncoding`, `sRGBEncoding`) changed in r152. **Do not bump the three.js version without porting to modules + the new color management.**

Section order in the script, top to bottom: renderer → lights → room (procedural canvas textures for floor planks and pillow print) → ball → `furMaterial` → `irisTexture` → GLB load & material swap → Web Audio bark → `say()` → name card → input → movement/collision → `tick()` render loop.

### Shell fur

`furMaterial(shell)` returns a `MeshStandardMaterial` patched via `onBeforeCompile`. On load, the skinned mesh whose glTF material is named `Pele` gets the base shell (`shell = 0`), plus `FUR.layers` extra `SkinnedMesh` clones sharing the same geometry and skeleton (`s.bind(o.skeleton, o.bindMatrix)`), each with `shell = i / layers` and ascending `renderOrder`. The vertex shader extrudes along the normal by `_furlen * uLen * uShell` with a gravity droop; the fragment shader hashes model-space position into a strand grid and discards fragments outside the strand radius.

All shells share `customProgramCacheKey = () => "lui-fur"` so the program compiles once; per-shell variation rides on the `uShell` uniform held in `m.userData`.

Layer count: 22 desktop, 14 on coarse pointers, overridable with `?camadas=N` (capped at 40). This is the main perf dial.

### Materials by name

The GLB is one mesh with seven materials; the loader replaces each by name:

| glTF material | Becomes |
|---|---|
| `Pele` | shell fur (base + N layers) |
| `Olho` | `MeshPhysicalMaterial` + procedural canvas iris texture (`flipY = false` — glTF UVs arrive flipped) |
| `Cornea` | hidden (`visible = false`) — the clearcoat on `Olho` supplies the wet highlight instead |
| `Narina`, `Palpebra`, `Nariz` | flat/standard dark materials |
| `Gravatinha` | procedural polka-dot canvas texture |

Renaming a material in the Blender script silently breaks the corresponding branch here.

### Animation layering

The GLB carries three clips: `Andar`, `Parado`, `Latir`. Rather than additive blending, `prepareClip()` **partitions tracks by bone**: walk and idle drop the bark bones, bark keeps only them. So barking can play over walking without fighting for the same bones.

```js
const BARK = ["pescoco", "cabeca", "orelhaL", "orelhaR"];
```

Note `orelhaL`, not `orelha.L`: three.js `PropertyBinding` strips `.` from glTF node names. Bone names in the Blender armature use the dotted `.L`/`.R` suffix; the game must use the stripped form. All `scale` tracks are dropped too.

Walk and idle both `play()` permanently and are cross-faded every frame by `setEffectiveWeight(moving)` where `moving` is derived from speed and turn rate; `walk.timeScale` goes negative when reversing.

### Movement, camera, collision

Dog state is `{ heading, speed, turn }` with exponential smoothing toward targets; the mesh is a `THREE.Group` positioned on the floor plane, forward is `(sin h, 0, cos h)`. The room is a square of half-width `ROOM = 8`. Obstacles are AABBs pushed onto `obstacles` (sofa, bowl) and resolved by clamping to the nearest point on the box then pushing out to `DOG_R`. The ball is pushed from a point 0.75 ahead of the dog ("nose"), then integrates with exponential damping and bounces off walls and the same AABB list.

Camera is a smoothed chase rig (`camPos.lerp(want, 1 - pow(0.02, dt))`); `C` / the on-screen button flips `camFront`, which swings the orbit angle by ~π and lowers the height. The sun light follows the dog so the shadow map stays tight around him.

### Bark

`woof()` synthesizes each bark from scratch with Web Audio: a sawtooth with a pitch snap through two bandpass formants plus a short noise burst. `bark()` fires two `woof`s 0.25 s apart, rate-limited to one per 0.55 s, restarts the `Latir` action, and raises the bubble through `say()`. `ensureAudio()` is called on first key/touch to satisfy autoplay policies.

### HUD

Pure DOM/CSS over the canvas, theme-aware via `prefers-color-scheme` plus a `[data-theme]` override, `env(safe-area-inset-*)` for notches, and `@media (pointer: coarse)` to swap the keyboard hints for the on-screen d-pad and bark button. The collar-tag status line (`#status`) is driven from the loop by `setStatus()`.

### Speech bubble and the player's name

Everything that makes Lui talk goes through `say(texto, segundos, tipo)`, which sets the bubble text, starts `bubbleTimer`, and records `bubbleKind`. The loop re-anchors the bubble to the `cabeca` bone each frame via `posicionaBalao()` (clamped to the viewport so long lines don't run off-screen). `bubbleKind` matters: only `"latido"` makes the collar tag read "latindo", so greetings don't masquerade as barking.

On first load the `#ask` card asks for the player's name and stores it under the `lui.nome` localStorage key (also kept in the `jogador` variable, so `amar()` still works when storage is blocked); `receber()` runs when the GLB finishes and either greets a returning player (`Lui estava com saudade de X ❤️`) or opens the card. Names are trimmed and collapsed to a single space, capped at 20 chars, and an empty one is rejected. Every localStorage access is wrapped in try/catch — it throws on `file://` in Chrome and in some private modes, in which case the game just asks again next time.

Arrow keys move; letters are actions — `L` bark, `A` love (`amar()`, repeats the `Lui ❤️ X` greeting on demand, mirrored by the `#loveBtn` heart on touch), `C` camera. The WASD aliases were dropped when `A` was taken. While the card is open, `asking` is true and the keydown handler bails out early — without that, typing a name would fire bark, love and camera. Clear the stored name with `localStorage.removeItem('lui.nome')`.

Google Analytics (`G-SPBGJ3H1EZ`) is loaded between `</head>` and `<body>`.

## Blender scripts

All three follow the same pipeline and share most code (`lui_realista.py` is `lui_animado.py` minus the armature/animation tail). Editing one usually means editing the other:

1. Body from ~30 ellipsoids joined and voxel-remeshed into one volume.
2. `coat(p)` paints a `Pelagem` float-color vertex attribute by region (black eye mask, white blaze, cream beard, dark back, black tail) — this becomes `COLOR_0` in the GLB.
3. Eyes (globe + iris + cornea + eyelids), nose with nostrils, polka-dot bow tie as separate objects.
4. Fur: numpy-sampled root points over the mesh triangles, with per-region length `L` and comb direction `G`, clumped and exported as a Curves object. Region masks (`ears`, `beard`, `muzz`, `crown`, `legs`, `tail`) are plain boolean arrays over the root positions.
5. `lui_animado.py` only: a 16-bone armature (`quadril` → `peito` → `pescoco` → `cabeca`, plus ears/legs/tail) with automatic weights, the extras joined into the skin and pinned to a single bone each, a `PeloSegueAPele` geometry-nodes modifier (`DeformCurvesOnSurface`) so fur follows the skin, then `make_action()` bakes `Andar` (24 f), `Parado` (48 f) and `Latir` (14 f) from plain sine functions.

The scripts do not save `.blend` files either — the committed `.blend`s were saved by hand.
