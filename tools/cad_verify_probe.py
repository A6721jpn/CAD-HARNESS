"""verify-v1: independent world BRep and consumed native-link measurements.

No compiler, generator, fixture, or case-name lookup is used by this Probe.
"""
import hashlib
import math
from pathlib import Path

if __package__:
    from .cad_spec_probe import (read_json, gold_check, Checks, BOX_KEYS, close,
                                same_bounds, union_bounds, axis, vector, rectangle_segments,
                                covers_segment, world_shape)
else:
    from cad_spec_probe import (read_json, gold_check, Checks, BOX_KEYS, close,
                               same_bounds, union_bounds, axis, vector, rectangle_segments,
                               covers_segment, world_shape)

SCHEMA = Path(__file__).resolve().parents[1] / "design/cad-harness-verify/gold-schema.json"
PROFILES = {"roller", "taper", "elbow", "ribbed_box", "flange", "rect_prism"}


def tight_box(shape):
    # Fixed FreeCAD 1.1.4 API: exact surfaces, no tessellation or tolerance padding.
    # Missing support is an exception, never a fallback to conservative BoundBox.
    return shape.optimalBoundingBox(False, False)


def bounds(shape, offset=(0, 0, 0)):
    b = tight_box(shape)
    return [b.XMin-offset[0], b.XMax-offset[0], b.YMin-offset[1], b.YMax-offset[1],
            b.ZMin-offset[2], b.ZMax-offset[2]]


def load_gold(path):
    g = read_json(Path(path).read_text(encoding="utf-8"))
    schema = read_json(SCHEMA.read_text(encoding="utf-8"))
    gold_check(g, schema, schema)
    if (g["profile"] not in PROFILES or g["parameters"]["profile"] != g["profile"]
            or hashlib.sha256(g["description"].encode("utf-8")).hexdigest() != g["description_sha256"]
            or g["tolerances"] != {"linear_mm": .01, "axis": 1e-6, "volume_relative": 1e-4}
            or g["volume"]["relative"] != 1e-4 or g["volume"]["target_mm3"] <= 0
            or any(g["bbox"][i] >= g["bbox"][i+1] for i in (0, 2, 4))):
        raise ValueError("verify_gold_contract")
    if "volume_scope" in g and (g["profile"] != "rect_prism" or not g["finish"]
                                or g["finish"]["kind"] != "fillet"):
        raise ValueError("unsupported_volume_scope")
    expected_keys={
        "roller":{"profile","radius","bore_radius","length","groove_z","groove_depth","section_z"},
        "taper":{"profile","bottom","top","height"},
        "elbow":{"profile","path_radius","outer_radius","inner_radius"},
        "ribbed_box":{"profile","bbox","wall","rib_thickness","rib_top"},
        "flange":{"profile","radius","bore_radius","thickness","pcd_radius","pcd_count","hole_radius","pockets"},
        "rect_prism":{"profile","bbox","pockets","holes","finish"}}
    if (set(g["parameters"]) != expected_keys[g["profile"]] or g["regions"] or g["steps"]
            or (g["sections"] and g["profile"] != "taper")
            or g["provenance"]["confirmed"] is not (g["provenance"]["authority"] == "human")):
        raise ValueError("unsupported_verify_predicate")
    return g


def plane_cut(shape, center, normal):
    import FreeCAD as App
    import Part
    size = max(tight_box(shape).DiagonalLength * 2, 100)
    f = Part.makePlane(size, size, App.Vector(*center), App.Vector(*normal))
    f.translate(App.Vector(*center)-f.CenterOfMass)
    return shape.section(f)


def edges_of(shape):
    return [(e, [vector(v.Point) for v in e.Vertexes]) for e in shape.Edges]


def segment_present(shape, a, b, tol):
    """Collinear edge coverage, also for rib diagonals and sloping side edges."""
    import FreeCAD as App
    import Part
    start, end = App.Vector(*a), App.Vector(*b)
    length = (end-start).Length
    direction = (end-start)/length
    ranges = []
    for e in shape.Edges:
        if len(e.Vertexes) != 2:
            continue
        pts = [v.Point-start for v in e.Vertexes]
        if not isinstance(e.Curve,Part.Line):
            pts += [e.valueAt(e.FirstParameter+(e.LastParameter-e.FirstParameter)*t)-start for t in (.25,.5,.75)]
        if any(v.cross(direction).Length > tol for v in pts):
            continue
        projected = [v.dot(direction) for v in pts]
        lo, hi = min(projected), max(projected)
        if lo >= -tol and hi <= length+tol:
            ranges.append((lo, hi))
    at = 0
    for lo, hi in sorted(ranges):
        if lo > at+tol:
            return False
        at = max(at, hi)
    return at >= length-tol


