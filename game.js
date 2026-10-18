import * as THREE from 'three';

const app = document.getElementById('app');
const overlay = document.getElementById('overlay');
const startBtn = document.getElementById('startBtn');
const kmhEl = document.getElementById('kmh');
const distEl = document.getElementById('dist');
const bestEl = document.getElementById('best');
const flashEl = document.getElementById('flash');

const TILE = 20;
const ROAD_HALF = 7;
const LANE_ONCOMING = [-5.25, -1.75];
const LANE_SAME = [1.75, 5.25];
const MAX_SPEED = 55;
const BEST_KEY = 'cockpitRacerBest';

let best = Number(localStorage.getItem(BEST_KEY) || 0);
bestEl.textContent = `Рекорд: ${Math.floor(best)} м`;

const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
app.appendChild(renderer.domElement);

const scene = new THREE.Scene();
scene.fog = new THREE.FogExp2(0xe8b487, 0.0075);

const camera = new THREE.PerspectiveCamera(66, window.innerWidth / window.innerHeight, 0.05, 1200);
scene.add(camera);

const hemi = new THREE.HemisphereLight(0xffd9a6, 0x3d4a2e, 0.65);
scene.add(hemi);

const sun = new THREE.DirectionalLight(0xffe2b4, 1.35);
scene.add(sun);
scene.add(sun.target);

const skyGeo = new THREE.SphereGeometry(900, 32, 16);
const skyMat = new THREE.ShaderMaterial({
  side: THREE.BackSide,
  depthWrite: false,
  uniforms: {
    top: { value: new THREE.Color(0x274b86) },
    mid: { value: new THREE.Color(0x8fb4d6) },
    bottom: { value: new THREE.Color(0xffc98a) },
  },
  vertexShader: `varying vec3 vPos; void main(){ vPos = position; gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }`,
  fragmentShader: `varying vec3 vPos; uniform vec3 top; uniform vec3 mid; uniform vec3 bottom;
    void main(){
      float h = normalize(vPos).y;
      vec3 c = h > 0.15 ? mix(mid, top, smoothstep(0.15, 0.75, h)) : mix(bottom, mid, smoothstep(-0.1, 0.15, h));
      gl_FragColor = vec4(c, 1.0);
    }`,
});
const sky = new THREE.Mesh(skyGeo, skyMat);
sky.frustumCulled = false;
scene.add(sky);

function canvasTexture(w, h, draw, repX = 1, repY = 1) {
  const c = document.createElement('canvas');
  c.width = w; c.height = h;
  draw(c.getContext('2d'), w, h);
  const t = new THREE.CanvasTexture(c);
  t.wrapS = t.wrapT = THREE.RepeatWrapping;
  t.repeat.set(repX, repY);
  t.anisotropy = renderer.capabilities.getMaxAnisotropy();
  return t;
}

const roadTex = canvasTexture(512, 1024, (g, w, h) => {
  g.fillStyle = '#3a3b40';
  g.fillRect(0, 0, w, h);
  for (let i = 0; i < 6000; i++) {
    const v = 45 + Math.random() * 30;
    g.fillStyle = `rgba(${v},${v},${v + 6},0.5)`;
    g.fillRect(Math.random() * w, Math.random() * h, 2, 2);
  }
  const m = w / 14;
  g.fillStyle = '#e9e6dc';
  g.fillRect(4, 0, 10, h);
  g.fillRect(w - 14, 0, 10, h);
  g.fillStyle = '#e6c445';
  g.fillRect(w / 2 - 11, 0, 7, h);
  g.fillRect(w / 2 + 4, 0, 7, h);
  g.fillStyle = '#e9e6dc';
  for (const lx of [w / 2 - 3.5 * m, w / 2 + 3.5 * m]) {
    for (let y = 0; y < h; y += 80) g.fillRect(lx - 5, y, 10, 46);
  }
}, 1, 25);

