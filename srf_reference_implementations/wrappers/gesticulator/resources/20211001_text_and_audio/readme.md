The default parameters were used to retrain the model, using both text and audio features.

This serves as a comparison to both the pretrained model and the text-only model (i.e. it serves as a sanity check that nothing went horribly wrong either in removing audio features or in other code changes).

The results was a loss of 0.0163 after 80 epochs, with a minimum of 0.0117 after 70 epochs.

