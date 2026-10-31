import sys, math, cadquery as cq
sys.argv=[sys.argv[0]]+sys.argv[1:3]
ns={}; src=open('bracket.py').read().replace('cq.exporters.export(body,"bracket.step")','')
exec(src,ns)
A,B,X,hull,body=ns['A'],ns['B'],ns['X'],ns['hull'],ns['body']
Z=X/2+10
def lug(pts_fn):
    return pts_fn.extrude(60,both=True).intersect(hull)
# AA block: z 30..50, from x=0 to Z+10, top-right corner R10 about hole (Z,40)
aa=(cq.Workplane("XZ").moveTo(0,30).lineTo(Z+10,30).lineTo(Z+10,40)
    .threePointArc((Z+10*math.cos(math.radians(45)),40+10*math.sin(math.radians(45))),(Z,50))
    .lineTo(0,50).close())
# BB block: z 0..20, from x=A-25 to A, top-left corner R10 about hole (A-15,10)
bb=(cq.Workplane("XZ").moveTo(A,0).lineTo(A,20).lineTo(A-15,20)
    .threePointArc((A-15-10*math.cos(math.radians(45)),10+10*math.sin(math.radians(45))),(A-25,10))
    .lineTo(A-25,0).close())
body=body.union(lug(aa)).union(lug(bb))
# re-cut tube bores, then Ø10 holes through all along Y
body=body.cut(cq.Workplane("XY").circle(X/2-4).extrude(300,both=True))
body=body.cut(cq.Workplane("XY").center(A,0).circle(8.5).extrude(300,both=True))
for (hx,hz) in [(Z,40),(A-15,10)]:
    body=body.cut(cq.Workplane("XZ").center(hx,hz).circle(5).extrude(100,both=True))
v=body.val().Volume(); print(f"A={A} B={B} Z={Z} vol={v:.2f} mass={v*0.0027:.2f} g")
cq.exporters.export(body,"bracket_mod.step")
