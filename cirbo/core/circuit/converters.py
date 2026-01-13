import typing as tp
import uuid

from cirbo.core.circuit import gate

if tp.TYPE_CHECKING:
    from cirbo.core.circuit.circuit import Circuit

__all__ = ['convert_gate', 'convert_gate_to_aig']


def convert_gate(_gate: gate.Gate, circuit: 'Circuit') -> None:
    """
    Convert gate in the circuit to bench format.

    If the corresponding conversion function is not specified for a given gate type, we
    assume that the gate is already in bench format.

    (!!!) Conversion ALWAYS_TRUE and ALWAYS_FALSE requires the presence of at least one
    input in the circuit. Since it is with the use of this input these type of gates
    will be replaced with subcircuit.

    """
    if _gate.gate_type in _convertors:
        _convertors[_gate.gate_type](_gate, circuit)


def _convert_lt(_gate: gate.Gate, circuit: 'Circuit') -> None:
    """Convert LT(x, y) to AND(NOT(x), y)."""
    new_gate_label = 'new_gate_LT_for_' + _gate.label + uuid.uuid4().hex
    circuit.emplace_gate(new_gate_label, gate.NOT, (_gate.operands[0],))

    circuit._remove_user(_gate.operands[0], _gate.label)
    circuit._add_user(new_gate_label, _gate.label)

    circuit._gates[_gate.label] = gate.Gate(
        _gate.label, gate.AND, (new_gate_label, _gate.operands[1])
    )

    _add_new_gate_to_blocks(_gate.label, new_gate_label, circuit)


def _convert_leq(_gate: gate.Gate, circuit: 'Circuit') -> None:
    """Convert LEQ(x, y) to OR(NOT(x), y)."""
    new_gate_label = 'new_gate_LEQ_for_' + _gate.label + uuid.uuid4().hex
    circuit.emplace_gate(new_gate_label, gate.NOT, (_gate.operands[0],))

    circuit._remove_user(_gate.operands[0], _gate.label)
    circuit._add_user(new_gate_label, _gate.label)

    circuit._gates[_gate.label] = gate.Gate(
        _gate.label, gate.OR, (new_gate_label, _gate.operands[1])
    )

    _add_new_gate_to_blocks(_gate.label, new_gate_label, circuit)


def _convert_gt(_gate: gate.Gate, circuit: 'Circuit') -> None:
    """Convert GT(x, y) to AND(x, NOT(y))."""
    new_gate_label = 'new_gate_GT_for_' + _gate.label + uuid.uuid4().hex
    circuit.emplace_gate(new_gate_label, gate.NOT, (_gate.operands[1],))

    circuit._remove_user(_gate.operands[1], _gate.label)
    circuit._add_user(new_gate_label, _gate.label)

    circuit._gates[_gate.label] = gate.Gate(
        _gate.label, gate.AND, (_gate.operands[0], new_gate_label)
    )

    _add_new_gate_to_blocks(_gate.label, new_gate_label, circuit)


def _convert_geq(_gate: gate.Gate, circuit: 'Circuit') -> None:
    """Convert GEQ(x, y) to OR(x, NOT(y))."""
    new_gate_label = 'new_gate_GEQ_for_' + _gate.label + uuid.uuid4().hex
    circuit.emplace_gate(new_gate_label, gate.NOT, (_gate.operands[1],))

    circuit._remove_user(_gate.operands[1], _gate.label)
    circuit._add_user(new_gate_label, _gate.label)

    circuit._gates[_gate.label] = gate.Gate(
        _gate.label, gate.OR, (_gate.operands[0], new_gate_label)
    )

    _add_new_gate_to_blocks(_gate.label, new_gate_label, circuit)


def _convert_liff(_gate: gate.Gate, circuit: 'Circuit') -> None:
    """Convert LIFF(x, y) to IFF(x)"""
    circuit._remove_user(_gate.operands[1], _gate.label)
    circuit._gates[_gate.label] = gate.Gate(_gate.label, gate.IFF, (_gate.operands[0],))


