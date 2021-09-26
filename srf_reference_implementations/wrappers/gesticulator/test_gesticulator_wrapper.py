import os
import sys

import pytest

import pymo
from .gesticulator_wrapper import Gesticulator
from ...interfaces import GeneaTranscript


def test_gesticulator_wrapper(sample_genea_transcript_short: GeneaTranscript) -> None:
    gesticulator = Gesticulator()
    mocap_data = gesticulator.generate_gestures(transcript=sample_genea_transcript_short.transcript)
    assert mocap_data.values.shape == (10, 174)


@pytest.mark.xfail
def test_gesticulator_wrapper_against_known_bvh() -> None:
    # since we had to modify a substantial amount of inference-time code, it's worth comparing against a known BVH prediction
    # to ensure correctness
    raise NotImplementedError()


def test_gesticulator_recovers_imports(sample_genea_transcript_short: GeneaTranscript) -> None:
    pymo_before = pymo
    assert os.path.normpath(pymo_before.__file__) == os.path.normpath(os.path.join(os.path.dirname(__file__), '../../../pymo/__init__.py'))
    pythonpath_before = sys.path

    Gesticulator().generate_gestures(transcript=sample_genea_transcript_short.transcript)

    assert os.path.normpath(pymo.__file__) == os.path.normpath(pymo_before.__file__)
    assert os.path.normpath(sys.modules['pymo'].__file__) == os.path.normpath(pymo.__file__)
    assert sys.path == pythonpath_before