def faces_of(shape):
    import Part
    planes, cylinders, other = [], [], []
    for f in shape.Faces:
        s = f.Surface
        row = {"bounds": bounds(f), "face": f, "area": f.Area}
        u0,u1,v0,v1=f.ParameterRange
        mid=f.valueAt((u0+u1)/2,(v0+v1)/2)
        normal=f.normalAt((u0+u1)/2,(v0+v1)/2)
        planar=isinstance(s,Part.Plane) or (all(abs((v.Point-mid).dot(normal))<1e-7 for v in f.Vertexes)
            and all(abs((f.valueAt(u0+(u1-u0)*a,v0+(v1-v0)*b)-mid).dot(normal))<1e-7
                    and abs(abs(f.normalAt(u0+(u1-u0)*a,v0+(v1-v0)*b).dot(normal))-1)<1e-6
                    for a in (.2,.5,.8) for b in (.2,.5,.8)))
        if planar:
            row["normal"] = vector(normal)
            planes.append(row)
        elif isinstance(s, Part.Cylinder):
            u0,u1,v0,v1 = f.ParameterRange
            v = f.valueAt((u0+u1)/2, (v0+v1)/2)-s.Center
            v -= s.Axis*v.dot(s.Axis)
            row.update(center=vector(s.Center), axis=axis(s.Axis), radius=s.Radius,
                       inside=f.normalAt((u0+u1)/2,(v0+v1)/2).dot(v) < 0)
            cylinders.append(row)
        else:
            row["type"] = type(s).__name__
            other.append(row)
    return planes, cylinders, other


def circular_edge(edge, center, normal, radius):
    import FreeCAD as App
    import Part
    curve=edge.Curve
    if isinstance(curve,Part.Circle):
        return (same_bounds(vector(curve.Center),center,.01)
                and same_bounds(axis(curve.Axis),axis_vector(normal),1e-6)
                and close(curve.Radius,radius,.01))
    # OCC can return a closed degree-1 B-spline for the same circular section
    # after FCStd serialization. Check every straight span, including its exact
    # radial minimum, rather than accepting a type name or a few sample points.
    if not isinstance(curve,Part.BSplineCurve) or curve.Degree!=1 or not edge.isClosed():
        return False
    if not same_bounds(vector(edge.CenterOfMass),center,.01):
        return False
    pts=[p-App.Vector(*center) for p in curve.getPoles()]
    direction=App.Vector(*axis_vector(normal))
    if len(pts)<3 or any(abs(p.dot(direction))>.01 for p in pts):
        return False
    area=App.Vector(0,0,0)
    for a,b in zip(pts,pts[1:]+pts[:1]):
        area+=a.cross(b)
        d=b-a
        t=max(0,min(1,-a.dot(d)/d.dot(d))) if d.dot(d)>0 else 0
        if not close(a.Length,radius,.01) or not close((a+d*t).Length,radius,.01):
            return False
    return area.Length>0 and same_bounds(axis(area),axis_vector(normal),1e-6)


def circle_section(shape, center, normal, radii, checks, name):
    cut = plane_cut(shape, center, normal)
    found = []
    for r in radii:
        chosen = [e for e in cut.Edges if circular_edge(e,center,normal,r)]
        actual = sum(e.Length for e in chosen)
        checks.add(name, name+".circle."+str(r), {"center":center,"radius":r,"axis":normal,"length":2*math.pi*r},
                   actual, abs(actual-2*math.pi*r) <= .01)
        found.extend(chosen)
    checks.add(name,name+".only_requested_loops",True,len(cut.Edges),
               bool(cut.Edges) and all(any(e.isSame(c) for c in found) for e in cut.Edges))
    return cut


def axis_vector(values):
    length = math.sqrt(sum(v*v for v in values))
    v = [a/length for a in values]
    first = next(a for a in v if abs(a)>1e-9)
    return [-a for a in v] if first < 0 else v


def planar_face(planes, b, normal, area, checks, name):
    chosen = [p for p in planes if same_bounds(p["bounds"],b,.01)
              and same_bounds(p["normal"],normal,1e-6)]
    actual = sum(p["area"] for p in chosen)
    checks.add(name,name+".face",{"bounds":b,"normal":normal,"area":area},
               {"bounds":union_bounds([p["bounds"] for p in chosen]),"area":actual},
               bool(chosen) and abs(actual-area) <= .01*max(1,math.sqrt(area)))