const grassTex = canvasTexture(256, 256, (g, w, h) => {
  g.fillStyle = '#5a7a3a';
  g.fillRect(0, 0, w, h);
  for (let i = 0; i < 2600; i++) {
    const s = Math.random();
    g.fillStyle = s > 0.5 ? 'rgba(96,132,58,0.7)' : 'rgba(70,100,44,0.7)';
    g.fillRect(Math.random() * w, Math.random() * h, 3, 3);
  }
}, 60, 80);

const road = new THREE.Mesh(
  new THREE.PlaneGeometry(14, 500),
  new THREE.MeshStandardMaterial({ map: roadTex, roughness: 0.92 })
);
road.rotation.x = -Math.PI / 2;
scene.add(road);

const grass = new THREE.Mesh(
  new THREE.PlaneGeometry(800, 1000),
  new THREE.MeshStandardMaterial({ map: grassTex, roughness: 1 })
);
grass.rotation.x = -Math.PI / 2;
scene.add(grass);

const shoulderMat = new THREE.MeshStandardMaterial({ color: 0x8a8375, roughness: 1 });
const shoulderL = new THREE.Mesh(new THREE.BoxGeometry(2.4, 0.06, 500), shoulderMat);
const shoulderR = shoulderL.clone();
scene.add(shoulderL, shoulderR);

const railMat = new THREE.MeshStandardMaterial({ color: 0xb8bcc2, roughness: 0.5, metalness: 0.25 });
const railL = new THREE.Mesh(new THREE.BoxGeometry(0.1, 0.22, 500), railMat);
const railR = railL.clone();
railL.position.y = 0.62;
railR.position.y = 0.62;
scene.add(railL, railR);

function blobShadow(w, l) {
  const tex = canvasTexture(128, 128, (g) => {
    const grd = g.createRadialGradient(64, 64, 6, 64, 64, 62);
    grd.addColorStop(0, 'rgba(0,0,0,0.55)');
    grd.addColorStop(1, 'rgba(0,0,0,0)');
    g.fillStyle = grd;
    g.fillRect(0, 0, 128, 128);
  });
  const m = new THREE.Mesh(
    new THREE.PlaneGeometry(w, l),
    new THREE.MeshBasicMaterial({ map: tex, transparent: true, depthWrite: false })
  );
  m.rotation.x = -Math.PI / 2;
  m.position.y = 0.03;
  return m;
}

const treeTrunkGeo = new THREE.CylinderGeometry(0.18, 0.28, 2.2, 6);
const treeTopGeo = new THREE.ConeGeometry(1.7, 4.6, 7);
const trunkMat = new THREE.MeshStandardMaterial({ color: 0x5c432c, roughness: 1 });
const topMat = new THREE.MeshStandardMaterial({ color: 0x3f6b35, roughness: 1 });
const poleMat = new THREE.MeshStandardMaterial({ color: 0x9aa0a6, roughness: 0.6, metalness: 0.4 });
const lampMat = new THREE.MeshStandardMaterial({ color: 0xfff2cc, emissive: 0xffdd88, emissiveIntensity: 1.4 });

const scenery = [];
function makeTree(x, z) {
  const g = new THREE.Group();
  const trunk = new THREE.Mesh(treeTrunkGeo, trunkMat);
  trunk.position.y = 1.1;
  const top = new THREE.Mesh(treeTopGeo, topMat);
  top.position.y = 3.8;
  g.add(trunk, top);
  const s = 0.7 + Math.random() * 1.1;
  g.scale.setScalar(s);
  g.position.set(x, 0, z);
  scene.add(g);
  scenery.push(g);
  return g;
}
function makePole(x, z) {
  const g = new THREE.Group();
  const pole = new THREE.Mesh(new THREE.CylinderGeometry(0.09, 0.12, 7, 6), poleMat);
  pole.position.y = 3.5;
  const arm = new THREE.Mesh(new THREE.BoxGeometry(1.6, 0.09, 0.09), poleMat);
  arm.position.set(x > 0 ? -0.8 : 0.8, 6.9, 0);
  const lamp = new THREE.Mesh(new THREE.BoxGeometry(0.5, 0.16, 0.28), lampMat);
  lamp.position.set(x > 0 ? -1.5 : 1.5, 6.8, 0);
  g.add(pole, arm, lamp);
  g.position.set(x, 0, z);
  scene.add(g);
  scenery.push(g);
  return g;
}
for (let i = 0; i < 46; i++) {
  const side = Math.random() > 0.5 ? 1 : -1;
  makeTree(side * (11 + Math.random() * 26), 40 - i * 10 - Math.random() * 6);
}
for (let i = 0; i < 10; i++) {
  const side = i % 2 === 0 ? 1 : -1;
  makePole(side * 9.4, 30 - i * 44);
}