def _convert_riff(_gate: gate.Gate, circuit: 'Circuit') -> None:
    """Convert RIFF(x, y) to IFF(y)"""
    circuit._remove_user(_gate.operands[0], _gate.label)
    circuit._gates[_gate.label] = gate.Gate(_gate.label, gate.IFF, (_gate.operands[1],))


def _convert_lnot(_gate: gate.Gate, circuit: 'Circuit') -> None:
    """Convert LNOT(x, y) to NOT(x)"""
    circuit._remove_user(_gate.operands[1], _gate.label)
    circuit._gates[_gate.label] = gate.Gate(_gate.label, gate.NOT, (_gate.operands[0],))


def _convert_rnot(_gate: gate.Gate, circuit: 'Circuit') -> None:
    """Convert RNOT(x, y) to NOT(y)"""
    circuit._remove_user(_gate.operands[0], _gate.label)
    circuit._gates[_gate.label] = gate.Gate(_gate.label, gate.NOT, (_gate.operands[1],))


def _convert_always_true(_gate: gate.Gate, circuit: 'Circuit') -> None:
    """
    Convert ALWAYS_TRUE to OR(x, NOT(x)), where x is the first inputs in circuit.

    If the circuit hasn't any inputs the algorithm raises.

    """
    first_input = circuit.input_at_index(0)

    new_gate_label = 'new_gate_ALWAYS_TRUE_for_' + _gate.label + uuid.uuid4().hex
    circuit.emplace_gate(new_gate_label, gate.NOT, (first_input,))

    circuit._add_user(first_input, _gate.label)
    circuit._add_user(new_gate_label, _gate.label)

    circuit._gates[_gate.label] = gate.Gate(
        _gate.label, gate.OR, (first_input, new_gate_label)
    )

    _add_new_gate_to_blocks(_gate.label, new_gate_label, circuit)


def _convert_always_false(_gate: gate.Gate, circuit: 'Circuit') -> None:
    """
    Convert ALWAYS_FALSE to AND(x, NOT(x)), where x is the first inputs in circuit.

    If the circuit hasn't any inputs the algorithm raises.

    """
    first_input = circuit.input_at_index(0)

    new_gate_label = 'new_gate_ALWAYS_FALSE_for_' + _gate.label + uuid.uuid4().hex
    circuit.emplace_gate(new_gate_label, gate.NOT, (first_input,))

    circuit._add_user(first_input, _gate.label)
    circuit._add_user(new_gate_label, _gate.label)

    circuit._gates[_gate.label] = gate.Gate(
        _gate.label, gate.AND, (first_input, new_gate_label)
    )

    _add_new_gate_to_blocks(_gate.label, new_gate_label, circuit)


_convertors: dict[gate.GateType, tp.Callable[[gate.Gate, 'Circuit'], None]] = {
    gate.LT: _convert_lt,
    gate.LEQ: _convert_leq,
    gate.GT: _convert_gt,
    gate.GEQ: _convert_geq,
    gate.LIFF: _convert_liff,
    gate.RIFF: _convert_riff,
    gate.LNOT: _convert_lnot,
    gate.RNOT: _convert_rnot,
    gate.ALWAYS_TRUE: _convert_always_true,
    gate.ALWAYS_FALSE: _convert_always_false,
}


def _add_new_gate_to_blocks(
    old_gate_label: gate.Label, new_gate_label: gate.Label, circuit: 'Circuit'
):
    """Add new gate to circuit's blocks, if their gates has old_gate_label."""
    for block in circuit.blocks.values():
        if old_gate_label in block.gates:
            block._gates.append(new_gate_label)


def _add_new_gates_to_blocks(
    old_gate_label: gate.Label, new_gate_labels: list[gate.Label], circuit: 'Circuit'
):
    """Add new gates to circuit's blocks, if their gates has old_gate_label."""
    for block in circuit.blocks.values():
        if old_gate_label in block.gates:
            block._gates.extend(new_gate_labels)


# =============================================================================
# AIG Conversion Functions
# =============================================================================


