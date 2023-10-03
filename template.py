import argparse
from app import create_app

from typing import Any

parser = argparse.ArgumentParser()
parser.add_argument('port', type=int)

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

    norms = {
        'n1': {'p11': ...}
    }

    app = create_app(
        YourModel,                      # your model class
        [...],                          # your model initialization arguments
        {...},                          # your model initialization keyword arguments
        norms,                          # your norms dictionary
        [
            your_value_semantics_function_1,
            your_value_semantics_function_2
        ]                               # your value semantics functions
        # path_length=10,               # change if needed, default is 10
        # path_sample=500               # change if needed, default is 500
    )

    args = parser.parse_args()
    app.run(debug=True, host="0.0.0.0", port=args.port)
