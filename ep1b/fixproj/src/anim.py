import math
from char import *

def sstep(x): x=max(0.0,min(1.0,x)); return x*x*(3-2*x)
def lerp(a,b,t): return a+(b-a)*t
def kf(t, keys):
    """keys [(t,v)...] smooth interpolation; v may be float or tuple"""
    if t<=keys[0][0]: return keys[0][1]
    if t>=keys[-1][0]: return keys[-1][1]
    for (t0,v0),(t1,v1) in zip(keys,keys[1:]):
        if t0<=t<=t1:
            u=sstep((t-t0)/(t1-t0))
            if isinstance(v0,(tuple,list)): return tuple(lerp(a,b,u) for a,b in zip(v0,v1))
            return lerp(v0,v1,u)
def klin(t, keys):
    if t<=keys[0][0]: return keys[0][1]
    if t>=keys[-1][0]: return keys[-1][1]
    for (t0,v0),(t1,v1) in zip(keys,keys[1:]):
        if t0<=t<=t1:
            u=(t-t0)/(t1-t0)
            return lerp(v0,v1,u)

def ex(name, **kw): return expr(name, **kw)
def exmix(a,b,t): return blend_expr(EXPR[a] if isinstance(a,str) else a, EXPR[b] if isinstance(b,str) else b, t)

def blink_at(t, seed=0):
    """periodic blinks"""
    p = (t*0.37 + seed*0.173) % 1.0
    per = 2.7
    u = (t+seed*0.9) % per
    if u<0.14: return math.sin(u/0.14*math.pi)
    return 0.0

SH_REL = -(HIP_H) - (TORSO - 52) + 22   # shoulder y (relaxed)

def walk_front(ph, amp=1.0, arms=1.0, **kw):
    p = Pose(view='front')
    for sg,(fx,name) in ((-1,(-52,'L')),(1,(52,'R'))):
        phi = ph + (0 if sg<0 else math.pi)
        s = math.sin(phi); c = math.cos(phi)
        lift = max(0, s)*46*amp
        yy = 14*s*amp
        setattr(p,'f'+name,(fx*(1-0.1*c*0) + 0, yy))
        setattr(p,'lift'+name, lift)
        setattr(p,'z'+name, 1+0.16*s*amp)
    p.bob = 12*abs(math.cos(ph))*amp
    p.lean = 0.0
    p.tilt = 0.03*math.sin(ph)*amp
    # arms swing (foreshortened): hands rise/fall opposite to same-side leg
    sw = arms*amp
    p.hL = (-126+8*math.sin(ph), SH_REL+292-38*math.sin(ph+math.pi)*sw)
    p.hR = (126-8*math.sin(ph), SH_REL+292-38*math.sin(ph)*sw)
    p.sway = math.sin(ph+0.5)
    p.__dict__.update(kw)
    return p

def walk_side(ph, A=95, lift=62, flip=1, arm=1.0, lean=0.04, **kw):
    p = Pose(view='side', flip=flip)
    xs = {}
    for name,off in (('L',0),('R',math.pi)):
        phi = ph+off
        x = A*math.cos(phi)
        l = max(0,-math.sin(phi))*lift
        setattr(p,'f'+name,(x,0)); setattr(p,'lift'+name,l)
        xs[name]=x
    p.bob = 16*abs(math.sin(ph))*(A/95.0)
    p.lean = lean
    # arms: left arm swings with right leg
    ah = 150*arm
    p.hL = (-xs['L']*0.9*arm+10, SH_REL+298-max(0,-math.sin(ph+math.pi*0))*30*arm)
    p.hR = (-xs['R']*0.9*arm+10, SH_REL+298-max(0,-math.sin(ph+math.pi))*30*arm)
    p.bendL = 1; p.bendR = 1
    p.sway = math.sin(ph)
    p.__dict__.update(kw)
    return p

def run_side(ph, flip=1, **kw):
    p = walk_side(ph, A=135, lift=150, flip=flip, arm=1.0, lean=0.30)
    xs={}
    for name,off in (('L',0),('R',math.pi)):
        phi=ph+off; xs[name]=math.cos(phi)
    # arms bent up and pumping
    p.hL = (xs['L']*-120+60, SH_REL+190+30*xs['L'])
    p.hR = (xs['R']*-120+60, SH_REL+190+30*xs['R'])
    p.bob = 28*abs(math.sin(ph))
    p.__dict__.update(kw)
    return p

def run_front(ph, **kw):
    p = walk_front(ph, amp=1.8, arms=2.2)
    p.lean = 0.0
    p.hL = (-120+30*math.sin(ph), SH_REL+210-60*math.sin(ph+math.pi))
    p.hR = (120-30*math.sin(ph), SH_REL+210-60*math.sin(ph))
    p.bob = 30*abs(math.cos(ph))
    p.tilt = 0.08*math.sin(ph)
    p.__dict__.update(kw)
    return p
