"""Opt-in v3: BRep gates plus consumed, typed native dimension role proofs.

No generator, case/description lookup, or arbitrary expression evaluation.
"""
import copy
import hashlib
import math
from pathlib import Path
import re

if __package__:
    from . import cad_verify_probe as v1, cad_verify_v2_probe as v2
else:
    import cad_verify_probe as v1, cad_verify_v2_probe as v2

SCHEMA=Path(__file__).resolve().parents[1]/'design/cad-harness-verify-v3/gold-schema.json'
Checks=v1.Checks
TOL=.01
DATUM_TYPES=frozenset(('Distance','DistanceX','DistanceY','Radius','Diameter','Angle'))


def load_gold(path):
    g=v1.read_json(Path(path).read_text(encoding='utf-8'))
    schema=v1.read_json(SCHEMA.read_text(encoding='utf-8'))
    v1.gold_check(g,schema,schema)
    keys={
        'roller':{'profile','radius','bore_radius','length','groove_z','groove_depth','section_z'},
        'taper':{'profile','bottom','top','height'},'elbow':{'profile','path_radius','outer_radius','inner_radius'},
        'ribbed_box':{'profile','bbox','wall','rib_thickness','rib_top'},
        'flange':{'profile','radius','bore_radius','thickness','pcd_radius','pcd_count','hole_radius','pockets'},
        'rect_prism':{'profile','bbox','pockets','holes','finish'}}
    if (g['profile'] not in keys or set(g['parameters'])!=keys[g['profile']]
            or g['parameters']['profile']!=g['profile'] or g['regions'] or g['steps']
            or g['sections'] and g['profile']!='taper'
            or hashlib.sha256(g['description'].encode()).hexdigest()!=g['description_sha256']
            or g['tolerances']!={'linear_mm':.01,'axis':1e-6,'volume_relative':1e-4}
            or g['volume']['relative']!=1e-4 or g['volume']['target_mm3']<=0
            or any(g['bbox'][i]>=g['bbox'][i+1] for i in (0,2,4))
            or g['provenance']['confirmed'] is not (g['provenance']['authority']=='human')):
        raise ValueError('verify_v3_gold_contract')
    roles=g['editability']['roles']
    if len({r['role'] for r in roles})!=len(roles):raise ValueError('duplicate_dimension_role')
    if g['profile']!='roller' and ([r['target_mm'] for r in roles]!=g['editability']['key_dimensions_mm'] or any(r['relation']!='native_primary' for r in roles)):
        raise ValueError('primary_dimension_roles')
    if g['profile']=='roller':
        p=g['parameters']; expected={'outer_diameter':2*p['radius'],'bore_diameter':2*p['bore_radius'],
            'length':p['length'],'groove_width':p['groove_z'][1]-p['groove_z'][0],'groove_depth':p['groove_depth']}
        if {r['role']:r['target_mm'] for r in roles}!=expected:raise ValueError('roller_primary_roles')
        if g['editability']['key_dimensions_mm']!=[expected[k] for k in ('outer_diameter','bore_diameter','length')]:
            raise ValueError('derived_roller_dimension_forbidden')
    if 'volume_scope' in g and (g['profile']!='rect_prism' or not g['finish'] or g['finish']['kind']!='fillet'):
        raise ValueError('unsupported_volume_scope')
    if 'completion_binding' in g:
        original,answer=g['description'].rsplit('\n',1)
        expected=dict(description_sha256=hashlib.sha256(original.encode()).hexdigest(),
            answer_sha256=hashlib.sha256(answer.encode()).hexdigest(),completion_input_sha256=g['description_sha256'])
        if expected!=g['completion_binding']:raise ValueError('completion_gold_binding')
    return g


