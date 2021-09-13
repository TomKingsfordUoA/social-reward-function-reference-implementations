import abc

import pymo.data
from srf_interfaces.transcripts import Transcript


class CoSpeechGestureGenerator(abc.ABC):
    @abc.abstractmethod
    def generate_gestures(self, transcript: Transcript) -> pymo.data.MocapData:
        raise NotImplementedError()