const carBodyGeo = new THREE.BoxGeometry(1.9, 0.55, 4.4);
const carCabinGeo = new THREE.BoxGeometry(1.72, 0.52, 2.1);
const wheelGeo = new THREE.CylinderGeometry(0.36, 0.36, 0.26, 12);
const headGeo = new THREE.BoxGeometry(0.34, 0.14, 0.08);
const tailGeo = new THREE.BoxGeometry(0.34, 0.13, 0.08);
const wheelMat = new THREE.MeshStandardMaterial({ color: 0x15151a, roughness: 0.9 });
const glassMat = new THREE.MeshStandardMaterial({ color: 0x2b4459, roughness: 0.2, metalness: 0.1 });
const headMat = new THREE.MeshStandardMaterial({ color: 0xfff8de, emissive: 0xfff2c0, emissiveIntensity: 2.2 });
const tailMat = new THREE.MeshStandardMaterial({ color: 0xff3222, emissive: 0xff2010, emissiveIntensity: 1.6 });
const darkMat = new THREE.MeshStandardMaterial({ color: 0x1a1a1e, roughness: 0.8 });

const CAR_COLORS = [0xd23b32, 0x2f6fd2, 0xe8e8ea, 0x2c2f36, 0xd8b13a, 0x3fa564, 0x8a49c7, 0xdd7b2a, 0x77808c];

function makeTrafficCar() {
  const g = new THREE.Group();
  const color = CAR_COLORS[Math.floor(Math.random() * CAR_COLORS.length)];
  const body = new THREE.Mesh(carBodyGeo, new THREE.MeshStandardMaterial({ color, roughness: 0.4, metalness: 0.15 }));
  body.position.y = 0.58;
  const cabin = new THREE.Mesh(carCabinGeo, glassMat);
  cabin.position.set(0, 1.08, 0.25);
  g.add(body, cabin);
  for (const [x, z] of [[-0.95, -1.4], [0.95, -1.4], [-0.95, 1.4], [0.95, 1.4]]) {
    const w = new THREE.Mesh(wheelGeo, wheelMat);
    w.rotation.z = Math.PI / 2;
    w.position.set(x, 0.36, z);
    g.add(w);
  }
  for (const x of [-0.6, 0.6]) {
    const hl = new THREE.Mesh(headGeo, headMat);
    hl.position.set(x, 0.62, -2.22);
    const tl = new THREE.Mesh(tailGeo, tailMat);
    tl.position.set(x, 0.66, 2.22);
    g.add(hl, tl);
  }
  const bump = new THREE.Mesh(new THREE.BoxGeometry(1.94, 0.2, 0.14), darkMat);
  bump.position.set(0, 0.36, 2.26);
  g.add(bump);
  g.add(blobShadow(3.2, 5.6));
  scene.add(g);
  return g;
}

const traffic = [];
for (let i = 0; i < 14; i++) {
  traffic.push({
    mesh: makeTrafficCar(),
    dir: 1,
    speed: 20,
    lane: LANE_SAME[0],
    active: false,
  });
}
window.__traffic = traffic;

