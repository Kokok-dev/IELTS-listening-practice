from pathlib import Path
from PIL import Image,ImageDraw
root=Path(__file__).resolve().parents[1]
dest=root/'assets';dest.mkdir(exist_ok=True)
image=Image.new('RGBA',(1024,1024),(0,0,0,0))
draw=ImageDraw.Draw(image)
draw.rounded_rectangle((20,20,1004,1004),radius=270,fill='#6257d7')
draw.arc((250,220,774,770),180,360,fill='white',width=58)
draw.rounded_rectangle((230,465,355,760),radius=45,fill='white')
draw.rounded_rectangle((669,465,794,760),radius=45,fill='white')
draw.line((765,690,765,765,670,815,540,815),fill='white',width=32)
draw.rounded_rectangle((472,786,575,844),radius=22,fill='white')
image.save(dest/'juting.ico',sizes=[(16,16),(24,24),(32,32),(48,48),(64,64),(128,128),(256,256)])
image.resize((256,256),Image.Resampling.LANCZOS).save(dest/'juting.png')
print(dest/'juting.ico')
