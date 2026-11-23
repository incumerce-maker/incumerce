import json, numpy as np, soundfile as sf
SR=44100
T=json.load(open("timing.json")); tot=T["total"]; sc=T["scenes"]
n=int(SR*tot)+SR; t=np.arange(n)/SR
out=np.zeros(n)
def env(start,end,fi=0.5,fo=0.5):
    e=np.clip((t-start)/fi,0,1)*np.clip((end-t)/fo,0,1); return e
def note(f): return 440*2**((f-69)/12)
# tense part: drone + pulse, 0 .. scene4 start
s4=sc[3]["start"]; s6=sc[5]["start"]
drone=(np.sin(2*np.pi*55*t)+0.6*np.sin(2*np.pi*82.4*t)+0.3*np.sin(2*np.pi*110*t*1.003))*(0.7+0.3*np.sin(2*np.pi*0.5*t))
out+=0.16*drone*env(0,s4,0.3,1.0)
beat=0.5  # 120bpm
for k in np.arange(0,s4-0.5,beat):
    i=int(k*SR); L=int(0.18*SR)
    if i+L>n: break
    tt=np.arange(L)/SR
    kick=np.sin(2*np.pi*(60+80*np.exp(-tt*30))*tt)*np.exp(-tt*18)
    out[i:i+L]+=0.35*kick
    if int(k/beat)%2==1:
        j=i; tk=np.random.randn(int(0.03*SR))*np.exp(-np.arange(int(0.03*SR))/SR*120)
        out[j:j+len(tk)]+=0.06*tk
# riser before scene 4
rs=s4-2.0; m=(t>rs)&(t<s4)
x=(t[m]-rs)/2.0
out[m]+=0.12*np.random.randn(m.sum())*x**2 + 0.1*np.sin(2*np.pi*(200+800*x**2)*(t[m]-rs))*x
# hopeful part: chords C G Am F, 2s each
prog=[[60,64,67],[55,59,62,67],[57,60,64],[53,57,60,65]]
cl=2.0
k=0; st=s4
while st<tot+1:
    ch=prog[k%4]; e=env(st,st+cl+0.4,0.15,0.6)
    vol=0.10 if st<s6 else 0.075
    for f in ch:
        fr=note(f)
        out+=vol*e*(np.sin(2*np.pi*fr*t)+0.3*np.sin(2*np.pi*2*fr*t))*0.5
    out+=vol*1.2*e*np.sin(2*np.pi*note(ch[0]-12)*t)
    # arpeggio (only before closing)
    if st<s6:
        for a_i in range(8):
            ts=st+a_i*0.25; i=int(ts*SR); L=int(0.35*SR)
            if i+L>n: break
            tt=np.arange(L)/SR; f=note(ch[a_i%len(ch)]+12)
            out[i:i+L]+=0.05*np.sin(2*np.pi*f*tt)*np.exp(-tt*9)
    st+=cl; k+=1
# SFX
def hit(ts,vol=0.5):
    i=int(ts*SR); L=int(0.8*SR); tt=np.arange(L)/SR
    s=(np.sin(2*np.pi*(45+60*np.exp(-tt*12))*tt)+0.4*np.random.randn(L)*np.exp(-tt*25))*np.exp(-tt*5)
    out[i:i+L]+=vol*s[:max(0,min(L,n-i))]
def whoosh(ts,vol=0.15):
    L=int(0.45*SR); i=int(max(0,ts-0.2)*SR); tt=np.arange(L)/SR
    nz=np.random.randn(L); nz=np.convolve(nz,np.ones(20)/20,'same')
    out[i:i+L]+=vol*3*nz*np.sin(np.pi*tt/tt[-1])**2
# alarm beeps at opening
for b in range(3):
    i=int((0.15+b*0.32)*SR); L=int(0.2*SR); tt=np.arange(L)/SR
    out[i:i+L]+=0.18*np.sign(np.sin(2*np.pi*880*tt))*np.exp(-tt*6)
hit(0.05,0.6); hit(sc[0]["start"]+3.2,0.5)
for s in sc[1:3]: hit(s["start"],0.45)
# crack (scene2 ~2.6s)
c=sc[1]["start"]+2.6; i=int(c*SR); L=int(0.25*SR)
out[i:i+L]+=0.35*np.random.randn(L)*np.exp(-np.arange(L)/SR*30)
for s in sc[3:]: whoosh(s["start"])
for s in T["subs"]:
    if sc[3]["start"]+0.5<s["start"]<sc[5]["start"] and any(w in s["text"][:4] for w in ["둘째","셋째","다섯째"]): whoosh(s["start"]-0.25,0.12)
# duck under narration
nar,nsr=sf.read("narration.wav"); 
nar=np.interp(np.arange(n)/SR, np.arange(len(nar))/nsr, nar, right=0)
envn=np.convolve(np.abs(nar),np.ones(int(0.3*SR))/(0.3*SR),'same')
duck=1-0.45*np.clip(envn/0.05,0,1)
out*=duck
out[-int(1.0*SR):]*=np.linspace(1,0,int(1.0*SR))
mixd=out*0.9+nar*1.0
mixd=mixd[:int(SR*tot)]
mixd/=max(1,np.abs(mixd).max()/0.95)
sf.write("final_audio.wav",np.stack([mixd,mixd],1),SR)
print("ok",len(mixd)/SR)
