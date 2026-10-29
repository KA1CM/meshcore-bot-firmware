"""Host fault-injection checks for the actual snapshot file helper; no board needed."""
from pathlib import Path
import os, subprocess, tempfile
src=Path(__file__).resolve().parents[2]/'vendor/MeshCore/examples/companion_radio'
mock=r'''
#pragma once
#include <map>
#include <string>
#include <vector>
#include <algorithm>
#include <cstdint>
#include <cstring>
#define FILE_READ "r"
#define FILE_WRITE "w"
struct MockFS;
struct File {
 MockFS* fs=nullptr;std::string path;size_t offset=0;bool valid=false;
 explicit operator bool()const{return valid;}
 size_t read(uint8_t*,size_t);size_t write(const uint8_t*,size_t);size_t size();
 void flush(){}void close(){}
};
struct MockFS {
 std::map<std::string,std::vector<uint8_t>> files;
 bool mounted=true,partial=false,corrupt=false;
 size_t totalBytes(){return mounted?1024*1024:0;}
 bool exists(const char* path){return files.count(path);}
 File open(const char* path,const char* mode){
  File result;result.fs=this;result.path=path;result.valid=mounted;
  if(!strcmp(mode,"w"))files[path].clear();else result.valid=result.valid&&exists(path);
  return result;
 }
}SPIFFS;
size_t File::size(){return fs->files[path].size();}
size_t File::read(uint8_t* out,size_t n){if(!valid)return 0;n=std::min(n,size()-offset);memcpy(out,fs->files[path].data()+offset,n);offset+=n;return n;}
size_t File::write(const uint8_t* data,size_t n){
 if(!valid)return 0;if(fs->partial)n/=2;
 auto& bytes=fs->files[path];bytes.insert(bytes.end(),data,data+n);
 if(fs->corrupt && n)bytes.back()^=1;
 return n;
}
'''
test=r'''
#include "BotSnapshotFile.h"
#include <cassert>
#include <cstring>
struct Payload {uint32_t count=0;uint8_t padding[5000]{};};
int main(){
 Payload data,out;BotSnapshotFile initial("/a","/b");
 assert(initial.load(&out,sizeof(out))==BotSnapshotFile::Missing);
 data.count=1;assert(initial.save(&data,sizeof(data)));
 data.count=2;assert(initial.save(&data,sizeof(data)));
 BotSnapshotFile reboot("/a","/b");assert(reboot.load(&out,sizeof(out))==BotSnapshotFile::Loaded&&out.count==2);
 SPIFFS.files["/b"].back()^=1;
 BotSnapshotFile damaged("/a","/b");assert(damaged.load(&out,sizeof(out))==BotSnapshotFile::Loaded&&out.count==1);
 SPIFFS.partial=true;data.count=3;assert(!damaged.save(&data,sizeof(data)));SPIFFS.partial=false;
 BotSnapshotFile interrupted("/a","/b");assert(interrupted.load(&out,sizeof(out))==BotSnapshotFile::Loaded&&out.count==1);
 SPIFFS.corrupt=true;assert(!interrupted.save(&data,sizeof(data)));assert(strstr(interrupted.lastError(),"verify"));SPIFFS.corrupt=false;
 BotSnapshotFile verify("/a","/b");assert(verify.load(&out,sizeof(out))==BotSnapshotFile::Loaded&&out.count==1);
 SPIFFS.mounted=false;assert(!verify.save(&data,sizeof(data)));assert(strstr(verify.lastError(),"filesystem"));
}
'''
with tempfile.TemporaryDirectory() as tmp:
    folder=Path(tmp);(folder/'SPIFFS.h').write_text(mock);(folder/'test.cpp').write_text(test)
    exe=folder/'test.exe'
    subprocess.run([os.environ.get('CXX','c++'),'-std=c++17','-I',str(folder),'-I',str(src),str(folder/'test.cpp'),'-o',str(exe)],check=True)
    subprocess.run([str(exe)],check=True)
print('PASS: large snapshot saves, reboot restore, corrupted/partial-write fallback, verification and unavailable filesystem')
