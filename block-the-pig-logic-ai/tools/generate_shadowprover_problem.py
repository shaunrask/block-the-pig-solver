def generate_problem():
    radius = 4
    cells = []
    adjacencies = []
    escapes = []

    # Generate cells
    for q in range(-radius, radius + 1):
        for r in range(-radius, radius + 1):
            if -radius <= q + r <= radius:
                cells.append((q, r))
                if abs(q) == radius or abs(r) == radius or abs(q + r) == radius:
                    escapes.append((q, r))

    # Generate adjacencies
    directions = [
        (1, 0), (1, -1), (0, -1),
        (-1, 0), (-1, 1), (0, 1)
    ]

    for q, r in cells:
        for dq, dr in directions:
            nq, nr = q + dq, r + dr
            if (nq, nr) in cells:
                adjacencies.append(((q, r), (nq, nr)))

    # Build Assumptions
    assumptions = []
    
    # 1. Adjacency Axioms
    for (q1, r1), (q2, r2) in adjacencies:
        n1 = f"C_{q1}_{r1}".replace("-", "m")
        n2 = f"C_{q2}_{r2}".replace("-", "m")
        assumptions.append(f"(Adjacent {n1} {n2})")

    # 2. Escape Axioms
    for q, r in escapes:
        name = f"C_{q}_{r}".replace("-", "m")
        assumptions.append(f"(Escape {name})")

    # 3. Domain Rules
    # Free definition: (forall (c) (iff (Free c) (and (not (HasWall c)) (not (OccupiedByPig c)))))
    assumptions.append("(forall (c) (iff (Free c) (and (not (HasWall c)) (not (OccupiedByPig c)))))")
    
    # Escape implies Free (if no wall/pig? User said Escape -> Free)
    # But we also have HasWall -> not Escape.
    # Let's use: (forall (c) (if (OccupiedByPig c) (not (HasWall c))))
    assumptions.append("(forall (c) (if (OccupiedByPig c) (not (HasWall c))))")
    
    # (forall (c) (if (HasWall c) (not (Escape c))))
    assumptions.append("(forall (c) (if (HasWall c) (not (Escape c))))")

    # Trapped Definition
    # (iff Trapped (forall (c1) (if (OccupiedByPig c1) (forall (c2) (if (Adjacent c1 c2) (HasWall c2))))))
    assumptions.append("(iff Trapped (forall (c1) (if (OccupiedByPig c1) (forall (c2) (if (Adjacent c1 c2) (HasWall c2))))))")

    # 4. Scenario Assumptions
    # Pig at C_0_0
    assumptions.append("(OccupiedByPig C_0_0)")
    
    # Walls around C_0_0
    neighbors_0_0 = [
        "C_1_0", "C_1_m1", "C_0_m1", "C_m1_0", "C_m1_1", "C_0_1"
    ]
    for n in neighbors_0_0:
        assumptions.append(f"(HasWall {n})")

    # Format Output
    output = []
    output.append("{:name \"Block the Pig Trap Test\"")
    output.append(" :description \"Verifying trapped condition\"")
    output.append(" :assumptions {")
    
    for i, asm in enumerate(assumptions):
        output.append(f"  A{i} {asm}")
        
    output.append(" }")
    output.append(" :goal (forall (x) (if (Adjacent C_0_0 x) (HasWall x)))")
    output.append("}")

    return "\n".join(output)

if __name__ == "__main__":
    with open("shadowprover/test_trap.clj", "w", encoding="utf-8") as f:
        f.write(generate_problem())
