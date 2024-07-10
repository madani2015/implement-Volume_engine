# Volume Engine Simulation

This repository contains the Volume Engine Simulation, which processes production, sales, and other business operations over multiple quarters. The main script to run the simulation is `session.py`.

## Running the Simulation

To run the simulation, use the following command in your terminal:

```sh
python session.py --n_quarters 4
```

In this command, `4` represents the number of quarters you want to simulate. You can change this number to simulate a different number of quarters.

## Input Data

The simulation uses data from `Data.xlsx`, which includes various parameters across multiple tabs. Here are the key tabs and their purposes:

- **Parameters**: General simulation parameters. It is possible to adjust these parameters.
- **Transfer**: Transfer costs and related parameters.
- **Compatibility Grid**: Compatibility information for different grades and items.
- **B2B Transactions**: Business-to-business transaction data.
  - Columns: `Quarter`, `Seller`, `Selling Region`, `Buyer`, `Buying Region`, `Product`, `Grade`, `Air / Surface`, `Volume`, `Price / unit`, `Payt Cash`, `AP 1`, `AP2`

    Example:
    ```
    4, 1, 1, 3, 1, Y, 0, Air, 20000, 110, 100, 0, 0
    ```
- **Production**: Production decisions. in production function, we can realize how many X is used to produce Y.
  - Columns: `Quarter`, `Company`, `Region`, `Item`, `Grade`, `Volume`, `Preference`, `Factory`, `Standard`

    Example:
    ```
    2, 1, 1, X, 1, 42000, 1, 1, std
    ```
- **Sales**: Sales data.
  - Columns: `Quarter`, `Company`, `Std_X`, `Price_Std_X`, `Dlx_X`, `Price_Dlx_X`, `Advertising_X`, `Std_Y`, `Price_Std_Y`, `Dlx_Y`, `Price_Dlx_Y`, `Advertising_Y`

    Example:
    ```
    4, 1, 0, 82, 1, 95, 50000, 0, 165, 1, 182, 12000
    ```
- **Acquisition**: Information about acquisitions.
  - Columns: `Quarter`, `Company`, `Region`, `Type`, `Evolution`, `Age`, `Index`

    Example:
    ```
    1, 1, 1, X, 1, 0, 0
    ```
- **R&D**: Research and development data.

## Output Data

After running the simulation, the output will include the following information for different companies shown in `output.xlsx` : 

- **Inventory**
  - Inventory X (units)
  - Inventory Y (units)

- **Sales**
  - Sales_X (units)
  - Sales_Y (units)

- **B2B Sales**
  - B2B_Sales_X (units)
  - B2B_Sales_Y (units)

- **Production**
  - Production_X (units)
  - Production_Y (units)

- **Max Grade**
  - Max_Grade_X
  - Max_Grade_Y

- **Factory Information**
  - Factory X | Age
  - Factory Y | Age

- **Sales Offices**
  - Number of Sales Offices

## Modules

The simulation is composed of several modules, each handling different aspects of the simulation:
## companies.py
Company Class

The `Company` class represents a company with its inventory, production facilities, and other attributes. This class handles the core functionalities such as managing inventory, processing production decisions, and handling sales office acquisitions.

## Attributes

- **name (str)**: The name of the company.
- **id (Any)**: The identifier of the company.
- **inventory (Inventory)**: The inventory of the company.
- **prod_inventory (Inventory)**: The production inventory of the company.
- **sales_inventory (Inventory)**: The sales inventory of the company.
- **factories (Factories)**: The factories owned by the company.
- **max_grades (dict)**: The maximum grades for items X and Y that a company can produce.
- **n_sales_offices (int)**: The number of sales offices.
- **stockouts (int)**: The number of stockouts.
- **goodwill (float)**: The goodwill of the company, if the company wants to sell the product that does not have, goodwill will be reduced.
- **wholeSaler (bool)**: The wholesaler status of the company.

## Methods

