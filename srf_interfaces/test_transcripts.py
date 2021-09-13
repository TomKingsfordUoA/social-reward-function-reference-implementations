import importlib.resources
import json
import typing

import pytest

from srf_interfaces.transcripts import TimedWord, GeneaTranscript


@pytest.fixture(scope='session')
def genea_sample_transcript() -> typing.Generator[str, None, None]:
    with importlib.resources.open_text('srf_interfaces.test_resources', 'GENEA_sample_transcript.json') as f:
        yield f.read()


def test_timed_word_to_dict() -> None:
    timed_word = TimedWord(
        word='test',
        start_time=1.2,
        end_time=1.5,
    )
    assert timed_word.to_dict() == {
        'word': 'test',
        'start_time': '1.2s',
        'end_time': '1.5s',
    }


def test_timed_word_from_dict() -> None:
    timed_word = TimedWord.from_dict({
        'word': 'test',
        'start_time': '1.2s',
        'end_time': '1.5s',
    })

    assert timed_word == TimedWord(
        word='test',
        start_time=1.2,
        end_time=1.5,
    )


def test_genea_transcript_from_dict(genea_sample_transcript: str) -> None:
    genea_transcript_json = json.loads(genea_sample_transcript)
    genea_transcript = GeneaTranscript.from_dict(genea_transcript_json)
    assert len(genea_transcript._elements) == 14
    assert len(genea_transcript._elements[2].alternatives[0].words) == 213


def test_genea_transcript_to_dict(genea_sample_transcript: str) -> None:
    genea_transcript_json = json.loads(genea_sample_transcript)
    genea_transcript = GeneaTranscript.from_dict(genea_transcript_json)
    assert genea_transcript.to_dict() == genea_transcript_json


def test_genea_transcript_to_transcript(genea_sample_transcript: str) -> None:
    genea_transcript_json = json.loads(genea_sample_transcript)
    genea_transcript = GeneaTranscript.from_dict(genea_transcript_json)
    transcript = genea_transcript.transcript
    assert transcript.confidence == 0.8299521116109995
    assert len(transcript.words) == 2741
