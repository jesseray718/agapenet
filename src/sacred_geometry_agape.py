#!/usr/bin/env python3
"""
sacred_geometry_agape.py - Pure Python, no external dependencies.
Tests Metatron's Cube, Vector Equilibrium, IVM, 64-Tet Grid, Tesseract,
and Truncated Octahedron (honeycomb cell shape).

Run: python3 sacred_geometry_agape.py
"""

import math
import json
from dataclasses import dataclass, field
from typing import List, Dict, Any

# ============================================================
# PURE PYTHON VECTOR MATH
# ============================================================

def vec(x, y, z):
    return [float(x), float(y), float(z)]

def vadd(a, b):
    return [a[0]+b[0], a[1]+b[1], a[2]+b[2]]

def vsub(a, b):
    return [a[0]-b[0], a[1]-b[1], a[2]-b[2]]

def vscale(a, s):
    return [a[0]*s, a[1]*s, a[2]*s]

def vmag(a):
    return math.sqrt(a[0]**2 + a[1]**2 + a[2]**2)

def vnorm(a):
    m = vmag(a)
    if m == 0:
        return [0.0, 0.0, 0.0]
    return [a[0]/m, a[1]/m, a[2]/m]

def vdist(a, b):
    return vmag(vsub(a, b))

# ============================================================
# NODE
# ============================================================

@dataclass
class Node:
    id: str
    pos: List[float]
    connections: List[str] = field(default_factory=list)
    agape_flow: float = 0.0
    energy_state: float = 0.0

# ============================================================
# 1. METATRON'S CUBE (13 Nodes)
# ============================================================

def generate_metatron_cube(radius=1.0):
    nodes = []
    nodes.append(Node(id="center", pos=vec(0, 0, 0)))

    raw_verts = []
    for x in [-1, 1]:
        for y in [-1, 1]:
            raw_verts.append(vec(x, y, 0))
            raw_verts.append(vec(x, 0, y))
            raw_verts.append(vec(0, x, y))

    seen = set()
    idx = 0
    for v in raw_verts:
        vn = vnorm(v)
        vp = vscale(vn, radius)
        key = (round(vp[0], 4), round(vp[1], 4), round(vp[2], 4))
        if key in seen:
            continue
        seen.add(key)
        nodes.append(Node(id=f"meta_{idx}", pos=vp))
        idx += 1

    # Metatron: connect all pairs within 1.5x radius
    for i, n1 in enumerate(nodes):
        for j, n2 in enumerate(nodes):
            if i >= j:
                continue
            d = vdist(n1.pos, n2.pos)
            if d < radius * 1.5:
                n1.connections.append(n2.id)
                n2.connections.append(n1.id)

    return nodes

# ============================================================
# 2. VECTOR EQUILIBRIUM (14 Nodes)
# ============================================================

def generate_vector_equilibrium(radius=1.0):
    nodes = []
    nodes.append(Node(id="ve_center", pos=vec(0, 0, 0)))

    raw_verts = []
    for x in [-1, 1]:
        for y in [-1, 1]:
            raw_verts.append(vec(x, y, 0))
            raw_verts.append(vec(x, 0, y))
            raw_verts.append(vec(0, x, y))

    seen = set()
    idx = 0
    for v in raw_verts:
        vn = vnorm(v)
        vp = vscale(vn, radius)
        key = (round(vp[0], 4), round(vp[1], 4), round(vp[2], 4))
        if key in seen:
            continue
        seen.add(key)
        nodes.append(Node(id=f"ve_{idx}", pos=vp))
        idx += 1

    # VE: connect nodes at exactly radius distance
    for i, n1 in enumerate(nodes):
        for j, n2 in enumerate(nodes):
            if i >= j:
                continue
            d = vdist(n1.pos, n2.pos)
            if abs(d - radius) < 0.01:
                n1.connections.append(n2.id)
                n2.connections.append(n1.id)

    return nodes

# ============================================================
# 3. ISOTROPIC VECTOR MATRIX (IVM)
# ============================================================

def generate_ivm(size=1):
    nodes = []
    r = 1.0

    # FCC lattice points
    coords = []
    for x in range(-size-1, size+2):
        for y in range(-size-1, size+2):
            for z in range(-size-1, size+2):
                if (x + y + z) % 2 == 0:
                    coords.append(vec(x*r, y*r, z*r))

    # Add half-offset points (tetrahedral filling)
    half = [vec(0.5, 0.5, 0), vec(0.5, -0.5, 0), vec(-0.5, 0.5, 0),
            vec(-0.5, -0.5, 0), vec(0.5, 0, 0.5), vec(0.5, 0, -0.5),
            vec(-0.5, 0, 0.5), vec(-0.5, 0, -0.5),
            vec(0, 0.5, 0.5), vec(0, 0.5, -0.5),
            vec(0, -0.5, 0.5), vec(0, -0.5, -0.5)]

    all_pts = []
    for c in coords:
        all_pts.append(c)
        for h in half:
            all_pts.append(vadd(c, h))

    # Deduplicate
    seen = set()
    unique = []
    for p in all_pts:
        key = (round(p[0], 3), round(p[1], 3), round(p[2], 3))
        if key not in seen:
            seen.add(key)
            unique.append(p)

    for i, p in enumerate(unique):
        nodes.append(Node(id=f"ivm_{i}", pos=p))

    # Connect nearest neighbors
    threshold = r * 1.1
    for i, n1 in enumerate(nodes):
        for j, n2 in enumerate(nodes):
            if i >= j:
                continue
            d = vdist(n1.pos, n2.pos)
            if d < threshold and d > 0.01:
                n1.connections.append(n2.id)
                n2.connections.append(n1.id)

    return nodes

