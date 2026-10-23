"""Fixed native SolidWorks feature recipes for data-only original60 gold.

Private gold values are consumed by this program only; never printed. Real SW
sketch/boss/cut/loft/revolve features, not imported FreeCAD shapes or source code.
Native operational editing evidence is separate from original FreeCAD history.
"""
import copy
import math


class Unsupported(ValueError):
    pass


def construction(gold):
    if 'parameters' in gold:
        return copy.deepcopy(gold['parameters'])
    if gold.get('steps'):
        return dict(profile='stepped_shaft',center_xy=gold.get('center_xy',[0,0]),steps=copy.deepcopy(gold['steps']))
    regions=copy.deepcopy(gold.get('regions',[]))
    if not regions:raise Unsupported('gold_has_no_constructible_regions')
    return dict(profile='rect_stack' if len(regions)>1 else 'rect_prism',regions=regions,
                bbox=copy.deepcopy(gold['bbox']),pockets=copy.deepcopy(gold.get('pockets',[])),
                holes=copy.deepcopy(gold.get('holes',[])),finish=copy.deepcopy(gold.get('finish')))


class Builder:
    def __init__(self,session):
        self.s=session
        self.doc=session.owned
        self.fm=self.doc.FeatureManager
        self.sm=self.doc.SketchManager
        self.util=self.s.call(self.s.app,'GetMathUtility')
        self.counter=0
        self.edit_parameter=None
        self.features=[]

    def call(self,obj,name,*args):
        return self.s.call(obj,name,*args)

    def name(self,prefix):
        self.counter+=1
        return 'M1_%s_%03d'%(prefix,self.counter)

    def _planes(self):
        f=self.call(self.doc,'FirstFeature')
        while f is not None:
            if self.call(f,'GetTypeName2')=='RefPlane':
                ref=self.call(f,'GetSpecificFeature2')
                yield f,list(ref.Transform.ArrayData)
            f=self.call(f,'GetNextFeature')

    def plane(self,axis,offset):
        self.s.guard()
        root=None
        for feature,m in self._planes():
            n=m[6:9]
            if abs(abs(n[axis])-1)<1e-9 and sum(abs(n[i]) for i in range(3) if i!=axis)<1e-9:
                if abs(m[9+axis]-offset/1000)<1e-9:
                    return feature,n
                if abs(m[9+axis])<1e-12:root=(feature,n)
        if root is None:raise Unsupported('required_default_reference_plane_missing')
        self.call(self.doc,'ClearSelection2',True)
        if not self.call(root[0],'Select2',False,0):raise RuntimeError('reference_plane_selection')
        distance=offset/1000/root[1][axis]
        constraint=8|(256 if distance<0 else 0)
        ref=self.call(self.fm,'InsertRefPlane',constraint,abs(distance),0,0.,0,0.)
        if ref is None:raise RuntimeError('offset_reference_plane_failed')
        new=self.call(self.doc,'FeatureByPositionReverse',0)
        if new is None or self.call(new,'GetTypeName2')!='RefPlane':raise RuntimeError('offset_plane_feature_identity')
        new.Name=self.name('Plane')
        for feature,m in self._planes():
            if abs(abs(m[6+axis])-1)<1e-9 and abs(m[9+axis]-offset/1000)<1e-9:
                return feature,m[6:9]
        raise RuntimeError('offset_plane_world_position_mismatch')

    def begin(self,axis,offset):
        plane,n=self.plane(axis,offset)
        self.call(self.doc,'ClearSelection2',True)
        if not self.call(plane,'Select2',False,0):raise RuntimeError('sketch_plane_selection')
        self.call(self.sm,'InsertSketch',True)
        sketch=self.sm.ActiveSketch
        self.transform=sketch.ModelToSketchTransform
        self.normal=n

    def point(self,p):
        from win32com.client import VARIANT
        a=VARIANT(self.s.pc.VT_ARRAY|self.s.pc.VT_R8,tuple(float(x)/1000 for x in p))
        q=self.call(self.util,'CreatePoint',a)
        q=self.call(q,'MultiplyTransform',self.transform)
        values=list(q.ArrayData)
        if len(values)!=3 or any(not math.isfinite(v) for v in values) or abs(values[2])>1e-7:
            raise RuntimeError('sketch_world_to_local_plane_mismatch')
        return values

    def rectangle(self,b,z):
        a=self.point((b[0],b[2],z));c=self.point((b[1],b[3],z))
        if not self.call(self.sm,'CreateCornerRectangle',*a,*c):raise RuntimeError('rectangle_creation')

    def circle(self,x,y,z,r):
        a=self.point((x,y,z))
        if self.call(self.sm,'CreateCircleByRadius',*a,float(r)/1000) is None:raise RuntimeError('circle_creation')

    def line(self,a,b,construction=False):
        a,b=self.point(a),self.point(b)
        return self.call(self.sm,'CreateCenterLine' if construction else 'CreateLine',*a,*b)

    def end(self):
        normal=self.normal
        self.call(self.sm,'InsertSketch',True)
        feature=self.call(self.doc,'FeatureByPositionReverse',0)
        if feature is None or self.call(feature,'GetTypeName2')!='ProfileFeature':
            raise RuntimeError('actual_sketch_feature_missing')
        feature.Name=self.name('Sketch')
        return feature,normal

    def extrude(self,sketch,normal,axis,direction,length,cut=False):
        self.s.guard()
        self.call(self.doc,'ClearSelection2',True)
        if not self.call(sketch,'Select2',False,0):raise RuntimeError('profile_selection')
        reverse=normal[axis]*direction<0
        # A cut's default direction is opposite the sketch normal.
        if cut:reverse=not reverse
        if cut:
            f=self.call(self.fm,'FeatureCut4',True,False,reverse,0,0,length/1000,0.,
                False,False,False,False,0.,0.,False,False,False,False,False,True,True,
                False,False,False,0,0.,False,False)
        else:
            f=self.call(self.fm,'FeatureExtrusion3',True,False,reverse,0,0,length/1000,0.,
                False,False,False,False,0.,0.,False,False,False,False,True,True,True,0,0.,False)
        if f is None:raise RuntimeError('native_cut_failed' if cut else 'native_boss_failed')
        f.Name=self.name('Cut' if cut else 'Boss')
        self.features.append({'name':f.Name,'type':self.call(f,'GetTypeName2')})
        self.edit_parameter='D1@'+f.Name
        return f

    def rect_pad(self,b):
        self.begin(2,b[4]);self.rectangle(b[:4],b[4]);sk,n=self.end()
        return self.extrude(sk,n,2,1,b[5]-b[4])

    def pocket(self,p):
        self.begin(2,p['top_z']);self.rectangle(p['bounds'],p['top_z']);sk,n=self.end()
        return self.extrude(sk,n,2,-1,p['depth'],True)

    def holes(self,holes,default_z):
        for h in holes:
            low,high=h.get('z',default_z)
            self.begin(2,high);self.circle(*h['center_xy'],high,h['diameter']/2);sk,n=self.end()
            self.extrude(sk,n,2,-1,high-low,True)

    def finish(self,b,f):
        if not f:return
        self.call(self.doc,'ClearSelection2',True)
        data=self.call(self.doc.SelectionManager,'CreateSelectData')
        data.Mark=1 if f['kind']=='fillet' else 0
        selected=[]
        for edge in self.call(self.s.body(),'GetEdges'):
            a,c=self.call(edge,'GetStartVertex'),self.call(edge,'GetEndVertex')
            if a is None or c is None:continue
            pts=[self.call(v,'GetPoint') for v in (a,c)]
            if all(abs(p[2]-b[5]/1000)<1e-8 for p in pts) and any(
                all(abs(p[axis]-side/1000)<1e-8 for p in pts)
                for axis,side in ((0,b[0]),(0,b[1]),(1,b[2]),(1,b[3]))):
                if not self.call(edge,'Select4',True,data):raise RuntimeError('finish_edge_selection')
                selected.append(edge)
        if len(selected)!=4:raise RuntimeError('finish_requires_four_actual_outer_top_edges')
        if f['kind']=='fillet':
            feature=self.call(self.fm,'FeatureFillet3',2,f['size']/1000,0.,0.,0,0,0,None,None,None,None,None,None,None)
        elif f['kind']=='chamfer':
            feature=self.call(self.fm,'InsertFeatureChamfer',0,1,f['size']/1000,math.pi/4,0.,0.,0.,0.)
        else:raise Unsupported('finish_kind_not_in_fixed_M1_recipes')
        if feature is None:raise RuntimeError('native_finish_failed')
        feature.Name=self.name('Finish')
        self.features.append({'name':feature.Name,'type':self.call(feature,'GetTypeName2')})
        # Prefer a consumed editable finish radius/size to a through-cut depth.
        self.edit_parameter='D1@'+feature.Name

    def build(self,p):
        kind=p['profile']
        if kind in ('rect_prism','rect_stack'):
            regions=p.get('regions') or [dict(bounds=p['bbox'])]
            for r in regions:self.rect_pad(r['bounds'])
            for q in p.get('pockets',[]):self.pocket(q)
            base_parameter=self.edit_parameter
            for h in p.get('holes',[]):self.holes([h],p['bbox'][4:6])
            self.finish(p['bbox'],p.get('finish'))
            if not p.get('finish'):self.edit_parameter=base_parameter
        elif kind=='roller':
            self.begin(2,0);self.circle(0,0,0,p['radius']);self.circle(0,0,0,p['bore_radius']);sk,n=self.end()
            self.extrude(sk,n,2,1,p['length'])
            low,high=p['groove_z']
            self.begin(2,high);self.circle(0,0,high,p['radius']);self.circle(0,0,high,p['radius']-p['groove_depth']);sk,n=self.end()
            self.extrude(sk,n,2,-1,high-low,True)
        elif kind=='taper':
            profiles=[]
            for z,dims in ((0,p['bottom']),(p['height'],p['top'])):
                self.begin(2,z);w,d=dims;self.rectangle([-w/2,w/2,-d/2,d/2],z);profiles.append(self.end()[0])
            self.call(self.doc,'ClearSelection2',True)
            for i,sk in enumerate(profiles):
                if not self.call(sk,'Select2',bool(i),1):raise RuntimeError('loft_profile_selection')
            f=self.call(self.fm,'InsertProtrusionBlend2',False,False,True,1.,0,0,1.,1.,False,False,False,0.,0.,0,True,True,True,0)
            if f is None:raise RuntimeError('native_loft_failed')
            f.Name=self.name('Loft');self.features.append({'name':f.Name,'type':self.call(f,'GetTypeName2')})
            # Height is carried by an actually consumed offset reference plane.
            for plane,m in self._planes():
                if abs(m[11]-p['height']/1000)<1e-9:self.edit_parameter='D1@'+plane.Name
        elif kind=='elbow':
            self.begin(0,0)
            self.circle(0,0,0,p['outer_radius']);self.circle(0,0,0,p['inner_radius'])
            axis=self.line((0,p['path_radius'],-p['outer_radius']*2),(0,p['path_radius'],p['outer_radius']*2),True)
            sk,n=self.end()
            self.call(self.doc,'ClearSelection2',True)
            if not self.call(sk,'Select2',False,0):raise RuntimeError('revolve_profile_selection')
            f=self.call(self.fm,'FeatureRevolve2',True,True,False,False,False,False,0,0,math.pi/2,0.,False,False,0.,0.,0,0.,0.,True,True,True)
            if f is None:raise RuntimeError('native_quarter_revolve_failed')
            f.Name=self.name('Revolve');self.features.append({'name':f.Name,'type':self.call(f,'GetTypeName2')})
            self.edit_parameter='D1@'+f.Name
        elif kind=='ribbed_box':
            b,t=p['bbox'],p['wall'];self.rect_pad(b)
            self.pocket(dict(bounds=[b[0]+t,b[1]-t,b[2]+t,b[3]-t],top_z=b[5],depth=b[5]-t))
            x0,x1=b[0]+t,b[1]-t;y=p['rib_thickness']/2
            self.begin(1,y)
            pts=[(x0,y,t),(x1,y,t),(x1,y,p['rib_top'])]
            for i in range(3):self.line(pts[i],pts[(i+1)%3])
            sk,n=self.end();self.extrude(sk,n,1,-1,p['rib_thickness'])
        elif kind=='flange':
            z=p['thickness']
            self.begin(2,0);self.circle(0,0,0,p['radius']);self.circle(0,0,0,p['bore_radius']);sk,n=self.end()
            self.extrude(sk,n,2,1,z);base_parameter=self.edit_parameter
            holes=[dict(center_xy=[p['pcd_radius']*math.cos(2*math.pi*i/p['pcd_count']),p['pcd_radius']*math.sin(2*math.pi*i/p['pcd_count'])],diameter=2*p['hole_radius']) for i in range(p['pcd_count'])]
            self.holes(holes,[0,z])
            for q in p.get('pockets',[]):self.pocket(q)
            if not p.get('pockets'):self.edit_parameter=base_parameter
        elif kind=='stepped_shaft':
            for step in p['steps']:
                low,high=step['z'];self.begin(2,low);self.circle(*p.get('center_xy',[0,0]),low,step['diameter']/2);sk,n=self.end()
                self.extrude(sk,n,2,1,high-low)
        else:raise Unsupported('gold_profile_has_no_fixed_native_recipe')
        self.s.guard()
        if not self.call(self.doc,'EditRebuild3'):raise RuntimeError('native_rebuild_failed')
        self.s.body()
        return {'features':self.features,'edit_parameter':self.edit_parameter,
                'construction':'actual_SW_native_features','not_original_FreeCAD_history':True}
