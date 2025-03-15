```
SPDX-License-Identifier: MIT
Copyright (c) 2025-present K. S. Ernest (iFire) Lee
```

# Linux or WSL Windows 11

```
"${SHELL}" <(curl -L micro.mamba.pm/install.sh)
source ~/.bashrc 
micromamba create -n pinsage python==3.12 
micromamba activate pinsage
micromamba install llvm scipy requests scikit-learn transformers pandas
pip3 install librecommender tf-keras tensorflow[and-cuda]
pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu126
python3 -c "import tensorflow as tf; print(tf.config.list_physical_devices('GPU'))"
python3 movie_prediction.py 
```
