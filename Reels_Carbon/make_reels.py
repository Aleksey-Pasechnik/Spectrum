import math
import os
import subprocess
import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1080, 1920
FPS = 30
ROOT = r"c:\Users\Aleksey\Documents\ANTIGRAVITY\liquid-hires-player\Reels_Carbon"
FRAMES_DIR = os.path.join(ROOT, "frames")
OUT_MP4 = os.path.join(ROOT, "Spectrum_Carbon_Reels.mp4")

FONT_BOLD = r"C:\Windows\Fonts\segoeuib.ttf"
FONT_REG  = r"C:\Windows\Fonts\segoeui.ttf"

def load_font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()

F_HERO = load_font(FONT_BOLD, 88)
F_TITLE = load_font(FONT_BOLD, 58)
F_BADGE = load_font(FONT_BOLD, 30)
F_SUB = load_font(FONT_REG, 36)
F_URL = load_font(FONT_BOLD, 38)
F_SM = load_font(FONT_REG, 28)

def trim_alpha(img, pad=8):
    bbox = img.split()[-1].getbbox()
    if not bbox:
        return img
    x0, y0, x1, y1 = bbox
    x0 = max(0, x0 - pad); y0 = max(0, y0 - pad)
    x1 = min(img.width, x1 + pad); y1 = min(img.height, y1 + pad)
    return img.crop((x0, y0, x1, y1))

