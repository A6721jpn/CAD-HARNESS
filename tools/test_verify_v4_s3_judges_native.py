"""Independent analytic/native C6 controls, never the C5 fitter as truth.

Run with CAD_VERIFY_S3_NATIVE=1 and bundled native Python -B -m unittest tools.test_verify_v4_s3_judges_native.
The host-safe card suite is separate. No compiler/rebuild imports occur here.
"""
import copy
import importlib.util
import json
import math
import os
from pathlib import Path
import sys
import tempfile
import unittest

NATIVE = (os.environ.get('CAD_VERIFY_S3_NATIVE') == '1' and sys.version_info[:3] == (3,11,14) and importlib.util.find_spec('FreeCAD') is not None)
NATIVE_REASON = 'set CAD_VERIFY_S3_NATIVE=1 under pinned FreeCAD Python; no launch at discovery'
App = Part = None

from tools import cad_verify_v4_s3_judges as judges


def _poly_local(coefficients,x0,x1,y0,y1):
    result = {}
    for (i,j),value in coefficients.items():
        for k in range(i+1):
            for h in range(j+1):
                term = value*math.comb(i,k)*math.comb(j,h)*x0**(i-k)*(x1-x0)**k*y0**(j-h)*(y1-y0)**h
                result[k,h] = result.get((k,h),0.)+term
    return result


def analytic_face(coefficients,physical=(0.,1.,0.,1.),degree=(3,3),native=(0.,1.,0.,1.),swap=False,reverse_u=False,reverse_v=False):
    """Exact power-to-Bernstein conversion of an independently declared graph."""
    x0,x1,y0,y1 = physical
    n,m = degree
    local = _poly_local(coefficients,x0,x1,y0,y1)
    poles = []
    for i in range(n+1):
        row = []
        for j in range(m+1):
            z = sum(value*math.comb(i,k)/math.comb(n,k)*math.comb(j,h)/math.comb(m,h) for (k,h),value in local.items() if k<=i and h<=j)
            row.append(App.Vector(x0+(x1-x0)*i/n,y0+(y1-y0)*j/m,z))
        poles.append(row)
    # Flags describe native -> chart. Apply their inverse to the native net.
    if reverse_u:
        poles = list(reversed(poles))
    if reverse_v:
        poles = [list(reversed(row)) for row in poles]
    if swap:
        poles = [list(row) for row in zip(*poles)]
        n,m = m,n
    surface = Part.BSplineSurface()
    surface.buildFromPolesMultsKnots(poles,[n+1,n+1],[m+1,m+1],list(native[:2]),list(native[2:]),False,False,n,m)
    face = surface.toShape()
    if (swap+reverse_u+reverse_v)%2:
        face.reverse()
    mapping = dict(domain_uv=list(native),chart_uv=list(physical),swap_uv=swap,reverse_u=reverse_u,reverse_v=reverse_v)
    return face,mapping


def patch(control,eps=1e-9):
    return judges._patch(*control,eps)


def continuity(patches,g2=True,resources=None,position=.008,normal=.009,curvature=.012):
    side = lambda index: dict(patch=index,axis='u',value=1.,range=[0.,1.],reverse=False)
    result = dict(metric='g2_continuity' if g2 else 'g1_continuity',maximum_position_mm=position,maximum_normal_sin=normal,seams=[dict(a=side(0),b=side(1))],resources=resources or dict(max_depth=16,max_cells=60000))
    if g2:
        result['maximum_curvature_per_mm']=curvature
    return judges.certify_continuity(patches,result)


