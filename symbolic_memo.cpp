// Exhaustive equality-pattern search for failure of the lexicographically
// first minimum mask. U precedes V. Alphabet size is unrestricted.
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
#include <unordered_set>
using namespace std;
struct DSU {
 array<int,32> p;
 DSU(){for(int i=0;i<32;++i)p[i]=i;}
 int root(int i)const{while(p[i]!=i)i=p[i];return i;}
 void join(int i,int j){p[root(i)]=root(j);}
};
struct Opt {int degree;uint32_t priority;};
static Opt optimal(const DSU &d,int m,int n,const vector<int>&w) {
 Opt dp[32][2],next[32][2];
 for(auto &row:dp)row[0]=row[1]={99,0};dp[0][0]={0,0};
 auto put=[](Opt &old,int degree,uint32_t priority){if(degree<old.degree||(degree==old.degree&&priority>old.priority))old={degree,priority};};
 for(int t=0;t<m+n;++t) {
  for(auto &row:next)row[0]=row[1]={99,0};
  for(int i=max(0,t-n);i<=min(m,t);++i) {
   int j=t-i;
   for(int last=0;last<2;++last) {
    auto x=dp[i][last];if(x.degree==99)continue;
    if(i<m&&d.root(i)==d.root(w[t]))put(next[i+1][1],x.degree+(last==0),(x.priority<<1)|1);
    if(j<n&&d.root(m+j)==d.root(w[t]))put(next[i][0],x.degree,x.priority<<1);
   }
  }
  for(int i=0;i<32;++i)for(int k=0;k<2;++k)dp[i][k]=next[i][k];
 }
 Opt x=dp[m][0];put(x,dp[m][1].degree,dp[m][1].priority);return x;
}
static vector<int> identities(uint32_t mask,int m,int L) {
 vector<int>w;int i=0,j=m;for(int t=0;t<L;++t)w.push_back(mask>>t&1?i++:j++);return w;
}
int main(int argc,char**argv) {
 int bound=argc>1?stoi(argv[1]):16,r=argc>2?stoi(argv[2]):4,start=argc>3?stoi(argv[3]):2*r-1;
 string tag=argc>4?argv[4]:"symbolic";
 if(bound>30||r<3)return 2;
 uint64_t tm=0,tn=0,tp=0,tb=0;
 auto begun=chrono::steady_clock::now();ofstream evidence(tag+"-bad.jsonl");
 for(int L=start;L<=bound;++L) {
  uint64_t masks=0,nodes=0,pruned_low=0,pruned_earlier=0,bad=0,duplicates=0;
  map<int,vector<vector<int>>> alternatives;
  for(uint32_t z=1;z<(1u<<L);++z) {
   int m=__builtin_popcount(z),rr=__builtin_popcount(z&~(z<<1));
   if(m==L||rr>r-2)continue;
   alternatives[m].push_back(identities(z,m,L));
  }
  for(uint32_t mask=1;mask<(1u<<L);++mask) {
   if(__builtin_popcount(mask&~(mask<<1))!=r)continue;
   int m=__builtin_popcount(mask),n=L-m;uint32_t priority=0;
   for(int t=0;t<L;++t)priority=(priority<<1)|(mask>>t&1);
   vector<int>original=identities(mask,m,L);
   vector<array<int,3>> blocks;int lo=0;
   for(int t=1;t<=L;++t)if(t==L||((mask>>t)&1)!=((mask>>lo)&1)){blocks.push_back({lo,t,int((mask>>lo)&1)});lo=t;}
   vector<vector<int>>moved;
   for(int k=1;k+1<(int)blocks.size();++k)if(!blocks[k][2]) {
    int a=blocks[k][0],b=blocks[k][1],l=blocks[k-1][0],h=blocks[k+1][1];
    for(auto move:vector<array<int,3>>{{l,a,b},{a,b,h}}){auto w=original;rotate(w.begin()+move[0],w.begin()+move[1],w.begin()+move[2]);moved.push_back(w);}
   }
   ++masks;
   vector<int> chosen(moved.size());
   vector<unordered_set<string>> seen(moved.size()+1);
   function<void(int,DSU)> branch=[&](int depth,DSU eq) {
    if(depth==(int)moved.size()) {
     ++bad;
     string letters;vector<int>roots;
     for(int i=0;i<L;++i){int x=eq.root(i);auto it=find(roots.begin(),roots.end(),x);if(it==roots.end()){roots.push_back(x);it=roots.end()-1;}letters+=char('A'+(it-roots.begin()));}
     string w,ms;for(int x:original)w+=letters[x];for(int t=0;t<L;++t)ms+=(mask>>t&1)?'U':'V';
     evidence<<"{\"u\":\""<<letters.substr(0,m)<<"\",\"v\":\""<<letters.substr(m)<<"\",\"w\":\""<<w<<"\",\"degree\":"<<r<<",\"mask\":\""<<ms<<"\",\"witness_indices\":[";
     for(size_t k=0;k<chosen.size();++k){if(k)evidence<<",";evidence<<chosen[k];}evidence<<"]}\n";evidence.flush();
     return;
    }
    auto &ww=moved[depth];auto &alts=alternatives[m];
    for(int k=0;k<(int)alts.size();++k) {
     DSU next=eq;for(int t=0;t<L;++t)next.join(ww[t],alts[k][t]);++nodes;
     array<int,32> names;names.fill(-1);int next_name=0;string key;
     for(int t=0;t<L;++t){int x=next.root(t);if(names[x]<0)names[x]=next_name++;key+=char(names[x]);}
     if(!seen[depth+1].insert(key).second){++duplicates;continue;}
     auto opt=optimal(next,m,n,original);
     if(opt.degree<r){++pruned_low;continue;}
     if(opt.priority>priority){++pruned_earlier;continue;}
     chosen[depth]=k;branch(depth+1,next);
    }
   };
   branch(0,DSU{});
  }
  tm+=masks;tn+=nodes;tp+=pruned_low+pruned_earlier;tb+=bad;
  cout<<"{\"length\":"<<L<<",\"degree\":"<<r<<",\"masks\":"<<masks<<",\"nodes\":"<<nodes<<",\"pruned_low\":"<<pruned_low<<",\"pruned_earlier\":"<<pruned_earlier<<",\"duplicates\":"<<duplicates<<",\"bad\":"<<bad<<",\"total_masks\":"<<tm<<",\"total_nodes\":"<<tn<<",\"total_bad\":"<<tb<<",\"elapsed\":"<<chrono::duration<double>(chrono::steady_clock::now()-begun).count()<<"}"<<endl;
 }
 return 0;
}