function respawnCar(car, playerZ) {
  const oncoming = Math.random() < 0.45;
  car.dir = oncoming ? -1 : 1;
  car.lane = oncoming
    ? LANE_ONCOMING[Math.floor(Math.random() * LANE_ONCOMING.length)]
    : LANE_SAME[Math.floor(Math.random() * LANE_SAME.length)];
  car.speed = oncoming ? 16 + Math.random() * 14 : 13 + Math.random() * 14;
  let z = playerZ - (150 + Math.random() * 220);
  for (const other of traffic) {
    if (other !== car && other.active && other.lane === car.lane && Math.abs(other.mesh.position.z - z) < 40) {
      z -= 45;
    }
  }
  car.mesh.position.set(car.lane, 0, z);
  car.mesh.rotation.y = oncoming ? Math.PI : 0;
  car.active = true;
}

function makeCockpit() {
  const g = new THREE.Group();
  const paint = new THREE.MeshStandardMaterial({ color: 0xc4322a, roughness: 0.4, metalness: 0.15 });
  const interior = new THREE.MeshStandardMaterial({ color: 0x23252b, roughness: 0.85 });
  const plastic = new THREE.MeshStandardMaterial({ color: 0x14151a, roughness: 0.7 });

  const hood = new THREE.Mesh(new THREE.BoxGeometry(2.04, 0.14, 2.4), paint);
  hood.position.set(0, -0.62, -2.3);
  hood.rotation.x = 0.045;
  g.add(hood);

  const hoodCurve = new THREE.Mesh(new THREE.BoxGeometry(2.04, 0.3, 0.4), paint);
  hoodCurve.position.set(0, -0.72, -3.4);
  g.add(hoodCurve);

  const dash = new THREE.Mesh(new THREE.BoxGeometry(1.78, 0.34, 0.55), interior);
  dash.position.set(0, -0.44, -0.68);
  dash.rotation.x = -0.12;
  g.add(dash);

  const dashTop = new THREE.Mesh(new THREE.BoxGeometry(1.78, 0.06, 0.62), plastic);
  dashTop.position.set(0, -0.27, -0.7);
  dashTop.rotation.x = -0.12;
  g.add(dashTop);

  const cluster = new THREE.Mesh(new THREE.BoxGeometry(0.46, 0.16, 0.05), plastic);
  cluster.position.set(-0.38, -0.3, -0.56);
  g.add(cluster);
  const screen = new THREE.Mesh(
    new THREE.PlaneGeometry(0.38, 0.1),
    new THREE.MeshBasicMaterial({ color: 0x7fe3ff })
  );
  screen.position.set(-0.38, -0.3, -0.528);
  g.add(screen);

  const wheelGroup = new THREE.Group();
  wheelGroup.position.set(-0.38, -0.34, -0.52);
  wheelGroup.rotation.x = -0.42;
  const rim = new THREE.Mesh(new THREE.TorusGeometry(0.19, 0.026, 10, 36), plastic);
  wheelGroup.add(rim);
  for (const a of [0, Math.PI / 2 + 0.35, -Math.PI / 2 - 0.35]) {
    const spoke = new THREE.Mesh(new THREE.BoxGeometry(0.17, 0.03, 0.02), plastic);
    spoke.position.set(Math.cos(a) * 0.09, Math.sin(a) * 0.09, 0);
    spoke.rotation.z = a;
    wheelGroup.add(spoke);
  }
  const hub = new THREE.Mesh(new THREE.CylinderGeometry(0.05, 0.05, 0.04, 12), interior);
  hub.rotation.x = Math.PI / 2;
  wheelGroup.add(hub);
  g.add(wheelGroup);

  const pillarGeo = new THREE.BoxGeometry(0.1, 0.1, 1.5);
  const pillarL = new THREE.Mesh(pillarGeo, interior);
  pillarL.position.set(-0.86, 0.22, -0.75);
  pillarL.rotation.x = 0.55;
  pillarL.rotation.z = -0.12;
  const pillarR = pillarL.clone();
  pillarR.position.x = 0.86;
  pillarR.rotation.z = 0.12;
  g.add(pillarL, pillarR);

  const roof = new THREE.Mesh(new THREE.BoxGeometry(1.9, 0.09, 1.5), interior);
  roof.position.set(0, 0.62, -0.1);
  g.add(roof);

  const visor = new THREE.Mesh(new THREE.BoxGeometry(0.8, 0.03, 0.34), interior);
  visor.position.set(-0.4, 0.56, -0.72);
  visor.rotation.x = 0.5;
  g.add(visor);

  const doorGeo = new THREE.BoxGeometry(0.1, 0.72, 2.0);
  const doorL = new THREE.Mesh(doorGeo, interior);
  doorL.position.set(-0.92, -0.28, 0.1);
  const doorR = doorL.clone();
  doorR.position.x = 0.92;
  g.add(doorL, doorR);

  const mirror = new THREE.Mesh(new THREE.BoxGeometry(0.36, 0.1, 0.05), plastic);
  mirror.position.set(0.15, 0.42, -0.68);
  g.add(mirror);
  const mirrorGlass = new THREE.Mesh(
    new THREE.PlaneGeometry(0.32, 0.07),
    new THREE.MeshBasicMaterial({ color: 0x46586b })
  );
  mirrorGlass.position.set(0.15, 0.42, -0.652);
  mirrorGlass.rotation.y = Math.PI;
  g.add(mirrorGlass);

  const cowl = new THREE.Mesh(new THREE.BoxGeometry(1.86, 0.1, 0.3), paint);
  cowl.position.set(0, -0.56, -1.05);
  g.add(cowl);

  return { group: g, wheel: wheelGroup };
}

