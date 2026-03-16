"""Tests for CubeAndConquerSolver."""

import copy

import pytest

from cirbo.core.circuit import Circuit
from cirbo.core.circuit.gate import Gate, AND, NOT, INPUT, ALWAYS_TRUE, ALWAYS_FALSE
from cirbo.sat.solver.cnc_solver import CubeAndConquerSolver
from cirbo.synthesis.generation.arithmetics import generate_mul, add_sum_two_numbers

CnCConfig = CubeAndConquerSolver.Config


# =============================================================================
# Helper Functions for AIG-based Miter Construction
# =============================================================================


def create_aig_xor() -> Circuit:
    """
    Create XOR gate using only AND and NOT gates (AIG).
    
    Logic: XOR(A, B) = NOT(AND(NOT(A), NOT(B))) AND NOT(AND(A, B))
    Which simplifies to: NOT(A AND B) AND NOT(NOT(A) AND NOT(B))
    """
    xor_ckt = Circuit.bare_circuit(input_size=2)

    in_a = xor_ckt.inputs[0]
    in_b = xor_ckt.inputs[1]

    # Invert the inputs
    xor_ckt.add_gate(Gate('not_a', NOT, (in_a,)))
    xor_ckt.add_gate(Gate('not_b', NOT, (in_b,)))

    # Check if both are False (0,0) -> (NOT A) AND (NOT B)
    xor_ckt.add_gate(Gate('both_false', AND, ('not_a', 'not_b')))
    # Check if both are True (1,1) -> A AND B
    xor_ckt.add_gate(Gate('both_true', AND, (in_a, in_b)))

    # Invert the intermediate results
    xor_ckt.add_gate(Gate('not_both_false', NOT, ('both_false',)))
    xor_ckt.add_gate(Gate('not_both_true', NOT, ('both_true',)))

    # Combine: (NOT both_false) AND (NOT both_true)
    xor_ckt.add_gate(Gate('xor_out', AND, ('not_both_false', 'not_both_true')))

    xor_ckt.mark_as_output('xor_out')
    return xor_ckt


# Pre-create the XOR circuit for reuse
AIG_XOR_CIRCUIT = create_aig_xor()


def build_aig_miter(left: Circuit, right: Circuit) -> Circuit:
    """
    Build a miter circuit using only AIG gates (AND, NOT).
    
    This function creates a circuit that outputs True iff left and right
    produce different outputs for some input. Used for equivalence checking.
    
    :param left: First circuit to compare.
    :param right: Second circuit to compare.
    :return: Miter circuit (SAT iff circuits are not equivalent).
    """
    if left.output_size != 1 or right.output_size != 1:
        raise ValueError("Both circuits must have exactly 1 output")
    
    if left.input_size != right.input_size:
        raise ValueError("Both circuits must have the same number of inputs")

    left_name = "ckt1"
    right_name = "ckt2"
    
    miter = Circuit().add_circuit(left, name=left_name)
    miter.connect_circuit(
        right,
        miter.get_block(left_name).inputs,
        right.inputs,
        name=right_name,
    )
    miter.connect_circuit(
        AIG_XOR_CIRCUIT,
        miter.get_block(left_name).outputs + miter.get_block(right_name).outputs,
        AIG_XOR_CIRCUIT.inputs,
        name="xor"
    )
    miter.set_outputs(miter.get_block("xor").outputs)

    return miter


