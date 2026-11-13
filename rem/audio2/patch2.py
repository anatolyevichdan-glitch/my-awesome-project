s = open("build_sfx.py").read()
a = s.index("def build_sfx(")
head = s[:a]
# lamp: drop pitch-down tone, shorten, quieter
head = head.replace("sig = click * 0.5 + thump * (0.9 + 0.3 * k) + bz * 0.5 + tone * [0.28, 0.3, 0.35][k]",
                    "sig = (click * 0.5 + thump * (0.7 + 0.15 * k) + bz * 0.45) * np.exp(-t / 0.9)")
new = '''def build_sfx(narr_mono, align):
    buf = np.zeros((2, N))
    log = []

    def L(t, name, moment, prominent, desc):
        log.append({"t": round(float(t), 3), "name": name, "moment": moment, "prominent": prominent, "desc": desc})
    r = rng(500)

    # 1) shadow appears (8.0 s): restrained low swell, no hit
    sh = swell([41.2, 82.4, 123.0], [1.0, 0.35, 0.12], 7.9, 9.0, 11.6, lpf=220, seed=1)
    nz = lp(r.standard_normal(N), 160, 2) * bump(8.0, 9.0, 9.2, 11.4) * 0.4
    buf += to_stereo((sh * 0.8 + nz) * 0.4)
    L(7.9, "shadow_swell", 1, True, "low swell 7.9-11.6 s, no impact")

    # 2) first phone: vibration (2 muffled pulses) + soft notification
    for t0 in [17.60, 18.05]:
        Ld = int(0.34 * SR)
        t = np.arange(Ld) / SR
        ph = 2 * np.pi * 172 * t
        m = np.sin(ph) + .55 * np.sin(2 * ph) + .3 * np.sin(3 * ph)
        m *= 1 + 0.3 * np.sin(2 * np.pi * 7 * t)
        rattle = bp(r.standard_normal(Ld), 350, 1300, 2) * (0.5 + 0.5 * np.sin(ph))
        env = np.clip(t / .012, 0, 1) * np.clip((0.34 - t) / .02, 0, 1)
        place(buf, lp((m * 0.7 + rattle * 1.2) * env, 1800, 2), t0, 0.55, 0.15)
    L(17.6, "phone_vibration", 2, True, "2-pulse vibration muffled by cloth")
    notif(buf, 19.0, 0.16, 0.36, 0.1)
    L(19.0, "notification_1", 2, True, "soft two-note notification")

    # 3) reflection: dropout is applied to other stems (dip_curve); very quiet glass squeak only
    t = np.arange(int(0.9 * SR)) / SR
    stick = (np.sin(2 * np.pi * 36 * t * (1 + 0.5 * t)) > 0.2).astype(float)
    stick = onepole(stick, 0.003)
    fq = 2300 + 900 * (t / 0.9) ** 1.5
    sq = np.sin(2 * np.pi * np.cumsum(fq) / SR) * stick
    sq += 0.6 * np.sin(2 * np.pi * np.cumsum(fq * 1.5) / SR) * stick
    sq += bp(r.standard_normal(len(t)), 4000, 9000, 1) * 0.25 * stick
    sq *= np.sin(np.pi * t / 0.9) ** 1.5
    place(buf, sq, 40.95, 0.05, 0.2)
    L(38.6, "reflection_dropout", 3, True, "music/ambience/foley dip 38.6-43.4 s (no stinger); very quiet glass squeak at 40.95 s. 'Tss' reverb tail removed")

    # 4) second phone notification (same tone), later one quieter and shorter
    notif(buf, 45.0, 0.16, 0.36, 0.1)
    L(45.0, "notification_2", 4, True, "same soft two-note tone as 19.0 s")
    notif(buf, 50.2, 0.06, 0.15, 0.1)
    L(50.2, "notification_3", 4, False, "quieter, shorter version of the tone")

    # 5) lamps
    for k, t0 in enumerate([56.60, 57.37, 58.20]):
        lamp(buf, t0, k)
        L(t0, "lamp_%d_off" % (k + 1), 5, True, "short electrical clunk + dying buzz")

    # 6) escape starts: subtle whoosh
    Lw = int(0.7 * SR)
    t = np.arange(Lw) / SR
    wh = bp(r.standard_normal(Lw), 400, 2500, 2) * np.sin(np.pi * np.clip(t / 0.7, 0, 1)) ** 2
    place(buf, wh, 59.0, 0.25, 0.0)
    L(59.1, "escape_whoosh", 6, True, "subtle cloth whoosh (footstep burst comes from foley)")

    # 7) collision: dull body impact (cloth + thud), nothing metallic
    Lc = int(0.8 * SR)
    t = np.arange(Lc) / SR
    body = np.sin(2 * np.pi * 55 * (1 + 0.8 * np.exp(-t / .05)) * t) * np.exp(-t / 0.13)
    body += lp(r.standard_normal(Lc), 200, 2) * np.exp(-t / 0.06) * 1.4
    cloth = bp(r.standard_normal(Lc), 600, 4000, 2) * np.exp(-0.5 * ((t - 0.03) / 0.05) ** 2) * 0.6
    place(buf, body + cloth, 64.9, 1.5, 0)
    L(64.9, "collision", 7, True, "single dull body impact (cloth + thud); music/ambience dip 64.9-66.6 s")

    # 9) rooftop reveal: slow deep swell + distant structural groan
    sub = swell([34.0, 36.2, 68.5, 51.0], [1.0, 0.8, 0.35, 0.3], 94.5, 96.0, 101.8, lpf=140, seed=9)
    buf += to_stereo(sub * 0.5)
    i0, i1 = int(95.2 * SR), int(100.8 * SR)
    tt = np.arange(i1 - i0) / SR
    sag = 1 - 0.035 * (tt / tt[-1]) ** 0.7
    vib = 1 + 0.004 * np.sin(2 * np.pi * 4.7 * tt)
    gr = np.zeros(len(tt))
    for ra, a in zip([1, 1.47, 2.09, 2.76, 3.9], [1, .7, .5, .35, .2]):
        gr += a * np.sin(2 * np.pi * np.cumsum(88 * ra * sag * vib) / SR + ra)
    gr *= (1 + 0.5 * lp(r.standard_normal(len(tt)), 8, 1) / 0.2)
    gr = lp(gr, 1400, 2) * np.clip(tt / 1.2, 0, 1) ** 2 * np.clip((tt[-1] - tt) / 2.5, 0, 1)
    g_full = np.zeros(N)
    g_full[i0:i1] = gr
    gw = convolve_stereo(to_stereo(g_full), ir_reverb(5.0, 81, decay_db=60, lp_hz=4000, predelay=0.06))
    buf += gw * 0.7 + to_stereo(g_full) * 0.1
    L(95.2, "rooftop_reveal", 9, True, "deep slow swell 94.5-101.8 s + distant structural groan 95.2-100.8 s")
    return buf, log
'''
open("build_sfx.py", "w").write(head + new)