def consumed(body):
    """Retain actual used links/subselections and uniquely identified axis seeds."""
    todo=[body.Tip] if body.Tip else [];seen=set();native=[];sketches={};seeds={};users={}
    allowed={'PartDesign::'+n for n in v2.NATIVE}
    while todo:
        obj=todo.pop()
        if obj.Name in seen:continue
        seen.add(obj.Name)
        if obj.TypeId=='Sketcher::SketchObject':sketches[obj.Name]=obj;continue
        if obj.TypeId not in allowed:continue
        native.append(obj)
        for key in ('Profile','BaseFeature','Base','Originals','Sections','Spine','AuxiliarySpine'):
            for s,sub in v2.link_items(getattr(obj,key,None)):
                todo.append(s)
                if s.TypeId=='Sketcher::SketchObject':
                    users.setdefault(s.Name,[]).append((obj,key,sub))
                    for i in v2.selected_geometry(s,sub):
                        seeds.setdefault(s.Name,{}).setdefault(i,[dict(feature=obj.Name,link=key,subnames=list(sub),sketch=s.Name,geometry=i)])
        ref=getattr(obj,'ReferenceAxis',None)
        for s,subs in v2.link_items(ref):
            if s.TypeId!='Sketcher::SketchObject':continue
            todo.append(s);construction=[i for i in range(s.GeometryCount) if s.getConstruction(i)]
            for sub in subs:
                index=0 if sub=='Axis' and len(construction)==1 else int(sub[4:]) if re.fullmatch(r'Axis[0-9]+',sub) else -1
                if 0<=index<len(construction):
                    i=construction[index];seeds.setdefault(s.Name,{}).setdefault(i,[dict(feature=obj.Name,link='ReferenceAxis',subnames=[sub],sketch=s.Name,geometry=i)])
    return native,sketches,seeds,users


def point(s,p):
    placement=s.getGlobalPlacement() if hasattr(s,'getGlobalPlacement') else s.Placement
    return v1.vector(placement.multVec(p))


def radius(p):return math.hypot(p[0],p[1])
def near(a,b):return abs(a-b)<=TOL
def active(s,i):
    # FreeCAD 1.1.4 rejects getDriving() for geometric constraints.
    if not s.getActive(i):return False
    return s.getDriving(i) if s.Constraints[i].Type in DATUM_TYPES else True
def scalar(v):return float(v.Value if hasattr(v,'Value') else v)
def length_mode(feature):return getattr(feature,'Type',None) in (0,'Length')


def geometry(s,i):
    geo=s.Geometry[i]
    if hasattr(geo,'StartPoint') and hasattr(geo,'EndPoint'):
        return dict(kind='line',points=[point(s,geo.StartPoint),point(s,geo.EndPoint)])
    if hasattr(geo,'Center') and hasattr(geo,'Radius') and hasattr(geo,'Axis'):
        center=point(s,geo.Center);end=point(s,geo.Center+geo.Axis)
        axis=[end[j]-center[j] for j in range(3)]
        if abs(abs(axis[2])-1)<1e-6 and abs(axis[0])+abs(axis[1])<1e-6 and radius(center)<TOL:
            return dict(kind='circle',radius=scalar(geo.Radius),center=center)
    return dict(kind='unsupported')


def radial_line(a,b):
    return (near(a[2],b[2]) and abs(a[0]*b[1]-a[1]*b[0])<1e-6
            and a[0]*b[0]+a[1]*b[1]>=-1e-6)


def endpoint(g,pos):
    return g['points'][pos-1] if g.get('kind')=='line' and pos in (1,2) else None


def attachment(s,i,pos,real,axis,value,records):
    """Actual boundary, reached by endpoint identity or an active typed link.

    Equal numeric coordinates elsewhere (even connected) never attach an operand.
    """
    todo=[(i,pos)];seen=set()
    while todo:
        pair=todo.pop()
        if pair in seen:continue
        seen.add(pair);idx,p=pair
        g=records.get(idx,{})
        q=endpoint(g,p)
        if idx in real and q is not None:
            points=g['points']
            if axis=='r' and all(near(radius(a),value) for a in points):return idx
            if axis=='z' and all(near(a[2],value) for a in points):return idx
        if idx in real and g.get('kind')=='circle' and axis=='r' and near(g['radius'],value):return idx
        for n,c in enumerate(s.Constraints):
            if not active(s,n):continue
            f=(getattr(c,'First',-1),getattr(c,'FirstPos',0));b=(getattr(c,'Second',-1),getattr(c,'SecondPos',0))
            if c.Type=='Coincident':
                if pair==f and b[0]>=0:todo.append(b)
                if pair==b and f[0]>=0:todo.append(f)
            elif c.Type=='PointOnObject' and pair==f and b[0] in real:
                g2=records[b[0]]
                if g2.get('kind')=='circle' and axis=='r' and near(g2['radius'],value):return b[0]
                if g2.get('kind')=='line':
                    if axis=='r' and all(near(radius(a),value) for a in g2['points']):return b[0]
                    if axis=='z' and all(near(a[2],value) for a in g2['points']):return b[0]
    return None


