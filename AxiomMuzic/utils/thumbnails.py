# -----------------------------------------------
# 🔸 AxiomMusic Project - SIMPLE & RELIABLE
# 🔹 Developed & Maintained by: Axiom Bots
# -----------------------------------------------

import os
import re
import aiofiles
import aiohttp
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageEnhance
from py_yt import VideosSearch
from config import YOUTUBE_IMG_URL

CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)

# ===== SAFE LAYOUT VALUES =====
CARD_W, CARD_H = 980, 470
CARD_X = (1280 - CARD_W) // 2
CARD_Y = (720 - CARD_H) // 2
CARD_RADIUS = 45  # Safe value

THUMB_SIZE = 320
THUMB_X = CARD_X + 55
THUMB_Y = CARD_Y + 65
THUMB_RADIUS = 30  # Safe value

TITLE_X = THUMB_X + THUMB_SIZE + 60
TITLE_Y = CARD_Y + 90
META_Y = TITLE_Y + 50

BAR_Y = META_Y + 55
BAR_X = TITLE_X
BAR_WIDTH = 510
BAR_HEIGHT = 5

PILL_W = 360
PILL_H = 90  # Height increased
PILL_RADIUS = 35  # Radius < PILL_H/2
PILL_X = TITLE_X + 150
PILL_Y = BAR_Y + 45

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


def create_rainbow_glow(size, radius, thickness=16, blur_amount=40):
    """Simple rainbow glow"""
    try:
        w, h = size
        pad = 100
        canvas = Image.new("RGBA", (w + pad * 2, h + pad * 2), (0, 0, 0, 0))
        draw = ImageDraw.Draw(canvas)

        colors = [
            (255, 50, 130), (200, 50, 220), (120, 80, 255),
            (60, 150, 255), (40, 220, 200), (80, 240, 120),
            (180, 240, 60), (255, 200, 50), (255, 120, 50),
        ]

        num_layers = thickness * 4
        for i in range(num_layers):
            color = colors[i % len(colors)]
            alpha = 200 if i < num_layers // 2 else 100
            offset = pad + i * 0.6
            layer_r = radius + thickness - i * 0.6
            
            if layer_r < 10:
                break

            draw.rounded_rectangle(
                (int(offset), int(offset),
                 int(w + pad * 2 - offset), int(h + pad * 2 - offset)),
                radius=int(layer_r),
                outline=color + (alpha,),
                width=2
            )

        glow = canvas.filter(ImageFilter.GaussianBlur(blur_amount))

        # Sharp border
        sharp = Image.new("RGBA", (w + pad * 2, h + pad * 2), (0, 0, 0, 0))
        sd = ImageDraw.Draw(sharp)
        sharp_colors = [(255, 50, 130), (120, 80, 255), (40, 220, 200)]
        for i in range(3):
            c = sharp_colors[i]
            offset = pad + thickness + i
            sd.rounded_rectangle(
                (int(offset), int(offset),
                 int(w + pad * 2 - offset), int(h + pad * 2 - offset)),
                radius=int(radius - i),
                outline=c + (255,),
                width=1
            )

        return glow, sharp
    except Exception as e:
        print(f"Glow error: {e}")
        img = Image.new("RGBA", (size[0] + 200, size[1] + 200), (0, 0, 0, 0))
        return img, img


