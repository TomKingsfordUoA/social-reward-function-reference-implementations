"""
This script takes a newline-delimited file of dialogue, generates transcripts, generates gestures, and submits to
a GENEA Visualizer (https://github.com/jonepatr/genea_visualizer) server to generate video files of that dialogue.
"""

import importlib
from argparse import ArgumentParser
from pathlib import Path
from tempfile import TemporaryFile, NamedTemporaryFile
from time import sleep

import requests

from pymo.writers import BVHWriter
from scripts.generate_simple_transcript import generate_transcript
from srf_reference_implementations.interfaces import GeneaTranscript

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--genea-visualizer-path", default="http://127.0.0.1:5001")
    parser.add_argument("--dialogues-file", type=Path, default=Path("dialogue.txt"))
    parser.add_argument("--confidence", type=float, default=0.5)
    parser.add_argument("--delta-t-s", type=float, default=0.5)
    parser.add_argument("--model", type=str, default='srf_reference_implementations.Gesticulator')
    parser.add_argument("--output-dir", type=Path, default=Path("gesticulator"))
    args = parser.parse_args()

    genea_visualizer_path: str = args.genea_visualizer_path
    dialogues_file: Path = args.dialogues_file
    confidence: float = args.confidence
    delta_t_s: float = args.delta_t_s
    model_name: str = args.model
    output_dir: Path = args.output_dir

    # Load model:
    model_split = model_name.split('.')
    mod = importlib.import_module(name='.'.join(model_split[:-1]))
    cls = getattr(mod, model_split[-1])
    model = cls()

    with args.dialogues_file.open() as f:
        dialogues = [dialogue.strip().split(" ") for dialogue in f.read().splitlines()]

    for idx, dialogue in enumerate(dialogues):
        print(f"Starting dialogue #{idx}")

        # Generate transcript
        transcript = generate_transcript(confidence=confidence, delta_t=delta_t_s, dialogue=dialogue)
        genea_transcript = GeneaTranscript.from_dict(transcript)

        # Make gestures:
        mocap_data = model.generate_gestures(transcript=genea_transcript.transcript)

        # Write gestures to BVH file:
        with NamedTemporaryFile(mode="w") as f_bvh:
            bvh_writer = BVHWriter()
            bvh_writer.write(mocap_data, f_bvh)

            with open(f_bvh.name) as f_bvh_read:
                data_bvh = f_bvh_read.read()

        # Submit to genea visualizer
        print("Submitting request...")
        bearer = "j7HgTkwt24yKWfHPpFG3eoydJK6syAsz"
        response = requests.post(
            f"{genea_visualizer_path}/render",
            headers={
                "Authorization": f"Bearer {bearer}",
            },
            files={"file": ("data.bvh", data_bvh, "text/plain")},
        )
        response.raise_for_status()
        job_id = response.text

        # Wait for processing:
        while True:
            print("\rWaiting for processing...", end="")
            response = requests.get(
                f"{genea_visualizer_path}{job_id}",
                headers={"Authorization": f"Bearer {bearer}"},
            )
            response.raise_for_status()
            response_json = response.json()

            if response_json['state'] == "SUCCESS":
                break
            sleep(0.5)
        print("Processing done!")

        # Retrieve mp4:
        print("Retrieving mp4...")
        response = requests.get(
            f"{genea_visualizer_path}{response_json['result']}",
            headers={"Authorization": f"Bearer {bearer}"},
        )
        response.raise_for_status()
        output_dir.mkdir(parents=True, exist_ok=True)
        with output_dir.joinpath(f"result_{idx}.mp4").open("wb") as f_result:
            f_result.write(response.content)
