# -----------------------------------------------
# 🔸 AxiomMusic Project - Perfect Thumbnail Generator
# 🔹 Developed & Maintained by: Axiom Bots (https://t.me/axiombots)
# 📅 Copyright © 2026 – All Rights Reserved
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

# Panel dimensions - EXACT from sample
PANEL_W, PANEL_H = 920, 440
PANEL_X = (1280 - PANEL_W) // 2
PANEL_Y = 140
PANEL_RADIUS = 45

# Thumbnail
THUMB_SIZE = 310
THUMB_X = PANEL_X + 45
THUMB_Y = PANEL_Y + 60
THUMB_RADIUS = 28

# Text positions
TITLE_X = THUMB_X + THUMB_SIZE + 50
TITLE_Y = THUMB_Y + 35
META_Y = TITLE_Y + 50

# Progress bar
BAR_Y = META_Y + 60
BAR_X = TITLE_X
BAR_WIDTH = 460
BAR_HEIGHT = 5

# Icons
ICONS_Y = BAR_Y + 45
ICONS_X = TITLE_X

MAX_TITLE_WIDTH = 480

def trim_text(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> str:
    if font.getlength(text) <= max_width:
        return text
    ellipsis = "…"
    for i in range(len(text) - 1, 0, -1):
        trimmed = text[:i] + ellipsis
        if font.getlength(trimmed) <= max_width:
            return trimmed
    return ellipsis

async def get_thumb(videoid: str) -> str:
    cache_path = os.path.join(CACHE_DIR, f"{videoid}_perfect.png")
    
    if os.path.exists(cache_path):
        return cache_path

    thumb_path = os.path.join(CACHE_DIR, f"thumb_{videoid}.png")
    
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
        
    except Exception:
        title, thumbnail_url, duration, views, channel = (
            "Unsupported Title", YOUTUBE_IMG_URL, None, "Unknown Views", "YouTube"
        )

    is_live = not duration or str(duration).strip().lower() in {"", "live", "live now"}
    duration_text = "LIVE" if is_live else (duration or "Unknown")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(thumbnail_url, timeout=10) as resp:
                if resp.status == 200:
                    async with aiofiles.open(thumb_path, "wb") as f:
                        await f.write(await resp.read())
                else:
                    return YOUTUBE_IMG_URL
    except Exception:
        return YOUTUBE_IMG_URL

    try:
        # Open thumbnail
        base_thumb = Image.open(thumb_path).convert("RGBA")
        base_thumb = base_thumb.resize((1280, 720), Image.LANCZOS)
        
        # BRIGHTNESS - Make it brighter like sample
        enhancer = ImageEnhance.Brightness(base_thumb)
        base_thumb = enhancer.enhance(1.35)
        
        enhancer = ImageEnhance.Contrast(base_thumb)
        base_thumb = enhancer.enhance(1.15)
        
        # Blur background
        bg = base_thumb.filter(ImageFilter.GaussianBlur(18))
        
        # Dark overlay
        dark_overlay = Image.new("RGBA", bg.size, (0, 0, 0, 75))
        bg = Image.alpha_composite(bg, dark_overlay)
        
        # Create panel area
        panel_area = bg.crop((PANEL_X, PANEL_Y, PANEL_X + PANEL_W, PANEL_Y + PANEL_H))
        
        # Frosted glass effect - SUBTLE like sample
        frosted = Image.new("RGBA", (PANEL_W, PANEL_H), (15, 15, 15, 45))
        panel = Image.alpha_composite(panel_area, frosted)
        panel = panel.filter(ImageFilter.GaussianBlur(1.5))
        
        # Rounded mask
        mask = Image.new("L", (PANEL_W, PANEL_H), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.rounded_rectangle((0, 0, PANEL_W, PANEL_H), radius=PANEL_RADIUS, fill=255)
        
        bg.paste(panel, (PANEL_X, PANEL_Y), mask)
        
        # MULTI-COLOR GRADIENT BORDER - EXACT like sample
        # Colors: Blue -> Green -> Pink/Purple gradient
        border_colors = [
            (40, 100, 255),    # Blue
            (40, 220, 120),    # Green
            (200, 80, 200),    # Purple/Pink
            (255, 120, 100),   # Orange-Pink
        ]
        
        # Create glowing border
        border_size = (PANEL_W + 60, PANEL_H + 60)
        border_img = Image.new("RGBA", border_size, (0, 0, 0, 0))
        border_draw = ImageDraw.Draw(border_img)
        
        # Multiple layers for smooth glow
        for i, color in enumerate(border_colors):
            offset = i * 5
            alpha = 220 - (i * 45)
            if alpha < 100:
                alpha = 100
            
            border_draw.rounded_rectangle(
                (offset, offset, border_size[0] - offset, border_size[1] - offset),
                radius=PANEL_RADIUS + offset + 8,
                outline=color + (alpha,),
                width=7
            )
        
        # Blur for glow effect
        border_img = border_img.filter(ImageFilter.GaussianBlur(32))
        
        # Paste border
        bg.paste(border_img, (PANEL_X - 30, PANEL_Y - 30), border_img)
        
        # Inner border (sharp)
        inner_border = Image.new("RGBA", (PANEL_W + 8, PANEL_H + 8), (0, 0, 0, 0))
        ib_draw = ImageDraw.Draw(inner_border)
        ib_draw.rounded_rectangle(
            (0, 0, PANEL_W + 8, PANEL_H + 8),
            radius=PANEL_RADIUS + 4,
            outline=(255, 255, 255, 40),
            width=2
        )
        bg.paste(inner_border, (PANEL_X - 4, PANEL_Y - 4), inner_border)
        
        # Process thumbnail
        thumb_img = Image.open(thumb_path).convert("RGBA")
        thumb_img = thumb_img.resize((THUMB_SIZE, THUMB_SIZE), Image.LANCZOS)
        
        # Brightness for thumb
        enhancer = ImageEnhance.Brightness(thumb_img)
        thumb_img = enhancer.enhance(1.2)
        
        # Thumbnail mask
        thumb_mask = Image.new("L", (THUMB_SIZE, THUMB_SIZE), 0)
        mask_draw = ImageDraw.Draw(thumb_mask)
        mask_draw.rounded_rectangle((0, 0, THUMB_SIZE, THUMB_SIZE), radius=THUMB_RADIUS, fill=255)
        
        # Thumbnail shadow
        shadow = Image.new("RGBA", (1280, 720), (0, 0, 0, 0))
        shadow_draw = ImageDraw.Draw(shadow)
        shadow_draw.rounded_rectangle(
            (THUMB_X - 5, THUMB_Y - 5, 
             THUMB_X + THUMB_SIZE + 5, THUMB_Y + THUMB_SIZE + 5),
            radius=THUMB_RADIUS + 6,
            fill=(0, 0, 0, 120)
        )
        shadow = shadow.filter(ImageFilter.GaussianBlur(15))
        bg = Image.alpha_composite(bg, shadow)
        
        # Thumbnail glow border - MULTI COLOR
        thumb_border_size = (THUMB_SIZE + 30, THUMB_SIZE + 30)
        thumb_border = Image.new("RGBA", thumb_border_size, (0, 0, 0, 0))
        tb_draw = ImageDraw.Draw(thumb_border)
        
        thumb_colors = [
            (60, 120, 255),    # Blue
            (60, 230, 130),    # Green
            (180, 100, 220),   # Purple
        ]
        
        for i, color in enumerate(thumb_colors):
            offset = i * 4
            alpha = 200 - (i * 50)
            tb_draw.rounded_rectangle(
                (offset, offset, thumb_border_size[0] - offset, thumb_border_size[1] - offset),
                radius=THUMB_RADIUS + offset + 5,
                outline=color + (alpha,),
                width=5
            )
        
        thumb_border = thumb_border.filter(ImageFilter.GaussianBlur(22))
        bg.paste(thumb_border, (THUMB_X - 15, THUMB_Y - 15), thumb_border)
        
        # Paste thumbnail
        bg.paste(thumb_img, (THUMB_X, THUMB_Y), thumb_mask)
        
        # Drawing
        draw = ImageDraw.Draw(bg)
        
        # Fonts
        try:
            title_font = ImageFont.truetype("AxiomMuzic/assets/assets/font2.ttf", 38)
            meta_font = ImageFont.truetype("AxiomMuzic/assets/assets/font.ttf", 23)
            time_font = ImageFont.truetype("AxiomMuzic/assets/assets/font.ttf", 20)
        except OSError:
            title_font = ImageFont.load_default()
            meta_font = title_font
            time_font = title_font
        
        # Title - UPPERCASE like sample
        trimmed_title = trim_text(title.upper(), title_font, MAX_TITLE_WIDTH)
        draw.text((TITLE_X, TITLE_Y), trimmed_title, fill="white", font=title_font)
        
        # Channel name
        draw.text((TITLE_X, META_Y), channel, fill=(220, 220, 220), font=meta_font)
        
        # Progress bar
        bar_end_x = BAR_X + BAR_WIDTH
        progress_width = int(BAR_WIDTH * 0.35)
        
        # Bar background - gray
        draw.rounded_rectangle(
            [(BAR_X, BAR_Y), (bar_end_x, BAR_Y + BAR_HEIGHT)],
            radius=3,
            fill=(90, 90, 90)
        )
        
        # Progress - BRIGHT GREEN like sample
        draw.rounded_rectangle(
            [(BAR_X, BAR_Y), (BAR_X + progress_width, BAR_Y + BAR_HEIGHT)],
            radius=3,
            fill=(80, 240, 100)
        )
        
        # Circle indicator
        circle_x = BAR_X + progress_width
        circle_y = BAR_Y + BAR_HEIGHT // 2
        draw.ellipse(
            [(circle_x - 7, circle_y - 7), (circle_x + 7, circle_y + 7)],
            fill="white"
        )
        
        # Times
        current_time = "01:58"
        total_time = duration_text if not is_live else "4:49"
        
        draw.text((BAR_X, BAR_Y + 22), current_time, fill="white", font=time_font)
        draw.text((bar_end_x - 40, BAR_Y + 22), total_time, fill="white", font=time_font)
        
        # CONTROL ICONS - EXACT like sample
        icon_y = ICONS_Y
        icon_spacing = 35
        start_x = ICONS_X
        
        # 1. Shuffle icon - GREEN/CYAN
        shuffle_x = start_x
        draw.line([(shuffle_x, icon_y+12), (shuffle_x+8, icon_y+4)], fill=(80, 255, 150), width=2)
        draw.line([(shuffle_x+8, icon_y+4), (shuffle_x+18, icon_y+4)], fill=(80, 255, 150), width=2)
        draw.line([(shuffle_x, icon_y+16), (shuffle_x+8, icon_y+24)], fill=(80, 255, 150), width=2)
        draw.line([(shuffle_x+8, icon_y+24), (shuffle_x+18, icon_y+24)], fill=(80, 255, 150), width=2)
        draw.line([(shuffle_x+6, icon_y+20), (shuffle_x+14, icon_y+12)], fill=(80, 255, 150), width=2)
        
        # 2. Repeat icon - ORANGE/YELLOW
        repeat_x = start_x + icon_spacing
        draw.arc([(repeat_x, icon_y+2), (repeat_x+24, icon_y+26)], 0, 270, fill=(255, 200, 80), width=2)
        draw.polygon([(repeat_x+16, icon_y), (repeat_x+24, icon_y), (repeat_x+24, icon_y+8)], fill=(255, 200, 80))
        draw.line([(repeat_x+18, icon_y+18), (repeat_x+26, icon_y+18)], fill=(255, 200, 80), width=2)
        draw.polygon([(repeat_x+26, icon_y+14), (repeat_x+26, icon_y+22), (repeat_x+18, icon_y+18)], fill=(255, 200, 80))
        
        # 3. Previous icon - WHITE
        prev_x = start_x + icon_spacing * 2
        draw.polygon([(prev_x, icon_y+4), (prev_x, icon_y+24), (prev_x+20, icon_y+14)], fill="white")
        draw.rectangle([(prev_x+22, icon_y+2), (prev_x+26, icon_y+26)], fill="white")
        
        # 4. Pause icon - WHITE (2 vertical bars)
        pause_x = start_x + icon_spacing * 3
        draw.rectangle([(pause_x, icon_y+2), (pause_x+8, icon_y+26)], fill="white")
        draw.rectangle([(pause_x+16, icon_y+2), (pause_x+24, icon_y+26)], fill="white")
        
        # 5. Next icon - WHITE
        next_x = start_x + icon_spacing * 4
        draw.rectangle([(next_x, icon_y+2), (next_x+4, icon_y+26)], fill="white")
        draw.polygon([(next_x+6, icon_y+4), (next_x+6, icon_y+24), (next_x+26, icon_y+14)], fill="white")
        
        # 6. Heart icon - RED
        heart_x = start_x + icon_spacing * 5 + 5
        draw.ellipse([(heart_x, icon_y+8), (heart_x+10, icon_y+18)], fill=(255, 70, 70))
        draw.ellipse([(heart_x+8, icon_y+8), (heart_x+18, icon_y+18)], fill=(255, 70, 70))
        draw.polygon([(heart_x+2, icon_y+13), (heart_x+16, icon_y+13), (heart_x+9, icon_y+24)], fill=(255, 70, 70))
        
        # 7. Headphones icon - WHITE
        hp_x = start_x + icon_spacing * 6 + 10
        draw.arc([(hp_x, icon_y+4), (hp_x+22, icon_y+20)], 180, 0, fill="white", width=3)
        draw.ellipse([(hp_x, icon_y+18), (hp_x+9, icon_y+27)], fill="white")
        draw.ellipse([(hp_x+13, icon_y+18), (hp_x+22, icon_y+27)], fill="white")
        
        # Save
        bg = bg.convert("RGB")
        bg.save(cache_path, "PNG", quality=95)
        
    except Exception as e:
        print(f"Error: {e}")
        return YOUTUBE_IMG_URL
    
    finally:
        try:
            if os.path.exists(thumb_path):
                os.remove(thumb_path)
        except OSError:
            pass

    return cache_path