def hole_checks(shape, gold, cylinders, checks):
    import FreeCAD as App
    import Part
    groups = []
    for c in cylinders:
        if not c["inside"] or not same_bounds(c["axis"],[0,0,1],1e-6):
            continue
        found = next((h for h in groups if same_bounds(h["center_xy"],c["center"][:2],.01)
                      and close(h["radius"],c["radius"],.01)),None)
        if found is None:
            found = dict(center_xy=c["center"][:2],radius=c["radius"],z=c["bounds"][4:6],axis=c["axis"])
            groups.append(found)
        found["z"]=[min(found["z"][0],c["bounds"][4]),max(found["z"][1],c["bounds"][5])]
    checks.add("holes","holes.locations_count",len(gold["holes"]),len(groups),len(groups)==len(gold["holes"]))
    for i, expected in enumerate(gold["holes"]):
        h=next((h for h in groups if same_bounds(h["center_xy"],expected["center_xy"],.01)),None)
        prefix="holes.%d." % i
        for k,v in (("center_xy",expected["center_xy"]),("radius",expected["diameter"]/2),("z",expected["z"]),("axis",[0,0,1])):
            a=h.get(k) if h else None
            ok=same_bounds(a,v,1e-6 if k=="axis" else .01) if isinstance(v,list) else close(a,v,.01)
            checks.add("holes",prefix+k,v,a,ok)
        x,y=expected["center_xy"]; low,high=expected["z"]; r=expected["diameter"]/2
        samples=[low,(3*low+high)/4,(low+high)/2,(low+3*high)/4,high]
        empty=all(not shape.isInside(App.Vector(x,y,z),1e-7,True) for z in samples)
        checks.add("holes",prefix+"axis_void",True,empty,empty)
        for z in (low,high):
            rims=[e for e in shape.Edges if isinstance(e.Curve,Part.Circle)
                  and same_bounds(vector(e.Curve.Center),[x,y,z],.01)
                  and same_bounds(axis(e.Curve.Axis),[0,0,1],1e-6) and close(e.Curve.Radius,r,.01)]
            length=sum(e.Length for e in rims)
            checks.add("holes",prefix+"opening."+str(z),2*math.pi*r,length,abs(length-2*math.pi*r)<=.01)
    return groups


def pocket_checks(shape, gold, planes, checks):
    import FreeCAD as App
    edges=edges_of(shape)
    for i,q in enumerate(gold["pockets"]):
        b,top=q["bounds"],q["top_z"]; floor=top-q["depth"]
        planar_face(planes,b+[floor,floor],[0,0,1],(b[1]-b[0])*(b[3]-b[2]),checks,"pockets.%d.floor" % i)
        for j,(target,n) in enumerate((( [b[0],b[0],b[2],b[3],floor,top],[1,0,0]),
                                      ( [b[1],b[1],b[2],b[3],floor,top],[-1,0,0]),
                                      ( [b[0],b[1],b[2],b[2],floor,top],[0,1,0]),
                                      ( [b[0],b[1],b[3],b[3],floor,top],[0,-1,0]))):
            chosen=[p for p in planes if same_bounds(p["bounds"],target,.01) and same_bounds(p["normal"],n,1e-6)]
            checks.add("pockets","pockets.%d.wall.%d"%(i,j),target,union_bounds([p["bounds"] for p in chosen]),bool(chosen))
        segments=rectangle_segments(b,top)+rectangle_segments(b,floor)
        segments += [((x,y,floor),(x,y,top)) for x in b[:2] for y in b[2:4]]
        checks.add("pockets","pockets.%d.sharp"%i,True,None,
                   all(covers_segment(edges,s,.01,True,shape) for s in segments))
        empty=all(not shape.isInside(App.Vector((b[0]+b[1])/2,(b[2]+b[3])/2,z),1e-7,True)
                  for z in ((floor+top)/2,top))
        checks.add("pockets","pockets.%d.void_open"%i,True,empty,empty)


