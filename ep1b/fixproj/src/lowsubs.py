import re
RANGES = [(17.0, 24.9), (44.5, 53.9)]
out = []
for ln in open('subs_fixed.ass', encoding='utf-8'):
    m = re.match(r'(Dialogue: \d+,)(\d+):(\d+):([\d.]+),([^,]*,[^,]*,[^,]*,[^,]*,[^,]*,[^,]*,[^,]*,)(.*)', ln)
    if m:
        t = int(m.group(2)) * 3600 + int(m.group(3)) * 60 + float(m.group(4))
        if any(a <= t <= b for a, b in RANGES):
            txt = m.group(6)
            if txt.startswith('{'):
                txt = '{\\pos(540,1830)' + txt[1:]
            else:
                txt = '{\\pos(540,1830)}' + txt
            ln = '%s%s:%s:%s,%s%s' % (m.group(1), m.group(2), m.group(3), m.group(4), m.group(5), txt)
            if not ln.endswith('\n'): ln += '\n'
    out.append(ln)
open('subs_fixed2.ass', 'w', encoding='utf-8').writelines(out)
