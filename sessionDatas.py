import numpy as np
import pandas as pd
import os

from transactions import TransactionRegistry
from production import ProductionRegistry
from sales import SalesRegistry
import companies
import RD

def session_data_initializer(session):
    """
    Takes a session and initialises the following attributes : 
    - `n_companies`
    - `n_quarters`
    - `n_regions`
    - `period_parameters`
    - `compatibilityGrid`     (for production of Y given X grade)
    - `transferCosts`         (transfer costs across regions)
    - `marketPlayers`         (the set of companies)
    - `transactions`          (B2B transactions between companies)
    - `acquisitions`          (acquisitions of sales offices or factories)
    - `production_decisions`  
    - `sales_registry`        (B2C sales decisions registry)
    - `biddings`              (biddings for R&D)
    """
    file_path = session.params_path
    parameters_df = pd.read_excel(file_path, sheet_name='Parameters')
    session.n_regions = 1 # TODO: Hardcoded n_regions must be changed to dynamic
    assert session.n_regions == 1, NotImplementedError("Only one region is supported so far but n_regions = {} was given.".format(session.n_regions))

    # TODO : Change import to single xlsx sheet
    session.period_parameters = PeriodParameters(parameters_df)
    session.compatibilityGrid = CompatibilityGrid(pd.read_excel(file_path, sheet_name='Compatibility Grid', skiprows=[0,1], usecols='C:L'))
    # session.transfercosts = TransferCostGrid(pd.read_excel(file_path, sheet_name='Transfers')) # TODO : Update this and subsequent functions

    # Setting up the companies
    # TODO : Consider not reusing twice the same pd.read_excel command below : 
    session.marketPlayers = companies.MarketPlayers(pd.read_excel(file_path, sheet_name='Companies'))
    session.wholesaler_registry =  WholesalerRegistry(pd.read_excel(file_path, sheet_name='Companies'))

    # Gathering decisions
    session.transactions =          TransactionRegistry(path = file_path) # B2B items transactions
    session.acquisitions =          AcquisitionsRegistry(pd.read_excel(file_path, sheet_name='Acquisitions')) # Factories & SO
    session.production_decisions =  ProductionRegistry(file_path)
    session.sales_registry =        SalesRegistry(pd.read_excel(file_path, sheet_name='Sales'))
    session.biddings =              RD.Biddings(session)
    return session

class AcquisitionsRegistry:
    """
    The registry of plant or sales offices acquisitions or sales for all quarters.

    Attributes
    ----------
    data : pd.DataFrame
        The DataFrame containing the acquisitions or sales data.

    Methods
    -------
    get_quarter(quarter)
        Returns the acquisitions corresponding to the demanded quarter.
    query(*args, **kwargs)
        Calls the `query()` method on the registry data DataFrame.
    """

    def __init__(self, df: pd.DataFrame) -> None:
        self.data = df

    def get_quarter(self, quarter: int) -> pd.DataFrame:
        """
        Returns the acquisitions corresponding to the demanded quarter.

        Parameters
        ----------
        quarter : int
            The demanded quarter (starts at 1).

        Returns
        -------
        pd.DataFrame
            The acquisitions DataFrame for the specified quarter.
        """
        return self.data.query(f"Quarter == {quarter}")

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

class CompatibilityGrid :
    """
    The grid containing the compatibility ratios between different grades of X and Y.
    Attributes
    ----------
    data: pd.DataFrame
        The compatibility grid data.
    Methods
    ----------
    get_compatibility(X,Y)
        Returns the compatibility between grade X and grade Y.

    """
    def __init__(self, df) -> None:
        self.data = df.values
    def get_compatibility(self,X:int,Y:int)->int:
        assert 0<=X<=9 and 0<=Y<=9, "Grades are only supported between ranges 0 and 9 but (X,Y) = {} was given.".format((X,Y))
        """Returns how many X are needed to produce 1 unit of Y"""
        return self.data[X, Y]
    pass

