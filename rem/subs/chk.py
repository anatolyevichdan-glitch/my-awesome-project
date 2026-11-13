import json
e=json.load(open('subs_events.json'))['events']
bad=[(i,x['text']) for i,x in enumerate(e[1:],1) if x['start_frame']<e[i-1]['end_frame']]
print('overlaps',bad,'n',len(e),'first',e[0]['start'],'last end',e[-1]['end'],'maxdur',max(x['end']-x['start'] for x in e),'mindur',min(x['end']-x['start'] for x in e))
# lead/trail vs words
import statistics
lead=[x['start']-x['words'][0]['start'] for x in e];trail=[x['end']-x['words'][-1]['end'] for x in e]
print('lead range',min(lead),max(lead),'trail range',min(trail),max(trail))
print([ (x['text'],round(t,2)) for x,t in zip(e,trail) if t>0.25 or t<0])
print(sum(1 for x in e for _ in x['emph'] if _['color']=='yellow'),sum(1 for x in e for _ in x['emph'] if _['color']=='red'))
