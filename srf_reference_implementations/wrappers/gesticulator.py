import pymo.data
from ..interfaces import CoSpeechGestureGenerator, Transcript


class Gesticulator(CoSpeechGestureGenerator):
    def generate_gestures(self, transcript: Transcript) -> pymo.data.MocapData:
        pass
