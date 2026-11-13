"""Development-only synthetic diagram generator; requires Pillow, not used by app."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import json, hashlib, shutil

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'samples'
FONT='C:/Windows/Fonts/msyh.ttc'
def font(n):
    return ImageFont.truetype(FONT,n) if Path(FONT).exists() else ImageFont.load_default()

CASES=[
 ('清晰禁停标志与车辆','yes','yes','no','yes','candidate','车辆与右侧禁停标志处于相邻路侧。','需核对适用范围与停车状态。'),
 ('黄色路侧线与车辆','yes','no','yes','yes','candidate','车辆相邻路侧可见连续黄色线条。','需确认标线性质与适用规则。'),
 ('标志被树木遮挡','yes','unclear','no','unclear','uncertain','右侧标志被树木部分遮挡。','无法完整辨认标志。'),
 ('路段没有可见禁停线索','yes','no','no','unclear','none','画面中有车辆，未见相关标志或标线。','画外可能存在其他信息。'),
 ('夜间低照度','yes','unclear','unclear','unclear','uncertain','夜间图像中仅能辨认车辆轮廓。','照度过低，标志和标线无法确认。'),
 ('标志在道路另一侧','yes','yes','no','unclear','uncertain','禁停标志与车辆分处道路两侧。','不能据此确认车辆位于适用范围。'),
 ('有禁停标志但没有车辆','no','yes','no','no','uncertain','路侧可见禁停标志，图中无车辆。','不构成含车辆的候选证据。'),
 ('停车场指示牌','yes','no','no','no','none','车辆旁为 P 停车指示牌。','不能将停车指示牌当作禁停标志。'),
 ('雨天模糊标线','yes','no','unclear','unclear','uncertain','雨天路侧线条模糊。','无法可靠判断标线类型。'),
 ('多辆车与禁停标志','yes','yes','yes','yes','candidate','右侧禁停标志、黄色线条及相邻车辆同时可见。','需逐车核实适用范围。'),
 ('车辆遮住路侧标线','yes','no','unclear','unclear','uncertain','车辆下方路侧线条被遮挡。','无法判定被遮挡部分是否连续。'),
 ('空路段无禁停线索','no','no','no','no','none','画面无车辆、禁停标志或相关标线。','仅对应当前视角。'),
]

def draw_scene(i):
    im=Image.new('RGB',(1000,620),'#dce9eb');d=ImageDraw.Draw(im)
    night=i==4
    for x,y,w in [(35,150,155),(225,100,185),(450,170,140),(785,110,170)]:
        d.rectangle((x,y,x+w,325),fill='#9bb4be')
        for xx in range(x+16,x+w-10,38):
            for yy in range(y+20,300,45): d.rectangle((xx,yy,xx+19,yy+23),fill='#d9e5df')
    d.rectangle((0,300,1000,355),fill='#a7b6a4');d.rectangle((0,355,1000,620),fill='#536874')
    for x in range(0,1000,140):d.rectangle((x,490,x+70,495),fill='#dbe6df')
    if i in (1,8,9,10):d.line((0,380,1000,380),fill='#f1c75c',width=7)
    if i in (0,2,4,5,6,9):
        cx,cy=(145,522) if i==5 else (820,245)
        d.line((cx,cy,cx,565 if i==5 else 355),fill='#d4dedc',width=8)
        d.ellipse((cx-37,cy-37,cx+37,cy+37),fill='#295c9b',outline='#ee675b',width=7)
        d.line((cx-25,cy-25,cx+25,cy+25),fill='#ee675b',width=6)
        d.line((cx+25,cy-25,cx-25,cy+25),fill='#ee675b',width=6)
    if i==2:
        d.rectangle((862,205,875,355),fill='#675b49');d.ellipse((794,190,902,270),fill='#3c7355')
    if i==7:
        d.line((820,245,820,355),fill='#dde5df',width=7);d.rectangle((785,210,855,280),fill='#2f699f');d.text((805,210),'P',font=font(50),fill='white')
    def car(x,y,color):
        d.polygon([(x+30,y),(x+65,y-47),(x+172,y-47),(x+215,y)],fill='#c8dce0')
        d.rounded_rectangle((x,y,x+245,y+64),14,fill=color)
        for wheel in (x+47,x+195): d.ellipse((wheel-21,y+41,wheel+21,y+83),fill='#233845')
    if i not in (6,11):car(380,360,'#398f96')
    if i==9:car(55,360,'#cc9b70')
    if i==4:
        overlay=Image.new('RGB',im.size,'#071a2c');im=Image.blend(im,overlay,.76)
    if i==8:
        im=im.filter(ImageFilter.GaussianBlur(3));d=ImageDraw.Draw(im)
        for x in range(20,1000,33): d.line((x,110,x-80,620),fill='#bdcbd0',width=2)
    d=ImageDraw.Draw(im)
    d.rectangle((0,0,1000,80),fill='#193a39')
    d.text((25,13),f'模拟场景 {i+1:02d} / SYNTHETIC DEMO',font=font(23),fill='#d6e7da')
    d.text((25,46),'程序绘制示意图 · 非真实取证照片 · 非模型输出',font=font(17),fill='#b8cebd')
    d.rectangle((0,570,1000,620),fill='#e8efea')
    d.text((25,584),CASES[i][0]+'  |  仅用于功能演示',font=font(18),fill='#294740')
    return im

def main():
    for folder in ('images','week-01','week-02'): (OUT/folder).mkdir(parents=True,exist_ok=True)
    manifest=[]
    for i,case in enumerate(CASES):
        name,v,s,m,r,c,e,u=case; filename=f'scene-{i+1:02d}.png'
        im=draw_scene(i);im.save(OUT/'images'/filename)
        week='week-01' if i<8 else 'week-02'
        shutil.copyfile(OUT/'images'/filename,OUT/week/filename)
        manifest.append(dict(filename=filename,name=name,batch='模拟数据 · 第1周' if i<8 else '模拟数据 · 第2周',sha256=hashlib.sha256((OUT/'images'/filename).read_bytes()).hexdigest(),result=dict(vehicle=v,sign=s,marking=m,relation=r,category=c,evidence=[e],uncertainties=[u])))
    for i in (0,3):shutil.copyfile(OUT/'images'/f'scene-{i+1:02d}.png',OUT/'week-02'/f'repeated-scene-{i+1:02d}.png')
    (OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    sheet=Image.new('RGB',(1200,1040),'#f4f6f3')
    for i in range(12):sheet.paste(draw_scene(i).resize((390,242)),((i%3)*400+5,(i//3)*260+5))
    sheet.save(OUT/'contact-sheet.jpg')

if __name__=='__main__':main()
