import os
import pandas as pd


class ProductionRegistry:
    """
    Stores all production decisions from all quarters.\n
    Implements
    ----------
    - get_current_registry(quarter) -> pd.DataFrame
    - get_company_registry(companyID) -> pd.DataFrame
    """
    def __init__(self, file_path:os.PathLike) -> None:
        self.registry = pd.read_excel(file_path, sheet_name='Production')
    def get_data(self):
        return self.registry
    def get_current_registry(self, quarter:int) -> pd.DataFrame:
        return self.registry.query(f"Quarter == {quarter}").reset_index()
    def get_company_registry(self, cid:int) -> pd.DataFrame:
        return self.registry.query(f"Company == {cid}").reset_index()

def produce_X(company, decision) -> None:
    """
    Purpose
    -------
    Produces the item `X` from the given company if the given decision can be taken.\n
    Details
    -------
    - If the requested grade is higher than available, then production is cancelled
    - If the requested volume is too high, then only maximum volume will be produced.
    """
    item = 'X'
    factory_index = decision["Factory"] # can be either 1,2 or 3
    max_volume = company.factories.get_factories_production(item)[factory_index -1]
    max_grade = company.max_grades[item]
    requested_grade = decision["Grade"]
    requested_volume = decision["Volume"]
    production_volume = requested_volume if requested_volume <= max_volume else max_volume
    if requested_grade > max_grade: production_volume = 0 # If grade is unavailable, production is cancelled

    company.prod_inventory.add(item,requested_grade, production_volume )
    
def produce_Y(company, decisions, grid, quarter) -> None:
    """
    Purpose
    -------
    Produce Y products according to preferences for the company and stores production in company.prod_inventory whenever possible.

    Details
    -------
    - A non possible grade will not be produced
    - An escessive production will be scaled down to the maximum supported by the factory
    """
    item = 'Y'
    preference = decisions.head(1)["Preference"].values
    usage_records = []
    # ascending = False means Std decisions will be first
    # That is the case for Std for Std (1) or Std for Dlx (3)
    ascending_order = False if preference in [1, 3] else True
    decisions = decisions.sort_values(by='Standard', inplace=False, ascending=ascending_order)
    total_X_used = {}
    
 
    for _, decision in decisions.iterrows():
        if decision["Grade"] > company.max_grades[item] : continue
        try :
            max_volume = company.factories.get_factories_production(item)[decision["Factory"] -1]
        except IndexError:
            raise IndexError("Likely cause : factory not found. Ensure factory exists.")
        
        if max_volume < decision["Volume"]: decision["Volume"] = max_volume

        if preference == 1:
            X_usage = prod_with_Std_priority(company, decision, grid)
            # Std for Std
            # prod_with_Std_priority(company, decision, grid)
        elif preference == 2:
            # Dlx for Dlx
            X_usage = prod_with_Dlx_priority(company, decision, grid)
        elif preference == 3:
            # Dlx for Std
            X_usage = prod_with_Dlx_priority(company, decision, grid)
        elif preference == 4:
            # Std for Dlx
            X_usage = prod_with_Std_priority(company, decision, grid)
            
        # total_X_used += sum(X_usage.values())
        
        
        if X_usage is None:
            X_usage = {}  # Ensure X_usage is always a dictionary
       
        for grade, qty in X_usage.items():
            grade = str(grade)
            if grade not in total_X_used:
                total_X_used[grade] = 0
            total_X_used[grade] += qty
        print(f"Quarter {quarter}, Company {company.id}:")
        print(f" Company {company.id}, Production of Y{decision['Grade']}:")
        for grade, qty in X_usage.items():
            print(f"  - Grade X{grade} used: {qty}")
        print("")
        
   
        
        
    #print(f"Total X used in the production of Y: {total_X_used}")
    
    # print(f" Company {company.id}: Total X used in the production of Y: {total_X_used}")
    
    

################################################
# Implementing the production preferences #
################################################
def prod_with_Std_priority(company, decision, grid) -> None:
    """
    Production method: uses in priority Std chips for Std products.
    Details
    -------
    - If Std X is not enough, uses Dlx X for Std Y.
    - If Std X is left, Std X is used in priority for Dlx Y.
    """
    
    inventory = company.get_dict_inventory()
    X_usage = {}
    X_std = inventory["X"]["Std"]["Grade"]
    X_std_qty = inventory["X"]["Std"]["Value"]

    if X_std is None:
        return  X_usage  # Case inventory is empty -> No production

    ratio = grid.get_compatibility(X_std, decision["Grade"])
    print("ratio", ratio)
    max_prod_qty = min(X_std_qty // ratio, decision["Volume"])
    

    company.inventory.remove("X", X_std, max_prod_qty * ratio)
    company.prod_inventory.add("Y", decision["Grade"], max_prod_qty)
    # added
    X_usage[X_std] = max_prod_qty * ratio
    

    remaining_prod = decision["Volume"] - max_prod_qty

    if remaining_prod > 0:
        X_dlx = inventory["X"]["Dlx"]["Grade"]
        X_dlx_qty = inventory["X"]["Dlx"]["Value"]

        if X_dlx is None:
            return X_usage

        dlx_ratio = grid.get_compatibility(X_dlx, decision["Grade"])
        max_prod_qty = min(X_dlx_qty // dlx_ratio, remaining_prod)
        company.inventory.remove("X", X_dlx, max_prod_qty * dlx_ratio)
        company.prod_inventory.add("Y", decision["Grade"], max_prod_qty)
        # added
        X_usage[X_dlx] = max_prod_qty * dlx_ratio
        
    return X_usage

def prod_with_Dlx_priority(company, decision, grid) -> None:
    """
    Production method: uses in priority Dlx chips for Dlx products.
    Details
    -------
    - If Dlx X is not enough, uses Std X for Dlx Y
    - If Dlx X is left, Dlx X is used in priority for Std Y
    """
    X_usage = {}
    inventory = company.get_dict_inventory()
    X_dlx, X_std = inventory["X"]["Dlx"]["Grade"], inventory["X"]["Std"]["Grade"]
    X_dlx_qty = inventory["X"]["Dlx"]["Value"]

    if X_dlx is None and X_std is None:
        return X_usage

    ratio = grid.get_compatibility(X_dlx, decision["Grade"]) if X_dlx_qty > 0 else 1

    max_prod_qty = min(X_dlx_qty // ratio, decision["Volume"])

    company.inventory.remove("X", X_dlx, max_prod_qty * ratio)
    company.prod_inventory.add("Y", decision["Grade"], max_prod_qty)
    # added
    X_usage[X_dlx] = max_prod_qty * ratio
    

    remaining_prod = decision["Volume"] - max_prod_qty

    if remaining_prod > 0:
        X_std = inventory["X"]["Std"]["Grade"]
        X_std_qty = inventory["X"]["Std"]["Value"]

        if X_std is None:
            return X_usage

        std_ratio = grid.get_compatibility(X_std, decision["Grade"])
        max_prod_qty = min(X_std_qty // std_ratio, remaining_prod)

        company.inventory.remove("X", X_std, max_prod_qty * std_ratio)
        company.prod_inventory.add("Y", decision["Grade"], max_prod_qty)
        
        # added
        
        X_usage[X_std] = max_prod_qty * std_ratio
