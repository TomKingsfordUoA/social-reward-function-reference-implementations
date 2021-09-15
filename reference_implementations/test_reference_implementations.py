import contextlib
import importlib.resources
import os
import pickle
import sys

import numpy as np

import reference_implementations
import reference_implementations.yoon2018 as yoon2018


@contextlib.contextmanager
def temporarily_prepend_to_python_path(*paths):
    for path in reversed(paths):
        sys.path.insert(0, path)
    yield
    for path in paths:
        sys.path.remove(path)


def test_yoon2018_generate_gestures() -> None:
    # TODO(TK): eventually, move this to a wrapper and then test the wrapper
    # TODO(TK): consider bundling the downloaded resources with the repo, or automatically downloading them in code

    with temporarily_prepend_to_python_path(os.path.join(os.path.dirname(__file__), 'yoon2018/scripts')):

        with importlib.resources.path('reference_implementations.yoon2018.resource', 'baseline_icra19_checkpoint_100.bin') as p_checkpoint:
            checkpoint_path = str(p_checkpoint)
        with importlib.resources.path('reference_implementations.yoon2018.resource', 'vocab_cache.pkl') as p_vocab_cache:
            vocab_cache_path = str(p_vocab_cache)
        with importlib.resources.path('reference_implementations.yoon2018.resource', 'sample_genea_transcript.json') as p_transcript:
            transcript_path = str(p_transcript)

        args, generator, loss_fn, lang_model, out_dim = yoon2018.utils.train_utils.load_checkpoint_and_model(
            checkpoint_path,
            yoon2018.inference.device,
        )

        # load lang_model
        with open(vocab_cache_path, 'rb') as f:
            lang_model = pickle.load(f)

        # prepare input
        transcript = yoon2018.utils.data_utils.SubtitleWrapper(transcript_path).get()

        word_list = []
        for wi in range(len(transcript)):
            word_s = float(transcript[wi]['start_time'][:-1])
            word_e = float(transcript[wi]['end_time'][:-1])
            word = transcript[wi]['word']

            word = yoon2018.inference.normalize_string(word)
            if len(word) > 0:
                word_list.append([word, word_s, word_e])

        # inference
        out_poses = yoon2018.inference.generate_gestures(args, generator, lang_model, word_list)

        # unnormalize
        mean = np.array(args.data_mean).squeeze()
        std = np.array(args.data_std).squeeze()
        std = np.clip(std, a_min=0.01, a_max=None)
        out_poses = np.multiply(out_poses, std) + mean

        # make mocap data:
        mocap_data = yoon2018.inference.make_mocap_data(out_poses)
        assert isinstance(mocap_data, list)
        assert len(mocap_data) == 1
        assert mocap_data[0].values.shape == (50, 174)
