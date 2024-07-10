import pandas as pd
import numpy as np
import salesHelpers.attractiveness as attr
class SalesRegistry:
    """
    Contains sales from all quarters.
    Attributes
    ----------
    data: pd.DataFrame
    Implements
    ----------
    - get_quarter(quarter:int) -> The sales DataFrame for the given quarter
    """
    def __init__(self, df:pd.DataFrame) -> None:
        self.data = df
    def get_quarter(self, quarter:int):
        return self.data.query(f'Quarter == {quarter}')
    
    def get_grades_sold(self, quarter, item):
        df = self.get_quarter(quarter)
        Std_array = pd.to_numeric(df[f'Std_{item}'], errors='coerce') # Coerce transforms the unconvertible values to Nan (useful is df is empty), 
        Dlx_array = pd.to_numeric(df[f'Dlx_{item}'], errors='coerce')
        grades_sold = np.unique(np.concatenate((Std_array, Dlx_array)))
        # print("Unique Grades Sold:")
        # print(grades_sold)  # Print the unique grades sold
        return np.unique(grades_sold[~np.isnan(grades_sold)])

    def get_n_grades_sold(self, quarter, item):
        grades_sold = self.get_grades_sold(quarter, item)
        # print(f"Grades sold for quarter {quarter} and item {item}: {grades_sold}")
        return len(grades_sold)
    def query(self, *args, **kwargs) -> pd.DataFrame:
        """
        Calls the `query()` method on the registry data DataFrame.

        Parameters
        ----------
        *args : tuple
            Positional arguments to pass to the `query()` method.
        **kwargs : dict
            Keyword arguments to pass to the `query()` method.

        Returns
        -------
        pd.DataFrame
            The result of the query operation on the registry data DataFrame.
        """
        return self.data.query(*args, **kwargs)

def get_current_market_demand(session, item:str,) -> np.ndarray:
# def get_current_market_demand(session, item:str,quarter:int) -> np.ndarray:
    assert item in ('X', 'Y')
    mkt = session.period_parameters.get_values(
        f'Mkt potential {item}', 
        periods = [session.quarter]
        # periods = [quarter]
        )
    
    return mkt

def get_num_sellers(session, item:str) -> int:
    parameter = 1
    n_std = len(np.unique(session.sales_registry.get_quarter(session.quarter).query(f"Std_{item}.notnull()")["Company"].values))
    n_dlx = len(np.unique(session.sales_registry.get_quarter(session.quarter).query(f"Dlx_{item}.notnull()")["Company"].values))
    

    return n_std + parameter*n_dlx



def get_total_market_demand(session, item:str) -> np.ndarray:
    # Returns the total market demand following this function : 
    # TotMktDemand(perPA)=n*PlCap*MktClimateF*GradesSoldF*TotAdvF
    # Where GradesSoldF is : 
    # GradesSoldF=(∑_(i=0)^G▒〖(Y=1,N=0)*〖Demand〗_i 〗)/NumberGradesSold*(NumberGradesSold+1)/2


    PlCap = get_current_market_demand(session, item)
    
    n = get_num_sellers(session, item )
    NgradesSold = session.sales_registry.get_n_grades_sold(session.quarter, item)
    GradesSold = session.sales_registry.get_grades_sold(session.quarter, item)

    MktClimateF = session.period_parameters.get_values(
        'Market climate factor',
        periods = [session.quarter]
    )/100
    # print(f"PlCap: {PlCap}")
    # print(f"Number of sellers (n): {n}")
    # print(f"Number of grades sold (NgradesSold): {NgradesSold}")
    # print(f"Grades sold (GradesSold): {GradesSold}")
    # print(f"Market climate factor (MktClimateF): {MktClimateF}")
    per_grade_demands = []
    for i in range(0,10):
        if i in GradesSold:
            grade_demand = session.period_parameters.get_values(
                f'Product Cycle {item}{i}', 
                session.quarter
                )/100 #Percentage of item 0
            per_grade_demands.append(grade_demand)
    
    AvgDemandInGradesSold =np.mean(per_grade_demands) if per_grade_demands else 0 # As a percentage of Item 0 demand
    # print(f"Average demand in grades sold (AvgDemandInGradesSold): {AvgDemandInGradesSold}")

    GradeSoldF = AvgDemandInGradesSold * (NgradesSold + 1)/2
    # print(f"Grade Sold Factor (GradeSoldF): {GradeSoldF}")


    totalAdvAmount = np.sum(session.sales_registry \
                                .get_quarter(session.quarter)[f'Advertising_{item}'] \
                                .values)
    #TODO : Move advertissement coeff to parameters sheet
    
    if n == 0 :
        return 0
    else :
        ADVERTISSEMENT_COEFF = 0.25 * (1/50000) * 1/n
        # print(f"Advertisement Coefficient (ADVERTISSEMENT_COEFF): {ADVERTISSEMENT_COEFF}")
        TotAdvF = 1 + ADVERTISSEMENT_COEFF * totalAdvAmount if not np.isnan(totalAdvAmount) else 1
        # print(f"Total advertisement amount: {totalAdvAmount}")
        # print(f"Total advertisement factor: {TotAdvF}")
        # print(f"Total Market Demand: {n * PlCap * MktClimateF * GradeSoldF * TotAdvF}")

        # return n * PlCap * MktClimateF * GradeSoldF * TotAdvF
        return n * PlCap * MktClimateF *  TotAdvF

