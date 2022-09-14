from argparse import ArgumentParser
import json
from pprint import pprint
from pathlib import Path


def idx_to_time(idx: int, delta_s: float) -> str:
    return f"{idx * delta_s:.3f}s"


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--transcript", default=Path("transcript.json"), type=Path)
    parser.add_argument("--confidence", default=0.5)
    parser.add_argument("dialogue", nargs="+")
    args = parser.parse_args()

    transcript = args.transcript
    confidence = args.confidence
    dialogue = args.dialogue

    delta_t = 0.25
    transcript_body = [{"language_code": "en-us", "alternatives": [{"confidence": confidence, "words": [{"start_time": idx_to_time(idx, delta_t), "end_time": idx_to_time(idx+1, delta_t), "word": word} for idx, word in enumerate(dialogue)]}]}]

    pprint(transcript_body)

    with transcript.open("w") as f:
        json.dump(transcript_body, f)