const cockpit = makeCockpit();
camera.add(cockpit.group);

const playerShadow = blobShadow(3.4, 5.8);
scene.add(playerShadow);

let audio = null;
function initAudio() {
  if (audio) return;
  const ctx = new (window.AudioContext || window.webkitAudioContext)();
  const osc = ctx.createOscillator();
  osc.type = 'sawtooth';
  const osc2 = ctx.createOscillator();
  osc2.type = 'square';
  osc2.detune.value = -1200;
  const lp = ctx.createBiquadFilter();
  lp.type = 'lowpass';
  lp.frequency.value = 600;
  const gain = ctx.createGain();
  gain.gain.value = 0;
  osc.connect(lp);
  osc2.connect(lp);
  lp.connect(gain);
  gain.connect(ctx.destination);
  osc.start();
  osc2.start();
  audio = { ctx, osc, osc2, lp, gain };
}

function crashSound() {
  if (!audio) return;
  const { ctx } = audio;
  const len = ctx.sampleRate * 0.6;
  const buf = ctx.createBuffer(1, len, ctx.sampleRate);
  const data = buf.getChannelData(0);
  for (let i = 0; i < len; i++) data[i] = (Math.random() * 2 - 1) * (1 - i / len) ** 2;
  const src = ctx.createBufferSource();
  src.buffer = buf;
  const bp = ctx.createBiquadFilter();
  bp.type = 'lowpass';
  bp.frequency.setValueAtTime(2500, ctx.currentTime);
  bp.frequency.exponentialRampToValueAtTime(120, ctx.currentTime + 0.5);
  const g = ctx.createGain();
  g.gain.setValueAtTime(0.7, ctx.currentTime);
  g.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.6);
  src.connect(bp).connect(g).connect(ctx.destination);
  src.start();
}

const input = { left: false, right: false, gas: false, brake: false };

const state = {
  mode: 'menu',
  x: 1.75,
  z: 0,
  heading: 0,
  speed: 0,
  steer: 0,
  dist: 0,
  shake: 0,
  offroad: false,
};

window.__state = state;

function resetGame() {
  state.mode = 'playing';
  state.x = 1.75;
  state.z = 0;
  state.heading = 0;
  state.speed = 14;
  state.steer = 0;
  state.dist = 0;
  state.shake = 0;
  for (const car of traffic) {
    car.active = false;
    respawnCar(car, 0);
  }
  for (const car of traffic) if (car.mesh.position.z > 40) respawnCar(car, 0);
  overlay.classList.add('hidden');
}

