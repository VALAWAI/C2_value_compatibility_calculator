import argparse
from mesa import Agent, Model
from mesa.time import BaseScheduler
from random import seed, uniform

from app import create_app

parser = argparse.ArgumentParser()
parser.add_argument('port', type=int)

seed(100)

class TaxModel(Model):
    def __init__(self) -> None:
        super().__init__()
        self.num_agents = 200
        self.num_segments = 5
        self.schedule = BaseScheduler(self)
        for i in range(self.num_agents):
            a = Agent(i, self)
            a.wealth = uniform(0, 100)
            self.schedule.add(a)
        self.sorted_agents = sorted(self.schedule.agents, key=lambda a: a.wealth)
        self.ags_per_seg = self.num_agents//self.num_segments
        self.segments = [i//self.ags_per_seg for i in range(self.num_agents)]

    def step(self, norms) -> None:
        common_fund = 0.
        for i in range(self.num_agents):
            a = self.sorted_agents[i]
            seg = self.segments[i]
            pay = a.wealth * norms['pay'][f"r{seg}"]
            if pay > a.wealth:
                pay = a.wealth
            a.wealth -= pay
            common_fund += pay
        common_fund *= 1.05
        segs_payback = [
            common_fund * norms['payback'][f"r{seg}"] / self.ags_per_seg
            for seg in range(self.num_segments)
        ]
        for i in range(self.num_agents):
            a = self.sorted_agents[i]
            seg = self.segments[i]
            a.wealth += segs_payback[seg]
        self.sorted_agents = sorted(self.schedule.agents, key=lambda a: a.wealth)


def ratio_wealth_value(mdl: TaxModel) -> float:
    """Semantics function for value equality based on the ratio between the
    maximum and the minimum wealth.

    Parameters
    ----------
    mdl : TaxModel

    Returns
    -------
    float
    """
    a = mdl.sorted_agents[99].wealth
    b = mdl.sorted_agents[199].wealth
    return a/b


def gini_index_value(mdl: TaxModel) -> float:
    """Semantics function for value equality based on the Gini Index.

    Parameters
    ----------
    mdl : TaxModel

    Returns
    -------
    float
    """
    sorted_wealth = [ag.wealth for ag in mdl.sorted_agents]
    N = mdl.num_agents
    B = sum(xi * (N - i) for i, xi in enumerate(sorted_wealth)) 
    GI =  1 + (1 / N) - 2 * B / (N * sum(sorted_wealth))
    return 1 - 2*GI

        
if __name__ == '__main__':

    normative_system = {
        'pay': {f'r{i}': 0.1+i/10 for i in range(5)},
        'payback': {f'r{i}': 0.2 for i in range(5)}
    }

    app = create_app(
        TaxModel,
        [],
        {},
        normative_system,
        [ratio_wealth_value, gini_index_value],
        path_length=5,
        path_sample=100
    )

    args = parser.parse_args()
    app.run(debug=True, host="0.0.0.0", port=args.port)