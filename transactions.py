import pandas as pd
import os

class TransactionRegistry:
    """
    The registry of transactions.

    Attributes
    ----------
    df : pd.DataFrame
        The transaction registry dataframe.

    Methods
    -------
    update(dataFrame)
        Replaces the transaction registry with the given dataframe.
    get_quarter(quarter)
        Returns the transactions corresponding to the requested quarter.
    filter_type(t_type)
        Returns the transactions dataframe corresponding to the requested transport type.
    """

    def __init__(self, path:os.PathLike, data:pd.DataFrame=None) -> None:
        self.path = path
        self.data = data

    def update(self) -> None:
        """
        Replaces the transaction registry with the given dataframe.

        Parameters
        ----------
        dataFrame : pd.DataFrame
            The new transaction registry dataframe.
        """
        self.data = pd.read_excel(self.path, sheet_name='B2B Transactions')

    def get_quarter(self, quarter: int) -> pd.DataFrame:
        """
        Returns the transactions corresponding to the requested quarter.

        Parameters
        ----------
        quarter : int
            The requested quarter.

        Returns
        -------
        pd.DataFrame
            The transactions dataframe for the requested quarter.
        """
        return self.data[self.data["Quarter"] == quarter]

    def filter_type(self, t_type: str) -> pd.DataFrame:
        """
        Returns the transactions dataframe corresponding to the requested transport type.

        Parameters
        ----------
        t_type : str
            The transport type. Can be either 'Air' or 'Surface'.

        Returns
        -------
        pd.DataFrame
            The transactions dataframe for the requested transport type.
        """
        assert t_type in ['Air', 'Surface'], "Parameter {} is not a recognized transport mode.".format(t_type)
        return self.data[self.data["Air / Surface"] == t_type]

if __name__ == "__main__":
    df = pd.read_excel("./Transaction_Registry.xlsx")
    T = TransactionRegistry()
    T.update(df)
    new_T = TransactionRegistry()
    new_T.update(T.get_quarter(2))
    print(new_T.filter_type(t_type="Surface").head())