def roller(shape, g, planes, cylinders, other, checks):
    p=g["parameters"]; R,r,L=p["radius"],p["bore_radius"],p["length"]; lo,hi=p["groove_z"]; rg=R-p["groove_depth"]
    for i,z in enumerate(p["section_z"]):
        outer = rg if lo < z < hi else R
        circle_section(shape,[0,0,z],[0,0,1],[outer,r],checks,"roller.section%d"%i)
    for z,outer,inner,n in ((0,R,r,[0,0,-1]),(L,R,r,[0,0,1]),(lo,R,rg,[0,0,1]),(hi,R,rg,[0,0,-1])):
        planar_face(planes,[-outer,outer,-outer,outer,z,z],n,math.pi*(outer**2-inner**2),checks,"roller.shoulder"+str(z))
    expected=[(R,[0,lo],False),(rg,[lo,hi],False),(R,[hi,L],False),(r,[0,L],True)]
    for i,(radius,z,inside) in enumerate(expected):
        chosen=[c for c in cylinders if c["inside"]==inside and close(c["radius"],radius,.01)
                and same_bounds(c["center"][:2],[0,0],.01) and same_bounds(c["axis"],[0,0,1],1e-6)
                and c["bounds"][4]>=z[0]-.01 and c["bounds"][5]<=z[1]+.01]
        extent=union_bounds([c["bounds"] for c in chosen])
        checks.add("roller","roller.wall.%d"%i,{"radius":radius,"z":z},extent,
                   extent is not None and same_bounds(extent[4:6],z,.01)
                   and abs(sum(c["area"] for c in chosen)-2*math.pi*radius*(z[1]-z[0]))<=.01*2*math.pi*radius)
    checks.add("roller","roller.no_extra_surfaces",True,None,not other and all(
        any(close(c["radius"],r0,.01) and c["inside"]==inside and same_bounds(c["axis"],[0,0,1],1e-6)
            and c["bounds"][4]>=z[0]-.01 and c["bounds"][5]<=z[1]+.01 for r0,z,inside in expected) for c in cylinders))


def taper(shape,g,planes,cylinders,other,checks):
    p=g["parameters"]; W,D=p["bottom"]; w,d=p["top"]; H=p["height"]
    for i,section in enumerate(g["sections"]):
        z,b=section["z"],section["bounds"]
        cut=plane_cut(shape,[0,0,z],[0,0,1])
        checks.add("taper","taper.section.%d.bounds"%i,b+[z,z],None if cut.isNull() else bounds(cut),
                   not cut.isNull() and same_bounds(bounds(cut),b+[z,z],.01))
        for j,(a,bp) in enumerate(rectangle_segments(b,z)):
            checks.add("taper","taper.section.%d.side.%d"%(i,j),[a,bp],None,segment_present(cut,a,bp,.01))
    planar_face(planes,[-W/2,W/2,-D/2,D/2,0,0],[0,0,-1],W*D,checks,"taper.bottom")
    planar_face(planes,[-w/2,w/2,-d/2,d/2,H,H],[0,0,1],w*d,checks,"taper.top")
    allowed=[]
    for coord,bottom,top in ((0,W,w),(1,D,d)):
        for sign in (-1,1):
            slope=(bottom-top)/(2*H)
            n=[0,0,slope]; n[coord]=sign
            n=[v/math.sqrt(1+slope*slope) for v in n]
            chosen=[f for f in planes if same_bounds(f["normal"],n,1e-6)
                    and all(close(sign*vector(v.Point)[coord]+slope*v.Point.z,bottom/2,.01) for v in f["face"].Vertexes)]
            checks.add("taper","taper.slope.%d.%d"%(coord,sign),n,chosen[0]["normal"] if chosen else None,bool(chosen))
            allowed+=chosen
    checks.add("taper","taper.no_extra",True,None,not cylinders and not other and all(
        f in allowed or same_bounds(f["normal"],[0,0,1],1e-6) or same_bounds(f["normal"],[0,0,-1],1e-6) for f in planes))


def elbow(shape,g,planes,cylinders,other,checks):
    import FreeCAD as App
    p=g["parameters"]; R,ro,ri=p["path_radius"],p["outer_radius"],p["inner_radius"]
    for i,t in enumerate((0,math.pi/4,math.pi/2)):
        center=[R*math.sin(t),R*(1-math.cos(t)),0]; tangent=[math.cos(t),math.sin(t),0]
        circle_section(shape,center,tangent,[ro,ri],checks,"elbow.section%d"%i)
    for i,(b,n) in enumerate((([0,0,-ro,ro,-ro,ro],[-1,0,0]),([R-ro,R+ro,R,R,-ro,ro],[0,1,0]))):
        planar_face(planes,b,n,math.pi*(ro**2-ri**2),checks,"elbow.end%d"%i)
    void=[]; wall=[]
    for t in (0,math.pi/8,math.pi/4,3*math.pi/8,math.pi/2):
        x,y=R*math.sin(t),R*(1-math.cos(t))
        void.append(not shape.isInside(App.Vector(x,y,0),1e-7,True))
        if 0<t<math.pi/2:
            wall.append(shape.isInside(App.Vector(x,y,(ri+ro)/2),1e-7,True))
    checks.add("elbow","elbow.lumen_open",True,void,all(void))
    checks.add("elbow","elbow.wall_material",True,wall,all(wall))
    # Curved sweep faces may be toroidal or an equivalent B-spline. Their
    # representation and counts are recorded; actual normal sections gate them.
    checks.add("elbow","elbow.no_unrequested_planes",True,None,not cylinders and all(
        same_bounds(f["normal"],[-1,0,0],1e-6) or same_bounds(f["normal"],[0,1,0],1e-6) for f in planes))