def make_carbon_bg():
    bg = Image.new("RGB", (W, H), (9, 10, 16))
    draw = ImageDraw.Draw(bg)
    # Диагональная карбоновая текстура
    for y in range(0, H, 8):
        col = (13, 14, 22) if (y // 8) % 2 == 0 else (8, 9, 14)
        draw.line([(0, y), (W, y)], fill=col, width=2)
    # Мягкое золотисто-малиновое свечение сверху и снизу (Carbon accent)
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([W//2 - 520, -260, W//2 + 520, 620], fill=(212, 168, 72, 42))
    gd.ellipse([-220, H - 720, W + 220, H + 260], fill=(224, 52, 118, 48))
    gd.ellipse([W - 440, H//2 - 360, W + 320, H//2 + 400], fill=(52, 210, 238, 28))
    glow = glow.filter(ImageFilter.GaussianBlur(120))
    bg = Image.alpha_composite(bg.convert("RGBA"), glow).convert("RGB")
    return bg

BASE_BG = make_carbon_bg()

SCENES = [
    {
        "file": "01_carbon_eq.png",
        "dur": 3.2,
        "badge": "SPECTRUM  •  CARBON EDITION",
        "title": "4 МБ НАТИВНОГО C++20",
        "sub": "Вместо 300-мегабайтных комбайнов.\nМгновенный старт и 0% лагов.",
        "accent": (235, 192, 86),
        "max_w": 840, "max_h": 1120,
    },
    {
        "file": "02_carbon_fft.png",
        "dur": 3.0,
        "badge": "ЖИВОЙ FFT-АНАЛИЗАТОР",
        "title": "ДЕТЕКТОР ФЕЙК HI-RES",
        "sub": "Мгновенно показывает реальный срез:\n16 кГц MP3 или честный Hi-Res.",
        "accent": (240, 72, 148),
        "max_w": 840, "max_h": 1120,
    },
    {
        "file": "03_carbon_master.png",
        "dur": 3.4,
        "badge": "СТУДИЙНЫЙ МАСТЕР-ТРАКТ",
        "title": "PURE AUDIO & DSD512",
        "sub": "WASAPI Exclusive • ASIO • PCM → DSD\nВосстановление динамики (+DR) и фазометр.",
        "accent": (64, 232, 188),
        "max_w": 940, "max_h": 1100,
    },
    {
        "file": "04_carbon_effects.png",
        "dur": 3.0,
        "badge": "ДИЗАЙН И АТМОСФЕРА",
        "title": "6 ТЕМ • 8 СКИНОВ",
        "sub": "Carbon • Cyberpunk • Liquid Glass • AMOLED\nЖивой винил, дождь, неон и шейдеры.",
        "accent": (176, 118, 255),
        "max_w": 940, "max_h": 1100,
    },
    {
        "file": "05_carbon_island.png",
        "dur": 2.6,
        "badge": "РЕЖИМ МИНИ-КАПСУЛЫ",
        "title": "ДИНАМИЧЕСКИЙ ОСТРОВОК",
        "sub": "Невесомое управление поверх игр и окон.\nФормат, битрейт и эквалайзер всегда на виду.",
        "accent": (78, 222, 248),
        "max_w": 960, "max_h": 360,
    },
    {
        "file": "06_carbon_library.png",
        "dur": 3.2,
        "badge": "БИБЛИОТЕКА И СТРИМИНГ",
        "title": "28 LOSSLESS FLAC-РАДИО",
        "sub": "24-bit Hi-Res • Рок • Джаз • Электроника\nБыстрая медиатека и умные плейлисты.",
        "accent": (235, 192, 86),
        "max_w": 1000, "max_h": 820,
    },
    {
        "file": None,
        "dur": 3.0,
        "badge": "WINDOWS 10 / 11  •  БЕСПЛАТНО",
        "title": "SPECTRUM 2.1",
        "sub": "4.4 МБ • Проверено антивирусом\nАвтообновления • 4 языка\n\ngithub.com/Aleksey-Pasechnik/Spectrum",
        "accent": (235, 192, 86),
        "max_w": 0, "max_h": 0,
    },
]

# Предзагружаем и обрезаем изображения
LOADED = {}
for sc in SCENES:
    fn = sc["file"]
    if fn:
        im = Image.open(os.path.join(FRAMES_DIR, fn)).convert("RGBA")
        im = trim_alpha(im, pad=6)
        LOADED[fn] = im

def ease_out_cubic(t):
    t = max(0.0, min(1.0, t))
    return 1.0 - (1.0 - t) ** 3

def draw_centered_text(draw, y, text, font, fill, line_spacing=12):
    lines = text.split("\n")
    cur_y = y
    for ln in lines:
        bbox = draw.textbbox((0, 0), ln, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        draw.text(((W - tw) // 2, cur_y), ln, font=font, fill=fill)
        cur_y += th + line_spacing

def render_scene_frame(sc, local_t, global_t):
    frame = BASE_BG.copy().convert("RGBA")
    draw = ImageDraw.Draw(frame)
    dur = sc["dur"]
    p = local_t / max(0.001, dur)
    enter = ease_out_cubic(min(1.0, local_t / 0.45))
    accent = sc["accent"]

    # Верхняя тонкая неоновая полоска прогресса всего ролика
    total_dur = sum(s["dur"] for s in SCENES)
    prog_w = int(W * min(1.0, global_t / total_dur))
    draw.rectangle([0, 0, prog_w, 8], fill=accent + (255,))

    # Анимированные полоски карбонового эквалайзера в самом низу (под стиль плеера!)
    bars = 28
    bar_w = 18
    gap = 14
    start_x = (W - (bars * bar_w + (bars - 1) * gap)) // 2
    base_y = H - 96
    for i in range(bars):
        amp = 0.25 + 0.75 * abs(math.sin(global_t * 5.2 + i * 0.48) * math.cos(global_t * 2.1 - i * 0.22))
        bh = int(14 + amp * 58)
        bx = start_x + i * (bar_w + gap)
        draw.rounded_rectangle([bx, base_y - bh, bx + bar_w, base_y], radius=6, fill=accent + (185,))

    if sc["file"] is not None:
        # Верхняя пилюля-бейдж
        y_off = int((1.0 - enter) * 42)
        b_txt = sc["badge"]
        bb = draw.textbbox((0, 0), b_txt, font=F_BADGE)
        bw, bh = bb[2] - bb[0], bb[3] - bb[1]
        px0 = (W - bw) // 2 - 28
        py0 = 128 + y_off
        draw.rounded_rectangle([px0, py0, px0 + bw + 56, py0 + bh + 22], radius=24, fill=(24, 26, 42, 220), outline=accent + (210,), width=2)
        draw.text(((W - bw) // 2, py0 + 9), b_txt, font=F_BADGE, fill=accent + (255,))

        # Заголовок
        draw_centered_text(draw, 212 + y_off, sc["title"], F_TITLE, (248, 250, 255, 255))

        # Главный скриншот с плавным Ken Burns зумом + мягкой тенью
        src = LOADED[sc["file"]]
        scale0 = min(sc["max_w"] / src.width, sc["max_h"] / src.height)
        zoom = 1.0 + 0.055 * p
        sc_f = scale0 * (0.94 + 0.06 * enter) * zoom
        nw, nh = max(1, int(src.width * sc_f)), max(1, int(src.height * sc_f))
        im_r = src.resize((nw, nh), Image.Resampling.LANCZOS)

        cx = W // 2
        cy = 960 + int((1.0 - enter) * 55)
        ix, iy = cx - nw // 2, cy - nh // 2

        # Неоновая рамка-ореол позади скриншота
        draw.rounded_rectangle([ix - 6, iy - 6, ix + nw + 6, iy + nh + 6], radius=26, outline=accent + (110,), width=3)
        frame.alpha_composite(im_r, (ix, iy))

        # Нижний подзаголовок
        draw_centered_text(draw, H - 310 + int((1.0 - enter) * 28), sc["sub"], F_SUB, (206, 216, 238, 255), line_spacing=14)
    else:
        # Финальный экран CTA
        y_off = int((1.0 - enter) * 50)
        b_txt = sc["badge"]
        bb = draw.textbbox((0, 0), b_txt, font=F_BADGE)
        bw, bh = bb[2] - bb[0], bb[3] - bb[1]
        px0 = (W - bw) // 2 - 30
        py0 = 640 + y_off
        draw.rounded_rectangle([px0, py0, px0 + bw + 60, py0 + bh + 24], radius=26, fill=(24, 26, 42, 230), outline=accent + (230,), width=2)
        draw.text(((W - bw) // 2, py0 + 10), b_txt, font=F_BADGE, fill=accent + (255,))

        draw_centered_text(draw, 740 + y_off, sc["title"], F_HERO, (255, 255, 255, 255))
        draw_centered_text(draw, 880 + y_off, sc["sub"], F_URL, (215, 226, 250, 255), line_spacing=18)

        # Кнопка CTA
        cta = "⬇  СКАЧАТЬ НА GITHUB"
        cb = draw.textbbox((0, 0), cta, font=F_URL)
        cw, ch = cb[2] - cb[0], cb[3] - cb[1]
        bx0 = (W - cw) // 2 - 44
        by0 = 1230 + y_off
        draw.rounded_rectangle([bx0, by0, bx0 + cw + 88, by0 + ch + 36], radius=34, fill=(132, 74, 240, 240), outline=accent + (255,), width=3)
        draw.text(((W - cw) // 2, by0 + 16), cta, font=F_URL, fill=(255, 255, 255, 255))

    # Мягкое затемнение на стыках сцен (fade in / fade out 0.25s)
    fade = 1.0
    if local_t < 0.25:
        fade = local_t / 0.25
    elif dur - local_t < 0.25:
        fade = (dur - local_t) / 0.25
    if fade < 0.999:
        dark = Image.new("RGBA", (W, H), (8, 9, 14, int((1.0 - max(0.0, fade)) * 255)))
        frame = Image.alpha_composite(frame, dark)

    return frame.convert("RGB")

def main():
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    cmd = [
        ffmpeg, "-y",
        "-f", "rawvideo", "-vcodec", "rawvideo",
        "-s", f"{W}x{H}", "-pix_fmt", "rgb24", "-r", str(FPS),
        "-i", "-",
        "-c:v", "libx264", "-preset", "fast", "-crf", "20",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart",
        OUT_MP4,
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
    global_t = 0.0
    total_frames = 0
    for sc in SCENES:
        n_frames = int(round(sc["dur"] * FPS))
        for f in range(n_frames):
            local_t = f / FPS
            img = render_scene_frame(sc, local_t, global_t)
            proc.stdin.write(img.tobytes())
            global_t += 1.0 / FPS
            total_frames += 1
    proc.stdin.close()
    rc = proc.wait()
    print(f"REELS_EXIT:{rc} FRAMES:{total_frames} SIZE:{os.path.getsize(OUT_MP4) if os.path.exists(OUT_MP4) else 0}")

if __name__ == "__main__":
    main()
