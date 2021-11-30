/*
 * hass.cpp
 *
 *  Created on: 2021年11月18日
 *      Author: zjf
 */

#include "hass.h"

hass::hass() {
	connected = false;
	pagenum = -1;
	ipaddr = StoragePreferences::getString("ipaddr", "192.168.3.168:8082"); //"192.168.3.168:8082";
	cfgName = StoragePreferences::getString("cfgName", "lovelace-led1"); //"lovelace-led1";
}

hass::~hass() {
}

static std::vector<OnHassDataUpdateFun> sHassDataUpdateListenerList;

void registerHassUpdateListener(OnHassDataUpdateFun pListener) {
//	Mutex::Autolock _l(sLock);
	LOGD("registerHassUpdateListener\n");
	if (pListener != NULL) {
		sHassDataUpdateListenerList.push_back(pListener);
	}
}

void unregisterHassDataUpdateListener(OnHassDataUpdateFun pListener) {
//	Mutex::Autolock _l(sLock);
	LOGD("unregisterProtocolDataUpdateListener\n");
	if (pListener != NULL) {
		std::vector<OnHassDataUpdateFun>::iterator iter = sHassDataUpdateListenerList.begin();
		for (; iter != sHassDataUpdateListenerList.end(); iter++) {
			if ((*iter) == pListener) {
				sHassDataUpdateListenerList.erase(iter);
				return;
			}
		}
	}
}

bool hass::readyToRun() {

}

bool hass::threadLoop() {
	LOGD("start connection ----");
	while (true) {
		conn = net::Dial("tcp", ipaddr);
		connected = true;
		while (true) { //while
			//读取，超时1000毫秒
			int n = conn->Read(buf, sizeof(buf) - 1, 1);			//1000);
			if (n == net::E_TIMEOUT) {
//				if (bufpos >0){
//					LOGD("有数据要处理了-------->：%d,%d", bufpos,allbuf[bufpos -1] );
//				}

				if (bufpos > 0 && allbuf[bufpos - 1] == '}') { //有数据，且尾巴是}
//					LOGD("读到数据-------->：%s", std::string((char*) allbuf, 0, bufpos).substr(0, 1000).c_str());
//					if (bufpos >1000)
//						LOGD("读到数据-------->：%s", std::string((char*) allbuf, 0, bufpos).substr(1000, 2000).c_str());
					//缓存中的值处理掉
					allbuf[bufpos] = 0;
					this->DealMsg(std::string((char*) allbuf, 0, bufpos));
					bufpos = 0;
				}

				continue;
			}

//			LOGD("读到数据-------->：%d,%d", n, sizeof(buf));
			if (n > 0) {
				if (bufpos >= sizeof(allbuf)) {
					bufpos = 0; //长度超出，肯定异常了，重新处理
				}

				std::memcpy(allbuf + bufpos, buf, n);
				bufpos += n;

//				buf[n] = 0;
//				this->DealMsg(std::string((char*) buf, 0, n));

			} else if (n == 0) {
				LOGD("连接正常断开");
				break;
			} else if (n == net::E_TIMEOUT) {
				LOGD("读取超时");
			} else {
				LOGD("出错");
				break;
			}
		}

		//关闭连接
		conn->Close();
		connected = false;
		LOGD("连接断开");
		//为了方便观察，这里添加休眠500ms
		usleep(1000 * 3000);
		LOGD("等待了3秒，准备重连接");
	}
}

void hass::send(const char* req) {
	//发送
	conn->Write((byte*) req, strlen(req));
}

hass* hass::getInstance() {
	static hass sUC;
	return &sUC;
}

void hass::LoadInitData() {
	std::string req = "{\"type\": \"lovelace/config\", \"url_path\": \"" + this->cfgName + "\"}";
	this->send(req.c_str());
	LOGD(" 发送初使化信号");
}

Json::Value hass::getConfig(int index) {
	if (index == -1)
		return pageconfig;
	if (index >= pageconfig.size())
		return pageconfig;
	return pageconfig[index];
}

void hass::switchchg(int pageindex, int btinindex, bool status) {
	//获取entity
	std::string entity = pageconfig[pageindex]["cards"][btinindex]["entity"].asString();
	if (status) {
		std::string req = "{\"type\": \"call_service\", \"domain\": \"switch\", \"service\": \"turn_off\", \"service_data\": {\"entity_id\": \"" + entity + "\"}}";
		this->send(req.c_str());
	} else {
		std::string req = "{\"type\": \"call_service\", \"domain\": \"switch\", \"service\": \"turn_on\", \"service_data\": {\"entity_id\": \"" + entity + "\"}}";
		this->send(req.c_str());
	}
}

void hass::invokeScreen(int type) {
	//通知 屏更新数据
	std::vector<OnHassDataUpdateFun>::const_iterator iter = sHassDataUpdateListenerList.begin();
	for (; iter != sHassDataUpdateListenerList.end(); iter++) {
		(*iter)(type);
	}
}