def build_multi_output_aig_miter(left: Circuit, right: Circuit) -> Circuit:
    """
    Build a miter circuit for multi-output circuits using only AIG gates.
    
    Creates XOR for each output pair and combines them with OR logic
    (implemented using AND/NOT: OR(a,b) = NOT(AND(NOT(a), NOT(b)))).
    
    :param left: First circuit to compare.
    :param right: Second circuit to compare.
    :return: Miter circuit (SAT iff circuits are not equivalent).
    """
    if left.input_size != right.input_size:
        raise ValueError("Both circuits must have the same number of inputs")
    if left.output_size != right.output_size:
        raise ValueError("Both circuits must have the same number of outputs")

    left_name = "ckt1"
    right_name = "ckt2"
    
    miter = Circuit().add_circuit(left, name=left_name)
    miter.connect_circuit(
        right,
        miter.get_block(left_name).inputs,
        right.inputs,
        name=right_name,
    )
    
    # Create XOR for each output pair
    xor_outputs = []
    for i, (left_out, right_out) in enumerate(zip(
        miter.get_block(left_name).outputs,
        miter.get_block(right_name).outputs
    )):
        xor_ckt = create_aig_xor()
        miter.connect_circuit(
            xor_ckt,
            [left_out, right_out],
            xor_ckt.inputs,
            name=f"xor_{i}"
        )
        xor_outputs.append(miter.get_block(f"xor_{i}").outputs[0])
    
    # Combine with OR logic: OR(a,b) = NOT(AND(NOT(a), NOT(b)))
    # For multiple outputs: reduce pairwise
    if len(xor_outputs) == 1:
        miter.set_outputs(xor_outputs)
    else:
        # Create OR tree using AND/NOT
        current_outputs = xor_outputs
        or_idx = 0
        while len(current_outputs) > 1:
            next_outputs = []
            for i in range(0, len(current_outputs), 2):
                if i + 1 < len(current_outputs):
                    a, b = current_outputs[i], current_outputs[i + 1]
                    not_a = f"or_not_a_{or_idx}"
                    not_b = f"or_not_b_{or_idx}"
                    and_gate = f"or_and_{or_idx}"
                    or_gate = f"or_out_{or_idx}"
                    
                    miter.emplace_gate(not_a, NOT, (a,))
                    miter.emplace_gate(not_b, NOT, (b,))
                    miter.emplace_gate(and_gate, AND, (not_a, not_b))
                    miter.emplace_gate(or_gate, NOT, (and_gate,))
                    
                    next_outputs.append(or_gate)
                    or_idx += 1
                else:
                    next_outputs.append(current_outputs[i])
            current_outputs = next_outputs
        
        miter.set_outputs(current_outputs)
    
    return miter


# =============================================================================
# Test Class: Basic SAT Tests
# =============================================================================


class TestCnCSolverBasicSAT:
    """Basic SAT tests with simple AIG circuits."""

    # INPUT CANNOT BE OUTPUT
    # def test_single_input_sat(self):
    #     """Test circuit with single input that can be satisfied."""
    #     circuit = Circuit()
    #     circuit.add_gate(Gate('x', INPUT))
    #     circuit.mark_as_output('x')
    #
    #     solver = CubeAndConquerSolver(CnCConfig())
    #     result = solver.solve(circuit)
    #
    #     assert result.answer is True
    #     assert result.model is not None
    
    def test_and_gate_sat(self):
        """Test simple AND gate circuit - satisfiable when both inputs are True."""
        circuit = Circuit()
        circuit.add_gate(Gate('a', INPUT))
        circuit.add_gate(Gate('b', INPUT))
        circuit.add_gate(Gate('out', AND, ('a', 'b')))
        circuit.mark_as_output('out')
        
        solver = CubeAndConquerSolver(CnCConfig())
        result = solver.solve(circuit)
        
        assert result.answer is True
        assert result.model is not None
    
    def test_not_gate_sat(self):
        """Test simple NOT gate circuit - satisfiable when input is False."""
        circuit = Circuit()
        circuit.add_gate(Gate('a', INPUT))
        circuit.add_gate(Gate('not_a', NOT, ('a',)))
        circuit.mark_as_output('not_a')
        
        solver = CubeAndConquerSolver(CnCConfig())
        result = solver.solve(circuit)
        
        assert result.answer is True
        assert result.model is not None
    
    def test_chain_and_not_sat(self):
        """Test chain of AND and NOT gates - satisfiable."""
        circuit = Circuit()
        circuit.add_gate(Gate('a', INPUT))
        circuit.add_gate(Gate('b', INPUT))
        circuit.add_gate(Gate('and1', AND, ('a', 'b')))
        circuit.add_gate(Gate('not1', NOT, ('and1',)))
        circuit.add_gate(Gate('not2', NOT, ('not1',)))
        circuit.mark_as_output('not2')
        
        solver = CubeAndConquerSolver(CnCConfig())
        result = solver.solve(circuit)
        
        # NOT(NOT(AND(a, b))) = AND(a, b)
        assert result.answer is True
        assert result.model is not None
    
    def test_three_input_and_sat(self):
        """Test three-input AND chain - satisfiable."""
        circuit = Circuit()
        circuit.add_gate(Gate('a', INPUT))
        circuit.add_gate(Gate('b', INPUT))
        circuit.add_gate(Gate('c', INPUT))
        circuit.add_gate(Gate('and1', AND, ('a', 'b')))
        circuit.add_gate(Gate('and2', AND, ('and1', 'c')))
        circuit.mark_as_output('and2')
        
        solver = CubeAndConquerSolver(CnCConfig())
        result = solver.solve(circuit)
        
        assert result.answer is True
        assert result.model is not None