def convert_gate_to_aig(_gate: gate.Gate, circuit: 'Circuit') -> None:
    """
    Convert gate in the circuit to AIG format (AND, NOT, INPUT, ALWAYS_TRUE, ALWAYS_FALSE).

    If the corresponding conversion function is not specified for a given gate type, we
    assume that the gate is already in AIG format.

    """
    if _gate.gate_type in _aig_convertors:
        _aig_convertors[_gate.gate_type](_gate, circuit)


def _convert_or_to_aig(_gate: gate.Gate, circuit: 'Circuit') -> None:
    """
    Convert OR(a, b, ...) to AIG: NOT(AND(NOT(a), NOT(b), ...)).

    For n operands, creates n NOT gates, then a tree of AND gates, then final NOT.
    Uses De Morgan's law: OR(a, b, c, ...) = NOT(AND(NOT(a), NOT(b), NOT(c), ...))

    """
    operands = _gate.operands
    uid = uuid.uuid4().hex
    new_gates: list[str] = []

    # Create NOT gate for each operand
    not_labels: list[str] = []
    for i, op in enumerate(operands):
        not_label = f'aig_or_n{i}_{_gate.label}_{uid}'
        circuit.emplace_gate(not_label, gate.NOT, (op,))
        not_labels.append(not_label)
        new_gates.append(not_label)
        circuit._remove_user(op, _gate.label)

    # Build AND tree from the NOT outputs
    current_labels = not_labels
    and_idx = 0
    while len(current_labels) > 1:
        next_labels: list[str] = []
        for i in range(0, len(current_labels), 2):
            if i + 1 < len(current_labels):
                and_label = f'aig_or_and{and_idx}_{_gate.label}_{uid}'
                circuit.emplace_gate(and_label, gate.AND, (current_labels[i], current_labels[i + 1]))
                next_labels.append(and_label)
                new_gates.append(and_label)
                and_idx += 1
            else:
                next_labels.append(current_labels[i])
        current_labels = next_labels

    # The final AND result
    final_and_label = current_labels[0]
    circuit._add_user(final_and_label, _gate.label)

    # Replace gate with NOT(final_and)
    circuit._gates[_gate.label] = gate.Gate(_gate.label, gate.NOT, (final_and_label,))

    _add_new_gates_to_blocks(_gate.label, new_gates, circuit)


def _convert_nand_to_aig(_gate: gate.Gate, circuit: 'Circuit') -> None:
    """
    Convert NAND(a, b, ...) to AIG: NOT(AND(a, b, ...)).

    For n operands, builds an AND tree, then NOT.

    """
    operands = _gate.operands
    uid = uuid.uuid4().hex
    new_gates: list[str] = []

    # Remove user tracking for all operands
    for op in operands:
        circuit._remove_user(op, _gate.label)

    # Build AND tree from operands
    current_labels = list(operands)
    and_idx = 0
    while len(current_labels) > 1:
        next_labels: list[str] = []
        for i in range(0, len(current_labels), 2):
            if i + 1 < len(current_labels):
                and_label = f'aig_nand_and{and_idx}_{_gate.label}_{uid}'
                circuit.emplace_gate(and_label, gate.AND, (current_labels[i], current_labels[i + 1]))
                next_labels.append(and_label)
                new_gates.append(and_label)
                and_idx += 1
            else:
                next_labels.append(current_labels[i])
        current_labels = next_labels

    # The final AND result
    final_and_label = current_labels[0]

    # If we had more than one operand, we created AND gates
    # Otherwise final_and_label is the single operand itself
    if new_gates:
        circuit._add_user(final_and_label, _gate.label)
    else:
        # Single operand case: NAND(a) = NOT(a)
        pass

    # Replace gate with NOT(final_and)
    circuit._gates[_gate.label] = gate.Gate(_gate.label, gate.NOT, (final_and_label,))

    _add_new_gates_to_blocks(_gate.label, new_gates, circuit)