class S3CardAdmission(unittest.TestCase):
    def test_strict_finite_independent_card(self):
        card = dict(schema='cad-harness.judge-card.v4c',profile='c-s3',source='independent_dev',numerical_uncertainty_mm=1e-6,criteria=[dict(id='solid',metric='solid_valid',expected_solids=1)])
        admitted = judges.validate_card(card)
        admitted['criteria'][0]['id']='changed'
        self.assertEqual(card['criteria'][0]['id'],'solid')
        for key,value in (('numerical_uncertainty_mm',float('nan')),('profile','c-s2'),('fitted_error_mm',0.)):
            bad = copy.deepcopy(card)
            bad[key]=value
            with self.assertRaises(ValueError):
                judges.validate_card(bad)
        bad = copy.deepcopy(card)
        bad['criteria']*=2
        with self.assertRaises(ValueError):
            judges.validate_card(bad)

    def test_native_full_is_explicit_host_safe_domain_method(self):
        mapping = dict(bounds_mm=[0.,1.,0.,1.,0.,1.],domain_uv='native_full',chart_uv=[0.,1.,0.,1.],swap_uv=False,reverse_u=False,reverse_v=False)
        criterion = dict(id='surface',metric='surface_deviation',maximum_mm=.03,output_region_mm=[0.,1.,0.,1.,-.1,1.1],selection_tolerance_mm=1e-6,output_patches=[mapping],resources=dict(max_depth=14,max_cells=12000))
        card = dict(schema='cad-harness.judge-card.v4c',profile='c-s3',source='independent_dev',numerical_uncertainty_mm=1e-6,criteria=[criterion])
        self.assertEqual(judges.validate_card(card),card)
        mapping['domain_uv']='nearest'
        with self.assertRaises(ValueError):
            judges.validate_card(card)


