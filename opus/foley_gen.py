"""Derive foley_events.json from the episode's actual animation phases (heel strikes = phase crossing k/2)."""
import json
import math
import sys
sys.path.insert(0, '/tmp/hoplite/workspace/opus'); sys.path.insert(0, '/tmp/hoplite/workspace/rem')
import motion as M
import opening as O
from episode import integ

ev = []
DT = 1 / 600


def strikes(phase_fn, t0, t1, who='hero', kind='step', gain=1.0, gate=None, cycle=0.5):
    k = 0
    prev = phase_fn(t0)
    t = t0 + DT
    while t < t1:
        ph = phase_fn(t)
        if math.floor(ph / cycle) > math.floor(prev / cycle) and (gate is None or gate(t)):
            ev.append({"t": round(t, 3), "kind": kind, "foot": -1 if k % 2 == 0 else 1, "gain": gain, "who": who, "lin": True})
            k += 1
        prev = ph
        t += DT


def add(t, kind, gain, foot=0, who='hero'):
    ev.append({"t": t, "kind": kind, "foot": foot, "gain": gain, "who": who, "lin": True})


# walk 0–11.9 (all shots use t*CAD)
strikes(lambda t: t * O.CAD, 0.0, 11.9, gain=0.9)
# B1 creature: the shape steps in sync, heavier and slower
S = 0.62
strikes(lambda t: (t - 9.2) * O.CAD * (O.V1 / O.CAD) / (500 * 0.5 * 1500 / 1000), 9.2, 11.9, who='creature', gain=0.55)
# B2 speeding up (his + its feet)
cad = lambda x: M.keys(x, [(11.9, 0.95), (12.6, 1.45), (14.3, 1.5)])
strikes(lambda t: integ(cad, 11.9, t), 11.9, 14.3, gain=1.05)
strikes(lambda t: 660 * 1.2 * integ(cad, 11.9, t) / (500 * 0.55 * 3300 / 1000), 11.9, 14.3, who='creature', gain=0.7)
# B3 decelerate & stop; the shape takes one more step and freezes
amp = lambda x: M.keys(x, [(14.3, 1.0), (14.95, 0.0)], fn=M.smooth)
strikes(lambda t: integ(lambda x: 1.2, 14.3, t), 14.3, 14.95, gain=0.9, gate=lambda t: amp(t) > 0.25)
add(14.95, 'scuff', 0.8, 1)
cph = lambda x: M.keys(x, [(14.3, 0.0), (15.9, 1.15)], fn=lambda u: 1 - (1 - u) ** 2)
strikes(cph, 14.3, 15.95, who='creature', gain=0.6)
# phone out, look up
add(18.0, 'rustle', 0.55); add(23.1, 'rustle', 0.3)
# turning his head at the window, shifting weight
add(27.4, 'rustle', 0.18); add(29.6, 'rustle', 0.2)
# recoil from the window (C9: launch 43.4, land 43.85)
add(43.42, 'rustle', 0.8); add(43.5, 'scuff', 0.6, -1); add(43.86, 'step', 1.2, 1); add(44.05, 'step', 0.8, -1)
# lamps: he shifts on his feet
add(56.7, 'scuff', 0.35, -1)
# the run
cad2 = lambda x: M.keys(x, [(59.1, 0.6), (59.6, 1.45)], fn=M.smooth)
amp2 = lambda x: M.keys(x, [(59.1, 0.4), (59.6, 1.0)], fn=M.smooth)
strikes(lambda t: integ(cad2, 59.1, t), 59.1, 61.0, kind='run_step', gain=1.0)
strikes(lambda t: (t - 61.0) * 1.45, 61.0, 63.0, kind='run_step', gain=0.9)
strikes(lambda t: (t - 63.0) * 1.5, 63.0, 64.9, kind='run_step', gain=1.0)
for t in (59.75, 60.55, 63.4, 64.2):
    add(t, 'splash', 0.55)
t = 60.6
while t < 64.6:   # his panting
    add(round(t, 3), 'breath', 0.85, -1); add(round(t + 0.36, 3), 'breath', 0.95, 1)
    t += 0.8
# collision + stagger
add(64.9, 'impact', 1.0); add(64.92, 'rustle', 0.9); add(65.12, 'step', 1.0, 1); add(65.3, 'scuff', 0.6, -1)
add(65.9, 'breath', 0.6)
# grab, whisper, struggle
add(74.98, 'rustle', 0.9); add(75.1, 'scuff', 0.5, 1)
for t in (81.6, 82.0, 82.45, 82.9, 83.35):
    add(t, 'rustle', 0.75)
add(81.8, 'scuff', 0.6, -1); add(82.7, 'scuff', 0.5, 1)
add(91.2, 'rustle', 0.5)                   # the double's grip loosens
add(93.3, 'rustle', 0.4)                   # he turns
json.dump(sorted(ev, key=lambda e: e['t']), open('/tmp/hoplite/workspace/rem/audio2/foley_events.json', 'w'), indent=0)
print(len(ev), 'events')