# =============================================================================
# Test Class: Basic UNSAT Tests
# =============================================================================


class TestCnCSolverBasicUNSAT:
    """Basic UNSAT tests with trivially unsatisfiable circuits."""
    
    def test_always_false_via_and(self):
        """Test circuit that is always false through AND logic - unsatisfiable."""
        circuit = Circuit()
        circuit.add_gate(Gate('x', INPUT))
        circuit.add_gate(Gate('not_x', NOT, ('x',)))
        circuit.add_gate(Gate('false', AND, ('x', 'not_x')))
        circuit.mark_as_output('false')
        
        solver = CubeAndConquerSolver(CnCConfig())
        result = solver.solve(circuit)
        
        assert result.answer is False
        assert result.model is None
    
    def test_and_with_negation_unsat(self):
        """Test x AND NOT(x) - always unsatisfiable."""
        circuit = Circuit()
        circuit.add_gate(Gate('x', INPUT))
        circuit.add_gate(Gate('not_x', NOT, ('x',)))
        circuit.add_gate(Gate('out', AND, ('x', 'not_x')))
        circuit.mark_as_output('out')
        
        solver = CubeAndConquerSolver(CnCConfig())
        result = solver.solve(circuit)
        
        assert result.answer is False
        assert result.model is None
    
    def test_complex_unsat(self):
        """Test more complex unsatisfiable circuit."""
        # (a AND b) AND (NOT(a) AND b) is always False
        circuit = Circuit()
        circuit.add_gate(Gate('a', INPUT))
        circuit.add_gate(Gate('b', INPUT))
        circuit.add_gate(Gate('not_a', NOT, ('a',)))
        circuit.add_gate(Gate('and1', AND, ('a', 'b')))
        circuit.add_gate(Gate('and2', AND, ('not_a', 'b')))
        circuit.add_gate(Gate('out', AND, ('and1', 'and2')))
        circuit.mark_as_output('out')
        
        solver = CubeAndConquerSolver(CnCConfig())
        result = solver.solve(circuit)
        
        assert result.answer is False
        assert result.model is None
    
    def test_triple_contradiction_unsat(self):
        """Test circuit with triple contradiction."""
        # a AND NOT(a) AND b is always False
        circuit = Circuit()
        circuit.add_gate(Gate('a', INPUT))
        circuit.add_gate(Gate('b', INPUT))
        circuit.add_gate(Gate('not_a', NOT, ('a',)))
        circuit.add_gate(Gate('and1', AND, ('a', 'not_a')))
        circuit.add_gate(Gate('out', AND, ('and1', 'b')))
        circuit.mark_as_output('out')
        
        solver = CubeAndConquerSolver(CnCConfig())
        result = solver.solve(circuit)
        
        assert result.answer is False
        assert result.model is None


# =============================================================================
# Test Class: XOR Circuit Tests
# =============================================================================


class TestCnCSolverXOR:
    """Tests for XOR circuit built from AIG gates."""
    
    def test_xor_is_sat(self):
        """Test that XOR circuit is satisfiable."""
        xor_ckt = create_aig_xor()
        
        solver = CubeAndConquerSolver(CnCConfig())
        result = solver.solve(xor_ckt)
        
        assert result.answer is True
        assert result.model is not None
    
    def test_xor_correctness(self):
        """Verify XOR circuit produces correct truth table."""
        xor_ckt = create_aig_xor()
        
        # XOR truth table: (0,0)->0, (0,1)->1, (1,0)->1, (1,1)->0
        assert xor_ckt.evaluate([False, False]) == [False]
        assert xor_ckt.evaluate([False, True]) == [True]
        assert xor_ckt.evaluate([True, False]) == [True]
        assert xor_ckt.evaluate([True, True]) == [False]


# =============================================================================
# Test Class: Miter Tests for Equivalent Circuits (UNSAT)
# =============================================================================