# def get_specific_market_demands(session, item:str, quarter:int) -> np.ndarray:
def get_specific_market_demands(session, item:str) -> np.ndarray:
    """
    Computes the specific market for all grades of a given item.

    Returns
    -------
    demand: np.ndarray
        a sparse array of shame [demandX0, demandX1, .... demand Xn]
    """
    global_market = get_total_market_demand(session, item)
    # print("Calculating specific market demands...")
    # print("Global market demand:", global_market)
    # global_market = get_total_market_demand(session, item,  quarter)
    attractivenesses = np.array([session.period_parameters.get_values(
                        f'Product Cycle {item}{i}',
                        session.quarter
                        # quarter
                        ) for i in range(0,10)
                        ])
    # print("Attractivenesses:", attractivenesses)
    n_sellers = np.array([len(np.unique(session.sales_registry \
                 .get_quarter(session.quarter)\
                 .query(f"Std_{item} == {i} or Dlx_{item} == {i}")["Company"]))

                 for i in range(0,10)
                    ])
    # print("Number of sellers for each grade:", n_sellers)
    a = [n_sellers[i]*attractivenesses[i] for i in range(0,10)]
    # print("Intermediate calculation 'a':", a)
    b = sum(n_sellers*attractivenesses)
    # print("Intermediate calculation 'b':", b)

    # Handling a case with no seller
    if b >0 :
        specific_markets = (a/b * global_market).astype(int)
    else: 
        specific_markets =  np.zeros_like(a)
    # print("Specific markets:", specific_markets)

    return np.array(specific_markets)

def get_companies_goodwill(session)-> dict:
    """
    Returns the goodwill index for each company under a dictionary.
    Returns
    -------
    goodwills: dict
        Company_{03d:id}

    """
    # print("Calculating companies' goodwill...")
    goodwills = {f"Company_{company.id:02d}": company.stockouts for company in session.marketPlayers}
    # print("Goodwills:", goodwills)
    
    return goodwills

def get_specific_market_shares(session, item:str, grade:int) -> dict:
    # Needs : goodwill, price difference wrt others, optimal_price_distance
    """
    Retrieves the marketshare for all companies given an item and a grade
    Returns
    -------
    markeshares: dict
        a dictionary of structure {Company_{id:02d}: int(marketshare)}
    
    """

    marketShares = {}
    for company in session.marketPlayers:
        goodwillF = attr.get_goodwill_factor(company)
        wholeSalerF = attr.get_wholesaler_factor(company, session.period_parameters.get_values('Wholesaler bonus', session.quarter))
        priceDifferenceF = attr.get_price_change_factor(session, company.id, item, grade,
                                                        session.period_parameters.get_values('Price change factor', session.quarter))
        
        priceDifferenceF = attr.get_price_change_factor(session, company.id, item, grade, priceDifferenceF)
        # print(f"Price Difference Factor: {priceDifferenceF}")
        priceOptimalityF = attr.get_price_optimality_factor(session, company.id, item, grade,
                                                            session.period_parameters.get_values('Price optimality factor', session.quarter))
       
        # print(f"Priceoptimality Value: {priceOptimalityF}")
        
        priceCompetitivenessF = attr.get_price_competitiveness_factor(session, company.id, item, grade, 
                                                                      session.period_parameters.get_values("Competitiveness factor", session.quarter))
        
        # print(f"Price Competitiveness Factor Value: {priceCompetitivenessF}")

       

        marketShares[f"Company_{company.id:02d}"] = goodwillF * wholeSalerF * priceDifferenceF *  priceOptimalityF * priceCompetitivenessF
        # print(" marketShares",goodwillF * wholeSalerF * priceDifferenceF * priceOptimalityF * priceCompetitivenessF)
    
    # print("likelyhood_to_probabilities",likelyhood_to_probabilities(marketShares))

    return  likelyhood_to_probabilities(marketShares)

def get_market_shares(session):
    """
    Returns the marketshares for each grade, item and company
    """
    market_shares_dict = {}
    
    for item in ('X', 'Y'):
        market_shares_dict[item] = {}
        # print(f"Calculating market shares for item {item}")
        for grade in range(0,10):
            market_shares_dict[item][grade] = get_specific_market_shares(session, item, grade)
            # print(f"Market shares for item {item}, grade {grade}: {market_shares_dict[item][grade]}")

    return market_shares_dict

