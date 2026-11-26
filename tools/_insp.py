from PIL import Image
im = Image.open('tools/_backup_v3.png').convert('RGB')
# 招牌A「新世界」大範圍
im.crop((20, 470, 230, 630)).resize((1050, 800), Image.LANCZOS).save('tools/_inspA.png')
# 招牌B「文夷康」大範圍
im.crop((790, 530, 990, 680)).resize((1000, 750), Image.LANCZOS).save('tools/_inspB.png')
# 底部葡文路牌 BESSA FDA 區域
im.crop((600, 1380, 1024, 1536)).resize((1060, 390), Image.LANCZOS).save('tools/_inspC.png')
print('ok')