void hass::DealMsg(std::string str) {
	if (str == "")
		return;

//	if (str[0] !='{' || str[str.length()-1] != "}"){
//		LOGD("数据不完整:%s", str.c_str());
//		LOGD("数据不完整1:%s", str[0]);
//		LOGD("数据不完整2:%s", str[str.length()-1]);
//		return ;
//	}

//	LOGD("income message:====>%s", str.c_str());
	//解析json
	Json::Reader reader;
	Json::Value root;
	if (!reader.parse(str, root, false)) {
		LOGD("unknown message:%s", str.c_str());
		return;
	}

	std::string type = root["type"].asString();
	if (type == "result") {	//结果查询类
		std::string success = root["success"].asString();
		if (success != "true")
			return;
		Json::Value data = root["result"];

		if (data.isMember("views")) { //获取配置信息
			Json::Value views = data["views"];
			pageconfig = views;
			pagenum = views.size(); //读出视图数量
			LOGD("解析成功,屏数：%d", pagenum);

			//时间设定
			TimeHelper::setDateTime(root["date"].asString().c_str());
			LOGD("时间定定为：%s", root["date"].asString().c_str());

			for (Json::ArrayIndex i = 0; i < views.size(); ++i) {
				Json::Value cards = views[i]["cards"];
				for (Json::ArrayIndex j = 0; j < cards.size(); ++j) {
					cards[j]["state"] = "unknown";
				}
				views[i]["cards"] = cards;
			}
			this->invokeScreen(0);
			//获取状态
//				std::string req2 = "{\"type\": \"get_states\"}";
//				this->send(req2.c_str());
		}
	} else if (type == "event") { //事件处理
		Json::Value event = root["event"];
		std::string event_type = event["event_type"].asString();
		if (event_type == "state_changed") {
			std::string entityid = event["data"]["entity_id"].asString();
			std::string newstate = event["data"]["new_state"]["state"].asString();

			LOGD("data==>%s,%s", entityid.c_str(), newstate.c_str());
			//遍历记录
			for (Json::ArrayIndex i = 0; i < pageconfig.size(); ++i) {
				Json::Value cards = pageconfig[i]["cards"];
				for (Json::ArrayIndex j = 0; j < cards.size(); ++j) {
					if (cards[j]["entity"].asString() == entityid) {
						cards[j]["state"] = newstate;
					}
				}
				pageconfig[i]["cards"] = cards;
			}
//			LOGD("生成的json字符串为: %s", pageconfig.toStyledString().c_str());
			this->invokeScreen(1);
//			if (entityid =="weather.wo_de_jia")
//				LOGD("----DEBUG----55--");
		}
	} else
		LOGD("unknown type:%s", type.c_str());
}

void hass::saveCfg() {
	StoragePreferences::putString("ipaddr", ipaddr);
	StoragePreferences::putString("cfgName", cfgName);
}

static std::string* lst = new std::string[15] { "clear-night", "cloudy", "exceptional", "fog", "hail", "lightning", "lightning-rainy", "partlycloudy", "pouring", "rainy", "snowy", "snowy-rainy",
		"sunny", "windy", "windy-variant" };

static std::string* chslst = new std::string[15] { "晴", "多云", "异常", "雾", "冰雹", "闪电", "闪电雨", "局部多云", "暴雨", "雨", "雪", "雨夹雪", "睛", "风", "大风" };

int findIndex(std::string weath) {
	int find = 0;
	for (int i = 0; i < 15; i++) {
		if (lst[i] == weath) {
			find = i;
			break;
		}
	}
	return find;
}

//取得天气对应图标
std::string hass::getWeatherData(std::string weath) {
	int find = findIndex(weath);
	char t[1];
	t[0] = 'a' + find;
	return std::string(t, 1);
}

//取得天气中文名
std::string hass::getWeatherChsData(std::string weath) {
	int find = findIndex(weath);
	return chslst[find];
}

//格式化温度
std::string hass::getTemp(std::string temp) {
	double f = atof(temp.c_str());

	char tmpstr[6];
	sprintf(tmpstr, "%.0f", f);
	return std::string(tmpstr);
}

//取得当天天气
std::string hass::getTodayTemp() {
	Json::Value weathercards;
	for (Json::ArrayIndex j = 0; j < pageconfig.size(); ++j) {
		Json::Value cards = pageconfig[j]["cards"];
		//获取标题及状态值
		for (Json::ArrayIndex i = 0; i < cards.size(); ++i) {
			if (cards[i]["type"].asString() == "weather-forecast") {
				weathercards = cards[i]["state"];
			}
		}
	}
	std::string weathname = weathercards["state"].asString();
	std::string ret = HASS->getWeatherData(weathname);
	ret += "," + weathercards["temperature"].asString();
	ret += "," + HASS->getWeatherChsData(weathname);
	return ret;
}
