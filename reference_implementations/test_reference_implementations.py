import contextlib
import importlib.resources
import json
import os
import sys

import pytest

from reference_implementations import Yoon2018
from srf_interfaces.transcripts import GeneaTranscript


@contextlib.contextmanager
def temporarily_prepend_to_python_path(*paths):
    for path in reversed(paths):
        sys.path.insert(0, path)
    yield
    for path in paths:
        sys.path.remove(path)


@pytest.fixture()
def sample_genea_transcript() -> GeneaTranscript:
    with importlib.resources.path('srf_interfaces.test_resources', 'GENEA_sample_transcript.json') as p_transcript:
        with open(str(p_transcript)) as f_transcript:
            d_transcript = json.load(f_transcript)
    return GeneaTranscript.from_dict(d_transcript)


def test_yoon2018_wrapper(sample_genea_transcript: GeneaTranscript) -> None:
    # TODO(TK): consider bundling the downloaded resources with the repo, or automatically downloading them in code

    yoon2018 = Yoon2018()
    mocap_data = yoon2018.generate_gestures(transcript=sample_genea_transcript.transcript)
    assert mocap_data.values.shape == (1190, 174)


def test_yoon2018_recovers_imports(sample_genea_transcript: GeneaTranscript) -> None:
    import pymo
    pymo_before = pymo
    assert os.path.normpath(pymo_before.__file__) == os.path.normpath(os.path.join(os.path.dirname(__file__), '../pymo/__init__.py'))
    pythonpath_before = sys.path

    Yoon2018().generate_gestures(transcript=sample_genea_transcript.transcript)

    assert os.path.normpath(pymo.__file__) == os.path.normpath(pymo_before.__file__)
    assert os.path.normpath(sys.modules['pymo'].__file__) == os.path.normpath(pymo.__file__)
    assert sys.path == pythonpath_before
