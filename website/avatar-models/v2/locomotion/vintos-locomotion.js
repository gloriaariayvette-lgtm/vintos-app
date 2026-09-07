/**
 * Vintos locomotion — he decides where to go; this walks him there.
 *
 * Two layers:
 *   HousePath  — room-to-room routing over house-map.json's door graph.
 *   Locomotion — turns a route into motion: turn to face, walk, arrive, idle.
 *
 * Needs no house geometry to route. When v2/house/<room>.glb exists, pass its
 * PORTAL_* and NAV_* node positions to setRoomGeometry() and the same route
 * becomes real world-space waypoints. Until then it walks the graph with
 * placeholder positions so the whole loop is testable.
 *
 * Clips come from v2/clips.json. Only three are required: an idle, a walk,
 * and a turn. Everything else is optional flavour.
 */

const DEG = Math.PI / 180;

export class HousePath {
  /** houseMap: the parsed scripts/house-map.json from the Vintos repo. */
  constructor(houseMap) {
    this.map = houseMap;
    this.adj = new Map();
    for (const r of houseMap.rooms) {
      // 'cats room' in the map, catsroom as a file/id elsewhere — accept both
      this.adj.set(this.norm(r.id), (r.adjacent || []).map(a => this.norm(a)));
    }
  }
  norm(id) { return String(id).toLowerCase().replace(/[^a-z]/g, ''); }

  /** Shortest room sequence, inclusive of both ends. Null when unreachable. */
  route(from, to) {
    from = this.norm(from); to = this.norm(to);
    if (from === to) return [from];
    const prev = new Map([[from, null]]);
    const q = [from];
    while (q.length) {
      const cur = q.shift();
      for (const nb of this.adj.get(cur) || []) {
        if (prev.has(nb)) continue;
        prev.set(nb, cur);
        if (nb === to) {
          const path = [nb];
          for (let p = cur; p != null; p = prev.get(p)) path.unshift(p);
          return path;
        }
        q.push(nb);
      }
    }
    return null;
  }

  /** Doors crossed on a route, as [roomA, roomB] pairs — these name PORTAL_ nodes. */
  doors(route) {
    const out = [];
    for (let i = 0; i + 1 < route.length; i++) out.push([route[i], route[i + 1]]);
    return out;
  }
}

/** One waypoint the body must reach, in world metres. */
class Waypoint {
  constructor(pos, room, kind) { this.pos = pos; this.room = room; this.kind = kind; }
}

export class Locomotion {
  /**
   * opts.THREE      three.js namespace
   * opts.root       the avatar's scene root (moved and rotated by this class)
   * opts.mixer      THREE.AnimationMixer bound to the avatar
   * opts.clips      { idle: AnimationClip, walk: AnimationClip, turn_left, turn_right, ... }
   * opts.speed      metres per second (default 1.1, an unhurried indoor walk)
   * opts.turnRate   degrees per second (default 220)
   */
  constructor(opts) {
    const T = this.THREE = opts.THREE;
    this.root = opts.root;
    this.mixer = opts.mixer;
    this.speed = opts.speed ?? 1.1;
    this.turnRate = (opts.turnRate ?? 220) * DEG;
    this.arriveRadius = opts.arriveRadius ?? 0.18;
    this.slowRadius = opts.slowRadius ?? 0.7;

    this.actions = {};
    for (const [name, clip] of Object.entries(opts.clips || {})) {
      const a = this.mixer.clipAction(clip);
      a.enabled = true; a.setEffectiveWeight(0); a.play();
      this.actions[name] = a;
    }
    this.state = 'idle';
    this.current = 'idle';
    this.queue = [];
    this.room = opts.startRoom || 'stairs';
    this.onArrive = null;
    this.onRoomChange = null;
    this._blend = 0.18;   // seconds to cross-fade
    this._up = new T.Vector3(0, 1, 0);
    this._setWeight('idle', 1);
  }

  /** Portal and floor positions per room, once the house GLBs exist.
   *  geo = { kitchen: { portals: { livingroom: Vector3, hall: Vector3, ... },
   *                     centre: Vector3, anchors: { countertops: Vector3 } } } */
  setRoomGeometry(geo) { this.geo = geo; }

  /** Where he is, in world metres. */
  get position() { return this.root.position; }

  /** Vintos's main verb: walk to a room, optionally to a named anchor in it. */
  goTo(room, anchor = null) {
    if (!this.path) throw new Error('call setHousePath(new HousePath(map)) first');
    const route = this.path.route(this.room, room);
    if (!route) { this._fail(`no route from ${this.room} to ${room}`); return false; }
    const T = this.THREE;
    this.queue = [];
    for (const [a, b] of this.path.doors(route)) {
      const p = this._portalPos(a, b);
      if (p) this.queue.push(new Waypoint(p, b, 'door'));
    }
    const dest = anchor ? this._anchorPos(room, anchor) : this._roomCentre(room);
    if (dest) this.queue.push(new Waypoint(dest, room, anchor ? 'anchor' : 'centre'));
    this.state = this.queue.length ? 'walking' : 'idle';
    this.target = room; this.targetAnchor = anchor;
    return true;
  }

