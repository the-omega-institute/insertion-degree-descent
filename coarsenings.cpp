// Independently check every equality coarsening of recorded witness partitions.
// A coarsening retaining original degree three must retain the exact 1L shift.
#include <algorithm>
#include <array>
#include <chrono>
#include <fstream>
#include <functional>
#include <iostream>
#include <map>
#include <sstream>
#include <string>
#include <vector>
using namespace std;
static int degree(const string& u,const string& v,const string& w) {
    const int m=u.size(),n=v.size();
    unsigned char dp[64][2],next[64][2];
    for(auto &row:dp)row[0]=row[1]=99;dp[0][0]=0;
    for(int t=0;t<m+n;++t) {
        for(auto &row:next)row[0]=row[1]=99;
        for(int i=max(0,t-n);i<=min(m,t);++i) {
            const int j=t-i;
            if(i<m&&u[i]==w[t]) next[i+1][1]=min(int(dp[i][1]),int(dp[i][0])+1);
            if(j<n&&v[j]==w[t]) next[i][0]=min(dp[i][0],dp[i][1]);
        }
        for(int i=0;i<64;++i)for(int q=0;q<2;++q)dp[i][q]=next[i][q];
    }
    return min(dp[m][0],dp[m][1]);
}
static vector<string> moves(const string& w,const string& mask) {
    vector<int>b{0};vector<string>out;
    for(int i=1;i<(int)mask.size();++i)if(mask[i]!=mask[i-1])b.push_back(i);
    b.push_back(mask.size());
    auto rotate=[&](int l,int k,int r){return w.substr(0,l)+w.substr(k,r-k)+w.substr(l,k-l)+w.substr(r);};
    for(int h=1;h+2<(int)b.size();++h)if(mask[b[h]]=='V') {
        out.push_back(rotate(b[h-1],b[h],b[h+1]));
        out.push_back(rotate(b[h],b[h+1],b[h+2]));
    }
    return out;
}
int main(int argc,char**argv) {
    if(argc!=2)return 2;
    ifstream input(argv[1]);string line;
    uint64_t total=0,kept=0,instances=0;array<uint64_t,4>ds{};
    auto start=chrono::steady_clock::now();
    while(getline(input,line)) {
        stringstream ss(line);array<string,5>x;for(auto &a:x)getline(ss,a,'\t');
        vector<char>alphabet;for(char c:x[0]+x[1])if(find(alphabet.begin(),alphabet.end(),c)==alphabet.end())alphabet.push_back(c);
        sort(alphabet.begin(),alphabet.end());vector<int>part(alphabet.size());
        function<void(int,int)>visit=[&](int k,int largest) {
            if(k<(int)part.size()) {
                for(int q=0;q<=largest+1;++q){part[k]=q;visit(k+1,max(largest,q));}
                return;
            }
            ++total;array<char,256>trans{};
            for(int i=0;i<(int)alphabet.size();++i)trans[(unsigned char)alphabet[i]]=char('A'+part[i]);
            array<string,3>y;for(int h=0;h<3;++h){y[h]=x[h];for(char &c:y[h])c=trans[(unsigned char)c];}
            int r=degree(y[0],y[1],y[2]);if(r>3){cerr<<"BAD ORIGINAL\n";exit(3);}++ds[r];
            if(r!=3)return;
            ++kept;auto z=moves(y[2],x[4]);
            array<int,4>expected{2,1,1,2};
            for(int h=0;h<4;++h)if(degree(y[0],y[1],z[h])!=expected[h]) {
                cerr<<"COUNTEREXAMPLE "<<y[0]<<" "<<y[1]<<" "<<y[2]<<" "<<x[3]<<" "<<x[4]<<" move "<<h<<"\n";exit(4);
            }
        };
        part[0]=0;visit(1,0);++instances;
        if(instances%20==0)cerr<<"instances "<<instances<<" coarsenings "<<total<<"\n";
    }
    cout<<"{\"status\":\"PASS\",\"instances\":"<<instances<<",\"coarsenings\":"<<total<<",\"degree_three_coarsenings\":"<<kept<<",\"degree_counts\":{\"1\":"<<ds[1]<<",\"2\":"<<ds[2]<<",\"3\":"<<ds[3]<<"},\"elapsed_seconds\":"<<chrono::duration<double>(chrono::steady_clock::now()-start).count()<<"}\n";
}
