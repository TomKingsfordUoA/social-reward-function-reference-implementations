import importlib
import importlib.resources
import os
import pickle

import joblib
import torch
import typing
import yaml
import numpy as np

import pymo.data
from ...interfaces import CoSpeechGestureGenerator, Transcript


class Gesticulator(CoSpeechGestureGenerator):
    def __init__(self) -> None:
        super().__init__(
            pythonpaths=[],
            pymo_path=os.path.join(os.path.dirname(__file__), '../../models/gesticulator/gesticulator/pymo'),
        )
        with self.manage_dependencies():
            from ...models.gesticulator.gesticulator.data_processing.process_dataset import create_embedding
            from ...models.gesticulator.gesticulator.model.model import GesticulatorModel

            # nb: importlib.resources doesn't support relative packages hence we resolve an absolute package
            gesticulator_resources_package = importlib.import_module(".resources", package=__package__).__name__
            with importlib.resources.path(gesticulator_resources_package, '.') as p_resources:
                model = '20210925_text_only_early_stopping'
                checkpoint_path = os.path.join(p_resources, model, 'trained_model.ckpt')
                with open(os.path.join(p_resources, model, 'hparams.yaml')) as f_hparams:
                    hparams = yaml.safe_load(f_hparams, )
                hparams['result_dir'] = str(p_resources)
            self._hparams = hparams

            gesticulator_package = importlib.import_module('...models.gesticulator.gesticulator', package=__package__).__name__
            with importlib.resources.path(f'{gesticulator_package}.utils', 'data_pipe.sav') as p_data_pipe:
                self._data_pipeline = joblib.load(str(p_data_pipe))
            self._embedding_model = create_embedding(hparams['text_embedding'])
            self._model = GesticulatorModel.load_from_checkpoint(
                args=hparams,
                checkpoint_path=checkpoint_path,
                inference_mode=True,
            ).eval()

    def generate_gestures(self, transcript: Transcript, serialize: bool = False) -> typing.Tuple[pymo.data.MocapData, typing.Optional[bytes]]:
        with self.manage_dependencies():
            from ...interfaces import GeneaTranscript
            from ...models.gesticulator.gesticulator.data_processing.text_features.parse_json_transcript import \
                encode_json_transcript_with_bert
            from ...models.gesticulator.gesticulator.interface.gesture_predictor import GesturePredictor

            # Preprocess the transcript into text features:
            genea_transcript = GeneaTranscript(_elements=[GeneaTranscript.Element(alternatives=[transcript], language_code='')])
            transcription_segments = genea_transcript.to_dict()
            text_encoding = encode_json_transcript_with_bert(
                transcription_segments=transcription_segments,
                tokenizer=self._embedding_model[0],
                bert_model=self._embedding_model[1],
            )

            # Upsample text features. In Gesticulator audio+text, the audio features are twice the frequency of text
            # features and an alignment by upsampling occurs, so we need to mimic this when audio is absent:
            cols = np.linspace(0, text_encoding.shape[0], endpoint=False, num=text_encoding.shape[0] * 2, dtype=int)
            text_encoding = text_encoding[cols, :]

            # Convert from numpy array to torch tensor:
            text_encoding_tensor = torch.as_tensor(torch.from_numpy(text_encoding)).float()

            # Pad text features so motion length is equal to transcript length:
            gesture_predictor = GesturePredictor(
                model=self._model,
                feature_type='MFCC',  # audio features; unused
            )
            text_encoding_tensor = gesture_predictor._pad_text_features(text_encoding_tensor)

            # Add a batch dimension of 1:
            text_encoding_tensor = text_encoding_tensor.unsqueeze(0)

            # Perform prediction:
            predicted_gestures = self._model.forward(
                torch.zeros(text_encoding_tensor.size()),  # audio features unused by text-only model
                text_encoding_tensor,
                use_conditioning=True,
                motion=None,
            )

            # Transform prediction into pymo.data.MocapData:
            mocap_data = self._data_pipeline.inverse_transform(predicted_gestures.detach().numpy())[0]

            # Correct framerate:
            mocap_data.framerate = (transcript.words[-1].end_time - transcript.words[0].start_time) / mocap_data.values.shape[0]

            # Optionally, serialize:
            s_mocap_data = None
            if serialize:
                s_mocap_data = pickle.dumps(mocap_data)

            return mocap_data, s_mocap_data
