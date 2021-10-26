# -*- coding: utf-8 -*-
"""
数据增强基础方法

@author: Adrian
Date: Sept 17, 2020
"""
import copy
import cv2
from skimage.util import random_noise
import numpy as np


class augutil:
    def __init__(self):
        pass

    def swap_transpose_elements(self, tag):
        """
        标注数据转置操作

        Parameters
        ----------
        tag: list
            标注数据 [x1, y1, x2, y2, label_id]

        Returns
        -------
        transpose_tag: list
            转置后的标注数据 [x1, y1, x2, y2, label]
        """
        if len(tag) != 5:
            raise Exception("标注数据长度不等于5，格式错误.")
        x1 = tag[0]
        y1 = tag[1]
        x2 = tag[2]
        y2 = tag[3]
        label = tag[4]
        return [y1, x1, y2, x2, label]

    def flip_elements(self, tag, direction, width, height):
        """
        标注数据翻折处理, vertically, horizontally, both axes

        Parameters
        ----------
        tag: list
            标注数据 [x1, y1, x2, y2, label_id]
        direction: int
            0: vertically, 1: horizontally, -1: both axes
        width: int
            图片宽度
        height: int
            图片高度

        Returns
        -------
        flip_tags: list
            转置后的标注数据 [x1, y1, x2, y2, label]

        """
        x1 = int(tag[0])
        y1 = int(tag[1])
        x2 = int(tag[2])
        y2 = int(tag[3])
        label = tag[4]
        if direction == 0:
            return [str(x1), str(height-y1), str(x2), str(height-y2), label]
        if direction == 1:
            return [str(width-x1), str(y1), str(width-x2), str(y2), label]
        if direction == -1:
            return [str(width-x1), str(height-y1), str(width-x2), str(height-y2), label]
        else:
            raise Exception("wrong type value! flip_elements type参数类型不在范围之内!")

    def transpose(self, img, tags):
        """
        对图片进行转置transpose处理

        Parameters
        ----------
        src_img: np.array
            cv2.imread() object, cv2图片对象
        tags: str
            标注数据，yolo格式 "x1,y1,x2,y2,label_id x1,y1,x2,y2,label_id"

        Returns
        -------
        transpose_img: list of tuple
            [transpose_img, transpose_tags]
            transpose_img: np.array, cv2 object, 转置处理后的cv2图片对象
            transpose_tags: str, 转置处理后的标注数据
        """
        src_img = copy.deepcopy(img)
        tagslist = tags.split()
        transpose_img = cv2.transpose(src_img)
        transpose_tags = []
        for t in tagslist:
            tl = t.split(",")
            transpose_tags.append(",".join(self.swap_transpose_elements(tl)))
        return [transpose_img, " ".join(transpose_tags)]

    def flip(self, img, tags):
        """
        对图片进行翻折处理, 默认处理三种操作 - vertically, horizontally, both axes

        Parameters
        ----------
        src_img: np.array
            cv2.imread() object, cv2图片对象
        tags: str
            标注数据，yolo格式 "x1,y1,x2,y2,label_id x1,y1,x2,y2,label_id"

        Returns
        -------
        flip_imgs: list of tuple
            [(flip_img, flip_tags), ...]
        """
        src_img = copy.deepcopy(img)
        tagslist = tags.split()
        shape = src_img.shape[0:2]
        height = shape[0]
        width = shape[1]
        transpose_tags_0 = []
        transpose_tags_1 = []
        transpose_tags_n1 = []

        # vertically 垂直翻折
        flip_img_0 = cv2.flip(src_img, 0)

        # horizontally 水平翻折
        flip_img_1 = cv2.flip(src_img, 1)

        # both axes
        flip_img_n1 = cv2.flip(src_img, -1)

        for t in tagslist:
            tl = t.split(",")
            transpose_tags_0.append(",".join(self.flip_elements(tag=tl, direction=0, width=width, height=height)))
            transpose_tags_1.append(",".join(self.flip_elements(tag=tl, direction=1, width=width, height=height)))
            transpose_tags_n1.append(",".join(self.flip_elements(tag=tl, direction=-1, width=width, height=height)))

        return [(flip_img_0, " ".join(transpose_tags_0)), (flip_img_1, " ".join(transpose_tags_1)),
                (flip_img_n1, " ".join(transpose_tags_n1))]

    def multi_noise(self, img):
        """
        gaussian noise, salt and pepper noise, speckle noise,
        no tags variable because all these data augumentation methods do not change the size of original image.

        Parameters
        ----------
        img: np.array
            cv2.imread() object, cv2图片对象

        Returns
        -------
        img_list: list
            [img1, img2, img3]
        """
        s1 = copy.deepcopy(img)
        s2 = copy.deepcopy(img)
        s3 = copy.deepcopy(img)
        gaus_img = random_noise(s1, mode="gaussian")
        gaus_img = (gaus_img*255).astype(np.uint8)
        salt_img = random_noise(s2, mode="s&p")
        salt_img = (salt_img*255).astype(np.uint8)
        speckle_img = random_noise(s3, mode="speckle")
        speckle_img = (speckle_img*255).astype(np.uint8)
        # cv2.imshow("salt", salt_img)
        # cv2.imwrite("gen/gaus.jpg", gaus_img)
        # cv2.imwrite("gen/salt.jpg", salt_img)
        # cv2.imwrite("gen/speckle.jpg", speckle_img)
        return [gaus_img, salt_img, speckle_img]

    def mosaic(self, img):
        """
        mosaic and mixup methods are included in yolov4 codes, so don't do it again if your work is realtime object
        detection.
        """
        raise NotImplementedError("mosaic method is not implemented.")

    def scale_crop(self):
        """
        scale image and crop

        """
        raise NotImplementedError("scale crop is not implemented.")

    def gan(self):
        """
        neural style transfer

        """
        raise NotImplementedError("gan is not implemented.")


if __name__ == "__main__":
    fp = "gen/v3/train_img/0.jpg"
    srcimg = cv2.imread(fp)

    dataaug = augutil()

    # transpose
    # tags = "12,32,12,32,0 12,23,12,12,1"
    # trsimg, trstags = dataaug.transpose(srcimg, tags)
    # print("transpose tags: ", trstags)
    # cv2.imshow("transpose", trsimg)

    # flip
    # dataaug.flip(srcimg, tags)

    # gaussian, salt, pepper, speckle noise
    imglst = dataaug.multi_noise(srcimg)
    cv2.waitKey(0)