class TestCnCSolverEquivalence:
    """Miter tests for equivalent circuits (should be UNSAT)."""
    
    def test_identity_circuit_equivalent(self):
        """Test that a circuit is equivalent to itself."""
        circuit = Circuit()
        circuit.add_gate(Gate('x', INPUT))
        circuit.add_gate(Gate('not_x', NOT, ('x',)))
        circuit.add_gate(Gate('not_not_x', NOT, ('not_x',)))
        circuit.mark_as_output('not_not_x')
        
        circuit_copy = copy.copy(circuit)
        miter = build_aig_miter(circuit, circuit_copy)
        
        solver = CubeAndConquerSolver(CnCConfig())
        result = solver.solve(miter)
        
        # Identical circuits should produce UNSAT miter
        assert result.answer is False
        assert result.model is None
    
    def test_double_negation_equivalent(self):
        """Test NOT(NOT(x)) is equivalent to x."""
        # Circuit 1: just x
        circuit1 = Circuit()
        circuit1.add_gate(Gate('x', INPUT))
        circuit1.mark_as_output('x')
        
        # Circuit 2: NOT(NOT(x))
        circuit2 = Circuit()
        circuit2.add_gate(Gate('x', INPUT))
        circuit2.add_gate(Gate('not_x', NOT, ('x',)))
        circuit2.add_gate(Gate('not_not_x', NOT, ('not_x',)))
        circuit2.mark_as_output('not_not_x')
        
        miter = build_aig_miter(circuit1, circuit2)
        
        solver = CubeAndConquerSolver(CnCConfig())
        result = solver.solve(miter)
        
        assert result.answer is False
        assert result.model is None
    
    def test_and_commutativity(self):
        """Test AND(a, b) is equivalent to AND(b, a)."""
        # Circuit 1: a AND b
        circuit1 = Circuit()
        circuit1.add_gate(Gate('a', INPUT))
        circuit1.add_gate(Gate('b', INPUT))
        circuit1.add_gate(Gate('out', AND, ('a', 'b')))
        circuit1.mark_as_output('out')
        
        # Circuit 2: b AND a
        circuit2 = Circuit()
        circuit2.add_gate(Gate('a', INPUT))
        circuit2.add_gate(Gate('b', INPUT))
        circuit2.add_gate(Gate('out', AND, ('b', 'a')))
        circuit2.mark_as_output('out')
        
        miter = build_aig_miter(circuit1, circuit2)
        
        solver = CubeAndConquerSolver(CnCConfig())
        result = solver.solve(miter)
        
        assert result.answer is False
        assert result.model is None
    
    def test_de_morgan_equivalence(self):
        """Test De Morgan's law: NOT(a AND b) = NOT(a) OR NOT(b)."""
        # Circuit 1: NOT(a AND b)
        circuit1 = Circuit()
        circuit1.add_gate(Gate('a', INPUT))
        circuit1.add_gate(Gate('b', INPUT))
        circuit1.add_gate(Gate('and_ab', AND, ('a', 'b')))
        circuit1.add_gate(Gate('out', NOT, ('and_ab',)))
        circuit1.mark_as_output('out')
        
        # Circuit 2: NOT(a) OR NOT(b) = NOT(NOT(NOT(a)) AND NOT(NOT(b)))
        #                             = NOT(a AND b) -- same as circuit1 in this case
        # Let's use: NOT(AND(NOT(NOT(a)), NOT(NOT(b)))) which equals NOT(AND(a, b))
        # Actually for De Morgan, NOT(a) OR NOT(b) in AIG is:
        # NOT(AND(NOT(NOT(a)), NOT(NOT(b)))) = NOT(AND(a, b))
        # So they should be equivalent
        circuit2 = Circuit()
        circuit2.add_gate(Gate('a', INPUT))
        circuit2.add_gate(Gate('b', INPUT))
        circuit2.add_gate(Gate('not_a', NOT, ('a',)))
        circuit2.add_gate(Gate('not_b', NOT, ('b',)))
        # OR(NOT(a), NOT(b)) = NOT(AND(NOT(NOT(a)), NOT(NOT(b)))) = NOT(AND(a, b))
        # But we need to implement OR using AIG: OR(x,y) = NOT(AND(NOT(x), NOT(y)))
        # So OR(NOT(a), NOT(b)) = NOT(AND(NOT(NOT(a)), NOT(NOT(b)))) = NOT(AND(a, b))
        circuit2.add_gate(Gate('not_not_a', NOT, ('not_a',)))
        circuit2.add_gate(Gate('not_not_b', NOT, ('not_b',)))
        circuit2.add_gate(Gate('and_nn', AND, ('not_not_a', 'not_not_b')))
        circuit2.add_gate(Gate('out', NOT, ('and_nn',)))
        circuit2.mark_as_output('out')
        
        miter = build_aig_miter(circuit1, circuit2)
        
        solver = CubeAndConquerSolver(CnCConfig())
        result = solver.solve(miter)
        
        assert result.answer is False
        assert result.model is None


# =============================================================================
# Test Class: Miter Tests for Non-Equivalent Circuits (SAT)
# =============================================================================


