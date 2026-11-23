import subprocess, re, json, sys, numpy as np, onnxruntime as ort, soundfile as sf
M="/tmp/claude-0/-home-user-incumerce/8b1e9bef-cd80-58ec-abaf-da403cba4618/scratchpad/tts/vits-mimic3-ko_KO-kss_low"
tok={}
for l in open(f"{M}/tokens.txt",encoding="utf8"):
    l=l.rstrip("\n"); 
    if not l: continue
    s,i=l.rsplit(" ",1); tok[s if s else " "]=int(i)
sess=ort.InferenceSession(f"{M}/ko_KO-kss_low.onnx")
SR=22050
def ipa(t):
    return subprocess.run(["espeak-ng","-v","ko","-q","--ipa"],input=t,capture_output=True,text=True).stdout.strip()
def ids_for(phr):
    words=ipa(phr).split()
    seq=[1,0]
    for wi,w in enumerate(words):
        if wi: seq+= [5,0]
        for c in w:
            if c in tok: seq+=[tok[c],0]
    seq+=[2]
    return seq
def synth(phr,ls=1.0):
    ids=np.array([ids_for(phr)],dtype=np.int64)
    a=sess.run(None,{"input":ids,"input_lengths":np.array([ids.shape[1]],dtype=np.int64),"scales":np.array([0.667,ls,0.8],dtype=np.float32)})[0].squeeze()
    return a.astype(np.float32)
def say(text,ls=1.0):
    out=[]
    for sent in re.split(r'(?<=[.!?])\s*',text):
        if not sent.strip(): continue
        parts=[p for p in re.split(r'\s*,\s*',sent.strip(" .!?")) if p]
        for j,p in enumerate(parts):
            out.append(synth(p,ls)); out.append(np.zeros(int(SR*(0.12 if j<len(parts)-1 else 0.25)),np.float32))
    return np.concatenate(out)
if __name__=="__main__":
    lines=json.load(open(sys.argv[1],encoding="utf8")); ls=float(sys.argv[2])
    for i,l in enumerate(lines):
        a=say(l,ls); a=a/ (np.abs(a).max()+1e-6)*0.9
        sf.write(f"n{i+1}.wav",a,SR); print(i+1,round(len(a)/SR,2))