def ribbed_box(shape,g,planes,cylinders,other,checks):
    import FreeCAD as App
    p=g["parameters"]; b=p["bbox"]; t=p["wall"]; rt=p["rib_thickness"]; top=p["rib_top"]
    x0,x1,y0,y1=b[0]+t,b[1]-t,b[2]+t,b[3]-t; dx=x1-x0; dz=top-t
    planar_face(planes,b[:4]+[0,0],[0,0,-1],(b[1]-b[0])*(b[3]-b[2]),checks,"box.bottom")
    planar_face(planes,b[:4]+[b[5],b[5]],[0,0,1],(b[1]-b[0])*(b[3]-b[2])-dx*(y1-y0),checks,"box.top_rim")
    for y,n in ((-rt/2,[0,-1,0]),(rt/2,[0,1,0])):
        planar_face(planes,[x0,x1,y,y,t,top],n,dx*dz/2,checks,"box.rib_side"+str(y))
    cut=plane_cut(shape,[0,0,0],[0,1,0])
    checks.add("rib","rib.diagonal",[[x0,0,t],[x1,0,top]],None,segment_present(cut,[x0,0,t],[x1,0,top],.01))
    expected_n=[-dz/math.sqrt(dx*dx+dz*dz),0,dx/math.sqrt(dx*dx+dz*dz)]
    planar_face(planes,[x0,x1,-rt/2,rt/2,t,top],expected_n,rt*math.sqrt(dx*dx+dz*dz),checks,"rib.slope")
    occupancy=[]
    for x in (x0+dx/4,(x0+x1)/2,x0+3*dx/4):
        height=t+dz*(x-x0)/dx
        for y,z,inside in ((0,(t+height)/2,True),(0,(height+b[5])/2,False),
                           (rt, (t+b[5])/2,False),(y0-t/2,b[5]/2,True)):
            actual=shape.isInside(App.Vector(x,y,z),1e-7,True)
            occupancy.append(actual==inside)
    checks.add("rib","rib.connection_and_cavity",True,occupancy,all(occupancy))
    # Check all four real wall positions, including inner cavity boundaries.
    for coord,pairs in ((0,((b[0],-1),(b[1],1),(x0,1),(x1,-1))),
                       (1,((b[2],-1),(b[3],1),(y0,1),(y1,-1)))):
        for position,sign in pairs:
            n=[0,0,0]; n[coord]=sign
            found=[f for f in planes if same_bounds(f["normal"],n,1e-6)
                   and close(f["bounds"][2*coord],position,.01) and close(f["bounds"][2*coord+1],position,.01)]
            checks.add("walls","walls.%d.%s"%(coord,position),position,None if not found else position,bool(found))
    allowed_normals=[[1,0,0],[-1,0,0],[0,1,0],[0,-1,0],[0,0,1],[0,0,-1],expected_n]
    checks.add("rib","rib.no_extra_surfaces",True,None,not cylinders and not other and all(
        any(same_bounds(f["normal"],n,1e-6) for n in allowed_normals) for f in planes))


