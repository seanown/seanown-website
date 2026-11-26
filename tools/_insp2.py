from PIL import Image
im = Image.open('tools/_backup_v3.png').convert('RGB')
im.crop((820, 620, 1024, 790)).resize((1020, 850), Image.LANCZOS).save('tools/_inspD.png')
print('ok')
