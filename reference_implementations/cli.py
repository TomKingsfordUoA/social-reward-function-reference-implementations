import argparse
import importlib
import json
import os
import pathlib

from pymo.writers import BVHWriter
from srf_interfaces.transcripts import GeneaTranscript


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-t', '--transcript',
        help='Path to a GENEA-formatted transcript',
        required=True,
        type=pathlib.Path,
    )
    parser.add_argument(
        '-o', '--output_dir',
        help='Path of an empty or non-existent directory to place outputs',
        type=pathlib.Path,
        default='bvh_output',
    )
    parser.add_argument(
        '-m', '--model',
        help='Model to use, expressed as an import path to a class implementing the CoSpeechGestureGenerator interface',
        type=str,
        default='reference_implementations.Yoon2018',
    )
    args = parser.parse_args()

    # Check args:
    # output_dir must be non-existent or empty (i.e. must not be populated):
    if os.path.isdir(args.output_dir) and os.listdir(args.output_dir):
        raise ValueError(f'output_dir must be empty or non-existent: {args.output_dir}')

    # Load model:
    model_split = args.model.split('.')
    mod = importlib.import_module(name='.'.join(model_split[:-1]))
    cls = getattr(mod, model_split[-1])
    model = cls()

    # Read the transcript:
    with open(args.transcript) as f_transcript:
        d_transcript = json.load(f_transcript)
        genea_transcript = GeneaTranscript.from_dict(d_transcript)

    # Make prediction:
    mocap_data = model.generate_gestures(transcript=genea_transcript.transcript)

    # Write prediction to BVH file:
    if not os.path.isdir(args.output_dir):
        os.mkdir(args.output_dir)
    bvh_writer = BVHWriter()
    bvh_path = os.path.join(args.output_dir, f'{os.path.split(args.transcript)[-1]}.bvh')
    with open(bvh_path, 'w') as f:
        bvh_writer.write(mocap_data, f)


if __name__ == '__main__':
    main()
