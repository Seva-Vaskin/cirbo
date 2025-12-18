import typing as tp

from cirbo.core.circuit import Circuit


__all__ = ['Cnf', 'Lit', 'Clause', 'CnfRaw', 'VarMap']


Lit = int
Clause = list[Lit]
CnfRaw = list[Clause]
VarMap = dict[str, Lit]


class Cnf:
    """Structure to store CNF formula."""

    @staticmethod
    def from_circuit(circuit: Circuit) -> 'Cnf':
        """
        Converts circuit to CNF by Tseytin transformation and returns CNF.

        :param circuit: Circuit what will be converted to cnf.

        """
        from cirbo.sat.cnf.tseytin import tseytin_transformation

        return tseytin_transformation(circuit)

    def __init__(
        self,
        cnf: tp.Optional[CnfRaw] = None,
        var_map: tp.Optional[VarMap] = None,
    ):
        """

        :param cnf: CNF can be not assigned, it means cnf is empty.
        :param var_map: Optional mapping from variable labels to variable numbers.
        """
        if cnf is None:
            self._cnf = []
        else:
            self._cnf = cnf
        self._var_map: VarMap = var_map if var_map is not None else {}

    def add_clause(self, clause: Clause):
        """
        Add clause to CNF.

        :param clause: new clause.

        """
        self._cnf.append(clause)

    def get_raw(self) -> CnfRaw:
        """Returns CnfRaw object."""
        return self._cnf

    @property
    def var_map(self) -> VarMap:
        """Returns mapping from variable labels to variable numbers."""
        return self._var_map

    def get_var(self, label: str) -> tp.Optional[Lit]:
        """Get variable number by label."""
        return self._var_map.get(label)