def run_sales_protocol(inventories:np.ndarray, specific_market_shares:np.ndarray, specific_grade_demand:int):
    """
    Parameters
    ----------
    inventories: np.ndarray
        An array indexed by the company ID and giving the integer number of items available in it's inventory
    specific_market_shares: np.ndarray
        An array of probabilities of reaching a consumer in the specific market, indexed by the company id.
    specific_grade_demand: int
        The gross demand for the specific market (i.e for the given 'X' and 'Y')

    Returns
    -------
    specific_market_potential: np.ndarray
        The number of sales that will be done by each company for the given item at the given grade

    Example
    -------
    With inputs : inventories = [10 000, 4 000, 4 000, 0], specific_market_shares = [0, 0.8, 0.2, 0], specific_grade_demand = 5 000
        --> specific_market_shares = [0, 4 000, 1 000, 0]
        --> I.e Company 1 sells 0 units of Y3s, Company 2 sells 10 000 units, Company 3 sells 8 000 and Company 4 sells 0
    """
    specific_market_potential = specific_grade_demand * specific_market_shares
    # print(f"Specific market potential: {specific_market_potential}")

    excess_indices = np.where(inventories < specific_market_potential)
    # print(f"Excess indices: {excess_indices}")
    shortage_indices = np.where(inventories > specific_market_potential)
    # print(f"Shortage indices: {shortage_indices}")

    excess_units = np.sum((specific_market_potential - inventories)[excess_indices])
    # print(f"Excess units: {excess_units}")
    
    if not np.any(shortage_indices):
        # print("No shortages detected.")
        # Remove all excesses ; and quit
        specific_market_potential = np.where(specific_market_potential < inventories, specific_market_potential, inventories)
        # print("Shortages detected.")
    else : 
        shortage_units = np.sum((inventories - specific_market_potential)[shortage_indices])
        # print(f"Shortage units: {shortage_units}")
        remaining_units = min(excess_units, shortage_units)
        # print(f"Remaining units: {remaining_units}")

        new_specific_market_shares = np.zeros_like(specific_market_shares)
        new_specific_market_shares[shortage_indices] = specific_market_shares[shortage_indices]
        # print("new_specific_market_shares",new_specific_market_shares)

        # Normalize new_specific_market_shares to probabilities
        total_new_market_shares = np.sum(new_specific_market_shares)
        if total_new_market_shares > 0:
            new_specific_market_shares /= total_new_market_shares

        new_market_potential = remaining_units * new_specific_market_shares
        # if  total_new_market_shares > 0:
        #     new_market_potential = specific_grade_demand * (specific_market_shares /  total_new_market_shares)
        # else:
        #     new_market_potential = np.zeros_like(specific_market_shares)

        # print(f"New market potential: {new_market_potential}")

        specific_market_potential = np.where(specific_market_potential < inventories, specific_market_potential, inventories)
        specific_market_potential += new_market_potential
        # print(f" specific_market_potential at the end: {new_market_potential}")

       
    # print("Calculation complete.")

    return np.array(specific_market_potential, dtype=int)
 
#########
#Helpers#
#########

def likelyhood_to_probabilities(dictionary: dict) -> dict:
    """
    Transforms likelihood values in a dictionary into probabilities.

    Args:
        dictionary (dict): A dictionary with string keys and positive float values representing likelihood.

    Returns:
        dict: A new dictionary with string keys and positive float values representing probabilities. If all
        input values are zeros, the function returns a new dictionary with zeros for all values.

    Examples:
        >>> my_dict = {
        ...     "A": 0.5,
        ...     "B": 0.3,
        ...     "C": 0.2
        ... }
        >>> transformed_dict = likelyhood_to_probabilities(my_dict)
        >>> print(transformed_dict)
        {'A': 0.5, 'B': 0.3, 'C': 0.2}

        >>> my_dict2 = {
        ...     "X": 0,
        ...     "Y": 0,
        ...     "Z": 0
        ... }
        >>> transformed_dict2 = likelyhood_to_probabilities(my_dict2)
        >>> print(transformed_dict2)
        {'X': 0, 'Y': 0, 'Z': 0}

    Raises:
        TypeError: If the input dictionary is not a valid dictionary.

    Note:
        The values in the transformed dictionary represent probabilities that sum up to 1, except when all input
        values are zeros. In that case, the function returns a new dictionary with zeros for all values.

    """
    total_sum = sum(dictionary.values())

    if total_sum == 0:
        transformed_dict = {key: 0 for key in dictionary.keys()}
    else:
        transformed_dict = {key: value / total_sum for key, value in dictionary.items()}

    return transformed_dict