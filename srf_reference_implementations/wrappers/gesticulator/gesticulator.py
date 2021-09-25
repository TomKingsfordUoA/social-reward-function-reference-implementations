import contextlib
import importlib
import importlib.resources
import os
import sys

import joblib
import torch
import yaml

import pymo.data
from ...interfaces import CoSpeechGestureGenerator, Transcript


# FIXME(TK): Move to wrappers.utils and share with yoon2018. This is a more advanced version than wrappers.yoon2018's
@contextlib.contextmanager
def manage_dependencies():
    # Prepend paths to PYTHONPATH:
    paths = [
        os.path.join(os.path.dirname(__file__), '../../models/gesticulator/gesticulator'),
    ]
    for path in reversed(paths):
        sys.path.insert(0, path)

    # pymo_path = os.path.join(os.path.dirname(__file__), '../../models/yoon2018/scripts/pymo')
    pymo_path = os.path.join(os.path.dirname(__file__), '../../models/gesticulator/gesticulator/pymo')
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
        if mod_name in sys.modules:
            del sys.modules[mod_name]
    specs_and_modules = dict()
    for mod_name in pymo_modules:
        mod_name_split = mod_name.split('.')
        if len(mod_name_split) == 1:
            mod_filename = '__init__.py'
        elif len(mod_name_split) == 2:
            mod_filename = f'{mod_name_split[1]}.py'
        else:
            raise ValueError()

        pymo_data_spec = importlib.util.spec_from_file_location(mod_name, os.path.join(pymo_path, mod_filename))
        if pymo_data_spec is None:
            raise ImportError()
        pymo_mod = importlib.util.module_from_spec(pymo_data_spec)
        specs_and_modules[mod_name] = (pymo_data_spec, pymo_mod)
        sys.modules[mod_name] = pymo_mod
    importlib.invalidate_caches()
    globals()['pymo'] = sys.modules['pymo']
    for mod_name in pymo_modules:
        parent_module, _, child_module = mod_name.rpartition('.')
        if parent_module:
            setattr(sys.modules[parent_module], child_module, sys.modules[mod_name])
    modules_to_be_executed = set(specs_and_modules.keys())
    while len(modules_to_be_executed):
        modules_executed_this_loop = set()
        for mod_name in modules_to_be_executed:
            spec, mod = specs_and_modules[mod_name]
            try:
                spec.loader.exec_module(mod)
                modules_executed_this_loop.add(mod_name)
            except (ImportError, NameError):
                pass
        if modules_to_be_executed and not modules_executed_this_loop:  # prevent infinite loops
            raise ImportError()
        modules_to_be_executed -= modules_executed_this_loop
    importlib.invalidate_caches()

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
    globals()['pymo'] = sys.modules['pymo']

    # Restore PYTHONPATH:
    for path in paths:
        sys.path.remove(path)


class Gesticulator(CoSpeechGestureGenerator):
    def __init__(self) -> None:
        with manage_dependencies():
            from ...models.gesticulator.gesticulator.data_processing.process_dataset import create_embedding
            from ...models.gesticulator.gesticulator.model.model import GesticulatorModel

            # nb: importlib.resources doesn't support relative packages hence we resolve an absolute package
            gesticulator_resources_package = importlib.import_module(".resources", package=__package__).__name__
            with importlib.resources.path(gesticulator_resources_package, '.') as p_resources:
                model = '20210925_text_only_early_stopping'
                checkpoint_path = os.path.join(p_resources, model, 'trained_model.ckpt')
                with open(os.path.join(p_resources, model, 'hparams.yaml')) as f_hparams:
                    hparams = yaml.load(f_hparams)
                hparams['result_dir'] = str(p_resources)

            gesticulator_package = importlib.import_module('...models.gesticulator.gesticulator', package=__package__).__name__
            with importlib.resources.path(f'{gesticulator_package}.utils', 'data_pipe.sav') as p_data_pipe:
                self._data_pipeline = joblib.load(str(p_data_pipe))
            self._embedding_model = create_embedding(hparams['text_embedding'])
            self._model = GesticulatorModel.load_from_checkpoint(
                args=hparams,
                checkpoint_path=checkpoint_path,
                inference_mode=True,
            ).eval()

    def generate_gestures(self, transcript: Transcript) -> pymo.data.MocapData:
        with manage_dependencies():
            from ...interfaces import GeneaTranscript
            from ...models.gesticulator.gesticulator.data_processing.text_features.parse_json_transcript import \
                encode_json_transcript_with_bert

            # Preprocess the transcript into text features:
            genea_transcript = GeneaTranscript(_elements=[GeneaTranscript.Element(alternatives=[transcript], language_code='')])
            transcription_segments = genea_transcript.to_dict()
            text_encoding = encode_json_transcript_with_bert(
                transcription_segments=transcription_segments,
                tokenizer=self._embedding_model[0],
                bert_model=self._embedding_model[1],
            )
            text_encoding_tensor = torch.as_tensor(torch.from_numpy(text_encoding)).float().unsqueeze(0)

            # Perform prediction:
            predicted_gestures = self._model.forward(text_encoding_tensor, text_encoding_tensor, use_conditioning=True, motion=None)

            # Transform prediction into pymo.data.MocapData:
            mocap_data = self._data_pipeline.inverse_transform(predicted_gestures.detach().numpy())[0]
            return mocap_data
