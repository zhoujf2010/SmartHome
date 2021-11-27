#include "net.h"
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

namespace net {

static int NonBlockConnect(int fd, const struct sockaddr* ai_addr,
    socklen_t ai_addrlen, int out_time_seconds) {

  /*设置套接字为非阻塞*/
  int flags = fcntl(fd, F_GETFL, 0);
  if (flags < 0) {
      LOGD("Get flags error:%s\n", strerror(errno));
      return -1;
  }
  flags |= O_NONBLOCK;
  if (fcntl(fd, F_SETFL, flags) < 0) {
      LOGD("Set flags error:%s\n", strerror(errno));
      return -1;
  }

  fd_set fdr, fdw;
  struct timeval timeout;
  int err = 0;
  int errlen = sizeof(err);
  /*阻塞情况下linux系统默认超时时间为75s*/
  int rc = ::connect(fd, ai_addr, ai_addrlen);
  if (rc != 0) {
      if (errno == EINPROGRESS) {
          LOGD("Doing connection.\n");
          /*正在处理连接*/
          FD_ZERO(&fdr);
          FD_ZERO(&fdw);
          FD_SET(fd, &fdr);
          FD_SET(fd, &fdw);
          timeout.tv_sec = out_time_seconds;
          timeout.tv_usec = 0;
          rc = select(fd + 1, &fdr, &fdw, NULL, &timeout);
          LOGD("rc is: %d\n", rc);
          /*select调用失败*/
          if (rc < 0) {
              LOGD("connect error:%s\n", strerror(errno));
              return -1;
          }

          /*连接超时*/
          if (rc == 0) {
              LOGD("Connect timeout.\n");
              return -1;
          }
          /*[1] 当连接成功建立时，描述符变成可写,rc=1*/
          if (rc == 1 && FD_ISSET(fd, &fdw)) {
              LOGD("Connect success\n");
              return 0;
          }
          /*[2] 当连接建立遇到错误时，描述符变为即可读，也可写，rc=2 遇到这种情况，可调用getsockopt函数*/
          if (rc == 2) {
              if (getsockopt(fd, SOL_SOCKET, SO_ERROR, &err, (socklen_t*)&errlen) == -1) {
                  LOGD("getsockopt(SO_ERROR): %s", strerror(errno));
                  return -1;
              }

              if (err) {
                  errno = err;
                  LOGD("connect error:%s\n", strerror(errno));
                  return -1;
              }
          }
      }
      LOGD("connect failed, error:%s.\n", strerror(errno));
      return -1;
  }
  return rc;
}

static int Send(int sock_fd, const byte* buffer, size_t buflen) {
  if (buflen <= 0) {
    return 0;
  }
  if (buffer == NULL) {
    return 0;
  }
  size_t tmp;
  size_t total = buflen;
  const unsigned char *p = buffer;

  while (true) {
      tmp = send(sock_fd, p, total, 0);
      if (tmp < 0) {
          // 当send收到信号时,可以继续写,但这里返回-1.
          if (errno == EINTR) {
            usleep(1000 * 100);
            continue;
          }
          // 当socket是非阻塞时,如返回此错误,表示写缓冲队列已满,
          // 在这里做延时后再重试.
          if (errno == EAGAIN) {
              usleep(1000 * 100);
              continue;
          }
          return -1;
      }

      if ((size_t) tmp == total) {
//        LOGD("send success");
        return buflen;
      }

      total -= tmp;
      p += tmp;
  }
  return tmp;
}

class TcpClientConn: public Conn {
public:
  bool Connect(std::string host, std::string port) {
    int status;
    int socketfd = -1;
    struct addrinfo host_info; // The struct that getaddrinfo() fills up with data.
    struct addrinfo * host_info_list = NULL;

    memset(&host_info, 0, sizeof host_info);

    host_info.ai_family = AF_UNSPEC;   // IP version not specified. Can be both.
    host_info.ai_socktype = SOCK_STREAM; // Use SOCK_STREAM for TCP or SOCK_DGRAM for UDP.

    LOGD("getaddrinfo");
    status = getaddrinfo(host.c_str(), port.c_str(), &host_info,
        &host_info_list);
    if (status != 0) {
      LOGD("ERROR: Hostname could not be resolved");
      return false;
    }
    LOGD("socket init");
    socketfd = socket(host_info_list->ai_family, host_info_list->ai_socktype,
        host_info_list->ai_protocol);
    if (socketfd == -1) {
      LOGE("ERROR: Could not open socket");
      freeaddrinfo(host_info_list);
      return false;
    }

#if 0
    status = ::connect(socketfd, host_info_list_->ai_addr,
        host_info_list_->ai_addrlen);
#else
    status = NonBlockConnect(socketfd, host_info_list->ai_addr,
        host_info_list->ai_addrlen, 10);
#endif
    if (status == -1) {
      LOGE("ERROR: Could not connect");
      freeaddrinfo(host_info_list);
      close(socketfd);
      return false;
    }
    sock_ = socketfd;
    host_info_list_ = host_info_list;
    LOGD("connect %s success!\n", host.c_str());
    return true;
  }

  virtual int Write(byte* bytes, int bytes_len) {
    if (sock_ < 0) {
      return -1;
    }
    return Send(sock_, bytes, bytes_len);
  }