startBtn.addEventListener('click', () => {
  initAudio();
  audio.ctx.resume();
  resetGame();
});

window.addEventListener('keydown', (e) => {
  if (e.code === 'ArrowLeft' || e.code === 'KeyA') input.left = true;
  if (e.code === 'ArrowRight' || e.code === 'KeyD') input.right = true;
  if (e.code === 'ArrowUp' || e.code === 'KeyW') input.gas = true;
  if (e.code === 'ArrowDown' || e.code === 'KeyS') input.brake = true;
  if (e.code === 'Enter' || e.code === 'KeyR') {
    if (state.mode !== 'playing') {
      initAudio();
      audio.ctx.resume();
      resetGame();
    }
  }
  if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'Space'].includes(e.code)) e.preventDefault();
});
window.addEventListener('keyup', (e) => {
  if (e.code === 'ArrowLeft' || e.code === 'KeyA') input.left = false;
  if (e.code === 'ArrowRight' || e.code === 'KeyD') input.right = false;
  if (e.code === 'ArrowUp' || e.code === 'KeyW') input.gas = false;
  if (e.code === 'ArrowDown' || e.code === 'KeyS') input.brake = false;
});

function gameOver() {
  state.mode = 'over';
  state.shake = 1;
  crashSound();
  if (audio) audio.gain.gain.setTargetAtTime(0, audio.ctx.currentTime, 0.05);
  flashEl.style.transition = 'none';
  flashEl.style.opacity = '0.75';
  requestAnimationFrame(() => {
    flashEl.style.transition = 'opacity 0.7s ease';
    flashEl.style.opacity = '0';
  });
  if (state.dist > best) {
    best = state.dist;
    localStorage.setItem(BEST_KEY, String(best));
  }
  bestEl.textContent = `Рекорд: ${Math.floor(best)} м`;
  overlay.querySelector('h1').innerHTML = 'АВАРИЯ<span>!</span>';
  overlay.querySelector('p').innerHTML =
    `Вы проехали <b>${Math.floor(state.dist)} м</b> и развели <b>${Math.round(state.speed * 3.6)} км/ч</b>.<br>Рекорд: ${Math.floor(best)} м.`;
  startBtn.textContent = 'Ещё раз';
  overlay.classList.remove('hidden');
}

