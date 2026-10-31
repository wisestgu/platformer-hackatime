import cadquery as cq, math, sys
A=float(sys.argv[1]) if len(sys.argv)>1 else 173
B=float(sys.argv[2]) if len(sys.argv)>2 else 77
X=A/2; Y=2*B/3; T=6; W=5; R=10; ang=math.radians(40)
tn,cs=math.tan(ang),math.cos(ang)
xb=A-40                       # bottom bend at small end
x1=xb-30/tn                   # bottom bend at big end
off=T/cs                      # vertical thickness on slope
# plate side profile (x,z)
xt1=x1+ (T/tn - T/math.sin(ang)) * -1  # placeholder not used
def lineint(z): return xb - (z)/tn   # x on bottom slope at height z
# top slope: z=(xb-x)*tn+off
pts=[(0,30),(x1,30),(xb,0),(A,0),(A,T),(xb-(T-off)/tn,T),(xb-(36-off)/tn,36),(0,36)]
plate=cq.Workplane("XZ").polyline(pts).close().extrude(-60,both=True)
plate=plate.edges("|Y").edges(cq.selectors.BoxSelector((x1-15,-100,-1),(xb+15,100,40))).fillet(R)
# top hull (tangent outline of two circles)
R1,R2=X/2,12.5
hull=(cq.Workplane("XY").circle(R1).extrude(200).union(cq.Workplane("XY").center(A,0).circle(R2).extrude(200)))
s=(R1-R2)/A; a=math.asin(s)
p=[(R1*math.sin(a),R1*math.cos(a)),(A+R2*math.sin(a),R2*math.cos(a))]
poly=cq.Workplane("XY").polyline([p[0],p[1],(p[1][0],-p[1][1]),(p[0][0],-p[0][1])]).close().extrude(200)
hull=hull.union(poly).translate((0,0,-50))
plate=plate.intersect(hull)
# web
topz=lambda x:(xb-x)*tn+Y/cs
xa=xb-(30+B-Y/cs)/tn; xc=xb-(Y-Y/cs)/tn
wpts=[(0,30),(x1,30),(xb,0),(A,0),(A,Y),(xc,Y),(xa,30+B),(0,30+B)]
web=cq.Workplane("XZ").polyline(wpts).close().extrude(W/2,both=True)
web=web.edges("|Y").edges(cq.selectors.BoxSelector((xa-5,-10,30+B-1),(xa+5,10,30+B+1))).fillet(R)
web=web.edges("|Y").edges(cq.selectors.BoxSelector((xc-5,-10,Y-1),(xc+5,10,Y+1))).fillet(R)
t1=cq.Workplane("XY").workplane(offset=30).circle(R1).extrude(B)
t2=cq.Workplane("XY").center(A,0).circle(R2).extrude(Y)
body=plate.union(web).union(t1).union(t2)
body=body.cut(cq.Workplane("XY").circle(R1-4).extrude(300,both=True)).cut(cq.Workplane("XY").center(A,0).circle(R2-4).extrude(300,both=True))
v=body.val().Volume(); print(f"A={A} B={B} vol={v:.2f} mm3 mass={v*0.0027:.2f} g")
cq.exporters.export(body,"bracket.step")
