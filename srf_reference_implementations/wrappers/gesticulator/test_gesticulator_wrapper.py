import os
import sys

import pymo
from .gesticulator_wrapper import Gesticulator
from ...interfaces import GeneaTranscript


def test_gesticulator_wrapper(sample_genea_transcript_short: GeneaTranscript) -> None:
    gesticulator = Gesticulator()
    mocap_data = gesticulator.generate_gestures(transcript=sample_genea_transcript_short.transcript)

    # Shape is correct:
    assert mocap_data.values.shape == (80, 174)

    # Timings are correct:
    assert abs(mocap_data.values.index[0].total_seconds() * mocap_data.framerate - sample_genea_transcript_short.transcript.words[0].start_time) < 0.5
    assert abs(mocap_data.values.index[-1].total_seconds() * mocap_data.framerate - sample_genea_transcript_short.transcript.words[-1].end_time) < 0.5


def test_gesticulator_recovers_imports(sample_genea_transcript_short: GeneaTranscript) -> None:
    pymo_before = pymo
    assert os.path.normpath(pymo_before.__file__) == os.path.normpath(os.path.join(os.path.dirname(__file__), '../../../pymo/__init__.py'))
    pythonpath_before = sys.path

    Gesticulator().generate_gestures(transcript=sample_genea_transcript_short.transcript)

    assert os.path.normpath(pymo.__file__) == os.path.normpath(pymo_before.__file__)
    assert os.path.normpath(sys.modules['pymo'].__file__) == os.path.normpath(pymo.__file__)
    assert sys.path == pythonpath_before
