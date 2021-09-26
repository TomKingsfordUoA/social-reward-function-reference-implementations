import importlib.resources
import importlib.util
import os
import pickle

import numpy as np

import pymo.data
from ..utils import manage_dependencies
from ...interfaces import CoSpeechGestureGenerator, Transcript
from ...models import yoon2018

_manage_dependencies = lambda: manage_dependencies(
    pythonpaths=[os.path.join(os.path.dirname(__file__), '../../models/yoon2018/scripts')],
    pymo_path=os.path.join(os.path.dirname(__file__), '../../models/yoon2018/scripts/pymo'),
)


class Yoon2018(CoSpeechGestureGenerator):
    def __init__(self) -> None:
        with _manage_dependencies():
            # nb: importlib.resources doesn't support relative packages hence we resolve an absolute package
            yoon2018_resources_package = importlib.import_module(".resources", package=__package__).__name__
            with importlib.resources.path(yoon2018_resources_package, 'baseline_icra19_checkpoint_100.bin') as p_checkpoint:
                checkpoint_path = str(p_checkpoint)
            with importlib.resources.path(yoon2018_resources_package, 'vocab_cache.pkl') as p_vocab_cache:
                vocab_cache_path = str(p_vocab_cache)

            self._args, self._generator, self._loss_fn, _, self._out_dim = \
                yoon2018.utils.train_utils.load_checkpoint_and_model(
                    checkpoint_path=checkpoint_path,
                    _device=yoon2018.inference.device,
                    verbose=0,
                )

            # load lang_model
            with open(vocab_cache_path, 'rb') as f:
                self._lang_model = pickle.load(f)

    def generate_gestures(self, transcript: Transcript) -> pymo.data.MocapData:
        with _manage_dependencies():
            word_list = [(timed_word.word, timed_word.start_time, timed_word.end_time)
                         for timed_word in transcript.words
                         if len(timed_word.word) > 0]

            # Inference
            out_poses = yoon2018.inference.generate_gestures(
                args=self._args,
                pose_decoder=self._generator,
                lang_model=self._lang_model,
                words=word_list,
                verbose=0,
            )

            # Denormalize
            mean = np.array(self._args.data_mean).squeeze()
            std = np.array(self._args.data_std).squeeze()
            std = np.clip(std, a_min=0.01, a_max=None)
            out_poses = np.multiply(out_poses, std) + mean

            # Transform poses to MocapData:
            mocap_data = yoon2018.inference.make_mocap_data(out_poses)

        return mocap_data