class TestCnCSolverNonEquivalence:
    """Miter tests for non-equivalent circuits (should be SAT)."""
    
    def test_not_vs_identity(self):
        """Test NOT(x) is not equivalent to x."""
        # Circuit 1: x
        circuit1 = Circuit()
        circuit1.add_gate(Gate('x', INPUT))
        circuit1.mark_as_output('x')
        
        # Circuit 2: NOT(x)
        circuit2 = Circuit()
        circuit2.add_gate(Gate('x', INPUT))
        circuit2.add_gate(Gate('not_x', NOT, ('x',)))
        circuit2.mark_as_output('not_x')
        
        miter = build_aig_miter(circuit1, circuit2)
        
        solver = CubeAndConquerSolver(CnCConfig())
        result = solver.solve(miter)
        
        assert result.answer is True
        assert result.model is not None
    
    def test_and_vs_first_input(self):
        """Test AND(a, b) is not equivalent to just a."""
        # Circuit 1: a
        circuit1 = Circuit()
        circuit1.add_gate(Gate('a', INPUT))
        circuit1.add_gate(Gate('b', INPUT))
        circuit1.mark_as_output('a')
        
        # Circuit 2: AND(a, b)
        circuit2 = Circuit()
        circuit2.add_gate(Gate('a', INPUT))
        circuit2.add_gate(Gate('b', INPUT))
        circuit2.add_gate(Gate('out', AND, ('a', 'b')))
        circuit2.mark_as_output('out')
        
        miter = build_aig_miter(circuit1, circuit2)
        
        solver = CubeAndConquerSolver(CnCConfig())
        result = solver.solve(miter)
        
        assert result.answer is True
        assert result.model is not None
    
    def test_different_and_structures(self):
        """Test AND(a, b) is not equivalent to AND(a, NOT(b))."""
        # Circuit 1: AND(a, b)
        circuit1 = Circuit()
        circuit1.add_gate(Gate('a', INPUT))
        circuit1.add_gate(Gate('b', INPUT))
        circuit1.add_gate(Gate('out', AND, ('a', 'b')))
        circuit1.mark_as_output('out')
        
        # Circuit 2: AND(a, NOT(b))
        circuit2 = Circuit()
        circuit2.add_gate(Gate('a', INPUT))
        circuit2.add_gate(Gate('b', INPUT))
        circuit2.add_gate(Gate('not_b', NOT, ('b',)))
        circuit2.add_gate(Gate('out', AND, ('a', 'not_b')))
        circuit2.mark_as_output('out')
        
        miter = build_aig_miter(circuit1, circuit2)
        
        solver = CubeAndConquerSolver(CnCConfig())
        result = solver.solve(miter)
        
        assert result.answer is True
        assert result.model is not None
    
    def test_xor_vs_and(self):
        """Test XOR(a, b) is not equivalent to AND(a, b)."""
        # Circuit 1: XOR(a, b) using AIG
        xor_ckt = create_aig_xor()
        
        # Circuit 2: AND(a, b)
        and_ckt = Circuit()
        and_ckt.add_gate(Gate('0', INPUT))
        and_ckt.add_gate(Gate('1', INPUT))
        and_ckt.add_gate(Gate('out', AND, ('0', '1')))
        and_ckt.mark_as_output('out')
        
        miter = build_aig_miter(xor_ckt, and_ckt)
        
        solver = CubeAndConquerSolver(CnCConfig())
        result = solver.solve(miter)
        
        assert result.answer is True
        assert result.model is not None


# =============================================================================
# Test Class: Buggy Circuit Tests
# =============================================================================


