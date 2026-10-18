🇷🇺 **Русская версия: [README.md](README.md)**

# Car Model in Blender

A procedural model of a car (a classic coupe) built with a Python script
(`bpy`) in Blender 5.2 — no manual modeling: the body is created by lofting
smoothed cross-sections, while wheels, lights and small details are assembled
from primitives.

![Car preview](car_preview.png)

## Contents

| File | Description |
|------|-------------|
| `car.blend` | Scene with the finished model, lighting and camera |
| `make_car.py` | Script that generates the model and renders it |
| `car_preview.png` | Preview render (EEVEE, 1280×720) |
| `game.js`, `index.html` | A small three.js game |

## Model Features

- Body lofted from 18 cross-sections with rounded edges: tapered nose,
  descending hood, flat beltline, sloping trunk
- Tinted glasshouse, raked A/C pillars, body-colored roof
- Wheels: tires with rounded shoulders, 5-spoke rims, brake discs
  and calipers
- Details: chrome grille, license plates, mirrors, door handles,
  panel gaps, spoiler, exhaust tips, glowing headlights and taillights
- Materials: metallic paint with clearcoat, tinted glass, chrome

## Rebuild

```bash
blender --background --python make_car.py
```

The script regenerates `car.blend` and `car_preview.png` from scratch.

## How to View

Open `car.blend` in Blender 5.x and press `F12` to render.

## Credits

This project (the model, the generator script, the render and the README)
was created by a **neural network** (the opencode AI assistant) at the
user's request.