def _convert_nor_to_aig(_gate: gate.Gate, circuit: 'Circuit') -> None:
    """
    Convert NOR(a, b, ...) to AIG: AND(NOT(a), NOT(b), ...).

    For n operands, creates n NOT gates, then builds an AND tree.
    NOR(a, b, c, ...) = NOT(OR(a, b, c, ...)) = AND(NOT(a), NOT(b), NOT(c), ...)

    """
    operands = _gate.operands
    uid = uuid.uuid4().hex
    new_gates: list[str] = []

    # Remove user tracking for all original operands
    for op in operands:
        circuit._remove_user(op, _gate.label)

    # Create NOT gate for each operand
    not_labels: list[str] = []
    for i, op in enumerate(operands):
        not_label = f'aig_nor_n{i}_{_gate.label}_{uid}'
        circuit.emplace_gate(not_label, gate.NOT, (op,))
        not_labels.append(not_label)
        new_gates.append(not_label)

    # Build AND tree from the NOT outputs
    current_labels = not_labels
    and_idx = 0
    while len(current_labels) > 1:
        next_labels: list[str] = []
        for i in range(0, len(current_labels), 2):
            if i + 1 < len(current_labels):
                and_label = f'aig_nor_and{and_idx}_{_gate.label}_{uid}'
                circuit.emplace_gate(and_label, gate.AND, (current_labels[i], current_labels[i + 1]))
                next_labels.append(and_label)
                new_gates.append(and_label)
                and_idx += 1
            else:
                next_labels.append(current_labels[i])
        current_labels = next_labels

    # The final result
    final_label = current_labels[0]
    circuit._add_user(final_label, _gate.label)

    # Replace gate - either with the final AND, or with NOT if single operand
    if len(operands) == 1:
        # NOR(a) = NOT(a)
        circuit._gates[_gate.label] = gate.Gate(_gate.label, gate.NOT, (final_label,))
    else:
        # Replace with AND pointing to final_label (identity transformation)
        # Actually we need to point to final_label properly
        # Since final_label is an AND gate we created, we can just reuse its operands
        final_gate = circuit.get_gate(final_label)
        circuit._gates[_gate.label] = gate.Gate(_gate.label, gate.AND, final_gate.operands)
        # Remove the now-redundant final AND gate
        circuit._gates.pop(final_label)
        new_gates.remove(final_label)
        # Update user tracking for the operands of the removed gate
        for op in final_gate.operands:
            circuit._remove_user(op, final_label)
            circuit._add_user(op, _gate.label)

    _add_new_gates_to_blocks(_gate.label, new_gates, circuit)


def _convert_xor_to_aig(_gate: gate.Gate, circuit: 'Circuit') -> None:
    """
    Convert XOR(a, b) to AIG: AND(NOT(AND(NOT(a), NOT(b))), NOT(AND(a, b))).

    This is XOR = AND(OR(a,b), NAND(a,b)) expanded to pure AIG.
    Creates: t1=AND(a,b), n1=NOT(t1), na=NOT(a), nb=NOT(b), t2=AND(na,nb), n2=NOT(t2),
             result=AND(n2,n1)

    """
    a, b = _gate.operands
    uid = uuid.uuid4().hex

    t1_label = f'aig_xor_t1_{_gate.label}_{uid}'
    n1_label = f'aig_xor_n1_{_gate.label}_{uid}'
    na_label = f'aig_xor_na_{_gate.label}_{uid}'
    nb_label = f'aig_xor_nb_{_gate.label}_{uid}'
    t2_label = f'aig_xor_t2_{_gate.label}_{uid}'
    n2_label = f'aig_xor_n2_{_gate.label}_{uid}'

    # t1 = AND(a, b)
    circuit.emplace_gate(t1_label, gate.AND, (a, b))
    # n1 = NOT(t1) -> NAND(a, b)
    circuit.emplace_gate(n1_label, gate.NOT, (t1_label,))
    # na = NOT(a)
    circuit.emplace_gate(na_label, gate.NOT, (a,))
    # nb = NOT(b)
    circuit.emplace_gate(nb_label, gate.NOT, (b,))
    # t2 = AND(na, nb) -> NOR(a, b)
    circuit.emplace_gate(t2_label, gate.AND, (na_label, nb_label))
    # n2 = NOT(t2) -> OR(a, b)
    circuit.emplace_gate(n2_label, gate.NOT, (t2_label,))

    # Update user tracking
    circuit._remove_user(a, _gate.label)
    circuit._remove_user(b, _gate.label)
    circuit._add_user(n2_label, _gate.label)
    circuit._add_user(n1_label, _gate.label)

    # result = AND(n2, n1) = AND(OR(a,b), NAND(a,b))
    circuit._gates[_gate.label] = gate.Gate(_gate.label, gate.AND, (n2_label, n1_label))

    _add_new_gates_to_blocks(
        _gate.label,
        [t1_label, n1_label, na_label, nb_label, t2_label, n2_label],
        circuit,
    )


