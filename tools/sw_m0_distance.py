"""M0 closed-solid boundary Hausdorff bounds, without changing any v4 judge.

For each direction the ENTIRE boundary must lie in the other solid's offset
shell: inside the dilation and outside the erosion. This uses full BRep boolean
operations, not a point cloud, volume agreement, or minimum-distance PASS.

Scope: valid closed, single-solid BReps whose small arc-join OCCT offsets and
booleans succeed. Bounds include a guard for input and offset approximation
precision. Native offset/boolean correctness is a kernel assumption (as for
v4 native closest-point witnesses); failures are UNVERIFIED, never PASS.
"""
import math


def boundary_distance(a,b,target=.005,refinements=8,*,decision_only=False):
    import FreeCAD as App
    import Part
    result={'status':'UNVERIFIED','maximum_mm':target,'lower_mm':0.,'upper_mm':None,
            'method':'entire_boundary_dual_offset_shell_containment_with_native_tolerance_guard',
            'kernel_assumption':'OCCT arc offsets approximate true parallel solids within requested precision; valid BRep boolean classification',
            'sampling_can_only_supply_FAIL_lower_witnesses':True,'trials':[]}
    for s in (a,b):
        if s.isNull() or not s.isValid() or not s.isClosed() or len(s.Solids)!=1 or s.Volume<=0:
            result['reason']='requires_valid_closed_single_solids';return result
    scale=max(1.,*(abs(v) for s in (a,b) for v in (s.BoundBox.XMin,s.BoundBox.XMax,s.BoundBox.YMin,s.BoundBox.YMax,s.BoundBox.ZMin,s.BoundBox.ZMax)))
    precision=max(float(s.getTolerance(1)) for s in (a,b))+128*math.ulp(scale)
    guard=8*precision
    result.update(native_precision_mm=precision,numerical_guard_mm=guard)
    if not math.isfinite(guard) or guard<=0 or 2*guard>=target:
        result['reason']='native_uncertainty_exhausts_distance_budget';return result
    boundaries=[Part.makeCompound(s.Faces) for s in (a,b)]
    directed_lower=[]
    for source,other in ((a,boundaries[1]),(b,boundaries[0])):
        lower=0.
        # An actual point-to-FULL-boundary distance is only a LOWER witness.
        for vertex in source.Vertexes:
            d=float(Part.Vertex(vertex.Point).distToShape(other)[0])
            if not math.isfinite(d) or d<0:
                result['reason']='native_distance_unavailable';return result
            lower=max(lower,max(0.,d-2*precision))
        directed_lower.append(lower)
    result['directed_lower_mm']=directed_lower
    result['lower_mm']=max(directed_lower)
    if result['lower_mm']>target:
        result['status']='FAIL';result['reason']='actual_boundary_closestpoint_lower_exceeds_target';return result

    def contained(radius):
        row={'radius_mm':radius,'directions':[]}
        try:
            for boundary,other in ((boundaries[0],b),(boundaries[1],a)):
                outer=other.makeOffsetShape(radius,precision,join=0)
                inner=other.makeOffsetShape(-radius,precision,join=0)
                for offset in (outer,inner):
                    if offset.isNull() or not offset.isValid() or not offset.isClosed() or len(offset.Solids)!=1:
                        raise ValueError('offset_not_valid_closed_single_solid')
                outside=boundary.cut(outer)
                deep_inside=boundary.common(inner)
                for remainder in (outside,deep_inside):
                    if not remainder.isNull() and not remainder.isValid():
                        raise ValueError('boundary_boolean_invalid')
                okay=not outside.Faces and not deep_inside.Faces
                row['directions'].append({'contained':okay,'outside_faces':len(outside.Faces),
                    'inside_erosion_faces':len(deep_inside.Faces),'outside_area_mm2':outside.Area,
                    'inside_area_mm2':deep_inside.Area})
            row['contained']=all(v['contained'] for v in row['directions'])
        except (RuntimeError,ValueError,Part.OCCError) as exc:
            row.update(contained=None,error=str(exc))
        result['trials'].append(row)
        return row['contained']

    radius=target-guard
    if contained(radius) is not True:
        result['reason']='no_whole_boundary_upper_certificate_at_target';return result
    upper=radius+guard
    # Refine the enclosure, not the threshold. Failed inclusion is NOT itself a
    # numerical lower proof; only genuine closest-point witnesses set lower_mm.
    lo,hi=0.,radius
    for _ in range(refinements):
        mid=(lo+hi)/2
        if mid<=4*guard:break
        state=contained(mid)
        if state is True:hi=mid;upper=hi+guard
        elif state is False:lo=mid
        else:break
        # Later refinements can tighten this already valid bound, not revoke it.
        # Keep the full numeric enclosure by default; callers needing only the
        # unchanged threshold decision may stop once outward rounding is safe.
        if decision_only and math.nextafter(upper,math.inf)<=target:break
    result.update(status='PASS',upper_mm=math.nextafter(upper,math.inf),
                  reason='both_entire_boundaries_contained_in_guarded_offset_shells')
    # Keep outward rounding inside the admitted target.
    if result['upper_mm']>target:result['status']='UNVERIFIED'
    return result
