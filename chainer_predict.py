# -*- coding: utf-8 -*-

import os
import argparse
import json

import numpy as np

import chainer
import chainer.functions as F
import chainer.links as L
from chainer import reporter
from chainer import training
from chainer.training import extensions

class AutoEncoder(chainer.Chain):
    def __init__(self, loss_func):
        self.loss_func = loss_func
        super(AutoEncoder, self).__init__()

        with self.init_scope():
            self.conv1 = L.Convolution2D(1, 8, ksize=3)
            self.deconv1 = L.Deconvolution2D(8, 1, ksize=3)

    def predict(self, x):
        h = self.conv1(x)
        h = F.relu(h)
        h = self.deconv1(h)
        y = F.sigmoid(h)
        return y

    def __call__(self, x, t):
        y = self.predict(x)
        loss = self.loss_func(y, t)
        reporter.report({'loss': loss})
        return loss

class MyMnist(chainer.dataset.DatasetMixin):
    def __init__(self):
        train, test = chainer.datasets.get_mnist(ndim=3)
        self.train = train
        self.test = test
        self.pos = -1
        
    def __len__(self):
        return len(self.train)
    
    def __getitem__(self, i):
        return self.train[i][0]

    def next(self):
        self.pos += 1
        ret = self[self.pos]
        return ret

    def reset(self):
        self.pos = -1
      
class MnistAEIterator(chainer.dataset.Iterator):
    def __init__(self, dataset, batch_size):
        self.dataset = dataset
        self.batch_size = batch_size
        self.pos = 0
        self.epoch = 0

    def fetch(self):
        self.pos += self.batch_size
        data = []
        try:
            for i in range(self.batch_size):
                data.append(self.dataset.next())
        except:
            self.pos = 0
            self.epoch += 1
            self.dataset.reset()
        return data

    def __next__(self):
        data = self.fetch()
        if len(data) <= 0:
            data = self.fetch()
        data = np.asarray(data)
        return data, data

    @property
    def epoch_detail(self):
        ed = self.epoch + float(self.pos / len(self.dataset))
        return ed

def convert(batch, device):
    if device >= 0:
        batch = cuda.to_gpu(batch)
    return batch

def arg():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', type=str, default='model.npz')
    parser.add_argument('--out', type=str, default='out')
    args = parser.parse_args()
    return args

def main():
    args = arg()
    model = AutoEncoder(F.mean_squared_error)
    chainer.serializers.load_npz(args.model, model)

    train, test = chainer.datasets.get_mnist(ndim=3)
    img = train[0][0]
    example_input = img.reshape((1, 1, 28, 28))
    x = chainer.Variable(example_input)
    y = model.predict(x)

    import matplotlib.pyplot as plt
    img1 = img.reshape(28, 28)
    plt.subplot(1,2,1)
    plt.imshow(img1)
    y = y.data.reshape(28, 28)
    plt.subplot(1,2,2)
    plt.imshow(y)
    plt.show()

if __name__ == '__main__':
    main()
