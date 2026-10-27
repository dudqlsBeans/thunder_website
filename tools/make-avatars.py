#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Crop the portraits in people/ into round avatars for the site.

    python3 tools/make-avatars.py            # rebuild assets/img/people/
    python3 tools/make-avatars.py --sheet    # also write a contact sheet to check framing

HOW TO MOVE SOMEONE'S FACE
--------------------------
Add or edit a line in CROP below, keyed by the person's Korean name exactly as
the file in people/ is named. The three numbers are:

    '김한별': (cx, cy, zoom)

    cx    horizontal centre of the crop, 0.0 = left edge, 1.0 = right edge
    cy    vertical centre,                0.0 = top edge,  1.0 = bottom edge
    zoom  size of the square, as a fraction of the photo's SHORT edge.
          1.0 = the biggest square that fits. Smaller = tighter on the face.
          ABOVE 1.0 the square is bigger than the photo, and the empty margin
          is filled by extending the photo's own edge pixels outward — on a
          plain studio backdrop that is invisible, and it lets you pull back
          from a portrait that was shot too tight. Try 1.15-1.4.
          Set BG['name'] = '#rrggbb' to force a flat fill colour instead.
          If a scan has a white border around the photo, list it in TRIM first
          so the padding copies the real backdrop and not the border.

So to move a face DOWN in the circle, make cy SMALLER (the crop moves up, the
face drops toward the middle). To move it RIGHT, make cx SMALLER. To fill more
of the circle with the face, make zoom SMALLER.

Anyone not listed in CROP gets the default: centred horizontally, and pushed
18% toward the top of the frame, which suits a standard headshot.

