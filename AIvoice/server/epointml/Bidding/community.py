# -*- coding: utf-8 -*-

import igraph as ig
import pandas as pd


# vertices should be a list, edges is like tuple in list -> [(1,2),(2,3)]
def get_multi_community(vertices, edges):
    g = ig.Graph()
    g.add_vertices(vertices)
    g.add_edges(edges)
    # return community result and degree
    return g.community_multilevel(), pd.Series(g.degree())


# convert multi_community result to list format.
def community_list(community_rst, degree, min_group_size):
    rtn_lst = []
    group_id = 0
    for item in community_rst:
        if len(item) < min_group_size:
            continue
        else:
            group_id += 1
            for node in item:
                rtn_lst.append({"GroupID": int(group_id), "Node": str(node),
                                "Degree": int(degree[node])})
    return rtn_lst