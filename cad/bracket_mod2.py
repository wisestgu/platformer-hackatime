import sys, math, cadquery as cq
sys.argv=[sys.argv[0]]+sys.argv[1:3]
ns={}; exec(open('bracket.py').read().replace('cq.exporters.export(body,"bracket.step")',''),ns)
A,B,X,hull,body=ns['A'],ns['B'],ns['X'],ns['hull'],ns['body']
W=X/2+5
# BB lug (kept from previous question); AA boss removed
bb=(cq.Workplane("XZ").moveTo(A,0).lineTo(A,20).lineTo(A-15,20)
    .threePointArc((A-15-10*math.cos(math.radians(45)),10+10*math.sin(math.radians(45))),(A-25,10))
    .lineTo(A-25,0).close())
body=body.union(bb.extrude(60,both=True).intersect(hull))
# AA: 12-wide thickened web from big-tube axis to x=W, full height of big tube
body=body.union(cq.Workplane("XY").workplane(offset=30).center(W/2,0).rect(W,12).extrude(B))
body=body.cut(cq.Workplane("XY").circle(X/2-4).extrude(300,both=True))
body=body.cut(cq.Workplane("XY").center(A,0).circle(8.5).extrude(300,both=True))
body=body.cut(cq.Workplane("XZ").center(A-15,10).circle(5).extrude(100,both=True))
# 6-wide slot through all, from bore to x=W-3
body=body.cut(cq.Workplane("XY").center((W-3)/2,0).rect(W-3,6).extrude(300,both=True))
v=body.val().Volume(); print(f"A={A} B={B} W={W} vol={v:.2f} mass={v*0.0027:.2f} g")
cq.exporters.export(body,"bracket_mod2.step")
