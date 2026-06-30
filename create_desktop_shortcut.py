import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter


ROOT = Path(__file__).resolve().parent
STATIC_DIR = ROOT / "src" / "ai_news_agent" / "static"
ASSET_DIR = ROOT / "assets"
PNG_PATH = STATIC_DIR / "app_icon.png"
ICO_PATH = ASSET_DIR / "ai_news_agent.ico"
BAT_PATH = ROOT / "start_news_app.bat"
VBS_PATH = ROOT / "start_news_app_silent.vbs"


def rounded_rect_mask(size: int, radius: int) -> Image.Image:
    mask = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle((0, 0, size, size), radius=radius, fill=255)
    return mask


def draw_icon(size: int = 512) -> Image.Image:
    """Create a simple original icon for the local app."""
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    mask = rounded_rect_mask(size, 112)

    background = Image.new("RGBA", (size, size), "#062f35")
    draw = ImageDraw.Draw(background)
    for y in range(size):
        ratio = y / size
        color = (
            int(6 + 20 * ratio),
            int(47 + 85 * ratio),
            int(53 + 70 * ratio),
            255,
        )
        draw.line((0, y, size, y), fill=color)

    glow = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    glow_draw.ellipse((92, 66, 420, 394), fill=(30, 210, 176, 58))
    glow = glow.filter(ImageFilter.GaussianBlur(34))
    background.alpha_composite(glow)

    icon_draw = ImageDraw.Draw(background)
    line = (218, 255, 247, 240)
    accent = (54, 218, 184, 255)

    paths = [
        ((122, 192), (206, 96), (306, 96), (390, 192)),
        ((122, 320), (206, 416), (306, 416), (390, 320)),
        ((144, 140), (88, 254), (144, 372), (256, 392)),
        ((368, 140), (424, 254), (368, 372), (256, 392)),
        ((132, 256), (210, 168), (302, 168), (380, 256)),
        ((132, 256), (210, 344), (302, 344), (380, 256)),
    ]

    soft_shadow = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(soft_shadow)
    for path in paths:
        shadow_draw.line(path, fill=(1, 28, 32, 70), width=34, joint="curve")
    soft_shadow = soft_shadow.filter(ImageFilter.GaussianBlur(7))
    background.alpha_composite(soft_shadow)

    for index, path in enumerate(paths):
        icon_draw.line(path, fill=accent if index in (0, 1) else line, width=24, joint="curve")

    icon_draw.rounded_rectangle((196, 214, 316, 298), radius=22, fill=(247, 255, 253, 250))
    icon_draw.line((222, 240, 290, 240), fill="#087f72", width=10)
    icon_draw.line((222, 268, 276, 268), fill="#087f72", width=10)

    image.alpha_composite(background)
    image.putalpha(mask)
    return image


def save_icon_files() -> None:
    STATIC_DIR.mkdir(parents=True, exist_ok=True)
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    image = draw_icon()
    image.save(PNG_PATH)
    image.save(ICO_PATH, sizes=[(16, 16), (32, 32), (48, 48), (128, 128), (256, 256)])


def create_shortcut() -> Path:
    ps = f"""
    $desktop = [Environment]::GetFolderPath('Desktop')
    if (-not (Test-Path -LiteralPath $desktop)) {{
      New-Item -ItemType Directory -Path $desktop | Out-Null
    }}
    $shortcutPath = Join-Path $desktop 'AI News Agent.lnk'
    $shell = New-Object -ComObject WScript.Shell
    $shortcut = $shell.CreateShortcut($shortcutPath)
    $shortcut.TargetPath = 'wscript.exe'
    $shortcut.Arguments = '"{VBS_PATH}"'
    $shortcut.WorkingDirectory = '{ROOT}'
    $shortcut.IconLocation = '{ICO_PATH}'
    $shortcut.Description = 'Open the local AI news monitor'
    $shortcut.Save()
    Write-Output $shortcutPath
    """
    result = subprocess.check_output(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps],
        text=True,
    )
    return Path(result.strip().splitlines()[-1])


def main() -> None:
    save_icon_files()
    shortcut = create_shortcut()
    print(f"Created icon: {ICO_PATH}")
    print(f"Created shortcut: {shortcut}")


if __name__ == "__main__":
    main()
