import numpy as np

def get_goodwill_factor(company):
    """"""
    return company.goodwill 
def get_wholesaler_factor(company, wholesaler_bonus):
    return 1 if company.wholeSaler == False else wholesaler_bonus
def get_price_competitiveness_factor(session, cid:int, item:str, grade:int, impact = 1):
    """
    Computes the factor resulting from the difference between the posted price and the average posted price by all companies.
    Sigmoid introduces non-linearities.

    Parameters
    ----------
    session: Session
        The current running session
    cid: int
        The company id
    item: str
        Either `X`or `Y`
    grade: int
        The grade of the item
    impact: float
        A positive number representing the impact of the price competitiveness
    
    Returns
    -------
    factor: float
        1 - parameter * sigmoid(own_price / avg_price)
    """
    
    assert 0<impact , ValueError("Parameter `impact` should be a positive float. Default value: 1")

    registry = session.sales_registry.get_quarter(session.quarter)

    # Retrieve matching posted prices in both standards
    prices_for_standards = []
    for standard in ("Std", "Dlx"):
        prices_for_standards.append(registry.query(f"{standard}_{item} == {grade}")[f"Price_{standard}_{item}"].values)

    # Retrieve own price
    own_price = get_written_price(session, cid, item, grade)
    if own_price == 0 : return 0
    
    # Compute average
    avg_price = np.average(np.concatenate(prices_for_standards))

    # Compute factor
    sig = sigmoid((avg_price - own_price)/avg_price)
    redressed_sigmoid = sig - 0.5
    res =  1 + impact * redressed_sigmoid
    if res[0] == None:
        return 0
    return res

def get_price_optimality_factor(session, cid:int, item:str, grade:int, impact:float=1) -> float:
    """ Returns the price optimality factor : translates how close the price is to the optimal price with respect to the product cycle and base brice.
    Parameters
    ----------
    session: Session
        The current running session
    cid: int
        The company id of the company posting the price
    item: str
        Either "X" or "Y"
    grade: int
        The grade of the concerned grade
    impact: float
        A positive float, hyperparameter, related to how impactful is price optimality on the final factor.
    """
    
    assert 0< impact, ValueError("Impact should be a positive float. Default : 1.")

    base_price = session.period_parameters.get_values(f"Optimum price {item}0", [session.quarter])
    price_multiplier = session.period_parameters.get_values(f"Product Cycle {item}{grade}", [session.quarter]) # From the grade cycle with respect to grade 0
    optimal_price = base_price * price_multiplier/100

    written_price = get_written_price(session, cid, item, grade)
    price_difference = abs(written_price - optimal_price) / optimal_price

    return 1 - impact * price_difference

def get_price_change_factor(session, cid:int ,item:str, grade:int, impact:float) -> float:
    """
    Takes into account the price change factor from one quarter to an other.
    Price_change_factor is parametrizable in Data.xlsx.

    Returns
    -------
    factor: int
        Worth 1 if price difference is irrelevant (eg. previous price doesn't exist), \n
        Or worth 1 - parameter * (% of difference) when applicable.
    cid: int
        The id of the company
    item: str
        Either `X`or `Y`.
    grade: int
        The grade of the item
    impact: float
        A positive number related to how impactful is the price change on the final factor.
    """

    # If only 1 or no quarter have elapsed, it is impossible to compute the difference
    if session.quarter <= 2:
        return 1
    # Retrieve both prices
    previous_price = get_written_price(session, cid, item, grade, session.quarter -1)
    current_price = get_written_price(session, cid, item, grade, session.quarter)

    if previous_price == 0 or current_price == 0:
        return 1
    
    else:
        return 1 - impact * abs(previous_price - current_price)/100

#########
# Helper#
#########
def get_written_price(session, cid:int, item:str, grade:int, quarter:int = None) -> int:
    """
    Given a company, a session, and item and its grade, returns the posted price by the company.
    If quarter is not specified, data for current quarter is returned.

    Returns
    -------
    price_posted: int
        The price posted by the company for the specified item in the current quarter
    """
    if quarter == None :
       quarter = session.quarter

    current_registry = session.sales_registry.get_quarter(session.quarter)
    # Attempt to retrieve price from Std
    price_posted = current_registry.query(f"Std_{item} == {grade} and Company == {cid}")[f"Price_Std_{item}"].values.astype(int)
    # If not found, retrieve from Dlx
    if not any(price_posted):
        price_posted = current_registry.query(f"Dlx_{item} == {grade} and Company == {cid}")[f"Price_Dlx_{item}"].values.astype(int)

    if not any(price_posted):
        price_posted = np.array(0)

    return price_posted

def sigmoid(x):
    return 1.0 / (1 + np.exp(-x))
