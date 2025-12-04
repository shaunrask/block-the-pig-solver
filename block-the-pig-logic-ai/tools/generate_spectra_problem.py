def generate_spectra_problem():
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

    # Build Background (Axioms)
    background = []
    
    # 1. Adjacency Axioms
    for (q1, r1), (q2, r2) in adjacencies:
        n1 = f"C_{q1}_{r1}".replace("-", "m")
        n2 = f"C_{q2}_{r2}".replace("-", "m")
        background.append(f"(Adjacent {n1} {n2})")

    # 2. Escape Axioms
    for q, r in escapes:
        name = f"C_{q}_{r}".replace("-", "m")
        background.append(f"(Escape {name})")

    # 3. Domain Rules
    # Free definition REMOVED (using fluent)
    # background.append("(forall (c) (iff (Free c) (and (not (HasWall c)) (not (OccupiedByPig c)))))")
    
    # Constraints (as axioms)
    background.append("(forall (c) (if (OccupiedByPig c) (not (HasWall c))))")
    background.append("(forall (c) (if (HasWall c) (not (Escape c))))")

    # Trapped Definition
    background.append("(iff Trapped (forall (c1) (if (OccupiedByPig c1) (forall (c2) (if (Adjacent c1 c2) (HasWall c2))))))")

    # Build Actions
    actions = []
    
    # PlaceWall
    actions.append("""
        (define-action PlaceWall [?c] {
            :preconditions [(Free ?c)]
            :additions [(HasWall ?c)]
            :deletions [(Free ?c)]
        })
    """)
    
    # PigMove
    actions.append("""
        (define-action PigMove [?a ?b] {
            :preconditions [(OccupiedByPig ?a) (Adjacent ?a ?b) (Free ?b)]
            :additions [(OccupiedByPig ?b) (Free ?a)]
            :deletions [(OccupiedByPig ?a) (Free ?b)]
        })
    """)

    # Build Start
    start = []
    start.append("(OccupiedByPig C_0_0)")
    # Add Free for all other cells
    for c in cells:
        if c != (0, 0):
            name = f"C_{c[0]}_{c[1]}".replace("-", "m")
            start.append(f"(Free {name})")

    # Build Goal
    goal = []
    # goal.append("(Trapped)")
    goal.append("(HasWall C_0_1)") # Simple goal

    # Format Output
    output = []
    output.append("{:name \"Block the Pig Planning\"")
    output.append(" :background [")
    for b in background:
        output.append(f"    {b}")
    output.append(" ]")
    
    output.append(" :actions [")
    for a in actions:
        output.append(a)
    output.append(" ]")
    
    output.append(" :start [")
    for s in start:
        output.append(f"    {s}")
    output.append(" ]")
    
    output.append(" :goal [")
    for g in goal:
        output.append(f"    {g}")
    output.append(" ]")
    output.append("}")

    return "\n".join(output)

if __name__ == "__main__":
    with open("spectra/block_the_pig.clj", "w", encoding="utf-8") as f:
        f.write(generate_spectra_problem())