class TransferCostGrid:
    """
    The grid containing transfer costs for different items, sources, and destinations.

    Attributes
    ----------
    data : dict
        A dictionary containing transfer cost data for different types (AIRFREIGHT, SURFACE).
    discount_rate : dict
        A dictionary containing discount rates for different types (AIRFREIGHT, SURFACE).

    Methods
    -------
    getTransferCost(item, source, destination, volume, type)
        Returns the total transfer cost based on the transfer cost grid.
    """

    def __init__(self, df_air: pd.DataFrame, df_surface: pd.DataFrame) -> None:
        col_names = ["Item", "Source", "Area 1 price", "Area 2 price", "Area 3 price", "None", "Area 1 discount",
                     "Area 2 discount", "Area 3 discount"]
        df_air = df_air.set_axis(col_names, axis=1)
        df_surface = df_surface.set_axis(col_names, axis=1)
        self.discount_rate = {"AIRFREIGHT": 0.5, "SURFACE": 0.33}
        self.data = {
            "AIRFREIGHT": df_air.loc[df_air['Item'].isin(['X', 'Y'])],
            "SURFACE": df_surface.loc[df_surface["Item"].isin(['X', 'Y'])]
        }

    def getTransferCost(self, item: str, source: int, destination: int, volume: int, type: str) -> float:
        """
        Returns the total transfer cost based on the transfer cost grid.

        Parameters
        ----------
        item : str
            The product type (X or Y).
        source : int
            The area of departure of the transfer.
        destination : int
            The area of destination of the transfer.
        volume : int
            The volume of the transfer (actual number, not thousands).
        type : str
            The type of requested transfer: AIRFREIGHT or SURFACE.

        Returns
        -------
        float
            The total transfer cost.
        """
        assert item in ["X", "Y"], "Product type must be either X or Y but {} was given".format(item)
        specific_data = self.data[type].loc[self.data[type]["Item"] == item]
        specific_data = specific_data.loc[specific_data["Source"] == "FROM AREA {} TO".format(source)]

        threshold_volume = specific_data["Area {} discount".format(destination)].values
        unit_price = specific_data["Area {} price".format(destination)].values

        if volume <= threshold_volume:
            price = volume * unit_price
        else:
            price = threshold_volume * unit_price
            price += self.discount_rate[type] * (volume - threshold_volume) * unit_price
        return price[0]

class PeriodParameters:
    """
    The parameters for different periods.

    Attributes
    ----------
    data : pd.DataFrame

    Methods
    -------
    get_values(parameter, periods)
        Returns the values of the given parameter name.
    """

    def __init__(self, df: pd.DataFrame) -> None:
        df.rename(columns={df.columns[0]: "Parameter"}, inplace=True)
        self.data = df

    def get_values(self, parameter: str, periods: list = None) -> np.ndarray:
        """
        Returns the values of the given parameter name.

        Parameters
        ----------
        parameter : str
            The string name of the considered parameter within the session period_parameters.
        periods : list, optional
            If specified, returns the values for the requested periods. Example: periods = [1, 2, 7].

        Returns
        -------
        np.ndarray
            The values of the parameter.
        """
        try:
            values = self.data.loc[self.data['Parameter'] == parameter].values[0, 1:]
        except:
            raise KeyError("Parameter {} was not found in the period parameters.".format(parameter))
        if periods is not None:
            periods = np.array(periods) - 1
            return values[periods]
        else:
            return values
        
class WholesalerRegistry:
    def __init__(self, df:pd.DataFrame) -> 'WholesalerRegistry':
        """
        Parameters
        ----------
        df: The companies dataframe
        """
        self.registry = df

    def get_wholesaler_status(self, cid:int, quarter:int) -> bool:
        try:
            # Find the row corresponding to the given ID
            row = self.registry[self.registry['Id'] == cid].iloc[0]

            # Extract the status for the given period
            status = row[f'Quarter {quarter}']

            return status
        except IndexError:
            # Handle the case where the ID is not found
            return f"No company found with ID {cid}"

if __name__ == '__main__':
    wr = WholesalerRegistry(pd.read_excel('Data.xlsx', sheet_name='Companies'))
    quarter = 1
    print(wr.get_wholesaler_status(cid=1, quarter=quarter))
    print(wr.get_wholesaler_status(cid=2, quarter=quarter))
    print(wr.get_wholesaler_status(cid=3, quarter=quarter))
    print(wr.get_wholesaler_status(cid=4, quarter=quarter))