def relation_axis(s,c,g):
    """DistanceX/Y must measure the requested world component; Distance needs alignment."""
    if g.get('kind')!='line':return None
    a,b=g['points'];kind=c.Type
    alignment=[x for n,x in enumerate(s.Constraints) if active(s,n) and x.Type in ('Horizontal','Vertical') and x.First==c.First]
    if kind=='Distance' and not alignment:return None
    if kind in ('DistanceX','DistanceY'):
        # Local X/Y projected into world coordinates, without importing FreeCAD in ordinary Python.
        raw=s.Geometry[c.First].StartPoint
        unit=type(raw)(1,0,0) if kind=='DistanceX' else type(raw)(0,1,0)
        zero=type(raw)(0,0,0);o=point(s,zero);u=point(s,unit);v=[u[j]-o[j] for j in range(3)]
        if near(a[0],b[0]) and near(a[1],b[1]) and abs(abs(v[2])-1)<1e-6:return 'z'
        d=[b[j]-a[j] for j in range(3)];length=math.sqrt(sum(x*x for x in d))
        if length>TOL and radial_line(a,b) and abs(abs(sum(d[j]*v[j] for j in range(3))/length)-1)<1e-6:return 'r'
        return None
    if near(a[0],b[0]) and near(a[1],b[1]):return 'z'
    return 'r' if radial_line(a,b) else None


def driver_rows(native,sketches,seeds,users):
    """Finite sketch constraints, never free-form expression/custom scalar harvesting."""
    rows=[];geometries={}
    for name,s in sketches.items():
        paths=v2.reachable(s,seeds.get(name,{}));real={i for i in seeds.get(name,{}) if not s.getConstruction(i)}
        records={i:geometry(s,i) for i in paths};geometries[name]=(s,real,records)
        for n,c in enumerate(s.Constraints):
            ids=v2.references(c,s.GeometryCount)
            if c.Type not in v2.DIMENSIONS or not active(s,n) or not ids or any(i not in paths for i in ids):continue
            row=dict(sketch=name,constraint=n,type=c.Type,value_mm=abs(float(c.Value)),geometry=ids,paths=[paths[i] for i in ids],operands=[])
            if c.Type in ('Radius','Diameter'):
                i=c.First;geo=records[i]
                if geo.get('kind')=='circle':
                    # Equal between circle radii is a typed causal binding; mere
                    # reachability/Coincident/PointOnObject does not bind a radius.
                    equivalents={i};todo=[i]
                    while todo:
                        current=todo.pop()
                        for k,q in enumerate(s.Constraints):
                            if q.Type!='Equal' or not active(s,k):continue
                            pair=v2.references(q,s.GeometryCount)
                            if len(pair)!=2 or current not in pair:continue
                            other=next(j for j in pair if j!=current)
                            if other in records and records[other].get('kind')=='circle' and other not in equivalents:
                                equivalents.add(other);todo.append(other)
                    for target in sorted(equivalents & real):
                        circle=records[target]
                        mm=circle['radius']*(2 if c.Type=='Diameter' else 1)
                        if near(mm,row['value_mm']):row['operands'].append(dict(axis='r',boundary=circle['radius'],geometry=target,driver_geometry=i,type=c.Type,value_mm=row['value_mm'],binding='direct' if target==i else 'active_circle_equal'))
            elif len(ids)==1:
                i=ids[0];geo=records[i]
                first=getattr(c,'First',-1);second=getattr(c,'Second',-1)
                pos=getattr(c,'FirstPos',0) if first==i else getattr(c,'SecondPos',0)
                axis=relation_axis(s,c,geo) if first==i else None
                # Point-to-native-origin coordinate: its measurement axis, rather
                # than the edge direction, decides whether it drives radius or Z.
                q=endpoint(geo,pos)
                anchor=second if first==i else first
                native_origin=anchor==-1 or (first==i and anchor==-2000)
                if q is not None and native_origin and c.Type in ('DistanceX','DistanceY'):
                    vector_type=type(s.Geometry[i].StartPoint)
                    o=point(s,vector_type(0,0,0));unit=point(s,vector_type(1,0,0) if c.Type=='DistanceX' else vector_type(0,1,0))
                    direction=[unit[j]-o[j] for j in range(3)]
                    radial=radius(q)
                    if abs(abs(direction[2])-1)<1e-6:axis='z'
                    elif radial>TOL and abs(abs((direction[0]*q[0]+direction[1]*q[1])/radial)-1)<1e-6:axis='r'
                if geo.get('kind')=='line' and axis:
                    a,b=geo['points'];coord=(lambda p:radius(p)) if axis=='r' else (lambda p:p[2])
                    # Whole-line dimension: both actual ends and a proved radial/axial direction.
                    if getattr(c,'FirstPos',0)==0 and getattr(c,'Second',-1)<0:
                        ends=[attachment(s,i,p,real,axis,coord(q),records) for p,q in ((1,a),(2,b))]
                        row['candidate_span']=dict(axis=axis,boundaries=[coord(a),coord(b)],geometry=i,attached_geometry=ends,aligned=True)
                        if all(e is not None for e in ends):
                            row['span']=dict(axis=axis,boundaries=[coord(a),coord(b)],attached_geometry=ends,aligned=True,dimension_type=c.Type,driver_value_mm=row['value_mm'])
                    # A point coordinate from native sketch origin. Only an operand, never a direct depth.
                    q=endpoint(geo,pos)
                    if q is not None and native_origin:
                        origin=point(s,type(s.Geometry[i].StartPoint)(0,0,0))
                        if (axis=='r' and radius(origin)<TOL or axis=='z' and near(origin[2],0)):
                            boundary=coord(q);attached=attachment(s,i,pos,real,axis,boundary,records)
                            if attached is not None:
                                row['operands']=[dict(axis=axis,boundary=boundary,geometry=attached,type='radial_coordinate' if axis=='r' else 'axial_coordinate',value_mm=boundary)]
            rows.append(row)
    return rows,geometries


