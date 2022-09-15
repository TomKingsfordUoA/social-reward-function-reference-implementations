# :closed_book: Social Reward Function: Reference Implementations

## Overview

This library provides a set of reference implementations of co-speech gesture generation systems, adhering to a standard
interface (mapping `srf_reference_implementations.interfaces.Transcript` onto `pymo.data.MocapData`).

This library exists to provide reference implementations to be evaluated by the [Social Reward Function](https://github.com/TomKingsfordUoA/social-reward-function).

These reference implementations exist as submodules, coupled with wrappers to implement a common interface 
(`srf_reference_implementations.interfaces.interfaces.CoSpeechGestureGenerator`).

## Reference Implementations

1. __Yoon2018__ 
   1. Source: https://github.com/youngwoo-yoon/Co-Speech_Gesture_Generation
   2. Fork: https://github.com/TomKingsfordUoA/Co-Speech_Gesture_Generation
2. __Gesticulator__
   1. Source: https://github.com/Svito-zar/gesticulator
   2. Fork: https://github.com/TomKingsfordUoA/gesticulator

## Getting Started

      # Clone submodules:
      git submodule init
      git submodule update
   
      # Establish a virtual environment:
      python3.7 -m venv venv
      source venv/bin/activate
      pip install -U pip
      pip install pip-tools
      pip-sync requirements.txt build_requirements.txt
   
      # Run tests and install:
      pip install . 
      pytest .
   
      # CLI:
      srf_ref -h

## Generating a transcript

In general, co-speech generation systems require the start and end timestamps of each word in dialogue to be given. 
These timestamps are used by at least some of the provided implementations. If you wish to generate a transcript with
equally spaced words (likely for testing purposes), you may use the script `scripts/generate_simple_transcript.py`. This
will generate a transcript file which can be provided to the CLI.

## ROS Integration

A `dockerfile` is provided to provide support for integration with ROS.

A reference stack is provided in `docker-compose.yml`:
1. Install [docker-compose](https://docs.docker.com/compose/install/) (v2.0+)
2. Run a virtual robot: `"/opt/Softbank Robotics/Choregraphe Suite 2.8/bin/naoqi-bin" -p 9559 -b 0.0.0.0`
3. Connect to the virtual robot with [Choreographe](https://developer.softbankrobotics.com/nao6/naoqi-developer-guide/choregraphe-suite/choregraphe-suite-installation-guide)
for visualisation.
4. `docker-compose up --build --remove-orphans`

## Requirements

Requirements are managed with `pip-tools`. A minimal set of dependencies with maximally broad versions is defined in
`requirements.in`. A working set of dependencies with pinned versions is defined in `requirements.txt`.
This latter file is built by running `pip-compile requirements.in`. The same is true for build requirements.