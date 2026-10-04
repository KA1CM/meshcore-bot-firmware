from pathlib import Path
import os, subprocess, tempfile
repo=Path(__file__).resolve().parents[2]
source=(repo/'vendor/MeshCore/examples/companion_radio/BotPathLookup.cpp').read_text(encoding='utf-8')
client=source[source.index('class LookupClient'):source.index('// Let HTTPClient')]
harness=r"""
#include <cassert>
#include <cstdint>
#include <cstring>
#include <cerrno>
#include <string>
#define AF_INET 2
#define SOCK_STREAM 1
#define MBEDTLS_ERR_X509_CERT_VERIFY_FAILED -9984
#define MBEDTLS_SSL_HELLO_REQUEST 0
uint32_t ticks=0;uint32_t millis(){return ticks;}
struct sockaddr_in {struct {uint32_t s_addr=42;} sin_addr;};
struct addrinfo {int ai_family=0,ai_socktype=0;void* ai_addr=nullptr;};
int dnsResult=0;
int getaddrinfo(const char*,const char*,addrinfo*,addrinfo** result){static sockaddr_in ip;static addrinfo a;a.ai_addr=&ip;*result=&a;return dnsResult;}
void freeaddrinfo(addrinfo*){}
struct IPAddress {explicit IPAddress(uint32_t){}};
struct TLSState {int state=0;};
struct Context {TLSState ssl_ctx;int socket=-1;uint32_t handshake_timeout=15000;};
int tlsResult=-9984;uint32_t tlsFlags=8;bool stopped=false;std::string observedHost;
int start_ssl_client(Context* ctx,IPAddress,int,const char* host,int,const char*,bool,const char*,const char*,const char*,const char*,bool insecure,const char**){assert(!insecure);observedHost=host;if(tlsResult==-77){ctx->socket=3;ctx->ssl_ctx.state=2;ticks+=15001;return -1;}return tlsResult;}
uint32_t mbedtls_ssl_get_verify_result(TLSState*){assert(!stopped);return tlsFlags;}
struct WiFiClientSecure {
 Context ctx;Context* sslclient=&ctx;int _timeout=0,_lastError=0;bool _connected=false,_use_ca_bundle=false,_use_insecure=false;
 const char* _CA_cert="trusted",*_cert=nullptr,*_private_key=nullptr;const char** _alpn_protos=nullptr;
 virtual int connect(const char*,uint16_t,int32_t){return 0;}
 void stop(){stopped=true;tlsFlags=0;_connected=false;}
};
std::string stage;uint32_t reportedFlags=0;int detail=0;bool failed=false;
void report(const char* s,int d=0,bool f=false,uint32_t flags=0){stage=s;detail=d;failed=f;reportedFlags=flags;}
"""+client+r"""
int main(){
 LookupClient c;assert(c.connect("analyzer.ctmesh.org",443,4000)==0);
 assert(stopped&&c.connectionFailed&&failed&&detail==-9984&&reportedFlags==8);
 assert(stage=="TLS certificate verification failed"&&observedHost=="analyzer.ctmesh.org");
 stopped=false;tlsResult=5;assert(c.connect("analyzer.ctmesh.org",443,4000)==1);
 assert(!stopped&&!c.connectionFailed&&c._connected);
 stopped=false;tlsResult=-1;errno=111;assert(c.connect("analyzer.ctmesh.org",443,4000)==0);
 assert(stage=="TCP connection failed"&&reportedFlags==0&&stopped);
 stopped=false;tlsResult=-77;assert(c.connect("analyzer.ctmesh.org",443,4000)==0);
 assert(stage=="TLS handshake timed out (milliseconds)"&&detail==15001&&stopped);
 stopped=false;dnsResult=2;assert(c.connect("analyzer.ctmesh.org",443,4000)==0);
 assert(stage=="DNS resolution failed"&&!stopped);
}
"""
with tempfile.TemporaryDirectory() as tmp:
 p=Path(tmp);cpp=p/'test.cpp';cpp.write_text(harness,encoding='utf-8');exe=p/'test.exe'
 subprocess.run([os.environ.get('CXX','c++'),'-std=c++11','-Wall','-Wextra','-Werror',str(cpp),'-o',str(exe)],check=True)
 subprocess.run([str(exe)],check=True)
print('PASS: certificate flags captured before cleanup; verified TLS hostname retained; DNS/TCP failures distinguished')
