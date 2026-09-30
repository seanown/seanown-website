import numpy as np
from PIL import Image, ImageFilter

im = Image.open('tools/_backup_v3.png').convert('RGB')

def inpaint_box(a, mask):
    filled = a.copy()
    unknown = mask.copy()
    rad = 12
    while unknown.any() and rad >= 1:
        known = (~unknown).astype(np.float64)
        kb = np.asarray(Image.fromarray((known*255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(rad))).astype(np.float64)/255.0
        todo_all = unknown & (kb > 0.05)
        if not todo_all.any():
            if rad <= 1: break
            rad = max(1, rad//2); continue
        src = filled * known[:,:,None]
        for c in range(3):
            ch = Image.fromarray(src[:,:,c].clip(0,255).astype(np.uint8))
            cb = np.asarray(ch.filter(ImageFilter.GaussianBlur(rad))).astype(np.float64)
            est = cb / np.maximum(kb, 1e-3)
            filled[todo_all, c] = est[todo_all]
        unknown = unknown & ~todo_all
        rad = max(1, rad//2)
    return filled

def clean(im, box, mask_fn, dilate=3, noise=8):
    X0,Y0,X1,Y1 = box
    a = np.asarray(im.crop(box)).astype(np.float64)
    mask = mask_fn(a)
    n0 = int(mask.sum())
    m_img = Image.fromarray((mask*255).astype(np.uint8)).filter(ImageFilter.MaxFilter(dilate*2+1))
    mask = np.asarray(m_img) > 0
    filled = inpaint_box(a, mask)
    # 絲網紋理噪點（僅填補區）
    ns = np.asarray(Image.effect_noise((X1-X0, Y1-Y0), noise).convert('L')).astype(np.float64) - 128
    sub = mask.astype(np.float64)[:,:,None]
    filled = filled + ns[:,:,None]*sub
    out = Image.fromarray(filled.clip(0,255).astype(np.uint8))
    im.paste(out, (X0,Y0))
    print(f'{box}: raw={n0}, dilated={int(mask.sum())}')
    return out

# A 「新世界」：橙紅字於深灰綠面板
clean(im, (58, 501, 170, 579), lambda a: (a[:,:,0]-a[:,:,1] > 40) & (a[:,:,0] > 110))
# B 「文夷康」：深紅字於黃綠面板
clean(im, (838, 588, 932, 628), lambda a: (a[:,:,0]-a[:,:,1] > 35) & (a[:,:,0]-a[:,:,2] > 60))
# C 「BESSA FDA」：深字於米色路牌
clean(im, (872, 648, 970, 684), lambda a: a.mean(axis=2) < 150)

im.save('assets/og/_v4_clean.png')
# 檢視圖
im.crop((20, 470, 230, 630)).resize((1050, 800), Image.LANCZOS).save('tools/_chkA.png')
im.crop((790, 530, 990, 700)).resize((1000, 850), Image.LANCZOS).save('tools/_chkB.png')
print('done')
