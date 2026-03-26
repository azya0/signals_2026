from __future__ import annotations

from dataclasses import dataclass


Vector = tuple[int, ...]
Edge = tuple[Vector, int, Vector]


CHECK_MATRIX: list[list[int]] = [
    [1, 0, 1, 1, 0, 1],
    [1, 0, 1, 0, 1, 0],
    [1, 1, 0, 1, 0, 0],
]


@dataclass(frozen=True)
class Trellis:
    layers: list[list[Vector]]
    edges:  list[list[Edge]]


def xor_vectors(a: Vector, b: Vector) -> Vector:
    return tuple(x ^ y for x, y in zip(a, b))


def zero_vector(size: int) -> Vector:
    return tuple(0 for _ in range(size))


def columns_of(matrix: list[list[int]]) -> list[Vector]:
    rows = len(matrix)
    cols = len(matrix[0])
    return [tuple(matrix[r][c] for r in range(rows)) for c in range(cols)]


def span(vectors: list[Vector], size: int) -> set[Vector]:
    result: set[Vector] = {zero_vector(size)}
    for vector in vectors:
        result |= {xor_vectors(state, vector) for state in result}
    return result


def build_parity_check_trellis(matrix: list[list[int]]) -> Trellis:
    cols = columns_of(matrix)
    m = len(matrix)
    n = len(cols)

    prefix_spans = [span(cols[:i], m) for i in range(n + 1)]
    suffix_spans = [span(cols[i:], m) for i in range(n + 1)]
    layers = [sorted(prefix_spans[i] & suffix_spans[i]) for i in range(n + 1)]

    edges: list[list[Edge]] = []
    for i, column in enumerate(cols):
        current_edges: list[Edge] = []
        next_layer = set(layers[i + 1])
        for state in layers[i]:
            for bit in (0, 1):
                target = state if bit == 0 else xor_vectors(state, column)
                if target in next_layer:
                    current_edges.append((state, bit, target))
        edges.append(sorted(current_edges))

    return Trellis(layers=layers, edges=edges)


def build_syndrome_trellis(matrix: list[list[int]]) -> Trellis:
    cols = columns_of(matrix)
    m = len(matrix)
    n = len(cols)
    zero = zero_vector(m)

    forward: list[set[Vector]] = [{zero}]
    for column in cols:
        next_states: set[Vector] = set()
        for state in forward[-1]:
            next_states.add(state)
            next_states.add(xor_vectors(state, column))
        forward.append(next_states)

    backward: list[set[Vector]] = [set() for _ in range(n + 1)]
    backward[n] = {zero}
    for i in range(n - 1, -1, -1):
        column = cols[i]
        current_states: set[Vector] = set()
        for target in backward[i + 1]:
            current_states.add(target)
            current_states.add(xor_vectors(target, column))
        backward[i] = current_states

    layers = [sorted(forward[i] & backward[i]) for i in range(n + 1)]

    edges: list[list[Edge]] = []
    for i, column in enumerate(cols):
        current_edges: list[Edge] = []
        next_layer = set(layers[i + 1])
        for state in layers[i]:
            for bit in (0, 1):
                target = state if bit == 0 else xor_vectors(state, column)
                if target in next_layer:
                    current_edges.append((state, bit, target))
        edges.append(sorted(current_edges))

    return Trellis(layers=layers, edges=edges)


def vector_to_str(vector: Vector) -> str:
    return "".join(str(bit) for bit in vector)


def print_trellis(title: str, trellis: Trellis) -> None:
    print(title)
    print("-" * len(title))

    for i, layer in enumerate(trellis.layers):
        labels = [f"{index}:{vector_to_str(state)}" for index, state in enumerate(layer)]
        print(f"Ярус {i}: " + ", ".join(labels))

    print()
    for i, edges in enumerate(trellis.edges, start=1):
        state_to_index: dict[Vector, int] = {
            state: index for index, state in enumerate(trellis.layers[i - 1])
        }
        next_to_index: dict[Vector, int] = {
            state: index for index, state in enumerate(trellis.layers[i])
        }
        print(f"Переходы по символу x_{i}:")
        for source, bit, target in edges:
            source_label = f"v{i - 1}_{state_to_index[source]}"
            target_label = f"v{i}_{next_to_index[target]}"
            print(
                f"  {source_label} ({vector_to_str(source)})"
                f" --{bit}--> {target_label} ({vector_to_str(target)})"
            )
        print()


def trellises_match(left: Trellis, right: Trellis) -> bool:
    return left.layers == right.layers and left.edges == right.edges


def main() -> None:
    parity_trellis = build_parity_check_trellis(CHECK_MATRIX)
    syndrome_trellis = build_syndrome_trellis(CHECK_MATRIX)

    print("Проверочная матрица H (в условии она обозначена буквой G):")
    for row in CHECK_MATRIX:
        print("  " + " ".join(str(bit) for bit in row))
    print()

    print_trellis("Решетка по проверочной матрице", parity_trellis)
    print_trellis("Синдромная решетка", syndrome_trellis)

    print(f"Совпадение слоев и переходов: {trellises_match(parity_trellis, syndrome_trellis)}")


if __name__ == "__main__":
    main()
