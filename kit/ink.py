"""Hand-drawn ink outlines from normal + object-id passes; composites onto a beauty render."""
import sys
import numpy as np
import skia


def load(p):
    return skia.Image.open(p).toarray(colorType=skia.ColorType.kRGBA_8888_ColorType).astype(np.float32) / 255


def shift(a, dy, dx):
    return np.roll(np.roll(a, dy, 0), dx, 1)


def edges(nrm, oid, thr_n=0.45):
    n = nrm[..., :3]
    e = np.zeros(n.shape[:2], np.float32)
    for dy, dx in ((0, 1), (1, 0), (1, 1), (1, -1)):
        dn = np.abs(n - shift(n, dy, dx)).sum(-1)
        e = np.maximum(e, (dn > thr_n).astype(np.float32))
        di = np.abs(oid[..., 0] - shift(oid, dy, dx)[..., 0])
        e = np.maximum(e, (di > 0.02).astype(np.float32))
    return e


def dilate(m, r):
    out = m.copy()
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            if dy * dy + dx * dx <= r * r:
                out = np.maximum(out, shift(m, dy, dx))
    return out


def wobble(m, amp=1.5, seed=0):
    h, w = m.shape
    rs = np.random.RandomState(seed)
    g = 40
    lo = rs.randn(h // g + 3, w // g + 3, 2)
    # bilinear upsample for smooth displacement
    yy0 = np.linspace(0, lo.shape[0] - 2, h); xx0 = np.linspace(0, lo.shape[1] - 2, w)
    y0 = yy0.astype(int); x0 = xx0.astype(int); fy = (yy0 - y0)[:, None, None]; fx = (xx0 - x0)[None, :, None]
    a = lo[y0][:, x0]; b = lo[y0][:, x0 + 1]; c = lo[y0 + 1][:, x0]; d = lo[y0 + 1][:, x0 + 1]
    ky = (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy
    yy, xx = np.mgrid[0:h, 0:w]
    sy = np.clip((yy + ky[..., 0] * amp * 3).astype(int), 0, h - 1)
    sx = np.clip((xx + ky[..., 1] * amp * 3).astype(int), 0, w - 1)
    return m[sy, sx]


def ink_composite(beauty_p, nrm_p, id_p, out_p, width=2, col=(0.08, 0.055, 0.04), seed=0):
    b = load(beauty_p); n = load(nrm_p); i = load(id_p)
    e = edges(n, i)
    e[:3, :] = 0; e[-3:, :] = 0; e[:, :3] = 0; e[:, -3:] = 0
    e = wobble(dilate(e, width), 1.4, seed)
    # soften
    e = (e * 4 + shift(e, 1, 0) + shift(e, 0, 1) + shift(e, -1, 0) + shift(e, 0, -1)) / 8
    a = np.clip(e * 1.15, 0, 1)[..., None] * 0.92
    ba = b[..., 3:4]
    rgb_pm = b[..., :3] * ba  # premultiplied
    out_a = ba + a * (1 - ba) * 0 + a - ba * a
    rgb = rgb_pm * (1 - a) + np.array(col, np.float32) * a
    rgb = rgb / np.maximum(out_a, 1e-4)
    outa = (np.clip(np.dstack([rgb, out_a]), 0, 1) * 255).astype(np.uint8)
    skia.Image.fromarray(outa).save(out_p, skia.kPNG)


if __name__ == "__main__":
    ink_composite(*sys.argv[1:5], width=int(sys.argv[5]) if len(sys.argv) > 5 else 2)
