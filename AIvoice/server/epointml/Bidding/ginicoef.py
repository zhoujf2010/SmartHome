# -*- coding: utf-8 -*-


def GRLC(values):
    '''
    Calculate Gini index, Gini coefficient, Robin Hood index, and points of
    Lorenz curve based on the instructions given in
    www.peterrosenmai.com/lorenz-curve-graphing-tool-and-gini-coefficient-calculator
    Lorenz curve values as given as lists of x & y points [[x1, x2], [y1, y2]]
    @param values: List of values
    @return: [Gini index, Gini coefficient, Robin Hood index, [Lorenz curve]]
    '''
    n = len(values)
    assert (n > 0), 'Empty list of values'
    sortedValues = sorted(values)  # Sort smallest to largest

    # Find cumulative totals
    cumm = [0]
    for i in range(n):
        cumm.append(sum(sortedValues[0:(i + 1)]))

    # Calculate Lorenz points
    LorenzPoints = []
    sumYs = 0  # Some of all y values
    # robinHoodIdx = -1  # Robin Hood index max(x_i, y_i)
    for i in range(1, n + 2):
        x = 100.0 * (i - 1) / n
        y = 100.0 * (cumm[i - 1] / float(cumm[n]))
        # LorenzPoints[0].append(x)
        # LorenzPoints[1].append(y)
        LorenzPoints.append({'xvalue': x, 'yvalue': y})
        sumYs += y
        # maxX_Y = x - y
        # if maxX_Y > robinHoodIdx: robinHoodIdx = maxX_Y

    giniIdx = 100 + (100 - 2 * sumYs) / n  # Gini index

    return [{'data': LorenzPoints, 'gini': giniIdx/100}]


def analyze_gini_json(data_json):
    '''
    Analyze json data for Gini index and points of Lorenz curve calculation.
    Json data is a sorted list that includes group number and money amount.
    :param data_json: [{'groupnum':1, 'jine':0.01}. {'groupnum':1}, 'jine':3]
    :return: a list of values(actually sorted because json data is sorted ascending)
    '''
    k = len(data_json)
    idx = data_json[0]['groupnum']
    box = data_json[0]['jine']
    rtn = []
    for i in range(k):
        if idx != data_json[i]['groupnum']:
            rtn.append(box)
            idx = data_json[i]['groupnum']
            box = data_json[i]['jine']
        else:
            box += data_json[i]['jine']
    rtn.append(box)
    return rtn
