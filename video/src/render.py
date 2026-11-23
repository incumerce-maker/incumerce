import json, math, random, subprocess, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1920, 1080, 30
T = json.load(open("timing.json", encoding="utf8"))
TOTAL = T["total"]
SC = T["scenes"]
SUBS = T["subs"]
FD = "/usr/share/fonts/truetype/nanum/"
_fc = {}


def F(size, w="B"):
    name = {"EB": "NanumSquareEB.ttf", "B": "NanumSquareB.ttf", "R": "NanumBarunGothic.ttf",
            "RB": "NanumBarunGothicBold.ttf", "G": "NanumGothicExtraBold.ttf"}[w]
    k = (name, size)
    if k not in _fc:
        _fc[k] = ImageFont.truetype(FD + name, size)
    return _fc[k]


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ease(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def ease_io(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


def back(x):
    x = clamp(x)
    c = 1.70158
    return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2


def mix(c1, c2, t):
    return tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))


def grad(c1, c2, vertical=True):
    g = Image.new("RGB", (1, 256))
    for y in range(256):
        g.putpixel((0, y), mix(c1, c2, y / 255))
    return g.resize((W, H))


def text_c(d, xy, s, font, fill, anchor="mm", shadow=True, stroke=0, stroke_fill=(0, 0, 0)):
    if shadow:
        d.text((xy[0] + 4, xy[1] + 5), s, font=font, fill=(0, 0, 0, 150), anchor=anchor)
    d.text(xy, s, font=font, fill=fill, anchor=anchor, stroke_width=stroke, stroke_fill=stroke_fill)


def overlay(img, fn):
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    fn(ImageDraw.Draw(ov))
    img.alpha_composite(ov)


def a(c, al):
    return (c[0], c[1], c[2], int(clamp(al) * 255))


# ---------- reusable figures ----------
def student(d, x, y, s, body=(90, 90, 90), head=(140, 140, 140), bob=0, smile=False, hair=None):
    y += bob
    d.rounded_rectangle([x - 34 * s, y, x + 34 * s, y + 70 * s], radius=int(20 * s), fill=body)
    d.ellipse([x - 26 * s, y - 58 * s, x + 26 * s, y - 6 * s], fill=head)
    if hair:
        d.chord([x - 28 * s, y - 62 * s, x + 28 * s, y - 14 * s], 180, 360, fill=hair)
    if smile:
        d.ellipse([x - 12 * s, y - 38 * s, x - 6 * s, y - 32 * s], fill=(40, 40, 40))
        d.ellipse([x + 6 * s, y - 38 * s, x + 12 * s, y - 32 * s], fill=(40, 40, 40))
        d.arc([x - 12 * s, y - 34 * s, x + 12 * s, y - 18 * s], 20, 160, fill=(40, 40, 40), width=max(2, int(3 * s)))


def desk(d, x, y, s, col=(70, 70, 75)):
    d.rectangle([x - 60 * s, y + 40 * s, x + 60 * s, y + 56 * s], fill=col)
    d.rectangle([x - 52 * s, y + 56 * s, x - 44 * s, y + 100 * s], fill=col)
    d.rectangle([x + 44 * s, y + 56 * s, x + 52 * s, y + 100 * s], fill=col)


def warn_tri(d, cx, cy, r, al):
    pts = [(cx, cy - r), (cx + r * 0.95, cy + r * 0.7), (cx - r * 0.95, cy + r * 0.7)]
    d.polygon(pts, fill=a((230, 30, 40), al))
    inner = [(cx, cy - r * 0.72), (cx + r * 0.72, cy + r * 0.55), (cx - r * 0.72, cy + r * 0.55)]
    d.polygon(inner, fill=a((255, 220, 0), al))
    d.text((cx, cy + r * 0.08), "!", font=F(int(r * 0.9), "EB"), fill=a((20, 20, 20), al), anchor="mm")


