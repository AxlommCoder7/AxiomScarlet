# -----------------------------------------------
# 🔸 AxiomMusic Project - WORKING Thumbnail
# 🔹 Simple + No errors
# -----------------------------------------------

import os
import re
import random
import aiofiles
import aiohttp
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageEnhance
from py_yt import VideosSearch
from config import YOUTUBE_IMG_URL

CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)

# ===== LAYOUT =====
CARD_W, CARD_H = 980, 470
CARD_X = (1280 - CARD_W) // 2
CARD_Y = (720 - CARD_H) // 2
CARD_RADIUS = 55

THUMB_SIZE = 350
THUMB_X = CARD_X + 75
THUMB_Y = CARD_Y + 70
THUMB_RADIUS = 35

TITLE_X = THUMB_X + THUMB_SIZE + 55
TITLE_Y = CARD_Y + 90
META_Y = TITLE_Y + 55

BAR_WIDTH = 480
BAR_HEIGHT = 5
BAR_X = TITLE_X
BAR_Y = META_Y + 70

CONTROLS_Y = BAR_Y + 70
CONTROLS_X = TITLE_X + 30

MAX_TITLE_WIDTH = 520


def trim_text(text, font, max_width):
    try:
        if font.getlength(text) <= max_width:
            return text
        for i in range(len(text) - 1, 0, -1):
            if font.getlength(text[:i] + "…") <= max_width:
                return text[:i] + "…"
        return "…"
    except:
        return text[:50] + "..."


def get_random_color():
    """Generate random vibrant color"""
    return (
        random.randint(100, 255),
        random.randint(100, 255),
        random.randint(100, 255)
    )


def draw_glow_border(draw, size, radius, color, thickness=20, blur=30):
    """Draw glowing border"""
    try:
        w, h = size
        # Create glow layer
        glow = Image.new("RGBA", (w + 100, h + 100), (0, 0, 0, 0))
        gdraw = ImageDraw.Draw(glow)
        
        # Multiple layers for glow effect
        for i in range(thickness, 0, -2):
            alpha = int(150 * (1 - i/thickness))
            gdraw.rounded_rectangle(
                [i, i, w + 100 - i, h + 100 - i],
                radius=radius + i,
                outline=(*color, alpha),
                width=2
            )
        
        glow = glow.filter(ImageFilter.GaussianBlur(blur))
        return glow
    except:
        return None


# ===== SIMPLE ICONS =====

def draw_icon_shuffle(draw, x, y, color):
    try:
        draw.line([(x, y+10), (x+15, y)], fill=color, width=2)
        draw.line([(x, y+20), (x+15, y+30)], fill=color, width=2)
        draw.line([(x+5, y), (x+20, y)], fill=color, width=2)
        draw.line([(x+5, y+30), (x+20, y+30)], fill=color, width=2)
    except: pass

def draw_icon_repeat(draw, x, y, color):
    try:
        draw.arc([(x, y), (x+30, y+25)], 180, 360, fill=color, width=2)
        draw.arc([(x, y+5), (x+30, y+30)], 0, 180, fill=color, width=2)
    except: pass

def draw_icon_prev(draw, x, y, color):
    try:
        draw.polygon([(x+20, y), (x+20, y+30), (x, y+15)], fill=color)
        draw.rectangle([(x+22, y+5), (x+26, y+25)], fill=color)
    except: pass

def draw_icon_pause(draw, x, y, color):
    try:
        draw.rectangle([(x, y+5), (x+10, y+25)], fill=color)
        draw.rectangle([(x+20, y+5), (x+30, y+25)], fill=color)
    except: pass

def draw_icon_next(draw, x, y, color):
    try:
        draw.rectangle([(x, y+5), (x+4, y+25)], fill=color)
        draw.polygon([(x+8, y), (x+8, y+30), (x+28, y+15)], fill=color)
    except: pass

def draw_icon_heart(draw, x, y, color):
    try:
        draw.ellipse([(x+2, y+8), (x+12, y+18)], fill=color)
        draw.ellipse([(x+10, y+8), (x+20, y+18)], fill=color)
        draw.polygon([(x+3, y+13), (x+19, y+13), (x+11, y+25)], fill=color)
    except: pass