def expression_driver(s,index,rows,sketches,seen=None):
    """Accept one native constraint reference/alias, no arithmetic evaluation."""
    seen=set() if seen is None else seen
    key=(s.Name,index)
    if key in seen:return None
    seen.add(key)
    expressions=dict(getattr(s,'ExpressionEngine',[]));alias=s.getName(index) if hasattr(s,'getName') else ''
    expr=expressions.get('Constraints[%d]'%index,expressions.get('Constraints.'+alias))
    if not expr:return next((r for r in rows if (r['sketch'],r['constraint'])==key),None)
    match=re.fullmatch(r'(?:([A-Za-z][A-Za-z0-9_]*)\.)?Constraints(?:\[([0-9]+)\]|\.([A-Za-z][A-Za-z0-9_]*))',str(expr).strip())
    if not match:return None
    obj=sketches.get(match[1] or s.Name)
    if obj is None:
        named=[o for o in sketches.values() if getattr(o,'Label',None)==match[1]]
        obj=named[0] if len(named)==1 else None
    if obj is None:return None
    try:n=int(match[2]) if match[2] else obj.getIndexViaName(match[3])
    except (ValueError,RuntimeError):return None  # unresolved alias is a predicate miss
    if not 0<=n<len(obj.Constraints) or not active(obj,n):return None
    return expression_driver(obj,n,rows,sketches,seen)