### `__init__(self, company_data) -> None`
Initializes the company with the provided data.

### `__str__(self) -> str`
Returns a string representation of the company.

### `get_inventory(self, item: str, type_: str = 'main') -> np.ndarray`
Returns the inventory corresponding to the specified item (X or Y) for the given inventory type (main, production, or sales).

### `get_dict_inventory(self) -> dict`
Returns a dictionary containing the grades and quantities for each standard (Std and Dlx).

### `update_stockouts(self, parameter: float = 0.1) -> None`
Computes the stockouts and goodwill for the company. The `parameter` can only be within 0 and 0.5.

### `merge_inventories(self, reset: bool = True) -> None`
Merges the production inventory with the current inventory and resets the production inventory unless specified otherwise.

### `produce(self, production_decisions: pd.DataFrame, grid: CompatibilityGrid, period_parameters, quarter)`
Processes production decisions for the company based on the given DataFrame and compatibility grid. Production decisions are processed in the order they appear, with standard decisions first, followed by deluxe.

### `process_SO_acquisition(self, decision: pd.DataFrame) -> None`
Adds or removes sales offices based on the value in the decision DataFrame.

### `increment_factories_age(self, period_parameters) -> None`
Increments the age of all the company's factories based on the provided period parameters.

### `set_wholesaler_status(self, status: str) -> None`
Sets the wholesaler status of the company. Valid values for `status` are 'Normal' or 'Wholesaler'.



## B2B Sales

### Process

B2B sales occur between two teams, where the seller and buyer are specified in `data.xls`. The teams negotiate the price and the type of transfer, which can be either airfreight or surface freight. The `Transfer` tab in `data.xls` contains the cost of product transfer. B2B sales have priority over B2C sales. The negotiated volume is sold first, and the remaining volume is available for B2C sales.

### Freight Handling

#### Main Functions

- **Risk Management:** 
  - `risk_expediting(session)`: Checks for airfreight risk and adjusts inventory if negative grades are found.

- **Airfreight:**
  - `airfreight_out(session)`: Processes outgoing airfreight and updates inventories at the beginning of each quarter.
  - `airfreight_in(session)`: Processes incoming airfreight and updates inventories at the beginning of each quarter.

- **Surface Freight:**
  - `surface_out(session)`: Processes outgoing surface freight and updates inventories at the beginning of each quarter.
  - `surface_in(session)`: Processes incoming surface freight and updates inventories at the end of each quarter.

### Example

Here is a brief summary of the key points related to freight handling:

- **Airfreight:**
  - **Outgoing:** Adjusts the inventory based on the airfreight sales.
  - **Incoming:** Updates the inventory with the airfreight purchases.

- **Surface Freight:**
  - **Outgoing:** Adjusts the inventory based on surface freight sales.
  - **Incoming:** Updates the inventory with surface freight purchases at the end of the quarter.

## Implementation Details

The implementation involves several helper functions and classes to manage sales and freight processes. Key components include:

- **SalesRegistry:** Manages sales data and provides methods to query and analyze sales for different quarters and items.
- **get_current_market_demand(session, item):** Retrieves the current market demand for a given item.
- **run_sales_protocol(inventories, specific_market_shares, specific_grade_demand):** Executes the sales protocol to calculate sales for each company based on inventories and market shares.




## `production.py`
This module manages the production processes of a company, focusing on product prioritization and resource allocation. It includes the following key functionalities:

- **Production Decision Management**: Implements logic for making production decisions based on preferences, such as prioritizing standard or deluxe products.
- **Inventory and Factory Management**: Allocates production volume based on factory capacities and available inventory, with error handling to prevent overproduction.
- **Utility Functions**: Supports the main production logic with helper functions for sorting decisions and managing inventory.
## Production Priorities
When producing item Y using item X, there are four possible production priorities:
1. **Standard for Standard:** Using standard-grade X to produce standard-grade Y.
2. **Standard for Deluxe:** Using standard-grade X to produce deluxe-grade Y.
3. **Deluxe for Standard:** Using deluxe-grade X to produce standard-grade Y.
4. **Deluxe for Deluxe:** Using deluxe-grade X to produce deluxe-grade Y.