def _convert_nxor_to_aig(_gate: gate.Gate, circuit: 'Circuit') -> None:
    """
    Convert NXOR(a, b) to AIG: AND(NOT(AND(a, NOT(b))), NOT(AND(b, NOT(a)))).

    This is NXOR = (a <-> b) = (a -> b) AND (b -> a) = AND(OR(NOT(a),b), OR(NOT(b),a)).
    Expanded: AND(NOT(AND(a, NOT(b))), NOT(AND(b, NOT(a))))
    Creates: na=NOT(a), nb=NOT(b), t1=AND(a,nb), n1=NOT(t1), t2=AND(b,na), n2=NOT(t2),
             result=AND(n1,n2)

    """
    a, b = _gate.operands
    uid = uuid.uuid4().hex

    na_label = f'aig_nxor_na_{_gate.label}_{uid}'
    nb_label = f'aig_nxor_nb_{_gate.label}_{uid}'
    t1_label = f'aig_nxor_t1_{_gate.label}_{uid}'
    n1_label = f'aig_nxor_n1_{_gate.label}_{uid}'
    t2_label = f'aig_nxor_t2_{_gate.label}_{uid}'
    n2_label = f'aig_nxor_n2_{_gate.label}_{uid}'

    # na = NOT(a)
    circuit.emplace_gate(na_label, gate.NOT, (a,))
    # nb = NOT(b)
    circuit.emplace_gate(nb_label, gate.NOT, (b,))
    # t1 = AND(a, nb) = a AND NOT(b)
    circuit.emplace_gate(t1_label, gate.AND, (a, nb_label))
    # n1 = NOT(t1) = NOT(a AND NOT(b)) = NOT(a) OR b
    circuit.emplace_gate(n1_label, gate.NOT, (t1_label,))
    # t2 = AND(b, na) = b AND NOT(a)
    circuit.emplace_gate(t2_label, gate.AND, (b, na_label))
    # n2 = NOT(t2) = NOT(b AND NOT(a)) = NOT(b) OR a
    circuit.emplace_gate(n2_label, gate.NOT, (t2_label,))

    # Update user tracking
    circuit._remove_user(a, _gate.label)
    circuit._remove_user(b, _gate.label)
    circuit._add_user(n1_label, _gate.label)
    circuit._add_user(n2_label, _gate.label)

    # result = AND(n1, n2)
    circuit._gates[_gate.label] = gate.Gate(_gate.label, gate.AND, (n1_label, n2_label))

    _add_new_gates_to_blocks(
        _gate.label,
        [na_label, nb_label, t1_label, n1_label, t2_label, n2_label],
        circuit,
    )


def _convert_leq_to_aig(_gate: gate.Gate, circuit: 'Circuit') -> None:
    """
    Convert LEQ(x, y) to AIG: NOT(AND(x, NOT(y))).

    LEQ(x, y) means x <= y, which is NOT(x) OR y = NOT(x AND NOT(y)).
    Creates: ny=NOT(y), t=AND(x,ny), result=NOT(t)

    """
    x, y = _gate.operands
    uid = uuid.uuid4().hex

    ny_label = f'aig_leq_ny_{_gate.label}_{uid}'
    t_label = f'aig_leq_t_{_gate.label}_{uid}'

    # ny = NOT(y)
    circuit.emplace_gate(ny_label, gate.NOT, (y,))
    # t = AND(x, ny)
    circuit.emplace_gate(t_label, gate.AND, (x, ny_label))

    # Update user tracking
    circuit._remove_user(x, _gate.label)
    circuit._remove_user(y, _gate.label)
    circuit._add_user(t_label, _gate.label)

    # result = NOT(t)
    circuit._gates[_gate.label] = gate.Gate(_gate.label, gate.NOT, (t_label,))

    _add_new_gates_to_blocks(_gate.label, [ny_label, t_label], circuit)