async def get_thumb(videoid: str) -> str:
    cache_path = os.path.join(CACHE_DIR, f"{videoid}_final.png")
    if os.path.exists(cache_path):
        return cache_path

    thumb_path = os.path.join(CACHE_DIR, f"thumb_{videoid}.png")

    try:
        # Fetch data
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
        
    except Exception as e:
        print(f"Fetch error: {e}")
        title, thumbnail_url, duration, views, channel = (
            "Unsupported Title", YOUTUBE_IMG_URL, None, "Unknown Views", "YouTube"
        )

    is_live = not duration or str(duration).strip().lower() in {"", "live", "live now"}
    duration_text = "LIVE" if is_live else (duration or "Unknown")

    # Download thumbnail
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(thumbnail_url, timeout=10) as resp:
                if resp.status == 200:
                    async with aiofiles.open(thumb_path, "wb") as f:
                        await f.write(await resp.read())
                else:
                    return YOUTUBE_IMG_URL
    except Exception as e:
        print(f"Download error: {e}")
        return YOUTUBE_IMG_URL

    try:
        # BACKGROUND
        base = Image.open(thumb_path).convert("RGBA")
        base = base.resize((1280, 720), Image.LANCZOS)
        base = ImageEnhance.Brightness(base).enhance(1.35)
        base = ImageEnhance.Contrast(base).enhance(1.15)
        bg = base.filter(ImageFilter.GaussianBlur(6))
        dark = Image.new("RGBA", bg.size, (0, 0, 0, 50))
        bg = Image.alpha_composite(bg, dark)

        # CARD - LIGHT TRANSPARENT
        card_area = bg.crop((CARD_X, CARD_Y, CARD_X + CARD_W, CARD_Y + CARD_H))
        card_area = card_area.filter(ImageFilter.GaussianBlur(10))
        frosted = Image.new("RGBA", (CARD_W, CARD_H), (240, 240, 245, 120))
        card = Image.alpha_composite(card_area, frosted)

        mask = Image.new("L", (CARD_W, CARD_H), 0)
        ImageDraw.Draw(mask).rounded_rectangle((0, 0, CARD_W, CARD_H), radius=CARD_RADIUS, fill=255)
        bg.paste(card, (CARD_X, CARD_Y), mask)

        # CARD GLOW
        card_glow, card_sharp = create_rainbow_glow(
            (CARD_W, CARD_H), CARD_RADIUS, thickness=16, blur_amount=40
        )
        bg.paste(card_glow, (CARD_X - 100, CARD_Y - 100), card_glow)
        bg.paste(card_sharp, (CARD_X - 100, CARD_Y - 100), card_sharp)

        # THUMBNAIL
        thumb_img = Image.open(thumb_path).convert("RGBA")
        thumb_img = thumb_img.resize((THUMB_SIZE, THUMB_SIZE), Image.LANCZOS)
        thumb_img = ImageEnhance.Brightness(thumb_img).enhance(1.1)

        thumb_mask = Image.new("L", (THUMB_SIZE, THUMB_SIZE), 0)
        ImageDraw.Draw(thumb_mask).rounded_rectangle(
            (0, 0, THUMB_SIZE, THUMB_SIZE), radius=THUMB_RADIUS, fill=255
        )

        # Shadow
        shadow = Image.new("RGBA", (1280, 720), (0, 0, 0, 0))
        sd = ImageDraw.Draw(shadow)
        sd.rounded_rectangle(
            (THUMB_X - 10, THUMB_Y - 10,
             THUMB_X + THUMB_SIZE + 10, THUMB_Y + THUMB_SIZE + 10),
            radius=THUMB_RADIUS + 12, fill=(0, 0, 0, 130)
        )
        shadow = shadow.filter(ImageFilter.GaussianBlur(18))
        bg = Image.alpha_composite(bg, shadow)

        # Thumb glow
        t_glow, t_sharp = create_rainbow_glow(
            (THUMB_SIZE, THUMB_SIZE), THUMB_RADIUS, thickness=14, blur_amount=35
        )
        bg.paste(t_glow, (THUMB_X - 100, THUMB_Y - 100), t_glow)
        bg.paste(t_sharp, (THUMB_X - 100, THUMB_Y - 100), t_sharp)

        bg.paste(thumb_img, (THUMB_X, THUMB_Y), thumb_mask)

        # DRAWING
        draw = ImageDraw.Draw(bg)

        # FONTS - Check if exist
        try:
            font_path = "AxiomMuzic/assets/assets/font2.ttf"
            if os.path.exists(font_path):
                title_font = ImageFont.truetype(font_path, 42)
            else:
                title_font = ImageFont.load_default()
            meta_font = title_font
            time_font = title_font
        except:
            title_font = ImageFont.load_default()
            meta_font = title_font
            time_font = title_font

        trimmed = trim_text(title, title_font, MAX_TITLE_WIDTH)
        draw.text((TITLE_X, TITLE_Y), trimmed, fill="white", font=title_font)
        draw.text((TITLE_X, META_Y), f"{channel}  |  {views}",
                  fill=(200, 200, 200), font=meta_font)

        # PROGRESS BAR
        bar_end = BAR_X + BAR_WIDTH
        progress = int(BAR_WIDTH * 0.30)

        draw.rounded_rectangle(
            [(BAR_X, BAR_Y), (bar_end, BAR_Y + BAR_HEIGHT)],
            radius=3, fill=(90, 90, 90)
        )
        draw.rounded_rectangle(
            [(BAR_X, BAR_Y), (BAR_X + progress, BAR_Y + BAR_HEIGHT)],
            radius=3, fill=(60, 230, 110)
        )

        cx, cy = BAR_X + progress, BAR_Y + BAR_HEIGHT // 2
        draw.ellipse([(cx - 8, cy - 8), (cx + 8, cy + 8)], fill="white")

        draw.text((BAR_X, BAR_Y + 18), "01:13", fill="white", font=time_font)
        total = duration_text if not is_live else "4:30"
        draw.text((bar_end - 42, BAR_Y + 18), total, fill="white", font=time_font)

        # CONTROL PILL - SAFE VALUES
        pill = Image.new("RGBA", (PILL_W, PILL_H), (0, 0, 0, 0))
        pd = ImageDraw.Draw(pill)
        
        # SAFE: radius < PILL_H/2
        safe_radius = min(PILL_RADIUS, PILL_H // 2 - 5)
        
        pd.rounded_rectangle((0, 0, PILL_W, PILL_H), radius=safe_radius,
                             fill=(25, 25, 30, 220))
        pd.rounded_rectangle((1, 1, PILL_W - 1, PILL_H - 1), radius=safe_radius - 1,
                             outline=(60, 60, 70, 200), width=1)
        bg.paste(pill, (PILL_X, PILL_Y), pill)

        # Icons
        icon_y = PILL_Y + (PILL_H - 28) // 2
        icon_size = 28
        sx = PILL_X + 28
        gap = 60

        # Simple icons
        draw.line([(sx, icon_y+10), (sx+14, icon_y)], fill="white", width=2)
        draw.line([(sx, icon_y+18), (sx+14, icon_y+28)], fill="white", width=2)
        
        draw.polygon([(sx+gap+20, icon_y+4), (sx+gap+20, icon_y+24), 
                     (sx+gap+4, icon_y+14)], fill="white")
        draw.rectangle([(sx+gap+24, icon_y+4), (sx+gap+28, icon_y+24)], fill="white")
        
        play_size = 46
        play_y = PILL_Y + (PILL_H - play_size) // 2
        draw.ellipse([(sx+gap*2+4, play_y), (sx+gap*2+4+play_size, play_y+play_size)], 
                    fill="white")
        draw.polygon([(sx+gap*2+20, play_y+12), (sx+gap*2+20, play_y+34), 
                     (sx+gap*2+38, play_y+23)], fill=(20, 20, 25))
        
        draw.rectangle([(sx+gap*3+8, icon_y+4), (sx+gap*3+12, icon_y+24)], fill="white")
        draw.polygon([(sx+gap*3+16, icon_y+4), (sx+gap*3+16, icon_y+24), 
                     (sx+gap*3+32, icon_y+14)], fill="white")
        
        draw.arc([(sx+gap*4+12, icon_y+4), (sx+gap*4+32, icon_y+24)], 
                180, 360, fill=(60, 230, 110), width=2)
        draw.arc([(sx+gap*4+12, icon_y+4), (sx+gap*4+32, icon_y+24)], 
                0, 180, fill=(60, 230, 110), width=2)

        # SAVE
        bg = bg.convert("RGB")
        bg.save(cache_path, "PNG", quality=95)
        print(f"✓ Thumbnail saved: {cache_path}")

    except Exception as e:
        import traceback
        print(f"❌ Thumbnail error: {e}")
        traceback.print_exc()
        return YOUTUBE_IMG_URL
    finally:
        try:
            if os.path.exists(thumb_path):
                os.remove(thumb_path)
        except:
            pass

    return cache_path
