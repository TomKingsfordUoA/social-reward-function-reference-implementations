import contextlib
import importlib.resources
import importlib.util
import os
import pickle
import sys

import numpy as np

import pymo.data
import srf_interfaces
from srf_interfaces.transcripts import Transcript
import reference_implementations.yoon2018


def replace_module(name: str, path: str) -> None:
    pymo_data_spec = importlib.util.spec_from_file_location(name, path)
    if pymo_data_spec is None:
        raise ImportError()
    if name in sys.modules:
        del sys.modules[name]
    pymo_mod = importlib.util.module_from_spec(pymo_data_spec)
    pymo_data_spec.loader.exec_module(pymo_mod)
    sys.modules[name] = pymo_mod
    importlib.invalidate_caches()
    __import__(name)


@contextlib.contextmanager
def manage_dependencies():
    # Prepend paths to PYTHONPATH:
    paths = [os.path.join(os.path.dirname(__file__), '../yoon2018/scripts')]
    for path in reversed(paths):
        sys.path.insert(0, path)

    pymo_path = os.path.join(os.path.dirname(__file__), '../yoon2018/scripts/pymo')
    pymo_modules = [
        os.path.splitext(filename)[0]
        for filename in os.listdir(pymo_path)
    ]
    pymo_modules = [f'pymo.{filename}' if filename != '__init__' else 'pymo'
                    for filename in pymo_modules
                    if filename != '__pycache__']
    pymo_modules_before = {
        mod_name: sys.modules[mod_name] if mod_name in sys.modules else None
        for mod_name in pymo_modules
    }
    for mod_name in pymo_modules:
        mod_name_split = mod_name.split('.')
        if len(mod_name_split) == 1:
            mod_filename = '__init__.py'
        elif len(mod_name_split) == 2:
            mod_filename = f'{mod_name_split[1]}.py'
        else:
            raise ValueError()

        replace_module(
            name=mod_name,
            path=os.path.join(pymo_path, mod_filename),
        )

    # sanity check (Mirror is only present in the old pymo used by Yoon2018)
    import pymo.preprocessing
    pymo.preprocessing.Mirror()

    yield

    # Restore pymo modules
    for mod_name, mod in pymo_modules_before.items():
        if mod is None:
            continue
        sys.modules[mod_name] = pymo_modules_before[mod_name]
        importlib.invalidate_caches()
        __import__(mod_name)

    # Restore PYTHONPATH:
    for path in paths:
        sys.path.remove(path)


class Yoon2018(srf_interfaces.CoSpeechGestureGenerator):
    def __init__(self) -> None:
        with manage_dependencies():
            with importlib.resources.path('reference_implementations.yoon2018.resource', 'baseline_icra19_checkpoint_100.bin') as p_checkpoint:
                checkpoint_path = str(p_checkpoint)
            with importlib.resources.path('reference_implementations.yoon2018.resource', 'vocab_cache.pkl') as p_vocab_cache:
                vocab_cache_path = str(p_vocab_cache)

            self._args, self._generator, self._loss_fn, _, self._out_dim = \
                reference_implementations.yoon2018.utils.train_utils.load_checkpoint_and_model(
                    checkpoint_path=checkpoint_path,
                    _device=reference_implementations.yoon2018.inference.device,
                    verbose=0,
                )

            # load lang_model
            with open(vocab_cache_path, 'rb') as f:
                self._lang_model = pickle.load(f)

    def generate_gestures(self, transcript: Transcript) -> pymo.data.MocapData:
        with manage_dependencies():
            word_list = [(timed_word.word, timed_word.start_time, timed_word.end_time)
                         for timed_word in transcript.words
                         if len(timed_word.word) > 0]

            # Inference
            out_poses = reference_implementations.yoon2018.inference.generate_gestures(
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
            mocap_data = reference_implementations.yoon2018.inference.make_mocap_data(out_poses)

        return mocap_data
