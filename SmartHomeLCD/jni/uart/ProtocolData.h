/*
 * ProtocolData.h
 *
 *  Created on: Sep 7, 2017
 *      Author: guoxs
 */

#ifndef _UART_PROTOCOL_DATA_H_
#define _UART_PROTOCOL_DATA_H_

#include <string>
#include "CommDef.h"

/******************** CmdID ***********************/
#define CMDID_DATA							0x0
#define CMDID_INFO            0x1    // 新增ID
/**************************************************/

/******************** 错误码 Error code ***********************/
#define ERROR_CODE_CMDID			1
/**************************************************/

typedef struct {
    char *info;
    char receive[255];
    BYTE reclen;
} SProtocolData;

#endif /* _UART_PROTOCOL_DATA_H_ */
