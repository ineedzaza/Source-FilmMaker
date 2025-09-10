import discord
from discord.ext import commands
from PIL import Image, ImageEnhance, ImageOps
import io
import numpy as np
import subprocess

# Discord bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# === IMAGE EFFECT HELPERS ===

def apply_hue_saturation(img, hue_shift=0, saturation_shift=0):
    # Convert to HSV
    hsv = img.convert("HSV")
    h, s, v = hsv.split()
    np_h = np.array(h, dtype=np.uint16)
    np_s = np.array(s, dtype=np.int16)

    # Shift hue
    np_h = (np_h + hue_shift) % 256
    # Adjust saturation
    np_s = np.clip(np_s + saturation_shift, 0, 255)

    h = Image.fromarray(np_h.astype(np.uint8), "L")
    s = Image.fromarray(np_s.astype(np.uint8), "L")
    hsv = Image.merge("HSV", (h, s, v))
    return hsv.convert("RGB")

def apply_invert(img):
    return ImageOps.invert(img)

def apply_fisheye(img, strength=0.5):
    # crude fisheye simulation with remapping
    w, h = img.size
    img_np = np.array(img)
    new_img = np.zeros_like(img_np)
    cx, cy = w/2, h/2
    max_r = np.sqrt(cx**2 + cy**2)
    for y in range(h):
        for x in range(w):
            dx, dy = x - cx, y - cy
            r = np.sqrt(dx**2 + dy**2)
            nr = r**(1+strength) / max_r**strength * max_r
            if r != 0:
                nx, ny = int(cx + dx * nr / r), int(cy + dy * nr / r)
                if 0 <= nx < w and 0 <= ny < h:
                    new_img[y, x] = img_np[ny, nx]
    return Image.fromarray(new_img)

# === DISCORD COMMANDS ===

@bot.command()
async def huesaturation(ctx, hue: int = 0, sat: int = 0):
    """Apply hue/saturation adjustment to an uploaded image."""
    if not ctx.message.attachments:
        await ctx.send("Please upload an image.")
        return

    attachment = ctx.message.attachments[0]
    img_bytes = await attachment.read()
    img = Image.open(io.BytesIO(img_bytes)).convert("RGB")

    # Clamp values
    hue = max(-360, min(360, hue))
    sat = max(-100, min(100, sat))

    edited = apply_hue_saturation(img, hue, sat)

    buf = io.BytesIO()
    edited.save(buf, format="PNG")
    buf.seek(0)

    await ctx.send(file=discord.File(buf, "edited.png"))

@bot.command()
async def invert(ctx):
    """Invert uploaded image."""
    if not ctx.message.attachments:
        await ctx.send("Please upload an image.")
        return

    attachment = ctx.message.attachments[0]
    img_bytes = await attachment.read()
    img = Image.open(io.BytesIO(img_bytes)).convert("RGB")

    edited = apply_invert(img)

    buf = io.BytesIO()
    edited.save(buf, format="PNG")
    buf.seek(0)

    await ctx.send(file=discord.File(buf, "inverted.png"))

@bot.command()
async def fisheye(ctx, strength: float = 0.5):
    """Apply fisheye effect."""
    if not ctx.message.attachments:
        await ctx.send("Please upload an image.")
        return

    attachment = ctx.message.attachments[0]
    img_bytes = await attachment.read()
    img = Image.open(io.BytesIO(img_bytes)).convert("RGB")

    strength = max(-1, min(1, strength))
    edited = apply_fisheye(img, strength)

    buf = io.BytesIO()
    edited.save(buf, format="PNG")
    buf.seek(0)

    await ctx.send(file=discord.File(buf, "fisheye.png"))

# === AUDIO EXAMPLE (SoX with subprocess) ===
@bot.command()
async def volume(ctx, level: float = 1.0):
    """Change audio volume (0 to 10)."""
    if not ctx.message.attachments:
        await ctx.send("Please upload an audio file.")
        return

    attachment = ctx.message.attachments[0]
    input_bytes = await attachment.read()
    with open("input.wav", "wb") as f:
        f.write(input_bytes)

    # Use SoX for volume adjustment
    subprocess.run(["sox", "input.wav", "output.wav", "vol", str(level)])

    await ctx.send(file=discord.File("output.wav"))

bot.run("YOUR_DISCORD_BOT_TOKEN")
