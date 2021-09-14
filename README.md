# Social Reward Function: Reference Implementations

## Overview

This library provides a set of reference implementations of co-speech gesture generation systems, adhering to a standard
interface (mapping `srf_interfaces.Transcript` onto `pymo.data.MocapData`).

This library exists to provide reference implementations to be evaluated by the [Social Reward Function](https://github.com/TomKingsfordUoA/social-reward-function).

These reference implementations exist as submodules, coupled with wrappers to 

## Interface and Wrappers

Refer to the `srf_interfaces.interfaces` module for the standard interface.

_Wrappers Coming Soon!_

## Reference Implementations

_Coming Soon!_

## Getting Started

    # Establish a virtual environment:
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    pip install -r build_requirements.txt

    # Run tests:
    pytest .