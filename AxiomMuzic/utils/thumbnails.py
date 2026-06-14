# -----------------------------------------------
# 🔸 AxiomMusic Project - EXACT Neon Thumbnail
# 🔹 Developed & Maintained by: Axiom Bots (https://t.me/axiombots)
# 📅 Copyright © 2026 – All Rights Reserved
# -----------------------------------------------

import os
import re
import math
import aiofiles
import aiohttp
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageEnhance
from py_yt import VideosSearch
from config import YOUTUBE_IMG_URL

CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)

# ===== LAYOUT (Exact from reference) =====
CARD_W, CARD_H = 1000, 480
CARD_X = (1280 - CARD_W) // 2
CARD_Y = (720 - CARD_H) // 2
CARD_RADIUS = 55

THUMB_SIZE = 320
THUMB_X = CARD_X + 60
THUMB_Y = CARD_Y + 60
THUMB_RADIUS = 35

TITLE_X = THUMB_X + THUMB_SIZE + 50
TITLE_Y = CARD_Y + 100
META_Y = TITLE_Y + 60

BAR_Y = META_Y + 60
BAR_X = TITLE_X
BAR_WIDTH = 520
BAR_HEIGHT = 6

PILL_W = 360
PILL_H = 80
PILL_RADIUS = 40
PILL_X = TITLE_X
PILL_Y = BAR_Y + 50

MAX_TITLE_WIDTH = 560

def trim_text(text, font, max_width):
    if font.getlength(text) <= max_width:
        return text
    for i in range(len(text) - 1, 0, -1):
        if font.getlength(text[:i] + "…") <= max_width:
            return text[:i] + "…"
    return "…"

def get_rainbow_color(position):
    """Get rainbow color based on position (0-1) around the border"""
    # position: 0=top-left, 0.25=top-right, 0.5=bottom-right, 0.75=bottom-left, 1=top-left
    colors = [
        (255, 50, 150),   # 0.0 - Pink/Magenta (top-left)
        (180, 50, 255),   # 0.125 - Purple
        (100, 100, 255),  # 0.25 - Blue (top-right)
        (50, 200, 255),   # 0.375 - Cyan
        (50, 255, 150),   # 0.5 - Green (right)
        (200, 255, 50),   # 0.625 - Yellow-Green
        (255, 200, 50),   # 0.75 - Yellow/Orange (bottom-right)
        (255, 100, 50),   # 0.875 - Orange
        (255, 50, 100),   # 1.0 - Pink (back to start)
    ]
    
    idx = int(position * (len(colors) - 1))
    return colors[idx]

