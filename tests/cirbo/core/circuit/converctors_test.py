import copy

import pytest

from cirbo.core.circuit import gate
from cirbo.core.circuit.circuit import Circuit
from cirbo.core.circuit.exceptions import GateDoesntExistError


@pytest.mark.parametrize(
    'type',
    [
        gate.AND,
        gate.GEQ,
        gate.GT,
        gate.LEQ,
        gate.LIFF,
        gate.LNOT,
        gate.LT,
        gate.NAND,
        gate.NOR,
        gate.NXOR,
        gate.OR,
        gate.RIFF,
        gate.RNOT,
        gate.XOR,
    ],
)
def test_simple(type: gate.GateType):
    C0 = (
        Circuit()
        .add_gate(gate.Gate('A', gate.INPUT))
        .add_gate(gate.Gate('B', gate.INPUT))
        .add_gate(gate.Gate('C', type, ('A', 'B')))
    )

    C1 = copy.copy(C0)
    C1.into_bench()

    assert C0.get_truth_table() == C1.get_truth_table()


def test_always_true():
    C0 = (
        Circuit()
        .add_gate(gate.Gate('A', gate.INPUT))
        .add_gate(gate.Gate('B', gate.ALWAYS_TRUE))
    )

    C1 = copy.copy(C0)
    C1.into_bench()

    assert C0.get_truth_table() == C1.get_truth_table()

    C0 = Circuit().add_gate(gate.Gate('A', gate.ALWAYS_TRUE))
    with pytest.raises(GateDoesntExistError):
        C0.into_bench()


def test_always_false():
    C0 = (
        Circuit()
        .add_gate(gate.Gate('A', gate.INPUT))
        .add_gate(gate.Gate('B', gate.ALWAYS_FALSE))
    )

    C1 = copy.copy(C0)
    C1.into_bench()

    assert C0.get_truth_table() == C1.get_truth_table()

    C0 = Circuit().add_gate(gate.Gate('A', gate.ALWAYS_FALSE))
    with pytest.raises(GateDoesntExistError):
        C0.into_bench()


def test_mix_ckt_gates():

    C0 = Circuit()

    C0.add_gate(gate.Gate('1', gate.INPUT))
    C0.add_gate(gate.Gate('2', gate.INPUT))
    C0.add_gate(gate.Gate('3', gate.NOT, ('1',)))
    C0.add_gate(gate.Gate('4', gate.AND, ('1', '2')))
    C0.add_gate(gate.Gate('5', gate.XOR, ('1', '2')))
    C0.add_gate(gate.Gate('6', gate.AND, ('2', '4')))
    C0.add_gate(gate.Gate('7', gate.ALWAYS_FALSE))
    C0.add_gate(gate.Gate('8', gate.ALWAYS_TRUE))
    C0.add_gate(gate.Gate('9', gate.LNOT, ('7', '3')))
    C0.add_gate(gate.Gate('10', gate.RNOT, ('4', '8')))
    C0.add_gate(gate.Gate('11', gate.LEQ, ('2', '4')))
    C0.add_gate(gate.Gate('12', gate.LT, ('2', '11')))
    C0.add_gate(gate.Gate('13', gate.GEQ, ('11', '12')))
    C0.add_gate(gate.Gate('14', gate.GT, ('13', '5')))
    C0.add_gate(gate.Gate('15', gate.IFF, ('14',)))
    C0.add_gate(gate.Gate('16', gate.LIFF, ('15', '5')))
    C0.add_gate(gate.Gate('17', gate.RIFF, ('13', '16')))

    C0.mark_as_output('17')

    C1 = copy.copy(C0)
    C1.into_bench()

    assert C0.get_truth_table() == C1.get_truth_table()
    assert set(C1.get_gate_users('1')) & set(['3', '4', '5', '7', '8']) == set(
        ['3', '4', '5', '7', '8']
    )
    assert len(C1.get_gate_users('1')) == 7
    assert C1.get_gate_users('3') == []
    assert len(C1.get_gate_users('7')) == 1
    assert C1.get_gate_users('8') == ['10']
    assert C0.get_gate_users('2') == ['4', '5', '6', '11', '12']
    assert '12' not in C1.get_gate_users('2')
    assert '11' not in C1.get_gate_users('2')
    assert set(C1.get_gate_users('2')) & set(['4', '5', '6']) == set(['4', '5', '6'])
    assert len(C1.get_gate_users('2')) == 5


