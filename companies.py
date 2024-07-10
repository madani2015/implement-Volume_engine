from typing import Any
import pandas as pd
import numpy as np

from production import produce_X, produce_Y
from factories import Factories

class Company:
    """
    Represents a company with inventory and factories.

    Attributes
    ----------
    name : str
        The name of the company.
    id : Any
        The identifier of the company.
    inventory : Inventory
        The inventory of the company.
    prod_inventory : Inventory
        The production inventory of the company.
    sales : Inventory
        The sales inventory of the company.
    factories : Factories
        The factories owned by the company.
    max_grades : dict
        The maximum grades for items X and Y.
    n_sales_offices : int
        The number of sales offices.

    Methods
    -------
    __str__() -> str:
        Returns a string representation of the company.
    get_inventory(item: str) -> np.ndarray:
        Returns the inventory corresponding to the specified item (X or Y).
    get_dict_inventory() -> dict:
        Returns a dictionary containing the grades and quantities for each standard.
    merge_inventories() -> None:
        Merges the production inventory with the current inventory and resets the production_inventory.
    produce(production_decisions: pd.DataFrame, grid: CompatibilityGrid) -> None:
        Processes production decisions for the company based on the given dataframe and compatibility grid.
    process_SO_acquistion(decision: pd.DataFrame) -> None:
        Adds or removes sales offices based on the value in the decision dataframe.
    """

    def __init__(self, company_data) -> None:
        self.name = company_data["Name"]
        self.id = company_data["Id"]
        self.inventory = Inventory()
        self.prod_inventory = Inventory()
        self.sales_inventory = Inventory()
        self.factories = Factories()
        self.max_grades = {'X': 0, 'Y': 0}
        self.n_sales_offices = 0
        self.stockouts = 0
        self.goodwill = 1
        self.wholeSaler = False

    def __str__(self):
        s = "######################\n"
        s += f"Company {self.name} -- Id {self.id}\n\n"
        s += str(self.inventory)
        return s

    def get_inventory(self, item: str, type_: str = 'main') -> np.ndarray:
        valid_types = {'main', 'production', 'sales'}
        
        if type_ not in valid_types:
            raise ValueError("Unknown inventory type '{}'".format(type_))
        
        inventory_mapping = {
            'main': self.inventory,
            'production': self.prod_inventory,
            'sales': self.sales_inventory
        }
        
        return inventory_mapping[type_].get(item)

    def get_dict_inventory(self) -> dict:
        """Returns a dictionary containing the grades and quantities for each standard."""
        inventory = {}
        for item in ("X", "Y"):
            full_inventory = self.get_inventory(item)
            non_zero_indices = np.nonzero(full_inventory)[0]
            num_non_zeroes = len(non_zero_indices)

            std, dlx = None, None
            std_qty, dlx_qty = 0, 0

            if num_non_zeroes > 0:
                std = np.min(non_zero_indices)
                std_qty = full_inventory[std]

                if num_non_zeroes > 1:
                    dlx = np.max(non_zero_indices)
                    dlx_qty = full_inventory[dlx]

            inventory[item] = {
                "Std": {"Grade": std, "Value": std_qty},
                "Dlx": {"Grade": dlx, "Value": dlx_qty}
            }
        return inventory
    
    def update_stockouts(self, parameter:float=0.1) -> None:
        """Computes the stockouts and goodwill for the given company."""

        assert 0<= parameter <= 0.5 , ValueError("Parameter `parameter` can only be within 0 and 0.5")

        is_stockout = False
        for item in ('X', 'Y'):
            inventory = self.inventory.get(item)
            sales = self.sales_inventory.get(item)
            stockouts = np.logical_and(self.inventory.get('X') != 0, inventory == sales)
            is_stockout = True if is_stockout == True else np.any(stockouts)
        if self.stockouts == 0:
            if is_stockout : 
                self.stockouts += 1
        if self.stockouts == 1 : 
            if is_stockout : 
                self.stockouts += 1
            else : self.stockouts -= 1
        if self.stockouts == 2:
            if is_stockout : 
                pass
            else : self.stockouts -= 1

        self.goodwill = 1 - parameter * self.stockouts


    def merge_inventories(self, reset:bool=True) -> None:
        """Merges production inventory with current inventory and then resets the production_inventory unless specified."""
        self.inventory = self.inventory.merge(self.prod_inventory)
        if reset == True : self.prod_inventory = Inventory()

    def produce(self, production_decisions: pd.DataFrame, grid, period_parameters, quarter):
        """
        Processes production decisions for the company.

        Production decisions will be processed in the order that they appear.
        Order is assumed to be Std first, then standard.

        Parameters
        ----------
        production_decisions: pd.DataFrame
            The dataframe containing the decision for the specific quarter.
        grid: CompatibilityGrid
            The grid of compatibility (a session attribute).
        """
        self.prod_inventory.reset()

        company_decisions = production_decisions.query(f"Company == {self.id}")
        Y_decisions = company_decisions.query(f"Item == 'Y'")
        X_decisions = company_decisions.query(f"Item == 'X'")

        # Produce Y
        produce_Y(self, Y_decisions, grid, quarter)

        # Producing X (after Y so they can't be used for Y production)
        for _, decision in X_decisions.iterrows():
            if self.max_grades['X'] >= decision["Grade"]:
                produce_X(self, decision)

        self.update_stockouts(period_parameters.get_values('Stockout impact')[quarter])

    def process_SO_acquistion(self, decision: pd.DataFrame) -> None:
        """
        Adds or removes sales offices based on the value in the decision dataframe.

        Parameters
        ----------
        decision: pd.DataFrame
            A dataframe whose only row contains sales office decisions.
        """
        self.n_sales_offices += decision["Evolution"]  # Where evolution is either +1 or -1

    def increment_factories_age(self, period_parameters):
        """
        Increments the age of all the company's factories
        """
        self.factories.increment_age(period_parameters)

    def set_wholesaler_status(self, status:str):
        
        if status == 'Normal' : 
            self.wholeSaler = False
        elif status == 'Wholesaler':
            self.wholeSaler = True
        else:
            raise ValueError(f'Unknown value for whole saler status {status}. Expected value : Normal or Wholesaler')


