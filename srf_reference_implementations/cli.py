import argparse
import importlib
import json
import os
import pathlib
import pickle
import sys

from pymo.writers import BVHWriter
from srf_reference_implementations.interfaces.transcripts import GeneaTranscript


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-m', '--model',
        help='Model to use, expressed as an import path to a class implementing the CoSpeechGestureGenerator interface',
        type=str,
        default='srf_reference_implementations.Yoon2018',
    )
    parser.add_argument(
        '--use_ros',
        action='store_true',
    )
    parser.add_argument(
        '-t', '--transcript',
        help='Path to a GENEA-formatted transcript',
        type=pathlib.Path,
    )
    parser.add_argument(
        '-o', '--output_dir',
        help='Path of an empty or non-existent directory to place outputs',
        type=pathlib.Path,
    )
    parser.add_argument(
        '--bvh_gestures_topic',
        help='The ROS topic to publish BVH-format gestures to',
        type=str,
        default='gestures_bvh',
    )
    args = parser.parse_args()

    # Check args:
    # TODO(TK): for ros, transcript should be acquired by subscribing to a relevant ROS topic
    if args.transcript is None:
        raise ValueError('transcript must be specified')
    # if not ((args.use_ros is not None) ^ (args.transcript is not None)):
    #     raise ValueError('use_ros and transcript are mutually exclusive and one is required')
    if not (args.use_ros ^ (args.output_dir is not None)):
        raise ValueError('use_ros and output_dir are mutually exclusive and one is required')
    if not args.use_ros and args.output_dir is None:
        args.output_dir = 'bvh_output'
    if not args.use_ros and os.path.isdir(args.output_dir) and os.listdir(args.output_dir):
        raise ValueError(f'output_dir must be empty or non-existent: {args.output_dir}')

    # Load model:
    model_split = args.model.split('.')
    mod = importlib.import_module(name='.'.join(model_split[:-1]))
    cls = getattr(mod, model_split[-1])
    model = cls()

    if args.use_ros:
        # ROS is not generally required, so do a just-in-time import. rospy will be provided on PYTHONPATH by the ROS environment
        # by a command like `source /opt/ros/melodic/setup.py`
        import rospy
        from std_msgs.msg import String

        # Read the transcript:
        # TODO(TK): for ros, transcript should be acquired by subscribing to a relevant ROS topic
        with open(args.transcript) as f_transcript:
            d_transcript = json.load(f_transcript)
            genea_transcript = GeneaTranscript.from_dict(d_transcript)

        # Make prediction:
        mocap_data, s_mocap_data = model.generate_gestures(transcript=genea_transcript.transcript, serialize=True)

        pub = rospy.Publisher(args.bvh_gestures_topic, String, queue_size=10)
        model_name = args.model.split(".")[-1]
        rospy.init_node(f'srf_{model_name}', anonymous=True)
        msg = String()
        msg.data = s_mocap_data.decode('latin1')
        pub.publish(msg)
    else:
        # Read the transcript:
        with open(args.transcript) as f_transcript:
            d_transcript = json.load(f_transcript)
            genea_transcript = GeneaTranscript.from_dict(d_transcript)

        # Make prediction:
        mocap_data, _ = model.generate_gestures(transcript=genea_transcript.transcript, serialize=False)

        # Write prediction to BVH file:
        if not os.path.isdir(args.output_dir):
            os.mkdir(args.output_dir)
        bvh_writer = BVHWriter()
        bvh_path = os.path.join(args.output_dir, f'{os.path.split(args.transcript)[-1]}.bvh')
        with open(bvh_path, 'w') as f:
            bvh_writer.write(mocap_data, f)


if __name__ == '__main__':
    main()
