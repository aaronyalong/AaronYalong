"""Compose a git-koi swimming around a git-bonsai into one looping GIF."""
import argparse
import os
from PIL import Image


def frames(path):
    im = Image.open(path)
    out = []
    for i in range(getattr(im, "n_frames", 1)):
        im.seek(i)
        out.append((im.convert("RGBA"), im.info.get("duration", 100)))
    return out


def union(boxes):
    boxes = [b for b in boxes if b]
    return (min(b[0] for b in boxes), min(b[1] for b in boxes),
            max(b[2] for b in boxes), max(b[3] for b in boxes))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bonsai", default="output/bonsai.gif")
    ap.add_argument("--koi", default="koi/koi.gif")
    ap.add_argument("--out", default="pond/pond.gif")
    ap.add_argument("--tree-scale", type=int, default=2)
    ap.add_argument("--squash", type=float, default=0.30, help="ellipse height / width")
    ap.add_argument("--koi-scale", type=float, default=0.75)
    a = ap.parse_args()

    tree = frames(a.bonsai)
    koi = frames(a.koi)

    # crop the swaying tree to the union of its frames, upscale with nearest to keep pixels crisp
    tb = union(f.getbbox() for f, _ in tree)
    s = a.tree_scale
    tree_imgs = [f.crop(tb).resize(((tb[2] - tb[0]) * s, (tb[3] - tb[1]) * s), Image.NEAREST)
                 for f, _ in tree]
    tree_ms = [d for _, d in tree]
    tw, th = tree_imgs[0].size

    kw, kh = koi[0][0].size
    W, H = 900, 900
    tree_top = 120
    # centre the orbit on the pot, not the whole tree, since crowns lean
    pot = tree_imgs[0].crop((0, int(th * 0.8), tw, th)).getbbox()
    pot_cx = (pot[0] + pot[2]) / 2 if pot else tw / 2
    tree_x = W // 2 - round(pot_cx)
    cx = W // 2
    pot_y = tree_top + int(th * 0.84)

    total = sum(tree_ms)
    out, durs, t = [], [], 0
    for kf, kd in koi:
        kb = kf.getbbox()
        sprite = kf.crop(kb)
        if a.koi_scale != 1:
            sprite = sprite.resize((max(1, round(sprite.width * a.koi_scale)),
                                    max(1, round(sprite.height * a.koi_scale))), Image.NEAREST)
        sx = (kb[0] + kb[2]) / 2 - kw / 2
        sy = (kb[1] + kb[3]) / 2 - kh / 2
        px = cx + sx * 1.15
        py = pot_y + sy * a.squash
        near = sy > 0  # lower half of the circle is nearer the viewer

        # tree frame playing at this moment
        m, acc, ti = t % total, 0, 0
        for i, d in enumerate(tree_ms):
            acc += d
            if m < acc:
                ti = i
                break

        canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        k_xy = (round(px - sprite.width / 2), round(py - sprite.height / 2))
        if not near:
            canvas.alpha_composite(sprite, k_xy)
        canvas.alpha_composite(tree_imgs[ti], (tree_x, tree_top))
        if near:
            canvas.alpha_composite(sprite, k_xy)
        out.append(canvas)
        durs.append(kd)
        t += kd

    ub = union(f.getbbox() for f in out)
    pad = 8
    ub = (max(0, ub[0] - pad), max(0, ub[1] - pad), min(W, ub[2] + pad), min(H, ub[3] + pad))
    out = [f.crop(ub) for f in out]

    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    out[0].save(a.out, save_all=True, append_images=out[1:], duration=durs,
                loop=0, disposal=2, optimize=False)
    out[0].save(os.path.splitext(a.out)[0] + ".png")
    print("wrote", a.out, out[0].size, len(out), "frames")


if __name__ == "__main__":
    main()
