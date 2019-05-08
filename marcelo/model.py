import numpy
import pandas as pd
from keras.models import Sequential, Dense, LSTM
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error

class Model:
    def read_data(self, filename):
        data = pd.read_csv(filename)
        
    def train_model(self):
        pass
    