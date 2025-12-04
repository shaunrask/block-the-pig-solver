def generate_hex_grid(radius):
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

    # Format output
    output = []
    output.append(";; Generated Hex Grid Radius " + str(radius))
    output.append("")
    
    # Constants
    for q, r in cells:
        name = f"C_{q}_{r}".replace("-", "m")
        output.append(f"const {name}:Cell.")

    output.append("")
    
    # Adjacencies
    for (q1, r1), (q2, r2) in adjacencies:
        n1 = f"C_{q1}_{r1}".replace("-", "m")
        n2 = f"C_{q2}_{r2}".replace("-", "m")
        output.append(f"axiom Adjacent({n1}, {n2}).")

    output.append("")

    # Escapes
    for q, r in escapes:
        name = f"C_{q}_{r}".replace("-", "m")
        output.append(f"axiom Escape({name}).")

    with open("shadowprover/hexgrid.sp", "w", encoding="utf-8") as f:
        f.write("\n".join(output))

if __name__ == "__main__":
    generate_hex_grid(4)