def test_block():
    C0 = (
        Circuit()
        .add_gate(gate.Gate('A', gate.INPUT))
        .add_gate(gate.Gate('B', gate.INPUT))
        .add_gate(gate.Gate('C', gate.LT, ('A', 'B')))
        .add_gate(gate.Gate('D', gate.AND, ('B', 'C')))
    )
    C0.mark_as_output('C')

    C0.make_block_from_slice('new_block', C0.inputs, ['C'])
    assert C0._blocks['new_block'].gates == ['C']

    C0.into_bench()
    assert len(C0._blocks['new_block'].gates) == 2


# =============================================================================
# AIG Conversion Tests
# =============================================================================

# Valid AIG gate types
AIG_GATE_TYPES = {gate.INPUT, gate.AND, gate.NOT, gate.ALWAYS_TRUE, gate.ALWAYS_FALSE}


def _is_aig_circuit(circuit: Circuit) -> bool:
    """Check if all gates in the circuit are valid AIG gates."""
    for g in circuit.gates.values():
        if g.gate_type not in AIG_GATE_TYPES:
            return False
    return True


@pytest.mark.parametrize(
    'gate_type',
    [
        gate.AND,
        gate.GEQ,
        gate.GT,
        gate.LEQ,
        gate.LIFF,
        gate.LNOT,
        gate.LT,
        gate.NAND,
        gate.NOR,
        gate.NXOR,
        gate.OR,
        gate.RIFF,
        gate.RNOT,
        gate.XOR,
    ],
)
def test_aig_simple(gate_type: gate.GateType):
    """Test that each gate type converts to AIG correctly with preserved truth table."""
    C0 = (
        Circuit()
        .add_gate(gate.Gate('A', gate.INPUT))
        .add_gate(gate.Gate('B', gate.INPUT))
        .add_gate(gate.Gate('C', gate_type, ('A', 'B')))
    )
    C0.mark_as_output('C')

    C1 = copy.copy(C0)
    C1.into_aig()

    # Truth table should be preserved
    assert C0.get_truth_table() == C1.get_truth_table()
    # Result should only contain AIG gates
    assert _is_aig_circuit(C1)


def test_aig_not_gate():
    """Test that NOT gate (already AIG) is preserved."""
    C0 = (
        Circuit()
        .add_gate(gate.Gate('A', gate.INPUT))
        .add_gate(gate.Gate('B', gate.NOT, ('A',)))
    )
    C0.mark_as_output('B')

    C1 = copy.copy(C0)
    C1.into_aig()

    assert C0.get_truth_table() == C1.get_truth_table()
    assert _is_aig_circuit(C1)
    # NOT gate should still be present
    assert C1.has_gate('B')
    assert C1.get_gate('B').gate_type == gate.NOT


def test_aig_iff_buffer():
    """Test that IFF (buffer) gate is properly eliminated."""
    C0 = (
        Circuit()
        .add_gate(gate.Gate('A', gate.INPUT))
        .add_gate(gate.Gate('B', gate.IFF, ('A',)))
        .add_gate(gate.Gate('C', gate.AND, ('A', 'B')))
    )
    C0.mark_as_output('C')

    C1 = copy.copy(C0)
    C1.into_aig()

    assert C0.get_truth_table() == C1.get_truth_table()
    assert _is_aig_circuit(C1)
    # IFF gate should be eliminated
    assert not C1.has_gate('B')


def test_aig_iff_as_output():
    """Test that IFF gate as output is properly handled."""
    C0 = (
        Circuit()
        .add_gate(gate.Gate('A', gate.INPUT))
        .add_gate(gate.Gate('B', gate.IFF, ('A',)))
    )
    C0.mark_as_output('B')

    C1 = copy.copy(C0)
    C1.into_aig()

    assert C0.get_truth_table() == C1.get_truth_table()
    assert _is_aig_circuit(C1)
    # Output should now point to 'A' directly
    assert 'A' in C1.outputs


def test_aig_always_true():
    """Test that ALWAYS_TRUE is preserved as valid AIG gate."""
    C0 = (
        Circuit()
        .add_gate(gate.Gate('A', gate.INPUT))
        .add_gate(gate.Gate('B', gate.ALWAYS_TRUE))
    )
    C0.mark_as_output('B')

    C1 = copy.copy(C0)
    C1.into_aig()

    assert C0.get_truth_table() == C1.get_truth_table()
    assert _is_aig_circuit(C1)


