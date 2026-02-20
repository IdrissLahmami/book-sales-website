from PIL import Image, ImageDraw, ImageFont
import os

covers = [
    ("cover_python_beginners.jpg", "Python\nBeginners"),
    ("cover_advanced_web_dev.jpg", "Advanced\nWeb Dev"),
    ("cover_data_science.jpg", "Data Science"),
    ("cover_flutter_dev.jpg", "Flutter Dev"),
    ("cover_cybersecurity.jpg", "Cybersecurity"),
]

output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "uploads")
os.makedirs(output_dir, exist_ok=True)

for filename, text in covers:
    img = Image.new("RGB", (320, 480), color=(13, 110, 253))
    d = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 32)
    except:
        font = ImageFont.load_default()
    # Calculate multiline text size manually
    lines = text.split("\n")
    line_heights = []
    max_width = 0
    for line in lines:
        bbox = font.getbbox(line)
        w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        max_width = max(max_width, w)
        line_heights.append(h)
    total_height = sum(line_heights) + (len(lines)-1)*10
    y = (480 - total_height) / 2
    for i, line in enumerate(lines):
        bbox = font.getbbox(line)
        w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        x = (320 - w) / 2
        d.text((x, y), line, fill=(255,255,255), font=font, align="center")
        y += h + 10
    img.save(os.path.join(output_dir, filename))
print("Placeholder book covers generated.")
