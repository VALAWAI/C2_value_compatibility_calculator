# Copyright 2023 IIIA-CSIC
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License version 3
# along with this program; if not, see <http://www.gnu.org/licenses/>.

from dataclasses import dataclass
from flask import Flask, Request, request
from traceback import format_exc
from valalgn.sampling import value_compatibility

from typing import Any, Callable, Iterable, Type

@dataclass
class CompatibilityCalculator:
    model_cls: Type
    model_args: list[Any]
    model_kwargs: dict[str, Any]
    norms: dict[str, dict[str, Any]]
    values: Iterable[Callable[[object], float]]
    path_length: int = 10
    path_sample: int = 500

    def compute_compatibility(self) -> float:
        return value_compatibility(
            self.model_cls,
            self.model_args,
            self.model_kwargs,
            self.norms,
            self.values,
            self.path_length,
            self.path_sample
        )

def create_app(
    model_cls: Type,
    model_args: list[Any],
    model_kwargs: dict[str, Any],
    norms: dict[str, dict[str, Any]],
    values: Iterable[Callable[[object], float]],
    path_length: int = 10,
    path_sample: int = 500
) -> Flask:
    """Create a Flask app that computes the compatibility among values.

    This C2 component of the VALAWAI architecture computes the compatibility of
    values under a given normative system [1]_.

    Parameters
    ----------
    model_cls : Type
        Class of the model.
    model_args : list[Any]
        Model initilization arguments.
    model_kwargs : dict[str, Any]
        Model initilization keyword arguments.
    norms : dict[str, dict[str, Any]]
        The set of norms governing the evolution of the model.
    values : Iterable[Callable[[object], float]]
        An iterable of the value semantics functions capturing the values whose
        compatibility is computed.
    path_length : int, optional
        The length of the paths to evaluate the alignment, by default 10.
    path_sample : int, optional
        The sample size of the paths to evaluate the alignment, by default 500.

    Returns
    -------
    Flask
        A Flask application that can process GET /compt requests.

    References
    ----------
    .. [1] Montes, N., & Sierra, C. (2022). Synthesis and properties of
        optimally value-aligned normative systems. Journal of Artificial
        Intelligence Research, 74, 1739–1774. https://doi.org/10.1613/jair.1.
        13487
    """
    app = Flask(__name__)
    
    calculator = CompatibilityCalculator(
        model_cls, model_args, model_kwargs, norms, values, path_length, path_sample
    )

    def __check_request(request: Request):
        if not request.is_json:
            return {"error": "Request must be JSON"}, 415
        input_data = request.get_json()
        if not isinstance(input_data, dict):
            return {"error": f"Params must be passed as a dict"}, 400
        return input_data

    @app.get('/compt')
    def get_algn():
        try:
            compt = calculator.compute_compatibility()
            return {'compt': compt}, 200
        except Exception:
            return {"error": format_exc()}, 400
        
    @app.patch('/norms')
    def patch_norms():
        input_data = __check_request(request)
        try:
            for k, v in input_data.items():
                calculator.norms[k].update(v)
            return {}, 200
        except Exception:
            return {"error": format_exc()}, 400
        
    @app.patch('/path_length')
    def patch_path_length():
        input_data = request.get_data()
        try:
            calculator.path_length = int(input_data)
            return {}, 200
        except Exception:
            return {"error": format_exc()}, 400
        
    @app.patch('/path_sample')
    def patch_path_sample():
        input_data = request.get_data()
        try:
            calculator.path_sample = int(input_data)
            return {}, 200
        except Exception:
            return {"error": format_exc()}, 400
        
    return app
