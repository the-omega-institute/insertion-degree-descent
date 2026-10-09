#define main audit_main
#include "audit.cpp"
#undef main
#include <random>

static vector<Mask> makemasks(int m,int n) {
 vector<Mask> out;
 function<void(int,int,uint32_t)> visit=[&](int p,int i,uint32_t mask){
  if(p==m+n) {
   Mask x{mask,0,__builtin_popcount(mask&~(mask<<1)),{}};
   for(int t=0;t<m+n;++t)x.priority=(x.priority<<1)|((mask>>t)&1);
   vector<array<int,3>> blocks;int lo=0;
   for(int t=1;t<=m+n;++t)if(t==m+n||((mask>>t)&1)!=((mask>>lo)&1)){blocks.push_back({lo,t,int((mask>>lo)&1)});lo=t;}
   for(int k=1;k+1<(int)blocks.size();++k)if(!blocks[k][2]) {
    int a=blocks[k][0],b=blocks[k][1],l=blocks[k-1][0],h=blocks[k+1][1];
    x.moves.push_back({l,a,b,a,b-a,a-l,0});x.moves.push_back({a,b,h,a,b-a,h-b,1});
   }
   out.push_back(std::move(x));return;
  }
  if(i<m)visit(p+1,i+1,mask|(1u<<p));
  if(p-i<n)visit(p+1,i,mask);
 };
 visit(0,0,0);return out;
}
int main(int argc,char**argv) {
 wordbits=1;
 string tag=argc>1?argv[1]:"targeted";
 int maxlen=argc>2?stoi(argv[2]):20;
 set<pair<string,string>> pairs;
 auto periodic=[](string base,int n,int offset){string s;for(int i=0;i<n;++i)s+=base[(i+offset)%base.size()];return s;};
 for(int period=2;period<=4;++period)for(int bits=1;bits<(1<<period)-1;++bits){
  string base;for(int i=0;i<period;++i)base+=char('0'+(bits>>i&1));
  for(int m=3;m<=12;++m)for(int n=3;n<=12&&m+n<=maxlen;++n)for(int phase=0;phase<period;++phase) {
   string u=periodic(base,m,0),v=periodic(base,n,phase);pairs.insert({u,v});
   if(m+n<=18)for(int k=0;k<m;++k){auto a=u;a[k]^=1;pairs.insert({a,v});}
   if(m+n<=18)for(int k=0;k<n;++k){auto b=v;b[k]^=1;pairs.insert({u,b});}
  }
 }
 vector<pair<string,string>> ordered(pairs.begin(),pairs.end());
 sort(ordered.begin(),ordered.end(),[](auto &a,auto &b){int n=a.first.size()+a.second.size(),m=b.first.size()+b.second.size();if(n!=m)return n<m;return a<b;});
 ofstream evidence(tag+"-failures.jsonl");
 ofstream inputs(tag+"-pairs.tsv");for(auto &[u,v]:ordered)inputs<<u<<"\t"<<v<<"\n";inputs.close();
 map<pair<int,int>,vector<Mask>> cache;
 uint64_t count=0,outputs=0,higher=0,badfirst=0,badlast=0,badmask=0,badlocal=0,badfactor=0,existfailed=0;
 int cached_length=-1;
 auto started=chrono::steady_clock::now();
 cerr<<"pairs "<<ordered.size()<<"\n";
 for(auto &[u,v]:ordered) {
  int m=u.size(),n=u.size()+v.size();
  if(n!=cached_length){cache.clear();cached_length=n;}
  auto key=make_pair(m,n-m);if(!cache.count(key))cache[key]=makemasks(m,n-m);
  auto &masks=cache[key];vector<Rec> recs(masks.size());vector<unsigned char> degree(1u<<n,255);
  string letters=u+v;
  for(int k=0;k<(int)masks.size();++k) {uint64_t w=0;int i=0,j=m;for(int p=0;p<n;++p)w|=uint64_t(letters[(masks[k].bits>>p&1)?i++:j++]-'0')<<p;recs[k]={w,k};degree[w]=min(int(degree[w]),masks[k].r);}
  sort(recs.begin(),recs.end(),[&](const Rec &a,const Rec &b){if(a.word!=b.word)return a.word<b.word;return masks[a.idx].priority>masks[b.idx].priority;});
  for(size_t l=0;l<recs.size();) {
   size_t h=l+1;while(h<recs.size()&&recs[h].word==recs[l].word)++h;
   ++outputs;uint64_t w=recs[l].word;int r=degree[w];
   if(r>1) {
    ++higher;vector<int> minima;for(size_t k=l;k<h;++k)if(masks[recs[k].idx].r==r)minima.push_back(recs[k].idx);
    auto works=[&](int idx){for(auto &a:masks[idx].moves)if(degree[rotateword(w,a)]==r-1)return true;return false;};
    bool f=works(minima.front()),b=works(minima.back());
    if(!f||!b) {
     badfirst+=!f;badlast+=!b;
     bool any=false;for(int idx:minima)any|=works(idx);
     if(!any)++existfailed;
     evidence<<"{\"u\":\""<<u<<"\",\"v\":\""<<v<<"\",\"w\":\""<<wordstr(w,n)<<"\",\"degree\":"<<r<<",\"first_failed\":"<<(!f?"true":"false")<<",\"last_failed\":"<<(!b?"true":"false")<<",\"existence_failed\":"<<(!any?"true":"false")<<",\"masks\":[";
     for(size_t t=0;t<minima.size();++t){if(t)evidence<<",";auto &x=masks[minima[t]];evidence<<"{\"mask\":\""<<maskstr(x.bits,n)<<"\",\"moves\":[";for(size_t k=0;k<x.moves.size();++k){if(k)evidence<<",";auto &a=x.moves[k];evidence<<"{\"word\":\""<<wordstr(rotateword(w,a),n)<<"\",\"degree\":"<<int(degree[rotateword(w,a)])<<",\"separator\":"<<a.sep<<",\"side\":\""<<(a.side?"right":"left")<<"\"}";}evidence<<"]}";}evidence<<"]}\n";evidence.flush();
     cerr<<"EXTREMAL FAILURE "<<u<<" "<<v<<" "<<wordstr(w,n)<<" "<<r<<" "<<any<<"\n";
     if(!any)return 3;
    }
    if(n<=18&&r>=4)for(int idx:minima)if(!works(idx)){
      ++badmask;uint32_t z=masks[idx].bits;bool local=false;
      for(int p=0;p<n-1;++p)if(!(z>>p&1)&&(z>>(p+1)&1)&&((w>>p&1)==(w>>(p+1)&1))) {
       uint32_t nz=z^(3u<<p);if(__builtin_popcount(nz&~(nz<<1))==r)local=true;
      }
      if(!local){++badlocal;if(badlocal<=30)evidence<<"{\"rule\":\"bad_mask_no_equal_shift\",\"u\":\""<<u<<"\",\"v\":\""<<v<<"\",\"w\":\""<<wordstr(w,n)<<"\",\"degree\":"<<r<<",\"mask\":\""<<maskstr(z,n)<<"\"}\n";}
    }
    if(r>=3)for(int idx:minima)if(!works(idx)) {
      string ww=wordstr(w,n),ll=maskstr(masks[idx].bits,n);
      vector<int> starts{0};for(int p=1;p<n;++p)if(ll[p]!=ll[p-1])starts.push_back(p);starts.push_back(n);
      bool shift=false;
      for(int k=0;k+2<(int)starts.size();++k)if(ll[starts[k]]=='V') {
        string a=ww.substr(starts[k],starts[k+1]-starts[k]),b=ww.substr(starts[k+1],starts[k+2]-starts[k+1]);
        if(a.size()>b.size()&&a.compare(a.size()-b.size(),b.size(),b)==0)shift=true;
        if(k==0&&a==b)shift=true;
        if(k>0&&a.size()<b.size()&&b.compare(0,a.size(),a)==0)shift=true;
      }
      if(!shift){++badfactor;if(badfactor<=100)evidence<<"{\"rule\":\"bad_mask_no_factor_shift\",\"u\":\""<<u<<"\",\"v\":\""<<v<<"\",\"w\":\""<<ww<<"\",\"degree\":"<<r<<",\"mask\":\""<<ll<<"\"}\n";}
    }
   }
   l=h;
  }
  ++count;
  if(count%100==0||count==ordered.size())cout<<"{\"pairs\":"<<count<<",\"outputs\":"<<outputs<<",\"higher\":"<<higher<<",\"bad_first\":"<<badfirst<<",\"bad_last\":"<<badlast<<",\"bad_masks\":"<<badmask<<",\"bad_no_equal_shift\":"<<badlocal<<",\"bad_no_factor_shift\":"<<badfactor<<",\"existence_failed\":"<<existfailed<<",\"length\":"<<n<<",\"elapsed\":"<<chrono::duration<double>(chrono::steady_clock::now()-started).count()<<"}"<<endl;
 }
}
