import abc

import pymo.data

from .transcripts import Transcript


class CoSpeechGestureGenerator(abc.ABC):
    @abc.abstractmethod
    def generate_gestures(self, transcript: Transcript) -> pymo.data.MocapData:
        raise NotImplementedError()
