from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[2]
OUTPUTS = ROOT / "examples" / "outputs"


def draw_demo(size: tuple[int, int], *, title: str) -> Image.Image:
    image = Image.new("RGB", size, "white")
    draw = ImageDraw.Draw(image)
    width, height = size
    draw.rectangle((30, 30, width - 30, height - 30), outline="black", width=3)
    draw.rectangle((80, 90, 330, 210), fill="#e8f2fb", outline="#1f4e79", width=3)
    draw.rectangle((430, 90, 680, 210), fill="#eaf6ea", outline="#357a38", width=3)
    draw.line((340, 150, 420, 150), fill="black", width=4)
    draw.polygon([(420, 150), (400, 140), (400, 160)], fill="black")
    draw.text((90, 105), "Input", fill="black")
    draw.text((440, 105), "Model", fill="black")
    draw.text((60, height - 82), title, fill="black")
    return image


def main() -> None:
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    # 1063 px at 300 dpi is the configured 90 mm single-column width.
    good = draw_demo((1063, 700), title="Synthetic schematic fixture")
    good.save(OUTPUTS / "schematic_demo.png", dpi=(300, 300))
    good.save(OUTPUTS / "schematic_demo.tiff", dpi=(300, 300))
    bad_ga = draw_demo((900, 300), title="Too small graphical abstract")
    bad_ga.save(OUTPUTS / "bad_graphical_abstract.png", dpi=(150, 150))


if __name__ == "__main__":
    main()
