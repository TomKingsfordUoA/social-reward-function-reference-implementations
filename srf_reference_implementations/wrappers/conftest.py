import importlib
import importlib.resources
import json

import pytest

from ..interfaces import GeneaTranscript


@pytest.fixture()
def sample_genea_transcript() -> GeneaTranscript:
    # nb: importlib.resources doesn't support relative packages hence we resolve an absolute package
    test_resources_package = importlib.import_module("..interfaces.test_resources", package=__package__).__name__
    with importlib.resources.path(test_resources_package, 'GENEA_sample_transcript.json') as p_transcript:
        with open(str(p_transcript)) as f_transcript:
            d_transcript = json.load(f_transcript)
    return GeneaTranscript.from_dict(d_transcript)


@pytest.fixture()
def sample_genea_transcript_short() -> GeneaTranscript:
    # nb: importlib.resources doesn't support relative packages hence we resolve an absolute package
    test_resources_package = importlib.import_module("..interfaces.test_resources", package=__package__).__name__
    with importlib.resources.path(test_resources_package, 'GENEA_sample_transcript.json') as p_transcript:
        with open(str(p_transcript)) as f_transcript:
            d_transcript = json.load(f_transcript)
    d_transcript = d_transcript[:1]
    d_transcript[0]['alternatives'][0]['words'] = d_transcript[0]['alternatives'][0]['words'][:10]
    return GeneaTranscript.from_dict(d_transcript)
