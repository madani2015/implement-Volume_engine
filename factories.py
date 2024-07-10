import os


class Factory:
    def __init__(self, region: int, type_: str, age: int, period_parameters, quarter: int) -> None:
        """
        Represents a factory.

        Parameters
        ----------
        region : int
            The region of the factory.
        type_ : str
            The type of item that can be produced (X or Y).
        age : int
            The age of the factory.
        period_parameters : pd.DataFrame
            The period parameters dataframe.
        quarter : int
            The quarter of the period.
        """
        self.region = region
        self.type = type_
        self.age = age
        self.max_output = period_parameters.get_values(f"Max capacity Plant {type_}", quarter)
        self.optimal_capacity = period_parameters.get_values(f"Optimum capacity {type_}", quarter)

    def incrementAge(self, aeging_parameter:float = 1) -> None:
        """
        Increments the age of the factory and adjusts production output if necessary.

        Parameters
        ----------
        session_parameters : pd.DataFrame
            The session parameters dataframe.
        """

        self.age += 1
        self.max_output *= aeging_parameter[self.age]

    def getOptimalCapacity(self):
        """Returns the optimal capacity of the factory."""
        return self.max_output * self.optimal_capacity


class Factories:
    def __init__(self):
        self.factories = {'X': {}, 'Y': {}}
        self.occupied = {'X': [False, False, False], 'Y': [False, False, False]}

    def add(self, factory: Factory) -> None:
        """
        Adds a factory to the collection.

        Parameters
        ----------
        factory : Factory
            The factory to add.
        """
        try:
            factory_index = self.occupied[factory.type].index(False) + 1
            self.factories[factory.type][factory_index] = factory
            self.occupied[factory.type][factory_index - 1] = True
        except ValueError:
            raise ValueError("Error: Could not add factory. Cause: too many factories.")

    def add_from_df(self, factory_df, period_parameters, quarter) -> None:
        """
        Adds a factory to the collection from a dataframe.

        Parameters
        ----------
        factory_df : pd.DataFrame
            The dataframe containing factory information.
        period_parameters : pd.DataFrame
            The period parameters dataframe.
        quarter : int
            The quarter of the period.
        """
        factory = Factory(
            region=factory_df['Region'],
            type_=factory_df['Type'],
            age=factory_df['Age'],
            period_parameters=period_parameters,
            quarter=quarter
        )
        self.add(factory)

    def remove(self, factory_index: int, factory_type: str) -> None:
        """
        Removes a factory from the collection.

        Parameters
        ----------
        factory_index : int
            The index of the factory.
        factory_type : str
            The type of the factory (X or Y).
        """
        self.occupied[factory_type][factory_index - 1] = False
        del self.factories[factory_type][factory_index]

    def get_factories_production(self, item_type: str) -> list:
        """
        Returns the production of factories for the specified item type.

        Parameters
        ----------
        item_type : str
            The item type (X or Y).

        Returns
        -------
        list
            The production of factories for the specified item type.
        """
        production = []
        for _, factory in self.factories[item_type].items():
            if factory.type == item_type:
                production.append(factory.max_output)
        return production

    def increment_age(self, session_parameters) -> None:
        """Increments the age of all factories by one year
        Parameters
        ----------
        self: "Factories"
            The set of factories whose ages should be incremented
        """
        for item in {'X', 'Y'}:
            occupied = self.occupied[item]
            factories = self.factories[item]
            for factory_index, boolean in enumerate(occupied):
                if boolean:
                    factory = factories.get(factory_index + 1)  # Factory indices are 1-based
                    factory.incrementAge(session_parameters.get_values('Factory aeging coefficient'))

    def __iter__(self):
        return iter(self.factories)

    def __getitem__(self, index):
        return self.factories[index]


if __name__ == "__main__":
    import session
    S = session.Session(os.getcwd())
    F = Factories()
    factory = Factory(1, "X", 0, S.period_parameters, 0)
    F.add(factory)
    F.add(factory)
    F.add(factory)
    F.remove(1, 'X')
    F.add(factory)
    factory = Factory(1, "Y", 0, S.period_parameters, 0)
    F.add(factory)
    F.add(factory)
    F.add(factory)
    F.remove(2, 'Y')
    print(F.get_factories_production('X'))
    print(F.occupied)
    pass