def draw_icon_headphones(draw, x, y, color):
    try:
        draw.arc([(x+5, y), (x+25, y+20)], 180, 0, fill=color, width=2)
        draw.ellipse([(x, y+18), (x+10, y+28)], fill=color)
        draw.ellipse([(x+20, y+18), (x+30, y+28)], fill=color)
    except: pass


# ===== MAIN =====

async def get_thumb(videoid: str) -> str:
    cache_path = os.path.join(CACHE_DIR, f"{videoid}_final.png")
    thumb_path = os.path.join(CACHE_DIR, f"thumb_{videoid}.png")

    print(f"🎨 Generating thumbnail for: {videoid}")

    # Fetch data
    try:
        results = VideosSearch(f"https://www.youtube.com/watch?v={videoid}", limit=1)
        results_data = await results.next()
        result_items = results_data.get("result", [])
        if not result_items:
            raise ValueError("No results")
        data = result_items[0]
        title = re.sub(r"\W+", " ", data.get("title", "Unsupported Title")).title()
        thumbnail_url = data.get("thumbnails", [{}])[0].get("url", YOUTUBE_IMG_URL)
        duration = data.get("duration")
        views = data.get("viewCount", {}).get("short", "Unknown Views")
        channel = data.get("channel", {}).get("name", "YouTube")
        print("✓ Data fetched")
    except Exception as e:
        print(f"❌ Fetch error: {e}")
        return YOUTUBE_IMG_URL

    is_live = not duration or str(duration).strip().lower() in {"", "live", "live now"}
    duration_text = "LIVE" if is_live else (duration or "Unknown")

    # Download thumbnail
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(thumbnail_url, timeout=10) as resp:
                if resp.status == 200:
                    async with aiofiles.open(thumb_path, "wb") as f:
                        await f.write(await resp.read())
                    print("✓ Thumbnail downloaded")
                else:
                    return YOUTUBE_IMG_URL
    except Exception as e:
        print(f"❌ Download error: {e}")
        return YOUTUBE_IMG_URL

    try:
        # Random colors
        card_color = get_random_color()
        thumb_color = get_random_color()
        print(f"🎨 Card color: {card_color}, Thumb color: {thumb_color}")

        # === BACKGROUND ===
        base = Image.open(thumb_path).convert("RGBA")
        base = base.resize((1280, 720), Image.LANCZOS)
        base = ImageEnhance.Brightness(base).enhance(1.35)
        base = ImageEnhance.Contrast(base).enhance(1.15)
        bg = base.filter(ImageFilter.GaussianBlur(8))
        dark = Image.new("RGBA", bg.size, (0, 0, 0, 70))
        bg = Image.alpha_composite(bg, dark)
        print("✓ Background created")

        # === CARD: TRANSPARENT + HIGH BLUR ===
        card_area = bg.crop((CARD_X, CARD_Y, CARD_X + CARD_W, CARD_Y + CARD_H))
        card_area = card_area.filter(ImageFilter.GaussianBlur(30))
        card = card_area.convert("RGBA")

        mask = Image.new("L", (CARD_W, CARD_H), 0)
        ImageDraw.Draw(mask).rounded_rectangle((0, 0, CARD_W, CARD_H), radius=CARD_RADIUS, fill=255)
        bg.paste(card, (CARD_X, CARD_Y), mask)
        print("✓ Card created")

        # === CARD GLOW BORDER ===
        card_glow = draw_glow_border(
            ImageDraw.Draw(Image.new("RGBA", (CARD_W + 100, CARD_H + 100), (0,0,0,0))),
            (CARD_W, CARD_H), CARD_RADIUS, card_color, thickness=20, blur=30
        )
        if card_glow:
            bg.paste(card_glow, (CARD_X - 50, CARD_Y - 50), card_glow)
            print("✓ Card glow applied")

        # === THUMBNAIL ===
        thumb_img = Image.open(thumb_path).convert("RGBA")
        thumb_img = thumb_img.resize((THUMB_SIZE, THUMB_SIZE), Image.LANCZOS)
        thumb_img = ImageEnhance.Brightness(thumb_img).enhance(1.1)

        # Shadow
        shadow = Image.new("RGBA", (1280, 720), (0, 0, 0, 0))
        sd = ImageDraw.Draw(shadow)
        sd.rounded_rectangle(
            (THUMB_X - 10, THUMB_Y - 10,
             THUMB_X + THUMB_SIZE + 10, THUMB_Y + THUMB_SIZE + 10),
            radius=THUMB_RADIUS + 12, fill=(0, 0, 0, 130)
        )
        shadow = shadow.filter(ImageFilter.GaussianBlur(18))
        bg = Image.alpha_composite(bg.convert("RGBA"), shadow)

        # Thumb glow
        thumb_glow = draw_glow_border(
            ImageDraw.Draw(Image.new("RGBA", (THUMB_SIZE + 100, THUMB_SIZE + 100), (0,0,0,0))),
            (THUMB_SIZE, THUMB_SIZE), THUMB_RADIUS, thumb_color, thickness=15, blur=25
        )
        if thumb_glow:
            bg.paste(thumb_glow, (THUMB_X - 50, THUMB_Y - 50), thumb_glow)

        thumb_mask = Image.new("L", (THUMB_SIZE, THUMB_SIZE), 0)
        ImageDraw.Draw(thumb_mask).rounded_rectangle(
            (0, 0, THUMB_SIZE, THUMB_SIZE), radius=THUMB_RADIUS, fill=255
        )
        bg.paste(thumb_img, (THUMB_X, THUMB_Y), thumb_mask)
        print("✓ Thumbnail created")

        # === TEXT ===
        draw = ImageDraw.Draw(bg)

        try:
            title_font = ImageFont.truetype("AxiomMuzic/assets/assets/font2.ttf", 40)
            meta_font = ImageFont.truetype("AxiomMuzic/assets/assets/font.ttf", 22)
            time_font = ImageFont.truetype("AxiomMuzic/assets/assets/font.ttf", 19)
        except:
            title_font = ImageFont.load_default()
            meta_font = title_font
            time_font = title_font

        trimmed = trim_text(title, title_font, MAX_TITLE_WIDTH)
        draw.text((TITLE_X, TITLE_Y), trimmed, fill="white", font=title_font)
        draw.text((TITLE_X, META_Y), channel, fill=(190, 190, 190), font=meta_font)

        # === PROGRESS BAR ===
        bar_end = BAR_X + BAR_WIDTH
        progress = int(BAR_WIDTH * 0.35)

        draw.rounded_rectangle(
            [(BAR_X, BAR_Y), (bar_end, BAR_Y + BAR_HEIGHT)],
            radius=3, fill=(85, 85, 85)
        )
        draw.rounded_rectangle(
            [(BAR_X, BAR_Y), (BAR_X + progress, BAR_Y + BAR_HEIGHT)],
            radius=3, fill=card_color
        )

        cx, cy = BAR_X + progress, BAR_Y + BAR_HEIGHT // 2
        draw.ellipse([(cx - 7, cy - 7), (cx + 7, cy + 7)], fill="white")

        draw.text((BAR_X, BAR_Y + 17), "01:17", fill="white", font=time_font)
        total = duration_text if not is_live else "3:46"
        draw.text((bar_end - 40, BAR_Y + 17), total, fill="white", font=time_font)

        # === CONTROLS ===
        icon_y = CONTROLS_Y
        sx = CONTROLS_X
        gap = 45

        draw_icon_shuffle(draw, sx, icon_y, thumb_color)
        draw_icon_repeat(draw, sx + gap, icon_y, thumb_color)
        draw_icon_prev(draw, sx + gap * 2, icon_y, "white")
        draw_icon_pause(draw, sx + gap * 3, icon_y, "white")
        draw_icon_next(draw, sx + gap * 4, icon_y, "white")
        draw_icon_heart(draw, sx + gap * 5, icon_y, thumb_color)
        draw_icon_headphones(draw, sx + gap * 6, icon_y, "white")
        print("✓ Controls added")

        # === SAVE ===
        bg = bg.convert("RGB")
        bg.save(cache_path, "PNG", quality=95)
        print(f"✓ Thumbnail saved: {cache_path}")

    except Exception as e:
        import traceback
        print(f"❌ Error: {e}")
        traceback.print_exc()
        return YOUTUBE_IMG_URL
    finally:
        try:
            if os.path.exists(thumb_path):
                os.remove(thumb_path)
        except OSError:
            pass

    return cache_path
