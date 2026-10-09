// Exhaustive grouping of every output and every minimum mask in an exact
// binary source-pair list. The new rule is checked on every degree-three bad mask.
#include <algorithm>
#include <array>
#include <chrono>
#include <cstdint>
#include <fstream>
#include <functional>
#include <iostream>
#include <map>
#include <string>
#include <vector>
using namespace std;
struct Mask {uint32_t bits;int runs;};
struct Rec {uint32_t word;uint32_t idx;};
struct Block {int lo,hi;bool u;};
static uint32_t low(int n){return (1u<<n)-1;}
static int runs(uint32_t b){return __builtin_popcount(b&~(b<<1));}
static uint32_t emit(const string&u,const string&v,uint32_t b) {
    uint32_t w=0;int i=0,j=0;
    for(int k=0;k<(int)(u.size()+v.size());++k)
        w|=uint32_t(((b>>k&1)?u[i++]:v[j++])-'0')<<k;
    return w;
}
static string wordstr(uint32_t w,int n){string s;for(int i=0;i<n;++i)s+=char('0'+(w>>i&1));return s;}
static string maskstr(uint32_t w,int n){string s;for(int i=0;i<n;++i)s+=(w>>i&1)?'U':'V';return s;}
static vector<Block> blocks(uint32_t b,int n) {
    vector<Block>out;int start=0;
    for(int i=1;i<=n;++i)if(i==n||(b>>i&1)!=(b>>start&1)) {
        out.push_back({start,i,bool(b>>start&1)});start=i;
    }
    return out;
}
static vector<uint32_t> moves(uint32_t w,uint32_t b,int n) {
    auto bb=blocks(b,n);vector<uint32_t>out;
    auto rotate=[&](int l,int k,int h) {
        int a=k-l,z=h-k;
        return (w&~(low(h)^low(l)))|(((w>>k)&low(z))<<l)|(((w>>l)&low(a))<<(l+z));
    };
    for(int k=1;k+1<(int)bb.size();++k)if(!bb[k].u) {
        out.push_back(rotate(bb[k-1].lo,bb[k].lo,bb[k].hi));
        out.push_back(rotate(bb[k].lo,bb[k].hi,bb[k+1].hi));
    }
    return out;
}
int main(int argc,char**argv) {
    if(argc!=3)return 2;
    ifstream input(argv[1]);ofstream evidence(string(argv[2])+"-bad-masks.jsonl");
    string u,v;map<pair<int,int>,vector<Mask>>cache;int last_length=-1;
    uint64_t pairs=0,outputs=0,higher=0,three=0,three_masks=0,bad=0,nonperiod=0,strong_failed=0,mask_count=0;
    auto start=chrono::steady_clock::now();
    auto report=[&](bool final) {
        cout<<"{\"complete\":"<<(final?"true":"false")<<",\"pairs\":"<<pairs<<",\"outputs\":"<<outputs
            <<",\"higher\":"<<higher<<",\"source_position_masks\":"<<mask_count<<",\"degree_three_outputs\":"<<three
            <<",\"degree_three_minimum_masks\":"<<three_masks<<",\"bad_degree_three_masks\":"<<bad
            <<",\"bad_nonperiodic_masks\":"<<nonperiod<<",\"strong_vector_failures\":"<<strong_failed
            <<",\"shift_rule_failures\":0,\"elapsed_seconds\":"<<chrono::duration<double>(chrono::steady_clock::now()-start).count()<<"}\n";
        cout.flush();
    };
    while(input>>u>>v) {
        int m=u.size(),n=m+v.size();if(n>22||n<2)return 3;
        if(n!=last_length){cache.clear();last_length=n;}
        auto key=make_pair(m,n-m);
        if(!cache.count(key)) {
            vector<Mask>mm;
            for(uint32_t b=1;b<(1u<<n);++b)if(__builtin_popcount(b)==m)mm.push_back({b,runs(b)});
            cache[key]=std::move(mm);
        }
        auto &mm=cache[key];vector<Rec>recs(mm.size());vector<unsigned char>degree(1u<<n,99);
        for(uint32_t k=0;k<mm.size();++k) {
            uint32_t w=emit(u,v,mm[k].bits);recs[k]={w,k};degree[w]=min(int(degree[w]),mm[k].runs);
        }
        mask_count+=mm.size();sort(recs.begin(),recs.end(),[](const Rec&a,const Rec&b){return a.word<b.word;});
        for(size_t l=0;l<recs.size();) {
            size_t h=l+1;while(h<recs.size()&&recs[h].word==recs[l].word)++h;
            ++outputs;uint32_t w=recs[l].word;int r=degree[w];higher+=r>1;
            if(r==3) {
                ++three;
                for(size_t k=l;k<h;++k)if(mm[recs[k].idx].runs==3) {
                    ++three_masks;uint32_t b=mm[recs[k].idx].bits;auto zz=moves(w,b,n);
                    bool exact=false;for(auto z:zz)exact|=degree[z]==2;if(exact)continue;
                    ++bad;auto bb=blocks(b,n);int s=bb[0].u?0:1;string ww=wordstr(w,n);
                    string a=ww.substr(bb[s].lo,bb[s].hi-bb[s].lo),
                        p=ww.substr(bb[s+1].lo,bb[s+1].hi-bb[s+1].lo),
                        c=ww.substr(bb[s+2].lo,bb[s+2].hi-bb[s+2].lo),
                        q=ww.substr(bb[s+3].lo,bb[s+3].hi-bb[s+3].lo),
                        d=ww.substr(bb[s+4].lo,bb[s+4].hi-bb[s+4].lo);
                    vector<string> factors{p,q,a+c,c+d};bool common=true;
                    for(int i=0;i<4;++i)for(int j=0;j<i;++j)common&=factors[i]+factors[j]==factors[j]+factors[i];
                    nonperiod+=!common;
                    if(p.size()<=c.size()||p.substr(p.size()-c.size())!=c) {
                        cerr<<"NO SHIFT "<<u<<" "<<v<<" "<<ww<<" "<<maskstr(b,n)<<"\n";return 4;
                    }
                    int pos=bb[s+2].lo,z=c.size();
                    uint32_t shifted=b^(low(z)<<(pos-z))^(low(z)<<pos);
                    if(emit(u,v,shifted)!=w||runs(shifted)!=3)return 5;
                    auto shifted_moves=moves(w,shifted,n);array<int,4>expected{2,1,1,2};bool strong=true;
                    if(degree[shifted_moves[0]]!=2) {
                        cerr<<"RULE FAILURE "<<u<<" "<<v<<" "<<ww<<" "<<maskstr(b,n)<<"\n";return 6;
                    }
                    for(int i=0;i<4;++i)strong&=degree[shifted_moves[i]]==expected[i];strong_failed+=!strong;
                    evidence<<"{\"u\":\""<<u<<"\",\"v\":\""<<v<<"\",\"w\":\""<<ww<<"\",\"mask\":\""<<maskstr(b,n)
                        <<"\",\"shifted_mask\":\""<<maskstr(shifted,n)<<"\",\"degrees\":[";
                    for(int i=0;i<4;++i){if(i)evidence<<",";evidence<<int(degree[shifted_moves[i]]);}evidence<<"]}\n";
                }
            }
            l=h;
        }
        ++pairs;if(pairs%5000==0)report(false);
    }
    report(true);
}
