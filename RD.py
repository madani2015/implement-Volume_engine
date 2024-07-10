
import pandas as pd
import numpy as np

import os

class Biddings:
    def __init__(self, session, n_winners = 3):
        self.data = pd.read_excel(session.params_path, sheet_name='R&D')
        self.n_winners = n_winners
    def get_winners(self, quarter:int, item:str) -> np.ndarray:
        """
        Returns the self.n_winners highest bidders ; i.e the winners of the R&D auction.
        Returns
        -------
        winners: np.ndarray
            The array of winners from highest to lowest bidders.
        """
        assert item in ['X', 'Y'], "Unknown item passed as parameter : {} instead of 'X' or 'Y'".format(item)
        winners = self.data.query(f"Quarter == {quarter} and {f'Bid_{item}'} > 0") \
            .reset_index()[["Company", f"Bid_{item}", f"Partner_1_{item}", f"Partner_2_{item}"]] \
            .sort_values([f"Bid_{item}"], ascending=False, inplace=False) \
            .head(self.n_winners)["Company"].values
        return winners
    def get_partners(self, company:int, quarter:int, item:str):
        """Given the id of a company, retrieves the partners it has as a np.ndarray
        Parameters
        ----------
        company:int
            The id of the company we are doing the research on
        quarter:int
            The quarter in which one is looking for the partners
        item: str
            Either `X` or `Y` and corresponds to the bidding that is being considered
        """
        partners = self.data.query(f"Quarter == {quarter}") \
            .query(f"Company == {company}")[[f"Partner_1_{item}", f"Partner_2_{item}"]] \
            .values.flatten()
        #removing Nan values : 
        partners = partners[~np.isnan(partners)]
        return partners.astype(int)


def RD_round(session) -> None:
    """
    Takes as inupt the biddings, gets the Biddings.n_winners best (by default 3) for each item and \n
    grants the patent to all of them and their partners.\n

    Parameters
    ----------
    session: Session
        The main running session
    """
    for item in ('X', 'Y'):
        winners = get_all_winners(session, item = item)
        update_all_winers(session, winners, item = item)

def update_all_winers(session, winners:np.ndarray, item:str) -> None:
    """
    Update direct winners' and their partners' max grade for 'item' to the current max.
    Parameters
    ----------
    session: Session
        The current running session
    winners: np.ndarray
        The array containing all winners. Generally, the output of get_all_winners()
    item: str
        Either `X`or `Y`-> Corresponds to the demanded product being bidded
    """
    for company in session.marketPlayers:
        if company.id in winners:
            company.max_grades[item] = session.quarter # Since each quarter the max available grade is incremented by 1, it's the same as the quarter iteself

def get_all_winners(session, item:str) -> np.ndarray:
    """ 
    Retrieves all the companies that have succeeded in getting a R&D upgrade.\n
    This includes both bidders and partners
    Parameters
    ----------
    item: str
        Either `X`or `Y`.

    Returns
    -------
    np.ndarray(dtype=int)
        A numpy array containing all winners.   
    """
    assert item in ('X', 'Y'), "Provided item must be either `X`or `Y`but `{}` was given".format(item)

    first_winners = session.biddings.get_winners(quarter = session.quarter, item = item)
    all_winners = np.empty(0)
    for winner in first_winners:
        new_partners = session.biddings.get_partners(company = winner, quarter = session.quarter, item= item)
        all_winners = np.unique(np.concatenate((all_winners, new_partners )))
    all_winners = np.concatenate((all_winners, first_winners))
    all_winners = np.unique(all_winners)
    return all_winners