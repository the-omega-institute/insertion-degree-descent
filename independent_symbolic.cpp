#include <algorithm>
#include <array>
#include <chrono>
#include <fstream>
#include <functional>
#include <iostream>
#include <numeric>
#include <vector>
using namespace std;

// Independent degree-three search written for this review. No author code
// or library is used. Enumerate run lengths, then impose contiguous-source
// deletion witnesses. The degree check uses a two-dimensional source grid.
struct Partition {
    vector<int> p;
    explicit Partition(int n):p(n){iota(p.begin(),p.end(),0);}
    int root(int a) const {while(p[a]!=a)a=p[a];return a;}
    void join(int a,int b){a=root(a);b=root(b);if(a!=b)p[max(a,b)]=min(a,b);}
};
int degree(const vector<int>& out,int m,const Partition& eq){
    int n=int(out.size())-m, inf=1000;
    vector<array<int,2>> grid((m+1)*(n+1),{inf,inf});
    auto cell=[&](int i,int j)->array<int,2>&{return grid[i*(n+1)+j];};
    cell(0,0)[0]=0; // previous label V
    for(int i=0;i<=m;++i)for(int j=0;j<=n;++j){
        if(i+j==int(out.size()))continue;
        auto cur=cell(i,j);
        if(i<m && eq.root(i)==eq.root(out[i+j]))
            cell(i+1,j)[1]=min(cell(i+1,j)[1],min(cur[0]+1,cur[1]));
        if(j<n && eq.root(m+j)==eq.root(out[i+j]))
            cell(i,j+1)[0]=min(cell(i,j+1)[0],min(cur[0],cur[1]));
    }
    return min(cell(m,n)[0],cell(m,n)[1]);
}
int main(int argc,char**argv){
    int maximum=argc>1?stoi(argv[1]):20;
    ofstream leaves(argc>2?argv[2]:"independent-leaves.jsonl");
    long long cumulative_masks=0,cumulative_nodes=0,cumulative_bad=0;
    auto started=chrono::steady_clock::now();
    for(int L=5;L<=maximum;++L){
        long long masks=0,nodes=0,pruned=0,bad=0;
        // V^x U^a V^p U^b V^q U^c V^y, a,p,b,q,c > 0.
        for(int x=0;x<=L-5;++x)for(int a=1;a<=L-x-4;++a)
        for(int p=1;p<=L-x-a-3;++p)for(int b=1;b<=L-x-a-p-2;++b)
        for(int q=1;q<=L-x-a-p-b-1;++q)for(int c=1;c<=L-x-a-p-b-q;++c){
            int y=L-x-a-p-b-q-c,m=a+b+c,n=L-m;
            vector<pair<int,int>> blocks={{0,x},{1,a},{0,p},{1,b},{0,q},{1,c},{0,y}};
            vector<int> original; vector<int> labels; int ui=0,vi=m;
            for(auto [label,count]:blocks)for(int t=0;t<count;++t){
                original.push_back(label?ui++:vi++);labels.push_back(label);
            }
            array<vector<int>,4> successors;
            array<pair<int,int>,4> swaps={{{1,2},{2,3},{3,4},{4,5}}};
            for(int move=0;move<4;++move){
                vector<vector<int>> pieces;int offset=0;
                for(auto [label,count]:blocks){
                    pieces.emplace_back(original.begin()+offset,original.begin()+offset+count);
                    offset+=count;
                }
                swap(pieces[swaps[move].first],pieces[swaps[move].second]);
                for(auto&piece:pieces)successors[move].insert(successors[move].end(),piece.begin(),piece.end());
            }
            ++masks;array<int,4> cuts{};
            function<void(int,const Partition&)> search=[&](int move,const Partition& eq){
                if(move==4){
                    ++bad;
                    leaves<<"{\"length\":"<<L<<",\"m\":"<<m<<",\"mask\":\"";
                    for(int label:labels)leaves<<(label?'U':'V');
                    leaves<<"\",\"classes\":[";
                    for(int t=0;t<L;++t){if(t)leaves<<',';leaves<<eq.root(t);}
                    leaves<<"],\"cuts\":[";
                    for(int t=0;t<4;++t){if(t)leaves<<',';leaves<<cuts[t];}
                    leaves<<"]}\n";return;
                }
                for(int cut=0;cut<=n;++cut){
                    ++nodes;Partition next=eq;
                    for(int t=0;t<L;++t){
                        int source=t<cut?m+t:(t<cut+m?t-cut:m+t-m);
                        next.join(successors[move][t],source);
                    }
                    if(degree(original,m,next)<3){++pruned;continue;}
                    cuts[move]=cut;search(move+1,next);
                }
            };
            search(0,Partition(L));
        }
        cumulative_masks+=masks;cumulative_nodes+=nodes;cumulative_bad+=bad;
        double seconds=chrono::duration<double>(chrono::steady_clock::now()-started).count();
        cout<<"{\"length\":"<<L<<",\"masks\":"<<masks<<",\"nodes\":"<<nodes
            <<",\"pruned\":"<<pruned<<",\"bad\":"<<bad<<",\"total_masks\":"<<cumulative_masks
            <<",\"total_nodes\":"<<cumulative_nodes<<",\"total_bad\":"<<cumulative_bad
            <<",\"elapsed\":"<<seconds<<"}"<<endl;
    }
}
