class WeinhuberStrategyException(Exception):
    """
    Raised when an invalid state inside weinhuber_approach_splitting_strategy.py is reached.
    """
    pass


class WeinhuberSplitException(Exception):
    """
    Raised when a Weinhuber Split Object reaches an invalid states.
    """
    pass


class WeinhuberPredicateParserException(Exception):
    """
    Raised when an invalid state inside predicate_parser.py is reached.
    """
    pass
