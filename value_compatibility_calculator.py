from flask import Flask, Request, request
from pathos.multiprocessing import cpu_count, ProcessPool
from traceback import format_exc

from typing import Any, Callable, Iterable, Type


def evaluate_path(
    model_cls: Type,
    model_args: list[Any],
    model_kwargs: dict[str, Any],
    norms: dict[str, dict[str, Any]],
    value: Callable[[object], float],
    path_length: int
) -> float:
    """Evaluate the outcome of a path in terms of a value.

    Parameters
    ----------
    model_cls : Type[...]
        Class of the model.
    model_args : list[Any]
        Model initilization arguments.
    model_kwargs : dict[str, Any]
        Model initialization keyword arguments.
    norms : dict[str, dict[str, Any]]
        The set of norms governing the evolution of the model.
    value : Callable[[object], float]
        The value semantics function that evaluates the final state of a path.
    path_length : int
        The number of steps in the path to evaluate.

    Returns
    -------
    float
    """
    mdl = model_cls(*model_args, **model_kwargs)
    for _ in range(path_length):
        mdl.step(norms)
    return value(mdl)


def alignment(
    model_cls: Type,
    model_args: list[Any],
    model_kwargs: dict[str, Any],
    norms: dict[str, dict[str, Any]],
    value: Callable[[object], float],
    path_length: int,
    path_sample: int,
    pool: ProcessPool
) -> float:
    """Compute the alignment from a sample of paths.

    This function uses a ``pathos.multiprocessing.ProcessPool`` already
    initialized to speed up the sampling.

    Parameters
    ----------
    model_cls : Type[Model]
        Class of the model.
    model_args : list[Any]
        Model initilization arguments.
    model_kwargs : dict[str, Any]
        Model initialization keyword arguments.
    norms : dict[str, dict[str, Any]]
        The set of norms governing the evolution of the model.
    value : Callable[[object], float]
        The value semantics function that evaluates the final state of a path.
    path_length : int
        The number of steps in the path to evaluate.
    path_sample : int
        The number of paths to sample.
    pool : ProcessPool
        A ``pathos.multiprocessing.ProcessPool`` to parallelize sampling.

    Returns
    -------
    float
    """
    args = [
        [model_cls] * path_sample,
        [model_args] * path_sample,
        [model_kwargs] * path_sample,
        [norms] * path_sample,
        [value] * path_sample,
        [path_length] * path_sample
    ]
    pool.restart()
    algn = 0.
    for res in pool.map(evaluate_path, *args):
        algn += res
    pool.close()
    pool.terminate()
    return algn / path_sample


def value_compatibility(
    model_cls: Type,
    model_args: list[Any],
    model_kwargs: dict[str, Any],
    normative_system: dict[str, dict[str, Any]],
    values: Iterable[Callable[[object], float]],
    path_length: int = 10,
    path_sample: int = 100
) -> float:
    """Compute the compatibility between two values under a normative system.

    Parameters
    ----------
    model_cls : Type
        The class of the model.
    model_args : list[Any]
        Model initilization arguments.
    model_kwargs : dict[str, Any]
        Model initialization keyword arguments.
    baseline_norms : dict[str, dict[str, Any]]
        The baseline norms causing no evolution of the ABM.
    normative_system : dict[str, dict[str, Any]]
        The complete normative system, as a mapping of norm IDs (the keys)
        to a dictionary of its normative parameters.
    values : Iterable[Callable[[object], float]]
        An iterable of the value semantics functions capturing the values whose
        compatibility is computed.
    path_length : int, optional
        The length of the evolution path used to compute the alignment, by
        default 10.
    path_sample : int, optional
        The number of paths to sample when computing the alignment, by
        default 100.
    
    Returns
    -------
    float
    """
    # prepare pool
    num_nodes = cpu_count()
    if path_sample <= num_nodes:
        num_nodes = path_sample
    pool = ProcessPool(nodes=num_nodes)
    # compute alignments
    algns = []
    for v in values:
        algn_v =  alignment(
            model_cls, model_args, model_kwargs, normative_system, v,
            path_length, path_sample, pool
        )
        algns.append(algn_v)
    pool.terminate()
    return min(algns)


def create_app(
    model_cls: Type,
    model_args: list[Any],
    model_kwargs: dict[str, Any],
    values: Iterable[Callable[[object], float]]
) -> Flask:
    """Create a Flask app that computes the Shapley value.

    This C2 component of the VALAWAI architecture computes the compatibility of
    a set of values under a given normative system [1]_.

    Parameters
    ----------
    model_cls : Type
        Class of the model.
    model_args : list[Any]
        Model initilization arguments.
    model_kwargs : dict[str, Any]
        Model initilization keyword arguments.
    values : Iterable[Callable[[object], float]]
        The set of values whose compatibility is being computed. Each value is
        passed as a function taking as input a model instance and returning the
        evaluation of the value semantics function given the state of the model.

    Returns
    -------
    Flask
        A Flask application that can process GET /compatible requests.

    References
    ----------
    .. [1] Montes, N., & Sierra, C. (2022). Synthesis and properties of
        optimally value-aligned normative systems. Journal of Artificial
        Intelligence Research, 74, 1739–1774. https://doi.org/10.1613/jair.1.
        13487
    """
    __EXPECTED_TYPES = {
        'normative_system': dict, 'path_length': int, 'path_sample': int
    }
    
    app = Flask(__name__)

    def __check_request(request: Request):
        if not request.is_json:
            return {"error": "Request must be JSON"}, 415
        input_data = request.get_json()
        if not isinstance(input_data, dict):
            return {"error": f"Params must be passed as a dict"}, 400
        return input_data


    @app.get('/compatible')
    def get_compatibility():
        input_data = __check_request(request)

        __NEED_KEYS = ['normative_system']
        __OPT_KEYS = ['path_length', 'path_sample']

        # check that the input data has all the necessary keys and they are the
        # correct type
        for k in __NEED_KEYS:
            if not k in input_data.keys():
                return {"error": f"missing necessary param {k}"}, 400
        for k in input_data.keys():
            if not isinstance(input_data[k], __EXPECTED_TYPES[k]):
                return {"error": f"type of param {k} must be {__EXPECTED_TYPES[k]}"}, 400

        # get optional arguments path_length and path_sample
        kwargs = {}
        for k in __OPT_KEYS:
            try:
                kwargs[k] = input_data[k]
            except KeyError:
                continue

        # compute and return
        try:
            comp = value_compatibility(
                model_cls,
                model_args,
                model_kwargs,
                input_data['normative_system'],
                values,
                **kwargs
            )
            return {'compatible': comp}, 200
        except Exception:
            return {"error": format_exc()}, 400
        
    return app
