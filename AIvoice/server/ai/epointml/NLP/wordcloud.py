#-*- coding:utf-8 -*-

import jieba.analyse
import operator

##############################################################
# SqlServer connection
# host: 192.168.200.128\SQL2008r2_kf8b
# account: sa
# password: epoint_kf8b
#
# check configuration detail in config.xml

def parse_wc_data(wc_data): # parse word cloud api data
    start_date = "\'" + str(wc_data['startDate']) + "\'"
    end_date = "\'" + str(wc_data['endDate']) +"\'"
    maxReturnNum = wc_data['maxReturnNum']
    return start_date, end_date, maxReturnNum


def get_text(nodelist): # helper function in parse config xml
    rc = ""
    for node in nodelist:
        if node.nodeType == node.TEXT_NODE:
            rc = rc + node.data
    return rc


def parse_config_xml(fname):
    from xml.dom.minidom import parse
    server = ""
    username = ""
    password = ""
    driver = ""
    dbname = ""
    domf = parse(fname)

    ServerConfig_element = domf.getElementsByTagName("ServerConfig")[0]
    dbconfig_element = ServerConfig_element.getElementsByTagName("dbConfig")[0]

    server_elememt = dbconfig_element.getElementsByTagName("server")
    username_elememt = dbconfig_element.getElementsByTagName("username")
    password_element = dbconfig_element.getElementsByTagName("password")
    driver_element = dbconfig_element.getElementsByTagName("driver")
    dbname_element = dbconfig_element.getElementsByTagName("dbname")

    for item in server_elememt: server += get_text(item.childNodes)
    for item in username_elememt: username += get_text(item.childNodes)
    for item in password_element: password += get_text(item.childNodes)
    for item in driver_element: driver += get_text(item.childNodes)
    for item in dbname_element: dbname += get_text(item.childNodes)
    return str(server), str(username), str(password), str(driver), str(dbname)

"""
def wc_main(start_date, end_date, maxRtnNum):
    server, username, password, driver, dbname = parse_config_xml('config/config.xml')
    SQL = "SELECT top 10 [RequestTitle], [Description], [RequestDate] FROM [{0}].[dbo].[CaseInfo] WHERE RequestDate >= {1} AND RequestDate <= {2}".format(dbname,start_date,end_date)
    # SQL = "SELECT TOP 10 [RequestTitle], [Description], [RequestDate] FROM [12345_ZJG].[dbo].[CaseInfo] WHERE RequestDate > '2017-01-01 00:00:00' "
    connection_string ='Driver={SQL Server};Server=' + server + ';Database=' + dbname + ';UID=' + username + ';PWD=' + password + ';'
    db = pypyodbc.connect(connection_string)
    cursor = db.cursor()
    cursor.execute(SQL)
    content = cursor.fetchall()
    cursor.close()
    db.close()

    wordwrap = ""
    for item in content:
        wordwrap += (item[0] + ',' + item[1] + ',')
    tags = jieba.analyse.extract_tags(wordwrap, withWeight=True,topK=maxRtnNum)
    return tags
"""

# create another api interface that only requires text data.
def wc_text(content, maxRtnNum):
    tags = jieba.analyse.extract_tags(content, withWeight=True, topK=maxRtnNum)
    return tags


def calculate_word_freq(data, rtn_num):
    jieba.set_dictionary('lib/dict.txt')
    content = data
    punct = set(u'''1234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ''')
    filterpunt = lambda s: ''.join(filter(lambda x: x not in punct, s))
    seglist = jieba.cut(filterpunt(content.replace('\r\n','a')),cut_all=False)

    stoplist = []
    with open("lib/stop",'r') as f:
        lines = f.readlines()
        for word in lines:
            stoplist.append((word.strip()))
    stopset = set(stoplist)

    worddict = {}
    for word in seglist:
        # print word
        if (word not in stopset) and (len(word) > 1):
            if word in worddict:
                worddict[word] += 1
            else:
                worddict[word] = 1
    sorted_x = sorted(worddict.keys, key=operator.itemgetter(1), reverse=True)
    return sorted_x[0:rtn_num]

# parse text data
def parse_wf_data(json_data):
    text_data = json_data['textData']
    maxRtnNum = json_data['maxReturnNum']
    return text_data, maxRtnNum