function update(dt, t) {
  const playing = state.mode === 'playing';

  if (playing) {
    const steerTarget = (input.left ? 1 : 0) + (input.right ? -1 : 0);
    state.steer += (steerTarget - state.steer) * Math.min(1, 10 * dt);

    if (input.gas) state.speed += 15 * dt;
    else if (input.brake) state.speed -= 32 * dt;
    else state.speed -= 3.5 * dt;

    state.offroad = Math.abs(state.x) > ROAD_HALF + 0.4;
    if (state.offroad) state.speed -= 16 * dt;
    state.speed = Math.max(0, Math.min(MAX_SPEED, state.speed));

    const grip = Math.min(1, state.speed / 8);
    state.heading += state.steer * 0.85 * grip * dt;
    state.heading *= 1 - Math.min(1, 1.6 * dt * (1 - Math.abs(state.steer)));
    state.heading = THREE.MathUtils.clamp(state.heading, -0.5, 0.5);

    const fx = -Math.sin(state.heading);
    const fz = -Math.cos(state.heading);
    state.x += fx * state.speed * dt;
    state.z += fz * state.speed * dt;
    state.x = THREE.MathUtils.clamp(state.x, -8.9, 8.9);

    state.dist += state.speed * dt;
    state.shake = Math.max(0, state.shake - dt * 2);
  }

  const fx = -Math.sin(state.heading);
  const fz = -Math.cos(state.heading);
  const rx = Math.cos(state.heading);
  const rz = -Math.sin(state.heading);
  const camOx = -0.38, camOz = 0.25;
  const bob = state.mode === 'playing'
    ? Math.sin(t * 13) * 0.006 * (state.speed / MAX_SPEED) + (state.offroad ? (Math.random() - 0.5) * 0.03 : 0)
    : 0;
  camera.position.set(
    state.x + rx * camOx - fx * camOz + (Math.random() - 0.5) * state.shake * 0.2,
    1.12 + bob,
    state.z + rz * camOx - fz * camOz + (Math.random() - 0.5) * state.shake * 0.2
  );
  camera.rotation.order = 'YXZ';
  camera.rotation.y = state.heading;
  camera.rotation.z = -state.steer * 0.035;
  camera.rotation.x = 0;

  const targetFov = 66 + (state.speed / MAX_SPEED) * 16;
  if (Math.abs(camera.fov - targetFov) > 0.1) {
    camera.fov += (targetFov - camera.fov) * Math.min(1, 4 * dt);
    camera.updateProjectionMatrix();
  }

  cockpit.wheel.rotation.z = state.steer * 1.7;

  sky.position.copy(camera.position);
  sun.position.set(camera.position.x - 90, 140, camera.position.z - 260);
  sun.target.position.set(camera.position.x, 0, camera.position.z);

  const scroll = state.dist / TILE;
  roadTex.offset.y = scroll;
  grassTex.offset.y = scroll;
  road.position.z = state.z - 200;
  grass.position.z = state.z - 300;
  shoulderL.position.set(-8.2, 0.03, state.z - 200);
  shoulderR.position.set(8.2, 0.03, state.z - 200);
  railL.position.x = -9.3;
  railR.position.x = 9.3;
  railL.position.z = state.z - 200;
  railR.position.z = state.z - 200;
  playerShadow.position.set(state.x, 0.03, state.z - 0.4);

  for (const obj of scenery) {
    if (obj.position.z - state.z > 60) obj.position.z -= 460;
    else if (state.z - obj.position.z > 420) obj.position.z += 460;
  }

  for (const car of traffic) {
    if (!car.active) continue;
    if (car.dir === 1) car.mesh.position.z -= car.speed * dt;
    else car.mesh.position.z += car.speed * dt;

    const rel = car.mesh.position.z - state.z;
    if (rel > 60 || rel < -420) {
      respawnCar(car, state.z);
      continue;
    }

    if (state.mode !== 'playing') continue;

    const dx = car.mesh.position.x - state.x;
    const dz = car.mesh.position.z - state.z;
    const lx = dx * rx + dz * rz;
    const lz = dx * -fx + dz * -fz;
    if (Math.abs(lx) < 1.9 && Math.abs(lz) < 4.5) {
      gameOver();
    }
  }

  if (audio && audio.ctx.state === 'running') {
    const sp = state.speed;
    const rpm = 0.15 + sp / MAX_SPEED;
    const f = 48 + sp * 5.2;
    audio.osc.frequency.setTargetAtTime(f, audio.ctx.currentTime, 0.08);
    audio.osc2.frequency.setTargetAtTime(f * 0.5, audio.ctx.currentTime, 0.08);
    audio.lp.frequency.setTargetAtTime(300 + rpm * 2400, audio.ctx.currentTime, 0.1);
    const targetGain = state.mode === 'playing' ? 0.045 + rpm * 0.05 : 0;
    audio.gain.gain.setTargetAtTime(targetGain, audio.ctx.currentTime, 0.1);
  }

  kmhEl.textContent = Math.round(state.speed * 3.6);
  distEl.textContent = `${Math.floor(state.dist)} м`;
}

let last = performance.now();
function loop(now) {
  const dt = Math.min(0.05, (now - last) / 1000);
  last = now;
  update(dt, now / 1000);
  renderer.render(scene, camera);
  requestAnimationFrame(loop);
}
requestAnimationFrame(loop);

window.addEventListener('resize', () => {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
});