def _convert_geq_to_aig(_gate: gate.Gate, circuit: 'Circuit') -> None:
    """
    Convert GEQ(x, y) to AIG: NOT(AND(NOT(x), y)).

    GEQ(x, y) means x >= y, which is x OR NOT(y) = NOT(NOT(x) AND y).
    Creates: nx=NOT(x), t=AND(nx,y), result=NOT(t)

    """
    x, y = _gate.operands
    uid = uuid.uuid4().hex

    nx_label = f'aig_geq_nx_{_gate.label}_{uid}'
    t_label = f'aig_geq_t_{_gate.label}_{uid}'

    # nx = NOT(x)
    circuit.emplace_gate(nx_label, gate.NOT, (x,))
    # t = AND(nx, y)
    circuit.emplace_gate(t_label, gate.AND, (nx_label, y))

    # Update user tracking
    circuit._remove_user(x, _gate.label)
    circuit._remove_user(y, _gate.label)
    circuit._add_user(t_label, _gate.label)

    # result = NOT(t)
    circuit._gates[_gate.label] = gate.Gate(_gate.label, gate.NOT, (t_label,))

    _add_new_gates_to_blocks(_gate.label, [nx_label, t_label], circuit)


def _convert_iff_to_aig(_gate: gate.Gate, circuit: 'Circuit') -> None:
    """
    Convert IFF(a) (buffer) to AIG by rewiring users directly to the operand.

    IFF is a buffer gate that simply passes through its input. In AIG, we eliminate
    it by rewiring all users of this gate to use the operand directly.

    """
    # Check if gate still exists (it might have been deleted already by a previous
    # conversion, e.g., if this was created from LIFF/RIFF and then processed again)
    if _gate.label not in circuit.gates:
        return

    # Get the current gate from the circuit (operands may have been rewired)
    current_gate = circuit.get_gate(_gate.label)

    # If the gate type changed (e.g., it was already converted), skip
    if current_gate.gate_type != gate.IFF:
        return

    operand = current_gate.operands[0]

    # Get users of this IFF gate (make a copy since we'll modify the list)
    users = list(circuit.get_gate_users(_gate.label))

    # Rewire each user to use the operand directly
    for user_label in users:
        # Check if user still exists
        if user_label not in circuit.gates:
            continue
        user_gate = circuit.get_gate(user_label)
        new_operands = tuple(
            operand if op == _gate.label else op for op in user_gate.operands
        )
        circuit._gates[user_label] = gate.Gate(
            user_label, user_gate.gate_type, new_operands
        )
        # Update user tracking: add user to operand's users
        circuit._add_user(operand, user_label)

    # Update outputs if this gate is an output
    for i, out_label in enumerate(circuit.outputs):
        if out_label == _gate.label:
            circuit._outputs[i] = operand

    # Remove this gate from operand's users
    circuit._remove_user(operand, _gate.label)

    # Remove the IFF gate itself
    del circuit._gates[_gate.label]
    if _gate.label in circuit._gate_to_users:
        del circuit._gate_to_users[_gate.label]

    # Remove from blocks
    for block in circuit.blocks.values():
        if _gate.label in block.gates:
            block._gates.remove(_gate.label)


