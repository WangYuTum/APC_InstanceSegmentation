"""Functions for loading and preprocessing dataset"""

from __future__ import print_function

from PIL import Image
import os
import sys
import random
import numpy as np
import glob
from collections import namedtuple
from scipy.misc import imsave

# define a data structure
Label_City = namedtuple( 'Label' , ['name', 'labelId', 'trainId', 'color',] )


class CityDataSet():

    def __init__(self, params):
        ''' type: 'train', 'val', 'test' '''
        self.dataset_type = params.get('dataset','train')
        self.city_dir = params.get('city_dir','../data/CityDatabase')
        self.pred_save_path = params.get('pred_save_path','../data/test_city')

        # Load dataset indices
        (self.img_indices, self.lbl_indices) = self.load_indicies()

        # Create mapping of (lable_name, id, color)
        self.labels = [
            Label_City(  'road'          ,   7,  0, (128, 64,128) ),
            Label_City(  'sidewalk'      ,   8,  1, (244, 35,232) ),
            Label_City(  'building'      ,   11,  2, ( 70, 70, 70) ),
            Label_City(  'wall'          ,   12,  3, (102,102,156) ),
            Label_City(  'fence'         ,   13,  4, (190,153,153) ),
            Label_City(  'pole'          ,   17,  5, (153,153,153) ),
            Label_City(  'traffic light' ,   19,  6, (250,170, 30) ),
            Label_City(  'traffic sign'  ,   20,  7, (220,220,  0) ),
            Label_City(  'vegetation'    ,   21,  8, (107,142, 35) ),
            Label_City(  'terrain'       ,   22,  9, (152,251,152) ),
            Label_City(  'sky'           ,   23, 10, ( 70,130,180) ),
            Label_City(  'person'        ,   24, 11, (220, 20, 60) ),
            Label_City(  'rider'         ,   25, 12, (255,  0,  0) ),
            Label_City(  'car'           ,   26, 13, (  0,  0,142) ),
            Label_City(  'truck'         ,   27, 14, (  0,  0, 70) ),
            Label_City(  'bus'           ,   28, 15, (  0, 60,100) ),
            Label_City(  'train'         ,   31, 16, (  0, 80,100) ),
            Label_City(  'motorcycle'    ,   32, 17, (  0,  0,230) ),
            Label_City(  'bicycle'       ,   33, 18, (119, 11, 32) ),
            Label_City(  'void'          ,   19, 19, (  0,  0,  0) )
        ]
        self.trainId2Color = [label.color for label in self.labels]
        self.trainId2labelId = [label.labelId for label in self.labels]
        # Randomization for training
        self.idx = 0
        self.random = params.get('randomize',True)
        self.seed = params.get('seed',None)

        # Randomization: seed and pick
        if self.random:
            random.seed(self.seed)
            self.idx = random.randint(0, len(self.img_indices)-1) # random init

    def load_indicies(self,):
        print('Load %s dataset'%self.dataset_type)
        files_img = []
        files_lbl = []

        # Load training images
        search_img = os.path.join(self.city_dir,
                                  'leftImg8bit',
                                  self.dataset_type,'*','*_leftImg8bit.png')
        files_img = glob.glob(search_img)
        files_img.sort()

        if self.dataset_type != 'test':
            # Load groudtruth images
            search_lbl = os.path.join(self.city_dir,
                                      'gtFine',
                                      self.dataset_type,
                                      '*','*_gtFine_labelTrainIds.png')
            files_lbl = glob.glob(search_lbl)
            files_lbl.sort()

        print('Training images:%d Ground Truth images:%d'%(len(files_img), len(files_lbl)))
        return (files_img, files_lbl)

    def next_batch(self):
        """
        - Reshape image and label, extend 1st axis for batch dimension
        - If 'predef_inx' is given, load sepecific image,
          Otherwise load randomly selected(if self.random is set), or incrementally
        - Return: (image, label)
        """
        # pick next input
        if self.random:
            self.idx = random.randint(0, len(self.img_indices)-1)
        else:
            self.idx += 1
            if self.idx == len(self.img_indices):
                self.idx = 0
        img_fname = self.img_indices[self.idx]
        print('Batch index: %d'%self.idx)
        image = self.load_image(img_fname)
        image = image.reshape(1, *image.shape)

        if self.dataset_type == 'test':
            return (image, None)
        else:
            lbl_fname = self.lbl_indices[self.idx]
            label = self.load_label(lbl_fname)
            label = label.reshape(1, *label.shape)

        return (image,label)

    def load_image(self, fname):
        """
        Load input image and preprocess for using pretrained weight from Caffee:
        - cast to float
        - switch channels RGB -> BGR
        - subtract mean
        - transpose to channel x height x width order
        """
        #print('Loading img:%s'%fname)
        try:
            img = Image.open(fname)
        except IOError as e:
            print('Warning: no image with name %s!!'%fname)

        image = np.array(img, dtype=np.float32)
        image = image[:,:,::-1]     # RGB -> BGR
        #image -= self.mean
        #image = image.transpose((2,0,1))
        return image

    def load_label(self, fname):
        """
        Load label image as 1 x height x width integer array of label indices.
        The leading singleton dimension is required by the loss.
        """
        #print('Loading lbl:%s'%fname)
        try:
            img = Image.open(fname)
        except IOError as e:
            print('Warning: no image with name %s!!'%fname)
            label = None
            return label

        label = np.array(img, dtype=np.uint8)
        label = label[np.newaxis, ...]

        return label

    def pred_to_color(self, fname_prefix, pred_in):
        '''
        Input:  data_instance, should be an instance of CityDataSet.
                pred: predicted matrix, must be [1, Height, Width]
        Return: colored .png image
        '''
        # Pad with RGB channels, producing [1, Height, Width, 4]
        pred_in = pred_in[..., np.newaxis]
        pred = np.lib.pad(pred_in, ((0,0),(0,0),(0,0),(0,3)), self.padding_func)
        # Slice RGB channels
        pred = pred[:,:,:,1:4]
        H = pred.shape[1]
        W = pred.shape[2]
        pred = np.reshape(pred, (H,W,3) )

        # write to .png file
        img_inx = self.img_indices[self.idx].split('_')
        fname = fname_prefix+img_inx[1]+img_inx[2]+'.png'
        save_path = os.path.join(self.pred_save_path,fname)
        imsave(save_path, pred)
        print('Colored prediction saved to %s '%save_path)

        return pred


    def padding_func(self, vector, iaxis_pad_width, iaxis, kwargs):
        '''
        Used by
        '''
        if iaxis == 3:
            idx = vector[0]
            values = self.trainId2Color[idx]
            vector[-iaxis_pad_width[1]:] = values
        return vector

    def convert_to_labelID(self, result_path, save_path):
        '''
        For evaluation purpose:
        convert prediction (trainID labeled png) to
        evaluation format (labelID png).
        '''
        search_path = os.path.join(result_path, '*')
        files_img = glob.glob(search_path)
        files_img.sort()

        for idx in range(len(files_img)):
            img = Image.open(files_img[idx])
            H = img.shape[0]
            W = img.shape[1]
            print("test_height: ", H)
            print("test_width: ", W)
            image = np.array(img, type=np.uint8)
            image = np.reshape(image, (H*W))

            print("transforming format of image %s ..."%files_img[idx])
            for i in range(H*W):
                image[i] = self.trainId2labelId[image[i]]
            print("transform done!")

            # Restore to original image size
            image = np.reshape(image, (H, W))
            output_img = files_img[idx].replace(result_path, save_path)
            imsave(output_img, image)
            print("save transformed image to %s"%output_img)


# Test example
'''
data_config = {'city_dir':"./data/CityDatabase",
                     'randomize': True,
                     'seed': None,
                     'dataset': 'test'}
dt = CityDataSet(data_config)
(img,lbl)=dt.next_batch()
print(img.shape,' ',lbl==None)
'''