def top_finish(shape,g,planes,cylinders,other,checks):
    f=g["finish"]; b=g["bbox"]; r=f["size"]
    horizontal=[c for c in cylinders if not same_bounds(c["axis"],[0,0,1],1e-6)]
    oblique=[p for p in planes if sum(abs(n)>1e-6 for n in p["normal"])>1]
    for coord,sign,boundary in ((0,-1,b[0]),(0,1,b[1]),(1,-1,b[2]),(1,1,b[3])):
        name="finish.%d.%d"%(coord,sign)
        if f["kind"]=="chamfer":
            n=[0,0,math.sqrt(.5)]; n[coord]=sign*math.sqrt(.5)
            chosen=[p for p in oblique if same_bounds(p["normal"],n,1e-6) and all(
                close(sign*vector(v.Point)[coord]+v.Point.z,sign*boundary+b[5]-r,.01) for v in p["face"].Vertexes)]
            checks.add("finish",name,{"leg":r,"normal":n},union_bounds([p["bounds"] for p in chosen]),bool(chosen))
        else:
            ax=[0,1,0] if coord==0 else [1,0,0]
            chosen=[c for c in horizontal if same_bounds(c["axis"],ax,1e-6) and close(c["radius"],r,.01)
                    and close(c["center"][coord],boundary-sign*r,.01) and close(c["center"][2],b[5]-r,.01)]
            checks.add("finish",name,{"radius":r,"axis":ax,"center_normal":boundary-sign*r,"center_z":b[5]-r},
                       union_bounds([c["bounds"] for c in chosen]),bool(chosen))
    top=union_bounds([p["bounds"] for p in planes if same_bounds(p["bounds"][4:6],[b[5],b[5]],.01)])
    target=[b[0]+r,b[1]-r,b[2]+r,b[3]-r,b[5],b[5]]
    checks.add("finish","finish.top_bounds",target,top,same_bounds(top,target,.01))
    if f["kind"]=="chamfer":
        checks.add("finish","finish.only_requested_chamfer",True,None,not horizontal and not other and all(
            close(p["bounds"][4],b[5]-r,.01) and close(p["bounds"][5],b[5],.01) for p in oblique))
    else:
        # S1's legal corner joining surfaces are confined to the four outer
        # corner patches. They do not supply a whole-volume target.
        legal=lambda a: a[4]>=b[5]-r-.01 and a[5]<=b[5]+.01 and (
            (a[1]<=b[0]+r+.01 or a[0]>=b[1]-r-.01) and (a[3]<=b[2]+r+.01 or a[2]>=b[3]-r-.01))
        checks.add("finish","finish.only_outer_R",True,None,not oblique and all(legal(o["bounds"]) for o in other)
                   and all(close(c["radius"],r,.01) and c["bounds"][4]>=b[5]-r-.01 and c["bounds"][5]<=b[5]+.01 for c in horizontal))
        for coord,normal,centers in ((0,[0,1,0],(b[0]+r,b[1]-r)),(1,[1,0,0],(b[2]+r,b[3]-r))):
            cut=plane_cut(shape,[0,0,0],normal)
            for center in centers:
                import Part
                c=[0,0,b[5]-r]; c[coord]=center
                chosen=[e for e in cut.Edges if isinstance(e.Curve,Part.Circle)
                        and same_bounds(vector(e.Curve.Center),c,.01) and close(e.Curve.Radius,r,.01)
                        and same_bounds(axis(e.Curve.Axis),normal,1e-6)]
                length=sum(e.Length for e in chosen)
                checks.add("finish","finish.local_R.%d.%s"%(coord,center),math.pi*r/2,length,abs(length-math.pi*r/2)<=.01)
            z=b[5]-r/2; delta=math.sqrt(r*r-(r/2)**2)
            for sign,center in ((-1,centers[0]),(1,centers[1])):
                point=[0,0,z]; point[coord]=center+sign*delta
                import FreeCAD as App
                inside=list(point); outside=list(point); inside[coord]-=sign*.003; outside[coord]+=sign*.003
                ok=shape.isInside(App.Vector(*inside),1e-7,True) and not shape.isInside(App.Vector(*outside),1e-7,True)
                checks.add("finish","finish.local_boundary.%d.%d"%(coord,sign),point,ok,ok)
        for x in b[:2]:
            for y in b[2:4]:
                checks.add("finish","finish.vertical_sharp.%s.%s"%(x,y),True,None,
                           covers_segment(edges_of(shape),((x,y,b[4]),(x,y,b[5]-r)),.01,True,shape))