class TestCnCSolverBuggyCircuits:
    """Tests with artificially buggy circuits."""
    
    def _create_buggy_and_for_zeros(self) -> Circuit:
        """
        Create a buggy AND gate that returns 1 when both inputs are 0.
        
        Normal AND: (0,0)->0, (0,1)->0, (1,0)->0, (1,1)->1
        Buggy AND:  (0,0)->1, (0,1)->0, (1,0)->0, (1,1)->1
        
        Implementation: AND(a, b) OR (NOT(a) AND NOT(b))
                      = NOT(AND(NOT(AND(a,b)), AND(NOT(a), NOT(b))))... actually
        Let's use: (a AND b) OR (NOT(a) AND NOT(b))
        In AIG: NOT(AND(NOT(a AND b), NOT(NOT(a) AND NOT(b))))
        """
        circuit = Circuit()
        circuit.add_gate(Gate('a', INPUT))
        circuit.add_gate(Gate('b', INPUT))
        
        # a AND b
        circuit.add_gate(Gate('and_ab', AND, ('a', 'b')))
        
        # NOT(a) AND NOT(b)
        circuit.add_gate(Gate('not_a', NOT, ('a',)))
        circuit.add_gate(Gate('not_b', NOT, ('b',)))
        circuit.add_gate(Gate('both_zero', AND, ('not_a', 'not_b')))
        
        # OR in AIG: NOT(AND(NOT(x), NOT(y)))
        circuit.add_gate(Gate('not_and_ab', NOT, ('and_ab',)))
        circuit.add_gate(Gate('not_both_zero', NOT, ('both_zero',)))
        circuit.add_gate(Gate('or_inner', AND, ('not_and_ab', 'not_both_zero')))
        circuit.add_gate(Gate('out', NOT, ('or_inner',)))
        
        circuit.mark_as_output('out')
        return circuit
    
    def test_buggy_and_differs_from_normal(self):
        """Test that buggy AND gate differs from normal AND."""
        # Normal AND
        normal_and = Circuit()
        normal_and.add_gate(Gate('a', INPUT))
        normal_and.add_gate(Gate('b', INPUT))
        normal_and.add_gate(Gate('out', AND, ('a', 'b')))
        normal_and.mark_as_output('out')
        
        # Buggy AND (returns 1 for both zeros)
        buggy_and = self._create_buggy_and_for_zeros()
        
        # Verify the buggy behavior
        assert buggy_and.evaluate([False, False]) == [True]  # Bug: should be False
        assert buggy_and.evaluate([False, True]) == [False]
        assert buggy_and.evaluate([True, False]) == [False]
        assert buggy_and.evaluate([True, True]) == [True]
        
        miter = build_aig_miter(normal_and, buggy_and)
        
        solver = CubeAndConquerSolver(CnCConfig())
        result = solver.solve(miter)
        
        # Should be SAT because circuits differ
        assert result.answer is True
        assert result.model is not None
    
    def test_buggy_not_gate(self):
        """Test a NOT gate that is stuck at 1."""
        # Normal circuit: NOT(x)
        normal = Circuit()
        normal.add_gate(Gate('x', INPUT))
        normal.add_gate(Gate('out', NOT, ('x',)))
        normal.mark_as_output('out')
        
        # Buggy circuit: always outputs 1 regardless of input
        buggy = Circuit()
        buggy.add_gate(Gate('x', INPUT))
        buggy.add_gate(Gate('true', ALWAYS_TRUE))
        buggy.mark_as_output('true')
        
        miter = build_aig_miter(normal, buggy)
        
        solver = CubeAndConquerSolver(CnCConfig())
        result = solver.solve(miter)
        
        # Should be SAT because circuits differ (when x=0, normal outputs 1, buggy outputs 1)
        # but when x=1, normal outputs 0, buggy outputs 1
        assert result.answer is True
        assert result.model is not None
    
    def test_stuck_at_zero_output(self):
        """Test detecting a stuck-at-0 fault."""
        # Normal: x
        normal = Circuit()
        normal.add_gate(Gate('x', INPUT))
        normal.mark_as_output('x')
        
        # Faulty: always 0
        faulty = Circuit()
        faulty.add_gate(Gate('x', INPUT))
        faulty.add_gate(Gate('false', ALWAYS_FALSE))
        faulty.mark_as_output('false')
        
        miter = build_aig_miter(normal, faulty)
        
        solver = CubeAndConquerSolver(CnCConfig())
        result = solver.solve(miter)
        
        assert result.answer is True
        assert result.model is not None
    
    def test_inverted_output_bug(self):
        """Test detecting an inverted output bug."""
        # Normal: AND(a, b)
        normal = Circuit()
        normal.add_gate(Gate('a', INPUT))
        normal.add_gate(Gate('b', INPUT))
        normal.add_gate(Gate('and', AND, ('a', 'b')))
        normal.mark_as_output('and')
        
        # Buggy: NOT(AND(a, b)) - inverted output
        buggy = Circuit()
        buggy.add_gate(Gate('a', INPUT))
        buggy.add_gate(Gate('b', INPUT))
        buggy.add_gate(Gate('and', AND, ('a', 'b')))
        buggy.add_gate(Gate('not_and', NOT, ('and',)))
        buggy.mark_as_output('not_and')
        
        miter = build_aig_miter(normal, buggy)
        
        solver = CubeAndConquerSolver(CnCConfig())
        result = solver.solve(miter)
        
        assert result.answer is True
        assert result.model is not None
    
    def test_swapped_inputs_bug(self):
        """Test detecting swapped inputs in asymmetric function."""
        # Create asymmetric function: a AND NOT(b)
        # This should differ from NOT(a) AND b when inputs are swapped
        
        # Normal: a AND NOT(b)
        normal = Circuit()
        normal.add_gate(Gate('a', INPUT))
        normal.add_gate(Gate('b', INPUT))
        normal.add_gate(Gate('not_b', NOT, ('b',)))
        normal.add_gate(Gate('out', AND, ('a', 'not_b')))
        normal.mark_as_output('out')
        
        # Buggy (swapped): b AND NOT(a) = NOT(a) AND b
        buggy = Circuit()
        buggy.add_gate(Gate('a', INPUT))
        buggy.add_gate(Gate('b', INPUT))
        buggy.add_gate(Gate('not_a', NOT, ('a',)))
        buggy.add_gate(Gate('out', AND, ('not_a', 'b')))
        buggy.mark_as_output('out')
        
        miter = build_aig_miter(normal, buggy)
        
        solver = CubeAndConquerSolver(CnCConfig())
        result = solver.solve(miter)
        
        assert result.answer is True
        assert result.model is not None


