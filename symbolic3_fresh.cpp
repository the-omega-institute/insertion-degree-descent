// All-alphabet search: can all four moves of a three-run mask land at degree 1?
// Source letters start as distinct variables. Each contiguous-U witness imposes
// equalities; union-find yields the most general sources satisfying them.
#include <algorithm>
#include <array>
#include <chrono>
#include <cstdint>
#include <fstream>
#include <functional>
#include <iostream>
#include <string>
#include <vector>
using namespace std;
struct DSU {
 array<int,32> p;
 DSU(){for(int i=0;i<32;++i)p[i]=i;}
 int root(int i)const{while(p[i]!=i)i=p[i];return i;}
 void join(int i,int j){p[root(i)]=root(j);}
};
static int degree(const DSU &d,int m,int n,const vector<int>&w) {
 unsigned char dp[32][2],next[32][2];
 for(auto &row:dp)row[0]=row[1]=99;dp[0][0]=0;
 for(int t=0;t<m+n;++t) {
  for(auto &row:next)row[0]=row[1]=99;
  for(int i=max(0,t-n);i<=min(m,t);++i) {
   int j=t-i;
   if(i<m&&d.root(i)==d.root(w[t]))next[i+1][1]=min(int(dp[i][1]),int(dp[i][0])+1);
   if(j<n&&d.root(m+j)==d.root(w[t]))next[i][0]=min(dp[i][0],dp[i][1]);
  }
  for(int i=0;i<32;++i)for(int q=0;q<2;++q)dp[i][q]=next[i][q];
 }
 return min(dp[m][0],dp[m][1]);
}
int main(int argc,char**argv) {
 int bound=argc>1?stoi(argv[1]):15,start=argc>2?stoi(argv[2]):5;
 string tag=argc>3?argv[3]:"symbolic3";
 uint64_t total_masks=0,total_nodes=0,total_pruned=0,total_bad=0;
 auto begun=chrono::steady_clock::now();
 ofstream evidence(tag+"-bad.jsonl");
 for(int L=start;L<=bound;++L) {
  uint64_t masks=0,nodes=0,pruned=0,bad=0,different_left=0,different_right=0;
  for(int m=3;m<=L-2;++m) {
   int n=L-m;
   vector<vector<int>> contiguous;
   for(int cut=0;cut<=n;++cut){vector<int>x;for(int j=0;j<cut;++j)x.push_back(m+j);for(int i=0;i<m;++i)x.push_back(i);for(int j=cut;j<n;++j)x.push_back(m+j);contiguous.push_back(x);}
   for(int a=1;a<=m-2;++a)for(int c=1;c<=m-a-1;++c) {
    int e=m-a-c;
    for(int p=0;p<=n-2;++p)for(int b=1;b<=n-p-1;++b)for(int d=1;d<=n-p-b;++d) {
      int q=n-p-b-d;
      vector<int> original;string mask;
      int i=0,j=m;
      auto append=[&](int len,bool source){for(int k=0;k<len;++k){original.push_back(source?i++:j++);mask+=source?'U':'V';}};
      append(p,false);append(a,true);append(b,false);append(c,true);append(d,false);append(e,true);append(q,false);
      vector<vector<int>> moved;
      for(auto x:vector<array<int,3>>{{p,p+a,p+a+b},{p+a,p+a+b,p+a+b+c},{p+a+b,p+a+b+c,p+a+b+c+d},{p+a+b+c,p+a+b+c+d,p+a+b+c+d+e}}) {
       vector<int> w=original;
       rotate(w.begin()+x[0],w.begin()+x[1],w.begin()+x[2]);moved.push_back(w);
      }
      ++masks;
      array<int,4> chosen;
      function<void(int,DSU)> branch=[&](int depth,DSU eq) {
       if(depth==4) {
        ++bad;
        auto equal_outputs=[&](int a,int b){for(int t=0;t<L;++t)if(eq.root(moved[a][t])!=eq.root(moved[b][t]))return false;return true;};
        bool left_equal=equal_outputs(0,1),right_equal=equal_outputs(2,3);
        different_left+=!left_equal;different_right+=!right_equal;
        if(true) {
         string letters;vector<int>roots;
         for(int i=0;i<L;++i){int r=eq.root(i);auto it=find(roots.begin(),roots.end(),r);if(it==roots.end()){roots.push_back(r);it=roots.end()-1;}letters+=char('A'+(it-roots.begin()));}
         string w;for(int x:original)w+=letters[x];
         evidence<<"{\"u\":\""<<letters.substr(0,m)<<"\",\"v\":\""<<letters.substr(m)<<"\",\"w\":\""<<w<<"\",\"mask\":\""<<mask<<"\",\"cuts\":["<<chosen[0]<<","<<chosen[1]<<","<<chosen[2]<<","<<chosen[3]<<"],\"left_equal\":"<<(left_equal?"true":"false")<<",\"right_equal\":"<<(right_equal?"true":"false")<<"}\n";evidence.flush();
        }
        return;
       }
       for(int cut=0;cut<=n;++cut) {
        DSU next=eq;for(int t=0;t<L;++t)next.join(moved[depth][t],contiguous[cut][t]);
        ++nodes;
        if(degree(next,m,n,original)<=2){++pruned;continue;}
        chosen[depth]=cut;branch(depth+1,next);
       }
      };
      branch(0,DSU{});
    }
   }
  }
  total_masks+=masks;total_nodes+=nodes;total_pruned+=pruned;total_bad+=bad;
  cout<<"{\"length\":"<<L<<",\"masks\":"<<masks<<",\"nodes\":"<<nodes<<",\"pruned\":"<<pruned<<",\"bad\":"<<bad<<",\"different_left\":"<<different_left<<",\"different_right\":"<<different_right<<",\"total_masks\":"<<total_masks<<",\"total_nodes\":"<<total_nodes<<",\"total_bad\":"<<total_bad<<",\"elapsed\":"<<chrono::duration<double>(chrono::steady_clock::now()-begun).count()<<"}"<<endl;
 }
 return 0;
}