def measure_shape(shape,g,checks):
    import FreeCAD as App
    import Part
    m=dict(bound_box_mm=dict(zip(BOX_KEYS,bounds(shape))),volume_mm3=shape.Volume,area_mm2=shape.Area,
           face_count=len(shape.Faces),edge_count=len(shape.Edges),solid_count=len(shape.Solids),is_valid=shape.isValid())
    checks.add("valid_solid","shape.solid",1,len(shape.Solids),len(shape.Solids)==1)
    checks.add("valid_solid","shape.valid",True,m["is_valid"],m["is_valid"] is True)
    for k,a,e in zip(BOX_KEYS,bounds(shape),g["bbox"]):
        checks.add("bbox","bbox."+k,e,a,close(a,e,.01),.01)
    volume=shape.Volume
    if "volume_scope" in g:
        b=g["volume_scope"]
        stock=Part.makeBox(b[1]-b[0],b[3]-b[2],b[5]-b[4],App.Vector(b[0],b[2],b[4]))
        volume=shape.common(stock).Volume
        m["scoped_volume_mm3"]=volume
        m["volume_scope"]=b
    target=g["volume"]["target_mm3"]
    checks.add("volume","volume.stock" if "volume_scope" in g else "volume.full",target,volume,
               abs(volume/target-1)<=1e-4,1e-4)
    planes,cylinders,other=faces_of(shape)
    m["surface_types"]=[type(f.Surface).__name__ for f in shape.Faces]
    m["holes"]=hole_checks(shape,g,cylinders,checks) if g["profile"]!="elbow" else []
    pocket_checks(shape,g,planes,checks)
    dispatch={"roller":roller,"taper":taper,"elbow":elbow,"ribbed_box":ribbed_box}
    if g["profile"] in dispatch:
        dispatch[g["profile"]](shape,g,planes,cylinders,other,checks)
    elif g["profile"]=="flange":
        R=g["parameters"]["radius"]; H=g["parameters"]["thickness"]
        outer=[c for c in cylinders if not c["inside"] and same_bounds(c["axis"],[0,0,1],1e-6)
               and same_bounds(c["center"][:2],[0,0],.01) and close(c["radius"],R,.01)]
        checks.add("flange","flange.outer_wall",[R,0,H],union_bounds([c["bounds"] for c in outer]),
                   bool(outer) and abs(sum(c["area"] for c in outer)-2*math.pi*R*H)<=.01*2*math.pi*R)
        checks.add("flange","flange.no_extra_curves",True,None,not other and all(
            c["inside"] or c in outer for c in cylinders) and all(sum(abs(v)>1e-6 for v in p["normal"])==1 for p in planes))
    elif g["profile"]=="rect_prism":
        b=g["bbox"]
        cut=plane_cut(shape,[0,0,(b[4]+min([q["top_z"]-q["depth"] for q in g["pockets"]]+[b[5]]))/2],[0,0,1])
        z=bounds(cut)[4]
        checks.add("sections","rect.lower_outline",b[:4],bounds(cut)[:4],same_bounds(bounds(cut)[:4],b[:4],.01)
                   and all(segment_present(cut,a,c,.01) for a,c in rectangle_segments(b[:4],z)))
        if g["finish"]:
            top_finish(shape,g,planes,cylinders,other,checks)
        else:
            checks.add("finish","finish.unrequested",True,None,not other and all(same_bounds(c["axis"],[0,0,1],1e-6)
                and c["inside"] for c in cylinders) and all(sum(abs(v)>1e-6 for v in p["normal"])==1 for p in planes))
    else:
        raise ValueError("unsupported_verify_predicate")
    return m


def links(value):
    if isinstance(value,(list,tuple)):
        for v in value:
            yield from links(v)
    elif hasattr(value,"TypeId"):
        yield value


