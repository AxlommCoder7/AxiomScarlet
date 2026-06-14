# -----------------------------------------------
# 🔸 AxiomMusic Project - Clean Thumbnail Generator
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

# Constants
CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)

# Panel dimensions - Match sample exactly
PANEL_W, PANEL_H = 950, 450
PANEL_X = (1280 - PANEL_W) // 2
PANEL_Y = 135
PANEL_RADIUS = 50  # More curved corners

# Thumbnail dimensions
THUMB_SIZE = 320
THUMB_X = PANEL_X + 50
THUMB_Y = PANEL_Y + 65
THUMB_RADIUS = 30

# Text positions
TITLE_X = THUMB_X + THUMB_SIZE + 55
TITLE_Y = THUMB_Y + 25
META_Y = TITLE_Y + 55

# Progress bar
BAR_Y = META_Y + 65
BAR_X = TITLE_X
BAR_WIDTH = 480
BAR_HEIGHT = 5

# Icons position
ICONS_Y = BAR_Y + 45
ICONS_X = TITLE_X

MAX_TITLE_WIDTH = 500

def trim_text(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> str:
    """Trim text to fit within max_width"""
    if font.getlength(text) <= max_width:
        return text
    
    ellipsis = "…"
    for i in range(len(text) - 1, 0, -1):
        trimmed = text[:i] + ellipsis
        if font.getlength(trimmed) <= max_width:
            return trimmed
    return ellipsis

def create_smooth_gradient_border(panel_size, colors, border_width=8, blur_radius=30):
    """Create smooth multi-color gradient border"""
    width, height = panel_size
    img = Image.new("RGBA", (width + border_width * 4, height + border_width * 4), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Create smooth gradient layers
    for i, color in enumerate(colors):
        offset = i * 3
        alpha = 200 - (i * 40)
        if alpha < 80:
            alpha = 80
        
        draw.rounded_rectangle(
            (offset, offset, width + border_width * 4 - offset, height + border_width * 4 - offset),
            radius=PANEL_RADIUS + offset + 5,
            outline=color + (alpha,),
            width=border_width
        )
    
    # Apply gaussian blur for smooth glow
    return img.filter(ImageFilter.GaussianBlur(blur_radius))

async def get_thumb(videoid: str) -> str:
    """Generate clean, professional thumbnail"""
    cache_path = os.path.join(CACHE_DIR, f"{videoid}_clean.png")
    
    if os.path.exists(cache_path):
        return cache_path

    # Fetch video data
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

    # Download thumbnail
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
        # Open and resize thumbnail
        base_thumb = Image.open(thumb_path).convert("RGBA")
        base_thumb = base_thumb.resize((1280, 720), Image.LANCZOS)
        
        # ENHANCE BRIGHTNESS - Make it brighter
        enhancer = ImageEnhance.Brightness(base_thumb)
        base_thumb = enhancer.enhance(1.3)  # 30% brighter
        
        # ENHANCE CONTRAST
        enhancer = ImageEnhance.Contrast(base_thumb)
        base_thumb = enhancer.enhance(1.2)  # 20% more contrast
        
        # Apply blur to background
        bg = base_thumb.filter(ImageFilter.GaussianBlur(15))
        
        # Darken background slightly
        dark_overlay = Image.new("RGBA", bg.size, (0, 0, 0, 80))
        bg = Image.alpha_composite(bg, dark_overlay)
        
        # Create frosted glass panel - CLEAN & SIMPLE
        panel_area = bg.crop((PANEL_X, PANEL_Y, PANEL_X + PANEL_W, PANEL_Y + PANEL_H))
        
        # Light frosted effect
        frosted = Image.new("RGBA", (PANEL_W, PANEL_H), (20, 20, 20, 50))
        panel = Image.alpha_composite(panel_area, frosted)
        panel = panel.filter(ImageFilter.GaussianBlur(2))
        
        # Create rounded mask with HIGH RADIUS
        mask = Image.new("L", (PANEL_W, PANEL_H), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.rounded_rectangle((0, 0, PANEL_W, PANEL_H), radius=PANEL_RADIUS, fill=255)
        
        # Paste panel with mask
        bg.paste(panel, (PANEL_X, PANEL_Y), mask)
        
        # GRADIENT BORDER - Smooth and subtle
        gradient_colors = [
            (0, 255, 200),    # Teal
            (0, 200, 255),    # Cyan
            (100, 150, 255),  # Blue
        ]
        
        border_glow = create_smooth_gradient_border(
            (PANEL_W, PANEL_H),
            gradient_colors,
            border_width=6,
            blur_radius=35
        )
        
        bg.paste(border_glow, (PANEL_X - 12, PANEL_Y - 12), border_glow)
        
        # Process thumbnail
        thumb_img = Image.open(thumb_path).convert("RGBA")
        thumb_img = thumb_img.resize((THUMB_SIZE, THUMB_SIZE), Image.LANCZOS)
        
        # ENHANCE thumbnail brightness too
        enhancer = ImageEnhance.Brightness(thumb_img)
        thumb_img = enhancer.enhance(1.2)
        
        # Create rounded mask for thumbnail
        thumb_mask = Image.new("L", (THUMB_SIZE, THUMB_SIZE), 0)
        mask_draw = ImageDraw.Draw(thumb_mask)
        mask_draw.rounded_rectangle((0, 0, THUMB_SIZE, THUMB_SIZE), radius=THUMB_RADIUS, fill=255)
        
        # Add subtle shadow
        shadow = Image.new("RGBA", (1280, 720), (0, 0, 0, 0))
        shadow_draw = ImageDraw.Draw(shadow)
        shadow_draw.rounded_rectangle(
            (THUMB_X - 4, THUMB_Y - 4, 
             THUMB_X + THUMB_SIZE + 4, THUMB_Y + THUMB_SIZE + 4),
            radius=THUMB_RADIUS + 5,
            fill=(0, 0, 0, 100)
        )
        shadow = shadow.filter(ImageFilter.GaussianBlur(12))
        bg = Image.alpha_composite(bg, shadow)
        
        # Thumbnail glow border
        thumb_glow_colors = [
            (0, 255, 200),
            (0, 220, 255),
        ]
        
        thumb_glow = Image.new("RGBA", (THUMB_SIZE + 24, THUMB_SIZE + 24), (0, 0, 0, 0))
        tg_draw = ImageDraw.Draw(thumb_glow)
        
        for i, color in enumerate(thumb_glow_colors):
            offset = i * 4
            alpha = 200 - (i * 50)
            tg_draw.rounded_rectangle(
                (offset, offset, THUMB_SIZE + 24 - offset, THUMB_SIZE + 24 - offset),
                radius=THUMB_RADIUS + offset + 3,
                outline=color + (alpha,),
                width=4
            )
        
        thumb_glow = thumb_glow.filter(ImageFilter.GaussianBlur(20))
        bg.paste(thumb_glow, (THUMB_X - 12, THUMB_Y - 12), thumb_glow)
        
        # Paste thumbnail
        bg.paste(thumb_img, (THUMB_X, THUMB_Y), thumb_mask)
        
        # Drawing
        draw = ImageDraw.Draw(bg)
        
        # Load fonts
        try:
            title_font = ImageFont.truetype("AxiomMuzic/assets/assets/font2.ttf", 36)
            meta_font = ImageFont.truetype("AxiomMuzic/assets/assets/font.ttf", 22)
            time_font = ImageFont.truetype("AxiomMuzic/assets/assets/font.ttf", 19)
        except OSError:
            title_font = ImageFont.load_default()
            meta_font = title_font
            time_font = title_font
        
        # Draw title - CLEAN
        trimmed_title = trim_text(title, title_font, MAX_TITLE_WIDTH)
        draw.text((TITLE_X, TITLE_Y), trimmed_title, fill="white", font=title_font)
        
        # Draw channel/views
        meta_text = f"{channel} | {views}"
        draw.text((TITLE_X, META_Y), meta_text, fill=(210, 210, 210), font=meta_font)
        
        # Progress bar - CLEAN & SIMPLE
        bar_end_x = BAR_X + BAR_WIDTH
        progress_percent = 0.30  # 30% - adjust as needed
        progress_width = int(BAR_WIDTH * progress_percent)
        
        # Bar background
        draw.rounded_rectangle(
            [(BAR_X, BAR_Y), (bar_end_x, BAR_Y + BAR_HEIGHT)],
            radius=3,
            fill=(70, 70, 70)
        )
        
        # Progress fill - BRIGHT GREEN
        draw.rounded_rectangle(
            [(BAR_X, BAR_Y), (BAR_X + progress_width, BAR_Y + BAR_HEIGHT)],
            radius=3,
            fill=(0, 230, 140)
        )
        
        # Progress circle
        circle_x = BAR_X + progress_width
        circle_y = BAR_Y + BAR_HEIGHT // 2
        draw.ellipse(
            [(circle_x - 6, circle_y - 6), (circle_x + 6, circle_y + 6)],
            fill="white"
        )
        
        # Time text
        current_time = "01:13"
        draw.text((BAR_X, BAR_Y + 22), current_time, fill="white", font=time_font)
        
        end_time_x = bar_end_x - (50 if is_live else 40)
        end_color = (0, 230, 140) if is_live else "white"
        draw.text((end_time_x, BAR_Y + 22), duration_text, fill=end_color, font=time_font)
        
        # Control icons - SIMPLE & CLEAN
        icon_color = "white"
        icon_gap = 38
        icon_y = ICONS_Y
        
        # Previous
        draw.polygon([(ICONS_X, icon_y+6), (ICONS_X, icon_y+22), (ICONS_X+18, icon_y+14)], fill=icon_color)
        draw.rectangle([(ICONS_X+20, icon_y+4), (ICONS_X+24, icon_y+24)], fill=icon_color)
        
        # Play
        play_x = ICONS_X + icon_gap
        draw.polygon([(play_x, icon_y+2), (play_x, icon_y+26), (play_x+28, icon_y+14)], fill=icon_color)
        
        # Next
        next_x = ICONS_X + icon_gap * 2
        draw.rectangle([(next_x, icon_y+4), (next_x+4, icon_y+24)], fill=icon_color)
        draw.polygon([(next_x+6, icon_y+6), (next_x+6, icon_y+22), (next_x+24, icon_y+14)], fill=icon_color)
        
        # Repeat
        repeat_x = ICONS_X + icon_gap * 3
        draw.arc([(repeat_x, icon_y+4), (repeat_x+26, icon_y+24)], 0, 270, fill=(120,120,120), width=2)
        draw.polygon([(repeat_x+18, icon_y), (repeat_x+26, icon_y), (repeat_x+26, icon_y+8)], fill=(120,120,120))
        
        # Heart
        heart_x = ICONS_X + icon_gap * 4 + 10
        # Left circle
        draw.ellipse([(heart_x, icon_y+6), (heart_x+12, icon_y+18)], fill=(255, 70, 70))
        # Right circle
        draw.ellipse([(heart_x+8, icon_y+6), (heart_x+20, icon_y+18)], fill=(255, 70, 70))
        # Bottom triangle
        draw.polygon([(heart_x+2, icon_y+12), (heart_x+18, icon_y+12), (heart_x+10, icon_y+24)], fill=(255, 70, 70))
        
        # Headphones
        hp_x = ICONS_X + icon_gap * 5 + 10
        draw.arc([(hp_x, icon_y), (hp_x+26, icon_y+18)], 180, 0, fill=(120,120,120), width=3)
        draw.ellipse([(hp_x, icon_y+16), (hp_x+10, icon_y+26)], fill=(120,120,120))
        draw.ellipse([(hp_x+16, icon_y+16), (hp_x+26, icon_y+26)], fill=(120,120,120))
        
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
