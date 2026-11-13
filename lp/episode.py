"""LAST PASSENGER — EP1 timeline. Every shot is fn(cv, t) with t = episode time."""
from common import DUR, skia, P, W, H
import sc1 as S1
import sc2 as S2

SHOTS = [
    (0.0, 2.86, S1.A1), (2.86, 4.56, S1.A2), (4.56, 6.52, S1.A3), (6.52, 8.6, S1.A4a), (8.6, 10.22, S1.A4b),
    (10.22, 11.68, S1.B1), (11.68, 14.96, S1.B2), (14.96, 16.3, S1.B3a), (16.3, 17.96, S1.B3b), (17.96, 19.46, S1.B4),
    (19.46, 22.12, S1.B5), (22.12, 25.76, S1.C1), (25.76, 28.08, S1.C2), (28.08, 31.7, S1.C3), (31.7, 36.14, S1.C4),
] + S2.SHOTS


def END(cv, t):
    cv.drawRect(skia.Rect(0, 0, W, H), P((0, 0, 0)))
    return dict(vign=0.0, grain=0.0, lift=(0, 0, 0))


def frame(cv, t):
    for a, b, fn in SHOTS:
        if a <= t < b:
            return fn(cv, t)
    return END(cv, t)
