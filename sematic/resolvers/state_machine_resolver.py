"""
Abstract base class for a state machine-based resolution.
"""
# Standard Library
import abc

# Sematic
from sematic.resolver import Resolver
from sematic.runners.state_machine_runner import StateMachineRunner


class StateMachineResolver(StateMachineRunner, Resolver, abc.ABC):
    pass
