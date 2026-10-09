#include <algorithm>
#include <array>
#include <chrono>
#include <cstdint>
#include <fstream>
#include <functional>
#include <iostream>
#include <map>
#include <set>
#include <string>
#include <unordered_map>
#include <vector>
using namespace std;
static int wordbits=2;
struct Move {int lo,cut,hi,sep,vl,ul,side;};
struct Mask {uint32_t bits,priority; int r; vector<Move> moves;};
struct Rec {uint64_t word; int idx;};
struct Count {uint64_t tested=0,failed=0;};
static string wordstr(uint64_t w,int n) {string s;for(int i=0;i<n;++i)s+=char('0'+((w>>(wordbits*i))&((1u<<wordbits)-1)));return s;}
static string maskstr(uint32_t m,int n) {string s;for(int i=0;i<n;++i)s+=(m>>i&1)?'U':'V';return s;}
static uint64_t low(int k) {return (uint64_t(1)<<(wordbits*k))-1;}
static uint64_t rotateword(uint64_t w,const Move &a) {
    int l=a.cut-a.lo,r=a.hi-a.cut;
    uint64_t x=(w>>(wordbits*a.lo))&low(l),y=(w>>(wordbits*a.cut))&low(r);
    return (w&~(low(a.hi)^low(a.lo)))|(y<<(wordbits*a.lo))|(x<<(wordbits*(a.lo+r)));
}
int main(int argc,char**argv) {
    int q=argc>1?stoi(argv[1]):2,bound=argc>2?stoi(argv[2]):13;
    wordbits=q==2?1:2;
    string tag=argc>3?argv[3]:"audit";
    bool restricted=argc>4?stoi(argv[4]):false;
    int start=argc>5?stoi(argv[5]):2;
    map<string,Count> total;
    set<string> witnessed;
    ofstream witnesses(tag+"-witnesses.jsonl");
    auto started=chrono::steady_clock::now();
    for(int n=start;n<=bound;++n) {
      map<string,Count> counts;
      uint64_t pairs=0,outputs=0,higher=0,masks_count=0;
      for(int m=1;m<n;++m) {
        vector<Mask> masks;
        for(uint32_t mask=1;mask<(1u<<n);++mask) if(__builtin_popcount(mask)==m) {
          Mask x{mask,0,__builtin_popcount(mask&~(mask<<1)),{}};
          for(int p=0;p<n;++p) x.priority=(x.priority<<1)|((mask>>p)&1);
          vector<array<int,3>> blocks;
          int lo=0;
          for(int p=1;p<=n;++p) if(p==n||((mask>>p)&1)!=((mask>>lo)&1)) {
            blocks.push_back({lo,p,int((mask>>lo)&1)});lo=p;
          }
          for(int k=1;k+1<(int)blocks.size();++k) if(!blocks[k][2]) {
            int a=blocks[k][0],b=blocks[k][1],l=blocks[k-1][0],h=blocks[k+1][1];
            x.moves.push_back({l,a,b,a,b-a,a-l,0});
            x.moves.push_back({a,b,h,a,b-a,h-b,1});
          }
          masks.push_back(x);
        }
        vector<Rec> recs(masks.size());
        vector<unsigned char> degree(uint64_t(1)<<(wordbits*n),255);
        vector<int> letters(n);
        function<void(int,int)> visit=[&](int pos,int largest) {
          if(pos<n) {
            for(int a=0;a<q && (!restricted||a<=largest+1);++a) {letters[pos]=a;visit(pos+1,max(largest,a));}
            return;
          }
          ++pairs;
          string u,v;for(int p=0;p<n;++p)(p<m?u:v)+=char('0'+letters[p]);
          for(int k=0;k<(int)masks.size();++k) {
            int i=0,j=m;uint64_t w=0;
            for(int p=0;p<n;++p) w|=uint64_t(letters[(masks[k].bits>>p&1)?i++:j++])<<(wordbits*p);
            recs[k]={w,k};degree[w]=min(int(degree[w]),masks[k].r);
          }
          masks_count+=recs.size();
          sort(recs.begin(),recs.end(),[&](const Rec &a,const Rec &b){
            if(a.word!=b.word)return a.word<b.word;
            return masks[a.idx].priority>masks[b.idx].priority;
          });
          for(size_t l=0;l<recs.size();) {
            size_t h=l+1;while(h<recs.size()&&recs[h].word==recs[l].word)++h;
            uint64_t w=recs[l].word;int r=degree[w];++outputs;
            if(r>1) {
              ++higher;
              vector<int> minima;for(size_t k=l;k<h;++k)if(masks[recs[k].idx].r==r)minima.push_back(recs[k].idx);
              bool some=false;
              for(size_t t=0;t<minima.size();++t) {
                auto &x=masks[minima[t]];
                vector<int> ds;for(auto &a:x.moves)ds.push_back(degree[rotateword(w,a)]);
                auto record=[&](string name,vector<int> chosen) {
                  bool good=false;for(int k:chosen)good|=ds[k]==r-1;
                  ++counts[name].tested;
                  if(!good) {
                    ++counts[name].failed;
                    if(!witnessed.count(name)) {
                      witnessed.insert(name);
                      witnesses<<"{\"rule\":\""<<name<<"\",\"u\":\""<<u<<"\",\"v\":\""<<v<<"\",\"w\":\""<<wordstr(w,n)<<"\",\"degree\":"<<r<<",\"mask\":\""<<maskstr(x.bits,n)<<"\",\"moves\":[";
                      for(size_t k=0;k<x.moves.size();++k) {
                        auto &a=x.moves[k];if(k)witnesses<<",";
                        witnesses<<"{\"word\":\""<<wordstr(rotateword(w,a),n)<<"\",\"degree\":"<<ds[k]<<",\"separator\":"<<a.sep<<",\"vlength\":"<<a.vl<<",\"ulength\":"<<a.ul<<",\"side\":\""<<(a.side?"right":"left")<<"\",\"chosen\":"<<(find(chosen.begin(),chosen.end(),k)!=chosen.end()?"true":"false")<<"}";
                      }
                      witnesses<<"]}\n";witnesses.flush();
                    }
                  }
                  return good;
                };
                vector<int> all;for(int k=0;k<(int)x.moves.size();++k)all.push_back(k);
                some|=record("each_mask_any",all);
                for(int k=0;k<(int)x.moves.size();k+=2)record("each_separator_either",{k,k+1});
                vector<string> prefixes;
                if(t==0)prefixes.push_back("first_mask");
                if(t+1==minima.size())prefixes.push_back("last_mask");
                for(auto prefix:prefixes) {
                  record(prefix+"_any",all);
                  for(int side=0;side<2;++side) {
                    vector<int> kk;for(int k:all)if(x.moves[k].side==side)kk.push_back(k);
                    string ss=side?"right":"left";
                    record(prefix+"_any_"+ss,kk);
                    record(prefix+"_first_"+ss,{kk.front()});
                    record(prefix+"_last_"+ss,{kk.back()});
                  }
                  record(prefix+"_first_either",{0,1});
                  record(prefix+"_last_either",{int(all.size())-2,int(all.size())-1});
                  for(int measure=0;measure<2;++measure)for(int shortest=0;shortest<2;++shortest) {
                    int best=shortest?100:-1;
                    for(auto &a:x.moves) {int k=measure?a.ul:a.vl;best=shortest?min(best,k):max(best,k);}
                    vector<int> kk;for(int k:all)if((measure?x.moves[k].ul:x.moves[k].vl)==best)kk.push_back(k);
                    record(prefix+"_"+(shortest?"shortest":"longest")+"_"+(measure?"ulength":"vlength"),kk);
                  }
                }
              }
              ++counts["existence"].tested;
              if(!some) {++counts["existence"].failed;cerr<<"EXISTENCE FAILURE "<<u<<" "<<v<<" "<<wordstr(w,n)<<"\n";}
            }
            l=h;
          }
          for(auto &x:recs)degree[x.word]=255;
        };
        visit(0,-1);
      }
      cout<<"{\"length\":"<<n<<",\"pairs\":"<<pairs<<",\"outputs\":"<<outputs<<",\"higher\":"<<higher<<",\"masks\":"<<masks_count<<",\"elapsed\":"<<chrono::duration<double>(chrono::steady_clock::now()-started).count()<<",\"rules\":{";
      bool first=true;for(auto &[name,c]:counts) {if(!first)cout<<",";first=false;cout<<"\""<<name<<"\":{\"tested\":"<<c.tested<<",\"failed\":"<<c.failed<<"}";total[name].tested+=c.tested;total[name].failed+=c.failed;}
      cout<<"}}"<<endl;
      ofstream summary(tag+"-summary.json");
      summary<<"{\"alphabet_size\":"<<q<<",\"bound\":"<<bound<<",\"start_length\":"<<start<<",\"completed_length\":"<<n<<",\"restricted_growth\":"<<(restricted?"true":"false")<<",\"rules\":{";
      first=true;for(auto &[name,c]:total){if(!first)summary<<",";first=false;summary<<"\""<<name<<"\":{\"tested\":"<<c.tested<<",\"failed\":"<<c.failed<<"}";}summary<<"}}\n";
    }
    return 0;
}
