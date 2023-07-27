from value_compatibility_calculator import create_app

from typing import Any


class YourModel:
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """A model whose evolution is determined by a set of norms."""
        super().__init__(*args, **kwargs)

    def step(
        self,
        norms: dict[str, dict[str, Any]]
    ) -> None:
        """The model evolves according to the set of norms in place.

        By having the norms as an input to the model's ``step()`` method, it is
        possible to model changes in the implemented normative system while the
        model is still running.

        Parameters
        ----------
        norms : Dict[Any, Dict[Any, Any]]
            A map of the norms governing the evolution of the model at that
            step. This map is provided as a dictionary from norm identifiers
            (keys) to a dictionary mapping each of the norms' parameters to
            their values.

        Raises
        ------
        NotImplementedError
        """
        raise NotImplementedError
    

def your_value_semantics_function_1(mdl: YourModel) -> float:
    """Value semantics function.

    Parameters
    ----------
    mdl : YourModel

    Returns
    -------
    float
        The degree of respect for the value at the current state of the model.

    Raises
    ------
    NotImplementedError
    """
    raise NotImplementedError


def your_value_semantics_function_2(mdl: YourModel) -> float:
    """Value semantics function.

    Parameters
    ----------
    mdl : YourModel

    Returns
    -------
    float
        The degree of respect for the value at the current state of the model.

    Raises
    ------
    NotImplementedError
    """
    raise NotImplementedError


if __name__ == '__main__':
    app = create_app(
        YourModel,                      # your model class
        [...],                          # your model initialization arguments
        {...},                          # your model initialization keyword arguments
        [                               # the set of values whose compatibility is computed
            your_value_semantics_function_1,
            your_value_semantics_function_2
        ]
    )
    app.run(debug=True)