def prove_role(role,target,operands,spans,lengths,symmetries=()):
    """Pure typed relations; each operand already attached to a consumed boundary."""
    proofs=[]
    def emit(relation,items,value):
        if near(value,target):proofs.append(dict(role=role,relation=relation,operands=items,value_mm=value))
    for span in spans:
        if span['axis']==('r' if role=='groove_depth' else 'z') and span.get('role')==role and span.get('aligned'):
            mm=abs(span['boundaries'][1]-span['boundaries'][0])
            if near(span.get('driver_value_mm',-1),mm):emit('direct_span',[span],mm)
    if role=='groove_width':
        for row in lengths:
            if row.get('operative') and row.get('role')==role:emit('operative_length',[row],row['value_mm'])
    first='outer' if role=='groove_depth' else 'upper';second='bottom' if role=='groove_depth' else 'lower'
    for a in operands:
        for b in operands:
            if a.get('boundary_role')!=first or b.get('boundary_role')!=second:continue
            if a.get('type')==b.get('type')=='Diameter' and role=='groove_depth':emit('diameter_difference_half',[a,b],(a['value_mm']-b['value_mm'])/2)
            elif role=='groove_depth' and a.get('type') in ('Radius','radial_coordinate') and b.get('type') in ('Radius','radial_coordinate'):
                emit('radius_difference',[a,b],a['value_mm']-b['value_mm'])
            elif role=='groove_width' and a.get('type')==b.get('type')=='axial_coordinate':emit('axial_boundary_difference',[a,b],a['value_mm']-b['value_mm'])
    for symmetry in symmetries:
        if role=='groove_width' and symmetry.get('active') and symmetry.get('both_boundaries') and symmetry.get('center_proved'):
            emit('symmetric_half_width',[symmetry],2*symmetry['half_width_mm'])
    return proofs


