import pickle

with open('models/encoders.pickle', 'rb') as handle:
    encoders = pickle.load(handle)