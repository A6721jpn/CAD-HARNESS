"""Deterministic pixel-boundary approximation; no cutter radius or fillet.

Uniformly resample a traced loop and approximate it with a periodic cubic
least-squares spline, then shared-tangent equal-distance biarcs. Enclose the
FINAL biarc-to-original-cell-boundary distance. Source hard corners retain
their distinct incoming/outgoing tangents and bypass periodic smoothing.
Nothing buffers, bridges, deletes a loop or adjusts geometry to pass min-R.
"""
import bisect
import math

MAX_SEGMENTS = 8192


def _add(a,b): return (a[0]+b[0],a[1]+b[1])
def _sub(a,b): return (a[0]-b[0],a[1]-b[1])
def _mul(a,k): return (a[0]*k,a[1]*k)
def _dot(a,b): return a[0]*b[0]+a[1]*b[1]
def _cross(a,b): return a[0]*b[1]-a[1]*b[0]


def _unit(v):
    length=math.hypot(*v)
    if length==0: raise ValueError('contour_curve_fit_zero_tangent')
    return _mul(v,1/length)


def _arc(a,b,tangent):
    chord=_sub(b,a);length=math.hypot(*chord)
    if length==0: raise ValueError('contour_curve_fit_zero_chord')
    normal=(-tangent[1],tangent[0]);den=2*_dot(normal,chord)
    if abs(den)<=128*math.ulp(max(1.,length)):
        if _dot(chord,tangent)<=0: raise ValueError('contour_curve_fit_reversed_line')
        return (dict(kind='line',p0=list(a),p1=list(b)),None,0.,0.,0.)
    offset=_dot(chord,chord)/den
    center=_add(a,_mul(normal,offset));radius=abs(offset)
    start=math.atan2(a[1]-center[1],a[0]-center[0])
    end=math.atan2(b[1]-center[1],b[0]-center[0])
    sweep=(end-start)%(2*math.pi) if offset>0 else -((start-end)%(2*math.pi))
    middle=start+sweep/2
    p=(center[0]+radius*math.cos(middle),center[1]+radius*math.sin(middle))
    return (dict(kind='arc',p0=list(a),pm=list(p),p1=list(b)),center,radius,start,sweep)


def _reverse(arc):
    segment,center,radius,start,sweep=arc
    result=dict(segment,p0=segment['p1'],p1=segment['p0'])
    return result,center,radius,start+sweep,-sweep


def _biarc(a,b,ta,tb):
    v=_sub(b,a);length2=_dot(v,v)
    along=_dot(v,_add(ta,tb));coefficient=2*(1-max(-1.,min(1.,_dot(ta,tb))))
    denominator=along+math.sqrt(max(0.,along*along+coefficient*length2))
    if denominator<=0: raise ValueError('contour_curve_fit_no_forward_biarc')
    distance=length2/denominator
    middle=_mul(_add(_add(a,b),_mul(_sub(ta,tb),distance)),.5)
    return [_arc(a,middle,ta),_reverse(_arc(b,middle,_mul(tb,-1)))]


def _flatten(arcs,tolerance):
    points=[];error=0.
    for segment,center,radius,start,sweep in arcs:
        if center is None:
            current=[segment['p0'],segment['p1']]
        else:
            angle=2*math.acos(max(-1.,1-min(tolerance/radius,1.)))
            if angle==0: raise ValueError('contour_curve_fit_resolution')
            count=max(1,math.ceil(abs(sweep)/angle))
            if count>1000000: raise ValueError('contour_curve_fit_resource_limit')
            current=[(center[0]+radius*math.cos(start+sweep*i/count),
                      center[1]+radius*math.sin(start+sweep*i/count)) for i in range(count+1)]
            current[0],current[-1]=segment['p0'],segment['p1']
            error=max(error,radius*(1-math.cos(abs(sweep)/count/2)))
        points.extend(current if not points else current[1:])
    return points,error


def _samples(points,step):
    result=[];cover=0.
    for a,b in zip(points,points[1:]):
        length=math.dist(a,b);count=max(1,math.ceil(length/step))
        if len(result)+count>1000000: raise ValueError('contour_curve_fit_resource_limit')
        cover=max(cover,length/count/2)
        result.extend((a[0]+(b[0]-a[0])*i/count,a[1]+(b[1]-a[1])*i/count) for i in range(count))
    result.append(points[-1])
    return result,cover


def _error(source,arcs,limit):
    import numpy as np
    import shapely
    from shapely.geometry import LineString
    output,curve_error=_flatten(arcs,limit/64)
    maximum=cover=0.
    for a,b in ((source,output),(output,source)):
        samples,gap=_samples(a,limit/4)
        distances=shapely.distance(shapely.points(samples),LineString(b))
        maximum=max(maximum,float(np.max(distances)));cover=max(cover,gap)
    magnitude=max(1.,*(abs(v) for p in source+output for v in p))
    return maximum+cover+curve_error+128*math.ulp(magnitude)


