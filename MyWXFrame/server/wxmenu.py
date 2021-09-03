
from weixinMgr.wxManage import wxManage

if __name__ == '__main__':
    rooturl = "http://test.tobloan.com/MyWx"

    wxman = wxManage()

    menuStr = {
        "button": [
            {
                "type": "view",
                "name": "我的家",
                "url": rooturl,
            },
            {
                "type": "view",
                "name": "我的家2",
                "url": wxman.genLogUrl(rooturl+"")
            },
            {
                "name": "博客园",
                "sub_button": [
                    {
                        "type": "view",
                        "name": "测试",
                        "url": rooturl+""
                    },
                    {
                        "type": "view",
                        "name": "测试2",
                        "url": wxman.genLogUrl(rooturl+"")
                    },
                    {
                        "type": "click",
                        "name": "博客园主页",
                        "key": "V002_YHHD"
                    }
                ]
            }
        ]
    }

    print(wxman.createMenu(menuStr))
