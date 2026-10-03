import os
import re
import json
import base64
from io import BytesIO
from PIL import Image

wp_dir = 'wallpaper'

# Mapping of known files to custom IDs and Names
METADATA = {
    'IMG_2833.PNG': { 'id': 'bunny_snow', 'name': '兔可可 · 纯真雪白' }
}

# Scan all raw images in wallpaper directory
raw_files = [f for f in os.listdir(wp_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))
             and not f.endswith('.opt.jpg') and not f.endswith('.min.b64')]

for rf in raw_files:
    if rf not in METADATA and rf != 'IMG_2833.PNG':
        clean_name = re.sub(r'\.[^.]+$', '', rf).replace('_', ' ').replace('-', ' ').strip()
        METADATA[rf] = {
            'id': 'wp_' + re.sub(r'[^a-zA-Z0-9_]', '', clean_name)[:20].lower(),
            'name': clean_name.title() or '自选座舱壁纸'
        }

# Read existing manifest
manifest_path = os.path.join(wp_dir, 'manifest.json')
if os.path.exists(manifest_path):
    with open(manifest_path, 'r', encoding='utf-8') as f:
        manifest_data = json.load(f)
else:
    manifest_data = {'wallpapers': []}

# Keep the base b64 split wallpapers (IMG_2833)
base_wallpapers = [w for w in manifest_data.get('wallpapers', []) if w.get('b64')]
if not base_wallpapers and os.path.exists(os.path.join(wp_dir, 'IMG_2833.min.b64.p1')):
    base_wallpapers = [{
        "id": "bunny_snow",
        "name": "兔可可 · 纯真雪白",
        "file": "wallpaper/IMG_2833.min.b64",
        "raw": "wallpaper/IMG_2833.PNG",
        "b64": True,
        "parts": 3,
        "size": 334780
    }]

placeholders = {
    "wallpaper/IMG_2833.min.b64": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDABQODxIPDRQSEBIXFRQYHjIhHhwcHj0sLiQySUBMS0dARkVQWnNiUFVtVkVGZIhlbXd7gYKBTmCNl4x9lnN+gXz/2wBDARUXFx4aHjshITt8U0ZTfHx8fHx8fHx8fHx8fHx8fHx8fHx8fHx8fHx8fHx8fHx8fHx8fHx8fHx8fHx8fHx8fHz/wAARCAAbADADASIAAhEBAxEB/8QAHwAAAQUBAQEBAQEAAAAAAAAAAAECAwQFBgcICQoL/8QAtRAAAgEDAwIEAwUFBAQAAAF9AQIDAAQRBRIhMUEGE1FhByJxFDKBkaEII0KxwRVS0fAkM2JyggkKFhcYGRolJicoKSo0NTY3ODk6Q0RFRkdISUpTVFVWV1hZWmNkZWZnaGlqc3R1dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWmp6ipqrKztLW2t7i5usLDxMXGx8jJytLT1NXW19jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn6/8QAHwEAAwEBAQEBAQEBAQAAAAAAAAECAwQFBgcICQoL/8QAtREAAgECBAQDBAcFBAQAAQJ3AAECAxEEBSExBhJBUQdhcRMiMoEIFEKRobHBCSMzUvAVYnLRChYkNOEl8RcYGRomJygpKjU2Nzg5OkNERUZHSElKU1RVVldYWVpjZGVmZ2hpanN0dXZ3eHl6goOEhYaHiImKkpOUlZaXmJmaoqOkpaanqKmqsrO0tba3uLm6wsPExcbHyMnK0tPU1dbX2Nna4uPk5ebn6Onq8vP09fb3+Pn6/9oADAMBAAIRAxEAPwDm43ZVAJNXbd9zEljkdAKWC2RpDnzHUHgRr1H1pxsZNxZUKAHjcaTV0BuaDNI0M4ZwwQ5Jqgy+c8rICSCSfQCn2QvLRH8hlAY/MCM5qSzQpKxKhycgZHIzUy1SQ0QBBGhkZTHEOSx6n8KkW1M2VjwcdiR0Ipt6kzXHzIzQoQQCeD7YqhdR3Czu6CUB2JUdMDNNJJaA3qXkVnxIHcJ/efgH6DqamM6KOFdjjktjP4elVkdmUFiSaCTmk433C5OtwAG+WXHXDEU1Z/lJAYH2bFLHyGB9Krr1o5UFywb8AKHiLAf3iDmnxXFu453REHorcVnygZz61CeDx6UKNth3P//Z"
}

new_wallpapers = []

for raw_name, meta in METADATA.items():
    if raw_name == 'IMG_2833.PNG':
        continue
    raw_path = os.path.join(wp_dir, raw_name)
    if not os.path.exists(raw_path):
        print(f"Skipping {raw_name}, not found")
        continue

    # 1. Optimize image: max 1920 width, progressive JPEG quality 82
    opt_name = re.sub(r'\.[^/.]+$', '.opt.jpg', raw_name)
    opt_path = os.path.join(wp_dir, opt_name)
    
    with Image.open(raw_path) as img:
        img = img.convert('RGB')
        w, h = img.size
        MAX_DIM = 1920
        if w > MAX_DIM or h > MAX_DIM:
            if w > h:
                new_w = MAX_DIM
                new_h = int(h * MAX_DIM / w)
            else:
                new_h = MAX_DIM
                new_w = int(w * MAX_DIM / h)
            img_resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        else:
            img_resized = img

        img_resized.save(opt_path, 'JPEG', quality=82, progressive=True, optimize=True)
        opt_size = os.path.getsize(opt_path)

        # 2. Generate 32x20 tiny thumbnail for blur-up placeholder
        thumb = img.resize((32, 20), Image.Resampling.BOX)
        buf = BytesIO()
        thumb.save(buf, format='JPEG', quality=60)
        b64_ph = "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode('ascii')
        
        file_key = f"wallpaper/{opt_name}"
        placeholders[file_key] = b64_ph
        placeholders[f"wallpaper/{raw_name}"] = b64_ph

        new_entry = {
            "id": meta['id'],
            "name": meta['name'],
            "file": file_key,
            "b64": False,
            "size": opt_size
        }
        new_wallpapers.append(new_entry)
        raw_size = os.path.getsize(raw_path)
        print(f"Optimized {raw_name}: {raw_size/1024:.1f} KB -> {opt_size/1024:.1f} KB (-{(1 - opt_size/raw_size)*100:.1f}%)")

# Combine all wallpapers
all_wallpapers = base_wallpapers + new_wallpapers
manifest_data['wallpapers'] = all_wallpapers
manifest_data['updatedAt'] = "2026-10-03T11:10:00Z"
manifest_data['note'] = "开源精简版壁纸包: 包含经典兔可可高清壁纸 (IMG_2833.PNG) 与 3 分片渐进式流式壁纸"

with open(manifest_path, 'w', encoding='utf-8') as f:
    json.dump(manifest_data, f, ensure_ascii=False, indent=2)

print(f"\nManifest successfully updated with {len(all_wallpapers)} wallpapers!")

# Save placeholders mapping to JSON
with open(os.path.join(wp_dir, 'placeholders.json'), 'w', encoding='utf-8') as f:
    json.dump(placeholders, f, ensure_ascii=False, indent=2)

print(f"Placeholders saved ({len(placeholders)} entries)!")
