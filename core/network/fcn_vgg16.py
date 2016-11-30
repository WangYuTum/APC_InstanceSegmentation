"""Compact interfaces lib for a neural network including:
-- Interfaces to define a nn layer e.g conv, pooling, relu, fcn, dropout etc
-- Interfaces for variable initialization
-- Interfaces for network data post-processing e.g logging, visualizing and so on
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import sys
sys.path.append("..")

import tensorflow as tf
import numpy as np
import nn
import data_utils as dt

DATA_DIR = 'data'

class FCN16VGG:

    def __init__(self, data_dir=None):
        """Dict keys:['conv5_1', 'fc6', 'conv5_3', 'fc7', 'fc8', 'conv5_2', 'conv4_1', 'conv4_2', 'conv4_3', 'conv3_3','conv3_2', 'conv3_1', 'conv1_1', 'conv1_2', 'conv2_2', 'conv2_1']"""
        # Load VGG16 pretrained weight
        data_dict = dt.load_vgg16_weight(data_dir)
        self.data_dict = data_dict
        
        # Init other necessary parameters
    def _build_model(self, feed_dict, image, is_train=True, random_init_fc8=False):
        model = {}
        
        model['conv1_1'] = nn.conv_layer(image, feed_dict, "conv1_1")
        model['conv1_2'] = nn.conv_layer(model['conv1_1'], feed_dict, "conv1_2")
        model['pool1'] = nn.max_pool_layer(model['conv1_2'], feed_dict, "pool1")

        model['conv2_1'] = nn.conv_layer(model['pool1'], feed_dict, "conv2_1")
        model['conv2_2'] = nn.conv_layer(model['conv2_1'], feed_dict, "conv2_2")
        model['pool2'] = nn.max_pool_layer(model['conv2_2'], feed_dict, "pool2")
        
        model['conv3_1'] = nn.conv_layer(model['pool2'], feed_dict, "conv3_1")
        model['conv3_2'] = nn.conv_layer(model['conv3_1'], feed_dict, "conv3_2")
        model['conv3_3'] = nn.conv_layer(model['conv3_2'], feed_dict, "conv3_3")
        model['pool3'] = nn.max_pool_layer(model['conv3_3'], feed_dict, "pool3")

        model['conv4_1'] = nn.conv_layer(model['pool3'], feed_dict, "conv4_1")
        model['conv4_2'] = nn.conv_layer(model['conv4_1'], feed_dict, "conv4_2")
        model['conv4_3'] = nn.conv_layer(model['conv4_2'], feed_dict, "conv4_3")
        model['pool4'] = nn.max_pool_layer(model['conv4_3'], feed_dict, "pool4")


        model['conv5_1'] = nn.conv_layer(model['pool4'], feed_dict, "conv5_1")
        model['conv5_2'] = nn.conv_layer(model['conv5_1'], feed_dict, "conv5_2")
        model['conv5_3'] = nn.conv_layer(model['conv5_2'], feed_dict, "conv5_3")
        model['pool5'] = nn.max_pool_layer(model['conv5_3'], feed_dict, "pool5")

        model['fconv6'] = nn.fully_conv_layer(model['pool5'], feed_dict, "fc6", dropout=is_train, keep_prob=0.5])
        model['fconv7'] = nn.fully_conv_layer(model['fconv6'], feed_dict, "fc7", dropout=is_train, keep_prob=0.5])
            
        # Unclear
        if random_init_fc8:
            model['score_fr'] = nn.score_layer(model['fconv7'], "score_fr", num_classes)
        else:
            model['score_fr'] = nn.fully_conv_layer(model['fconv7'], "score_fr",
                                                    num_classes=num_classes,
                                                    relu=False)
        return model

    def inference(self, image, num_classes):
        # Image preprocess
        # Network structure -- VGG16
        # Upsampling
        # Return predict

        model = self._build_model(self.data_dict, image, is_train=False)

        pred = tf.argmax(model['score_fr'], dimension=3)
        upscore2 = nn.upscore_layer(model['score_fr'],
                                    shape=tf.shape(model['pool4']),
                                    num_classes=num_classes,
                                    name="upscore2",
                                    ksize=4, stride=2)

        score_pool4 = nn.score_layer(model['pool4', "score_pool4",
                                     num_classes=num_classes)
        fuse_pool4 = tf.add(upscore2, score_pool4)
        upscore32 = nn.upscore_layer(fuse_pool4,
                                     shape=tf.shape(image),
                                     num_classes=num_classes,
                                     name="upscore32",
                                     ksize=32, stride=16)

        pred_up = tf.argmax(upscore32, dimension=3)
        pass

    def train(self, total_loss, learning_rate ):
        # To be implemented Later
        # Mini-batch
        # Minimize loss
        # Add necessary params to summary
        # Return train_op
        pass