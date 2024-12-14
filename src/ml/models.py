import torch.nn as nn
import torch
import torch.optim as optim
from torch.utils.data.dataset import Dataset

class MatrixFactorization(nn.Module):
    def __init__(self, n_users, n_items, n_factors=20):
        super().__init__()

        self.user_factors = nn.Embedding(n_users, n_factors)
        self.item_factors = nn.Embedding(n_items, n_factors)
        self.user_factors.weight.data.uniform_(0, 0.05)
        self.item_factors.weight.data.uniform_(0, 0.05)

    def forward(self, data):
        users, items = data[:, 0], data[:, 1]
        return (self.user_factors(users) * self.item_factors(items)).sum(1)

    def predict(self, user, item):
        return self.forward(user, item)
    
class Loader(Dataset):
    def __init__(self, df):
        self.ratings = df.copy()

        users = df.userId.unique()
        titles = df.animeId.unique()

        self.userId2idx = {o:i for i,o in enumerate(users)}
        self.animeId2idx = {o:i for i,o in enumerate(titles)}

        self.idx2userId = {i:o for o,i in self.userId2idx.items()}
        self.idx2animeId = {i:o for o,i in self.animeId2idx.items()}

        self.ratings.animeId = df.animeId.apply(lambda x: self.animeId2idx[x])
        self.ratings.userId = df.userId.apply(lambda x: self.userId2idx[x])

        self.x = self.ratings.drop(['rating'], axis=1).values
        self.y = self.ratings['rating'].values
        self.x, self.y = torch.tensor(self.x), torch.tensor(self.y)

    def __getitem__(self, index):
        return (self.x[index], self.y[index])

    def __len__(self):
        return len(self.ratings)