def test_aig_always_false():
    """Test that ALWAYS_FALSE is preserved as valid AIG gate."""
    C0 = (
        Circuit()
        .add_gate(gate.Gate('A', gate.INPUT))
        .add_gate(gate.Gate('B', gate.ALWAYS_FALSE))
    )
    C0.mark_as_output('B')

    C1 = copy.copy(C0)
    C1.into_aig()

    assert C0.get_truth_table() == C1.get_truth_table()
    assert _is_aig_circuit(C1)


def test_aig_mixed_circuit():
    """Test conversion of a complex circuit with multiple gate types."""
    C0 = Circuit()

    C0.add_gate(gate.Gate('1', gate.INPUT))
    C0.add_gate(gate.Gate('2', gate.INPUT))
    C0.add_gate(gate.Gate('3', gate.NOT, ('1',)))
    C0.add_gate(gate.Gate('4', gate.AND, ('1', '2')))
    C0.add_gate(gate.Gate('5', gate.XOR, ('1', '2')))
    C0.add_gate(gate.Gate('6', gate.OR, ('2', '4')))
    C0.add_gate(gate.Gate('7', gate.NAND, ('3', '6')))
    C0.add_gate(gate.Gate('8', gate.NOR, ('5', '7')))
    C0.add_gate(gate.Gate('9', gate.NXOR, ('6', '8')))
    C0.add_gate(gate.Gate('10', gate.LEQ, ('2', '4')))
    C0.add_gate(gate.Gate('11', gate.LT, ('2', '10')))
    C0.add_gate(gate.Gate('12', gate.GEQ, ('10', '11')))
    C0.add_gate(gate.Gate('13', gate.GT, ('12', '9')))

    C0.mark_as_output('13')

    C1 = copy.copy(C0)
    C1.into_aig()

    assert C0.get_truth_table() == C1.get_truth_table()
    assert _is_aig_circuit(C1)


def test_aig_chain_of_buffers():
    """Test that a chain of IFF (buffer) gates is properly eliminated."""
    C0 = (
        Circuit()
        .add_gate(gate.Gate('A', gate.INPUT))
        .add_gate(gate.Gate('B', gate.IFF, ('A',)))
        .add_gate(gate.Gate('C', gate.IFF, ('B',)))
        .add_gate(gate.Gate('D', gate.IFF, ('C',)))
    )
    C0.mark_as_output('D')

    C1 = copy.copy(C0)
    C1.into_aig()

    assert C0.get_truth_table() == C1.get_truth_table()
    assert _is_aig_circuit(C1)
    # All IFF gates should be eliminated
    assert not C1.has_gate('B')
    assert not C1.has_gate('C')
    assert not C1.has_gate('D')


def test_aig_already_aig_circuit():
    """Test that a circuit already in AIG format is unchanged."""
    C0 = (
        Circuit()
        .add_gate(gate.Gate('A', gate.INPUT))
        .add_gate(gate.Gate('B', gate.INPUT))
        .add_gate(gate.Gate('C', gate.NOT, ('A',)))
        .add_gate(gate.Gate('D', gate.AND, ('C', 'B')))
    )
    C0.mark_as_output('D')

    C1 = copy.copy(C0)
    C1.into_aig()

    assert C0.get_truth_table() == C1.get_truth_table()
    assert _is_aig_circuit(C1)
    # Gates should still exist with same types
    assert C1.get_gate('C').gate_type == gate.NOT
    assert C1.get_gate('D').gate_type == gate.AND


def test_aig_block_preservation():
    """Test that blocks are updated when gates are added during AIG conversion."""
    C0 = (
        Circuit()
        .add_gate(gate.Gate('A', gate.INPUT))
        .add_gate(gate.Gate('B', gate.INPUT))
        .add_gate(gate.Gate('C', gate.OR, ('A', 'B')))
        .add_gate(gate.Gate('D', gate.AND, ('B', 'C')))
    )
    C0.mark_as_output('C')

    C0.make_block_from_slice('new_block', C0.inputs, ['C'])
    assert C0._blocks['new_block'].gates == ['C']

    C0.into_aig()
    # Block should now include the new gates created during conversion
    assert len(C0._blocks['new_block'].gates) > 1
    assert _is_aig_circuit(C0)