def roller_roles(body,gold):
    native,sketches,seeds,users=consumed(body)
    rows,records=driver_rows(native,sketches,seeds,users)
    p=gold['parameters'];R=p['radius'];bottom=R-p['groove_depth'];lo,hi=p['groove_z']
    operands=[];spans=[];lengths=[];symmetries=[];primary={k:[] for k in ('outer_diameter','bore_diameter','length')}
    def cylindrical_boundary(feature,r,interval=None):
        _,cylinders,_=v1.faces_of(v1.world_shape(feature))
        matching=[c for c in cylinders if near(c['radius'],r) and v1.same_bounds(c['axis'],[0,0,1],1e-6) and radius(c['center'])<TOL]
        if interval is not None:matching=[c for c in matching if near(c['bounds'][4],interval[0]) and near(c['bounds'][5],interval[1])]
        return bool(matching)
    for row in rows:
        s,real,geos=records[row['sketch']]
        resolved=expression_driver(s,row['constraint'],rows,sketches)
        if resolved is None:continue
        for op in row['operands']:
            value=op['boundary'];axis=op['axis'];geo=geos[op['geometry']]
            links=users.get(s.Name,[])
            # A consumed stock/groove profile; spine-only numerical matches cannot control a cut.
            links=[(f,k,sub) for f,k,sub in links if k in ('Profile','Sections')]
            if not links:continue
            if axis=='r':
                for name,r in (('outer_diameter',R),('bore_diameter',p['bore_radius'])):
                    if near(value,r) and any(cylindrical_boundary(f,r) for f,_,_ in links):
                        mm=op['value_mm'] if op['type']=='Diameter' else 2*op['value_mm']
                        if near(mm,2*r):primary[name].append(dict(role=name,relation='typed_diameter' if op['type']=='Diameter' else 'typed_radius_twice',value_mm=mm,operand=op,sketch=s.Name,constraint=row['constraint'],paths=row['paths']))
            if axis=='r':
                label='outer' if near(value,R) else 'bottom' if near(value,bottom) else None
                if not label:continue
                if geo.get('kind')=='line':
                    zs=sorted(a[2] for a in geo['points'])
                    if label=='bottom' and not (near(zs[0],lo) and near(zs[1],hi)):continue
                    if label=='outer' and not (zs[1]>zs[0]+TOL and (zs[0]<=lo+TOL or zs[1]>=hi-TOL)):continue
                if label=='bottom' and not any(f.TypeId in ('PartDesign::Pocket','PartDesign::Groove','PartDesign::Revolution') for f,_,_ in links):continue
                if not any(cylindrical_boundary(f,value,(lo,hi) if label=='bottom' else None) for f,_,_ in links):continue
            else:
                label='lower' if near(value,lo) else 'upper' if near(value,hi) else None
                if not label or geo.get('kind')!='line':continue
                if not all(bottom-TOL<=radius(a)<=R+TOL for a in geo['points']):continue
            # Expressions must resolve to another accepted native driver of the same typed value.
            if not near(resolved['value_mm'],row['value_mm']):continue
            operands.append(dict(op,boundary_role=label,sketch=s.Name,constraint=row['constraint'],paths=row['paths'],expression_driver=dict(sketch=resolved['sketch'],constraint=resolved['constraint']),features=[f.Name for f,_,_ in links]))
        span=row.get('span')
        if span:
            boundaries=sorted(span['boundaries'])
            if span['axis']=='z' and near(boundaries[0],0) and near(boundaries[1],p['length']):
                primary['length'].append(dict(span,role='length',relation='direct_axial_span',value_mm=p['length'],sketch=s.Name,constraint=row['constraint'],paths=row['paths']))
            role='groove_depth' if span['axis']=='r' and near(boundaries[0],bottom) and near(boundaries[1],R) else 'groove_width' if span['axis']=='z' and near(boundaries[0],lo) and near(boundaries[1],hi) else None
            if role:spans.append(dict(span,role=role,sketch=s.Name,constraint=row['constraint'],paths=row['paths']))
    for f in native:
        if f.TypeId=='PartDesign::Pad' and length_mode(f) and 'Length' in f.PropertiesList:
            if near(scalar(f.Length),p['length']) and cylindrical_boundary(f,R):
                bb=v1.bounds(v1.world_shape(f))
                if near(bb[4],0) and near(bb[5],p['length']):primary['length'].append(dict(role='length',relation='operative_length',value_mm=scalar(f.Length),feature=f.Name,property='Length'))
        if f.TypeId!='PartDesign::Pocket' or not length_mode(f) or 'Length' not in f.PropertiesList:continue
        linked=list(v2.link_items(getattr(f,'Profile',None)))
        if len(linked)!=1:continue
        s,_=linked[0];rec=records.get(s.Name)
        if not rec:continue
        _,real,geos=rec;circles=[v for i,v in geos.items() if i in real and v.get('kind')=='circle']
        # Through-all/up-to-face/two-length/default Length2 are explicitly excluded.
        zs={round(c['center'][2],7) for c in circles}
        if len(circles)!=2 or len(zs)!=1 or not any(near(c['radius'],bottom) for c in circles):continue
        if not any(c['radius']>=R-TOL for c in circles):continue
        normal=point(s,type(s.Geometry[next(iter(real))].Center)(0,0,1));origin=point(s,type(s.Geometry[next(iter(real))].Center)(0,0,0))
        dz=normal[2]-origin[2]
        if abs(abs(dz)-1)>1e-6 or getattr(f,'Midplane',False):continue
        start=next(iter(zs));length=scalar(f.Length);end=start+dz*(1 if getattr(f,'Reversed',False) else -1)*length
        if near(min(start,end),lo) and near(max(start,end),hi):
            lengths.append(dict(role='groove_width',operative=True,feature=f.Name,link='Profile',sketch=s.Name,property='Length',value_mm=length,target_geometry=sorted(real)))
    # Active Symmetric endpoints + a driven center and a driven boundary half-span.
    for name,(s,real,geos) in records.items():
        for n,c in enumerate(s.Constraints):
            if c.Type!='Symmetric' or not active(s,n) or len(v2.references(c,s.GeometryCount))!=3:continue
            a=endpoint(geos.get(c.First,{}),c.FirstPos);b=endpoint(geos.get(c.Second,{}),c.SecondPos);center=endpoint(geos.get(c.Third,{}),c.ThirdPos)
            if a is None or b is None or center is None:continue
            if not (near(min(a[2],b[2]),lo) and near(max(a[2],b[2]),hi) and near(center[2],(lo+hi)/2)):continue
            attached=[attachment(s,i,pos,real,'z',q[2],geos) for i,pos,q in [(c.First,c.FirstPos,a),(c.Second,c.SecondPos,b)]]
            # The center need not be a consumed boundary, but its own actual point
            # must be driven along Z from a uniquely resolved native origin.
            center_driven=False
            for m,d in enumerate(s.Constraints):
                if d.Type not in ('DistanceX','DistanceY') or not active(s,m):continue
                pair=(d.First,getattr(d,'FirstPos',0));other=getattr(d,'Second',-1)
                if pair!=(c.Third,c.ThirdPos) or other not in (-1,-2000):continue
                vector_type=type(s.Geometry[c.Third].StartPoint);o=point(s,vector_type(0,0,0));u=point(s,vector_type(1,0,0) if d.Type=='DistanceX' else vector_type(0,1,0))
                if abs(abs(u[2]-o[2])-1)<1e-6 and near(o[2],0) and near(abs(float(d.Value)),abs(center[2])):center_driven=True
            halves=[]
            for row in rows:
                span=row.get('candidate_span')
                if row['sketch']!=name or not span or span['axis']!='z' or not near(abs(span['boundaries'][1]-span['boundaries'][0]),(hi-lo)/2) or not near(row['value_mm'],(hi-lo)/2):continue
                # Both measured endpoints must be linked to the proven center and
                # one symmetric boundary, not merely have the same coordinates.
                i=span['geometry'];ends=geos[i]['points']
                for boundary_i,boundary_pos,boundary_point in ((c.First,c.FirstPos,a),(c.Second,c.SecondPos,b)):
                    for first_pos,second_pos in ((1,2),(2,1)):
                        if not near(ends[first_pos-1][2],center[2]) or not near(ends[second_pos-1][2],boundary_point[2]):continue
                        links=[]
                        for x,y in (((i,first_pos),(c.Third,c.ThirdPos)),((i,second_pos),(boundary_i,boundary_pos))):
                            links.append(any(active(s,k) and q.Type=='Coincident' and { (q.First,q.FirstPos),(q.Second,q.SecondPos) }=={x,y} for k,q in enumerate(s.Constraints)))
                        if all(links):halves.append(row)
            if all(i is not None for i in attached) and center_driven and halves:
                symmetries.append(dict(active=True,both_boundaries=True,center_proved=True,half_width_mm=halves[0]['value_mm'],sketch=name,constraint=n,geometry=[c.First,c.Second,c.Third],driver=halves[0]))
    return {**primary,**{role:prove_role(role,target,operands,spans,lengths,symmetries) for role,target in [('groove_depth',p['groove_depth']),('groove_width',hi-lo)]}}


