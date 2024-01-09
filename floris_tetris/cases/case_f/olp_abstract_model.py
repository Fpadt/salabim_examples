import pyomo.environ as pyo
from pyomo.opt import SolverFactory, SolverStatus, TerminationCondition


def create_model_TGC(
    m: int,
    n: int,
    alpha: float,
    beta: float,
    gamma: float,
) -> pyo.ConcreteModel:
    """
    Create the TGC model.

    Parameters
    ----------
    m : int
        Number of EVSEs.
    n : int
        Number of time periods.
    alpha : float
        EVSE efficiency.
    beta : float
        Customer satisfaction.
    gamma : float
        Cost of energy.

    Returns
    -------
    pyo.ConcreteModel
        The model object.
    """
    # --------------------------------------------------------------------------
    # TGC: Tetris Game Charger
    # --------------------------------------------------------------------------

    # --------------------------------------------------------------------------
    # Abstract Models
    # https://pyomo.readthedocs.io/en/stable/pyomo_overview/simple_examples.html#a-simple-abstract-pyomo-model
    # --------------------------------------------------------------------------

    TGC = pyo.AbstractModel()

    # --------------------------------------------------------------------------
    # Sets
    # https://pyomo.readthedocs.io/en/stable/pyomo_modeling_components/Sets.html
    # note: pyomo uses 1-based indexing, these sets are fixed
    # the first value and step size default to 1
    # --------------------------------------------------------------------------

    TGC.I = pyo.RangeSet(m, doc="fixed set of EVSEs")
    TGC.J = pyo.RangeSet(n, doc="fixed set of time periods for a certain horizon (h=5)")

    # --------------------------------------------------------------------------
    # Parameters
    # https://pyomo.readthedocs.io/en/stable/pyomo_modeling_components/Parameters.html
    # note: pyomo uses 1-based indexing, these parameters are all mutable
    # --------------------------------------------------------------------------

    # energy price per kWh for each time period
    TGC.energy_price = pyo.Param(TGC.J, default=0, mutable=True, within=pyo.Reals)

    # enexis max Power output for each time period (constant)
    TGC.enexis = pyo.Param(TGC.J, default=0, mutable=True, within=pyo.NonNegativeReals)

    # max Power EVSE session for each time period
    TGC.session = pyo.Param(
        TGC.I, TGC.J, default=0, mutable=True, within=pyo.NonNegativeReals
    )

    # remaining charge for each session
    TGC.remaining_charge = pyo.Param(
        TGC.I, default=0, mutable=True, within=pyo.NonNegativeReals
    )

    # time period length for each time period
    TGC.pt = pyo.Param(TGC.J, default=0, mutable=True, within=pyo.NonNegativeReals)

    # weight for each time period
    TGC.w = pyo.Param(TGC.J, default=0, mutable=True, within=pyo.NonNegativeReals)

    # --------------------------------------------------------------------------
    # Variables
    # https://pyomo.readthedocs.io/en/stable/pyomo_modeling_components/Variables.html
    # --------------------------------------------------------------------------

    TGC.x = pyo.Var(TGC.I, TGC.J, domain=pyo.NonNegativeReals)

    # --------------------------------------------------------------------------
    # Objective function
    # https://pyomo.readthedocs.io/en/stable/pyomo_modeling_components/Objectives.html
    # --------------------------------------------------------------------------

    def obj_expression(TGC) -> float:
        """
        Objective function for the TGC problem.

        Parameters
        ----------
        model : pyomo.environ.ConcreteModel
            The model object.

        Returns
        -------
        float
            The objective value.
        """

        return (
            alpha
            * sum(
                TGC.w[j] * (1 - sum(TGC.x[i, j] for i in TGC.I) / TGC.enexis[j])
                for j in TGC.J
            )
            + beta
            * sum(
                (
                    1
                    - sum(TGC.pt[j] * TGC.x[i, j] for j in TGC.J)
                    / TGC.remaining_charge[i]
                )
                for i in TGC.I
            )
            / m
            + (
                gamma
                / sum(TGC.energy_price[j] * TGC.pt[j] * TGC.enexis[j] for j in TGC.J)
            )
            * sum(
                (TGC.energy_price[j] * TGC.pt[j] * sum(TGC.x[i, j] for i in TGC.I))
                for j in TGC.J
            )
        )

    TGC.OBJ = pyo.Objective(rule=obj_expression)

    # --------------------------------------------------------------------------
    # Constraints
    # https://pyomo.readthedocs.io/en/stable/pyomo_modeling_components/Constraints.html
    # https://pyomo.readthedocs.io/en/stable/pyomo_modeling_components/Expressions.html
    # --------------------------------------------------------------------------

    def ex_grid_constraint_rule(TGC, j) -> float:
        """
        Constraint: Total power of all EVSEs in a time period (j)
        must be less than or equal to the maximum power output of the grid.

        Parameters
        ----------
        model : pyomo.environ.ConcreteModel
            The model object.
        j : int
            The time period.
        """
        return sum(TGC.x[i, j] for i in TGC.I) <= TGC.enexis[j]

    def session_constraint_rule(TGC, i, j) -> float:
        """
        Constraint: Power of EVSE (i) in a time period (j)
        must be less than or equal to the maximum power input of the EVSE.

        Parameters
        ----------
        model : pyomo.environ.ConcreteModel
            The model object.
        i : int
            The EVSE.
        j : int
            The time period.
        """
        return TGC.x[i, j] <= TGC.session[i, j]

    def deschrg_constraint_rule(TGC, i) -> float:
        """
        Constraint: Final charge of EVSE (i) must be less than or equal to
        the desired (realistic) charge of the EVSE.

        Parameters
        ----------
        model : pyomo.environ.ConcreteModel
            The model object.
        i : int
            The EVSE.
        """
        return sum(TGC.pt[j] * TGC.x[i, j] for j in TGC.J) <= TGC.remaining_charge[i]

    # the next line creates one constraint for each member of the set model.J
    TGC.Ex_Grid_Constraint = pyo.Constraint(TGC.J, rule=ex_grid_constraint_rule)
    TGC.DesChrg_Constraint = pyo.Constraint(TGC.I, rule=deschrg_constraint_rule)
    TGC.Session_Constraint = pyo.Constraint(TGC.I, TGC.J, rule=session_constraint_rule)

    # --------------------------------------------------------------------------
    # create a model instance
    # https://pyomo.readthedocs.io/en/stable/working_abstractmodels/instantiating_models.html
    # https://link.springer.com/book/10.1007/978-3-030-68928-5
    # --------------------------------------------------------------------------

    return TGC.create_instance()