- **Standard Grade:** The lowest grade available.
- **Deluxe Grade:** The highest grade available.

### Grade Definitions
- Each company has two grades.
- If a company has only one grade, it is considered as standard.
- If the highest grade in the market is, for example, 8, and a company only has grade 8, that grade will be considered as standard.

### Downgrading Function
- If a company has more than two grades, the downgrading function will convert three grades into two grades.
- The two lowest grades will be merged to form the ending inventory.

#### Example:
- If a company has grades X0, X1, and X2, the inventory of X0 and X1 will be merged, and the company will have grades X0 and X1 after the execution of the downgrading function.

### Production Function
After executing the downgrading function, the production function will show how many units of X are used to produce Y in a specific quarter for each company.


## `sales.py`
This module focuses on sales operations, particularly in calculating market potential and transforming likelihoods into probabilities. Key functionalities include:

- **Market Potential Calculation**: Calculates market potential using given data, ensuring that market demand aligns with inventory levels.
- **Probability Transformation**: Converts likelihood values into probabilities, handling cases where input values might be zero.
- **Helpers and Utilities**: Provides additional helper functions for various transformations and calculations needed in sales analysis and decision-making.

- **RD**: Handles research and development operations.
- **Exporter**: Exports simulation data to output files.
- **Sales**: Manages sales operations.
- **SessionDatas**: Initializes session data.
- **Session**: Main session management, running the core simulation logic.

The run_sales_protocol function calculates the amount of B2C (Business to Consumer) sales for each company. It considers several factors such as goodwill, price differentiation, price optimality, advertisement, and attractiveness.

Key Factors in B2C Sales

Goodwill Factor (goodwillF):
Dependent on the company's reputation.
Reduced if the company attempts to sell more than its available inventory.
Lower goodwill leads to fewer sales.

Price Differentiation Factor (priceDifferenceF):
Compares the current price with previous prices.
Significant changes in price can lead to reduced sales.

Price Optimality Factor (priceOptimalityF):
Measures how much the current price deviates from the optimal price.
The optimal price is defined in parameters in data.xls.
Advertisement:

Each company sets its advertising budget in the sales tab in data.xls.
Higher advertising spending leads to more sales.

Attractiveness (product cycle):
Defined in the parameters in data.xls.
Reflects the attractiveness of the product in the market.

Sales Calculation
Market Potential: Based on the parameters set in data.xls, including market shares and potential.
Market Shares: Each company's share of the market, calculated based on the factors mentioned above.
Specific Market Shares: Market shares for each grade and item.
Goodwill: Index of goodwill for each company.

### Key Functions for sales.py

- `get_current_market_demand(session, item)`: Retrieves the current market demand for a given item.
- `get_num_sellers(session, item)`: Counts the number of sellers for a given item.
- `get_total_market_demand(session, item)`: Calculates the total market demand for an item considering various factors.
- `get_specific_market_demands(session, item)`: Computes the specific market demands for all grades of a given item.
- `get_companies_goodwill(session)`: Returns the goodwill index for each company.
- `get_specific_market_shares(session, item, grade)`: Retrieves the market share for all companies for a specific item and grade.
- `run_sales_protocol(inventories, specific_market_shares, specific_grade_demand)`: Executes the sales protocol to determine the amount of sales for each company.

### RD.py
The RD.py module handles the R&D bidding process for a simulation session. This involves selecting the highest bidders (companies) for each item (X and Y) and updating their maximum grade based on the results.

## Class: Biddings
The Biddings class is responsible for managing the R&D bidding data and determining the winners of the bids.

## Attributes:

data: A pandas DataFrame containing the bidding data.
n_winners: The number of top bidders to be selected as winners.
Methods:

