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
      python3 -m venv venv
      source venv/bin/activate
      pip install -r requirements.txt
      pip install -r build_requirements.txt
   
      # Run tests and install:
      pip install . 
      pytest .
   
      # CLI:
      srf_ref -h

## ROS Integration

A `dockerfile` is provided to provide support for integration with ROS.

A reference stack is provided in `docker-compose.yml`:
1. Install [docker-compose](https://docs.docker.com/compose/install/) (v2.0+)
2. Run a virtual robot: `"/opt/Softbank Robotics/Choregraphe Suite 2.8/bin/naoqi-bin" -p 9559 -b 0.0.0.0`
3. Connect to the virtual robot with [Choreographe](https://developer.softbankrobotics.com/nao6/naoqi-developer-guide/choregraphe-suite/choregraphe-suite-installation-guide)
for visualisation.
4. `docker-compose up --build --remove-orphans`