@unittest.skipUnless(NATIVE,NATIVE_REASON)
class PolynomialNativeCertificates(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        global App,Part
        import FreeCAD as App
        import Part
        if tuple(App.Version()[:3]) != ('1','1','4'):
            raise RuntimeError('requires_pinned_FreeCAD_1_1_4')

    def test_complete_native_pipeline_metrics_without_fitter(self):
        from tools import cad_verify_v4_inputs as inputs
        from tools import cad_verify_v4_ledger as ledger
        from tools import cad_verify_v4_plans as plans
        with tempfile.TemporaryDirectory(prefix='cad-s3-independent-judges-') as directory:
            root = Path(directory)
            shape = Part.makeBox(9.,7.,3.)
            step = root/'source.step'
            shape.exportStep(str(step))
            digest = ledger.file_sha(step)
            manifest = root/'manifest.json'
            manifest.write_text(json.dumps(dict(schema='cad-harness.inputs.v4c',profile='c-s3',evidence_mode='independent_dev',assets={'source':dict(kind='step',role='reference',path='source.step',sha256=digest,bytes=step.stat().st_size)})),encoding='utf-8')
            recipe = dict(schema='cad-harness.step-recipe.v4c',profile='c-s3',source_axes=['X','Y','Z'],source_units='mm',signature_precision_mm=1e-6)
            prepared = inputs.inspect_step(manifest,'source',recipe,root/'prepared.json')
            selected = max(prepared['assets']['source']['faces'],key=lambda f:f['center_mm'][2])
            cell = {k:selected[k] for k in ('signature','adjacent_face_ids')}
            cell.update(face_id=selected['id'],swap_uv=False,reverse_u=False,reverse_v=False)
            plan = dict(schema='cad-harness.plan.v4c',profile='c-s3',family='surface_rebuild',asset_id='source',source_sha256=digest,grid=[[cell]],continuity='G2',fit_tolerance_mm=.07,kernel_tolerance_mm=1e-6,max_degree=5,max_poles=120)
            criteria = [dict(id='solid',metric='solid_valid',expected_solids=1),dict(id='faces',metric='face_count',scope='full',relation='equal',correspondence='spatial_fixed_frame',expected_count=6),dict(id='reopen',metric='native_roundtrip',maximum_bounds_difference_mm=.004,maximum_volume_difference_mm3=.03,require_editable=False)]
            card = dict(schema='cad-harness.judge-card.v4c',profile='c-s3',source='independent_dev',numerical_uncertainty_mm=1e-5,criteria=criteria)
            doc = App.newDocument('S3IndependentRoundtrip')
            try:
                feature = doc.addObject('PartDesign::Body','Body').newObject('PartDesign::Feature','NativeControl')
                feature.Shape=shape
                doc.recompute()
                fcstd = root/'control.FCStd'
                doc.saveAs(str(fcstd))
            finally:
                App.closeDocument(doc.Name)
            reopened = App.openDocument(str(fcstd))
            try:
                actual = reopened.getObject('NativeControl').Shape
                imported = Part.Shape()
                imported.read(str(step))
                evidence = dict(fcstd_reopened=not actual.isNull(),step_reopened=not imported.isNull(),editable=False,bounds_difference_mm=max(abs(a-b) for a,b in zip(judges._bounds(actual),judges._bounds(imported))),volume_difference_mm3=abs(actual.Volume-imported.Volume))
                result = judges.judge(plan,manifest,prepared,actual,card,native_evidence=evidence)
                plans.validate_document(result,'judge-result',profile='c-s3')
                self.assertEqual(result['status'],'PASS',result)
                self.assertEqual(judges.judge(plan,manifest,prepared,actual,card)['status'],'UNVERIFIED')
                bad = dict(evidence,step_reopened=False)
                self.assertEqual(judges.judge(plan,manifest,prepared,actual,card,native_evidence=bad)['status'],'FAIL')
            finally:
                App.closeDocument(reopened.Name)

    def test_actual_bezier_saddle_uses_raw_controls_not_approximate_conversion(self):
        surface = Part.BezierSurface()
        for i,x in enumerate((0.,2.),1):
            for j,y in enumerate((0.,3.),1):
                surface.setPole(i,j,App.Vector(x,y,.08*x*y))
        self.assertEqual(surface.UDegree,1)
        mapping = dict(domain_uv=[0.,1.,0.,1.],chart_uv=[0.,2.,0.,3.],swap_uv=False,reverse_u=False,reverse_v=False)
        a = patch((surface.toShape(),mapping))
        self.assertEqual(len(a['spans'][0]['net']),2)
        b = patch(analytic_face({(1,1):.08},physical=(0.,2.,0.,3.),degree=(3,3)))
        status,measured,_ = judges.certify_deviation([a],[b],[0.,2.,0.,3.],.004,dict(max_depth=12,max_cells=12000),1e-9)
        self.assertEqual(status,'PASS',measured)

    def test_native_full_polynomial_endpoint_extension_is_not_clipped(self):
        polynomial = {(2,0):.2,(1,1):.06,(0,2):.1}
        original,_ = analytic_face(polynomial,degree=(3,4))
        extended = original.Surface.toShape(-.125,1.125,-.0625,1.0625)
        mapping = dict(domain_uv='native_full',chart_uv=[0.,1.,0.,1.],swap_uv=False,reverse_u=False,reverse_v=False)
        control = patch((extended,mapping))
        self.assertEqual(control['mapping']['domain_uv'],list(extended.ParameterRange))
        self.assertEqual(control['domain_method'],'native_full')
        self.assertEqual(len(control['spans']),1)
        net = control['spans'][0]['net']
        for u,v in ((0.,0.),(.23,.71),(1.,1.)):
            native_u,native_v = -.125+1.25*u,-.0625+1.125*v
            expected = [native_u,native_v,.2*native_u**2+.06*native_u*native_v+.1*native_v**2]
            enclosed = judges._curve_at([judges._curve_at(row,v) for row in net],u)
            self.assertTrue(all(q.lo<=p<=q.hi for p,q in zip(expected,enclosed)),(expected,enclosed))
            self.assertLess((extended.valueAt(native_u,native_v)-App.Vector(*expected)).Length,1e-10)
        state,measured,_ = judges.certify_deviation([control],[control],[0.,1.,0.,1.],.002,dict(max_depth=12,max_cells=12000),1e-9)
        self.assertEqual(state,'PASS',measured)

    def test_unequal_physical_transverse_speed_is_geometric_g2(self):
        polynomial = {(2,0):.07,(1,1):.04,(0,2):.11}
        a = patch(analytic_face(polynomial,physical=(0.,1.,0.,1.),degree=(3,4)))
        face,mapping = analytic_face(polynomial,physical=(1.,3.,0.,1.),degree=(3,4),native=(-2.,9.,4.,7.),swap=True,reverse_v=True)
        mapping['chart_uv']=[1.,2.,0.,1.]
        b = patch((face,mapping))
        # Global chart derivatives differ by a factor two; raw jet equality
        # cannot certify these actual geometrically identical second forms.
        status,measured,evidence = continuity([a,b])
        self.assertEqual(status,'PASS',(measured,evidence))

    def test_reparameterized_nonplanar_g2(self):
        polynomial = {(2,0):.07,(1,1):.04,(0,2):.11,(3,0):.015}
        a = patch(analytic_face(polynomial,physical=(0.,1.,0.,1.),degree=(3,4)))
        b = patch(analytic_face(polynomial,physical=(1.,2.,0.,1.),degree=(3,4),native=(-3.,7.,2.,5.),swap=True,reverse_u=True))
        status,measured,evidence = continuity([a,b])
        self.assertEqual(status,'PASS',(measured,evidence))
        self.assertLessEqual(measured['upper'][2],.012)

    def test_g1_only_quadratic_decoy(self):
        a = patch(analytic_face({(0,2):.08},physical=(0.,1.,0.,1.)))
        # Height and slope agree at x=1; second fundamental form does not.
        b = patch(analytic_face({(0,2):.08,(2,0):.4,(1,0):-.8,(0,0):.4},physical=(1.,2.,0.,1.)))
        self.assertEqual(continuity([a,b],g2=False)[0],'PASS')
        self.assertEqual(continuity([a,b],g2=True)[0],'FAIL')

    def test_rotated_principal_curvatures_in_physical_frame(self):
        # At the origin these jets have the same eigenvalues {0.2,0.6},
        # but principal directions rotated by 45 degrees. Scalar comparison
        # would accept them. Ambient operators must distinguish them.
        one = [[judges.I(x) for x in row] for row in ((0,0,0),(1,0,0),(0,1,0),(0,0,.2),(0,0,0),(0,0,.6))]
        two = [[judges.I(x) for x in row] for row in ((0,0,0),(1,0,0),(0,1,0),(0,0,.4),(0,0,-.2),(0,0,.4))]
        sa = judges._geometry(one,1)[2]
        sb = judges._geometry(two,1)[2]
        residual = judges._norm([sa[i][j]-sb[i][j] for i in range(3) for j in range(3)])
        self.assertGreater(residual.lo,.35)
        # Actual native polynomial controls carry the same jets, not a report.
        fa,_ = analytic_face({(2,0):.1,(0,2):.3})
        fb,_ = analytic_face({(2,0):.2,(1,1):-.2,(0,2):.2})
        self.assertAlmostEqual(fa.Surface.value(0,0).z,fb.Surface.value(0,0).z)
        controls = [patch(analytic_face({(2,0):.1,(0,2):.3})),patch(analytic_face({(2,0):.2,(1,1):-.2,(0,2):.2}))]
        operators = []
        for control in controls:
            jets = [judges._curve_at([judges._curve_at(row,0.) for row in net],0.) for net in judges._jet_nets(control['spans'][0])]
            operators.append(judges._geometry(jets,1)[2])
        native_residual = judges._norm([operators[0][i][j]-operators[1][i][j] for i in range(3) for j in range(3)])
        self.assertGreater(native_residual.lo,.35)

    def test_full_domain_offgrid_localized_deviation(self):
        # z=600*x^2*(1-x)^2*(x-.5)^2*y^2*(1-y)^2:
        # every 3x3 coarse sample is exactly zero, while interior spikes exist.
        u = {2:.25,3:-1.5,4:3.25,5:-3.,6:1.}
        v = {2:1.,3:-2.,4:1.}
        polynomial = {(i,j):600*a*b for i,a in u.items() for j,b in v.items()}
        a = patch(analytic_face({},degree=(6,4)))
        b = patch(analytic_face(polynomial,degree=(6,4)))
        for x in (0.,.5,1.):
            for y in (0.,.5,1.):
                self.assertLess(abs(b['face'].Surface.value(x,y).z),1e-12)
        status,measured,_ = judges.certify_deviation([a],[b],[0.,1.,0.,1.],.03,dict(max_depth=14,max_cells=20000),1e-9)
        self.assertEqual(status,'FAIL',measured)
        self.assertGreater(measured['lower_mm'],.03)
        self.assertGreaterEqual(measured['upper_mm'],measured['lower_mm'])

    def test_nontrivial_continuous_deviation_pass(self):
        polynomial = {(2,0):.2,(0,2):.1,(1,1):.06,(3,0):-.03}
        a = patch(analytic_face(polynomial))
        # Native affine parameterization differs by unequal UV scales.
        b = patch(analytic_face(polynomial,native=(-5.,13.,3.,3.75),reverse_u=True))
        status,measured,_ = judges.certify_deviation([a],[b],[0.,1.,0.,1.],.002,dict(max_depth=12,max_cells=10000),1e-9)
        self.assertEqual(status,'PASS',measured)
        self.assertLessEqual(measured['upper_mm'],.002)

    def test_bidirectional_native_closestpoint_not_correspondence_lower(self):
        a = patch(analytic_face({},degree=(2,2)))
        b = patch(analytic_face({},degree=(2,2),reverse_u=True,reverse_v=True))
        status,measured,_ = judges.certify_deviation([a],[b],[0.,1.,0.,1.],.004,dict(max_depth=8,max_cells=2000),1e-9)
        self.assertEqual(status,'PASS')
        self.assertEqual(measured['lower_mm'],0.)

    def test_resource_bound_and_singular_are_unverified(self):
        polynomial = {(2,0):.08,(0,2):.06}
        a = patch(analytic_face(polynomial,physical=(0.,1.,0.,1.)))
        b = patch(analytic_face(polynomial,physical=(1.,2.,0.,1.)))
        self.assertEqual(continuity([a,b],resources=dict(max_depth=0,max_cells=1),position=1e-13,normal=1e-13,curvature=1e-13)[0],'UNVERIFIED')
        jets = [[judges.I(x) for x in row] for row in ((0,0,0),(1,0,0),(2,0,0),(0,0,0),(0,0,0),(0,0,0))]
        with self.assertRaisesRegex(judges.Unknown,'jacobian|metric'):
            judges._geometry(jets,1)
        # Actual polynomial native patch has x=1+t^2: the joining boundary
        # loses rank although sampled face normals elsewhere look regular.
        surface = Part.BSplineSurface()
        poles = [[App.Vector(x,j/2,0.) for j in range(3)] for x in (1.,1.,2.)]
        surface.buildFromPolesMultsKnots(poles,[3,3],[3,3],[0.,1.],[0.,1.],False,False,2,2)
        mapping = dict(domain_uv=[0.,1.,0.,1.],chart_uv=[1.,2.,0.,1.],swap_uv=False,reverse_u=False,reverse_v=False)
        singular = patch((surface.toShape(),mapping))
        regular = patch(analytic_face({},physical=(0.,1.,0.,1.),degree=(2,2)))
        self.assertEqual(continuity([regular,singular],resources=dict(max_depth=0,max_cells=1))[0],'UNVERIFIED')

    def test_trim_holes_and_incomplete_chart_coverage(self):
        face,mapping = analytic_face({(2,0):.1})
        # A rectangular support with a triangular actual trimming wire must
        # not gain an upper certificate from its untrimmed control net.
        points = [face.Surface.value(0,0),face.Surface.value(1,0),face.Surface.value(0,1)]
        wire = Part.makePolygon(points+[points[0]])
        triangle = Part.Face(face.Surface,wire)
        with self.assertRaises(judges.Unknown):
            judges._patch(triangle,mapping,1e-9)
        cropped = copy.deepcopy(mapping)
        cropped['domain_uv'][0]+=1e-11
        with self.assertRaisesRegex(judges.Unknown,'complete_trimmed_face'):
            judges._patch(face,cropped,1e-9)
        with self.assertRaisesRegex(judges.Unknown,'coverage'):
            judges._tile([[0.,.49,0.,1.],[.51,1.,0.,1.]],[0.,1.,0.,1.])
        with self.assertRaisesRegex(judges.Unknown,'coverage'):
            judges._tile([[0.,.6,0.,1.],[.4,1.,0.,1.]],[0.,1.,0.,1.])

    def test_rational_domain_is_explicitly_unsupported(self):
        face,mapping = analytic_face({(2,0):.1},degree=(2,2))
        surface = face.Surface.copy()
        surface.setWeight(2,2,1.3)
        with self.assertRaisesRegex(judges.Unknown,'rational'):
            judges._patch(surface.toShape(),mapping,1e-9)

    def test_registered_roi_is_face_order_independent_and_complete(self):
        a,ma = analytic_face({(0,0):2.},physical=(0.,1.,0.,1.))
        b,mb = analytic_face({(0,0):2.},physical=(1.,2.,0.,1.))
        ma['bounds_mm'],mb['bounds_mm'] = judges._bounds(a),judges._bounds(b)
        card = dict(output_region_mm=[-.1,2.1,-.1,1.1,1.8,2.2],selection_tolerance_mm=1e-7,output_patches=[ma,mb])
        output = judges._output(Part.makeCompound([b,a]),card,1e-9)
        self.assertEqual(len(output),2)
        # Real additional face in the region cannot be silently omitted.
        extra,_ = analytic_face({(0,0):2.1},physical=(.1,.2,.1,.2))
        candidate = Part.makeCompound([a,b,extra])
        mapped = judges._output(candidate,card,1e-9)
        plan = dict(grid=[[dict(face_id='Face1')],[dict(face_id='Face2')]])
        state,evidence = judges._outside_preservation(Part.makeCompound([a,b]),candidate,plan,mapped,1e-9,dict(max_depth=12,max_cells=12000))
        self.assertEqual(state,'FAIL',evidence)

    def test_same_face_internal_knots_use_one_sided_jets(self):
        left,_ = analytic_face({(0,2):.09},physical=(0.,1.,0.,1.),degree=(2,2))
        right,_ = analytic_face({(0,2):.09,(2,0):.3,(1,0):-.6,(0,0):.3},physical=(1.,2.,0.,1.),degree=(2,2))
        poles = left.Surface.getPoles()+right.Surface.getPoles()[1:]
        surface = Part.BSplineSurface()
        surface.buildFromPolesMultsKnots(poles,[3,2,3],[3,3],[0.,1.,2.],[0.,1.],False,False,2,2)
        mapping = dict(domain_uv=[0.,2.,0.,1.],chart_uv=[0.,2.,0.,1.],swap_uv=False,reverse_u=False,reverse_v=False)
        control = patch((surface.toShape(),mapping))
        side = dict(patch=0,axis='u',value=1.,range=[0.,1.],reverse=False)
        criterion = dict(metric='g2_continuity',maximum_position_mm=.008,maximum_normal_sin=.009,maximum_curvature_per_mm=.012,seams=[dict(a=side,b=dict(side))],resources=dict(max_depth=16,max_cells=60000))
        judges._seam_coverage([control],criterion,[0.,2.,0.,1.])
        self.assertEqual(judges.certify_continuity([control],criterion)[0],'FAIL')
        virtual = copy.deepcopy(criterion)
        virtual['seams'][0]['a']['value']=.999999
        virtual['seams'][0]['b']['value']=.999999
        # The virtual card line lies inside the LEFT polynomial and is smooth.
        # The actual native knot still MUST be judged at exact native u=1.
        self.assertEqual(judges.certify_continuity([control],virtual)[0],'FAIL')
        criterion['metric']='g1_continuity'
        self.assertEqual(judges.certify_continuity([control],criterion)[0],'PASS')
        smooth,mapping = analytic_face({(3,0):.02,(1,1):.04,(0,2):.09},physical=(0.,2.,0.,1.),native=(0.,2.,0.,1.),degree=(3,3))
        surface = smooth.Surface.copy()
        surface.insertUKnot(1.,1,1e-12)
        criterion['metric']='g2_continuity'
        control = patch((surface.toShape(),mapping))
        self.assertEqual(judges.certify_continuity([control],criterion)[0],'PASS')
        exact = dict(criterion,maximum_position_mm=0.,maximum_normal_sin=0.,maximum_curvature_per_mm=0.)
        status,measured,evidence = judges.certify_continuity([control],exact)
        self.assertEqual(status,'PASS',(measured,evidence))
        self.assertEqual(measured['upper'],[0.,0.,0.])
        self.assertGreaterEqual(evidence['structural_exact_seams'],1)
        self.assertEqual(evidence['automatic_native_seams'],1)
        reversed_map = copy.deepcopy(exact)
        reversed_map['seams'][0]['b']['reverse']=True
        self.assertNotEqual(judges.certify_continuity([control],reversed_map)[0],'PASS')
        with self.assertRaisesRegex(judges.Unknown,'correspondence'):
            judges._seam_coverage([control],reversed_map,[0.,2.,0.,1.])
        missing = dict(criterion,seams=[])
        with self.assertRaisesRegex(judges.Unknown,'omitted'):
            judges._seam_coverage([control],missing,[0.,2.,0.,1.])

    def test_exact_structural_path_cannot_bypass_native_singular_seam(self):
        surface = Part.BSplineSurface()
        poles = [[App.Vector(x,j,0.) for j in (0.,1.)] for x in (-1.,1.,-1.,1.)]
        surface.buildFromPolesMultsKnots(poles,[4,4],[2,2],[0.,2.],[0.,1.],False,False,3,1)
        mapping = dict(domain_uv=[0.,2.,0.,1.],chart_uv=[0.,2.,0.,1.],swap_uv=False,reverse_u=False,reverse_v=False)
        control = patch((surface.toShape(),mapping))
        side = dict(patch=0,axis='u',value=1.,range=[0.,1.],reverse=False)
        criterion = dict(metric='g2_continuity',maximum_position_mm=0.,maximum_normal_sin=0.,maximum_curvature_per_mm=0.,seams=[dict(a=side,b=dict(side))],resources=dict(max_depth=0,max_cells=1))
        with self.assertRaisesRegex(judges.Unknown,'jacobian_singular'):
            judges.certify_continuity([control],criterion)

    def test_exact_numeric_boundary_is_not_rounded_to_pass(self):
        a = patch(analytic_face({}))
        b = patch(analytic_face({(0,0):.125}))
        resources = dict(max_depth=0,max_cells=1)
        status,measured,_ = judges.certify_deviation([a],[b],[0.,1.,0.,1.],.125,resources,1e-9)
        self.assertEqual(status,'UNVERIFIED',measured)
        self.assertLess(measured['lower_mm'],.125)
        self.assertGreater(measured['upper_mm'],.125)
        self.assertEqual(judges.certify_deviation([a],[b],[0.,1.,0.,1.],.125+4e-9,resources,1e-9)[0],'PASS')
        self.assertEqual(judges.certify_deviation([a],[b],[0.,1.,0.,1.],.125-4e-9,resources,1e-9)[0],'FAIL')

    def test_polynomial_periodic_domain_is_explicitly_unsupported(self):
        poles = [[App.Vector(x,y,z) for z in (0.,1.)] for x,y in ((1.,0.),(-.5,.9),(-.5,-.9))]
        surface = Part.BSplineSurface()
        surface.buildFromPolesMultsKnots(poles,[1,1,1,1],[2,2],[0.,1.,2.,3.],[0.,1.],True,False,2,1)
        face = surface.toShape()
        mapping = dict(domain_uv=list(face.ParameterRange),chart_uv=[0.,1.,0.,1.],swap_uv=False,reverse_u=False,reverse_v=False)
        with self.assertRaisesRegex(judges.Unknown,'periodic'):
            judges._patch(face,mapping,1e-9)

    def test_closed_same_face_count_outside_bottom_outlier_fails(self):
        original = Part.makeBox(9.,7.,3.)
        candidate = Part.makeBox(9.,7.,4.,App.Vector(0.,0.,-1.))
        self.assertTrue(candidate.isValid())
        self.assertTrue(candidate.isClosed())
        self.assertEqual(len(candidate.Faces),len(original.Faces))
        selected = max(range(len(original.Faces)),key=lambda i:original.Faces[i].CenterOfMass.z)
        plan = dict(grid=[[dict(face_id='Face'+str(selected+1))]])
        roof = max(candidate.Faces,key=lambda f:f.CenterOfMass.z)
        self.assertAlmostEqual(roof.CenterOfMass.z,3.)
        state,evidence = judges._outside_preservation(original,candidate,plan,[dict(face=roof)],1e-6,dict(max_depth=14,max_cells=12000))
        self.assertEqual(state,'FAIL',evidence)
        self.assertGreater(evidence['lower_mm'],.5)

    def test_curved_bottom_and_polynomial_trim_walls_full_step_identity(self):
        roof,_ = analytic_face({(2,0):.13,(1,1):.04,(0,2):.07},physical=(0.,2.,0.,1.),degree=(3,3))
        original = roof.extrude(App.Vector(0.,0.,-3.))
        self.assertTrue(original.isValid())
        self.assertTrue(original.isClosed())
        selected = max(range(len(original.Faces)),key=lambda i:original.Faces[i].CenterOfMass.z)
        plan = dict(grid=[[dict(face_id='Face'+str(selected+1))]])
        with tempfile.TemporaryDirectory(prefix='cad-s3-curved-outside-') as directory:
            path = Path(directory)/'independent.step'
            original.exportStep(str(path))
            candidate = Part.Shape()
            candidate.read(str(path))
            roof = max(candidate.Faces,key=lambda f:f.CenterOfMass.z)
            state,evidence = judges._outside_preservation(original,candidate,plan,[dict(face=roof)],2e-6,dict(max_depth=16,max_cells=50000))
            self.assertEqual(state,'PASS',evidence)
            self.assertEqual(evidence['source_faces'],5)
            self.assertLessEqual(evidence['upper_mm'],2e-6)

    def test_actual_boundary_equality(self):
        # Nonflat common boundary, unequal speeds, and reversed native UV.
        polynomial = {(0,2):.17,(1,1):.05,(2,0):.03}
        a,ma = analytic_face(polynomial,physical=(0.,1.,0.,1.))
        b,mb = analytic_face(polynomial,physical=(1.,2.,0.,1.),native=(2.,8.,-4.,9.),reverse_v=True)
        for t in (0.,.137,.431,.89,1.):
            ua,va = judges._native_uv(ma,1.,t)
            ub,vb = judges._native_uv(mb,1.,t)
            self.assertLess((a.Surface.value(ua,va)-b.Surface.value(ub,vb)).Length,1e-12)
        # Sampling is merely diagnostic; PASS still requires whole seam proof.
        self.assertEqual(continuity([patch((a,ma)),patch((b,mb))])[0],'PASS')


if __name__ == '__main__':
    unittest.main()
