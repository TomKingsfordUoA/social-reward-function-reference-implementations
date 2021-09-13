import dataclasses
import statistics
import typing

import dataclasses_json


@dataclasses.dataclass(frozen=True)
class TimedWord:
    word: str
    start_time: float
    end_time: float

    def to_dict(self) -> typing.Dict[str, typing.Any]:
        return {
            "word": self.word,
            "start_time": f"{self.start_time}s",
            "end_time": f"{self.end_time}s",
        }

    @staticmethod
    def from_dict(d: typing.Dict[str, typing.Any]) -> 'TimedWord':
        if set(d.keys()) != {"word", "start_time", "end_time"}:
            raise ValueError()
        if d["start_time"][-1] != "s":
            raise ValueError()
        if d["end_time"][-1] != "s":
            raise ValueError()
        return TimedWord(
            word=d["word"],
            start_time=float(d["start_time"][:-1]),
            end_time=float(d["end_time"][:-1]),
        )


@dataclasses_json.dataclass_json(undefined=dataclasses_json.Undefined.RAISE)
@dataclasses.dataclass(frozen=True)
class Transcript:
    words: typing.List[TimedWord]
    confidence: typing.Optional[float] = dataclasses.field(
        default=None,
        metadata=dataclasses_json.config(
            exclude=lambda x: x is None,
        )
    )


@dataclasses.dataclass(frozen=True)
class GeneaTranscript:
    @dataclasses_json.dataclass_json(undefined=dataclasses_json.Undefined.RAISE)
    @dataclasses.dataclass(frozen=True)
    class Element:
        alternatives: typing.List[Transcript]
        language_code: str

    _elements: typing.List[Element]

    @property
    def transcript(self) -> Transcript:
        confidences = [alternative.confidence for element in self._elements for alternative in element.alternatives if alternative.confidence is not None]
        if len(confidences) != 0:
            mean_confidence: typing.Optional[float] = statistics.mean(confidences)
        else:
            mean_confidence = None

        words = [word for element in self._elements for alternative in element.alternatives for word in alternative.words]

        return Transcript(
            words=words,
            confidence=mean_confidence,
        )

    def to_dict(self) -> typing.Any:
        if len(self._elements[0].alternatives) != 1:
            raise ValueError()
        return [element.to_dict() for element in self._elements]

    @staticmethod
    def from_dict(d: typing.Any) -> 'GeneaTranscript':
        if not isinstance(d, list):
            raise ValueError()
        elements = [GeneaTranscript.Element.from_dict(element_dict) for element_dict in d]
        genea_transcript = GeneaTranscript(_elements=elements)

        for idx in range(len(genea_transcript._elements)):
            if len(genea_transcript._elements[idx].alternatives) != 1:
                raise ValueError()

        return genea_transcript
