#########################################
# B2B Expeditions, receptions and risks #
#########################################

def risk_expediting(session) -> dict:
    """
    Checks for each company in the session the airfreight risk_expediting:\n
    If inventory is negative for a grade, then the grade and value are remembered and the quantities set back to 0.

    Returns
    -------
    risk_dict: dict
        Contains the remembered inventory negatives : [Company{ID}][item]['grades', 'quantities'\n
        # Where grades and quantities are lists of integers.\n
        NB : Returned dict is likely unused.
    """
    risk_dict = {}
    for company in session.marketPlayers:
        identifier = f"Company{company.id}"
        company_risk_dict = {}
        for item in ("X", "Y"):
            lst = [(i,-q) for i,q in enumerate(company.get_inventory(item))if q<0]
            if lst:
                grades, quantities = zip(*lst)
                company_risk_dict[item] = {"Grades":list(grades), "Quantities":list(quantities)}
                for g,q in zip(grades, quantities):
                    company.inventory.add(item, grade=g, quantity=q)
        if company_risk_dict:
            risk_dict[identifier] = company_risk_dict

    return risk_dict

def airfreight_out(session) -> None:
    """
    Processes the airfreight out and updates inventories.\n
    This corresponds to the outgoing airfreight at the begining of each quarter.
    """
    currentQ = session.quarter
    cur_registry = session.transactions.get_quarter(currentQ)
    for company in session.marketPlayers:
        # Gathering sells from that company
        sells = cur_registry.query(f"Seller == {company.id} & (`Air / Surface`) == 'Air'").loc[:, ["Product", "Grade", "Volume"]] \
                       .groupby(['Product', 'Grade']).sum().reset_index()
        # Updating its inventory
        for product, grade, volume in sells.values:
            company.inventory.remove(product, grade, volume)

def airfreight_in(session) -> None:
    """
    Processes the airfreight_in and updates the inventories.
    This corresponding to incoming airfreiht at the begining of each quarter.
    """
    currentQ = session.quarter
    cur_registry = session.transactions.get_quarter(currentQ)
    for company in session.marketPlayers:
        # Gathering purchases from that company
        purchases = cur_registry.query(f"Buyer == {company.id} & (`Air / Surface`) == 'Air'").loc[:, ["Product", "Grade", "Volume"]] \
                       .groupby(['Product', 'Grade']).sum().reset_index()
        for product, grade, volume in purchases.values:
            company.inventory.add(product, grade, volume)

def surface_out(session) -> None:
    """
    Processes the surface freight out and updates inventories. \n
    This corresponds to outgoing freight at the begining of each quarter.
    """
    currentQ = session.quarter
    cur_registry = session.transactions.get_quarter(currentQ)
    for company in session.marketPlayers:
        # Gathering sells from that company
        sells = cur_registry.query(f"Seller == {company.id} & (`Air / Surface`) == 'Surface'").loc[:, ["Product", "Grade", "Volume"]] \
                       .groupby(['Product', 'Grade']).sum().reset_index()
        # Updating its inventory
        for product, grade, volume in sells.values:
            company.inventory.remove(product, grade, volume)

def surface_in(session) -> None:
    """
    Processes the surface_in and updates the inventories. \n
    This corresponding to incoming surface freight recieved at the end of each quarter.
    """
    currentQ = session.quarter
    cur_registry = session.transactions.get_quarter(currentQ)
    for company in session.marketPlayers:
        # Gathering purchases from that company
        purchases = cur_registry.query(f"Buyer == {company.id} & (`Air / Surface`) == 'Surface'").loc[:, ["Product", "Grade", "Volume"]] \
                       .groupby(['Product', 'Grade']).sum().reset_index()
        for product, grade, volume in purchases.values:
            company.inventory.add(product, grade, volume)
