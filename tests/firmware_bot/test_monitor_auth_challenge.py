from pathlib import Path
import os, subprocess, tempfile
src=Path(__file__).resolve().parents[2]/'vendor/MeshCore/examples/companion_radio'
mock=r"""
#pragma once
#include <string>
#include <map>
using String=std::string;
enum HTTPAuthMethod {BASIC_AUTH,DIGEST_AUTH};
class WebServer {
protected:
 String _snonce,_sopaque,_srealm;
 String _getRandomHexString(){static int n=0;return std::to_string(++n);}
public:
 int status=0,basic=0;std::map<String,String> headers;
 explicit WebServer(int){}
 void requestAuthentication(HTTPAuthMethod,const char*,const String&){++basic;}
 void sendHeader(const String& k,const String& v){headers[k]=v;}
 void send(int s,const char*,const String&){status=s;}
};
"""
test=r"""
#include "MonitorWebServer.h"
#include <cassert>
struct Inspect : MonitorWebServer {
 Inspect():MonitorWebServer(80){}
 String nonce(){return _snonce;}String opaque(){return _sopaque;}
};
int main(){
 Inspect server;
 server.requestAuthentication(DIGEST_AUTH,"Mesh battery monitor");
 const auto a=server.headers["WWW-Authenticate"];
 const auto nonce=server.nonce(),opaque=server.opaque();
 assert(server.status==401&&!nonce.empty()&&!opaque.empty());
 assert(a.find("nonce=\""+nonce+"\"")!=String::npos);
 assert(a.find("opaque=\""+opaque+"\"")!=String::npos);
 // Other tabs, users, and incorrect passwords may all trigger more challenges.
 for(int i=0;i<100;++i){server.requestAuthentication(DIGEST_AUTH,"Mesh battery monitor");assert(server.headers["WWW-Authenticate"]==a);assert(server.nonce()==nonce&&server.opaque()==opaque);}
 assert(server.headers["Cache-Control"]=="no-store");
 Inspect restarted;restarted.requestAuthentication(DIGEST_AUTH,"Mesh battery monitor");
 assert(restarted.nonce()!=nonce&&restarted.opaque()!=opaque);
 server.requestAuthentication(DIGEST_AUTH,"different realm");assert(server.nonce()!=nonce);
 server.requestAuthentication(BASIC_AUTH,"test");assert(server.basic==1);
}
"""
with tempfile.TemporaryDirectory() as folder:
 d=Path(folder);(d/'WebServer.h').write_text(mock);(d/'test.cpp').write_text(test)
 binary=d/'test.exe'
 subprocess.run([os.environ.get('CXX','c++'),'-std=c++17','-I',str(d),'-I',str(src),str(d/'test.cpp'),'-o',str(binary)],check=True)
 subprocess.run([str(binary)],check=True)
print('PASS: concurrent challenges remain valid, reboot and realm change replace challenge, no-store and Basic fallback')
