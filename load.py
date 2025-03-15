# SPDX-License-Identifier: MIT
# Copyright (c) 2025-present K. S. Ernest (iFire) Lee

import pandas as pd
import zipfile
import requests
from libreco.algorithms import PinSage
from libreco.data import DatasetFeat, split_by_ratio_chrono, split_multi_value, DataInfo
import os
import logging
import tensorflow as tf

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# important to reset graph if model is loaded in the same shell.
tf.compat.v1.reset_default_graph()

data_info = DataInfo.load("model_path_data", model_name="pinsage")
print(data_info)

model = PinSage.load(
    path="model_path_model", model_name="pinsage", data_info=data_info, manual=True
)



print("Num GPUs Available: ", len(tf.config.experimental.list_physical_devices("GPU")))

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Download and extract the dataset if not already done
url = "http://files.grouplens.org/datasets/movielens/ml-20m.zip"
local_filename = "ml-20m.zip"
extract_dir = "ml-20m"

if not os.path.exists(extract_dir):
    logger.info("Downloading dataset...")
    response = requests.get(url)
    with open(local_filename, "wb") as f:
        f.write(response.content)

    logger.info("Extracting dataset...")
    with zipfile.ZipFile(local_filename, "r") as zip_ref:
        zip_ref.extractall()

    os.rename("ml-20m", extract_dir)
    logger.info("Dataset downloaded and extracted.")

logger.info("Loading data...")
ratings = pd.read_csv("ml-20m/ratings.csv")
movies = pd.read_csv("ml-20m/movies.csv")

data = pd.merge(ratings, movies, on="movieId")

# Convert column names to lowercase
data.columns = data.columns.str.lower()

# Rename columns to match expected names
data.rename(
    columns={
        "userid": "user",
        "movieid": "item",
        "timestamp": "time",
        "rating": "label",
    },
    inplace=True,
)

# Normalize the label to a range from 0 to 1
max_label = data["label"].max()
data["label"] = data["label"] / max_label

sparse_col = ["genres_1", "genres_2", "genres_3"]
dense_col = []
multi_value_col = ["genres"]
user_col = []
item_col = ["genres_1", "genres_2", "genres_3"]

# Split multi-value features
logger.info("Splitting multi-value features...")
data, multi_sparse_col, multi_user_col, multi_item_col = split_multi_value(
    data,
    multi_value_col,
    sep="|",
    max_len=[3],
    pad_val="missing",
    user_col=user_col,
    item_col=item_col,
)

# Update user and item columns
user_col += multi_user_col
item_col += multi_item_col

# Ensure 'data' contains 'user' and 'time' columns
assert "user" in data.columns and "time" in data.columns, (
    "data must contain 'user' and 'time' columns"
)

# Split the data into training and evaluation sets
logger.info("Splitting data into training and evaluation sets...")
train_data, test_data = split_by_ratio_chrono(
    data, test_size=0.2
)  # 0.95 for 20 minutes of training

# Prepare the dataset for PinSage
logger.info("Preparing dataset for PinSage...")

train_data, data_info = DatasetFeat.build_trainset(
    train_data, user_col, item_col, sparse_col, dense_col
)
test_data = DatasetFeat.build_testset(test_data)
print(data_info)

data_info = DataInfo.load("model_path_data", model_name="pinsage")
print(data_info)

pinsage = PinSage(
    task="ranking",
    data_info=data_info,
    loss_type="max_margin",
    paradigm="i2i",
    embed_size=16,
    n_epochs=2,
    lr=3e-4,
    lr_decay=False,
    reg=None,
    batch_size=16384,
    num_neg=3,
    dropout_rate=0.0,
    num_layers=2,
    num_neighbors=3,
    num_walks=10,
    neighbor_walk_len=2,
    sample_walk_len=5,
    termination_prob=0.5,
    margin=1.0,
    sampler="random",
    start_node="random",
    focus_start=False,
    seed=42,
)

pinsage = PinSage.load(
    path="model_path_model", model_name="pinsage", data_info=data_info, manual=True
)

# Make predictions and recommendations
logger.info("Making predictions and recommendations...")

recommendations = pinsage.recommend_user(user=1, n_rec=7)
print("recommendation: ", recommendations)

# Load movies data
movies = pd.read_csv("ml-20m/movies.csv")

# Merge recommendations with movie titles
recommended_movies = movies[movies["movieId"].isin(recommendations)]
print("Recommended movie titles: ", recommended_movies["title"].tolist())
