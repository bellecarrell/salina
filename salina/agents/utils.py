#
# Copyright (c) Facebook, Inc. and its affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.
#

import torch
import torch.nn as nn

from salina import Agent, TAgent


class Agents(Agent):
    """ Execute multiple agents sequentiall

    Args:
        Agent ([salina.Agent]): The agents to execute
    """

    def __init__(self, *agents, name=None):
        super().__init__(name=name)
        for a in agents:
            assert isinstance(a, Agent)
        self.agents = nn.ModuleList(agents)

    def __call__(self, workspace, **args):
        for a in self.agents:
            a(workspace, **args)

    def forward(**args):
        raise NotImplementedError

    def seed(self, seed):
        for a in self.agents:
            a.seed(seed)

    def __getitem__(self, k):
        return self.agents[k]

    def get_by_name(self, n):
        r = []
        for a in self.agents:
            r = r + a.get_by_name(n)
        if n == self._name:
            r = r + [self]
        return r


class TemporalAgent(Agent):
    """ Execute one Agent over multiple timesteps

    Args:
        Agent ([salina.Agent])
    """


    def __init__(self, agent, name=None):
        super().__init__(name=name)
        self.agent = agent

    def __call__(self, workspace, t=0, n_steps=None, stop_variable=None, **args):
        """ Execute the agent startiing at time t, for n_steps

        Args:
            workspace ([salina.Workspace]):
            t (int, optional): The starting timestep. Defaults to 0.
            n_steps ([type], optional): The number of steps. Defaults to None.
            stop_variable ([type], optional): if True everywhere (at time t), execution is stopped. Defaults to None = not used.
        """

        assert not (n_steps is None and stop_variable is None)
        _t = t
        while True:
            self.agent(workspace, t=_t, **args)
            if not stop_variable is None:
                s = workspace.get(stop_variable, _t)
                if s.all():
                    break
            _t += 1
            if not n_steps is None:
                if _t >= t + n_steps:
                    break

    def forward(self, **args):
        raise NotImplementedError

    def seed(self, seed):
        self.agent.seed(seed)

    def get_by_name(self, n):
        r = self.agent.get_by_name(n)
        if n == self._name:
            r = r + [self]
        return r


class CopyTAgent(Agent):
    """ An agent that copy a variable

    Args:
        input_name ([str]): The variable to copy from
        output_name ([str]): The variable to copy to
        detach ([bool]): copy with detach if True
    """
    def __init__(self, input_name, output_name, detach=False, name=None):
        super().__init__(name=name)
        self.input_name = input_name
        self.output_name = output_name
        self.detach = detach

    def forward(self, t=None, **args):
        """
        Args:
            t ([type], optional): if not None, copy at time t. Defaults to None.
        """
        if t is None:
            x = self.get(self.input_name)
            if not self.detach:
                self.set(self.output_name, x)
            else:
                self.set((self.output_name, t), x.detach())
        else:
            x = self.get((self.input_name, t))
            if not self.detach:
                self.set((self.output_name, t), x)
            else:
                self.set((self.output_name, t), x.detach())

class PrintAgent(Agent):
    """An agent to generate print in the console (mainly for debugging)

    Args:
        Agent ([type]): [description]
    """
    def __init__(self, *names, name=None):
        """
        Args:
            names ([str], optional): The variables to print
        """
        super().__init__(name=name)
        self.names = names

    def forward(self, t, **args):
        for n in self.names:
            print(n, " = ", self.get((n, t)))