__init__(self, session, n_winners=3):
Initializes the Biddings instance with the session data and the number of winners.

get_winners(self, quarter: int, item: str) -> np.ndarray:
Retrieves the highest bidders for a given quarter and item (X or Y).

get_partners(self, company: int, quarter: int, item: str):
Retrieves the partners of a given company for a specific quarter and item.

Function: RD_round
The RD_round function runs the R&D bidding process for each item (X and Y) in the given session, updates the winners and their partners with the maximum grade available for the current quarter.

## Parameters:

session: The current running session.
Function: update_all_winers
The update_all_winers function updates the maximum grade for the winners and their partners.

Parameters:

session: The current running session.
winners: A numpy array of winning companies.
item: The item (X or Y) being considered.
Function: get_all_winners
The get_all_winners function retrieves all companies that succeeded in getting an R&D upgrade, including both bidders and their partners.

Parameters:

session: The current running session.
item: The item (X or Y) being considered.
Returns:

A numpy array containing all winners.
Input Data Format
The input data is expected to be in an Excel file with the following columns:

Quarter: The quarter in which the bidding takes place.
Company: The ID of the bidding company.
Bid_X: The bid amount for item X.
Partner_1_X: The ID of the first partner for item X.
Partner_2_X: The ID of the second partner for item X.
Bid_Y: The bid amount for item Y.
Partner_1_Y: The ID of the first partner for item Y.
Partner_2_Y: The ID of the second partner for item Y.



## `session.py`

The `session.py` script serves as the entry point of the simulation program. It initializes the session, manages the flow of operations for each quarter, and calls the necessary methods to simulate the activities of companies in the market. 

### Class: `Session`
The `Session` class represents a simulation session. It handles data loading, processing, and running the simulation for a specified number of quarters.

#### Attributes
- **data_path**: The path to the directory containing data files.
- **params_path**: The path to the parameters file (`Data.xlsx`).
- **quarter**: The current quarter of the session.
- **n_companies**, **n_quarters**, **n_regions**, **period_parameters**, **compatibilityGrid**, **transferCosts**, **transactions**, **marketPlayers**: Various session parameters and market player information initialized during session startup.

#### Methods

- **`__init__(self, data_path: os.PathLike)`**: Initializes the session with the specified data path and loads necessary data.

- **`load_ckpt(self)`**: Placeholder for loading a previously saved checkpoint. Currently, it raises a warning indicating that checkpoint loading is not implemented.

- **`runQuarter(self) -> 'Session'`**: Executes a full sequence of activities for a single quarter, including:
  - Expedite and downgrade inventories
  - Run production
  - Handle sales
  - Manage surface freight
  - Process estate changes (sales offices and factories)
  - Conduct research and development
  - Export session data

- **`runSessions(self, n_quarters) -> None`**: Runs the simulation for the specified number of quarters by repeatedly calling `runQuarter()`.

- **`sales(self)`**: Manages the sales process by calculating market shares, handling specific market demands, and updating inventories.

- **`expedite(self)`**: Manages the expedition process, including air and surface freight, and applies downgrading.

- **`downgrade(self)`**: Applies downgrading to all companies' inventories.

- **`run_production(self) -> None`**: Handles the production process for all companies, updating their production inventories based on decisions and compatibility grids.

- **`process_estate_changes(self) -> None`**: Processes changes related to factories and sales offices, including acquisitions and merges inventories.

- **`write_output(self, company)`**: Debug function to write summarized inventory output to a text file.

### Main Execution
When run as the main script, `session.py` parses command-line arguments to determine the number of quarters to run and the path to the working folder. It initializes a `Session` object and runs the specified number of quarters.





## Running the Program

To run the program, use the command:

```sh
python session.py --n_quarters 4
```

Ensure that `Data.xlsx` is correctly placed in the expected directory and contains all necessary data for the simulation.

## Contact

For further assistance, please contact Maryam at maryammadani2015@gmail.com or maryam.madani@eurecom.fr