def _tangents(points,span,corner_degrees):
    n=len(points);closed=points+[points[0]];distances=[0.]
    for a,b in zip(closed,closed[1:]):distances.append(distances[-1]+math.dist(a,b))
    perimeter=distances[-1];window=min(span,perimeter/8)
    def at(s):
        s%=perimeter;i=min(n-1,bisect.bisect_right(distances,s)-1)
        f=(s-distances[i])/(distances[i+1]-distances[i])
        return _add(closed[i],_mul(_sub(closed[i+1],closed[i]),f))
    incoming=[];outgoing=[];corners=[]
    threshold=math.cos(math.radians(corner_degrees))
    for i,p in enumerate(points):
        back,forward=at(distances[i]-window),at(distances[i]+window)
        before,after=_unit(_sub(p,back)),_unit(_sub(forward,p))
        hard=_dot(before,after)<threshold
        if hard:
            incoming.append(_unit(_sub(p,points[i-1])))
            outgoing.append(_unit(_sub(points[(i+1)%n],p)));corners.append(i)
        else:
            tangent=_unit(_sub(forward,back));incoming.append(tangent);outgoing.append(tangent)
    return incoming,outgoing,corners


def _smooth(points,config,rms):
    """Frozen pixel-space FITPACK fit; RMS is not a manufacturing tolerance."""
    import numpy as np
    from scipy.interpolate import splprep,splev
    closed=np.asarray(points+[points[0]],dtype=float)
    lengths=np.concatenate(([0.],np.cumsum(np.linalg.norm(np.diff(closed,axis=0),axis=1))))
    count=max(8,math.ceil(float(lengths[-1])/config['sample_spacing_pixels']))
    if count>1000000:raise ValueError('contour_curve_fit_resource_limit')
    parameters=np.arange(count+1,dtype=float)/count
    samples=[np.interp(parameters*lengths[-1],lengths,closed[:,axis]) for axis in (0,1)]
    (tck,_),_,status,_=splprep(samples,u=parameters,k=3,per=True,
        s=count*rms**2,full_output=1)
    if status>0:raise ValueError('contour_curve_fit_spline_not_converged')
    xy=splev(parameters[:-1],tck)
    derivative=splev(parameters[:-1],tck,der=1)
    fitted=list(zip(xy[0].tolist(),xy[1].tolist()))
    tangents=[_unit(v) for v in zip(derivative[0].tolist(),derivative[1].tolist())]
    def evaluate(parameter):
        xy=splev(parameter,tck)
        derivative=splev(parameter,tck,der=1)
        return (float(xy[0]),float(xy[1])),_unit((float(derivative[0]),float(derivative[1])))
    return fitted,tangents,evaluate


def _approximate(points,incoming,outgoing,corners,limit,remaining,evaluate=None):
    n=len(points)
    anchors=corners or sorted({int(k*n/4) for k in range(4)})
    if len(anchors)==1:anchors=sorted(set(anchors+[int((anchors[0]+n//2)%n)]))
    anchors=anchors+[anchors[0]+n]
    segments=[];fitted_arcs=[];extra={}
    def sample(index):
        if int(index)==index:
            i=int(index)%n
            return points[i],incoming[i],outgoing[i]
        if index not in extra:
            point,tangent=evaluate(index/n)
            extra[index]=(point,tangent,tangent)
        return extra[index]
    def fit(i,j,depth=0):
        a,_,ta=sample(i);b,tb,_=sample(j)
        path=[a]+[points[k%n] for k in range(math.floor(i)+1,math.ceil(j))]+[b]
        try:
            arcs=_biarc(a,b,ta,tb)
        except ValueError:
            arcs=[]
        accepted=bool(arcs) and _error(path,arcs,limit)<=limit
        if accepted:
            if len(segments)+len(arcs)>remaining:raise ValueError('contour_curve_fit_segment_limit')
            segments.extend(arc[0] for arc in arcs);fitted_arcs.extend(arcs)
        elif depth<32 and (j-i>1 or evaluate is not None):
            middle=math.floor((i+j)/2) if j-i>1 else (i+j)/2
            fit(i,middle,depth+1);fit(middle,j,depth+1)
        else:
            raise ValueError('contour_curve_fit_error_budget_unattainable')
    for a,b in zip(anchors,anchors[1:]):fit(a,b)
    return segments,fitted_arcs


def fit_loops(source,config):
    """First source-error-certified fit, never a radius-driven geometry search."""
    limit=config['maximum_error_pixels'];result=[];total=0
    for loop in source:
        anchor=tuple(loop['segments'][0]['p0'])
        # Integer source-local coordinates make padding irrelevant to FITPACK
        # conditioning, knot decisions and the approximation itself.
        raw=[_sub(segment['p0'],anchor) for segment in loop['segments']]
        incoming,outgoing,corners=_tangents(raw,config['tangent_span_pixels'],config['corner_angle_degrees'])
        passes=1 if corners else config['maximum_fit_passes']
        for attempt in range(passes):
            if corners:
                points=raw;fit_limit=limit;evaluate=None
            else:
                rms=config['smoothing_rms_pixels']/(2**attempt)
                points,incoming,evaluate=_smooth(raw,config,rms);outgoing=incoming
                fit_limit=config['biarc_error_pixels']
            segments,arcs=_approximate(points,incoming,outgoing,corners,fit_limit,MAX_SEGMENTS-total,evaluate)
            if _error(raw+[raw[0]],arcs,limit)<=limit:
                break
        else:
            raise ValueError('contour_curve_fit_source_error_budget_exceeded')
        total+=len(segments)
        segments=[{key:(list(_add(value,anchor)) if key in ('p0','pm','p1') else value)
                   for key,value in segment.items()} for segment in segments]
        start=min(range(len(segments)),key=lambda i:segments[i]['p0'])
        segments=segments[start:]+segments[:start]
        result.append(dict(loop,segments=segments))
    return result
