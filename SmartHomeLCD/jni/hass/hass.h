/*
 * hass.h
 *
 *  Created on: 2021年11月18日
 *      Author: zjf
 */

#ifndef JNI_HASS_HASS_H_
#define JNI_HASS_HASS_H_
#include <system/Thread.h>
#include "net/net.h"
#include <sys/socket.h>
#include <arpa/inet.h>
#include <netdb.h>
#include <unistd.h>
#include <fcntl.h>
#include <poll.h>
#include <sys/select.h>
#include <errno.h>
#include <time.h>
#include <signal.h>
#include <vector>
#include <string.h>
#include <system/Thread.h>
#include "json/json.h"
#include <cstring>

#include "restclient-cpp/restclient.h"
#include "storage/StoragePreferences.h"
#include "utils/TimeHelper.h"



typedef void (*OnHassDataUpdateFun)(int type);
void registerHassUpdateListener(OnHassDataUpdateFun pListener);
void unregisterHassDataUpdateListener(OnHassDataUpdateFun pListener);


class hass: public Thread {
public:
	hass();
	virtual ~hass();

	void send(const char* req);

	static hass* getInstance();

//	int getPageNum();

	void LoadInitData();
	Json::Value getConfig(int index);


	void switchchg(int pageindex,int btinindex,bool status);

	std::string ipaddr;
	std::string cfgName;
	void saveCfg();
	std::string getWeatherData(std::string weath);
	std::string getWeatherChsData(std::string weath);

	std::string getTemp(std::string temp);
	std::string getTodayTemp();

protected:
	virtual bool readyToRun();
	virtual bool threadLoop();

	net::Conn* conn;

	bool connected;
	int pagenum;
	byte buf[1024]; //10240
	byte allbuf[10240];
	int bufpos = 0;

	Json::Value pageconfig;

	void DealMsg(std::string str);

	void invokeScreen(int type);
};


#define HASS		hass::getInstance()

#endif /* JNI_HASS_HASS_H_ */
