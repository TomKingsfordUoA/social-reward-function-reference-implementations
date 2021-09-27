"""
The purpose of this script is to evaluate the loss of the pretrained model with respect to the GENEA dataset. Since we
have made changes to Gesticulator to support text-only features, we need to retrain the model. Ensuring we achieve a
similar loss is an important sanity check that retraining didn't fail to converge, or otherwise degrade model performance
too significantly.
"""

import os
import statistics
from argparse import ArgumentParser
from pathlib import Path

import torch
from tqdm import tqdm

from srf_reference_implementations.wrappers.utils import manage_dependencies


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--checkpoint', type=Path, default='./default.ckpt')
    parser.add_argument('--data_dir', type=Path, default='../dataset/processed_data')
    args = parser.parse_args()

    if not os.path.isfile(args.checkpoint):
        raise FileNotFoundError(args.checkpoint)
    if not os.path.isdir(args.data_dir):
        raise FileNotFoundError(args.data_dir)

    with manage_dependencies(
        pythonpaths=[],
        pymo_path=os.path.join(os.path.dirname(__file__), '../../../../models/gesticulator/gesticulator/pymo'),
    ):
        from srf_reference_implementations.models.gesticulator.gesticulator.model.model import GesticulatorModel
        model = GesticulatorModel.load_from_checkpoint(
            args.checkpoint,
            data_dir=args.data_dir,
            inference_mode=True,
            result_dir='..',
            run_name='pretrained',
            disable_audio=False,
        )
        model.load_datasets()

        training_loader = torch.utils.data.DataLoader(model.train_dataset, batch_size=32)
        training_batch_losses = []
        for idx, batch in enumerate(tqdm(training_loader)):
            predicted_gesture = model.forward(
                audio=batch['audio'],
                text=batch['text'],
                use_conditioning=False,
                motion=None,
                use_teacher_forcing=False,
            )
            true_gesture = batch['output'][:, model.hparams.past_context:-model.hparams.future_context]
            batch_loss = model.loss(predicted_gesture, true_gesture)
            training_batch_losses.append(float(batch_loss))

        print(f'training_loss=(mean={statistics.mean(training_batch_losses)}, std={statistics.stdev(training_batch_losses)})')
        # print(f'validation_loss={statistics.mean(validation_batch_losses)}')  # TODO(TK): implement
