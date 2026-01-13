import logging

from cirbo.core.circuit import Circuit, Gate, gate, Label
from cirbo.core.circuit.transformer import Transformer
from cirbo.minimization.simplification.merge_unary_operators import MergeUnaryOperators

__all__ = [
    'RemoveConstantGates',
]

logger = logging.getLogger(__name__)


class RemoveConstantGates(Transformer):
    """
    Simplifies the circuit by propagating and removing constant gates.

    When a gate has a constant (ALWAYS_TRUE or ALWAYS_FALSE) operand, the transformer
    computes the simplified form of that gate based on the truth table evaluation
    with the known constant value.

    Examples:
        - AND(x, ALWAYS_TRUE) -> x
        - AND(x, ALWAYS_FALSE) -> ALWAYS_FALSE
        - OR(x, ALWAYS_TRUE) -> ALWAYS_TRUE
        - OR(x, ALWAYS_FALSE) -> x
        - NOT(ALWAYS_TRUE) -> ALWAYS_FALSE
        - XOR(x, ALWAYS_TRUE) -> NOT(x)
        - XOR(x, ALWAYS_FALSE) -> x

    Note: output gate labels may change after this method is applied, but their
    order will be preserved.

    """

    __idempotent__: bool = True

    def __init__(self):
        super().__init__(post_transformers=(
            # MergeUnaryOperators(),
        ))

    def _transform(self, circuit: Circuit) -> Circuit:
        """
        :param circuit: the original circuit to be simplified
        :return: new simplified version of the circuit

        """
        # Check if there are non-binary gates. If yes, throw an error.
        for g in circuit.gates.values():
            if len(g.operands) > 2:
                raise ValueError(f"Gate {g.label} has {len(g.operands)} operands. Only binary/unary/nullary gates are supported.")

        new_circuit = Circuit()

        # Save constants in a mapping: label -> value (True/False)
        const_map: dict[Label, bool] = {}

        # Save label remappings: label -> mapped_label
        label_remap: dict[Label, Label] = {}

        def resolve_label(lbl: Label) -> Label:
            return label_remap.get(lbl, lbl)

        # Traverse gates in topological order.
        for g in circuit.top_sort(inverse=True):
            # Resolve operands first
            resolved_operands = tuple(resolve_label(op) for op in g.operands)
            
            # Keep inputs.
            if g.gate_type == gate.INPUT:
                new_circuit.emplace_gate(g.label, g.gate_type, g.operands)
                continue

            # Capture existing constant gates
            if g.gate_type == gate.ALWAYS_TRUE:
                const_map[g.label] = True
                continue
            if g.gate_type == gate.ALWAYS_FALSE:
                const_map[g.label] = False
                continue

            # Identify operands that are constants
            const_indices = [i for i, op in enumerate(resolved_operands) if op in const_map]

            # If a gate has no constant operands
            if not const_indices:
                new_circuit.emplace_gate(g.label, g.gate_type, resolved_operands)
                continue

            # If a gate has one constant operand (Binary gate case)
            if len(const_indices) == 1 and len(resolved_operands) == 2:
                const_idx = const_indices[0]
                const_val = const_map[resolved_operands[const_idx]]
                non_const_idx = 1 - const_idx
                non_const_op = resolved_operands[non_const_idx]

                # Check how the gate relates to the other non-constant input.
                
                args0 = [None] * 2
                args0[const_idx] = const_val
                args0[non_const_idx] = False
                val0 = g.operator(*args0)

                args1 = [None] * 2
                args1[const_idx] = const_val
                args1[non_const_idx] = True
                val1 = g.operator(*args1)

                # If the gate is ALWAYS_TRUE/ALWAYS_FALSE, save it as a constant.
                if val0 == val1:
                    const_map[g.label] = val0
                # If the gate is IFF/NOT, save it.
                elif val0 is False and val1 is True:
                    # Identity (IFF) -> Remap to the operand
                    label_remap[g.label] = non_const_op
                elif val0 is True and val1 is False:
                    # Invert (NOT)
                    operand_gate = new_circuit.gates.get(non_const_op)
                    if operand_gate and operand_gate.gate_type == gate.NOT:
                         # NOT(NOT(X)) -> X
                        label_remap[g.label] = operand_gate.operands[0]
                    else:
                        new_circuit.emplace_gate(g.label, gate.NOT, (non_const_op,))
                else:
                    raise RuntimeError(f"Unexpected evaluation result for gate {g.label}: val0={val0}, val1={val1}")
                continue

            # If the gate has two constant operands, evaluate its value and save it in constants.
            if len(const_indices) == len(resolved_operands):
                args = [const_map[op] for op in resolved_operands]
                val = g.operator(*args)
                const_map[g.label] = val
                continue
            
            raise RuntimeError(f"Unexpected case: gate {g.label}.")

        # Set inputs to the remaining inputs.
        final_inputs = [in_ for in_ in circuit.inputs if in_ not in const_map]
        new_circuit.set_inputs(final_inputs)

        # Set outputs to the remaining outputs.
        # We need to resolve outputs that might have been remapped
        final_outputs = [
            out for out in map(resolve_label, circuit.outputs) if out not in const_map
        ]
        new_circuit.set_outputs(final_outputs)

        return new_circuit
