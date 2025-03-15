# Movie Recommendation System with PinSage

This repository contains a movie recommendation system built using the PinSage algorithm from the LibRecommender library. The system leverages collaborative filtering and graph-based techniques to provide personalized movie recommendations based on the MovieLens 20M dataset.

## Features

- **Graph-Based Recommendations**: Utilizes PinSage for item-to-item (i2i) recommendations.
- **Multi-Value Feature Handling**: Processes multi-genre movie data using genre splitting.
- **Chronological Split**: Splits dataset chronologically for realistic time-based evaluation.
- **GPU Acceleration**: Supports TensorFlow GPU acceleration for faster training.
- **Model Persistence**: Saves trained models for later inference.

## Installation

1. Clone the repository:

```bash
git clone https://github.com/V-Sekai-fire/vsk-session-item-recommendation-01
cd movie-recommendation-pinsage
```

2. Install Mac or Linux requirements:

```bash
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

## Usage

1. Run the script:

```bash
python recommenda.py
```

2. Expected Output:

```
* 8 hours to train
• Automatic dataset download and extraction
• Training logs with evaluation metrics (precision/recall)
• Example prediction for user 1
• Top 7 movie recommendations with titles
```

## Data Processing Pipeline

1. Downloads MovieLens 20M dataset
2. Merges ratings and movie metadata
3. Normalizes ratings (0-1 scale)
4. Processes multi-value genre features
5. Creates chronological train/test split (80/20)

## Model Configuration

- **Algorithm**: PinSage (graph neural network)
- **Task**: Ranking with max-margin loss
- **Embedding Size**: 16
- **Training**: 2 epochs, 16,384 batch size
- **Negative Sampling**: 3 negatives per positive
- **Graph Parameters**: 2 layers, 3 neighbors per node

## License

MIT License - See [LICENSE](LICENSE) for details.

## Acknowledgments

- MovieLens dataset from GroupLens Research
- LibRecommender library
- TensorFlow ecosystem

This implementation demonstrates modern recommendation system techniques using graph neural networks, suitable for both educational purposes and as a foundation for production systems.
