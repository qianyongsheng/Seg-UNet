# -*- coding: utf-8 -*-
import keras.backend.tensorflow_backend as KTF
import tensorflow as tf
from keras.callbacks import EarlyStopping, TensorBoard, ModelCheckpoint

from generator import data_gen_small

import os
import numpy as np
import argparse
import json
import pandas as pd

from SegUNet import CreateSegUNet


def main(args):
    # set the necessary list
    train_list = pd.read_csv(args.train_list,header=None)
    val_list = pd.read_csv(args.val_list,header=None)

    # set the necessary directories
    trainimg_dir = args.trainimg_dir
    trainmsk_dir = args.trainmsk_dir
    valimg_dir = args.valimg_dir
    valmsk_dir = args.valmsk_dir

    # get old session
    old_session = KTF.get_session()

    with tf.Graph().as_default():
        session = tf.Session('')
        KTF.set_session(session)
        KTF.set_learning_phase(1)

        # class weights
        classes = ['background', 'hat', 'hair', 'glove', 'sunglasses', 'upperclothes',
                'dress', 'coat', 'socks', 'pants', 'jumpsuits', 'scarf', 'skirt',
                'face', 'leftArm', 'rightArm', 'leftLeg', 'rightLeg', 'leftShoe','rightShoe']
        if args.class_weights:
            class_weights = [1, 40, 1, 114, 151, 3, 53, 7, 165, 7, 106, 249, 150, 1, 1, 1, 1, 1, 114, 118]

        # set callbacks
        fpath = './pretrained_class_weights/LIP_SegUNet_class_weights{epoch:02d}.hdf5'
        cp_cb = ModelCheckpoint(filepath = fpath, monitor='val_loss', verbose=1, save_best_only=True, mode='auto', period=2)
        es_cb = EarlyStopping(monitor='val_loss', patience=2, verbose=1, mode='auto')
        tb_cb = TensorBoard(log_dir="./pretrained_class_weights", write_images=True)

        # set generater
        train_gen = data_gen_small(trainimg_dir,
                trainmsk_dir,
                train_list,
                args.batch_size,
                [args.input_shape[0], args.input_shape[1]],
                args.n_labels)
        val_gen = data_gen_small(valimg_dir,
                valmsk_dir,
                val_list,
                args.batch_size,
                [args.input_shape[0], args.input_shape[1]],
                args.n_labels)

        # set model
        segunet = CreateSegUNet(args.input_shape, args.n_labels, args.kernel, args.pool_size, args.output_mode)
        print(segunet.summary())

        # compile model
        segunet.compile(loss=args.loss,
                optimizer=args.optimizer,
                metrics=["accuracy"])

        # fit with genarater
        segunet.fit_generator(generator=train_gen,
                steps_per_epoch=args.epoch_steps,
                epochs=args.n_epochs,
                validation_data=val_gen,
                validation_steps=args.val_steps,
                class_weight=class_weights,
                callbacks=[cp_cb, es_cb, tb_cb])

    # save model
    with open("./pretrained/LIP_SegUNet.json", "w") as json_file:
        json_file.write(json.dumps(json.loads(segunet.to_json()), indent=2))
    print("save json model done...")


if __name__ == "__main__":
    # command line argments
    parser = argparse.ArgumentParser(description="SegUNet LIP dataset")
    parser.add_argument("--train_list",
            help="train list path")
    parser.add_argument("--trainimg_dir",
            help="train image dir path")
    parser.add_argument("--trainmsk_dir",
            help="train mask dir path")
    parser.add_argument("--val_list",
            help="val list path")
    parser.add_argument("--valimg_dir",
            help="val image dir path")
    parser.add_argument("--valmsk_dir",
            help="val mask dir path")
    parser.add_argument("--batch_size",
            default=5,
            type=int,
            help="batch size")
    parser.add_argument("--n_epochs",
            default=10,
            type=int,
            help="number of epoch")
    parser.add_argument("--epoch_steps",
            default=6000,
            type=int,
            help="number of epoch step")
    parser.add_argument("--val_steps",
            default=1000,
            type=int,
            help="number of valdation step")
    parser.add_argument("--n_labels",
            default=20,
            type=int,
            help="Number of label")
    parser.add_argument("--input_shape",
            default=(512, 512, 3),
            help="Input images shape")
    parser.add_argument("--kernel",
            default=3,
            type=int,
            help="Kernel size")
    parser.add_argument("--pool_size",
            default=(2, 2),
            help="pooling and unpooling size")
    parser.add_argument("--output_mode",
            default="softmax",
            type=str,
            help="output activation")
    parser.add_argument("--loss",
            default="categorical_crossentropy",
            type=str,
            help="loss function")
    parser.add_argument("--optimizer",
            default="adadelta",
            type=str,
            help="oprimizer")
    parser.add_argument("--class_weights",
            default=True,
            help="dataset class weights")
    parser.add_argument("--gpu_num",
            default="1",
            type=str,
            help="num of gpu")
    args = parser.parse_args()

    # device number
    if args.gpu_num:
        os.environ["CUDA_VISIBLE_DEVICES"] = args.gpu_num

    main(args)