  virtual int Read(byte* buffer, int buffer_len, int timeout_millisecond) {
    if (sock_ < 0) {
      //没有连接
      return -1;
    }
    struct pollfd fd;
    fd.fd = sock_;
    fd.events = POLLIN;
    int ret = poll(&fd, 1, timeout_millisecond);
    switch (ret) {
    case -1:
      //LOGD("poll error"); // Error
      Close();
      return -1;
      break;
    case 0:
      // Timeout
      //LOGD("select read timeouot");
      return net::E_TIMEOUT;
      break;
    default: {
      int recv_bytes = recv(sock_, buffer, buffer_len, 0);
      if (recv_bytes == 0) {
        //连接已关闭
        LOGD("recv 0, close it");
        Close();
        return 0;
      } else if (recv_bytes < 0) {
        //添加错误处理
        if ((errno == EINTR) || (errno == EWOULDBLOCK) || (errno == EAGAIN)) {
          //继续recv
          LOGD("eagain");
        } else {
          LOGD("disconnect %d", errno);
          Close();
          return -1;
        }
      } else if (recv_bytes > 0) {
        return recv_bytes;
      }
    }
      break;
    }
    return -1;
  }
  virtual void Close() {
    if (sock_ >= 0) {
      LOGD("SocketClient close socket...\n");
      freeaddrinfo(host_info_list_);
      host_info_list_ = NULL;
      close(sock_);
      sock_ = -1;
    }
  }
  virtual Addr LocalAddr() {
    return Addr();
  }
  virtual Addr RemoteAddr() {
    return Addr();
  }

  TcpClientConn() {
    sock_ = -1;
    host_info_list_ = NULL;
  }
  virtual ~TcpClientConn() {
    Close();
  }

private:
  int sock_;
  struct addrinfo *host_info_list_;
};

class UdpConn : public Conn {
public:
  bool Initialize(std::string host, std::string port) {
    if ((sock_ = socket(AF_INET, SOCK_DGRAM, 0)) == -1) {
        LOGD("socket fail\n");
        return false;
    }

#if 0
    //设置为广播类型，
    const int opt = 1;
    int nb = 0;
    nb = setsockopt(sock_, SOL_SOCKET, SO_BROADCAST, (char *)&opt, sizeof(opt));
    if(nb == -1) {
      LOGD("set socket error...");
      return false;
    }
#endif


#if 0
    /*设置套接字为非阻塞*/
    int flags = fcntl(sock_, F_GETFL, 0);
    if (flags < 0) {
        LOGD("Get flags error:%s", strerror(errno));
        return -1;
    }
    flags |= O_NONBLOCK;
    if (fcntl(sock_, F_SETFL, flags) < 0) {
        LOGD("Set flags error:%s", strerror(errno));
        return -1;
    }
#endif

    memset(&remote_addr_, 0, sizeof(remote_addr_));
    remote_addr_.sin_family = AF_INET;
    remote_addr_.sin_port = htons(atoi(port.c_str()));
    remote_addr_.sin_addr.s_addr = inet_addr(host.c_str());
    return true;
  }

  virtual int Write(byte* bytes, int bytes_len) {
    if (sock_ < 0) {
      return -1;
    }
    return sendto(sock_, bytes, bytes_len, 0, (sockaddr*)&remote_addr_, sizeof(remote_addr_));
  }
  /**
   * timeout: 超时时间  毫秒
   * return >0  读到数据
   *        =0  已关闭
   *        -10000 读取超时
   *        其他   出错
   */
  virtual int Read(byte* buffer, int buffer_len, int timeout_millisecond) {
    if (sock_ < 0) {
      //没有连接
      return -1;
    }
    struct pollfd fd;
    fd.fd = sock_;
    fd.events = POLLIN;
    int ret = poll(&fd, 1, timeout_millisecond);
    switch (ret) {
    case -1:
      //LOGD("poll error"); // Error
      Close();
      return -1;
      break;
    case 0:
      // Timeout
      //LOGD("select read timeouot");
      return net::E_TIMEOUT;
      break;
    default: {
      socklen_t  addr_len = sizeof(remote_addr_);
      int recv_bytes = recvfrom(sock_, buffer, buffer_len, 0, (sockaddr*)&remote_addr_, &addr_len);
      if (recv_bytes == 0) {
        //连接已关闭
        LOGD("recv 0, close it");
        Close();
        return 0;
      } else if (recv_bytes < 0) {
        //添加错误处理
        if ((errno == EINTR) || (errno == EWOULDBLOCK) || (errno == EAGAIN)) {
          //继续recv
          LOGD("eagain");
        } else {
          LOGD("disconnect %d", errno);
          Close();
          return -1;
        }
      } else if (recv_bytes > 0) {
        return recv_bytes;
      }
    }
      break;
    }
    return -1;
  }
  virtual void Close() {
    if (sock_ >= 0) {
      LOGD("UdpClient close socket");
      close(sock_);
      sock_ = -1;
    }
  }
  virtual Addr LocalAddr() {
    return Addr();
  }
  virtual Addr RemoteAddr() {
    return Addr();
  }

  virtual ~UdpConn() {
    Close();
  }
private:
  struct sockaddr_in remote_addr_;
  int sock_;
};

/**
 * tcp, 192.168.1.1:80
 */
Conn* Dial(std::string network, std::string address) {
  signal(SIGPIPE,SIG_IGN);
  int colon = address.find(':');
  if (network.compare("tcp") == 0) {
    TcpClientConn* tcp = new TcpClientConn();
    tcp->Connect(address.substr(0, colon), address.substr(colon + 1));
    return tcp;
  } else if (network.compare("udp") == 0) {
    UdpConn* udp = new UdpConn();
    udp->Initialize(address.substr(0, colon), address.substr(colon + 1));
    return udp;
  } else {
    return NULL;
  }
}


} /* namespace net */