def editability(doc,body,shape,g,checks,native_shape=None):
    allowed={"PartDesign::Pad","PartDesign::Pocket","PartDesign::Revolution","PartDesign::Groove",
             "PartDesign::AdditiveLoft","PartDesign::SubtractiveLoft","PartDesign::AdditivePipe","PartDesign::SubtractivePipe",
             "PartDesign::Fillet","PartDesign::Chamfer","PartDesign::Thickness","PartDesign::LinearPattern",
             "PartDesign::PolarPattern","PartDesign::MultiTransform","PartDesign::Mirrored"}
    profiles={"PartDesign::Pad","PartDesign::Pocket","PartDesign::Revolution","PartDesign::Groove",
              "PartDesign::AdditiveLoft","PartDesign::SubtractiveLoft","PartDesign::AdditivePipe","PartDesign::SubtractivePipe"}
    bodies=[o for o in doc.Objects if o.TypeId=="PartDesign::Body"]
    tip=getattr(body,"Tip",None)
    checks.add("editability","edit.body",1,len(bodies),len(bodies)==1 and bodies[0]==body)
    checks.add("editability","edit.native_tip",True,getattr(tip,"TypeId",None),tip is not None and tip.TypeId in allowed and tip in body.Group)
    ts=getattr(tip,"Shape",None); ns=native_shape if native_shape is not None else shape
    same=ts is not None and ts.isValid() and len(ts.Solids)==1 and len(ns.Solids)==1 and ts.Solids[0].isSame(ns.Solids[0])
    checks.add("editability","edit.tip_solid",True,same,same)
    todo=[tip] if tip else []; seen=set(); native=[]; sketches=[]; consumed_construction={}
    while todo:
        obj=todo.pop()
        if obj.Name in seen: continue
        seen.add(obj.Name)
        checks.add("editability","edit.used_member."+str(len(seen)),True,obj in body.Group,obj in body.Group)
        if obj.TypeId=="Sketcher::SketchObject":
            sketches.append(obj)
            continue
        if obj.TypeId not in allowed:
            checks.add("editability","edit.unsupported_dependency",True,obj.TypeId,False)
            continue
        native.append(obj)
        if obj.TypeId in profiles:
            used=list(links(getattr(obj,"Profile",None)))
            ok=len(used)==1 and used[0].TypeId=="Sketcher::SketchObject" and not used[0].Shape.isNull()
            checks.add("editability","edit.used_profile."+str(len(native)),True,ok,ok)
        for key in ("Profile","BaseFeature","Base","Originals","Sections","Spine","AuxiliarySpine"):
            todo.extend(links(getattr(obj,key,None)))
        ref=getattr(obj,"ReferenceAxis",None)
        if ref and isinstance(ref,(tuple,list)) and len(ref)==2 and getattr(ref[0],"TypeId",None)=="Sketcher::SketchObject":
            s=ref[0]; todo.append(s)
            constructions=[i for i in range(s.GeometryCount) if s.getConstruction(i)]
            for sub in ref[1]:
                # FreeCAD 1.1.4 may normalize a used Axis0 link to "Axis".
                # Resolve only a unique construction axis; ambiguity stays a
                # missing dimension rather than counting unused construction.
                if sub == "Axis" and len(constructions) == 1:
                    consumed_construction.setdefault(s.Name,set()).add(constructions[0])
                elif sub.startswith("Axis") and sub[4:].isdigit() and int(sub[4:])<len(constructions):
                    consumed_construction.setdefault(s.Name,set()).add(constructions[int(sub[4:])])
    checks.add("editability","edit.consumed_sketch",True,len(sketches),bool(sketches))
    errors=[i for i,o in enumerate(doc.Objects) if any("error" in str(v).lower() or "invalid" in str(v).lower() for v in o.State)]
    checks.add("editability","edit.clean_recompute",[],errors,not errors)
    native_valid=checks.predicates.get("editability") is True
    values=[]
    for obj in native:
        for key in ("Length","Length2","Radius","Size","Size2"):
            if key in obj.PropertiesList:
                v=getattr(obj,key); values.append(abs(float(v.Value if hasattr(v,"Value") else v)))
    for s in sketches:
        # Loft section height is the actual Placement of a consumed section,
        # not an unused numeric annotation. Construction axis dimensions only
        # count when a native Revolution/Groove actually uses that axis.
        values.extend(abs(v) for v in vector(s.Placement.Base))
        for i,c in enumerate(s.Constraints):
            first=c.First
            if (c.Type in ("Distance","DistanceX","DistanceY","Radius","Diameter") and s.getDriving(i)
                    and 0<=first<s.GeometryCount
                    and (not s.getConstruction(first) or first in consumed_construction.get(s.Name,set()))):
                values.append(abs(c.Value))
    for i,d in enumerate(g["editability"]["key_dimensions_mm"]):
        found=next((v for v in values if close(v,d,.01) or close(v,d/2,.01)),None)
        checks.add("editability","edit.driving_dimension.%d"%i,d,found,found is not None)
    return {"native_features":len(native),"used_sketches":len(sketches),"native_valid":native_valid,"driving_dimensions_mm":values},[
        "flatface_advice"] if any(str(s.MapMode)!="FlatFace" for s in sketches[1:]) else []


def probe(doc,body,gold,require_editability=True):
    checks=Checks(gold["case_id"])
    tip=getattr(body,"Tip",None) if require_editability else None
    shape=world_shape(tip) if tip is not None else body.Shape
    if shape.isNull():
        checks.add("valid_solid","shape.null",False,True,False)
        return dict(measurements={"volume_mm3":None},predicates=checks.predicates,probe_pass=False,
                    geometry_ok=False,editability_ok=False,skill_warnings=[],predicate_details=checks.details())
    m=measure_shape(shape,gold,checks)
    geometry=all(checks.predicates.values()); warnings=[]
    if require_editability:
        m["editability"],warnings=editability(doc,body,shape,gold,checks,native_shape=tip.Shape if tip else shape)
    return dict(measurements=m,predicates=checks.predicates,probe_pass=all(checks.predicates.values()),
                geometry_ok=geometry,editability_ok=checks.predicates.get("editability") if require_editability else None,
                skill_warnings=warnings,predicate_details=checks.details(),
                reference={"gold_schema":gold["schema"],"volume_mm3":gold["volume"]["target_mm3"],"volume_scope":gold.get("volume_scope")})