class MarketPlayers:
    """
    Represents a set of market players (companies).

    Attributes
    ----------
    companies : list
        The list of companies in the market.

    Methods
    -------
    addPlayer(company_data: pd.DataFrame) -> None:
        Adds a new player (company) to the market.
    """

    def __init__(self, companies_data) -> None:
        self.companies = []
        for _, company_data in companies_data.iterrows():
            self.addPlayer(company_data)

    def addPlayer(self, company_data: pd.DataFrame):
        """Adds a new player (company) to the market."""
        self.companies.append(Company(company_data))

    def __iter__(self):
        """Defines the iterator on companies."""
        return iter(self.companies)
    
    def __len__(self):
        """Defines the length of MarketPlayers"""
        return len(self.companies)

    def __getitem__(self, index):
        """Gets a company from the market using indexing."""
        return self.companies[index]
    def get_inventories(self, item, grade):
        inventories = {}
        for company in self:
            inventories[str(company.id)] = company.get_inventory(item)[grade]
        return inventories
    def increment_factories_age(self, period_parameters):
        for company in self.companies:
            company.increment_factories_age(period_parameters)
    def update_wholesaling_status(self, quarter, registry):
        for company in self.companies:
            cid = company.id
            status = registry.get_wholesaler_status(cid = cid, quarter=quarter)
            company.set_wholesaler_status(status)
        ...

class Inventory:
    """
    Represents the inventory of a company.

    Attributes
    ----------
    X : np.ndarray
        The inventory for item X.
    Y : np.ndarray
        The inventory for item Y.

    Methods
    -------
    downgrade() -> None:
        Applies downgrading to the inventory.
    remove(item: str, grade: int, quantity: int) -> None:
        Removes the specified quantity of items from the inventory.
    add(item: str, grade: int, quantity: int) -> None:
        Adds the specified quantity of items to the inventory.
    get(item: str) -> np.ndarray:
        Returns the inventory corresponding to the specified item (X or Y).
    merge(inventory: Inventory) -> Inventory:
        Merges another inventory into the current inventory.
    """

    def __init__(self, X=None, Y=None) -> None:
        self.X = np.zeros(10) if X is None else X
        self.Y = np.zeros(10) if Y is None else Y

    def downgrade(self) -> None:
        """
        Applies downgrading to the inventory.

        Keeps the highest grade and converts all lower grades to the lower current grade.
        Example: Grades 4, 5, 6, and 7 -> Grade 6 and 5 are converted to grade 4.
        """
        for lst in [self.X, self.Y]:
            inv = [(i, quantity) for i, quantity in enumerate(lst) if quantity != 0]
            if len(inv) <= 2:
                break
            summed = sum(quantity for _, quantity in inv[:-1])
            lst[:] = np.zeros(len(lst))
            lst[inv[0][0]], lst[inv[-1][0]] = summed, inv[-1][1]

    def remove(self, item, grade, quantity):
        """Removes the specified quantity of items from the inventory."""
        inventory = self.X if item == "X" else self.Y
        inventory[grade] -= quantity

    def add(self, item, grade, quantity):
        """Adds the specified quantity of items to the inventory."""
        inventory = self.X if item == "X" else self.Y
        inventory[grade] += quantity

    def get(self, item):
        """Returns the inventory corresponding to the specified item (X or Y)."""
        assert item in ["X", "Y"], KeyError("Specified item {} is not known. Try 'X' or 'Y'.".format(item))
        if item == "X":
            return self.X
        if item == "Y":
            return self.Y
    
    def reset(self):
        self.X = np.zeros(10)
        self.Y = np.zeros(10)

    def merge(self, inventory: 'Inventory') -> 'Inventory':
        """Merges another inventory into the current inventory and returns a new inventory object."""
        new_inventory = Inventory()
        new_inventory.X = np.add(self.X, inventory.X)
        new_inventory.Y = np.add(self.Y, inventory.Y)
        return new_inventory

    def __str__(self) -> str:
        str = "Inventory X:\n"
        inv_X = [(i, quantity) for i, quantity in enumerate(self.X) if quantity != 0]
        if len(inv_X) == 0:
            str += "\tEmpty\n"

        for item in inv_X:
            str += f"\tGrade {item[0]}: {item[1]} units\n"

        str += "Inventory Y:\n"
        inv_Y = [(i, quantity) for i, quantity in enumerate(self.Y) if quantity != 0]
        if len(inv_Y) == 0:
            str += "\tEmpty"

        for item in inv_Y:
            str += f"\tGrade {item[0]}: {item[1]} units\n"

        return str


if __name__ == "__main__":
    cols = ["Id", "Name"]
    companies = [
        ["1", "Chipsters"],
        ["2", "Compify"]
    ]

    companies_data = pd.DataFrame(companies, columns=cols)
    market = MarketPlayers(companies_data)
    i = Inventory()
    i.add("X", 7, 100)
    i.add("X", 2, 100)
    i.add("X", 6, 100)
    i2 = Inventory()
    i2.add("Y", 3, 457)
    i2.add("X", 6, 200)
    print(i)
    print("###########")
    i.merge(i2)
    print(i)