# =============================================================================
# Test Class: Multi-Output Circuit Tests
# =============================================================================


class TestCnCSolverMultiOutput:
    """Tests for multi-output circuits using the multi-output miter."""
    
    def test_two_output_equivalent(self):
        """Test equivalent two-output circuits."""
        # Circuit 1
        circuit1 = Circuit()
        circuit1.add_gate(Gate('a', INPUT))
        circuit1.add_gate(Gate('b', INPUT))
        circuit1.add_gate(Gate('and', AND, ('a', 'b')))
        circuit1.add_gate(Gate('not_and', NOT, ('and',)))
        circuit1.mark_as_output('and')
        circuit1.mark_as_output('not_and')
        
        # Circuit 2 - same logic
        circuit2 = Circuit()
        circuit2.add_gate(Gate('a', INPUT))
        circuit2.add_gate(Gate('b', INPUT))
        circuit2.add_gate(Gate('and', AND, ('a', 'b')))
        circuit2.add_gate(Gate('not_and', NOT, ('and',)))
        circuit2.mark_as_output('and')
        circuit2.mark_as_output('not_and')
        
        miter = build_multi_output_aig_miter(circuit1, circuit2)
        
        solver = CubeAndConquerSolver(CnCConfig())
        result = solver.solve(miter)
        
        assert result.answer is False
        assert result.model is None
    
    def test_two_output_different(self):
        """Test non-equivalent two-output circuits."""
        # Circuit 1: outputs (AND, NOT(AND))
        circuit1 = Circuit()
        circuit1.add_gate(Gate('a', INPUT))
        circuit1.add_gate(Gate('b', INPUT))
        circuit1.add_gate(Gate('and', AND, ('a', 'b')))
        circuit1.add_gate(Gate('not_and', NOT, ('and',)))
        circuit1.mark_as_output('and')
        circuit1.mark_as_output('not_and')
        
        # Circuit 2: outputs (a, b) - different
        circuit2 = Circuit()
        circuit2.add_gate(Gate('a', INPUT))
        circuit2.add_gate(Gate('b', INPUT))
        circuit2.mark_as_output('a')
        circuit2.mark_as_output('b')
        
        miter = build_multi_output_aig_miter(circuit1, circuit2)
        
        solver = CubeAndConquerSolver(CnCConfig())
        result = solver.solve(miter)
        
        assert result.answer is True
        assert result.model is not None


# =============================================================================
# Test Class: max_depth Parameter Tests
# =============================================================================


