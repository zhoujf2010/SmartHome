# -*- coding: utf-8 -*-

"""
This is python algorithms for multiple linear regression,
ridge, kernel ridge and Lasso regression;

In v2, I add r^2 score, confidence for judging the fit of
sample data.

Author: Adrian
Date: 2017/02/24
"""

import numpy as np
import scipy.stats.stats as st
from sklearn import linear_model


def anova(x, y):  # x and y should be array like
    # fow = st.f_oneway(x,y)
    # fvalue = fow[0]
    # pvalue = fow[1]
    reg = linear_model.LinearRegression()
    t = x[:, np.newaxis]
    reg.fit(t, y)
    prvalue = st.pearsonr(x, y)
    # print fvalue, pvalue, prvalue
    pearsonr = prvalue[0]  # pearson correlation coefficient
    pvalue = prvalue[1]  # 2-tailed p-value
    rsquare = reg.score(t, y)  # r square value
    coef = reg.coef_
    intercept = reg.intercept_
    if str(prvalue[1]) == 'nan':
        pvalue = 0
    return {"pearson": pearsonr, "pvalue": pvalue, "rsquare": rsquare,
            "coef": list(coef), "intercept": intercept, "num": len(x)}


def parse_anova(json_data):
    xlst = []
    ylst = []
    idlst = json_data["independentVariable"]
    dlst = json_data["dependentVariable"]
    for item in idlst:
        xlst.append(item["value"])
    for item in dlst:
        ylst.append(item["value"])
    return np.array(xlst), np.array(ylst)


def main():
    x = [1853142.57,
    2051757.26,
    3203420.30,
    7980344.19,
    5650279.78,
    5744265.39,
    9938509.68]

    y =[3419100,
    4762000,
    6237700,
    6943600,
    7682700,
    8806800,
    10025000]

    x = np.array(x)
    y = np.array(y)
    anova(x,y)
    print(st.pearsonr(x,y))

    reg = linear_model.LinearRegression()
    t = x[:,np.newaxis]
    reg.fit(t,y)
    print(reg.score(t,y))
    print(reg.coef_, reg.intercept_)


if __name__ == "__main__":
    main()