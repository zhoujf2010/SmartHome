[TOC]
# 智能客服接口文档（v1.0） #
## 功能说明 ##
智能客服问答机器人,对话机器人 
## 接口说明 ##
服务器ip：http://ip:port/{servicename}/rest/webhook: 5005(可在config文件夹下修改)
一共有一个接口：

1 /{servicename}/rest/webhook：post请求，输入id和文本信息，输出id和回复文本。

传入参数：

|参数名称|类型|备注|  
|:----|:----:|:----:|
|sender|string|客户id|
|messsage|string|输入文本|

<br>
返回参数：
```
{'error_code': '0', 'error_msg': '报错内容', 'recipient_id': 'id', 'text': '回复文本'}
```

|参数名称 | 类型 |  备注|
|:---|:---:|:---:|  
|error_code | string | 0为接口请求成功，1为失败|
|error_msg | string |error_code为1返回报错内容，为0的时候该字段为空|
|recipient_id | string |回复对象的id（等于sender）|
|text | string |回复文本，报错为空|
|status | string |回复类型判断，0为回复异常，1为回复正常|

2 语义分析接口，识别输入内容的意图和实体

/{servicename}/nlu

POST请求  

传入参数：

|参数名称|类型|备注|  
|:----|:----:|:----:|
|sender|string|客户id|
|messsage|string|输入文本|
<br>
返回参数：
```
    {
        "text": "Hello, how are you today",
        "intent": {
            "name": "greet",
            "confidence": 1.0
        },
        "entities": [
        {
            "start": 0,
            "end": 4,
            "value": "Hello",
            "entity": "cuisine"
         }]
    }
```

#### 代码示例
Java接口示例：
```java

```
Python接口示例：
```python
r = requests.post(url=url, data=json.dumps({'sender': id，'messsage':text})).text
```
JavaScript接口示例：
```javascript
 $.ajax({
      url: url,
      data: JSON.stringify({
        sender: id,
        messsage: text
      }),
      type: 'post',
      contentType: 'application/json',
      dataType: 'json',
      success: function (response) {
        response.result
      }
    });
```



## 安装部署
<br>
两种安装方式，一是独立安装部署，二是作为智能平台插件部署。

### 独立安装部署步骤
1. 获取安装包，邮件联系研究中心
2. 安装python运行环境，参考知识库：[《python安装》](https://fdoc.epoint.com.cn/onlinedoc/rest/d/qiEFFb)  
3. 下载Epointml包，[下载地址](http://192.168.186.13/epointml/)
4. 安装epointml，执行命令：pip install epointml-0.2.1-py3-none-win_amd64.whl
4. 解压安装包
5. 记事本打开config\config.properties可修改参数[端口、服务名]
6. 命令行进入解压目录
7. 执行python server.py
8. 看到以下界面表示成功  

![](https://fdoc.epoint.com.cn/onlinedoc/rest/frame/base/attach/attachAction/getContent?isCommondto=true&attachGuid=57e34437-2942-48c8-9249-974c62fee684)

### AI平台中参数配置
1. 进入AI平台
2. 进入菜单人工智能->后台管理->程序包管理,上传zip包
3. 进入菜单人工智能->智能建模->模型管理，新建普通建模
4. 配置Init、train(可选download)和deploy三个步骤，在deploy中可配置参数。
5. 勾选新建的模型，点击立即执行。
6. 在模型执行记录中可以观察是否成功
7. 在API管理中可看到模型发布的接口地址，点击详细即可验证。
8. 取得地址后可以应用中使用。

![](https://fdoc.epoint.com.cn/onlinedoc/rest/frame/base/attach/attachAction/getContent?isCommondto=true&attachGuid=40cbb39c-2acf-4d8a-a002-919f4bbd6838)
<br>
## 修改参数 ##
<br>
接口可修改的参数有：
### init 参数 ###
init.whlsource:pip安装源

### train 参数 ###
train.jdbcurl：标注数据库
train.model_url：词向量模型地址
train.nlu_threads：训练线程

### movedata 参数 ###
movedata.kefudburl：客服系统数据库地址
movedata.jdbcurl：标注数据库地址
movedata.IncValue：上次抽取增量时间戳（为空时全部记录）

### download 参数 ###
download.model_url:模型下载地址

### deploy 参数 ###
deploy.port：服务端口
deploy.serviceName：服务名
deploy.url：全文检索地址

## 性能指标 ##
<br>
cpu服务器10并发，响应时间2.176s：
![](https://fdoc.epoint.com.cn/onlinedoc/rest/frame/base/attach/attachAction/getContent?isCommondto=true&attachGuid=8bb8694b-7327-4903-8956-d031faa38eff)

Gpu服务器10并发，响应时间0.941s：
![](https://fdoc.epoint.com.cn/onlinedoc/rest/frame/base/attach/attachAction/getContent?isCommondto=true&attachGuid=dcbccf91-cc41-4132-997c-4107530db2e1)
