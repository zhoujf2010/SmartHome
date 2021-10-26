# -*- coding: utf-8 -*-
"""
This is python algorithm for multiple linear regression;
ridge, and Lasso;

本文件包括线性回归，ridge回归， Lasso回归, 多项式回归算法

Author: Adrian
Date: 2016/11/25

"""

from sklearn import linear_model
import scipy
import numpy as np
from sklearn.linear_model import Ridge
from sklearn.preprocessing import PolynomialFeatures
from sklearn.pipeline import make_pipeline
from sklearn.kernel_ridge import KernelRidge


# linear regression
def linear_regression(y_axis, p_num=2):
    y_axis = np.array(y_axis)
    x_axis = np.array(range(len(y_axis)))
    t_axis = x_axis[:, np.newaxis]

    reg = linear_model.LinearRegression()
    reg.fit(t_axis, y_axis)

    p_x = np.array(range(len(y_axis), len(y_axis)+p_num))
    predict_x = p_x[:, np.newaxis]
    result = reg.predict(predict_x)
    return result.tolist(), reg.score(t_axis,y_axis)


# ridge
def ridge_regression(y_axis, p_num=2, alpha=1.0):
    y_axis = np.array(y_axis)
    x_axis = np.array(range(len(y_axis)))
    t_axis = x_axis[:, np.newaxis]

    reg = Ridge(alpha=alpha)
    reg.fit(t_axis, y_axis)

    p_x = np.array(range(len(y_axis),len(y_axis)+p_num))
    predict_x = p_x[:, np.newaxis]
    result = reg.predict(predict_x)
    return result.tolist(), reg.score(t_axis,y_axis)


# Lasso
def lasso_regression(y_axis, p_num=2, alpha=1.0):
    y_axis = np.array(y_axis)
    x_axis = np.array(range(len(y_axis)))
    t_axis = x_axis[:,np.newaxis]

    reg = linear_model.Lasso(alpha=alpha)
    reg.fit(t_axis, y_axis)

    p_x = np.array(range(len(y_axis),len(y_axis)+p_num))
    predict_x = p_x[:,np.newaxis]
    result = reg.predict(predict_x)
    return result.tolist(), reg.score(t_axis,y_axis)


# Polynominal by ridge regression y_axis should be array
def polynominal_regression(y_axis,p_num=2,poly_feature=2,alpha=1):
    # source data scatter
    # plt.scatter(X, y, color='navy', s=30, marker='o', label="training points")
    y_axis = np.array(y_axis)

    model = make_pipeline(PolynomialFeatures(poly_feature), Ridge(alpha=alpha))
    x_axis = np.array(range(len(y_axis)))
    t_x = x_axis[:, np.newaxis]

    try:
        model.fit(t_x, y_axis)
    except Exception as err:
        print(err)
    p_x = np.array(range(len(y_axis), len(y_axis)+p_num))  # 往后预测两个值
    predict_x = p_x[:, np.newaxis]
    y_predict = model.predict(predict_x)
    rst_list = y_predict.tolist()
    return rst_list, model.score(t_x, y_axis)


# kernel ridge regression
def kernel_ridge(y_axis, p_num=2, alpha=1.0):
    y_axis = np.array(y_axis)

    x_axis = np.array(range(len(y_axis)))
    t_x = x_axis[:, np.newaxis]

    clf = KernelRidge(alpha=alpha)
    try:
        clf.fit(t_x, y_axis)
    except Exception as err:
        print(err)
    p_x = np.array(range(len(y_axis), len(y_axis)+p_num))  # predict p_Num values
    predict_x = p_x[:, np.newaxis]
    result = clf.predict(predict_x)
    return result.tolist(), clf.score(t_x, y_axis)