class TestCnCSolverMaxDepth:
    """Tests for the max_depth parameter that limits cube recursion depth."""

    def test_max_depth_zero_allows_one_level(self):
        """Test that max_depth=0 allows cubing at depth 0 only (depth > 0 stops)."""
        circuit = Circuit()
        circuit.add_gate(Gate('a', INPUT))
        circuit.add_gate(Gate('b', INPUT))
        circuit.add_gate(Gate('and', AND, ('a', 'b')))
        circuit.mark_as_output('and')

        solver = CubeAndConquerSolver(CnCConfig(max_depth=0))
        cubes = solver.cube(circuit)

        assert len(cubes) >= 1

    def test_max_depth_one_limits_cubing(self):
        """Test that max_depth=1 limits cubing to depths 0 and 1."""
        circuit = Circuit()
        circuit.add_gate(Gate('a', INPUT))
        circuit.add_gate(Gate('b', INPUT))
        circuit.add_gate(Gate('c', INPUT))
        circuit.add_gate(Gate('and1', AND, ('a', 'b')))
        circuit.add_gate(Gate('and2', AND, ('and1', 'c')))
        circuit.mark_as_output('and2')

        solver = CubeAndConquerSolver(CnCConfig(max_depth=1))
        cubes = solver.cube(circuit)

        assert len(cubes) <= 4

    def test_default_max_depth(self):
        """Test that default max_depth matches the explicit default value (2)."""
        circuit = Circuit()
        circuit.add_gate(Gate('a', INPUT))
        circuit.add_gate(Gate('b', INPUT))
        circuit.add_gate(Gate('and', AND, ('a', 'b')))
        circuit.mark_as_output('and')

        solver_default = CubeAndConquerSolver(CnCConfig())
        solver_explicit = CubeAndConquerSolver(CnCConfig(max_depth=2))

        cubes_default = solver_default.cube(circuit)
        cubes_explicit = solver_explicit.cube(circuit)

        assert len(cubes_default) == len(cubes_explicit)

    def test_max_depth_still_produces_correct_sat_result(self):
        """Test that solver with max_depth still produces correct SAT result."""
        circuit = Circuit()
        circuit.add_gate(Gate('a', INPUT))
        circuit.add_gate(Gate('b', INPUT))
        circuit.add_gate(Gate('and', AND, ('a', 'b')))
        circuit.mark_as_output('and')

        solver = CubeAndConquerSolver(CnCConfig(max_depth=1))
        result = solver.solve(circuit)

        assert result.answer is True
        assert result.model is not None

    def test_max_depth_still_produces_correct_unsat_result(self):
        """Test that solver with max_depth still produces correct UNSAT result."""
        circuit = Circuit()
        circuit.add_gate(Gate('x', INPUT))
        circuit.add_gate(Gate('not_x', NOT, ('x',)))
        circuit.add_gate(Gate('out', AND, ('x', 'not_x')))
        circuit.mark_as_output('out')

        solver = CubeAndConquerSolver(CnCConfig(max_depth=1))
        result = solver.solve(circuit)

        assert result.answer is False
        assert result.model is None

    def test_higher_depth_produces_more_cubes(self):
        """Test that higher max_depth can produce more cubes."""
        circuit = Circuit()
        circuit.add_gate(Gate('a', INPUT))
        circuit.add_gate(Gate('b', INPUT))
        circuit.add_gate(Gate('c', INPUT))
        circuit.add_gate(Gate('and1', AND, ('a', 'b')))
        circuit.add_gate(Gate('and2', AND, ('and1', 'c')))
        circuit.mark_as_output('and2')

        solver_depth_0 = CubeAndConquerSolver(CnCConfig(max_depth=0))
        solver_depth_1 = CubeAndConquerSolver(CnCConfig(max_depth=1))
        solver_depth_2 = CubeAndConquerSolver(CnCConfig(max_depth=2))

        cubes_0 = solver_depth_0.cube(circuit)
        cubes_1 = solver_depth_1.cube(circuit)
        cubes_2 = solver_depth_2.cube(circuit)

        assert len(cubes_0) <= len(cubes_1) <= len(cubes_2)

    def test_max_depth_higher_than_natural_depth(self):
        """Test that when max_depth exceeds natural recursion depth, result matches another large value."""
        circuit = Circuit()
        circuit.add_gate(Gate('a', INPUT))
        circuit.add_gate(Gate('b', INPUT))
        circuit.add_gate(Gate('and', AND, ('a', 'b')))
        circuit.mark_as_output('and')

        solver_high_depth = CubeAndConquerSolver(CnCConfig(max_depth=5))
        solver_also_high = CubeAndConquerSolver(CnCConfig(max_depth=8))

        cubes_high = solver_high_depth.cube(circuit)
        cubes_also_high = solver_also_high.cube(circuit)

        assert len(cubes_high) == len(cubes_also_high)

    def test_max_depth_is_limiting_factor(self):
        """Test that max_depth actually limits when it's lower than natural depth."""
        xor_ckt = create_aig_xor()

        solver_depth_0 = CubeAndConquerSolver(CnCConfig(max_depth=0))
        solver_depth_1 = CubeAndConquerSolver(CnCConfig(max_depth=1))
        solver_depth_5 = CubeAndConquerSolver(CnCConfig(max_depth=5))

        cubes_depth_0 = solver_depth_0.cube(xor_ckt)
        cubes_depth_1 = solver_depth_1.cube(xor_ckt)
        cubes_depth_5 = solver_depth_5.cube(xor_ckt)

        assert len(cubes_depth_0) <= len(cubes_depth_1) <= len(cubes_depth_5)
