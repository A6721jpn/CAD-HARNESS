"""Additional M1 distance: existing offset proof OR existing v4 planar proof.

No geometry is repaired, approximated, cropped, or sampled into a PASS. When
OCCT cannot offset a rib/crease, a complete bijection of actual planar faces may
instead be certified by the unchanged v4 filled-trim boundary-homotopy kernel.
The target remains 0.005mm, including a conservative native-input margin.
"""
import math

from tools.sw_m0_distance import boundary_distance


def whole_distance(a,b,target=.005,refinements=8):
    import Part
    from tools import cad_verify_v4_s3_judges as j
    result=boundary_distance(a,b,target,refinements)
    if result['status']!='UNVERIFIED':return result
    if result.get('reason')!='no_whole_boundary_upper_certificate_at_target':return result
    if not a.Faces or len(a.Faces)!=len(b.Faces):return result
    if any(not isinstance(f.Surface,Part.Plane) for f in list(a.Faces)+list(b.Faces)):return result
    scale=max(1.,*(abs(x) for s in (a,b) for x in j._bounds(s)))
    native=max(float(s.getTolerance(1)) for s in (a,b))+128*math.ulp(scale)
    # Both native boundaries can move within their per-coordinate enclosures.
    margin=2*math.sqrt(3)*native
    budget=target-margin
    if not math.isfinite(budget) or budget<=0:return result
    used=set();bounds=[];cells=0
    resources={'max_depth':16,'max_cells':60000}
    try:
        for face in a.Faces:
            candidates=[]
            for index,other in enumerate(b.Faces):
                if index in used:continue
                if max(abs(x-y) for x,y in zip(j._bounds(face),j._bounds(other)))>target:continue
                try:
                    upper,count=j._planar_trim_identity(face,other,budget,resources)
                except (j.Unknown,j.Changed,RuntimeError,ValueError,Part.OCCError):continue
                candidates.append((index,upper,count))
            if len(candidates)!=1:raise j.Unknown('all_planar_face_bijection_unavailable')
            index,upper,count=candidates[0]
            used.add(index);bounds.append(upper);cells+=count
            if cells>resources['max_cells']:raise j.Unknown('all_planar_resource_bound')
        upper=math.nextafter(max(bounds)+margin,math.inf)
        if len(used)!=len(b.Faces) or upper>target:raise j.Unknown('whole_planar_bound_exhausted')
        return dict(status='PASS',maximum_mm=target,lower_mm=result['lower_mm'],upper_mm=upper,
            method='unchanged_v4_planar_filled_domain_homotopy_all_actual_faces_bijective',
            coverage='both_entire_actual_boundaries_including_hole_trim_loops',
            face_pairs=len(used),cells=cells,native_coordinate_uncertainty_mm=native,
            numerical_margin_mm=margin,original_offset_result=result)
    except (j.Unknown,j.Changed,RuntimeError,ValueError,Part.OCCError) as exc:
        result['planar_alternative_status']='UNVERIFIED'
        # Detailed numeric geometry remains inside the private evidence only.
        result['planar_alternative_error_type']=type(exc).__name__
        return result
