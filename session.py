import os
import pandas as pd
import numpy as np
import freight
from sessionDatas import session_data_initializer
from RD import RD_round
import warnings
from exporter import export_data
from sales import get_market_shares, get_specific_market_demands, run_sales_protocol
import argparse

class Session :
    """
    Represents a session, will be initialised at every session start. Loads the data from the given input.
    By default, starts on session 0.
    Attributes:
    -----------
    data_path\n
    n_companies\n
    n_quarters\n
    n_regions\n
    period_parameters\n
    compatibilityGrid\n
    transferCosts\n
    transactions\n
    marketPlayers\n
    quarter (the current quarter)
    """
    def __init__(self, data_path:os.PathLike) -> None:
        self.data_path = data_path
        # Loads all the data from the global parameters sheet
        self.params_path = os.path.join(self.data_path, "Data.xlsx")
        # Inits the session data
        self = session_data_initializer(self)
        self.quarter = 1
        pass

    def load_ckpt(self):
        """Loads the previously remembered checkpoint
        Updates the quarter N°, retrieves the marketplayers status and others.
        """
        warnings.warn("Checkpoint Loading isn't yet implemented. Running on 1 quarter only.")

    def runQuarter(self) -> 'Session':
        """
        Runs a whole quarter in the following sequence :
        - load_ckpt
        - expedite and downgrade
        - run_production
        - sales
        - surface_in
        - process_estate_changes (Sales Offices and factories)
        - R&D
        """

        self.transactions.update()

        # Gathering begining inventory
        self.expedite()
        # this is deleted
        # self.downgrade()

        # Running production

        ####
        self.sales()
        #self.downgrade()
        self.run_production()


        # Doing sales
        
        

        # Finishing quarter
        # # Freight
        freight.surface_in(self)
        self.downgrade()

        # # Updating factories, Sales Offices and merging inventories
        self.process_estate_changes()

        # # Research and develpment
        RD_round(self)

        # Exporting data to output.xlsx

        export_data(self)

        self.quarter += 1

        return self

    def runSessions(self, n_quarters) -> None:
        for _ in range(n_quarters):
            self.runQuarter()
    
    def sales(self):
        market_shares = get_market_shares(self)
        # For each item X and Y
        # iterate over the 10 grades
        #   Give the mkt_share * gross demand for each
            # Then, iterate until there is no more shortage or excess given theinventory
        for company in self.marketPlayers:
            company.sales_inventory.reset()

        for item in ('X', 'Y'):

            specMktGD = get_specific_market_demands(self, item)
            # print("specMktGD", specMktGD)
            for grade in range(0,10):
                grade_demand = specMktGD[grade]
                # print("grade_demand ", grade_demand )
                # For all companies, inventory of the requested item
                inventories = np.array(list(self.marketPlayers.get_inventories(item, grade).values()))
                specific_market_shares = np.array(list(market_shares[item][grade].values())).flatten()
                # print("specific_market_shares", specific_market_shares)

                number_of_sales = run_sales_protocol(inventories, specific_market_shares, grade_demand)
                # Updating the inventories
                for company in self.marketPlayers:
                    sales_qty = int(number_of_sales[company.id -1])
                    # print("sales_qty", sales_qty)
                    # print("#################")
                    # print(company.id, company)
                    company.inventory.remove(item, grade, sales_qty)
                    # print(company.id, company)
                    company.sales_inventory.add(item, grade, sales_qty)
                pass

    def expedite(self):
        """Expedites inventories Air and Surface, and recieves from Air."""
        freight.airfreight_out(self)
        risks_air = freight.risk_expediting(self)
        freight.airfreight_in(self)
        # this is added to do downgrading after freight_in
        self.downgrade()
        freight.surface_out(self)
        risks_surface = freight.risk_expediting(self)
        self.expedition_risks = {"Surface": risks_surface, "Air":risks_air}

    def downgrade(self):
        """Applies downgrading to all marketplayers."""
        for company in self.marketPlayers:
            company.inventory.downgrade()

    def run_production(self) -> None:
        """
        Iterates over all company and calls 'Company.produce()' on each of them.\n
        Inventories are updated and stored into company.prod_inventory
        """
        for company in self.marketPlayers:
            decisions = self.production_decisions.get_current_registry(self.quarter)
            company.produce(decisions, self.compatibilityGrid, self.period_parameters, self.quarter)
        # # add it
        # for company in self.marketPlayers:
        #      company.merge_inventories(reset=False)
        

    def process_estate_changes(self) -> None:
        """
        Calls increment_age in all factories\n
        Then processes plants and sales offices acquisitions and drops.\n
        ALso merges production_inventory with main inventory
        Data is read from self.acquisitions

        Returns
        -------
        None
        """
        # Incrementing factories age
        self.marketPlayers.increment_factories_age(self.period_parameters)

        # Processing plant acquisitions & removals
        plants_df = self.acquisitions.query(f"Type in ('X','Y') and Quarter == {self.quarter}")
        for _, row in plants_df.iterrows():
            company = row["Company"] - 1
            self.marketPlayers[company].factories.add_from_df(row, self.period_parameters, self.quarter)

        # Processing sales offices acquisitions & removals
        salesOffices_df = self.acquisitions.get_quarter(self.quarter).query(f"Type == 'SO' and Quarter == {self.quarter}")
        for _, row in salesOffices_df.iterrows():
            company = row["Company"] - 1
            self.marketPlayers[company].process_SO_acquistion(row)

        # Processing statute changes for companies
        self.marketPlayers.update_wholesaling_status(quarter = self.quarter, registry = self.wholesaler_registry)

        # Merging production inventories with main inventories
        for company in self.marketPlayers : 
            company.merge_inventories(reset=False)

        # # Downgrading all inventories
        # self.downgrade()

    def write_output(self,company):
        """DEBUG function -> Writes summarized inventory output into Data/output.txt"""
        filepath = os.path.join(self.data_path, "output.txt")
        if os.path.isfile(filepath) : 
            f = open(filepath, 'a')
            f.write('\n')
        else :
            f = open(os.path.join(self.data_path,"output.txt"), "w")
        f.write(str(company))
        f.close

#########################################
# B2B Expeditions, receptions and risks #
#########################################

if __name__ == "__main__":

    default_path = ""


    parser = argparse.ArgumentParser(description="Runs a simulation given a path and a number of quarters")
    parser.add_argument('--n_quarters', '-n', type=int, default=5, help="Number of sessions to run.")
    parser.add_argument('--path', '-p', type=str, default=default_path, help="Path to the working folder")

    args = parser.parse_args()

    print(args.path)

    S = Session(args.path)
    S.runSessions(args.n_quarters)

    pass