def badge_title(img, d, lt, line1, line2=None, y=150, col=(255, 255, 255), hl=(255, 210, 60), size=78):
    k = ease(lt / 0.5)
    yy = y + (1 - k) * 40
    overlay(img, lambda o: (o.text((W // 2 + 4, yy + 5), line1, font=F(size, "EB"), fill=(0, 0, 0, int(160 * k)), anchor="mm"),
                            o.text((W // 2, yy), line1, font=F(size, "EB"), fill=a(col, k), anchor="mm")))
    if line2:
        k2 = ease((lt - 0.35) / 0.5)
        overlay(img, lambda o: (o.text((W // 2 + 3, yy + 92), line2, font=F(int(size * 0.62), "B"), fill=(0, 0, 0, int(150 * k2)), anchor="mm"),
                                o.text((W // 2, yy + 88), line2, font=F(int(size * 0.62), "B"), fill=a(hl, k2), anchor="mm")))


# ---------- scenes ----------
def scene1(t, dur):
    pulse = 0.5 + 0.5 * math.sin(t * 9)
    img = grad((25, 5, 10), (5, 5, 15)).convert("RGBA")
    # red radial glow
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    r = 700 + 60 * pulse
    gd.ellipse([W / 2 - r, H / 2 - r * 0.6, W / 2 + r, H / 2 + r * 0.6], fill=(200, 0, 20, int(70 + 50 * pulse)))
    img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(120)))
    d = ImageDraw.Draw(img)
    # exam hall (left)
    sw = ease(t / 0.8)
    ox = -400 * (1 - sw)
    d.rectangle([80 + ox, 300, 900 + ox, 840], fill=(30, 30, 40), outline=(90, 90, 110), width=4)
    d.text((490 + ox, 335), "수능 시험장", font=F(36, "B"), fill=(200, 200, 210), anchor="mm")
    d.rectangle([300 + ox, 370, 680 + ox, 430], fill=(20, 60, 40))
    d.text((490 + ox, 400), "2026학년도 대학수학능력시험", font=F(24, "R"), fill=(220, 230, 220), anchor="mm")
    for row in range(3):
        for col in range(4):
            sx = 200 + col * 190 + ox + (row - 1) * 10
            sy = 490 + row * 110
            s = 0.55 + row * 0.08
            student(d, sx, sy, s, body=(70, 70, 85), head=(150, 140, 130))
            desk(d, sx, sy, s)
    # phone (right)
    ph = ease((t - 0.6) / 0.8)
    px = 1300 + 600 * (1 - ph)
    d.rounded_rectangle([px, 260, px + 380, 900], radius=48, fill=(15, 15, 20), outline=(160, 160, 175), width=6)
    d.rounded_rectangle([px + 20, 310, px + 360, 860], radius=20, fill=(240, 242, 248))
    d.rounded_rectangle([px + 150, 280, px + 230, 292], radius=6, fill=(60, 60, 70))
    d.text((px + 190, 340), "AI 챗봇", font=F(26, "B"), fill=(40, 40, 60), anchor="mm")
    bubbles = [("수학 30번 풀어줘", True, 1.4), ("정답은 ③번입니다.", False, 2.2), ("풀이 과정:\n① 미분 후 대입…", False, 2.9)]
    by = 390
    for txt, me, at in bubbles:
        if t > at:
            k = ease((t - at) / 0.3)
            fnt = F(26, "R")
            bb = d.multiline_textbbox((0, 0), txt, font=fnt)
            bw, bh = bb[2] - bb[0] + 40, bb[3] - bb[1] + 30
            bx = px + 340 - bw if me else px + 40
            col = (60, 120, 255) if me else (225, 228, 235)
            d.rounded_rectangle([bx, by, bx + bw * k, by + bh], radius=18, fill=col)
            if k > 0.9:
                d.multiline_text((bx + 20, by + 14), txt, font=fnt, fill=(255, 255, 255) if me else (30, 30, 40))
            by += bh + 24
    # quick cross-cut flashes between hall and phone
    if 0.9 < t < 3.2 and int(t * 6) % 3 == 0:
        overlay(img, lambda o: o.rectangle([0, 0, W, H], fill=(255, 0, 30, 40)))
    # breaking bar
    d.rectangle([0, 0, W, 110], fill=(190, 0, 20))
    d.rectangle([0, 0, 300, 110], fill=(255, 255, 255))
    d.text((150, 55), "속보", font=F(64, "EB"), fill=(190, 0, 20), anchor="mm")
    tick = "   수능·국가시험까지 AI 부정행위 적발   ·   스마트폰 속 AI 답변 확산   ·   'AI 교육 선언' 7년의 역설   "
    off = (t * 260) % 1700
    d.text((330 - off, 55), tick * 2, font=F(40, "B"), fill=(255, 255, 255), anchor="lm")
    d.rectangle([0, 0, 300, 110], fill=(255, 255, 255))
    d.text((150, 55), "속보", font=F(64, "EB"), fill=(190, 0, 20), anchor="mm")
    # warning triangles
    if t > 1.0:
        al = 0.55 + 0.45 * pulse
        warn_tri(d, 1100, 600, 95, al)
    # title
    k = back((t - 3.2) / 0.6)
    if t > 3.2:
        overlay(img, lambda o: o.rectangle([0, 170, W, 280 + 90 * ease((t - 3.6) / 0.4)], fill=(0, 0, 0, 220)))
        fs = int(90 * (0.6 + 0.4 * k))
        text_c(d, (W // 2, 225), "수능까지 뚫은 AI 부정행위", F(fs, "EB"), (255, 255, 255), stroke=3, stroke_fill=(190, 0, 20))
    if t > 3.7:
        k2 = ease((t - 3.7) / 0.4)
        text_c(d, (W // 2, 320), "'AI 교육 선언' 7년의 거대한 역설", F(54, "B"), a((255, 200, 60), k2)[:3])
    img = glitch(img, t)
    return img


def glitch(img, t):
    if t < 0.5 or (3.15 < t < 3.35):
        random.seed(int(t * 30))
        out = img.copy()
        for _ in range(9):
            y = random.randint(0, H - 60)
            h = random.randint(10, 60)
            dx = random.randint(-60, 60)
            strip = img.crop((0, y, W, y + h))
            out.paste(strip, (dx, y))
        return out
    return img


def scene2(t, dur):
    gray = 1 - 0.6 * ease((t - 3.5) / 1.5)
    img = grad(mix((30, 30, 36), (40, 40, 48), 1), (12, 12, 16)).convert("RGBA")
    d = ImageDraw.Draw(img)
    # student grid (mechanical)
    if t > 3.0:
        k = ease((t - 3.0) / 0.8)
        for row in range(3):
            for col in range(9):
                sx = 140 + col * 205
                sy = 640 + row * 125
                bob = 6 * math.sin(t * 10) if True else 0
                c = int(70 + 30 * k)
                student(d, sx, sy, 0.5, body=(c, c, c), head=(c + 40, c + 40, c + 40), bob=bob * k)
                desk(d, sx, sy, 0.5, col=(55, 55, 60))
                # workbook
                d.rectangle([sx - 25, sy + 26 + bob * k, sx + 25, sy + 40 + bob * k], fill=(200, 200, 200))
        overlay(img, lambda o: o.rectangle([0, 560, W, H], fill=(0, 0, 0, int(90 * (1 - k)))))
    # document card
    k = ease(t / 0.6)
    cx, cy = W // 2, 400 - (1 - k) * 60
    sc = 1 - 0.25 * ease((t - 3.0) / 0.8)
    cw, ch = 640 * sc, 420 * sc
    cy2 = cy - 70 * ease((t - 3.0) / 0.8)
    d.rounded_rectangle([cx - cw / 2, cy2 - ch / 2, cx + cw / 2, cy2 + ch / 2], radius=12, fill=(245, 240, 228), outline=(200, 180, 140), width=4)
    d.text((cx, cy2 - ch / 2 + 50 * sc), "2019 AI 공교육 공동선언문", font=F(int(40 * sc), "EB"), fill=(40, 40, 50), anchor="mm")
    for i in range(5):
        lw = (480 - (i % 2) * 120) * sc
        ly = cy2 - ch / 2 + (110 + i * 44) * sc
        d.rounded_rectangle([cx - 240 * sc, ly, cx - 240 * sc + lw, ly + 14 * sc], radius=6, fill=(190, 185, 175))
    # 휴머니즘 word
    if t > 1.0:
        wk = back((t - 1.0) / 0.5)
        crack = clamp((t - 2.6) / 0.25)
        fall = ease((t - 2.9) / 1.4)
        word = "휴머니즘"
        fnt = F(int(150 * (0.5 + 0.5 * clamp(wk, 0, 1.2))), "EB")
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ld = ImageDraw.Draw(layer)
        ld.text((W // 2 + 6, 420 + 8), word, font=fnt, fill=(0, 0, 0, 160), anchor="mm")
        ld.text((W // 2, 420), word, font=fnt, fill=(255, 200, 70), anchor="mm", stroke_width=4, stroke_fill=(120, 70, 0))
        if crack > 0:
            pts = [(W // 2 - 20, 300), (W // 2 + 15, 360), (W // 2 - 25, 420), (W // 2 + 20, 480), (W // 2 - 10, 545)]
            ld.line(pts, fill=(20, 20, 20, int(255 * crack)), width=9)
        if fall > 0:
            L = layer.crop((0, 0, W // 2, H)).rotate(-25 * fall, center=(W // 2, 420), resample=Image.BICUBIC)
            R = layer.crop((W // 2, 0, W, H)).rotate(25 * fall, center=(0, 420), resample=Image.BICUBIC)
            layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            layer.paste(L, (int(-160 * fall), int(500 * fall ** 2)), L)
            layer.paste(R, (W // 2 + int(160 * fall), int(500 * fall ** 2)), R)
            alpha = layer.getchannel("A").point(lambda v: int(v * (1 - fall)))
            layer.putalpha(alpha)
        img.alpha_composite(layer)
    # desaturate
    if gray < 1:
        g = img.convert("L").convert("RGBA")
        img = Image.blend(img, g, 1 - gray)
    d = ImageDraw.Draw(img)
    if t > 4.0:
        k = ease((t - 4.0) / 0.5)
        overlay(img, lambda o: o.rounded_rectangle([W / 2 - 720, 40, W / 2 + 720, 140], radius=20, fill=(0, 0, 0, int(190 * k))))
        d = ImageDraw.Draw(img)
        d.text((W // 2, 90), "기술은 도입했지만,", font=F(56, "B"), fill=a((255, 255, 255), k), anchor="rm")
        d.text((W // 2 + 15, 90), "'인간 중심' 본질은 실종", font=F(56, "EB"), fill=a((255, 90, 90), k), anchor="lm")
    return img


def cctv(d, x, y, s, col=(160, 160, 170)):
    d.polygon([(x - 120 * s, y - 40 * s), (x + 110 * s, y - 70 * s), (x + 130 * s, y + 10 * s), (x - 110 * s, y + 40 * s)], fill=col)
    d.ellipse([x + 90 * s, y - 50 * s, x + 150 * s, y + 10 * s], fill=(40, 40, 50))
    d.ellipse([x + 108 * s, y - 32 * s, x + 132 * s, y - 8 * s], fill=(220, 30, 30))
    d.rectangle([x - 20 * s, y + 30 * s, x + 10 * s, y + 120 * s], fill=col)
    d.rectangle([x - 90 * s, y + 110 * s, x + 80 * s, y + 140 * s], fill=col)


def classroom(t):
    img = grad((255, 236, 190), (255, 214, 150)).convert("RGBA")
    d = ImageDraw.Draw(img)
    d.rectangle([0, 760, W, H], fill=(196, 150, 100))
    for i in range(3):  # windows
        x = 120 + i * 260
        d.rectangle([x, 160, x + 200, 460], fill=(170, 220, 255), outline=(255, 255, 255), width=10)
        d.line([x + 100, 160, x + 100, 460], fill=(255, 255, 255), width=8)
    d.rectangle([960, 170, 1800, 520], fill=(40, 100, 70), outline=(150, 100, 60), width=16)
    d.text((1380, 300), "어떻게 가르치고", font=F(60, "EB"), fill=(255, 255, 255), anchor="mm")
    d.text((1380, 400), "어떻게 평가할까?", font=F(60, "EB"), fill=(255, 240, 120), anchor="mm")
    cols = [(240, 90, 90), (80, 160, 240), (100, 200, 120), (250, 170, 50), (170, 110, 220), (60, 190, 190)]
    for i in range(6):
        sx = 260 + i * 280
        bob = 8 * math.sin(t * 4 + i)
        student(d, sx, 700, 0.95, body=cols[i], head=(255, 214, 180), bob=bob, smile=True, hair=(60, 40, 30))
        desk(d, sx, 700, 0.95, col=(150, 100, 60))
    return img


def scene3(t, dur):
    dark = grad((20, 22, 30), (8, 8, 12)).convert("RGBA")
    d = ImageDraw.Draw(dark)
    cctv(d, 640, 430, 1.6)
    cctv(d, 1300, 470, 1.2, col=(130, 130, 140))
    d.text((W // 2, 780), "단속 · 감시 · 통제", font=F(70, "EB"), fill=(200, 200, 210), anchor="mm")
    if t > 1.0:
        k = ease((t - 1.0) / 0.4)
        k2 = ease((t - 1.3) / 0.4)
        L = 330
        d.line([W / 2 - L, 470 - L, W / 2 - L + 2 * L * k, 470 - L + 2 * L * k], fill=(240, 30, 40), width=48)
        if k2 > 0:
            d.line([W / 2 + L, 470 - L, W / 2 + L - 2 * L * k2, 470 - L + 2 * L * k2], fill=(240, 30, 40), width=48)
    wipe = ease_io((t - 2.6) / 0.9)
    if wipe <= 0:
        img = dark
    else:
        cl = classroom(t)
        mask = Image.new("L", (W, H), 0)
        md = ImageDraw.Draw(mask)
        r = wipe * 1200
        md.ellipse([W / 2 - r, H / 2 - r, W / 2 + r, H / 2 + r], fill=255)
        img = Image.composite(cl, dark, mask)
    d = ImageDraw.Draw(img)
    if t > 3.4:
        k = ease((t - 3.4) / 0.5)
        overlay(img, lambda o: o.rounded_rectangle([W / 2 - 800, 30, W / 2 + 800, 140], radius=24, fill=(20, 30, 60, int(220 * k))))
        d = ImageDraw.Draw(img)
        d.text((W // 2 - 10, 85), "단순 통제는 한계!", font=F(58, "B"), fill=a((255, 255, 255), k), anchor="rm")
        d.text((W // 2 + 10, 85), "해법은 '평가의 대전환'", font=F(58, "EB"), fill=a((255, 215, 70), k), anchor="lm")
    if t > dur - 2.8:
        k = back((t - (dur - 2.8)) / 0.5)
        r = 110 * clamp(k, 0, 1.3)
        d.ellipse([W - 260 - r, 640 - r, W - 260 + r, 640 + r], fill=(230, 60, 60), outline=(255, 255, 255), width=8)
        if k > 0.6:
            d.text((W - 260, 615), "5가지", font=F(46, "EB"), fill=(255, 255, 255), anchor="mm")
            d.text((W - 260, 670), "해법", font=F(40, "B"), fill=(255, 255, 255), anchor="mm")
    return img


def solution_frame(n, title, color, lt, sdur, draw_icon):
    img = grad(mix(color, (255, 255, 255), 0.75), mix(color, (255, 255, 255), 0.45)).convert("RGBA")
    d = ImageDraw.Draw(img)
    # progress dots
    for i in range(5):
        x = W / 2 - 200 + i * 100
        on = i + 1 == n
        done = i + 1 < n
        r = 26 if on else 18
        d.ellipse([x - r, 70 - r, x + r, 70 + r], fill=color if (on or done) else (255, 255, 255), outline=color, width=4)
        d.text((x, 70), str(i + 1), font=F(26 if on else 20, "EB"), fill=(255, 255, 255) if (on or done) else color, anchor="mm")
    # slide-in
    k = ease(lt / 0.45)
    dx = int((1 - k) * 300)
    # number + title (left)
    cx = 470 - dx
    r = 120
    d.ellipse([cx - r, 400 - r, cx + r, 400 + r], fill=color)
    d.text((cx, 400), "①②③④⑤"[n - 1], font=F(150, "R"), fill=(255, 255, 255), anchor="mm")
    lines = title.split("\n")
    for i, ln in enumerate(lines):
        d.text((cx + 4, 600 + i * 95 + 5), ln, font=F(78, "EB"), fill=(0, 0, 0, 90), anchor="mm")
        d.text((cx, 600 + i * 95), ln, font=F(78, "EB"), fill=mix(color, (0, 0, 0), 0.45), anchor="mm")
    # icon panel (right)
    pk = ease((lt - 0.15) / 0.5)
    px = 1000 + int((1 - pk) * 500)
    d.rounded_rectangle([px, 180, px + 820, 800], radius=40, fill=(255, 255, 255), outline=mix(color, (255, 255, 255), 0.3), width=6)
    draw_icon(img, d, px, 180, lt)
    return img


def icon_prompt(img, d, x, y, lt):
    d.rounded_rectangle([x + 60, y + 70, x + 760, y + 170], radius=20, fill=(245, 246, 250), outline=(120, 130, 200), width=4)
    s = "이 주장의 근거를 검증해 줘"
    n = int(clamp((lt - 0.4) / 1.6) * len(s))
    d.text((x + 90, y + 120), s[:n] + ("|" if int(lt * 3) % 2 == 0 else ""), font=F(40, "R"), fill=(30, 30, 50), anchor="lm")
    d.text((x + 60, y + 40), "질문(프롬프트) 설계", font=F(30, "B"), fill=(90, 90, 160), anchor="lm")
    steps = ["질문 설계", "답변 비교", "출처 검증", "나의 결론"]
    for i, st in enumerate(steps):
        k = ease((lt - 1.6 - i * 0.35) / 0.3)
        bx = x + 70 + i * 180
        if k > 0:
            d.rounded_rectangle([bx, y + 300, bx + 150, y + 400], radius=16, fill=a((100, 110, 230), k)[:3])
            d.text((bx + 75, y + 350), st, font=F(28, "B"), fill=(255, 255, 255), anchor="mm")
            if i < 3:
                d.polygon([(bx + 155, y + 340), (bx + 175, y + 350), (bx + 155, y + 360)], fill=(100, 110, 230))
    # hand typing
    hy = y + 470 + 6 * math.sin(lt * 14)
    d.rounded_rectangle([x + 200, y + 450, x + 620, y + 560], radius=14, fill=(60, 60, 70))
    for r in range(3):
        for c in range(10):
            d.rounded_rectangle([x + 215 + c * 40, y + 462 + r * 32, x + 245 + c * 40, y + 486 + r * 32], radius=5, fill=(120, 120, 135))
    d.ellipse([x + 360, hy, x + 460, hy + 80], fill=(255, 205, 170))
    d.text((x + 410, y + 590), "정답이 아닌 '과정'을 평가", font=F(34, "B"), fill=(90, 90, 160), anchor="mm")


def icon_board(img, d, x, y, lt):
    d.rectangle([x + 60, y + 50, x + 760, y + 520], fill=(35, 90, 65), outline=(150, 100, 60), width=14)
    d.text((x + 410, y + 110), "우리 반 AI 활용 규칙", font=F(44, "EB"), fill=(255, 255, 255), anchor="mm")
    rules = ["1. 사용 내역은 투명하게 공개", "2. 출처와 사실을 꼭 확인", "3. 최종 판단은 나 스스로", "4. 무조건 금지 대신 윤리 교육"]
    for i, r in enumerate(rules):
        n = int(clamp((lt - 0.5 - i * 0.7) / 0.6) * len(r))
        d.text((x + 120, y + 200 + i * 75), r[:n], font=F(38, "R"), fill=(245, 245, 230), anchor="lm")
    d.rectangle([x + 620, y + 500, x + 700, y + 515], fill=(250, 250, 250))
    for i in range(3):
        bx = x + 200 + i * 210
        student(d, bx, y + 560, 0.55, body=[(240, 90, 90), (80, 160, 240), (250, 170, 50)][i], head=(255, 214, 180), smile=True, hair=(60, 40, 30),
                bob=4 * math.sin(lt * 8 + i))


def icon_idea(img, d, x, y, lt):
    cx, cy = x + 410, y + 250
    glow = 0.5 + 0.5 * math.sin(lt * 6)
    k = back((lt - 0.3) / 0.6)
    r = 120 * clamp(k, 0, 1.2)
    for i in range(12):
        ang = i * math.pi / 6 + lt * 0.5
        L1, L2 = r + 30, r + 70 + 20 * glow
        d.line([cx + L1 * math.cos(ang), cy + L1 * math.sin(ang), cx + L2 * math.cos(ang), cy + L2 * math.sin(ang)], fill=(255, 190, 40), width=10)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(255, 225, 90), outline=(240, 170, 20), width=6)
    d.rectangle([cx - 45, cy + r - 10, cx + 45, cy + r + 50], fill=(150, 150, 160))
    if k > 0.6:
        d.text((cx, cy), "?", font=F(150, "EB"), fill=(230, 120, 0), anchor="mm")
    # sketches
    for i, (lab, col) in enumerate([("왜?", (240, 90, 90)), ("만약에?", (80, 160, 240)), ("새로운 방법!", (100, 190, 110))]):
        kk = ease((lt - 1.2 - i * 0.4) / 0.4)
        if kk > 0:
            bx = x + 70 + i * 235
            d.rounded_rectangle([bx, y + 470, bx + 210, y + 560], radius=40, fill=col)
            d.text((bx + 105, y + 515), lab, font=F(34, "EB"), fill=(255, 255, 255), anchor="mm")
    d.text((cx, y + 600), "인간 고유의 질문하는 힘", font=F(34, "B"), fill=(200, 130, 0), anchor="mm")


def icon_mentor(img, d, x, y, lt):
    # teacher (taller) and student with tablet
    student(d, x + 260, y + 300, 1.5, body=(60, 90, 150), head=(255, 214, 180), smile=True, hair=(40, 30, 30))
    student(d, x + 520, y + 360, 1.1, body=(240, 120, 90), head=(255, 214, 180), smile=True, hair=(70, 45, 30), bob=3 * math.sin(lt * 5))
    d.rounded_rectangle([x + 400, y + 360, x + 600, y + 490], radius=16, fill=(30, 30, 40))
    d.rounded_rectangle([x + 412, y + 372, x + 588, y + 478], radius=8, fill=(130, 200, 255))
    d.line([x + 430, y + 450, x + 480, y + 410, x + 520, y + 430, x + 570, y + 390], fill=(255, 255, 255), width=6)
    if lt > 0.8:
        k = back((lt - 0.8) / 0.4)
        bw = 330 * clamp(k, 0, 1.1)
        d.rounded_rectangle([x + 60, y + 50, x + 60 + bw, y + 150], radius=30, fill=(255, 245, 200), outline=(230, 180, 60), width=4)
        if k > 0.8:
            d.text((x + 225, y + 100), "좋은 질문이야!", font=F(38, "EB"), fill=(150, 90, 0), anchor="mm")
    # paperwork shrinking
    shrink = ease((lt - 1.4) / 1.2)
    for i in range(int(7 * (1 - shrink)) + 1):
        d.rectangle([x + 640, y + 520 - i * 18, x + 760, y + 534 - i * 18], fill=(235, 235, 235), outline=(160, 160, 160))
    d.text((x + 700, y + 580), "행정 업무 ↓", font=F(30, "B"), fill=(200, 60, 60), anchor="mm")
    k = ease((lt - 2.0) / 0.5)
    d.text((x + 300, y + 590), "감시자  →  멘토", font=F(44, "EB"), fill=a((60, 90, 150), k)[:3] if k > 0 else (255, 255, 255), anchor="mm")


def icon_career(img, d, x, y, lt):
    base = y + 540
    collapse = ease((lt - 0.9) / 0.8)
    hs = [380, 320, 260, 200, 150, 100]
    for i, h in enumerate(hs):
        bx = x + 110 + i * 105
        fall = collapse * (1 + i * 0.15)
        hh = h * (1 - clamp(fall))
        d.rectangle([bx, base - hh, bx + 70, base], fill=(170, 170, 185))
        if fall < 0.5:
            d.text((bx + 35, base - hh - 25), f"{i + 1}등", font=F(26, "B"), fill=(110, 110, 130), anchor="mm")
    d.line([x + 80, base, x + 760, base], fill=(120, 120, 130), width=4)
    if lt < 1.6:
        d.text((x + 410, y + 80), "한 줄 세우기", font=F(44, "EB"), fill=(110, 110, 130), anchor="mm")
    items = [("디자인", (240, 90, 120)), ("과학", (80, 160, 240)), ("개발", (100, 190, 110)), ("예술", (170, 110, 220)), ("창업", (250, 160, 40)), ("돌봄", (60, 190, 190))]
    for i, (lab, col) in enumerate(items):
        k = ease((lt - 1.4 - i * 0.2) / 0.6)
        if k <= 0:
            continue
        ang = i / len(items) * 2 * math.pi + lt * 0.4
        cx = x + 410 + 260 * math.cos(ang) * k
        cy = y + 320 + 190 * math.sin(ang) * k - 10 * math.sin(lt * 3 + i)
        r = 70
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=col, outline=(255, 255, 255), width=5)
        d.text((cx, cy), lab, font=F(32, "EB"), fill=(255, 255, 255), anchor="mm")
    if lt > 1.8:
        d.text((x + 410, y + 320), "미래 역량", font=F(48, "EB"), fill=(60, 60, 90), anchor="mm")


def multi_scene(t, scene_idx, items):
    st = SC[scene_idx]["start"]
    subs = [s for s in SUBS if st - 0.01 <= s["start"] < SC[scene_idx]["end"]]
    starts = [st] + [s["start"] - 0.12 for s in subs[1:]]
    ends = starts[1:] + [SC[scene_idx]["end"]]
    g = st + t
    for i, (a0, a1) in enumerate(zip(starts, ends)):
        if g < a1 or i == len(starts) - 1:
            n, title, color, icon = items[i]
            return solution_frame(n, title, color, g - a0, a1 - a0, icon)


def scene4(t, dur):
    return multi_scene(t, 3, [(1, "과정 중심\n사고력 평가", (90, 100, 220), icon_prompt),
                              (2, "AI 윤리 교육\n정규화", (40, 150, 100), icon_board),
                              (3, "질문하는 힘·\n창의력 강화", (235, 150, 20), icon_idea)])


def scene5(t, dur):
    return multi_scene(t, 4, [(4, "교사는\n'학습 설계자·멘토'", (60, 110, 190), icon_mentor),
                              (5, "대입 제도의\n일관성 확보", (200, 70, 110), icon_career)])


def scene6(t, dur):
    img = grad((120, 190, 255), (255, 225, 170)).convert("RGBA")
    d = ImageDraw.Draw(img)
    # sun rays
    cx, cy = W // 2, 640
    for i in range(18):
        ang = i * math.pi / 9 + t * 0.15
        d.polygon([(cx, cy), (cx + 1400 * math.cos(ang - 0.06), cy + 1400 * math.sin(ang - 0.06)),
                   (cx + 1400 * math.cos(ang + 0.06), cy + 1400 * math.sin(ang + 0.06))], fill=(255, 245, 210))
    zoom = 1 + 0.08 * ease(t / dur)
    s = 3.0 * zoom
    # student close-up (big)
    hx, hy = W // 2, 600
    d.rounded_rectangle([hx - 230 * s / 3 * 2, hy + 120, hx + 230 * s / 3 * 2, hy + 700], radius=150, fill=(80, 150, 230))
    R = 200 * zoom
    d.ellipse([hx - R, hy - R, hx + R, hy + R], fill=(255, 214, 180))
    d.chord([hx - R - 10, hy - R - 25, hx + R + 10, hy + R * 0.2], 180, 360, fill=(60, 40, 30))
    blink = 1 if (t % 3.0) > 0.12 else 0.15
    for ex in (-70, 70):
        d.ellipse([hx + ex * zoom - 16, hy + 10 - 20 * blink, hx + ex * zoom + 16, hy + 10 + 20 * blink], fill=(40, 30, 30))
    d.chord([hx - 80 * zoom, hy + 40, hx + 80 * zoom, hy + 140 * zoom], 0, 180, fill=(200, 70, 70))
    d.ellipse([hx - 150 * zoom, hy + 60, hx - 100 * zoom, hy + 95], fill=(255, 170, 160))
    d.ellipse([hx + 100 * zoom, hy + 60, hx + 150 * zoom, hy + 95], fill=(255, 170, 160))
    # AI orb in hand, nodes orbiting
    ox, oy = hx + 420, hy + 160
    pulse = 0.5 + 0.5 * math.sin(t * 4)
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(glow).ellipse([ox - 150, oy - 150, ox + 150, oy + 150], fill=(120, 220, 255, int(120 + 80 * pulse)))
    img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(40)))
    d = ImageDraw.Draw(img)
    d.ellipse([ox - 80, oy - 80, ox + 80, oy + 80], fill=(90, 200, 255), outline=(255, 255, 255), width=6)
    d.text((ox, oy), "AI", font=F(64, "EB"), fill=(255, 255, 255), anchor="mm")
    for i in range(5):
        ang = t * 1.2 + i * 2 * math.pi / 5
        nx, ny = ox + 150 * math.cos(ang), oy + 90 * math.sin(ang)
        d.line([ox, oy, nx, ny], fill=(255, 255, 255), width=3)
        d.ellipse([nx - 14, ny - 14, nx + 14, ny + 14], fill=(255, 255, 255))
    d.ellipse([ox - 60, oy + 70, ox + 40, oy + 130], fill=(255, 214, 180))  # hand
    # caption
    k = ease((t - 0.6) / 0.6)
    overlay(img, lambda o: o.rounded_rectangle([W / 2 - 860, 60, W / 2 + 860, 260], radius=30, fill=(255, 255, 255, int(215 * k))))
    d = ImageDraw.Draw(img)
    d.text((W // 2, 120), "기술을 지배하는 '주체적 인간'", font=F(72, "EB"), fill=a((30, 70, 160), k)[:3] if k > 0.05 else (255, 255, 255), anchor="mm")
    if t > 1.2:
        k2 = ease((t - 1.2) / 0.6)
        d.text((W // 2, 210), "그것이 진짜 AI 교육의 답입니다.", font=F(52, "B"), fill=mix((255, 255, 255), (60, 60, 80), k2), anchor="mm")
    # source
    d.text((W - 40, H - 30), "출처: 손기서 전 강서양천교육장 칼럼", font=F(28, "R"), fill=(70, 70, 90), anchor="rd")
    # end fade
    fo = clamp((t - (dur - 1.0)) / 1.0)
    if fo > 0:
        overlay(img, lambda o: o.rectangle([0, 0, W, H], fill=(0, 0, 0, int(255 * fo))))
    return img


SCENES = [scene1, scene2, scene3, scene4, scene5, scene6]


def wrap(text, font, maxw, d):
    words, lines, cur = text.split(" "), [], ""
    for w in words:
        test = (cur + " " + w).strip()
        if d.textlength(test, font=font) > maxw and cur:
            lines.append(cur)
            cur = w
        else:
            cur = test
    lines.append(cur)
    return lines


def subtitles(img, g):
    for s in SUBS:
        if s["start"] - 0.05 <= g <= s["end"] + 0.05:
            d = ImageDraw.Draw(img)
            fnt = F(42, "RB")
            lines = wrap(s["text"], fnt, 1500, d)
            lh = 58
            hgt = lh * len(lines) + 30
            y0 = H - 60 - hgt
            ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            od = ImageDraw.Draw(ov)
            mw = max(d.textlength(l, font=fnt) for l in lines)
            od.rounded_rectangle([W / 2 - mw / 2 - 40, y0, W / 2 + mw / 2 + 40, y0 + hgt], radius=18, fill=(0, 0, 0, 165))
            for i, l in enumerate(lines):
                od.text((W / 2, y0 + 15 + lh * i + lh / 2), l, font=fnt, fill=(255, 255, 255, 255), anchor="mm")
            img.alpha_composite(ov)
            return


def frame(g):
    for i, sc in enumerate(SC):
        if g < sc["end"] or i == len(SC) - 1:
            t = g - sc["start"]
            img = SCENES[i](t, sc["end"] - sc["start"])
            # short flash at scene cuts
            if i > 0 and t < 0.12:
                overlay(img, lambda o: o.rectangle([0, 0, W, H], fill=(255, 255, 255, int(200 * (1 - t / 0.12)))))
            break
    if img.mode != "RGBA":
        img = img.convert("RGBA")
    if g < SC[-1]["end"] - 1.0:
        subtitles(img, g)
    return img.convert("RGB")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "preview":
        for g in [float(x) for x in sys.argv[2:]]:
            frame(g).save(f"prev_{g:05.1f}.png")
        sys.exit()
    part, nparts = int(sys.argv[1]), int(sys.argv[2])
    N = int(math.ceil(TOTAL * FPS))
    lo, hi = part * N // nparts, (part + 1) * N // nparts
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                          "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", f"part{part}.mp4"],
                         stdin=subprocess.PIPE)
    for f in range(lo, hi):
        p.stdin.write(frame(f / FPS).tobytes())
    p.stdin.close()
    p.wait()