def create_neon_border(size, radius, thickness=8, glow_blur=40):
    """Create rainbow neon border with intense glow"""
    w, h = size
    canvas_size = (w + 100, h + 100)
    img = Image.new("RGBA", canvas_size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Draw multiple layers for smooth gradient
    num_layers = 60
    for i in range(num_layers):
        # Calculate position around the border (0 to 1)
        position = i / num_layers
        
        # Get color for this position
        color = get_rainbow_color(position)
        
        # Calculate offset and radius
        offset = 50 + i * (thickness / num_layers)
        layer_radius = radius + 50 - i * (thickness / num_layers)
        
        if layer_radius < 10:
            break
        
        # Draw with varying alpha for glow effect
        alpha = 255 if i < num_layers // 2 else int(255 * (1 - (i - num_layers//2) / (num_layers//2)))
        
        draw.rounded_rectangle(
            (int(offset), int(offset), 
             int(canvas_size[0] - offset), int(canvas_size[1] - offset)),
            radius=int(layer_radius),
            outline=color + (alpha,),
            width=2
        )
    
    # Apply heavy blur for neon glow
    glow = img.filter(ImageFilter.GaussianBlur(glow_blur))
    
    # Create sharp inner border
    sharp = Image.new("RGBA", canvas_size, (0, 0, 0, 0))
    sharp_draw = ImageDraw.Draw(sharp)
    
    for i in range(3):
        position = i / 3
        color = get_rainbow_color(position)
        offset = 50 + thickness + i
        layer_radius = radius - i
        
        sharp_draw.rounded_rectangle(
            (int(offset), int(offset),
             int(canvas_size[0] - offset), int(canvas_size[1] - offset)),
            radius=int(layer_radius),
            outline=color + (255,),
            width=1
        )
    
    return glow, sharp

# ===== ICON FUNCTIONS =====

def draw_icon_shuffle(draw, x, y, size, color):
    s = int(size)
    x, y = int(x), int(y)
    # Crossed arrows
    draw.line([(x, y + s//2), (x + s//2, y)], fill=color, width=2)
    draw.line([(x, y + s//2), (x + s//2, y + s)], fill=color, width=2)
    draw.line([(x + s//4, y), (x + s*3//4, y)], fill=color, width=2)
    draw.line([(x + s//4, y + s), (x + s*3//4, y + s)], fill=color, width=2)
    # Arrow heads
    draw.polygon([(x + s//2, y), (x + s//2 + 6, y + 4), (x + s//2, y + 8)], fill=color)
    draw.polygon([(x + s//2, y + s), (x + s//2 + 6, y + s - 4), (x + s//2, y + s - 8)], fill=color)

def draw_icon_prev(draw, x, y, size, color):
    s = int(size)
    x, y = int(x), int(y)
    # Triangle pointing left
    draw.polygon([(x + s*3//4, y + 2), (x + s*3//4, y + s - 2), (x + 2, y + s//2)], fill=color)
    # Vertical bar
    draw.rectangle([(x + s*4//5, y + 4), (x + s, y + s - 4)], fill=color)

def draw_icon_play(draw, x, y, size, circle_color, triangle_color):
    s = int(size)
    x, y = int(x), int(y)
    # White circle
    draw.ellipse([(x, y), (x + s, y + s)], fill=circle_color)
    # Dark triangle (play)
    draw.polygon([
        (x + s*2//5, y + s//4),
        (x + s*2//5, y + s*3//4),
        (x + s*3//4, y + s//2)
    ], fill=triangle_color)

def draw_icon_next(draw, x, y, size, color):
    s = int(size)
    x, y = int(x), int(y)
    # Vertical bar
    draw.rectangle([(x, y + 4), (x + s//5, y + s - 4)], fill=color)
    # Triangle pointing right
    draw.polygon([(x + s//4, y + 2), (x + s//4, y + s - 2), (x + s - 2, y + s//2)], fill=color)

def draw_icon_repeat(draw, x, y, size, color):
    s = int(size)
    x, y = int(x), int(y)
    # Two curved arrows forming a loop
    # Top arrow (going right)
    draw.arc([(x, y), (x + s, y + s//2)], 180, 0, fill=color, width=2)
    draw.polygon([(x + s - 4, y), (x + s + 4, y + 4), (x + s - 4, y + 8)], fill=color)
    # Bottom arrow (going left)
    draw.arc([(x, y + s//2), (x + s, y + s)], 0, 180, fill=color, width=2)
    draw.polygon([(x + 4, y + s), (x - 4, y + s - 4), (x + 4, y + s - 8)], fill=color)

# ===== MAIN FUNCTION =====

async def get_thumb(videoid: str) -> str:
    cache_path = os.path.join(CACHE_DIR, f"{videoid}_neon.png")
    
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
        # === BACKGROUND (Very dark) ===
        base_thumb = Image.open(thumb_path).convert("RGBA")
        base_thumb = base_thumb.resize((1280, 720), Image.LANCZOS)
        
        # Heavy blur and darken
        bg = base_thumb.filter(ImageFilter.GaussianBlur(30))
        bg = ImageEnhance.Brightness(bg).enhance(0.3)  # Very dark
        bg = ImageEnhance.Contrast(bg).enhance(1.5)
        
        # Dark overlay
        dark = Image.new("RGBA", bg.size, (0, 0, 0, 180))
        bg = Image.alpha_composite(bg, dark)
        
        # === CARD (Very dark, almost black) ===
        card_area = bg.crop((CARD_X, CARD_Y, CARD_X + CARD_W, CARD_Y + CARD_H))
        
        # Dark frosted effect
        frosted = Image.new("RGBA", (CARD_W, CARD_H), (5, 5, 8, 200))
        card = Image.alpha_composite(card_area, frosted)
        
        mask = Image.new("L", (CARD_W, CARD_H), 0)
        ImageDraw.Draw(mask).rounded_rectangle((0, 0, CARD_W, CARD_H), radius=CARD_RADIUS, fill=255)
        bg.paste(card, (CARD_X, CARD_Y), mask)
        
        # === CARD NEON BORDER ===
        card_glow, card_sharp = create_neon_border(
            (CARD_W, CARD_H), CARD_RADIUS, thickness=10, glow_blur=45
        )
        bg.paste(card_glow, (CARD_X - 50, CARD_Y - 50), card_glow)
        bg.paste(card_sharp, (CARD_X - 50, CARD_Y - 50), card_sharp)
        
        # === THUMBNAIL ===
        thumb_img = Image.open(thumb_path).convert("RGBA")
        thumb_img = thumb_img.resize((THUMB_SIZE, THUMB_SIZE), Image.LANCZOS)
        
        thumb_mask = Image.new("L", (THUMB_SIZE, THUMB_SIZE), 0)
        ImageDraw.Draw(thumb_mask).rounded_rectangle(
            (0, 0, THUMB_SIZE, THUMB_SIZE), radius=THUMB_RADIUS, fill=255
        )
        
        # Thumbnail shadow
        shadow = Image.new("RGBA", (1280, 720), (0, 0, 0, 0))
        sd = ImageDraw.Draw(shadow)
        sd.rounded_rectangle(
            (THUMB_X - 8, THUMB_Y - 8, 
             THUMB_X + THUMB_SIZE + 8, THUMB_Y + THUMB_SIZE + 8),
            radius=THUMB_RADIUS + 10, fill=(0, 0, 0, 180)
        )
        shadow = shadow.filter(ImageFilter.GaussianBlur(20))
        bg = Image.alpha_composite(bg, shadow)
        
        # Thumbnail neon border
        thumb_glow, thumb_sharp = create_neon_border(
            (THUMB_SIZE, THUMB_SIZE), THUMB_RADIUS, thickness=8, glow_blur=35
        )
        bg.paste(thumb_glow, (THUMB_X - 50, THUMB_Y - 50), thumb_glow)
        bg.paste(thumb_sharp, (THUMB_X - 50, THUMB_Y - 50), thumb_sharp)
        
        bg.paste(thumb_img, (THUMB_X, THUMB_Y), thumb_mask)
        
        # === TEXT ===
        draw = ImageDraw.Draw(bg)
        
        try:
            title_font = ImageFont.truetype("AxiomMuzic/assets/assets/font2.ttf", 40)
            meta_font = ImageFont.truetype("AxiomMuzic/assets/assets/font.ttf", 22)
            time_font = ImageFont.truetype("AxiomMuzic/assets/assets/font.ttf", 20)
        except OSError:
            title_font = ImageFont.load_default()
            meta_font = title_font
            time_font = title_font
        
        # Title
        trimmed = trim_text(title, title_font, MAX_TITLE_WIDTH)
        draw.text((TITLE_X, TITLE_Y), trimmed, fill="white", font=title_font)
        
        # Meta
        draw.text((TITLE_X, META_Y), f"{channel}  |  {views}", 
                  fill=(160, 160, 160), font=meta_font)
        
        # === PROGRESS BAR ===
        bar_end = BAR_X + BAR_WIDTH
        progress = int(BAR_WIDTH * 0.32)
        
        # Background (gray)
        draw.rounded_rectangle(
            [(BAR_X, BAR_Y), (bar_end, BAR_Y + BAR_HEIGHT)],
            radius=3, fill=(60, 60, 60)
        )
        
        # Progress (bright green)
        draw.rounded_rectangle(
            [(BAR_X, BAR_Y), (BAR_X + progress, BAR_Y + BAR_HEIGHT)],
            radius=3, fill=(50, 230, 100)
        )
        
        # Circle indicator
        cx, cy = BAR_X + progress, BAR_Y + BAR_HEIGHT // 2
        draw.ellipse([(cx - 8, cy - 8), (cx + 8, cy + 8)], fill="white")
        
        # Times
        draw.text((BAR_X, BAR_Y + 20), "01:13", fill="white", font=time_font)
        total = duration_text if not is_live else "03:56"
        draw.text((bar_end - 45, BAR_Y + 20), total, fill="white", font=time_font)
        
        # === CONTROL PILL ===
        pill = Image.new("RGBA", (PILL_W, PILL_H), (0, 0, 0, 0))
        pd = ImageDraw.Draw(pill)
        
        # Dark background
        pd.rounded_rectangle(
            (0, 0, PILL_W, PILL_H), radius=PILL_RADIUS, 
            fill=(20, 20, 25, 220)
        )
        
        # Subtle border
        pd.rounded_rectangle(
            (1, 1, PILL_W - 1, PILL_H - 1), radius=PILL_RADIUS - 1,
            outline=(40, 40, 50, 150), width=1
        )
        
        bg.paste(pill, (PILL_X, PILL_Y), pill)
        
        # Icons inside pill
        icon_y = PILL_Y + (PILL_H - 28) // 2
        icon_size = 26
        gap = 60
        sx = PILL_X + 30
        
        # Shuffle (white)
        draw_icon_shuffle(draw, sx, icon_y, icon_size, "white")
        
        # Previous (white)
        draw_icon_prev(draw, sx + gap, icon_y, icon_size, "white")
        
        # Play button (LARGE, white circle, dark triangle)
        play_size = 44
        play_y = PILL_Y + (PILL_H - play_size) // 2
        draw_icon_play(draw, sx + gap * 2, play_y, play_size, "white", (15, 15, 20))
        
        # Next (white)
        draw_icon_next(draw, sx + gap * 3 + 8, icon_y, icon_size, "white")
        
        # Repeat (GREEN accent)
        draw_icon_repeat(draw, sx + gap * 4 + 16, icon_y, icon_size, (50, 230, 100))
        
        # === SAVE ===
        bg = bg.convert("RGB")
        bg.save(cache_path, "PNG", quality=95)
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return YOUTUBE_IMG_URL
    finally:
        try:
            if os.path.exists(thumb_path):
                os.remove(thumb_path)
        except OSError:
            pass

    return cache_path