# ============================================================
# 4. 64-TETRAHEDRON GRID (SEED)
# ============================================================

def generate_64_tet_grid():
    nodes = []
    # Central node
    nodes.append(Node(id="grid_center", pos=vec(0, 0, 0)))

    # 8 cube vertices at (+-1, +-1, +-1)
    # These form the outer boundary of the first VE expansion
    for x in [-1, 1]:
        for y in [-1, 1]:
            for z in [-1, 1]:
                nodes.append(Node(id=f"tet_{x}{y}{z}", pos=vec(x, y, z)))

    # 12 cuboctahedron vertices (mid-edge points)
    cubo = []
    for a in [-1, 1]:
        for b in [-1, 1]:
            cubo.append(vec(a, b, 0))
            cubo.append(vec(a, 0, b))
            cubo.append(vec(0, a, b))

    seen = set()
    cidx = 0
    for v in cubo:
        key = (round(v[0], 3), round(v[1], 3), round(v[2], 3))
        if key in seen:
            continue
        seen.add(key)
        nodes.append(Node(id=f"cubo_{cidx}", pos=v))
        cidx += 1

    # Connect center to all
    center = nodes[0]
    for n in nodes[1:]:
        center.connections.append(n.id)
        n.connections.append(center.id)

    # Connect adjacent outer nodes
    for i, n1 in enumerate(nodes):
        if i == 0:
            continue
        for j, n2 in enumerate(nodes):
            if j <= i:
                continue
            d = vdist(n1.pos, n2.pos)
            if d < 1.5 and d > 0.01:
                n1.connections.append(n2.id)
                n2.connections.append(n1.id)

    return nodes

# ============================================================
# 5. 4D HYPERCUBE (TESSERACT) PROJECTION
# ============================================================

def generate_tesseract():
    nodes = []
    w_dist = 3.0  # Perspective distance for 4D to 3D projection

    coords_4d = []
    for x in [-1, 1]:
        for y in [-1, 1]:
            for z in [-1, 1]:
                for w4 in [-1, 1]:
                    factor = 1.0 / (w_dist - w4 / w_dist)
                    p3 = vec(x * factor, y * factor, z * factor)
                    nodes.append(Node(id=f"tess_{x}{y}{z}{w4}", pos=p3))
                    coords_4d.append([x, y, z, w4])

    # Connect nodes that differ in exactly one 4D coordinate
    for i in range(len(coords_4d)):
        for j in range(i + 1, len(coords_4d)):
            diff = sum(1 for a, b in zip(coords_4d[i], coords_4d[j]) if a != b)
            if diff == 1:
                nodes[i].connections.append(nodes[j].id)
                nodes[j].connections.append(nodes[i].id)

    return nodes

# ============================================================
# 6. TRUNCATED OCTAHEDRON (Honeycomb Cell Shape)
# Tessellates perfectly in 3D - fills all space
# ============================================================

def generate_truncated_octahedron(scale=1.0):
    nodes = []
    # 24 vertices of truncated octahedron
    # All permutations of (0, +-1, +-2) with even sign count
    raw = []
    signs = [-2, -1, 0, 1, 2]
    for a in [0]:
        for b in [-1, 1]:
            for c in [-2, 2]:
                raw.append(vec(a, b, c))
                raw.append(vec(a, c, b))
                raw.append(vec(b, a, c))
                raw.append(vec(b, c, a))
                raw.append(vec(c, a, b))
                raw.append(vec(c, b, a))

    # Also permutations of (+-1, +-1, +-1) are NOT part of trunc oct
    # Correct verts: all permutations of (0, +-1, +-2)
    # Let's be precise: 24 vertices from permutations of (0, +-1, +-2)
    perms = []
    base = [0, 1, 2]
    import itertools
    for perm in itertools.permutations(base):
        for s1 in [-1, 1]:
            for s2 in [-1, 1]:
                v = [0, 0, 0]
                v[perm[0]] = 0
                v[perm[1]] = s1 * 1
                v[perm[2]] = s2 * 2
                perms.append(vec(v[0], v[1], v[2]))

    seen = set()
    idx = 0
    for p in perms:
        key = (round(p[0], 4), round(p[1], 4), round(p[2], 4))
        if key in seen:
            continue
        seen.add(key)
        sp = vscale(p, scale * 0.5)
        nodes.append(Node(id=f"to_{idx}", pos=sp))
        idx += 1

    # Connect adjacent vertices (edge length = sqrt(2) * scale * 0.5)
    edge_len = math.sqrt(2) * scale * 0.5
    for i, n1 in enumerate(nodes):
        for j, n2 in enumerate(nodes):
            if i >= j:
                continue
            d = vdist(n1.pos, n2.pos)
            if abs(d - edge_len) < 0.05:
                n1.connections.append(n2.id)
                n2.connections.append(n1.id)

    return nodes

