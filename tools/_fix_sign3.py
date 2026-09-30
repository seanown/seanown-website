import numpy as np
from PIL import Image, ImageFilter

im = Image.open('tools/_backup_v3.png').convert('RGB')

def clean(im, box, rg_thresh=45):
    X0,Y0,X1,Y1 = box
    region = im.crop(box)
    a = np.asarray(region).astype(np.int16)
    r,g,b = a[:,:,0], a[:,:,1], a[:,:,2]
    stroke = (r-g > rg_thresh) & (r > 110)
    n0 = stroke.sum()
    bg = a[~stroke]
    mean = bg.mean(axis=0)
    a[stroke] = mean
    r2 = Image.fromarray(a.clip(0,255).astype(np.uint8))
    bl = r2.filter(ImageFilter.GaussianBlur(1.1))
    m = Image.fromarray((stroke*255).astype(np.uint8)).filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.GaussianBlur(0.8))
    r2 = Image.composite(bl, r2, m)
    noise = np.asarray(Image.effect_noise(r2.size, 8).convert('L')).astype(np.int16)-128
    a2 = np.asarray(r2).astype(np.int16)
    sub = np.asarray(m).astype(np.int16)//255
    for c in range(3):
        a2[:,:,c] += noise*sub//9
    im.paste(Image.fromarray(a2.clip(0,255).astype(np.uint8)), (X0,Y0))
    print(f'{box}: stroke={n0}, mean={mean.round(0)}')

# 「新世界」字區（招牌帶內部，避開邊框）
clean(im, (60, 517, 160, 584))
# 「文夷康」字區
clean(im, (850, 578, 925, 620))

im.save('assets/og/_v3_clean.png')
im.crop((40,470,210,610)).resize((850,700), Image.LANCZOS).save('tools/_fixA.png')
im.crop((820,545,960,660)).resize((840,690), Image.LANCZOS).save('tools/_fixB.png')
print('done')