def _convert_liff_to_aig(_gate: gate.Gate, circuit: 'Circuit') -> None:
    """
    Convert LIFF(x, y) to AIG by rewiring users directly to operand x.

    LIFF returns the left operand, so we eliminate the gate by rewiring users to x.

    """
    # Check if gate still exists
    if _gate.label not in circuit.gates:
        return

    current_gate = circuit.get_gate(_gate.label)
    if current_gate.gate_type != gate.LIFF:
        return

    left_operand = current_gate.operands[0]
    right_operand = current_gate.operands[1]

    # Get users of this gate (make a copy)
    users = list(circuit.get_gate_users(_gate.label))

    # Rewire each user to use the left operand directly
    for user_label in users:
        if user_label not in circuit.gates:
            continue
        user_gate = circuit.get_gate(user_label)
        new_operands = tuple(
            left_operand if op == _gate.label else op for op in user_gate.operands
        )
        circuit._gates[user_label] = gate.Gate(
            user_label, user_gate.gate_type, new_operands
        )
        circuit._add_user(left_operand, user_label)

    # Update outputs
    for i, out_label in enumerate(circuit.outputs):
        if out_label == _gate.label:
            circuit._outputs[i] = left_operand

    # Remove this gate from operands' users
    circuit._remove_user(left_operand, _gate.label)
    circuit._remove_user(right_operand, _gate.label)

    # Remove the gate
    del circuit._gates[_gate.label]
    if _gate.label in circuit._gate_to_users:
        del circuit._gate_to_users[_gate.label]

    # Remove from blocks
    for block in circuit.blocks.values():
        if _gate.label in block.gates:
            block._gates.remove(_gate.label)


def _convert_riff_to_aig(_gate: gate.Gate, circuit: 'Circuit') -> None:
    """
    Convert RIFF(x, y) to AIG by rewiring users directly to operand y.

    RIFF returns the right operand, so we eliminate the gate by rewiring users to y.

    """
    # Check if gate still exists
    if _gate.label not in circuit.gates:
        return

    current_gate = circuit.get_gate(_gate.label)
    if current_gate.gate_type != gate.RIFF:
        return

    left_operand = current_gate.operands[0]
    right_operand = current_gate.operands[1]

    # Get users of this gate (make a copy)
    users = list(circuit.get_gate_users(_gate.label))

    # Rewire each user to use the right operand directly
    for user_label in users:
        if user_label not in circuit.gates:
            continue
        user_gate = circuit.get_gate(user_label)
        new_operands = tuple(
            right_operand if op == _gate.label else op for op in user_gate.operands
        )
        circuit._gates[user_label] = gate.Gate(
            user_label, user_gate.gate_type, new_operands
        )
        circuit._add_user(right_operand, user_label)

    # Update outputs
    for i, out_label in enumerate(circuit.outputs):
        if out_label == _gate.label:
            circuit._outputs[i] = right_operand

    # Remove this gate from operands' users
    circuit._remove_user(left_operand, _gate.label)
    circuit._remove_user(right_operand, _gate.label)

    # Remove the gate
    del circuit._gates[_gate.label]
    if _gate.label in circuit._gate_to_users:
        del circuit._gate_to_users[_gate.label]

    # Remove from blocks
    for block in circuit.blocks.values():
        if _gate.label in block.gates:
            block._gates.remove(_gate.label)


_aig_convertors: dict[gate.GateType, tp.Callable[[gate.Gate, 'Circuit'], None]] = {
    gate.OR: _convert_or_to_aig,
    gate.NAND: _convert_nand_to_aig,
    gate.NOR: _convert_nor_to_aig,
    gate.XOR: _convert_xor_to_aig,
    gate.NXOR: _convert_nxor_to_aig,
    gate.LEQ: _convert_leq_to_aig,
    gate.GEQ: _convert_geq_to_aig,
    gate.IFF: _convert_iff_to_aig,
    # LT and GT are already AIG-compatible after bench conversion (AND + NOT)
    gate.LT: _convert_lt,
    gate.GT: _convert_gt,
    # LIFF, RIFF directly rewire to operand (buffer elimination)
    gate.LIFF: _convert_liff_to_aig,
    gate.RIFF: _convert_riff_to_aig,
    # LNOT, RNOT convert to NOT which is already AIG
    gate.LNOT: _convert_lnot,
    gate.RNOT: _convert_rnot,
}
