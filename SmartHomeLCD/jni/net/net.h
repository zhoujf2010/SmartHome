#ifndef JNI_EXTRA_NET_NET_H_
#define JNI_EXTRA_NET_NET_H_

#include <netinet/in.h>
#include <string>
#include "utils/Log.h"

typedef unsigned char byte;

namespace net {
enum Error {
  E_TIMEOUT = -10000,
};

class Addr {
public:
  struct sockaddr addr;
};

class Conn {
public:
  virtual int Write(byte* bytes, int bytes_len) = 0;
  /**
   * timeout: 超时时间  毫秒
   * return >0  读到数据
   *        =0  已关闭
   *        -10000 读取超时
   *        其他   出错
   */
  virtual int Read(byte* buffer, int buffer_len, int timeout_millisecond) = 0;
  virtual void Close() = 0;
  virtual Addr LocalAddr() = 0;
  virtual Addr RemoteAddr() = 0;
  virtual ~Conn(){};
};

Conn* Dial(std::string network, std::string address);

} /* namespace net */

#endif /* JNI_EXTRA_NET_NET_H_ */
