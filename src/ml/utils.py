import pickle
import tempfile
import numpy as np
from ratings.models import Rating
from django.db.models import F
from django.contrib.contenttypes.models import ContentType
from surprise import accuracy, Reader, Dataset, SVD
from surprise.model_selection import cross_validate
from exports import storages as exports_storages
from django.core.files.base import File
from django.conf import settings
import torch
from torch.utils.data import DataLoader
import torch.optim as optim
import torch.nn as nn
from tqdm import tqdm
from .models import MatrixFactorization, Loader
import logging
import gc
# from memory_profiler import profile

logger = logging.getLogger()
logger.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# Possible Method of data loading:

def export_ratings_dataset():
    ctype = ContentType.objects.get(app_label='anime', model='anime')
    qs = Rating.objects.filter(active=True, content_type=ctype)
    qs = qs.annotate(userId=F('user_id'), animeId=F('object_id'), rating=F('value'))
    return qs.values('userId', 'animeId', 'rating')

def qs_to_generator(queryset):
    for item in queryset.iterator():
        yield item

# @profile
def get_data_loader(dataset, columns=['userId', 'animeId', 'rating']):
    logging.info("Importing pandas...")
    import pandas as pd
    logging.info("Creating a dataframe...")
    df = pd.DataFrame(qs_to_generator(export_ratings_dataset()))
    gc.collect()
    logging.info("Done!")
    logging.info("Optimizing the dataframe...")
    df = df.astype({
        'userId': np.int32,
        'animeId': np.int32,
        'rating': np.int32 
    })
    logging.info("Done!")
    df = df[df['rating'].notna()]
    logging.info(df.info(memory_usage='deep'))
    max_rating, min_rating = df.rating.max(), df.rating.min()
    reader = Reader(rating_scale=(min_rating, max_rating))
    logging.info("Returning the dataset...")
    return Dataset.load_from_df(df[columns], reader)


# Data loading from ratings exports:

def get_data_from_csv(columns=['userId', 'animeId', 'rating']):
    import pandas as pd
    from exports.models import Export
    latest_export = Export.objects.filter(file__isnull=False).order_by('-timestamp').first()
    if not latest_export:
        raise ValueError("No export file found.")
    csv_path = latest_export.file.path
    dtype_mapping = {'userId': 'int32', 'animeId': 'int32', 'rating': 'int32'}
    df = pd.read_csv(csv_path, dtype=dtype_mapping)
    df = df[df['rating'].notna()]
    logging.info(df.info(memory_usage='deep'))
    # max_rating, min_rating = df.rating.max(), df.rating.min()
    # reader = Reader(rating_scale=(min_rating, max_rating))
    # logging.info("Returning the dataset...")
    # return Dataset.load_from_df(df[columns], reader)
    return df


def get_model_acc(trainset, model, use_rmse=True):
    testset = trainset.build_testset()
    predictions = model.test(testset)
    if not use_rmse:
        return accuracy.mae(predictions, verbose=True)
    acc = accuracy.rmse(predictions, verbose=True)
    return acc

# Training functions for each model.
def train_surprise_model(n_epochs=20, verbose=True):
    import pandas as pd
    # dataset = export_ratings_dataset()
    # loaded_data = get_data_loader(dataset)
    columns = ['userId', 'animeId', 'rating']
    df = get_data_from_csv(columns=columns)
    max_rating, min_rating = df.rating.max(), df.rating.min()
    reader = Reader(rating_scale=(min_rating, max_rating))
    logging.info("Returning the dataset...")
    loaded_data = Dataset.load_from_df(df[columns], reader)
    model = SVD(n_epochs=n_epochs, verbose=verbose)
    cv_results = cross_validate(model, loaded_data, measures=['RMSE', 'MAE'], cv=4, verbose=True)
    trainset = loaded_data.build_full_trainset()
    model.fit(trainset)
    acc = get_model_acc(trainset, model, use_rmse=True)
    acc_label = int(100 * acc)
    model_name = f"model-{acc_label}"
    export_model(model, model_name, model_type='surprise', model_ext='pkl', verbose=True)


def train_torch_model(df, model_class=MatrixFactorization, n_factors=20, batch_size=64, epochs=10, learning_rate=0.001):
    dataset = Loader(df)
    data_loader = DataLoader(dataset, batch_size=batch_size, shuffle=True)
    n_users = len(dataset.userId2idx)
    n_items = len(dataset.animeId2idx)
    model = model_class(n_users, n_items, n_factors)
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model.to(device)
    loss_function = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=learning_rate)
    logging.info("Entering the training loop...")
    for epoch in tqdm(range(epochs)):
        model.train()
        losses = []
        for x, y in data_loader:
            x, y = x.to(device), y.to(device)
            optimizer.zero_grad()
            outputs = model(x)
            loss = loss_function(outputs.squeeze(), y.type(torch.float32))
            losses.append(loss.item())
            loss.backward()
            optimizer.step()
        print("iter #{}".format(epoch), "Loss:", sum(losses) / len(losses))
    final_loss = sum(losses) / len(losses)
    logging.info("Done!")
    # model_name = "TorchModel-{final_loss}"
    # export_model(model, model_name=model_name, model_type='torch', model_ext='pth', verbose=True)

# Fuctions below designed to handle both models.
def export_model(model, model_name='model', model_type='torch', model_ext='pth', verbose=True):
    with tempfile.NamedTemporaryFile(mode='rb+') as temp_f:
        if model_type == 'surprise':
            pickle.dump({"model": model}, temp_f)
        elif model_type == 'torch':
            torch.save(model.state_dict(), temp_f.name)
        else:
            raise ValueError(f"Unsupported model type: {model_type}")
        path = f"ml/models/{model_type}/{model_name}.{model_ext}"
        path_latest = f"ml/models/{model_type}/latest.{model_ext}"
        if verbose:
            print(f"Exporting to {path} and {path_latest}")
        exports_storages.save(path, File(temp_f))
        exports_storages.save(path_latest, File(temp_f), overwrite=True)


def load_model(model_type='torch', model_ext='pth', model_class=MatrixFactorization, **model_kwargs):
    path_latest = settings.MEDIA_ROOT / f"ml/models/{model_type}/latest.{model_ext}"  
    if not path_latest.exists():
        raise FileNotFoundError(f"No saved model found at {path_latest}")
    if model_type == 'surprise':
        with open(path_latest, 'rb') as f:
            model_data = pickle.load(f)
            return model_data.get('model')
    elif model_type == 'torch':
        if model_class is None:
            raise ValueError("For Torch models, `model_class` must be provided.")
        model = model_class(**model_kwargs)
        model.load_state_dict(torch.load(path_latest))
        model.eval()
        return model
    else:
        raise ValueError(f"Unsupported model type: {model_type}")
