import importlib
import importlib.resources
import os

import joblib
import torch
import yaml

import pymo.data
from ..utils import manage_dependencies
from ...interfaces import CoSpeechGestureGenerator, Transcript

_manage_dependencies = lambda: manage_dependencies(
    pythonpaths=[],
    pymo_path=os.path.join(os.path.dirname(__file__), '../../models/gesticulator/gesticulator/pymo'),
)


class Gesticulator(CoSpeechGestureGenerator):
    def __init__(self) -> None:
        with _manage_dependencies():
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
        with _manage_dependencies():
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