  setHousePath(p) { this.path = p; }
  stop() { this.queue = []; this.state = 'idle'; }

  /** Play a one-shot clip (wave, point, shrug) without disturbing locomotion. */
  gesture(name) {
    const a = this.actions[name];
    if (!a) return false;
    a.reset(); a.setLoop(this.THREE.LoopOnce, 1); a.clampWhenFinished = true;
    a.setEffectiveWeight(1); a.play();
    return true;
  }

  _portalPos(a, b) {
    const g = this.geo?.[a]?.portals?.[b];
    if (g) return g.clone();
    return this._placeholder(a, b);
  }
  _roomCentre(r) {
    const g = this.geo?.[r]?.centre;
    if (g) return g.clone();
    return this._placeholder(r, r);
  }
  _anchorPos(r, name) {
    const g = this.geo?.[r]?.anchors?.[name];
    return g ? g.clone() : this._roomCentre(r);
  }
  /** Deterministic stand-in positions so routing and gait are testable
   *  before any room geometry exists. Replaced entirely by setRoomGeometry. */
  _placeholder(a, b) {
    const T = this.THREE;
    const h = s => { let x = 0; for (const c of s) x = (x * 31 + c.charCodeAt(0)) >>> 0; return x; };
    const k = h(a + '|' + b);
    return new T.Vector3(((k % 1000) / 1000 - 0.5) * 8, 0, (((k >> 10) % 1000) / 1000 - 0.5) * 8);
  }

  _setWeight(name, w) {
    const a = this.actions[name];
    if (a) a.setEffectiveWeight(w);
  }
  /** Cross-fade the locomotion pose toward one clip. */
  _drive(name, dt) {
    if (!this.actions[name]) name = 'idle';
    if (name !== this.current) {
      const from = this.actions[this.current], to = this.actions[name];
      if (to) { to.enabled = true; to.play(); }
      this._fade = { from: this.current, to: name, t: 0 };
      this.current = name;
    }
    if (this._fade) {
      this._fade.t += dt / this._blend;
      const k = Math.min(1, this._fade.t);
      this._setWeight(this._fade.from, 1 - k);
      this._setWeight(this._fade.to, k);
      if (k >= 1) this._fade = null;
    } else {
      this._setWeight(name, 1);
    }
  }

  /** Call every frame. dt in seconds. */
  update(dt) {
    const T = this.THREE;
    if (this.state !== 'walking' || !this.queue.length) {
      this._drive('idle', dt);
      this.mixer.update(dt);
      return;
    }
    const wp = this.queue[0];
    const here = this.root.position;
    const to = new T.Vector3().subVectors(wp.pos, here); to.y = 0;
    const dist = to.length();

    // arrive
    if (dist < this.arriveRadius) {
      this.queue.shift();
      if (wp.room !== this.room) {
        const was = this.room; this.room = wp.room;
        this.onRoomChange?.(was, this.room);
      }
      if (!this.queue.length) {
        this.state = 'idle';
        this.onArrive?.(this.room, this.targetAnchor);
      }
      this._drive('idle', dt); this.mixer.update(dt);
      return;
    }

    // face the waypoint, turning at a bounded rate
    const want = Math.atan2(to.x, to.z);
    const have = this.root.rotation.y;
    let diff = ((want - have + Math.PI * 3) % (Math.PI * 2)) - Math.PI;
    const maxTurn = this.turnRate * dt;
    const turned = Math.max(-maxTurn, Math.min(maxTurn, diff));
    this.root.rotation.y = have + turned;

    // turn in place when badly misaligned, otherwise walk
    const misaligned = Math.abs(diff) > 50 * DEG;
    if (misaligned) {
      this._drive(diff > 0 ? 'turn_left' : 'turn_right', dt);
    } else {
      // ease down on approach so he does not stop dead
      const ease = Math.min(1, dist / this.slowRadius);
      const step = this.speed * ease * dt;
      const dir = to.normalize();
      this.root.position.addScaledVector(dir, Math.min(step, dist));
      this._drive('walk', dt);
      const a = this.actions.walk;
      if (a) a.setEffectiveTimeScale(Math.max(0.55, ease));
    }
    this.mixer.update(dt);
  }

  _fail(msg) { this.state = 'idle'; this.onError?.(msg); }
}

/** Convenience: build the clip map from v2/clips.json plus loaded GLBs.
 *  roles used: walk, idle_stand, turn_left, turn_right; the rest pass through by name. */
export function clipsByRole(clipsJson, loaded) {
  const out = {};
  const roleTo = { walk: 'walk', idle_stand: 'idle', turn_left: 'turn_left', turn_right: 'turn_right' };
  for (const [name, meta] of Object.entries(clipsJson.clips || {})) {
    const clip = loaded[name];
    if (!clip) continue;
    out[name] = clip;
    const alias = roleTo[meta.role];
    if (alias && !out[alias]) out[alias] = clip;
  }
  return out;
}