def set_tgc_energy_price(tgc, EnergyPrice):
    """
    Set the energy price for each time period.

    Parameters
    ----------
    tgc : pyomo.environ.ConcreteModel
        The model object.
    EnergyPrice : list
        List of energy prices for each time period.
    """
    for j in tgc.J:
        tgc.energy_price[j].value = EnergyPrice[j - 1]


def set_tgc_session_max_power(tgc, EVSE):
    """
    Set the maximum power for each EVSE for each time period.

    Parameters
    ----------
    tgc : pyomo.environ.ConcreteModel
        The model object.
    EVSE : list
        List of maximum power for each EVSE for each time period.
    """
    for i in tgc.I:
        for j in tgc.J:
            tgc.session[i, j].value = EVSE[i - 1, j - 1]


def set_tgc_remaining_charge(tgc, remaining_charge):
    """
    Set the remaining charge for each EVSE.

    Parameters
    ----------
    tgc : pyomo.environ.ConcreteModel
        The model object.
    remaining_charge : list
        List of remaining charge for each EVSE.
    """
    for i in tgc.I:
        tgc.remaining_charge[i].value = remaining_charge[i - 1]


def set_tgc_enexis_max_power(tgc, EX_MPO):
    """
    Set the maximum power for the Enexis grid for each time period.

    Parameters
    ----------
    tgc : pyomo.environ.ConcreteModel
        The model object.
    EX_MPO : float
        Maximum power for the Enexis grid for each time period.
    """
    for j in tgc.J:
        tgc.enexis[j].value = EX_MPO


def set_tgc_pt(tgc, pt):
    """
    Set the time period length for each time period and the weights.

    Parameters
    ----------
    tgc : pyomo.environ.ConcreteModel
        The model object.
    pt : list
        List of time period length for each time period.
    """
    for j in tgc.J:
        tgc.pt[j].value = pt[j - 1]
        tgc.w[j].value = pt[j - 1] / np.sum(pt)