Re-run the script after editing. Nothing else needs to change — the HTML already
points at these filenames.
"""
import argparse, glob, html, json, os, re, unicodedata
from PIL import Image, ImageDraw, ImageFont, ImageOps

OUT_DIR   = 'assets/img/people'
SRC_DIR   = 'people'
MAX       = 320     # stored size in px; sources smaller than this are never upscaled
TOP_BIAS  = 0.18    # default: how far down the frame the crop starts

# person's Korean name -> (cx, cy, zoom).  See the note above.
CROP = {
    '김도현': (0.5, 0.5, 1.3),
    '박대영': (0.5, 0.5, 1.3),
    '고병현': (0.5, 0.5, 1.3),
    '김진표': (0.5, 0.5, 1.3),
    '이재환': (0.5, 0.5, 1.3),
    '박종원': (0.5, 0.5, 1.3),
    '김한별': (0.5, 0.5, 1.3),
    '이현규': (0.5, 0.5, 1.3),
    '강민규': (0.5, 0.5, 1.3),
    '이상민': (0.5, 0.5, 1.3),
    '손영준': (0.5, 0.5, 1.3),
    '조경제': (0.5, 0.5, 1.3),
    '이규성': (0.5, 0.5, 1.3),
    '이동영': (0.5, 0.5, 1.3),
    '석지헌': (0.5, 0.5, 1.3),
    '김종민': (0.38, 0.5, 1.0),   # landscape holiday photo
    '강다연': (0.5, 0.5, 1.1),
    '소연경': (0.5, 0.5, 1.3),
    '정성목': (0.5, 0.5, 1.2),
    '박수영': (0.5, 0.5, 1.3),
    '김상호': (0.5, 0.35, 1.1),
    '김민수': (0.5, 0.5, 1.3),
    '이창진': (0.5, 0.5, 1.2),
    '박윤희': (0.5, 0.5, 1.3),
    '표영빈': (0.5, 0.5, 1.3),   # mixed backdrop — padding would streak, so keep it inside
    '송원영': (0.50, 0.5, 1.3),
    '김채원': (0.50, 0.5, 1.3),
    '이규성': (0.50, 0.412, 1.26),
    '이창진': (0.50, 0.427, 1.15),   # crown clipped by the frame; pad white above
    '전형근': (0.50, 0.26, 1.0),    # outdoor half-body
    '권택민': (0.5, 0.5, 1.0),
    '황세연': (0.5, 0.5, 1.3),
}

# Optional flat fill for a padded avatar, when edge-extension looks wrong.
# e.g. BG = {'표영빈': '#ffffff'}
BG = {
    # his hair is clipped by the top of the photo, so extending the edge would
    # smear hair upward; his backdrop is pure white, so fill it flat instead
    '이창진': '#ffffff',
}

# Some scans carry a white border around the actual photo. Trim it off first,
# otherwise the padding above copies the border instead of the backdrop.
# Fractions of the source: (left, top, right, bottom).
TRIM = {
    '조경제': (0.07, 0.02, 0.93, 0.98),   # white frame around a grey-backdrop photo
}

nfc = lambda s: unicodedata.normalize('NFC', s)


def square_with_padding(im, x0, y0, side, fill=None):
    """Crop a square that may run outside the photo.

    The part that overlaps the photo is copied as-is; the margin is filled
    either with `fill`, or by stretching the photo's outermost row/column of
    pixels outward, which matches a plain or softly graded backdrop."""
    w, h = im.size
    sx0, sy0 = max(0, x0), max(0, y0)
    sx1, sy1 = min(w, x0 + side), min(h, y0 + side)
    if (sx0, sy0, sx1, sy1) == (x0, y0, x0 + side, y0 + side):
        return im.crop((x0, y0, x0 + side, y0 + side))      # fully inside, no padding

    region = im.crop((sx0, sy0, sx1, sy1))
    rw, rh = region.size
    px, py = sx0 - x0, sy0 - y0
    canvas = Image.new('RGB', (side, side), fill or (255, 255, 255))
    canvas.paste(region, (px, py))
    if fill:
        return canvas
    # extend the region's edges outward, sampling a few pixels in so a stray
    # hairline at the very edge does not get smeared across the whole margin
    i = min(3, max(0, min(rw, rh) // 4 - 1))
    if py > 0:
        canvas.paste(region.crop((0, i, rw, i + 1)).resize((rw, py)), (px, 0))
    if py + rh < side:
        canvas.paste(region.crop((0, rh - 1 - i, rw, rh - i)).resize((rw, side - py - rh)), (px, py + rh))
    if px > 0:
        col = canvas.crop((px + i, 0, px + i + 1, side))
        canvas.paste(col.resize((px, side)), (0, 0))
    if px + rw < side:
        col = canvas.crop((px + rw - 1 - i, 0, px + rw - i, side))
        canvas.paste(col.resize((side - px - rw, side)), (px + rw, 0))
    return canvas


def edge_uniformity(im):
    """How flat the photo's border is, 0 = perfectly uniform. Padding is
    seamless when this is small; a busy border means the fill will show."""
    w, h = im.size
    strip = [im.crop((0, 0, w, 2)), im.crop((0, h - 2, w, h)),
             im.crop((0, 0, 2, h)), im.crop((w - 2, 0, w, h))]
    px = []
    for s_ in strip:
        s_ = s_.resize((min(s_.width, 60), min(s_.height, 60)))
        px += list(s_.getdata())
    n = len(px)
    mean = [sum(c[i] for c in px) / n for i in range(3)]
    var = sum(sum((c[i] - mean[i]) ** 2 for i in range(3)) for c in px) / n
    return var ** 0.5, tuple(int(v) for v in mean)


def load_roster():
    """(english name, korean name) for every person card on the People page."""
    s = open('people.html', encoding='utf-8').read()
    out, seen = [], set()
    for en, kr in re.findall(r'<h4>([^<]+?) <span class="kr">\(([^)]+)\)</span></h4>', s):
        en, kr = html.unescape(en).strip(), nfc(html.unescape(kr))
        if en in seen:
            continue
        seen.add(en)
        out.append((en, kr))
    return out


def source_files():
    files = {}
    for f in glob.glob(os.path.join(SRC_DIR, '*')):
        if os.path.basename(f).startswith('.'):
            continue
        files[nfc(os.path.splitext(os.path.basename(f))[0])] = f
    return files


def build(sheet=False):
    files = source_files()
    os.makedirs(OUT_DIR, exist_ok=True)
    made, missing, soft, busy = {}, [], [], []

    for en, kr in load_roster():
        src = files.get(kr) or files.get(kr + '교수님') or files.get(kr + '_교수님')
        if not src:
            missing.append((en, kr))
            continue

        im = ImageOps.exif_transpose(Image.open(src))
        if im.mode in ('RGBA', 'LA', 'P'):                     # flatten transparency onto white
            im = im.convert('RGBA')
            bg = Image.new('RGB', im.size, (255, 255, 255))
            bg.paste(im, mask=im.split()[-1])
            im = bg
        else:
            im = im.convert('RGB')

        # many scans carry a 1-2px dark hairline around the edge; extending that
        # outward would paint the whole margin dark, so shave it off first
        sw, sh = im.size
        shave = 2 if min(sw, sh) >= 200 else 1
        im = im.crop((shave, shave, sw - shave, sh - shave))

        if kr in TRIM:
            tw, th = im.size
            l, t, r, b = TRIM[kr]
            im = im.crop((int(l * tw), int(t * th), int(r * tw), int(b * th)))

        w, h = im.size
        padded = False
        if kr in CROP:
            cx, cy, zoom = CROP[kr]
            side = max(16, int(min(w, h) * zoom))
            left = int(cx * w - side / 2)
            top  = int(cy * h - side / 2)
            if side <= w and side <= h:                 # fits: keep it inside the photo
                left = max(0, min(left, w - side))
                top  = max(0, min(top,  h - side))
            else:
                padded = True
        else:
            side = min(w, h)
            left = (w - side) // 2
            top  = int(min(max((h - side) * TOP_BIAS, 0), h - side))

        if padded:
            fill = BG.get(kr)
            if isinstance(fill, str):
                fill = tuple(int(fill.lstrip('#')[i:i + 2], 16) for i in (0, 2, 4))
            spread, mean = edge_uniformity(im)
            if spread > 18 and not fill:
                busy.append((en, round(spread)))
            im = square_with_padding(im, left, top, side, fill)
        else:
            im = im.crop((left, top, left + side, top + side))
        out_side = min(side, MAX)
        if side != out_side:
            im = im.resize((out_side, out_side), Image.LANCZOS)

        slug = re.sub(r'[^a-z]+', '-', en.lower()).strip('-')
        path = os.path.join(OUT_DIR, slug + '.jpg')
        im.save(path, 'JPEG', quality=84, optimize=True, progressive=True)
        made[en] = (slug + '.jpg', out_side, kr)
        if out_side < 144:
            soft.append((en, out_side))

    total = sum(os.path.getsize(os.path.join(OUT_DIR, v[0])) for v in made.values())
    print('wrote %d avatars to %s  (%.0f KB total)' % (len(made), OUT_DIR, total / 1024))
    if missing:
        print('no photo found for:', ', '.join('%s (%s)' % m for m in missing))
    if soft:
        print('source below 144px, soft on retina:', ', '.join('%s %dpx' % s for s in soft))
    if busy:
        print('padded, but the photo border is not flat so the fill may show:',
              ', '.join('%s' % b[0] for b in busy),
              '\n  -> set BG[name] to a colour, or lower that zoom back under 1.0')
    json.dump({k: v[0] for k, v in made.items()}, open('/tmp/photomap.json', 'w'))
    if sheet:
        contact_sheet(made)
    return made


def contact_sheet(made, path='avatar-check.png'):
    items = sorted(made.items(), key=lambda kv: kv[0])
    COLS, CELL, PAD, LABEL = 8, 132, 16, 24
    rows = (len(items) + COLS - 1) // COLS
    W, H = COLS * (CELL + PAD) + PAD, rows * (CELL + PAD + LABEL) + PAD + 40
    sheet = Image.new('RGB', (W, H), (10, 11, 13))
    d = ImageDraw.Draw(sheet)
    def font(size, bold=False):
        for path in ('/System/Library/Fonts/AppleSDGothicNeo.ttc',        # has Hangul
                     '/System/Library/Fonts/Supplemental/AppleGothic.ttf',
                     '/System/Library/Fonts/Supplemental/Arial Bold.ttf' if bold
                     else '/System/Library/Fonts/Supplemental/Arial.ttf'):
            try:
                return ImageFont.truetype(path, size, index=4 if bold and path.endswith('.ttc') else 0)
            except Exception:
                continue
        return ImageFont.load_default()
    f, fb = font(12), font(15, bold=True)
    d.text((PAD, 12), 'avatars as cropped for the site   (amber = source under 144px, · = has a CROP override)',
           font=fb, fill=(232, 236, 238))
    for i, (en, (fn, side, kr)) in enumerate(items):
        x = PAD + (i % COLS) * (CELL + PAD)
        y = 40 + PAD + (i // COLS) * (CELL + PAD + LABEL)
        im = Image.open(os.path.join(OUT_DIR, fn)).resize((CELL, CELL), Image.LANCZOS)
        mask = Image.new('L', (CELL, CELL), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, CELL - 1, CELL - 1), fill=255)
        sheet.paste(im, (x, y), mask)
        d.ellipse((x, y, x + CELL - 1, y + CELL - 1), outline=(70, 78, 84))
        label = ('· ' if kr in CROP else '') + kr
        tw = d.textlength(label, font=f)
        d.text((x + (CELL - tw) / 2, y + CELL + 6), label, font=f,
               fill=(162, 172, 178) if side >= 144 else (232, 171, 111))
    sheet.save(path)
    print('contact sheet ->', path)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--sheet', action='store_true', help='also write avatar-check.png')
    build(**vars(ap.parse_args()))
