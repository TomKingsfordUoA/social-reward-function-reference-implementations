Performed early stopping on the training loss (patience = 10).

Validation loss seems to be unreliable. Subjectively, we see validation loss plateau or increase even as the training loss is decreasing but also the gestures are looking more natural. This is likely because the MSE metric is invalid insofar as legitimate gestures with small deviations toward the shoulder can yield large squared errors at the wrist, but still be legitimate.

It is assumed that, regardless of validation loss, a lower training loss corresponds to better gestures (or at least, this is the best assumption we can make).

In this trial, text features but not audio features were used. This is required for co-speech gestures.

The final loss was 0.0201 and the best loss was 0.017. Training ran for 32 epochs and the best loss was at epoch 22.
