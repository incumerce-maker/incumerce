import json, re, subprocess, numpy as np, soundfile as sf
from tts import synth, SR
LS=0.74; TEMPO=1.16
spoken=json.load(open("lines.json",encoding="utf8"))
shown=json.load(open("display.json",encoding="utf8"))
def sents(t): return [s.strip() for s in re.split(r'(?<=[.!?])\s+',t) if s.strip()]
def tempo(a):
    sf.write("_t.wav",a,SR)
    subprocess.run(["ffmpeg","-y","-loglevel","error","-i","_t.wav","-filter:a",f"atempo={TEMPO}","_o.wav"],check=True)
    return sf.read("_o.wav",dtype="float32")[0]
track=[np.zeros(int(SR*0.5),np.float32)]; t=0.5
scenes=[]; subs=[]
for i,(sp,sh) in enumerate(zip(spoken,shown)):
    s_start=t-(0.5 if i==0 else 0.25)
    for a_s,d_s in zip(sents(sp),sents(sh)):
        parts=[p for p in re.split(r'\s*,\s*',a_s.strip(" .!?")) if p]
        chunk=[]
        for j,p in enumerate(parts):
            chunk.append(synth(p,LS))
            if j<len(parts)-1: chunk.append(np.zeros(int(SR*0.12),np.float32))
        a=tempo(np.concatenate(chunk)); a=a/(np.abs(a).max()+1e-6)*0.85
        subs.append({"start":t,"end":t+len(a)/SR,"text":d_s})
        track.append(a); t+=len(a)/SR
        g=0.22; track.append(np.zeros(int(SR*g),np.float32)); t+=g
    g=0.3 if i<5 else 1.2
    track.append(np.zeros(int(SR*g),np.float32)); t+=g
    scenes.append({"start":max(0,s_start),"end":t-0.25 if i<5 else t})
scenes[-1]["end"]=t
for k in range(1,6): scenes[k]["start"]=scenes[k-1]["end"]
sf.write("narration.wav",np.concatenate(track),SR)
json.dump({"total":t,"scenes":scenes,"subs":subs},open("timing.json","w",encoding="utf8"),ensure_ascii=False,indent=1)
print(round(t,2),[ (round(s['start'],2),round(s['end'],2)) for s in scenes])