def editability(doc,body,shape,gold,checks,native_shape=None):
    g=copy.deepcopy(gold)
    # v2 supplies native integrity and existing primary-dimension checks. The roller
    # list contains only OD/bore/length; depth/width can pass only by role proof.
    if gold['profile']=='roller':g['editability']['key_dimensions_mm']=[]
    measured,warnings=v2.editability(doc,body,shape,g,checks,native_shape)
    if gold['profile']=='roller':
        proofs=roller_roles(body,gold);measured['role_evidence']=proofs
        for role in ('outer_diameter','bore_diameter','length','groove_width','groove_depth'):
            expected=next(r['target_mm'] for r in gold['editability']['roles'] if r['role']==role)
            checks.add('editability','edit.role.'+role,expected,proofs[role] or None,bool(proofs[role]),TOL)
    return measured,warnings


def probe(doc,body,gold,require_editability=True):
    checks=Checks(gold['case_id']);tip=getattr(body,'Tip',None) if require_editability else None
    shape=v1.world_shape(tip) if tip else body.Shape
    if shape.isNull():
        checks.add('valid_solid','shape.null',False,True,False)
        return dict(measurements={'volume_mm3':None},predicates=checks.predicates,probe_pass=False,geometry_ok=False,editability_ok=False,skill_warnings=[],predicate_details=checks.details())
    measured=v1.measure_shape(shape,gold,checks);geometry_ok=all(checks.predicates.values());warnings=[]
    if require_editability:measured['editability'],warnings=editability(doc,body,shape,gold,checks,native_shape=tip.Shape if tip else shape)
    return dict(measurements=measured,predicates=checks.predicates,probe_pass=all(checks.predicates.values()),geometry_ok=geometry_ok,
        editability_ok=checks.predicates.get('editability') if require_editability else None,skill_warnings=warnings,predicate_details=checks.details(),
        reference=dict(gold_schema=gold['schema'],volume_mm3=gold['volume']['target_mm3'],volume_scope=gold.get('volume_scope'),probe_profile='verify-v3'))
