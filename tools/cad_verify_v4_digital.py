"""Source-only fg-4/bg-8 cell topology; never repairs a mask or a candidate.

Raw walks can share a vertex. They are reference boundaries, not certified
geometric output loops. The independent checker does not import this module.
"""
from collections import deque

MAX_CELL_EDGES = 1_000_000
MAX_BOUNDARY_SEGMENTS = 8192


def _labels(mask):
    import numpy as np
    from scipy.ndimage import label
    foreground, count = label(mask, structure=np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]]))
    if not count:
        raise ValueError('contour_empty_mask')
    padded, backgrounds = label(~np.pad(mask, 1), structure=np.ones((3, 3), dtype=int))
    exterior = int(padded[0, 0])
    background = padded[1:-1, 1:-1].copy()
    background[background == exterior] = 0
    return foreground, background, int(count), int(backgrounds - 1)


def _contacts(mask, foreground):
    import numpy as np
    a, b, c, d = mask[:-1, :-1], mask[:-1, 1:], mask[1:, :-1], mask[1:, 1:]
    ambiguous = (a & d & ~b & ~c) | (b & c & ~a & ~d)
    result = []
    for row, column in zip(*np.nonzero(ambiguous)):
        incident = sorted(set(int(v) for v in foreground[row:row+2, column:column+2].ravel() if v))
        result.append(dict(vertex_pixels=[int(column + 1), int(mask.shape[0] - row - 1)],
                           incident_components=incident))
    return sorted(result, key=lambda item: item['vertex_pixels'])


def contacts(mask):
    foreground, _, _, _ = _labels(mask)
    return _contacts(mask, foreground)


def trace(mask, *, allow_multiple=True):
    """Canonical directed-edge walks and an adjacency-derived nesting forest."""
    foreground, background, components, holes = _labels(mask)
    if not allow_multiple and components != 1:
        raise ValueError('contour_multiple_islands_one_solid_refused')
    if 4 * (components + holes) > MAX_BOUNDARY_SEGMENTS:
        raise ValueError('contour_boundary_complexity_limit')
    height, width = mask.shape
    edges, outgoing = {}, {}
    def edge(a, b, fg, bg):
        edges[(a, b)] = (fg, bg)
        outgoing.setdefault(a, []).append(b)
        if len(edges) > MAX_CELL_EDGES:
            raise ValueError('contour_exposed_cell_edge_limit')
    ys, xs = mask.nonzero()
    for row, column in zip(ys.tolist(), xs.tolist()):
        bottom, top = height-row-1, height-row
        owner = int(foreground[row, column])
        if row == 0 or not mask[row-1, column]:
            edge((column+1, top), (column, top), owner,
                 int(background[row-1, column]) if row else 0)
        if column == 0 or not mask[row, column-1]:
            edge((column, top), (column, bottom), owner,
                 int(background[row, column-1]) if column else 0)
        if row == height-1 or not mask[row+1, column]:
            edge((column, bottom), (column+1, bottom), owner,
                 int(background[row+1, column]) if row < height-1 else 0)
        if column == width-1 or not mask[row, column+1]:
            edge((column+1, bottom), (column+1, top), owner,
                 int(background[row, column+1]) if column < width-1 else 0)
    graph, walks = {}, []
    for start in sorted(edges):
        if start not in edges:
            continue
        current, points, owners = start, [], set()
        while True:
            if current not in edges:
                raise ValueError('contour_digital_boundary_pairing_failed')
            owners.add(edges.pop(current))
            a, b = current
            points.append(a)
            dx, dy = b[0]-a[0], b[1]-a[1]
            choices = outgoing.get(b, [])
            if not choices:
                raise ValueError('contour_digital_open_boundary')
            # Foreground stays on the left. At a diagonal ambiguity, the
            # left turn stays with its 4-connected foreground region.
            following = max(choices, key=lambda p: (dx*(p[1]-b[1])-dy*(p[0]-b[0]), p))
            current = (b, following)
            if current == start:
                break
        if len(owners) != 1:
            raise ValueError('contour_digital_mixed_region_walk')
        vertices = []
        for index, point in enumerate(points):
            previous, following = points[index-1], points[(index+1) % len(points)]
            if ((point[0]-previous[0])*(following[1]-point[1]) -
                    (point[1]-previous[1])*(following[0]-point[0])):
                vertices.append(point)
        smallest = min(vertices)
        starts = [i for i, p in enumerate(vertices) if p == smallest]
        beginning = min(starts, key=lambda i: vertices[i:] + vertices[:i])
        vertices = vertices[beginning:] + vertices[:beginning]
        fg, bg = next(iter(owners))
        material, void = ('f', fg), ('b', bg)
        graph.setdefault(material, set()).add(void)
        graph.setdefault(void, set()).add(material)
        walks.append((material, void, vertices))
    parents, pending = {('b', 0): None}, deque([('b', 0)])
    while pending:
        node = pending.popleft()
        for neighbour in sorted(graph.get(node, ())):
            if neighbour not in parents:
                parents[neighbour] = node
                pending.append(neighbour)
            elif parents[node] != neighbour and parents[neighbour] != node:
                raise ValueError('contour_digital_adjacency_not_a_forest')
    if len(parents) != components + holes + 1:
        raise ValueError('contour_digital_region_coverage_failed')
    by_region = {}
    for material, void, vertices in walks:
        if parents.get(material) == void:
            child, role = material, 'outer'
        elif parents.get(void) == material:
            child, role = void, 'hole'
        else:
            raise ValueError('contour_digital_boundary_owner_failed')
        if child in by_region:
            raise ValueError('contour_digital_nonunique_region_boundary')
        area = sum(a[0]*b[1]-a[1]*b[0]
                   for a, b in zip(vertices, vertices[1:] + vertices[:1]))
        if not area or (area > 0) != (role == 'outer'):
            raise ValueError('contour_digital_boundary_orientation_failed')
        by_region[child] = (role, vertices)
    children = {}
    for child in by_region:
        parent = parents[child]
        children.setdefault(parent, []).append(child)
    for siblings in children.values():
        siblings.sort(key=lambda child: by_region[child][1])
    stack, loops, indices = list(reversed(children.get(('b', 0), []))), [], {}
    while stack:
        child = stack.pop()
        role, vertices = by_region[child]
        parent = parents[child]
        loop = dict(role=role, segments=[dict(kind='line', p0=list(a), p1=list(b))
                    for a, b in zip(vertices, vertices[1:] + vertices[:1])])
        if parent != ('b', 0):
            loop['parent'] = indices[parent]
        indices[child] = len(loops)
        loops.append(loop)
        stack.extend(reversed(children.get(child, [])))
    if sum(len(loop['segments']) for loop in loops) > MAX_BOUNDARY_SEGMENTS:
        raise ValueError('contour_boundary_complexity_limit')
    return dict(loops=loops, contacts=_contacts(mask, foreground),
                topology=dict(components=components, holes=holes, euler_characteristic=components-holes))


def mask_region(mask, scale, origin):
    """Exact ORIGINAL cell union; point contacts stay present in this reference."""
    import numpy as np
    from shapely.geometry import box
    from shapely.ops import unary_union
    cells = []
    for row, values in enumerate(mask):
        ends = np.flatnonzero(np.diff(np.concatenate(([False], values, [False]))))
        for start, stop in zip(ends[::2], ends[1::2]):
            cells.append(box(origin[0] + int(start)*scale,
                             origin[1] + (mask.shape[0]-row-1)*scale,
                             origin[0] + int(stop)*scale,
                             origin[1] + (mask.shape[0]-row)*scale))
    return unary_union(cells)