# ============================================================
# AGAPE FLOW SIMULATION
# ============================================================

def simulate_agape_flow(structure_name, nodes):
    print(f"\n--- {structure_name} ---")

    # Reset all flows
    for n in nodes:
        n.agape_flow = 0.0

    # Find center node
    center = nodes[0]
    for n in nodes:
        if "center" in n.id or "ve_center" in n.id or "grid_center" in n.id:
            center = n
            break

    center.agape_flow = 100.0

    # BFS propagation
    queue = [center]
    visited = {center.id}

    for iteration in range(15):
        next_queue = []
        for current in queue:
            if not current.connections:
                continue
            flow_share = current.agape_flow / len(current.connections)
            for nid in current.connections:
                neighbor = next((n for n in nodes if n.id == nid), None)
                if neighbor and neighbor.id not in visited:
                    neighbor.agape_flow += flow_share
                    visited.add(neighbor.id)
                    next_queue.append(neighbor)
        queue = next_queue
        if not queue:
            break

    # Analyze
    flows = [n.agape_flow for n in nodes if n.agape_flow > 0]
    total_connections = sum(len(n.connections) for n in nodes) // 2
    avg_flow = sum(flows) / len(flows) if flows else 0
    variance = sum((f - avg_flow)**2 for f in flows) / len(flows) if flows else 0
    std_dev = math.sqrt(variance)
    max_flow = max(flows) if flows else 0
    min_flow = min(flows) if flows else 0

    equilibrium = "PERFECT" if variance < 1.0 else ("HIGH" if variance < 50 else "MUTATION")

    print(f"  Nodes: {len(nodes)}")
    print(f"  Connections: {total_connections}")
    print(f"  Avg Flow: {avg_flow:.2f}")
    print(f"  Min/Max: {min_flow:.2f} / {max_flow:.2f}")
    print(f"  Std Dev: {std_dev:.2f}")
    print(f"  Variance: {variance:.2f}")
    print(f"  Status: {equilibrium}")

    return {
        "structure": structure_name,
        "nodes": len(nodes),
        "connections": total_connections,
        "avg_flow": round(avg_flow, 4),
        "variance": round(variance, 4),
        "std_dev": round(std_dev, 4),
        "min_flow": round(min_flow, 4),
        "max_flow": round(max_flow, 4),
        "equilibrium": equilibrium
    }

# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 60)
    print("SACRED GEOMETRY AGAPE ENGINE")
    print("Metatron | VE | IVM | 64-Grid | Tesseract | Truncated Octahedron")
    print("=" * 60)

    results = []

    # 1. Metatron's Cube
    metatron = generate_metatron_cube()
    results.append(simulate_agape_flow("Metatron's Cube (Mutation)", metatron))

    # 2. Vector Equilibrium
    ve = generate_vector_equilibrium()
    results.append(simulate_agape_flow("Vector Equilibrium (Balance)", ve))

    # 3. Isotropic Vector Matrix
    ivm = generate_ivm(size=1)
    results.append(simulate_agape_flow("Isotropic Vector Matrix", ivm))

    # 4. 64-Tetrahedron Grid
    grid64 = generate_64_tet_grid()
    results.append(simulate_agape_flow("64-Tetrahedron Grid Seed", grid64))

    # 5. Tesseract
    tess = generate_tesseract()
    results.append(simulate_agape_flow("Tesseract (4D Projection)", tess))

    # 6. Truncated Octahedron (Honeycomb)
    toct = generate_truncated_octahedron()
    results.append(simulate_agape_flow("Truncated Octahedron (Honeycomb)", toct))

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY: GEOMETRIC EFFICIENCY COMPARISON")
    print("=" * 70)
    print(f"{'Structure':<35} {'Nodes':>6} {'Conns':>6} {'Var':>8} {'Status':<15}")
    print("-" * 70)
    for r in results:
        print(f"{r['structure']:<35} {r['nodes']:>6} {r['connections']:>6} {r['variance']:>8.2f} {r['equilibrium']:<15}")

    # Save results
    with open("sacred_geometry_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print("\nResults saved to: sacred_geometry_results.json")

if __name__ == "__main__":
    main()
