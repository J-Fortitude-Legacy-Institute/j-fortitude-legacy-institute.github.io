import{bM as Ce,r as w,j as e,C as W,a0 as ie,I as te,B as E,a1 as oe,s as C,b as vr,d as yr,a as br,e as P,bi as $e,g as ee,E as Ne,P as ge,S as Ct,O as je,i as se,az as At,L as Pt,aj as Cr,ad as It,v as Ye,cn as Ot,D as Ft,c9 as Dt,l as Lt,m as Ut,n as Mt,W as z,T as le,X as De,Y as Le,Z as Ue,_ as Me,$ as ce,b$ as _r,a$ as Bt,bj as Ar,bh as Wt,a9 as Vr,f as Se,cG as mr,u as Gt,aC as Be,b_ as Pr,ao as Ir,bl as qt,bg as Ht}from"./index-CyuDsdKB.js";import{S as Jr}from"./smartphone-1tteGXQw.js";import{C as he}from"./copy-BcMX1SKM.js";import{E as _e}from"./external-link-BhEdPp6x.js";import{B as Kt}from"./BayconCampaignPanel-Cllf3kAw.js";import{P as zt}from"./package-CN0VgzGa.js";import{r as Ze,H as Or,R as ze,C as Vt,a as Jt,M as Yt,A as Zt}from"./MissionStatusBanner-BSCtY00U.js";import{C as Qe}from"./circle-x-BkawX5WK.js";import{L as Qt}from"./link-2-D3DzeISB.js";import{P as Yr}from"./plus-DachUQmk.js";import{B as ir}from"./beaker-DyK-EES0.js";import{R as Ke}from"./repeat-Yn9Ctx7u.js";import{P as Xt}from"./package-check-Da9RNSx2.js";import{f as en}from"./formatDistanceToNow-D9VL9dVM.js";import"./settings-DL6q0P94.js";import"./rocket-CmG4Pv_z.js";import"./calendar-clock-CMFTRUdF.js";import"./eye-DU6W1few.js";import"./circle-help-Clmk1mqI.js";import"./en-US-qzRY79ct.js";import"./endOfMonth-WTFpSllx.js";var Ae={},rn=function(){return typeof Promise=="function"&&Promise.prototype&&Promise.prototype.then},Zr={},re={};let kr;const tn=[0,26,44,70,100,134,172,196,242,292,346,404,466,532,581,655,733,815,901,991,1085,1156,1258,1364,1474,1588,1706,1828,1921,2051,2185,2323,2465,2611,2761,2876,3034,3196,3362,3532,3706];re.getSymbolSize=function(t){if(!t)throw new Error('"version" cannot be null or undefined');if(t<1||t>40)throw new Error('"version" should be in range from 1 to 40');return t*4+17};re.getSymbolTotalCodewords=function(t){return tn[t]};re.getBCHDigit=function(r){let t=0;for(;r!==0;)t++,r>>>=1;return t};re.setToSJISFunction=function(t){if(typeof t!="function")throw new Error('"toSJISFunc" is not a valid function.');kr=t};re.isKanjiModeEnabled=function(){return typeof kr<"u"};re.toSJIS=function(t){return kr(t)};var Xe={};(function(r){r.L={bit:1},r.M={bit:0},r.Q={bit:3},r.H={bit:2};function t(s){if(typeof s!="string")throw new Error("Param is not a string");switch(s.toLowerCase()){case"l":case"low":return r.L;case"m":case"medium":return r.M;case"q":case"quartile":return r.Q;case"h":case"high":return r.H;default:throw new Error("Unknown EC Level: "+s)}}r.isValid=function(o){return o&&typeof o.bit<"u"&&o.bit>=0&&o.bit<4},r.from=function(o,i){if(r.isValid(o))return o;try{return t(o)}catch{return i}}})(Xe);function Qr(){this.buffer=[],this.length=0}Qr.prototype={get:function(r){const t=Math.floor(r/8);return(this.buffer[t]>>>7-r%8&1)===1},put:function(r,t){for(let s=0;s<t;s++)this.putBit((r>>>t-s-1&1)===1)},getLengthInBits:function(){return this.length},putBit:function(r){const t=Math.floor(this.length/8);this.buffer.length<=t&&this.buffer.push(0),r&&(this.buffer[t]|=128>>>this.length%8),this.length++}};var nn=Qr;function Pe(r){if(!r||r<1)throw new Error("BitMatrix size must be defined and greater than 0");this.size=r,this.data=new Uint8Array(r*r),this.reservedBit=new Uint8Array(r*r)}Pe.prototype.set=function(r,t,s,o){const i=r*this.size+t;this.data[i]=s,o&&(this.reservedBit[i]=!0)};Pe.prototype.get=function(r,t){return this.data[r*this.size+t]};Pe.prototype.xor=function(r,t,s){this.data[r*this.size+t]^=s};Pe.prototype.isReserved=function(r,t){return this.reservedBit[r*this.size+t]};var sn=Pe,Xr={};(function(r){const t=re.getSymbolSize;r.getRowColCoords=function(o){if(o===1)return[];const i=Math.floor(o/7)+2,n=t(o),c=n===145?26:Math.ceil((n-13)/(2*i-2))*2,d=[n-7];for(let l=1;l<i-1;l++)d[l]=d[l-1]-c;return d.push(6),d.reverse()},r.getPositions=function(o){const i=[],n=r.getRowColCoords(o),c=n.length;for(let d=0;d<c;d++)for(let l=0;l<c;l++)d===0&&l===0||d===0&&l===c-1||d===c-1&&l===0||i.push([n[d],n[l]]);return i}})(Xr);var et={};const on=re.getSymbolSize,Fr=7;et.getPositions=function(t){const s=on(t);return[[0,0],[s-Fr,0],[0,s-Fr]]};var rt={};(function(r){r.Patterns={PATTERN000:0,PATTERN001:1,PATTERN010:2,PATTERN011:3,PATTERN100:4,PATTERN101:5,PATTERN110:6,PATTERN111:7};const t={N1:3,N2:3,N3:40,N4:10};r.isValid=function(i){return i!=null&&i!==""&&!isNaN(i)&&i>=0&&i<=7},r.from=function(i){return r.isValid(i)?parseInt(i,10):void 0},r.getPenaltyN1=function(i){const n=i.size;let c=0,d=0,l=0,m=null,f=null;for(let g=0;g<n;g++){d=l=0,m=f=null;for(let h=0;h<n;h++){let k=i.get(g,h);k===m?d++:(d>=5&&(c+=t.N1+(d-5)),m=k,d=1),k=i.get(h,g),k===f?l++:(l>=5&&(c+=t.N1+(l-5)),f=k,l=1)}d>=5&&(c+=t.N1+(d-5)),l>=5&&(c+=t.N1+(l-5))}return c},r.getPenaltyN2=function(i){const n=i.size;let c=0;for(let d=0;d<n-1;d++)for(let l=0;l<n-1;l++){const m=i.get(d,l)+i.get(d,l+1)+i.get(d+1,l)+i.get(d+1,l+1);(m===4||m===0)&&c++}return c*t.N2},r.getPenaltyN3=function(i){const n=i.size;let c=0,d=0,l=0;for(let m=0;m<n;m++){d=l=0;for(let f=0;f<n;f++)d=d<<1&2047|i.get(m,f),f>=10&&(d===1488||d===93)&&c++,l=l<<1&2047|i.get(f,m),f>=10&&(l===1488||l===93)&&c++}return c*t.N3},r.getPenaltyN4=function(i){let n=0;const c=i.data.length;for(let l=0;l<c;l++)n+=i.data[l];return Math.abs(Math.ceil(n*100/c/5)-10)*t.N4};function s(o,i,n){switch(o){case r.Patterns.PATTERN000:return(i+n)%2===0;case r.Patterns.PATTERN001:return i%2===0;case r.Patterns.PATTERN010:return n%3===0;case r.Patterns.PATTERN011:return(i+n)%3===0;case r.Patterns.PATTERN100:return(Math.floor(i/2)+Math.floor(n/3))%2===0;case r.Patterns.PATTERN101:return i*n%2+i*n%3===0;case r.Patterns.PATTERN110:return(i*n%2+i*n%3)%2===0;case r.Patterns.PATTERN111:return(i*n%3+(i+n)%2)%2===0;default:throw new Error("bad maskPattern:"+o)}}r.applyMask=function(i,n){const c=n.size;for(let d=0;d<c;d++)for(let l=0;l<c;l++)n.isReserved(l,d)||n.xor(l,d,s(i,l,d))},r.getBestMask=function(i,n){const c=Object.keys(r.Patterns).length;let d=0,l=1/0;for(let m=0;m<c;m++){n(m),r.applyMask(m,i);const f=r.getPenaltyN1(i)+r.getPenaltyN2(i)+r.getPenaltyN3(i)+r.getPenaltyN4(i);r.applyMask(m,i),f<l&&(l=f,d=m)}return d}})(rt);var er={};const me=Xe,We=[1,1,1,1,1,1,1,1,1,1,2,2,1,2,2,4,1,2,4,4,2,4,4,4,2,4,6,5,2,4,6,6,2,5,8,8,4,5,8,8,4,5,8,11,4,8,10,11,4,9,12,16,4,9,16,16,6,10,12,18,6,10,17,16,6,11,16,19,6,13,18,21,7,14,21,25,8,16,20,25,8,17,23,25,9,17,23,34,9,18,25,30,10,20,27,32,12,21,29,35,12,23,34,37,12,25,34,40,13,26,35,42,14,28,38,45,15,29,40,48,16,31,43,51,17,33,45,54,18,35,48,57,19,37,51,60,19,38,53,63,20,40,56,66,21,43,59,70,22,45,62,74,24,47,65,77,25,49,68,81],Ge=[7,10,13,17,10,16,22,28,15,26,36,44,20,36,52,64,26,48,72,88,36,64,96,112,40,72,108,130,48,88,132,156,60,110,160,192,72,130,192,224,80,150,224,264,96,176,260,308,104,198,288,352,120,216,320,384,132,240,360,432,144,280,408,480,168,308,448,532,180,338,504,588,196,364,546,650,224,416,600,700,224,442,644,750,252,476,690,816,270,504,750,900,300,560,810,960,312,588,870,1050,336,644,952,1110,360,700,1020,1200,390,728,1050,1260,420,784,1140,1350,450,812,1200,1440,480,868,1290,1530,510,924,1350,1620,540,980,1440,1710,570,1036,1530,1800,570,1064,1590,1890,600,1120,1680,1980,630,1204,1770,2100,660,1260,1860,2220,720,1316,1950,2310,750,1372,2040,2430];er.getBlocksCount=function(t,s){switch(s){case me.L:return We[(t-1)*4+0];case me.M:return We[(t-1)*4+1];case me.Q:return We[(t-1)*4+2];case me.H:return We[(t-1)*4+3];default:return}};er.getTotalCodewordsCount=function(t,s){switch(s){case me.L:return Ge[(t-1)*4+0];case me.M:return Ge[(t-1)*4+1];case me.Q:return Ge[(t-1)*4+2];case me.H:return Ge[(t-1)*4+3];default:return}};var tt={},rr={};const Ee=new Uint8Array(512),Ve=new Uint8Array(256);(function(){let t=1;for(let s=0;s<255;s++)Ee[s]=t,Ve[t]=s,t<<=1,t&256&&(t^=285);for(let s=255;s<512;s++)Ee[s]=Ee[s-255]})();rr.log=function(t){if(t<1)throw new Error("log("+t+")");return Ve[t]};rr.exp=function(t){return Ee[t]};rr.mul=function(t,s){return t===0||s===0?0:Ee[Ve[t]+Ve[s]]};(function(r){const t=rr;r.mul=function(o,i){const n=new Uint8Array(o.length+i.length-1);for(let c=0;c<o.length;c++)for(let d=0;d<i.length;d++)n[c+d]^=t.mul(o[c],i[d]);return n},r.mod=function(o,i){let n=new Uint8Array(o);for(;n.length-i.length>=0;){const c=n[0];for(let l=0;l<i.length;l++)n[l]^=t.mul(i[l],c);let d=0;for(;d<n.length&&n[d]===0;)d++;n=n.slice(d)}return n},r.generateECPolynomial=function(o){let i=new Uint8Array([1]);for(let n=0;n<o;n++)i=r.mul(i,new Uint8Array([1,t.exp(n)]));return i}})(tt);const nt=tt;function wr(r){this.genPoly=void 0,this.degree=r,this.degree&&this.initialize(this.degree)}wr.prototype.initialize=function(t){this.degree=t,this.genPoly=nt.generateECPolynomial(this.degree)};wr.prototype.encode=function(t){if(!this.genPoly)throw new Error("Encoder not initialized");const s=new Uint8Array(t.length+this.degree);s.set(t);const o=nt.mod(s,this.genPoly),i=this.degree-o.length;if(i>0){const n=new Uint8Array(this.degree);return n.set(o,i),n}return o};var an=wr,st={},fe={},Nr={};Nr.isValid=function(t){return!isNaN(t)&&t>=1&&t<=40};var ae={};const ot="[0-9]+",ln="[A-Z $%*+\\-./:]+";let Re="(?:[u3000-u303F]|[u3040-u309F]|[u30A0-u30FF]|[uFF00-uFFEF]|[u4E00-u9FAF]|[u2605-u2606]|[u2190-u2195]|u203B|[u2010u2015u2018u2019u2025u2026u201Cu201Du2225u2260]|[u0391-u0451]|[u00A7u00A8u00B1u00B4u00D7u00F7])+";Re=Re.replace(/u/g,"\\u");const cn="(?:(?![A-Z0-9 $%*+\\-./:]|"+Re+`)(?:.|[\r
]))+`;ae.KANJI=new RegExp(Re,"g");ae.BYTE_KANJI=new RegExp("[^A-Z0-9 $%*+\\-./:]+","g");ae.BYTE=new RegExp(cn,"g");ae.NUMERIC=new RegExp(ot,"g");ae.ALPHANUMERIC=new RegExp(ln,"g");const dn=new RegExp("^"+Re+"$"),pn=new RegExp("^"+ot+"$"),un=new RegExp("^[A-Z0-9 $%*+\\-./:]+$");ae.testKanji=function(t){return dn.test(t)};ae.testNumeric=function(t){return pn.test(t)};ae.testAlphanumeric=function(t){return un.test(t)};(function(r){const t=Nr,s=ae;r.NUMERIC={id:"Numeric",bit:1,ccBits:[10,12,14]},r.ALPHANUMERIC={id:"Alphanumeric",bit:2,ccBits:[9,11,13]},r.BYTE={id:"Byte",bit:4,ccBits:[8,16,16]},r.KANJI={id:"Kanji",bit:8,ccBits:[8,10,12]},r.MIXED={bit:-1},r.getCharCountIndicator=function(n,c){if(!n.ccBits)throw new Error("Invalid mode: "+n);if(!t.isValid(c))throw new Error("Invalid version: "+c);return c>=1&&c<10?n.ccBits[0]:c<27?n.ccBits[1]:n.ccBits[2]},r.getBestModeForData=function(n){return s.testNumeric(n)?r.NUMERIC:s.testAlphanumeric(n)?r.ALPHANUMERIC:s.testKanji(n)?r.KANJI:r.BYTE},r.toString=function(n){if(n&&n.id)return n.id;throw new Error("Invalid mode")},r.isValid=function(n){return n&&n.bit&&n.ccBits};function o(i){if(typeof i!="string")throw new Error("Param is not a string");switch(i.toLowerCase()){case"numeric":return r.NUMERIC;case"alphanumeric":return r.ALPHANUMERIC;case"kanji":return r.KANJI;case"byte":return r.BYTE;default:throw new Error("Unknown mode: "+i)}}r.from=function(n,c){if(r.isValid(n))return n;try{return o(n)}catch{return c}}})(fe);(function(r){const t=re,s=er,o=Xe,i=fe,n=Nr,c=7973,d=t.getBCHDigit(c);function l(h,k,v){for(let y=1;y<=40;y++)if(k<=r.getCapacity(y,v,h))return y}function m(h,k){return i.getCharCountIndicator(h,k)+4}function f(h,k){let v=0;return h.forEach(function(y){const L=m(y.mode,k);v+=L+y.getBitsLength()}),v}function g(h,k){for(let v=1;v<=40;v++)if(f(h,v)<=r.getCapacity(v,k,i.MIXED))return v}r.from=function(k,v){return n.isValid(k)?parseInt(k,10):v},r.getCapacity=function(k,v,y){if(!n.isValid(k))throw new Error("Invalid QR Code version");typeof y>"u"&&(y=i.BYTE);const L=t.getSymbolTotalCodewords(k),S=s.getTotalCodewordsCount(k,v),u=(L-S)*8;if(y===i.MIXED)return u;const x=u-m(y,k);switch(y){case i.NUMERIC:return Math.floor(x/10*3);case i.ALPHANUMERIC:return Math.floor(x/11*2);case i.KANJI:return Math.floor(x/13);case i.BYTE:default:return Math.floor(x/8)}},r.getBestVersionForData=function(k,v){let y;const L=o.from(v,o.M);if(Array.isArray(k)){if(k.length>1)return g(k,L);if(k.length===0)return 1;y=k[0]}else y=k;return l(y.mode,y.getLength(),L)},r.getEncodedBits=function(k){if(!n.isValid(k)||k<7)throw new Error("Invalid QR Code version");let v=k<<12;for(;t.getBCHDigit(v)-d>=0;)v^=c<<t.getBCHDigit(v)-d;return k<<12|v}})(st);var it={};const hr=re,at=1335,_n=21522,Dr=hr.getBCHDigit(at);it.getEncodedBits=function(t,s){const o=t.bit<<3|s;let i=o<<10;for(;hr.getBCHDigit(i)-Dr>=0;)i^=at<<hr.getBCHDigit(i)-Dr;return(o<<10|i)^_n};var lt={};const mn=fe;function xe(r){this.mode=mn.NUMERIC,this.data=r.toString()}xe.getBitsLength=function(t){return 10*Math.floor(t/3)+(t%3?t%3*3+1:0)};xe.prototype.getLength=function(){return this.data.length};xe.prototype.getBitsLength=function(){return xe.getBitsLength(this.data.length)};xe.prototype.write=function(t){let s,o,i;for(s=0;s+3<=this.data.length;s+=3)o=this.data.substr(s,3),i=parseInt(o,10),t.put(i,10);const n=this.data.length-s;n>0&&(o=this.data.substr(s),i=parseInt(o,10),t.put(i,n*3+1))};var hn=xe;const fn=fe,ar=["0","1","2","3","4","5","6","7","8","9","A","B","C","D","E","F","G","H","I","J","K","L","M","N","O","P","Q","R","S","T","U","V","W","X","Y","Z"," ","$","%","*","+","-",".","/",":"];function ve(r){this.mode=fn.ALPHANUMERIC,this.data=r}ve.getBitsLength=function(t){return 11*Math.floor(t/2)+6*(t%2)};ve.prototype.getLength=function(){return this.data.length};ve.prototype.getBitsLength=function(){return ve.getBitsLength(this.data.length)};ve.prototype.write=function(t){let s;for(s=0;s+2<=this.data.length;s+=2){let o=ar.indexOf(this.data[s])*45;o+=ar.indexOf(this.data[s+1]),t.put(o,11)}this.data.length%2&&t.put(ar.indexOf(this.data[s]),6)};var gn=ve;const xn=fe;function ye(r){this.mode=xn.BYTE,typeof r=="string"?this.data=new TextEncoder().encode(r):this.data=new Uint8Array(r)}ye.getBitsLength=function(t){return t*8};ye.prototype.getLength=function(){return this.data.length};ye.prototype.getBitsLength=function(){return ye.getBitsLength(this.data.length)};ye.prototype.write=function(r){for(let t=0,s=this.data.length;t<s;t++)r.put(this.data[t],8)};var vn=ye;const yn=fe,bn=re;function be(r){this.mode=yn.KANJI,this.data=r}be.getBitsLength=function(t){return t*13};be.prototype.getLength=function(){return this.data.length};be.prototype.getBitsLength=function(){return be.getBitsLength(this.data.length)};be.prototype.write=function(r){let t;for(t=0;t<this.data.length;t++){let s=bn.toSJIS(this.data[t]);if(s>=33088&&s<=40956)s-=33088;else if(s>=57408&&s<=60351)s-=49472;else throw new Error("Invalid SJIS character: "+this.data[t]+`
Make sure your charset is UTF-8`);s=(s>>>8&255)*192+(s&255),r.put(s,13)}};var kn=be,ct={exports:{}};(function(r){var t={single_source_shortest_paths:function(s,o,i){var n={},c={};c[o]=0;var d=t.PriorityQueue.make();d.push(o,0);for(var l,m,f,g,h,k,v,y,L;!d.empty();){l=d.pop(),m=l.value,g=l.cost,h=s[m]||{};for(f in h)h.hasOwnProperty(f)&&(k=h[f],v=g+k,y=c[f],L=typeof c[f]>"u",(L||y>v)&&(c[f]=v,d.push(f,v),n[f]=m))}if(typeof i<"u"&&typeof c[i]>"u"){var S=["Could not find a path from ",o," to ",i,"."].join("");throw new Error(S)}return n},extract_shortest_path_from_predecessor_list:function(s,o){for(var i=[],n=o;n;)i.push(n),s[n],n=s[n];return i.reverse(),i},find_path:function(s,o,i){var n=t.single_source_shortest_paths(s,o,i);return t.extract_shortest_path_from_predecessor_list(n,i)},PriorityQueue:{make:function(s){var o=t.PriorityQueue,i={},n;s=s||{};for(n in o)o.hasOwnProperty(n)&&(i[n]=o[n]);return i.queue=[],i.sorter=s.sorter||o.default_sorter,i},default_sorter:function(s,o){return s.cost-o.cost},push:function(s,o){var i={value:s,cost:o};this.queue.push(i),this.queue.sort(this.sorter)},pop:function(){return this.queue.shift()},empty:function(){return this.queue.length===0}}};r.exports=t})(ct);var wn=ct.exports;(function(r){const t=fe,s=hn,o=gn,i=vn,n=kn,c=ae,d=re,l=wn;function m(S){return unescape(encodeURIComponent(S)).length}function f(S,u,x){const N=[];let j;for(;(j=S.exec(x))!==null;)N.push({data:j[0],index:j.index,mode:u,length:j[0].length});return N}function g(S){const u=f(c.NUMERIC,t.NUMERIC,S),x=f(c.ALPHANUMERIC,t.ALPHANUMERIC,S);let N,j;return d.isKanjiModeEnabled()?(N=f(c.BYTE,t.BYTE,S),j=f(c.KANJI,t.KANJI,S)):(N=f(c.BYTE_KANJI,t.BYTE,S),j=[]),u.concat(x,N,j).sort(function(T,B){return T.index-B.index}).map(function(T){return{data:T.data,mode:T.mode,length:T.length}})}function h(S,u){switch(u){case t.NUMERIC:return s.getBitsLength(S);case t.ALPHANUMERIC:return o.getBitsLength(S);case t.KANJI:return n.getBitsLength(S);case t.BYTE:return i.getBitsLength(S)}}function k(S){return S.reduce(function(u,x){const N=u.length-1>=0?u[u.length-1]:null;return N&&N.mode===x.mode?(u[u.length-1].data+=x.data,u):(u.push(x),u)},[])}function v(S){const u=[];for(let x=0;x<S.length;x++){const N=S[x];switch(N.mode){case t.NUMERIC:u.push([N,{data:N.data,mode:t.ALPHANUMERIC,length:N.length},{data:N.data,mode:t.BYTE,length:N.length}]);break;case t.ALPHANUMERIC:u.push([N,{data:N.data,mode:t.BYTE,length:N.length}]);break;case t.KANJI:u.push([N,{data:N.data,mode:t.BYTE,length:m(N.data)}]);break;case t.BYTE:u.push([{data:N.data,mode:t.BYTE,length:m(N.data)}])}}return u}function y(S,u){const x={},N={start:{}};let j=["start"];for(let R=0;R<S.length;R++){const T=S[R],B=[];for(let K=0;K<T.length;K++){const J=T[K],U=""+R+K;B.push(U),x[U]={node:J,lastCount:0},N[U]={};for(let p=0;p<j.length;p++){const _=j[p];x[_]&&x[_].node.mode===J.mode?(N[_][U]=h(x[_].lastCount+J.length,J.mode)-h(x[_].lastCount,J.mode),x[_].lastCount+=J.length):(x[_]&&(x[_].lastCount=J.length),N[_][U]=h(J.length,J.mode)+4+t.getCharCountIndicator(J.mode,u))}}j=B}for(let R=0;R<j.length;R++)N[j[R]].end=0;return{map:N,table:x}}function L(S,u){let x;const N=t.getBestModeForData(S);if(x=t.from(u,N),x!==t.BYTE&&x.bit<N.bit)throw new Error('"'+S+'" cannot be encoded with mode '+t.toString(x)+`.
 Suggested mode is: `+t.toString(N));switch(x===t.KANJI&&!d.isKanjiModeEnabled()&&(x=t.BYTE),x){case t.NUMERIC:return new s(S);case t.ALPHANUMERIC:return new o(S);case t.KANJI:return new n(S);case t.BYTE:return new i(S)}}r.fromArray=function(u){return u.reduce(function(x,N){return typeof N=="string"?x.push(L(N,null)):N.data&&x.push(L(N.data,N.mode)),x},[])},r.fromString=function(u,x){const N=g(u,d.isKanjiModeEnabled()),j=v(N),R=y(j,x),T=l.find_path(R.map,"start","end"),B=[];for(let K=1;K<T.length-1;K++)B.push(R.table[T[K]].node);return r.fromArray(k(B))},r.rawSplit=function(u){return r.fromArray(g(u,d.isKanjiModeEnabled()))}})(lt);const tr=re,lr=Xe,Nn=nn,Sn=sn,En=Xr,$n=et,fr=rt,gr=er,jn=an,Je=st,Rn=it,Tn=fe,cr=lt;function Cn(r,t){const s=r.size,o=$n.getPositions(t);for(let i=0;i<o.length;i++){const n=o[i][0],c=o[i][1];for(let d=-1;d<=7;d++)if(!(n+d<=-1||s<=n+d))for(let l=-1;l<=7;l++)c+l<=-1||s<=c+l||(d>=0&&d<=6&&(l===0||l===6)||l>=0&&l<=6&&(d===0||d===6)||d>=2&&d<=4&&l>=2&&l<=4?r.set(n+d,c+l,!0,!0):r.set(n+d,c+l,!1,!0))}}function An(r){const t=r.size;for(let s=8;s<t-8;s++){const o=s%2===0;r.set(s,6,o,!0),r.set(6,s,o,!0)}}function Pn(r,t){const s=En.getPositions(t);for(let o=0;o<s.length;o++){const i=s[o][0],n=s[o][1];for(let c=-2;c<=2;c++)for(let d=-2;d<=2;d++)c===-2||c===2||d===-2||d===2||c===0&&d===0?r.set(i+c,n+d,!0,!0):r.set(i+c,n+d,!1,!0)}}function In(r,t){const s=r.size,o=Je.getEncodedBits(t);let i,n,c;for(let d=0;d<18;d++)i=Math.floor(d/3),n=d%3+s-8-3,c=(o>>d&1)===1,r.set(i,n,c,!0),r.set(n,i,c,!0)}function dr(r,t,s){const o=r.size,i=Rn.getEncodedBits(t,s);let n,c;for(n=0;n<15;n++)c=(i>>n&1)===1,n<6?r.set(n,8,c,!0):n<8?r.set(n+1,8,c,!0):r.set(o-15+n,8,c,!0),n<8?r.set(8,o-n-1,c,!0):n<9?r.set(8,15-n-1+1,c,!0):r.set(8,15-n-1,c,!0);r.set(o-8,8,1,!0)}function On(r,t){const s=r.size;let o=-1,i=s-1,n=7,c=0;for(let d=s-1;d>0;d-=2)for(d===6&&d--;;){for(let l=0;l<2;l++)if(!r.isReserved(i,d-l)){let m=!1;c<t.length&&(m=(t[c]>>>n&1)===1),r.set(i,d-l,m),n--,n===-1&&(c++,n=7)}if(i+=o,i<0||s<=i){i-=o,o=-o;break}}}function Fn(r,t,s){const o=new Nn;s.forEach(function(l){o.put(l.mode.bit,4),o.put(l.getLength(),Tn.getCharCountIndicator(l.mode,r)),l.write(o)});const i=tr.getSymbolTotalCodewords(r),n=gr.getTotalCodewordsCount(r,t),c=(i-n)*8;for(o.getLengthInBits()+4<=c&&o.put(0,4);o.getLengthInBits()%8!==0;)o.putBit(0);const d=(c-o.getLengthInBits())/8;for(let l=0;l<d;l++)o.put(l%2?17:236,8);return Dn(o,r,t)}function Dn(r,t,s){const o=tr.getSymbolTotalCodewords(t),i=gr.getTotalCodewordsCount(t,s),n=o-i,c=gr.getBlocksCount(t,s),d=o%c,l=c-d,m=Math.floor(o/c),f=Math.floor(n/c),g=f+1,h=m-f,k=new jn(h);let v=0;const y=new Array(c),L=new Array(c);let S=0;const u=new Uint8Array(r.buffer);for(let T=0;T<c;T++){const B=T<l?f:g;y[T]=u.slice(v,v+B),L[T]=k.encode(y[T]),v+=B,S=Math.max(S,B)}const x=new Uint8Array(o);let N=0,j,R;for(j=0;j<S;j++)for(R=0;R<c;R++)j<y[R].length&&(x[N++]=y[R][j]);for(j=0;j<h;j++)for(R=0;R<c;R++)x[N++]=L[R][j];return x}function Ln(r,t,s,o){let i;if(Array.isArray(r))i=cr.fromArray(r);else if(typeof r=="string"){let m=t;if(!m){const f=cr.rawSplit(r);m=Je.getBestVersionForData(f,s)}i=cr.fromString(r,m||40)}else throw new Error("Invalid data");const n=Je.getBestVersionForData(i,s);if(!n)throw new Error("The amount of data is too big to be stored in a QR Code");if(!t)t=n;else if(t<n)throw new Error(`
The chosen QR Code version cannot contain this amount of data.
Minimum version required to store current data is: `+n+`.
`);const c=Fn(t,s,i),d=tr.getSymbolSize(t),l=new Sn(d);return Cn(l,t),An(l),Pn(l,t),dr(l,s,0),t>=7&&In(l,t),On(l,c),isNaN(o)&&(o=fr.getBestMask(l,dr.bind(null,l,s))),fr.applyMask(o,l),dr(l,s,o),{modules:l,version:t,errorCorrectionLevel:s,maskPattern:o,segments:i}}Zr.create=function(t,s){if(typeof t>"u"||t==="")throw new Error("No input text");let o=lr.M,i,n;return typeof s<"u"&&(o=lr.from(s.errorCorrectionLevel,lr.M),i=Je.from(s.version),n=fr.from(s.maskPattern),s.toSJISFunc&&tr.setToSJISFunction(s.toSJISFunc)),Ln(t,i,o,n)};var dt={},Sr={};(function(r){function t(s){if(typeof s=="number"&&(s=s.toString()),typeof s!="string")throw new Error("Color should be defined as hex string");let o=s.slice().replace("#","").split("");if(o.length<3||o.length===5||o.length>8)throw new Error("Invalid hex color: "+s);(o.length===3||o.length===4)&&(o=Array.prototype.concat.apply([],o.map(function(n){return[n,n]}))),o.length===6&&o.push("F","F");const i=parseInt(o.join(""),16);return{r:i>>24&255,g:i>>16&255,b:i>>8&255,a:i&255,hex:"#"+o.slice(0,6).join("")}}r.getOptions=function(o){o||(o={}),o.color||(o.color={});const i=typeof o.margin>"u"||o.margin===null||o.margin<0?4:o.margin,n=o.width&&o.width>=21?o.width:void 0,c=o.scale||4;return{width:n,scale:n?4:c,margin:i,color:{dark:t(o.color.dark||"#000000ff"),light:t(o.color.light||"#ffffffff")},type:o.type,rendererOpts:o.rendererOpts||{}}},r.getScale=function(o,i){return i.width&&i.width>=o+i.margin*2?i.width/(o+i.margin*2):i.scale},r.getImageWidth=function(o,i){const n=r.getScale(o,i);return Math.floor((o+i.margin*2)*n)},r.qrToImageData=function(o,i,n){const c=i.modules.size,d=i.modules.data,l=r.getScale(c,n),m=Math.floor((c+n.margin*2)*l),f=n.margin*l,g=[n.color.light,n.color.dark];for(let h=0;h<m;h++)for(let k=0;k<m;k++){let v=(h*m+k)*4,y=n.color.light;if(h>=f&&k>=f&&h<m-f&&k<m-f){const L=Math.floor((h-f)/l),S=Math.floor((k-f)/l);y=g[d[L*c+S]?1:0]}o[v++]=y.r,o[v++]=y.g,o[v++]=y.b,o[v]=y.a}}})(Sr);(function(r){const t=Sr;function s(i,n,c){i.clearRect(0,0,n.width,n.height),n.style||(n.style={}),n.height=c,n.width=c,n.style.height=c+"px",n.style.width=c+"px"}function o(){try{return document.createElement("canvas")}catch{throw new Error("You need to specify a canvas element")}}r.render=function(n,c,d){let l=d,m=c;typeof l>"u"&&(!c||!c.getContext)&&(l=c,c=void 0),c||(m=o()),l=t.getOptions(l);const f=t.getImageWidth(n.modules.size,l),g=m.getContext("2d"),h=g.createImageData(f,f);return t.qrToImageData(h.data,n,l),s(g,m,f),g.putImageData(h,0,0),m},r.renderToDataURL=function(n,c,d){let l=d;typeof l>"u"&&(!c||!c.getContext)&&(l=c,c=void 0),l||(l={});const m=r.render(n,c,l),f=l.type||"image/png",g=l.rendererOpts||{};return m.toDataURL(f,g.quality)}})(dt);var pt={};const Un=Sr;function Lr(r,t){const s=r.a/255,o=t+'="'+r.hex+'"';return s<1?o+" "+t+'-opacity="'+s.toFixed(2).slice(1)+'"':o}function pr(r,t,s){let o=r+t;return typeof s<"u"&&(o+=" "+s),o}function Mn(r,t,s){let o="",i=0,n=!1,c=0;for(let d=0;d<r.length;d++){const l=Math.floor(d%t),m=Math.floor(d/t);!l&&!n&&(n=!0),r[d]?(c++,d>0&&l>0&&r[d-1]||(o+=n?pr("M",l+s,.5+m+s):pr("m",i,0),i=0,n=!1),l+1<t&&r[d+1]||(o+=pr("h",c),c=0)):i++}return o}pt.render=function(t,s,o){const i=Un.getOptions(s),n=t.modules.size,c=t.modules.data,d=n+i.margin*2,l=i.color.light.a?"<path "+Lr(i.color.light,"fill")+' d="M0 0h'+d+"v"+d+'H0z"/>':"",m="<path "+Lr(i.color.dark,"stroke")+' d="'+Mn(c,n,i.margin)+'"/>',f='viewBox="0 0 '+d+" "+d+'"',h='<svg xmlns="http://www.w3.org/2000/svg" '+(i.width?'width="'+i.width+'" height="'+i.width+'" ':"")+f+' shape-rendering="crispEdges">'+l+m+`</svg>
`;return typeof o=="function"&&o(null,h),h};const Bn=rn,xr=Zr,ut=dt,Wn=pt;function Er(r,t,s,o,i){const n=[].slice.call(arguments,1),c=n.length,d=typeof n[c-1]=="function";if(!d&&!Bn())throw new Error("Callback required as last argument");if(d){if(c<2)throw new Error("Too few arguments provided");c===2?(i=s,s=t,t=o=void 0):c===3&&(t.getContext&&typeof i>"u"?(i=o,o=void 0):(i=o,o=s,s=t,t=void 0))}else{if(c<1)throw new Error("Too few arguments provided");return c===1?(s=t,t=o=void 0):c===2&&!t.getContext&&(o=s,s=t,t=void 0),new Promise(function(l,m){try{const f=xr.create(s,o);l(r(f,t,o))}catch(f){m(f)}})}try{const l=xr.create(s,o);i(null,r(l,t,o))}catch(l){i(l)}}Ae.create=xr.create;Ae.toCanvas=Er.bind(null,ut.render);Ae.toDataURL=Er.bind(null,ut.renderToDataURL);Ae.toString=Er.bind(null,function(r,t,s){return Wn.render(r,s)});async function Ur(r){const{data:t,error:s}=await C.from("desktop_devices").select("id, kind, status, device_name, enrolled_at").eq("id",r).maybeSingle();if(s)throw new Error(`Phone device evidence could not be verified: ${s.message}`);if(!t)return{ready:!1,reason:"Phone device receipt is not available yet."};if(t.kind!=="mobile_approver"||t.status!=="active")return{ready:!1,reason:"Phone enrollment is not active yet."};const{data:o,error:i}=await C.from("mobile_push_subscriptions").select("id, device_id, last_seen_at, last_error, revoked_at").eq("device_id",r).is("revoked_at",null).order("last_seen_at",{ascending:!1}).limit(1).maybeSingle();if(i)throw new Error(`Phone push evidence could not be verified: ${i.message}`);return o?o.device_id!==r||o.revoked_at||o.last_error?{ready:!1,reason:o.last_error?`Phone push receipt reports an error: ${o.last_error}`:"Phone push receipt did not match the active device."}:{ready:!0,phone:{device_name:t.device_name??"Phone",enrolled_at:t.enrolled_at??null,push_last_seen_at:o.last_seen_at??null}}:{ready:!1,reason:"Phone device is active, but an active push subscription is not verified yet."}}function Gn({onEnrolled:r}){const{toast:t}=Ce(),[s,o]=w.useState("My phone"),[i,n]=w.useState(!1),[c,d]=w.useState(!1),[l,m]=w.useState(null),[f,g]=w.useState(null),[h,k]=w.useState(null),[v,y]=w.useState(null),[L,S]=w.useState(null),[u,x]=w.useState(null),[N,j]=w.useState(null),R=U=>{j(U),m(null),g(null),k(null),y(null),t({title:"Phone approver verified ✅",description:`${U.device_name} has an active device and push receipt.`}),r==null||r()},T=async()=>{var U;n(!0),y(null),k(null);try{const{data:p,error:_}=await C.functions.invoke("desktop-enroll-start",{body:{device_name:s.trim()||"My phone",kind:"mobile_approver"}});if(_)throw _;const $=p;if(!($!=null&&$.ok)||!((U=$.device)!=null&&U.id))throw new Error(($==null?void 0:$.error)||"Phone enrollment returned no durable device receipt.");const I=$.device;if(g(I.id),$.already_enrolled){const M=await Ur(I.id);if(M.ready&&M.phone){R(M.phone);return}j(null),k(M.reason??"Existing phone found; waiting for verification."),t({title:"Existing phone found",description:"Verifying its active push receipt before marking it ready."});return}if(!I.enrollment_code||!I.enrollment_code_expires_at)throw new Error("Enrollment response did not include a verified QR/code receipt.");j(null),m({id:I.id,enrollment_code:I.enrollment_code,enrollment_code_expires_at:I.enrollment_code_expires_at}),$.reused_pending&&t({title:"Using existing phone QR",description:"A valid pending phone enrollment receipt was re-used."})}catch(p){const _=String((p==null?void 0:p.message)??p);y(_),t({title:"Couldn't create phone code",description:_,variant:"destructive"})}finally{n(!1)}},B=async()=>{var U;if(confirm("Revoke your existing phone enrollments and push subscriptions, then generate a fresh QR?")){d(!0),y(null),k(null);try{const{data:p,error:_}=await C.auth.getUser();if(_)throw new Error(`Could not verify signed-in owner: ${_.message}`);const $=(U=p.user)==null?void 0:U.id;if(!$)throw new Error("Not signed in");const I=new Date().toISOString(),{error:M}=await C.from("mobile_push_subscriptions").update({revoked_at:I}).eq("user_id",$).is("revoked_at",null);if(M)throw M;const{error:Z}=await C.from("desktop_devices").update({status:"revoked",revoked_at:I}).eq("user_id",$).eq("kind","mobile_approver").neq("status","revoked");if(Z)throw Z;const[ne,Y]=await Promise.all([C.from("mobile_push_subscriptions").select("id",{count:"exact",head:!0}).eq("user_id",$).is("revoked_at",null),C.from("desktop_devices").select("id",{count:"exact",head:!0}).eq("user_id",$).eq("kind","mobile_approver").neq("status","revoked")]);if(ne.error)throw new Error(`Push revocation could not be re-verified: ${ne.error.message}`);if(Y.error)throw new Error(`Device revocation could not be re-verified: ${Y.error.message}`);if((ne.count??0)!==0||(Y.count??0)!==0)throw new Error("Phone reset could not be re-verified; an active device or push receipt remains.");t({title:"Phone reset verified",description:"Old device and push receipts are revoked. Generating a fresh QR…"}),m(null),j(null),g(null),await T()}catch(p){const _=String((p==null?void 0:p.message)??p);y(_),t({title:"Reset failed",description:_,variant:"destructive"})}finally{d(!1)}}};w.useEffect(()=>{if(!l){S(null),x(null);return}const U=`${window.location.origin}/mobile-enroll?code=${l.enrollment_code}`;x(null),Ae.toDataURL(U,{width:220,margin:1}).then(p=>{S(p),x(null)}).catch(p=>{S(null),x(String((p==null?void 0:p.message)??"QR generation failed. Use the link or code instead."))})},[l]),w.useEffect(()=>{if(!f)return;let U=!1;const p=async()=>{try{const $=await Ur(f);if(U)return;y(null),$.ready&&$.phone?R($.phone):k($.reason??"Phone enrollment is still being verified.")}catch($){if(U)return;y(String(($==null?void 0:$.message)??$))}},_=setInterval(p,3e3);return p(),()=>{U=!0,clearInterval(_)}},[f]);const K=async(U,p)=>{try{return await navigator.clipboard.writeText(U),t({title:`${p} copied`}),!0}catch{return t({title:"Copy failed",description:"Copy manually instead.",variant:"destructive"}),!1}},J=l?`${window.location.origin}/mobile-enroll?code=${l.enrollment_code}`:null;return e.jsxs(W,{className:"p-4 space-y-3",children:[e.jsxs("div",{className:"flex items-center gap-2 text-sm font-medium",children:[e.jsx(Jr,{className:"h-4 w-4"})," Enroll a phone (approver)"]}),e.jsx("p",{className:"text-xs text-muted-foreground",children:"Turn your phone into a remote approver. The platform marks it ready only after both the mobile-approver device and an active push subscription are re-verified. No app install — your phone's browser handles it."}),(v||h)&&!N&&e.jsx("div",{className:"rounded border border-amber-500/40 bg-amber-500/5 p-3 text-xs",children:e.jsxs("div",{className:"flex items-start gap-2",children:[e.jsx(ie,{className:"h-4 w-4 mt-0.5 text-amber-600 shrink-0"}),e.jsxs("div",{children:[e.jsx("div",{className:"font-medium",children:"Phone readiness not verified yet"}),e.jsx("div",{className:"text-muted-foreground mt-1",children:v??h})]})]})}),N&&e.jsxs("div",{className:"rounded border border-green-500/40 bg-green-500/10 p-3 text-sm",children:["✅ ",e.jsx("strong",{children:N.device_name})," has a verified mobile-approver device and active push receipt",N.enrolled_at?e.jsxs(e.Fragment,{children:[" from ",new Date(N.enrolled_at).toLocaleString()]}):null,".",e.jsxs("div",{className:"mt-1 text-xs text-muted-foreground",children:["Push subscription verified",N.push_last_seen_at?`; last seen ${new Date(N.push_last_seen_at).toLocaleString()}`:"","."]})]}),!l&&!N&&e.jsxs("div",{className:"space-y-2",children:[e.jsxs("div",{className:"flex flex-col sm:flex-row gap-2",children:[e.jsx(te,{value:s,onChange:U=>o(U.target.value),placeholder:"My iPhone"}),e.jsx(E,{onClick:T,disabled:i||c,children:i?"Creating…":f?"Recheck / generate QR":"Generate phone QR"})]}),e.jsxs(E,{variant:"outline",size:"sm",className:"w-full",onClick:B,disabled:i||c,children:[e.jsx(oe,{className:`h-3 w-3 mr-2 ${c?"animate-spin":""}`}),c?"Resetting…":"Reset & re-enroll phone (revoke old push + device)"]}),e.jsx("p",{className:"text-xs text-muted-foreground",children:"Use this if push stopped arriving, you switched phones, or you re-installed the Home Screen app."})]}),l&&e.jsxs("div",{className:"grid sm:grid-cols-[220px_1fr] gap-4 items-start",children:[e.jsx("div",{className:"flex justify-center",children:L?e.jsx("img",{src:L,alt:"Scan to enroll phone",className:"rounded border",width:220,height:220}):u?e.jsx("div",{className:"w-[220px] min-h-[140px] grid place-items-center text-xs text-destructive border rounded p-4 text-center",children:"QR unavailable. Use the enrollment link or code."}):e.jsx("div",{className:"w-[220px] h-[220px] grid place-items-center text-xs text-muted-foreground border rounded",children:"Generating QR…"})}),e.jsxs("div",{className:"space-y-2 text-sm",children:[u&&e.jsxs("p",{className:"text-xs text-destructive",children:["QR error: ",u]}),e.jsxs("div",{children:[e.jsx("div",{className:"text-xs text-muted-foreground",children:"Scan with your phone's camera, or open this link on the phone:"}),e.jsxs("div",{className:"mt-1 flex items-center gap-2",children:[e.jsx("code",{className:"text-xs bg-muted rounded px-2 py-1 truncate flex-1",children:J}),e.jsx(E,{size:"sm",variant:"outline",onClick:()=>J&&void K(J,"Link"),children:e.jsx(he,{className:"h-3 w-3"})})]})]}),e.jsxs("div",{children:[e.jsx("div",{className:"text-xs text-muted-foreground",children:"Or type this code manually:"}),e.jsxs("div",{className:"mt-1 flex items-center gap-2",children:[e.jsx("code",{className:"font-mono tracking-widest text-lg bg-background border rounded px-2 py-1",children:l.enrollment_code}),e.jsx(E,{size:"sm",variant:"outline",onClick:()=>void K(l.enrollment_code,"Code"),children:e.jsx(he,{className:"h-3 w-3"})})]})]}),e.jsxs(E,{className:"w-full",onClick:async()=>{!l||!await K(l.enrollment_code,"Code")||window.open("/mobile-enroll","_blank","noopener")},children:[e.jsx(_e,{className:"h-4 w-4 mr-2"}),"Copy code & open enroll page"]}),e.jsxs("p",{className:"text-xs text-muted-foreground",children:["Expires ",new Date(l.enrollment_code_expires_at).toLocaleTimeString(),". iPhone users: add the site to your Home Screen first (Safari → Share → Add to Home Screen), then open this link from the new icon — Safari only delivers push notifications to home-screen apps."]}),e.jsxs(E,{size:"sm",variant:"ghost",onClick:()=>{m(null),g(null),k(null)},children:[e.jsx(oe,{className:"h-3 w-3 mr-1"})," New code"]})]})]})]})}const qn='# Unk Desktop Companion (Phase 3)\r\n\r\nSingle-file Python companion that runs on your Windows PC, pairs with the JFLI\r\nplatform via a one-time enrollment code, and executes **only** approved\r\ndesktop actions filed through the Change Gate.\r\n\r\n## Install\r\n\r\n```powershell\r\npython -m pip install requests pillow keyring playwright\r\npython -m playwright install chromium\r\n```\r\n\r\n`pillow` is only needed for `capture_screenshot`. `playwright` is required for\r\nbrowser-based Facebook Page publishing. `keyring` stores credentials\r\nin Windows Credential Manager instead of a 0600 file under\r\n`%USERPROFILE%\\.unk-companion\\`.\r\n\r\n## First run (enrollment)\r\n\r\n1. On the platform: open **/grant-engine/desktop-command** → *Generate\r\n   enrollment code*. Code is valid 15 minutes, one use.\r\n2. On the PC:\r\n\r\n   ```powershell\r\n   python .\\unk_companion.py\r\n   ```\r\n\r\n   Paste the 8-character code when prompted.\r\n\r\nIf the window closes after you press Enter, run it from an already-open\r\nPowerShell window instead:\r\n\r\n```powershell\r\ncd $env:USERPROFILE\\Downloads\r\npython .\\unk_companion.py --enroll\r\n```\r\n\r\nThe companion also writes the exact error to\r\n`%USERPROFILE%\\.unk-companion\\companion.log` and now pauses before closing on\r\nstartup/enrollment errors.\r\n\r\nIf Facebook publishing reports `playwright_not_installed`, run `setup_unk.ps1`\r\nagain or use **Update & Restart** from Desktop Command. Newer builds also try a\r\nlocal Playwright/Chromium repair before failing a publish job.\r\n\r\n## Normal run\r\n\r\n```powershell\r\npython .\\unk_companion.py            # heartbeat loop, polls every 15s\r\npython .\\unk_companion.py --status   # one-shot heartbeat, print JSON, exit\r\npython .\\unk_companion.py --enroll   # force re-enrollment\r\n```\r\n\r\n## Permission profile (edit at top of `unk_companion.py`)\r\n\r\n| Knob | Default |\r\n| --- | --- |\r\n| `ALLOWED_ROOTS` | `~/Documents/JFLI`, `~/Documents/Bot-Fresh`, `~/Documents/Grants`, `~/Documents/BAMA`, `~/Downloads/Unk`, `~/.unk-companion` |\r\n| `ALLOWED_EXECUTABLES` | `python`, `python.exe`, `pythonw.exe`, `Bot-Fresh.py`, `notepad.exe` |\r\n| `URL_ALLOWLIST` | TradingView, Coinbase, Google Drive/Docs/Calendar/Mail/Meet, BAMA, JFLI, Facebook/Meta Page publishing surfaces, Grants.gov, Submittable, Instrumentl, Kauffman, MO Humanities, lovable.app/dev |\r\n| `URL_HARD_BLOCKLIST_SUBSTRINGS` | IRS, EFTPS, SAM.gov, major banks (Chase/WF/BofA/USBank), brokerages (Fidelity/Schwab/Vanguard/E\\*Trade/Robinhood/TD/IB), payroll (Gusto/ADP/Paychex), QuickBooks Online, Stripe dashboard |\r\n| `OPEN_FILE_DENY_EXT` | `.exe .bat .cmd .com .scr .pif .msi .msp .ps1 .psm1 .vbs .vbe .js .wsf .jar .reg .lnk` |\r\n| `POLL_SECONDS` | 15 |\r\n\r\nAnything outside these is refused at the companion, regardless of what the\r\nserver sent. Hard-block wins over allow-list.\r\n\r\n## Supported capabilities\r\n\r\n### Tier 1 — read + narrow write\r\n| capability | payload | risk |\r\n| --- | --- | --- |\r\n| `capture_screenshot` | — | low |\r\n| `read_file` | `{path, max_bytes?}` | low |\r\n| `write_file` | `{path, content}` | medium |\r\n| `launch_process` | `{executable, args[], cwd?}` | medium |\r\n| `run_check` | `{executable, args[]}` | low |\r\n\r\n### Tier 2 — open and show\r\n| capability | payload | risk |\r\n| --- | --- | --- |\r\n| `open_url` | `{url}` (must match `URL_ALLOWLIST`, never `URL_HARD_BLOCKLIST_SUBSTRINGS`) | low |\r\n| `connector_escort` | `{provider?, account_email?, url?, checklist?}` opens Lovable and copies the connector checklist; OAuth consent stays human-only | low |\r\n| `open_file` | `{path}` (path allow-list + extension deny-list) | low |\r\n| `reveal_in_explorer` | `{path}` | low |\r\n| `read_clipboard` | — | low |\r\n| `write_clipboard` | `{text}` (≤ 8000 chars) | low |\r\n\r\n### Tier 3 — paperwork (medium risk, approval required for write ops)\r\n| capability | payload | risk |\r\n| --- | --- | --- |\r\n| `append_to_file` | `{path, content}` append-only, ≤ 1 MB per call | medium |\r\n| `download_url_to_folder` | `{url, folder?, filename?}` ≤ 25 MB | medium |\r\n\r\n### Tier 3 — Meta / Facebook publishing\r\n| capability | payload | risk |\r\n| --- | --- | --- |\r\n| `browser_publish_facebook` | `{job_id, page_slug, message, image_url?, video_url?}` | medium |\r\n\r\n### Tier 3 — cloud (runs server-side, no companion needed)\r\nThese do **not** run inside the companion. They dispatch through\r\n`supabase/functions/cloud-action-dispatch/index.ts` and the platform\'s\r\nconnected Google / Microsoft connector accounts.\r\n\r\n| capability | payload | risk |\r\n| --- | --- | --- |\r\n| `calendar_create_event` | `{summary, start, end, description?, location?, attendees?, calendar_id?}` | medium |\r\n| `email_draft` | `{provider: "google"\\|"outlook", to, subject, body, cc?, bcc?}` | medium |\r\n\r\n### Tier 4 / Tier 5 — not implemented\r\nSend-for-real email, form submission, file delete/move, anything banking /\r\nbrokerage / IRS / payroll. Human-only by design.\r\n\r\nUnknown capabilities return `{ok:false, error:"unsupported_capability"}` — they\r\nnever execute.\r\n\r\n## Run as a self-healing background service\r\n\r\nRun `setup_unk.ps1` once from the extracted folder. It installs:\r\n\r\n- `UnkSupervisor` — the local watchdog that owns `unk_companion.py`.\r\n- `UnkSupervisorKeepAlive` — a second scheduled task that runs every 5 minutes and restarts/recreates `UnkSupervisor` if Windows stops it or its liveness marker goes stale.\r\n- A Startup-folder fallback that runs the same keepalive script after sign-in.\r\n- If you use **Run installer as admin**, `UnkSupervisorBootKeepAlive` is also added at Windows startup to repair/start the supervisor as early as Windows allows.\r\n\r\nDo **not** point Task Scheduler directly at `unk_companion.py`; the supervisor must be the single owner. Logs go to `%USERPROFILE%\\.unk-companion\\supervisor.log`, `companion.log`, and `keepalive.log`.\r\n\r\n## Infrastructure Recovery (Ground Zero doctrine)\r\n\r\nThe platform now recognizes four *classes* of failure. Each has its own recovery path:\r\n\r\n| Class     | Recovery path                                                                                     |\r\n| --------- | ------------------------------------------------------------------------------------------------- |\r\n| Software  | Supervisor restarts the process (`unk_supervisor.py`, backoff ladder).                            |\r\n| Browser   | Companion repairs Playwright/Chromium in place before failing a publish job.                      |\r\n| Power     | BIOS auto-power-on + supervisor auto-launch. Logged as `power_return` in `infrastructure_events`. |\r\n| Internet  | Companion keeps retrying; nothing to restart locally. Logged when connectivity returns.           |\r\n\r\nTo make **power recovery** work on Ground Zero (no human required):\r\n\r\n1. **BIOS / UEFI** → look for a setting named\r\n   *"Restore on AC Power Loss"*, *"AC Power Recovery"*, or\r\n   *"After Power Failure"* → set it to **Power On**.\r\n2. **Windows autostart** — `install_supervisor.ps1` registers the supervisor,\r\n   the keepalive task, the Startup fallback, and—when run as admin—the boot\r\n   keepalive task. The supervisor then launches `unk_companion.py`, which\r\n   unlocks the browser profile and resumes the autonomous sweep.\r\n3. On next boot the supervisor detects a short system uptime combined with a\r\n   stale liveness marker and posts a `power_return` event. The platform stores\r\n   it as a `power` failure class in `infrastructure_events` and shows it on\r\n   **/grant-engine/desktop-heartbeat**.\r\n\r\n**Strongly recommended:** a small UPS (battery backup) on the PC + router.\r\nEven a modest unit rides through storm blinks, prevents corrupted browser\r\nprofiles, and gives Windows time to shut down cleanly during longer outages.\r\n',Hn=`"""\r
Unk Desktop Companion (Phase 3)\r
================================\r
Single-file Windows companion that pairs with the JFLI platform and executes\r
APPROVED desktop actions inside a strict permission profile.\r
\r
Lifecycle:\r
  1. First run with no stored credentials  -> prompts for enrollment code\r
     (generated from /grant-engine/desktop-command) and POSTs\r
     action=enroll_complete to the desktop-companion edge function.\r
  2. Receives a one-time device_key, stores it in Windows Credential Manager\r
     (falls back to a 0600 file on non-Windows).\r
  3. Loops forever: every POLL_SECONDS sends action=heartbeat with a status\r
     snapshot and receives pending_actions (already approved server-side).\r
    4. Executes each action through a whitelisted handler. NO arbitrary shell.\r
      NO action without a server-approved request row. Admin elevation is only\r
      allowed for pre-shipped maintenance scripts under the install directory.\r
\r
Hard rules baked in (mirror the platform Change Gate):\r
  - Runs as the logged-in user, never SYSTEM / never elevated.\r
  - Only capabilities in CAPABILITY_HANDLERS are executable; everything else\r
    is reported back as 'unsupported_capability'.\r
  - File ops are confined to ALLOWED_ROOTS. Path traversal is rejected.\r
  - Process launches are confined to ALLOWED_EXECUTABLES (basename match).\r
  - URLs (open_url, download_url_to_folder) must match URL_ALLOWLIST and\r
    must NOT match URL_HARD_BLOCKLIST (banking / brokerage / IRS / payroll).\r
  - open_file rejects executable / script file types regardless of folder.\r
  - append_to_file is append-only, never overwrite/delete.\r
  - Results (stdout tail, exit code, screenshot path) are posted back via\r
    action=action_result so the Post-Test Review loop has evidence.\r
\r
Usage:\r
    python unk_companion.py            # normal run\r
    python unk_companion.py --enroll   # force re-enrollment\r
    python unk_companion.py --status   # one-shot heartbeat, print result, exit\r
\r
Dependencies (stdlib only by default):\r
    pip install requests pillow    # pillow only needed for screenshots\r
"""\r
\r
from __future__ import annotations\r
\r
import argparse\r
import hashlib\r
import json\r
import os\r
import platform\r
import re\r
import socket\r
import subprocess\r
import sys\r
import tempfile\r
import threading\r
import time\r
import traceback\r
import urllib.parse\r
import uuid\r
\r
# Stable per-process identity (generated once at import). Used by the\r
# persistence-repair-runner await_respawn phase to prove restart via a\r
# strictly-changed instance_id + boot_ts pair instead of a fuzzy pid+ts guess.\r
INSTANCE_ID = uuid.uuid4().hex\r
BOOT_TS = time.time()\r
COMPANION_VERSION = "phase71-device-vault-bridge"\r
from dataclasses import dataclass\r
from datetime import datetime, timezone\r
from pathlib import Path\r
from typing import Any, Callable\r
# --- Unk window policy: never flash a console window, never steal focus ---\r
try:\r
    from unk_window_policy import install_quiet_subprocess as _install_quiet_subprocess, browser_args as _win_browser_args\r
    _install_quiet_subprocess()\r
except Exception:  # policy module missing -> behave as before\r
    def _win_browser_args(base=None, **_kw):\r
        return list(base or [])\r
\r
\r
try:\r
    import requests\r
except Exception:\r
    print("Missing Python dependency: requests")\r
    print("Run this first, then start the companion again:")\r
    print("  python -m pip install requests pillow keyring")\r
    try:\r
        input("\\nPress Enter to close...")\r
    except Exception:\r
        pass\r
    raise SystemExit(1)\r
\r
# ---------------------------------------------------------------------------\r
# Configuration\r
# ---------------------------------------------------------------------------\r
\r
SUPABASE_PROJECT_REF = "kwbegsybeyyxfmavjswv"\r
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY", "").strip()\r
FUNCTIONS_BASE = f"https://{SUPABASE_PROJECT_REF}.supabase.co/functions/v1"\r
COMPANION_URL = f"{FUNCTIONS_BASE}/desktop-companion"\r
\r
POLL_SECONDS = 15\r
HTTP_TIMEOUT = 30\r
\r
HOME = Path.home()\r
COMPANION_DIR = HOME / ".unk-companion"\r
COMPANION_DIR.mkdir(exist_ok=True)\r
CRED_FILE = COMPANION_DIR / "device.json"\r
LOG_FILE = COMPANION_DIR / "companion.log"\r
SCREENSHOT_DIR = COMPANION_DIR / "screenshots"\r
SCREENSHOT_DIR.mkdir(exist_ok=True)\r
DOWNLOAD_DIR = HOME / "Downloads" / "Unk"\r
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)\r
RUNNING_BUILD_FILE = COMPANION_DIR / "running_build.json"\r
BACKGROUND_WORKER_REGISTRY_FILE = COMPANION_DIR / "background_workers.json"\r
\r
# Permission profile -- edit these to widen/narrow what Unk can touch.\r
# The companion's own install directory is included so read-only self-diagnosis\r
# (worker logs, supervisor log) is possible without a human opening the machine.\r
# Without it, "is the mirror worker actually running?" is unanswerable remotely.\r
ALLOWED_ROOTS = [\r
    HOME / "Documents" / "JFLI",\r
    HOME / "Documents" / "Bot-Fresh",\r
    HOME / "Documents" / "Grants",\r
    HOME / "Documents" / "BAMA",\r
    DOWNLOAD_DIR,\r
    COMPANION_DIR,\r
    Path(__file__).resolve().parent,\r
]\r
\r
ALLOWED_EXECUTABLES = {\r
    "python.exe", "python", "pythonw.exe",\r
    "Bot-Fresh.py",       # launched via python\r
    "notepad.exe",\r
}\r
\r
# --- Canonical trading-bot runtime -----------------------------------------\r
# The Coinbase Advanced bot runtime lives at the user-profile root and MUST\r
# keep the name Bot-Fresh.py. HOME itself is deliberately NOT an allowed root\r
# (far too broad); only this exact file, and its directory used as a working\r
# directory, are reachable. Nothing here touches strategy, thresholds,\r
# credentials, or the live-trading gate -- launch + read-only probe only.\r
BOT_FRESH_PATH = HOME / "Bot-Fresh.py"\r
BOT_FRESH_DIR = BOT_FRESH_PATH.parent\r
BOT_FRESH_LOG = BOT_FRESH_DIR / "bot-fresh.out.log"\r
ALLOWED_EXACT_FILES = {BOT_FRESH_PATH, BOT_FRESH_LOG}\r
ALLOWED_EXACT_CWDS = {BOT_FRESH_DIR}\r
\r
# Tier-2 URL allow-list. Anything outside is refused at the companion.\r
URL_ALLOWLIST = {\r
    # Trading + market data\r
    "tradingview.com", "www.tradingview.com",\r
    "coinbase.com", "www.coinbase.com", "pro.coinbase.com",\r
    # JFLI / BAMA infrastructure\r
    "drive.google.com", "docs.google.com", "calendar.google.com",\r
    # Google Cloud console — service-account provisioning only. No billing,\r
    # no payment surfaces; Unk stops at any human-only gate.\r
    "console.cloud.google.com",\r
    "mail.google.com", "meet.google.com",\r
    "blackarchives.org", "www.blackarchives.org",\r
    "jfortitude.com", "www.jfortitude.com",\r
    "jfortitudelegacyinstitute.org", "www.jfortitudelegacyinstitute.org",\r
    # Meta/Facebook browser-assisted Page publishing. Personal profiles remain\r
    # human-only; Unk only opens authorized Page surfaces and never touches\r
    # passwords, 2FA, payments, banking, or identity checks.\r
    "facebook.com", "www.facebook.com", "business.facebook.com",\r
    "meta.com", "www.meta.com", "developers.facebook.com",\r
    # Funder / grant portals\r
    "grants.gov", "www.grants.gov",\r
    "ojp.gov", "www.ojp.gov", "bja.ojp.gov",\r
    "epa.gov", "www.epa.gov",\r
    "ded.mo.gov", "www.ded.mo.gov",\r
    "instrumentl.com", "www.instrumentl.com",\r
    "submittable.com", "www.submittable.com",\r
    "kauffman.org", "www.kauffman.org",\r
    "humanitiescouncil.org", "www.humanitiescouncil.org",\r
    "mohumanities.org", "www.mohumanities.org",\r
    # Lovable platform (so Unk can open his own dashboards)\r
    "lovable.app", "lovable.dev",\r
    # AI provider dashboards Unk is authorized to drive Jason to for API-key\r
    # creation. Unk NEVER touches the key value itself — Jason still copies from\r
    # OpenAI and pastes into the Lovable secret form. Unk just opens the tabs.\r
    "platform.openai.com",\r
    # LinkedIn profile build-out escort. Unk opens the authorized edit\r
    # surfaces for the approved identity and stages copy on the clipboard.\r
    # He never enters passwords, 2FA codes, or identity checks.\r
    "linkedin.com", "www.linkedin.com",\r
    # ChatGPT connector escort. Unk opens the connector settings surface so the\r
    # JFLI Grant Engine MCP connector can be removed and re-added after the\r
    # OAuth consent route shipped. No passwords, 2FA, or payment surfaces.\r
    "chatgpt.com", "chat.openai.com",\r
}\r
\r
# Browser-compatible public-source headers. These contain no credentials and\r
# let official funder/CDN endpoints serve the same public files shown in a browser.\r
PUBLIC_DOWNLOAD_HEADERS = {\r
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) JFortitude-Unk/phase69",\r
    "Accept": "application/pdf,text/html,application/xhtml+xml,application/octet-stream;q=0.9,*/*;q=0.8",\r
}\r
\r
# Hard block — Unk REFUSES these even if every other check would pass.\r
# Banking, brokerage, IRS, payroll. Human-only, full stop.\r
URL_HARD_BLOCKLIST_SUBSTRINGS = [\r
    "irs.gov", "eftps.gov", "sam.gov",\r
    "chase.com", "wellsfargo.com", "bankofamerica.com", "usbank.com",\r
    "fidelity.com", "schwab.com", "vanguard.com", "etrade.com", "robinhood.com",\r
    "tdameritrade.com", "interactivebrokers.com",\r
    "gusto.com", "adp.com", "paychex.com", "quickbooks.intuit.com",\r
    "stripe.com/login", "dashboard.stripe.com",\r
]\r
\r
# File-type deny-list for open_file (executables / scripts / installers).\r
OPEN_FILE_DENY_EXT = {\r
    ".exe", ".bat", ".cmd", ".com", ".scr", ".pif",\r
    ".msi", ".msp", ".ps1", ".psm1", ".vbs", ".vbe", ".js", ".wsf",\r
    ".jar", ".reg", ".lnk",\r
}\r
\r
CLIPBOARD_MAX_CHARS = 8_000\r
DOWNLOAD_MAX_BYTES = 25 * 1024 * 1024  # 25 MB cap\r
APPEND_MAX_BYTES = 1 * 1024 * 1024     # 1 MB per append call\r
\r
# ---------------------------------------------------------------------------\r
# Logging\r
# ---------------------------------------------------------------------------\r
\r
def log(msg: str) -> None:\r
    line = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}"\r
    print(line, flush=True)\r
    try:\r
        with LOG_FILE.open("a", encoding="utf-8") as f:\r
            f.write(line + "\\n")\r
    except Exception:\r
        pass\r
\r
def pause_before_exit() -> None:\r
    try:\r
        if sys.stdin and sys.stdin.isatty():\r
            input("\\nPress Enter to close...")\r
    except Exception:\r
        pass\r
\r
def fatal(message: str, code: int = 1) -> None:\r
    log(f"FATAL: {message}")\r
    pause_before_exit()\r
    raise SystemExit(code)\r
\r
# ---------------------------------------------------------------------------\r
# Credential storage (Windows Credential Manager preferred, file fallback)\r
# ---------------------------------------------------------------------------\r
\r
def _try_keyring_save(device_id: str, device_key: str) -> bool:\r
    try:\r
        import keyring  # type: ignore\r
        keyring.set_password("unk-companion", "device_id", device_id)\r
        keyring.set_password("unk-companion", "device_key", device_key)\r
        return True\r
    except Exception:\r
        return False\r
\r
def _try_keyring_load() -> tuple[str, str] | None:\r
    try:\r
        import keyring  # type: ignore\r
        did = keyring.get_password("unk-companion", "device_id")\r
        dkey = keyring.get_password("unk-companion", "device_key")\r
        if did and dkey:\r
            return did, dkey\r
    except Exception:\r
        pass\r
    return None\r
\r
def save_credentials(device_id: str, device_key: str) -> None:\r
    if _try_keyring_save(device_id, device_key):\r
        log("Saved device credentials to OS credential store.")\r
        CRED_FILE.write_text(json.dumps({"device_id": device_id, "stored": "keyring"}))\r
        return\r
    CRED_FILE.write_text(json.dumps({"device_id": device_id, "device_key": device_key}))\r
    try:\r
        os.chmod(CRED_FILE, 0o600)\r
    except Exception:\r
        pass\r
    log(f"Saved device credentials to {CRED_FILE} (keyring unavailable).")\r
\r
def load_credentials() -> tuple[str, str] | None:\r
    kr = _try_keyring_load()\r
    if kr:\r
        return kr\r
    if not CRED_FILE.exists():\r
        return None\r
    try:\r
        data = json.loads(CRED_FILE.read_text())\r
        if "device_key" in data:\r
            return data["device_id"], data["device_key"]\r
    except Exception:\r
        return None\r
    return None\r
\r
# ---------------------------------------------------------------------------\r
# Enrollment\r
# ---------------------------------------------------------------------------\r
\r
def enroll_interactive() -> tuple[str, str]:\r
    print("=== Unk Desktop Companion :: Enrollment ===")\r
    print("1. Open /grant-engine/desktop-command on the platform.")\r
    print("2. Click 'Generate enrollment code'.")\r
    print("3. Paste the 8-character code below.\\n")\r
    code = (os.environ.get("UNK_ENROLL_CODE") or "").strip().upper()\r
    if code:\r
        print("Enrollment code: read from UNK_ENROLL_CODE")\r
    else:\r
        code = input("Enrollment code: ").strip().upper()\r
    if len(code) < 6:\r
        fatal("Code too short. Aborting.")\r
\r
    payload = {\r
        "action": "enroll_complete",\r
        "enrollment_code": code,\r
        "hostname": socket.gethostname(),\r
        "os": f"{platform.system()} {platform.release()}",\r
    }\r
    r = requests.post(\r
        COMPANION_URL,\r
        headers={"apikey": SUPABASE_ANON_KEY, "Content-Type": "application/json"},\r
        json=payload,\r
        timeout=HTTP_TIMEOUT,\r
    )\r
    if r.status_code != 200:\r
        fatal(f"Enrollment failed: HTTP {r.status_code} :: {r.text}")\r
    data = r.json()\r
    device_id = data["device_id"]\r
    device_key = data["device_key"]\r
    save_credentials(device_id, device_key)\r
    log(f"Enrolled. device_id={device_id}")\r
    return device_id, device_key\r
\r
# ---------------------------------------------------------------------------\r
# Safety helpers\r
# ---------------------------------------------------------------------------\r
\r
def expand_path(p) -> Path:\r
    """Expand ~ and %VARS% before any allow-list decision. Previously a payload\r
    like "~/Documents/Bot-Fresh" was compared literally and always failed."""\r
    return Path(os.path.expandvars(str(p))).expanduser()\r
\r
\r
def path_is_allowed(p: Path) -> bool:\r
    try:\r
        rp = expand_path(p).resolve()\r
    except Exception:\r
        return False\r
    for exact in ALLOWED_EXACT_FILES:\r
        try:\r
            if rp == exact.resolve():\r
                return True\r
        except Exception:\r
            continue\r
    return any(str(rp).startswith(str(root.resolve())) for root in ALLOWED_ROOTS)\r
\r
\r
def cwd_is_allowed(p: Path) -> bool:\r
    """Working directories: allow-listed roots plus the exact canonical bot dir."""\r
    try:\r
        rp = expand_path(p).resolve()\r
    except Exception:\r
        return False\r
    for exact in ALLOWED_EXACT_CWDS:\r
        try:\r
            if rp == exact.resolve():\r
                return True\r
        except Exception:\r
            continue\r
    return path_is_allowed(rp)\r
\r
\r
def _running_processes_matching(needle: str) -> list[dict]:\r
    """Real process identity, no guessing. Windows uses CIM; POSIX uses ps."""\r
    out: list[dict] = []\r
    try:\r
        if os.name == "nt":\r
            ps_cmd = (\r
                "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like "\r
                f"'*{needle}*' " + "} | Select-Object ProcessId,CommandLine,CreationDate "\r
                "| ConvertTo-Json -Compress"\r
            )\r
            r = subprocess.run(\r
                ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", ps_cmd],\r
                capture_output=True, text=True, timeout=60,\r
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),\r
            )\r
            raw = (r.stdout or "").strip()\r
            if raw:\r
                data = json.loads(raw)\r
                if isinstance(data, dict):\r
                    data = [data]\r
                for d in data or []:\r
                    cl = str(d.get("CommandLine") or "")\r
                    if "Get-CimInstance" in cl:\r
                        continue  # our own probe\r
                    try:\r
                        pid = int(d.get("ProcessId"))\r
                    except Exception:\r
                        continue\r
                    out.append({"pid": pid, "cmdline": cl,\r
                                "started_at": str(d.get("CreationDate") or "")})\r
        else:\r
            r = subprocess.run(["ps", "-eo", "pid=,args="],\r
                               capture_output=True, text=True, timeout=30)\r
            for line in (r.stdout or "").splitlines():\r
                line = line.strip()\r
                if needle.lower() in line.lower() and " -eo " not in line:\r
                    pid_s, _, args = line.partition(" ")\r
                    try:\r
                        out.append({"pid": int(pid_s), "cmdline": args.strip()})\r
                    except Exception:\r
                        continue\r
    except Exception as e:\r
        return [{"pid": None, "cmdline": "", "probe_error": str(e)}]\r
    return out\r
\r
\r
_BOT_CMD_RE = re.compile(r"python[a-z0-9._-]*(\\.exe)?[\\"'\\s].*Bot-Fresh\\.py", re.I)\r
\r
\r
def bot_fresh_processes() -> list[dict]:\r
    """Only real \`python ... Bot-Fresh.py\` runtimes. Excludes this companion,\r
    inline \`-c\` probes, and anything that merely mentions the filename."""\r
    me = os.getpid()\r
    out = []\r
    for p in _running_processes_matching("Bot-Fresh.py"):\r
        pid, cmd = p.get("pid"), str(p.get("cmdline") or "")\r
        if not pid or pid == me:\r
            continue\r
        if " -c " in cmd or cmd.strip().endswith(" -c"):\r
            continue\r
        if not _BOT_CMD_RE.search(cmd):\r
            continue\r
        out.append(p)\r
    return out\r
\r
\r
def bot_fresh_paper_mode() -> dict:\r
    """READ-ONLY confirmation that paper/dry-run is still the active mode.\r
    Never edits the file, never changes strategy or the live gate."""\r
    try:\r
        text = BOT_FRESH_PATH.read_text(encoding="utf-8", errors="ignore")\r
    except Exception as e:\r
        return {"readable": False, "error": str(e), "path": str(BOT_FRESH_PATH)}\r
    lines = []\r
    for raw in text.splitlines():\r
        s = raw.strip()\r
        if re.match(r"^(DRY_RUN|PAPER[A-Z_]*|LIVE[A-Z_]*|SIMULAT[A-Z_]*|TRADING_MODE|MODE)\\s*=", s, re.I):\r
            lines.append(s[:200])\r
        if len(lines) >= 25:\r
            break\r
    live_on = any(re.match(r"^(LIVE[A-Z_]*|ENABLE_LIVE[A-Z_]*)\\s*=\\s*(True|1)\\b", l, re.I) for l in lines)\r
    dry_on = any(re.match(r"^(DRY_RUN|PAPER[A-Z_]*|SIMULAT[A-Z_]*)\\s*=\\s*(True|1)\\b", l, re.I) for l in lines)\r
    return {"readable": True, "path": str(BOT_FRESH_PATH), "mode_lines": lines,\r
            "dry_run_flag_true": dry_on, "live_flag_true": live_on}\r
\r
\r
def bot_fresh_log_evidence(tail_bytes: int = 4000) -> dict:\r
    try:\r
        if not BOT_FRESH_LOG.exists():\r
            return {"exists": False, "path": str(BOT_FRESH_LOG)}\r
        st = BOT_FRESH_LOG.stat()\r
        with BOT_FRESH_LOG.open("rb") as f:\r
            if st.st_size > tail_bytes:\r
                f.seek(-tail_bytes, os.SEEK_END)\r
            tail = f.read().decode("utf-8", errors="ignore")\r
        return {"exists": True, "path": str(BOT_FRESH_LOG), "size_bytes": st.st_size,\r
                "modified_at": datetime.fromtimestamp(st.st_mtime, timezone.utc).isoformat(),\r
                "age_seconds": int(time.time() - st.st_mtime), "tail": tail}\r
    except Exception as e:\r
        return {"exists": None, "error": str(e), "path": str(BOT_FRESH_LOG)}\r
\r
\r
def bot_fresh_snapshot() -> dict:\r
    procs = bot_fresh_processes()\r
    return {\r
        "runtime_path": str(BOT_FRESH_PATH),\r
        "runtime_exists": BOT_FRESH_PATH.exists(),\r
        "running": bool(procs),\r
        "pids": [p["pid"] for p in procs],\r
        "processes": procs,\r
        "log": bot_fresh_log_evidence(),\r
        "paper_mode": bot_fresh_paper_mode(),\r
        "checked_at": datetime.now(timezone.utc).isoformat(),\r
    }\r
\r
def executable_is_allowed(exe: str) -> bool:\r
    return Path(exe).name in ALLOWED_EXECUTABLES\r
\r
def url_is_allowed(url: str) -> tuple[bool, str]:\r
    """Returns (allowed, reason). Hard block wins over allow-list."""\r
    if not url or not isinstance(url, str):\r
        return False, "empty_url"\r
    try:\r
        parsed = urllib.parse.urlparse(url)\r
    except Exception:\r
        return False, "url_parse_failed"\r
    if parsed.scheme not in ("http", "https"):\r
        return False, f"scheme_not_allowed:{parsed.scheme}"\r
    host = (parsed.hostname or "").lower()\r
    if not host:\r
        return False, "no_host"\r
    full = url.lower()\r
    for blocked in URL_HARD_BLOCKLIST_SUBSTRINGS:\r
        if blocked in full:\r
            return False, f"hard_blocked:{blocked}"\r
    # Allow if host or any parent domain is in the allow-list.\r
    parts = host.split(".")\r
    for i in range(len(parts) - 1):\r
        candidate = ".".join(parts[i:])\r
        if candidate in URL_ALLOWLIST:\r
            return True, "ok"\r
    if host in URL_ALLOWLIST:\r
        return True, "ok"\r
    return False, f"host_not_in_allowlist:{host}"\r
\r
def file_open_ext_allowed(p: Path) -> bool:\r
    return p.suffix.lower() not in OPEN_FILE_DENY_EXT\r
\r
# ---------------------------------------------------------------------------\r
# Capability handlers\r
# Each returns a dict appended to the action result.\r
# ---------------------------------------------------------------------------\r
\r
@dataclass\r
class ActionContext:\r
    action_id: str\r
    capability: str\r
    action_type: str\r
    payload: dict[str, Any]\r
    created_at: str | None = None\r
\r
def cap_capture_screenshot(ctx: ActionContext) -> dict:\r
    try:\r
        from PIL import ImageGrab  # type: ignore\r
    except Exception:\r
        return {"ok": False, "error": "pillow_not_installed"}\r
    out = SCREENSHOT_DIR / f"{ctx.action_id}.png"\r
    img = ImageGrab.grab()\r
    img.save(out, format="PNG")\r
    return {"ok": True, "screenshot_path": str(out), "size": img.size}\r
\r
def cap_read_file(ctx: ActionContext) -> dict:\r
    p = Path(ctx.payload.get("path", ""))\r
    if not path_is_allowed(p):\r
        return {"ok": False, "error": "path_not_allowed"}\r
    if not p.exists():\r
        return {"ok": False, "error": "not_found"}\r
    max_bytes = int(ctx.payload.get("max_bytes", 64_000))\r
    data = p.read_bytes()[:max_bytes]\r
    try:\r
        text = data.decode("utf-8", errors="replace")\r
    except Exception:\r
        text = repr(data)\r
    return {"ok": True, "bytes": len(data), "text": text}\r
\r
def cap_write_file(ctx: ActionContext) -> dict:\r
    p = Path(ctx.payload.get("path", ""))\r
    if not path_is_allowed(p):\r
        return {"ok": False, "error": "path_not_allowed"}\r
    content = ctx.payload.get("content", "")\r
    p.parent.mkdir(parents=True, exist_ok=True)\r
    p.write_text(content, encoding="utf-8")\r
    return {"ok": True, "bytes": len(content)}\r
\r
def cap_append_to_file(ctx: ActionContext) -> dict:\r
    """Append-only. Never overwrites. Cap per call: APPEND_MAX_BYTES."""\r
    p = Path(ctx.payload.get("path", ""))\r
    if not path_is_allowed(p):\r
        return {"ok": False, "error": "path_not_allowed"}\r
    content = ctx.payload.get("content", "")\r
    if not isinstance(content, str):\r
        return {"ok": False, "error": "bad_content"}\r
    if len(content.encode("utf-8")) > APPEND_MAX_BYTES:\r
        return {"ok": False, "error": "content_too_large"}\r
    p.parent.mkdir(parents=True, exist_ok=True)\r
    with p.open("a", encoding="utf-8") as f:\r
        f.write(content)\r
    return {"ok": True, "appended_bytes": len(content), "path": str(p)}\r
\r
def _kill_pids(pids: list[int]) -> list[dict]:\r
    killed = []\r
    for pid in pids:\r
        try:\r
            if os.name == "nt":\r
                r = subprocess.run(["taskkill", "/PID", str(pid), "/F"],\r
                                   capture_output=True, text=True, timeout=30,\r
                                   creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))\r
                killed.append({"pid": pid, "exit_code": r.returncode,\r
                               "out": (r.stdout or r.stderr or "").strip()[:200]})\r
            else:\r
                os.kill(pid, 9)\r
                killed.append({"pid": pid, "exit_code": 0, "out": "sigkill"})\r
        except Exception as e:\r
            killed.append({"pid": pid, "error": str(e)})\r
    return killed\r
\r
\r
def cap_launch_process(ctx: ActionContext) -> dict:\r
    """Canonical desktop process launch.\r
\r
    Bot-Fresh.py gets extra handling, because a trading runtime must never be\r
    duplicated and a launch with no receipt is worthless:\r
      - idempotent: an existing Bot-Fresh.py process short-circuits the launch\r
      - correct cwd, so logs land beside the bot\r
      - stdout/stderr captured to bot-fresh.out.log (never DEVNULL)\r
      - post-launch re-probe returns real PID + log evidence + paper-mode read\r
    """\r
    exe = ctx.payload.get("executable", "")\r
    args = ctx.payload.get("args", [])\r
    if not executable_is_allowed(exe):\r
        return {"ok": False, "error": "executable_not_allowed", "executable": exe}\r
    if not isinstance(args, list) or not all(isinstance(a, str) for a in args):\r
        return {"ok": False, "error": "bad_args"}\r
\r
    is_bot = any(str(a).lower().endswith("bot-fresh.py") for a in args) or \\\r
        bool(ctx.payload.get("bot_fresh"))\r
    cwd_raw = ctx.payload.get("cwd")\r
    stdout_target = subprocess.DEVNULL\r
    stderr_target = subprocess.DEVNULL\r
    log_handle = None\r
    force_restart = bool(ctx.payload.get("force_restart"))\r
    killed: list[dict] = []\r
\r
    if is_bot:\r
        target = BOT_FRESH_PATH\r
        for a in args:\r
            if str(a).lower().endswith("bot-fresh.py"):\r
                cand = expand_path(a)\r
                if cand.exists():\r
                    target = cand\r
                break\r
        if target.name != "Bot-Fresh.py":\r
            return {"ok": False, "error": "bot_runtime_name_locked", "given": target.name}\r
        if not target.exists():\r
            return {"ok": False, "error": "bot_runtime_missing",\r
                    "expected_path": str(BOT_FRESH_PATH)}\r
        if not path_is_allowed(target):\r
            return {"ok": False, "error": "path_not_allowed", "path": str(target)}\r
        # -u: unbuffered stdout so bot-fresh.out.log is a real heartbeat,\r
        # not a file that only updates when Python flushes its buffer.\r
        args = ["-u", str(target)]\r
        cwd_raw = cwd_raw or str(target.parent)\r
\r
        existing = bot_fresh_processes()\r
        if existing and not force_restart:\r
            snap = bot_fresh_snapshot()\r
            snap.update({"ok": True, "launched": False, "already_running": True,\r
                         "pid": existing[0]["pid"],\r
                         "note": "idempotent: live Bot-Fresh.py process found; no duplicate launched"})\r
            return snap\r
        if existing and force_restart:\r
            killed = _kill_pids([p["pid"] for p in existing])\r
            time.sleep(2)\r
\r
    cwd = None\r
    if cwd_raw:\r
        cp = expand_path(cwd_raw)\r
        if not cwd_is_allowed(cp):\r
            return {"ok": False, "error": "cwd_not_allowed", "cwd": str(cp)}\r
        cwd = str(cp)\r
\r
    try:\r
        if is_bot:\r
            BOT_FRESH_LOG.parent.mkdir(parents=True, exist_ok=True)\r
            log_handle = BOT_FRESH_LOG.open("a", encoding="utf-8", errors="ignore")\r
            log_handle.write(\r
                f"\\n=== Unk launch {datetime.now(timezone.utc).isoformat()} "\r
                f"action={ctx.action_id} ===\\n")\r
            log_handle.flush()\r
            stdout_target = log_handle\r
            stderr_target = subprocess.STDOUT\r
        creation_flags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0\r
        launch_env = None\r
        if is_bot:\r
            # Windows consoles default to cp1252; the bot prints emoji in its\r
            # alert lines and dies with UnicodeEncodeError -> "Retrying in 20s".\r
            # Force UTF-8 on the child only. No strategy/credential change.\r
            launch_env = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"}\r
        proc = subprocess.Popen(\r
            [exe, *args],\r
            cwd=cwd,\r
            stdout=stdout_target,\r
            stderr=stderr_target,\r
            creationflags=creation_flags,\r
            env=launch_env,\r
        )\r
    except Exception as e:\r
        if log_handle:\r
            try:\r
                log_handle.close()\r
            except Exception:\r
                pass\r
        return {"ok": False, "error": "launch_failed", "detail": str(e)}\r
    finally:\r
        if log_handle:\r
            try:\r
                log_handle.close()\r
            except Exception:\r
                pass\r
\r
    if not is_bot:\r
        return {"ok": True, "pid": proc.pid, "cwd": cwd}\r
\r
    # Real evidence: give it a few seconds, then re-probe the OS.\r
    time.sleep(6)\r
    snap = bot_fresh_snapshot()\r
    alive = proc.poll() is None\r
    snap.update({\r
        "ok": alive and snap["running"],\r
        "launched": True,\r
        "already_running": False,\r
        "pid": proc.pid,\r
        "spawn_alive": alive,\r
        "spawn_exit_code": proc.returncode,\r
        "cwd": cwd,\r
        "killed_stale": killed,\r
        "executable": exe,\r
    })\r
    if not snap["ok"]:\r
        snap["error"] = "bot_exited_immediately"\r
    return snap\r
\r
def cap_elevate_powershell_script(ctx: ActionContext) -> dict:\r
    """Trigger a UAC prompt on the logged-in user's desktop to run an\r
    approved .ps1 under this companion's own install dir with admin rights.\r
\r
    Guardrails:\r
      - Windows only.\r
      - Script must live under %LOCALAPPDATA%\\\\UnkCompanion (durable install).\r
      - Script must be a .ps1 that already exists.\r
      - Uses Start-Process -Verb RunAs so Windows displays the UAC dialog.\r
        Jason must click Yes; we never bypass consent.\r
    """\r
    if platform.system() != "Windows":\r
        return {"ok": False, "error": "windows_only"}\r
    install_root = Path(os.environ.get("LOCALAPPDATA", "")) / "UnkCompanion"\r
    script_raw = str(ctx.payload.get("script", "") or "").strip()\r
    script_relative = str(ctx.payload.get("script_relative", "") or "").strip()\r
    if script_relative:\r
        rel = Path(script_relative)\r
        if rel.is_absolute() or ".." in rel.parts:\r
            return {"ok": False, "error": "bad_script_relative", "script_relative": script_relative}\r
        script_path = install_root / rel\r
    elif script_raw:\r
        script_path = Path(script_raw)\r
    else:\r
        return {"ok": False, "error": "script_required"}\r
    if script_path.suffix.lower() != ".ps1":\r
        return {"ok": False, "error": "not_ps1"}\r
    try:\r
        script_path = script_path.resolve()\r
        install_root_resolved = install_root.resolve()\r
    except Exception as e:\r
        return {"ok": False, "error": "path_resolve_failed", "detail": str(e)}\r
    if install_root_resolved not in script_path.parents and script_path.parent != install_root_resolved:\r
        return {"ok": False, "error": "script_outside_install_root",\r
                "expected_root": str(install_root_resolved), "given": str(script_path)}\r
    if not script_path.exists():\r
        return {"ok": False, "error": "script_missing", "path": str(script_path)}\r
    extra_args = ctx.payload.get("args", []) or []\r
    if not isinstance(extra_args, list) or not all(isinstance(a, str) for a in extra_args):\r
        return {"ok": False, "error": "bad_args"}\r
    # Build a single PowerShell -Command that spawns an elevated child.\r
    # Start-Process from a non-elevated parent triggers the UAC dialog.\r
    arg_list_parts = ["'-NoProfile'", "'-ExecutionPolicy'", "'Bypass'", "'-File'", f"'{script_path}'"]\r
    for a in extra_args:\r
        safe = a.replace("'", "''")\r
        arg_list_parts.append(f"'{safe}'")\r
    inner = f"Start-Process powershell.exe -Verb RunAs -ArgumentList {','.join(arg_list_parts)}"\r
    try:\r
        proc = subprocess.Popen(\r
            ["powershell.exe", "-NoProfile", "-WindowStyle", "Hidden", "-Command", inner],\r
            stdout=subprocess.DEVNULL,\r
            stderr=subprocess.DEVNULL,\r
        )\r
        return {"ok": True, "pid": proc.pid, "script": str(script_path),\r
                "note": "uac_prompt_shown_to_user"}\r
    except Exception as e:\r
        return {"ok": False, "error": "elevate_launch_failed", "detail": str(e)}\r
\r
\r
# --- run_local_script (Ground Zero signed audit runner) --------------------\r
GROUND_ZERO_ROOT = Path(r"C:\\JFortitude\\ground-zero-audit")\r
GROUND_ZERO_LOG_DIR = GROUND_ZERO_ROOT / "logs"\r
GROUND_ZERO_OUT_DIR = GROUND_ZERO_ROOT / "out"\r
GROUND_ZERO_MANIFEST = GROUND_ZERO_ROOT / "manifest.json"\r
GROUND_ZERO_MAX_TIMEOUT = 3600\r
GROUND_ZERO_DEFAULT_TIMEOUT = 900\r
\r
_INTERPRETERS = {\r
    "powershell": ("powershell.exe",\r
                   ["-NoProfile", "-ExecutionPolicy", "Bypass", "-File"]),\r
    "python":     ("python",       []),\r
    "cmd":        ("cmd.exe",      ["/c"]),\r
}\r
\r
def _sha256_of(p: Path) -> str:\r
    import hashlib\r
    h = hashlib.sha256()\r
    with p.open("rb") as f:\r
        for chunk in iter(lambda: f.read(1024 * 1024), b""):\r
            h.update(chunk)\r
    return h.hexdigest()\r
\r
def _load_ground_zero_manifest() -> tuple[dict | None, str | None]:\r
    if not GROUND_ZERO_MANIFEST.exists():\r
        return None, "manifest_missing"\r
    try:\r
        data = json.loads(GROUND_ZERO_MANIFEST.read_text(encoding="utf-8"))\r
    except Exception as e:\r
        return None, f"manifest_unreadable:{e}"\r
    scripts = data.get("scripts")\r
    if not isinstance(scripts, dict):\r
        return None, "manifest_missing_scripts"\r
    return scripts, None\r
\r
def cap_run_local_script(ctx: ActionContext) -> dict:\r
    """Execute a SIGNED script from C:\\\\JFortitude\\\\ground-zero-audit\\\\.\r
\r
    Guardrails (all enforced):\r
      - Windows only.\r
      - Script must resolve inside GROUND_ZERO_ROOT (no traversal).\r
      - Script's SHA-256 must equal manifest.json entry for its relative path.\r
      - Interpreter is chosen from a fixed map (powershell | python | cmd) —\r
        picked from the manifest entry, never the caller.\r
      - Blocking run with a hard timeout (default 900s, cap 3600s).\r
      - stdout+stderr written to logs\\\\<action_id>.log; tails returned.\r
      - Any *.zip appearing under out\\\\ after start_ts is captured with\r
        {path, size, sha256}. Nothing is uploaded from here; the platform\r
        pulls artifacts via the existing private artifact channel.\r
    """\r
    if platform.system() != "Windows":\r
        return {"ok": False, "error": "windows_only"}\r
\r
    rel = str(ctx.payload.get("script", "") or "").strip()\r
    if not rel:\r
        return {"ok": False, "error": "script_required"}\r
\r
    # Resolve + jail.\r
    try:\r
        root = GROUND_ZERO_ROOT.resolve()\r
    except Exception:\r
        return {"ok": False, "error": "root_missing", "root": str(GROUND_ZERO_ROOT)}\r
    if not root.exists():\r
        return {"ok": False, "error": "root_missing", "root": str(root)}\r
\r
    candidate = (root / rel)\r
    try:\r
        candidate = candidate.resolve()\r
    except Exception as e:\r
        return {"ok": False, "error": "path_resolve_failed", "detail": str(e)}\r
    if root != candidate and root not in candidate.parents:\r
        return {"ok": False, "error": "script_outside_root",\r
                "root": str(root), "given": str(candidate)}\r
    if not candidate.is_file():\r
        return {"ok": False, "error": "script_missing", "path": str(candidate)}\r
\r
    # Manifest / signature check.\r
    scripts, err = _load_ground_zero_manifest()\r
    if err:\r
        return {"ok": False, "error": err, "manifest": str(GROUND_ZERO_MANIFEST)}\r
    rel_key = candidate.relative_to(root).as_posix()\r
    entry = scripts.get(rel_key)\r
    if not isinstance(entry, dict):\r
        return {"ok": False, "error": "script_not_signed", "script": rel_key}\r
    expected = str(entry.get("sha256", "")).lower().strip()\r
    if len(expected) != 64:\r
        return {"ok": False, "error": "manifest_entry_bad_hash", "script": rel_key}\r
    actual = _sha256_of(candidate)\r
    if actual.lower() != expected:\r
        return {"ok": False, "error": "signature_mismatch",\r
                "script": rel_key, "expected_sha256": expected, "actual_sha256": actual}\r
\r
    interp_key = str(entry.get("interpreter", "")).lower().strip()\r
    interp = _INTERPRETERS.get(interp_key)\r
    if not interp:\r
        return {"ok": False, "error": "unsupported_interpreter",\r
                "interpreter": interp_key, "allowed": sorted(_INTERPRETERS)}\r
    exe, prefix_args = interp\r
\r
    # Caller args (optional).\r
    extra_args = ctx.payload.get("args", []) or []\r
    if not isinstance(extra_args, list) or not all(isinstance(a, str) for a in extra_args):\r
        return {"ok": False, "error": "bad_args"}\r
\r
    # Repository repair is doubly authorized: Project K matches an exact\r
    # authorization row and the signed local manifest independently matches\r
    # the exact argument vector. No caller text becomes a shell command.\r
    if rel_key == "unk_repository_repair.py":\r
        allowed_args = entry.get("allowed_args")\r
        if (not isinstance(allowed_args, list)\r
                or extra_args not in allowed_args):\r
            return {"ok": False, "error": "manifest_args_not_authorized",\r
                    "script": rel_key}\r
\r
    # Timeout.\r
    try:\r
        timeout = int(ctx.payload.get("timeout_seconds", GROUND_ZERO_DEFAULT_TIMEOUT))\r
    except Exception:\r
        timeout = GROUND_ZERO_DEFAULT_TIMEOUT\r
    timeout = max(1, min(timeout, GROUND_ZERO_MAX_TIMEOUT))\r
\r
    # Prepare logs + output dirs.\r
    GROUND_ZERO_LOG_DIR.mkdir(parents=True, exist_ok=True)\r
    GROUND_ZERO_OUT_DIR.mkdir(parents=True, exist_ok=True)\r
    log_path = GROUND_ZERO_LOG_DIR / f"{ctx.action_id}.log"\r
\r
    cmd = [exe, *prefix_args, str(candidate), *extra_args]\r
    start_ts = time.time()\r
    timed_out = False\r
    try:\r
        r = subprocess.run(\r
            cmd,\r
            cwd=str(root),\r
            capture_output=True,\r
            text=True,\r
            timeout=timeout,\r
        )\r
        stdout, stderr, exit_code = r.stdout, r.stderr, r.returncode\r
    except subprocess.TimeoutExpired as te:\r
        timed_out = True\r
        stdout = te.stdout.decode(errors="replace") if isinstance(te.stdout, bytes) else (te.stdout or "")\r
        stderr = te.stderr.decode(errors="replace") if isinstance(te.stderr, bytes) else (te.stderr or "")\r
        exit_code = -1\r
    except Exception as e:\r
        return {"ok": False, "error": "run_failed", "detail": str(e), "cmd": cmd[:2]}\r
\r
    duration = round(time.time() - start_ts, 2)\r
\r
    # Persist full log.\r
    try:\r
        log_path.write_text(\r
            f"# script: {rel_key}\\n"\r
            f"# sha256: {actual}\\n"\r
            f"# interpreter: {interp_key}\\n"\r
            f"# args: {json.dumps(extra_args)}\\n"\r
            f"# exit_code: {exit_code}\\n"\r
            f"# duration_s: {duration}\\n"\r
            f"# timed_out: {timed_out}\\n"\r
            f"\\n===== STDOUT =====\\n{stdout}\\n"\r
            f"\\n===== STDERR =====\\n{stderr}\\n",\r
            encoding="utf-8",\r
        )\r
    except Exception:\r
        pass\r
\r
    # Collect ZIP outputs created / modified after start.\r
    zips: list[dict] = []\r
    try:\r
        for z in sorted(GROUND_ZERO_OUT_DIR.rglob("*.zip")):\r
            try:\r
                st = z.stat()\r
                if st.st_mtime >= start_ts - 1:\r
                    zips.append({\r
                        "path": str(z),\r
                        "relative_path": z.relative_to(GROUND_ZERO_OUT_DIR).as_posix(),\r
                        "size": st.st_size,\r
                        "sha256": _sha256_of(z),\r
                        "modified_at": int(st.st_mtime),\r
                    })\r
            except Exception:\r
                continue\r
    except Exception:\r
        pass\r
\r
    return {\r
        "ok": not timed_out and exit_code == 0,\r
        "script": rel_key,\r
        "sha256": actual,\r
        "interpreter": interp_key,\r
        "exit_code": exit_code,\r
        "duration_s": duration,\r
        "timed_out": timed_out,\r
        "stdout_tail": stdout[-4000:],\r
        "stderr_tail": stderr[-2000:],\r
        "log_path": str(log_path),\r
        "zip_outputs": zips,\r
    }\r
\r
\r
\r
def cap_run_check(ctx: ActionContext) -> dict:\r
    """Short, blocking, read-only command (whitelisted exe). 30s cap."""\r
    _check = str((ctx.payload or {}).get("check") or "").lower().strip()\r
    if _check in ("bot_fresh_status", "bot_runtime_status"):\r
        snap = bot_fresh_snapshot()\r
        snap.update({"ok": True, "exit_code": 0, "check": "bot_fresh_status",\r
                     "companion_version": COMPANION_VERSION})\r
        return snap\r
    if _check == "bot_status":\r
        return {\r
            "ok": True,\r
            "exit_code": 0,\r
            "check": "bot_status",\r
            "companion_version": COMPANION_VERSION,\r
            "status": status_snapshot(),\r
            "heartbeat_sidecar_exists": HEARTBEAT_SIDECAR.exists(),\r
        }\r
    exe = ctx.payload.get("executable", "")\r
    args = ctx.payload.get("args", [])\r
    if not executable_is_allowed(exe):\r
        return {"ok": False, "error": "executable_not_allowed", "executable": exe}\r
    try:\r
        r = subprocess.run(\r
            [exe, *args],\r
            capture_output=True, text=True, timeout=30,\r
        )\r
        return {\r
            "ok": True,\r
            "exit_code": r.returncode,\r
            "stdout_tail": r.stdout[-4000:],\r
            "stderr_tail": r.stderr[-2000:],\r
        }\r
    except subprocess.TimeoutExpired:\r
        return {"ok": False, "error": "timeout"}\r
    except Exception as e:\r
        return {"ok": False, "error": "run_failed", "detail": str(e)}\r
\r
\r
_FAST_PROBE_PS = r"""\r
$ErrorActionPreference = 'SilentlyContinue'\r
$ProgressPreference = 'SilentlyContinue'\r
$started = Get-Date\r
function Task-Info($name) {\r
  $out = [ordered]@{\r
    exists=$false; status=$null; last_result=$null; run_as_user=$null;\r
    task_to_run=$null; schedule=$null; enabled=$null;\r
    missed_start_enabled=$null; execution_time_limit=$null; interval_minutes=$null\r
  }\r
  try {\r
    $raw = & schtasks.exe /query /tn $name /v /fo LIST 2>$null\r
    if ($LASTEXITCODE -ne 0 -or -not $raw) { return $out }\r
    $out.exists = $true\r
    $map = @{}\r
    foreach ($line in $raw) {\r
      if ($line -match '^\\s*([^:]+?):\\s*(.*)$') { $map[$Matches[1].Trim()] = $Matches[2].Trim() }\r
    }\r
    $out.status = $map['Status']\r
    $out.last_result = $map['Last Result']\r
    $out.run_as_user = $map['Run As User']\r
    $out.task_to_run = $map['Task To Run']\r
    $out.schedule = $map['Schedule Type']\r
    $out.enabled = ($map['Scheduled Task State'] -eq 'Enabled')\r
    $out.execution_time_limit = $map['Task Time Limit']\r
    if ($map['Repeat: Every']) { $out.interval_minutes = $map['Repeat: Every'] }\r
  } catch {}\r
  try {\r
    $t = Get-ScheduledTask -TaskName ($name -replace '^\\\\','') -ErrorAction SilentlyContinue\r
    if ($t) {\r
      $s = $t.Settings\r
      if ($s) { $out.missed_start_enabled = [bool]$s.StartWhenAvailable }\r
    }\r
  } catch {}\r
  return $out\r
}\r
$sup  = Task-Info '\\UnkSupervisor'\r
$keep = Task-Info '\\UnkSupervisorKeepAlive'\r
$py = @(Get-Process python,pythonw -ErrorAction SilentlyContinue)\r
$companionPid = $null; $companionStart = $null\r
foreach ($p in $py) {\r
  try {\r
    $cl = (Get-CimInstance Win32_Process -Filter "ProcessId=$($p.Id)" -ErrorAction SilentlyContinue).CommandLine\r
    if ($cl -match 'unk_companion\\.py') { $companionPid = $p.Id; $companionStart = $p.StartTime.ToString('o'); break }\r
  } catch {}\r
}\r
$installerPath = Join-Path $env:LOCALAPPDATA 'UnkCompanion\\install_supervisor.ps1'\r
$installerExists = Test-Path $installerPath\r
$installerMtime = $null\r
if ($installerExists) { try { $installerMtime = (Get-Item $installerPath).LastWriteTime.ToString('o') } catch {} }\r
$out = [ordered]@{\r
  supervisor_exists = $sup.exists\r
  supervisor_status = $sup.status\r
  supervisor_last_result = $sup.last_result\r
  supervisor_run_as_user = $sup.run_as_user\r
  supervisor_task_to_run = $sup.task_to_run\r
  supervisor_schedule = $sup.schedule\r
  supervisor_start_in = $null\r
  supervisor_enabled = $sup.enabled\r
  supervisor_missed_start_enabled = $sup.missed_start_enabled\r
  supervisor_execution_time_limit = $sup.execution_time_limit\r
  keepalive_exists = $keep.exists\r
  keepalive_status = $keep.status\r
  keepalive_last_result = $keep.last_result\r
  keepalive_run_as_user = $keep.run_as_user\r
  keepalive_task_to_run = $keep.task_to_run\r
  keepalive_schedule = $keep.schedule\r
  keepalive_interval_minutes = $keep.interval_minutes\r
  keepalive_enabled = $keep.enabled\r
  current_companion_pid = $companionPid\r
  current_companion_start_time = $companionStart\r
  companion_instance_count = ($py | Measure-Object).Count\r
  installer_exists = $installerExists\r
  installer_modified_at = $installerMtime\r
  probe_duration_ms = [int]((Get-Date) - $started).TotalMilliseconds\r
  probe_result = 'ok'\r
}\r
$out | ConvertTo-Json -Compress\r
"""\r
\r
\r
def _run_fast_probe(action_id: str) -> dict:\r
    started = time.time()\r
    try:\r
        r = subprocess.run(\r
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-Command", _FAST_PROBE_PS],\r
            capture_output=True, text=True, timeout=30,\r
        )\r
    except subprocess.TimeoutExpired:\r
        return {"ok": False, "error": "fast_probe_timeout", "probe_duration_ms": int((time.time() - started) * 1000)}\r
    except Exception as e:\r
        return {"ok": False, "error": "fast_probe_failed", "detail": str(e)}\r
    payload = None\r
    try:\r
        payload = json.loads((r.stdout or "").strip().splitlines()[-1])\r
    except Exception as e:\r
        return {"ok": False, "error": "fast_probe_parse_failed", "stdout_tail": (r.stdout or "")[-2000:], "stderr_tail": (r.stderr or "")[-1000:], "detail": str(e)}\r
    payload["action_id"] = action_id\r
    payload["ok"] = True\r
    payload["mode"] = "fast_probe"\r
    payload["companion_version"] = COMPANION_VERSION\r
    return payload\r
\r
\r
def cap_platform_persistence_repair(ctx: ActionContext) -> dict:\r
    """Diagnose and repair the Ground Zero always-on worker layer.\r
\r
    Modes:\r
      - fast_probe: bounded (<=30s) task-state snapshot. No elevation.\r
      - audit / apply: legacy repair_persistence.ps1 path.\r
    """\r
    if platform.system() != "Windows":\r
        return {"ok": False, "error": "windows_only"}\r
\r
    mode = str((ctx.payload or {}).get("mode") or "audit").lower().strip()\r
    if mode == "fast_probe":\r
        return _run_fast_probe(ctx.action_id)\r
    if mode == "noop":\r
        return {"ok": True, "mode": "noop", "exit_code": 0, "companion_version": COMPANION_VERSION, "status": status_snapshot()}\r
    if mode == "kill_proof":\r
        _RESTART_REQUESTED["pending"] = True\r
        _RESTART_REQUESTED["reason"] = "persistence_kill_proof"\r
        _RESTART_REQUESTED["strategy"] = "supervisor_exit"\r
        return {\r
            "ok": True,\r
            "mode": "kill_proof",\r
            "exit_code": 0,\r
            "restart_scheduled": True,\r
            "strategy": "supervisor_exit",\r
            "old_instance_id": INSTANCE_ID,\r
            "old_boot_ts": BOOT_TS,\r
            "companion_version": COMPANION_VERSION,\r
        }\r
\r
    script = _companion_script_dir() / "repair_persistence.ps1"\r
    if not script.exists():\r
        return {"ok": False, "error": "repair_script_missing", "path": str(script)}\r
    apply = bool((ctx.payload or {}).get("apply")) or mode in {"apply", "repair"}\r
    timeout = 300 if apply else 240\r
    args = [\r
        "powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",\r
        "-File", str(script), "-ActionId", ctx.action_id,\r
    ]\r
    if apply:\r
        args.append("-Apply")\r
    if bool((ctx.payload or {}).get("request_elevation_if_needed")):\r
        args.append("-RequestElevationIfNeeded")\r
    try:\r
        r = subprocess.run(args, capture_output=True, text=True, timeout=timeout, cwd=str(_companion_script_dir()))\r
    except subprocess.TimeoutExpired as te:\r
        stdout = te.stdout.decode(errors="replace") if isinstance(te.stdout, bytes) else (te.stdout or "")\r
        stderr = te.stderr.decode(errors="replace") if isinstance(te.stderr, bytes) else (te.stderr or "")\r
        return {"ok": False, "error": "timeout", "stdout_tail": stdout[-8000:], "stderr_tail": stderr[-4000:], "exit_code": -1}\r
    except Exception as e:\r
        return {"ok": False, "error": "run_failed", "detail": str(e)}\r
\r
    receipt_path = COMPANION_DIR / "persistence_repair_latest.json"\r
    receipt = None\r
    if receipt_path.exists():\r
        try:\r
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))\r
        except Exception as e:\r
            receipt = {"receipt_unreadable": str(e), "path": str(receipt_path)}\r
    return {\r
        "ok": r.returncode == 0,\r
        "mode": "apply" if apply else "audit",\r
        "exit_code": r.returncode,\r
        "stdout_tail": (r.stdout or "")[-8000:],\r
        "stderr_tail": (r.stderr or "")[-4000:],\r
        "detail": receipt,\r
    }\r
\r
def cap_desktop_commander_repair(ctx: ActionContext) -> dict:\r
    """Run the bounded persistence probe for recurring desktop repair checks.\r
\r
    This path is diagnostic only. It does not elevate or apply a repair, and the\r
    receipt says so explicitly so an automated verifier cannot mistake a probe\r
    for a completed repair.\r
    """\r
    result = _run_fast_probe(ctx.action_id)\r
    result["requested_capability"] = "desktop_commander_repair"\r
    result["repair_applied"] = False\r
    return result\r
\r
# ----- Tier 2 capabilities -----\r
\r
def _open_with_default_app(target: str) -> None:\r
    sys_name = platform.system()\r
    if sys_name == "Windows":\r
        os.startfile(target)  # type: ignore[attr-defined]\r
    elif sys_name == "Darwin":\r
        subprocess.Popen(["open", target])\r
    else:\r
        subprocess.Popen(["xdg-open", target])\r
\r
def cap_open_url(ctx: ActionContext) -> dict:\r
    url = ctx.payload.get("url", "")\r
    ok, reason = url_is_allowed(url)\r
    if not ok:\r
        return {"ok": False, "error": "url_not_allowed", "reason": reason}\r
    try:\r
        _open_with_default_app(url)\r
        return {"ok": True, "url": url}\r
    except Exception as e:\r
        return {"ok": False, "error": "open_failed", "detail": str(e)}\r
\r
def cap_connector_escort(ctx: ActionContext) -> dict:\r
    """Human-in-the-loop escort for Lovable workspace connectors.\r
\r
    Unk cannot click through Google consent, read passwords, or bypass the\r
    Lovable workspace UI. What he can do safely is open the Lovable surface and\r
    put the exact connector checklist on Jason's clipboard so the human step is\r
    guided instead of remembered from chat.\r
    """\r
    payload = ctx.payload or {}\r
    url = str(payload.get("url") or "https://lovable.app")\r
    ok, reason = url_is_allowed(url)\r
    if not ok:\r
        return {"ok": False, "error": "url_not_allowed", "reason": reason}\r
\r
    provider = str(payload.get("provider") or "Google Drive")\r
    account = str(payload.get("account_email") or "jason@blackarchives.org")\r
    checklist = str(payload.get("checklist") or f"""Unk Connector Escort — {provider}\r
\r
Goal: add/link a SECOND {provider} connection for {account}.\r
\r
1. In Lovable, open the workspace-level Connectors area.\r
2. Search/select {provider}.\r
3. Choose + Add connection / Connect another account.\r
4. On Google, choose Use another account and sign in as {account}.\r
5. Keep Drive read permission selected and approve.\r
6. Return to Lovable and finish linking the new connection to this project.\r
7. Tell Lovable chat: "I did it" so the agent can verify list_connections shows another google_drive row.\r
\r
If you only see Gmail or Calendar afterward, that was the wrong Google connector; repeat under Google Drive.\r
""")\r
\r
    clipboard_ok = _clipboard_set(checklist[:CLIPBOARD_MAX_CHARS])\r
    try:\r
        _open_with_default_app(url)\r
    except Exception as e:\r
        return {\r
            "ok": False,\r
            "error": "open_failed",\r
            "detail": str(e),\r
            "clipboard_ok": clipboard_ok,\r
            "checklist": checklist,\r
        }\r
    return {\r
        "ok": True,\r
        "url": url,\r
        "provider": provider,\r
        "account_email": account,\r
        "clipboard_ok": clipboard_ok,\r
        "next_human_step": "Use the copied checklist in Lovable's Connectors UI; Google consent remains human-only.",\r
    }\r
\r
def cap_open_file(ctx: ActionContext) -> dict:\r
    p = Path(ctx.payload.get("path", ""))\r
    if not path_is_allowed(p):\r
        return {"ok": False, "error": "path_not_allowed"}\r
    if not p.exists():\r
        return {"ok": False, "error": "not_found"}\r
    if not file_open_ext_allowed(p):\r
        return {"ok": False, "error": "extension_blocked", "ext": p.suffix.lower()}\r
    try:\r
        _open_with_default_app(str(p))\r
        return {"ok": True, "path": str(p)}\r
    except Exception as e:\r
        return {"ok": False, "error": "open_failed", "detail": str(e)}\r
\r
def cap_reveal_in_explorer(ctx: ActionContext) -> dict:\r
    p = Path(ctx.payload.get("path", ""))\r
    if not path_is_allowed(p):\r
        return {"ok": False, "error": "path_not_allowed"}\r
    if not p.exists():\r
        return {"ok": False, "error": "not_found"}\r
    sys_name = platform.system()\r
    try:\r
        if sys_name == "Windows":\r
            subprocess.Popen(["explorer", "/select,", str(p)])\r
        elif sys_name == "Darwin":\r
            subprocess.Popen(["open", "-R", str(p)])\r
        else:\r
            subprocess.Popen(["xdg-open", str(p.parent)])\r
        return {"ok": True, "path": str(p)}\r
    except Exception as e:\r
        return {"ok": False, "error": "reveal_failed", "detail": str(e)}\r
\r
def _clipboard_get() -> str | None:\r
    sys_name = platform.system()\r
    try:\r
        if sys_name == "Windows":\r
            r = subprocess.run(["powershell", "-NoProfile", "-Command", "Get-Clipboard"],\r
                               capture_output=True, text=True, timeout=5)\r
            return r.stdout if r.returncode == 0 else None\r
        if sys_name == "Darwin":\r
            r = subprocess.run(["pbpaste"], capture_output=True, text=True, timeout=5)\r
            return r.stdout if r.returncode == 0 else None\r
        r = subprocess.run(["xclip", "-selection", "clipboard", "-o"],\r
                           capture_output=True, text=True, timeout=5)\r
        return r.stdout if r.returncode == 0 else None\r
    except Exception:\r
        return None\r
\r
def _clipboard_set(text: str) -> bool:\r
    sys_name = platform.system()\r
    try:\r
        if sys_name == "Windows":\r
            p = subprocess.Popen(["clip"], stdin=subprocess.PIPE)\r
            p.communicate(input=text.encode("utf-16le"))\r
            return p.returncode == 0\r
        if sys_name == "Darwin":\r
            p = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE)\r
            p.communicate(input=text.encode("utf-8"))\r
            return p.returncode == 0\r
        p = subprocess.Popen(["xclip", "-selection", "clipboard"], stdin=subprocess.PIPE)\r
        p.communicate(input=text.encode("utf-8"))\r
        return p.returncode == 0\r
    except Exception:\r
        return False\r
\r
def cap_read_clipboard(ctx: ActionContext) -> dict:\r
    text = _clipboard_get()\r
    if text is None:\r
        return {"ok": False, "error": "clipboard_unavailable"}\r
    if len(text) > CLIPBOARD_MAX_CHARS:\r
        text = text[:CLIPBOARD_MAX_CHARS]\r
    return {"ok": True, "text": text, "chars": len(text)}\r
\r
def cap_write_clipboard(ctx: ActionContext) -> dict:\r
    text = ctx.payload.get("text", "")\r
    if not isinstance(text, str):\r
        return {"ok": False, "error": "bad_text"}\r
    if len(text) > CLIPBOARD_MAX_CHARS:\r
        return {"ok": False, "error": "text_too_large"}\r
    ok = _clipboard_set(text)\r
    return {"ok": ok, "chars": len(text)} if ok else {"ok": False, "error": "clipboard_write_failed"}\r
\r
def cap_download_url_to_folder(ctx: ActionContext) -> dict:\r
    url = ctx.payload.get("url", "")\r
    ok, reason = url_is_allowed(url)\r
    if not ok:\r
        return {"ok": False, "error": "url_not_allowed", "reason": reason}\r
    folder_raw = ctx.payload.get("folder") or str(DOWNLOAD_DIR)\r
    folder = Path(folder_raw)\r
    if not path_is_allowed(folder):\r
        return {"ok": False, "error": "folder_not_allowed"}\r
    folder.mkdir(parents=True, exist_ok=True)\r
    filename = ctx.payload.get("filename")\r
    if not filename:\r
        parsed = urllib.parse.urlparse(url)\r
        filename = Path(parsed.path).name or f"download_{ctx.action_id}.bin"\r
    # sanitize\r
    filename = re.sub(r"[^A-Za-z0-9._\\-]", "_", filename)[:200]\r
    out = folder / filename\r
    try:\r
        with requests.get(url, stream=True, timeout=HTTP_TIMEOUT, headers=PUBLIC_DOWNLOAD_HEADERS, allow_redirects=True) as r:\r
            r.raise_for_status()\r
            total = 0\r
            with out.open("wb") as f:\r
                for chunk in r.iter_content(chunk_size=65_536):\r
                    if not chunk:\r
                        continue\r
                    total += len(chunk)\r
                    if total > DOWNLOAD_MAX_BYTES:\r
                        f.close()\r
                        out.unlink(missing_ok=True)\r
                        return {"ok": False, "error": "size_cap_exceeded"}\r
                    f.write(chunk)\r
        return {"ok": True, "path": str(out), "bytes": total}\r
    except Exception as e:\r
        return {"ok": False, "error": "download_failed", "detail": str(e)}\r
\r
try:\r
    from meta_credentials import meta_status  # type: ignore\r
except Exception:  # pragma: no cover\r
    meta_status = None  # type: ignore\r
\r
try:\r
    from meta_publisher import (  # type: ignore\r
        publish_text as _meta_publish_text,\r
        publish_photo as _meta_publish_photo,\r
        publish_video as _meta_publish_video,\r
        publish_reel as _meta_publish_reel,\r
        get_post_metrics as _meta_get_post_metrics,\r
        refresh_long_lived_token as _meta_refresh_token,\r
        recent_log as _meta_recent_log,\r
    )\r
except Exception:  # pragma: no cover\r
    _meta_publish_text = None  # type: ignore\r
    _meta_publish_photo = None  # type: ignore\r
    _meta_publish_video = None  # type: ignore\r
    _meta_publish_reel = None  # type: ignore\r
    _meta_get_post_metrics = None  # type: ignore\r
    _meta_refresh_token = None  # type: ignore\r
    _meta_recent_log = None  # type: ignore\r
\r
\r
def _meta_guard(fn) -> dict | None:\r
    if fn is None:\r
        return {"ok": False, "error": "meta_publisher_missing"}\r
    return None\r
\r
\r
def cap_meta_status(ctx: ActionContext) -> dict:\r
    if meta_status is None:\r
        return {"ok": False, "error": "meta_helper_missing"}\r
    return meta_status()\r
\r
\r
def cap_meta_publish(ctx: ActionContext) -> dict:\r
    guard = _meta_guard(_meta_publish_text)\r
    if guard:\r
        return guard\r
    message = (ctx.payload.get("message") or "").strip()\r
    if not message:\r
        return {"ok": False, "error": "empty_message"}\r
    if len(message) > 8000:\r
        return {"ok": False, "error": "message_too_long"}\r
    return _meta_publish_text(message, link=ctx.payload.get("link"))\r
\r
\r
def cap_meta_publish_photo(ctx: ActionContext) -> dict:\r
    guard = _meta_guard(_meta_publish_photo)\r
    if guard:\r
        return guard\r
    path = ctx.payload.get("image_path") or ctx.payload.get("path")\r
    if not path:\r
        return {"ok": False, "error": "missing_image_path"}\r
    p = Path(path)\r
    if not path_is_allowed(p):\r
        return {"ok": False, "error": "path_not_allowed"}\r
    return _meta_publish_photo(\r
        str(p),\r
        caption=ctx.payload.get("caption"),\r
        published=bool(ctx.payload.get("published", True)),\r
    )\r
\r
\r
def cap_meta_publish_video(ctx: ActionContext) -> dict:\r
    guard = _meta_guard(_meta_publish_video)\r
    if guard:\r
        return guard\r
    path = ctx.payload.get("video_path") or ctx.payload.get("path")\r
    if not path:\r
        return {"ok": False, "error": "missing_video_path"}\r
    p = Path(path)\r
    if not path_is_allowed(p):\r
        return {"ok": False, "error": "path_not_allowed"}\r
    return _meta_publish_video(\r
        str(p),\r
        description=ctx.payload.get("description"),\r
        title=ctx.payload.get("title"),\r
    )\r
\r
\r
def cap_meta_publish_reel(ctx: ActionContext) -> dict:\r
    guard = _meta_guard(_meta_publish_reel)\r
    if guard:\r
        return guard\r
    path = ctx.payload.get("video_path") or ctx.payload.get("path")\r
    if not path:\r
        return {"ok": False, "error": "missing_video_path"}\r
    p = Path(path)\r
    if not path_is_allowed(p):\r
        return {"ok": False, "error": "path_not_allowed"}\r
    return _meta_publish_reel(str(p), description=ctx.payload.get("description"))\r
\r
\r
def cap_meta_post_metrics(ctx: ActionContext) -> dict:\r
    guard = _meta_guard(_meta_get_post_metrics)\r
    if guard:\r
        return guard\r
    post_id = ctx.payload.get("post_id")\r
    if not post_id:\r
        return {"ok": False, "error": "missing_post_id"}\r
    return _meta_get_post_metrics(post_id)\r
\r
\r
def cap_meta_refresh_token(ctx: ActionContext) -> dict:\r
    guard = _meta_guard(_meta_refresh_token)\r
    if guard:\r
        return guard\r
    return _meta_refresh_token()\r
\r
\r
def cap_meta_recent_log(ctx: ActionContext) -> dict:\r
    guard = _meta_guard(_meta_recent_log)\r
    if guard:\r
        return guard\r
    try:\r
        limit = int(ctx.payload.get("limit", 50))\r
    except Exception:\r
        limit = 50\r
    limit = max(1, min(limit, 500))\r
    return _meta_recent_log(limit=limit)\r
\r
\r
try:\r
    from meta_autopilot import (  # type: ignore\r
        autopilot_publish as _meta_autopilot_publish,\r
        list_holds as _meta_list_holds,\r
        list_alerts as _meta_list_alerts,\r
        list_history as _meta_list_history,\r
        release_hold as _meta_release_hold,\r
        classify as _meta_classify,\r
    )\r
except Exception:  # pragma: no cover\r
    _meta_autopilot_publish = None  # type: ignore\r
    _meta_list_holds = None  # type: ignore\r
    _meta_list_alerts = None  # type: ignore\r
    _meta_list_history = None  # type: ignore\r
    _meta_release_hold = None  # type: ignore\r
    _meta_classify = None  # type: ignore\r
\r
\r
def cap_meta_autopilot_publish(ctx: ActionContext) -> dict:\r
    if _meta_autopilot_publish is None:\r
        return {"ok": False, "error": "meta_autopilot_missing"}\r
    payload = ctx.payload\r
    message = (payload.get("message") or "").strip()\r
    if not message and payload.get("format", "text") == "text":\r
        return {"ok": False, "error": "empty_message"}\r
    if len(message) > 8000:\r
        return {"ok": False, "error": "message_too_long"}\r
    # Validate any paths through the existing allow-list\r
    for key in ("image_path", "video_path"):\r
        v = payload.get(key)\r
        if v and not path_is_allowed(Path(v)):\r
            return {"ok": False, "error": f"{key}_not_allowed"}\r
    return _meta_autopilot_publish(\r
        message=message,\r
        format=payload.get("format", "text"),\r
        image_path=payload.get("image_path"),\r
        video_path=payload.get("video_path"),\r
        link=payload.get("link"),\r
        title=payload.get("title"),\r
        source_id=payload.get("source_id"),\r
        force=bool(payload.get("force", False)),\r
    )\r
\r
\r
def cap_meta_autopilot_holds(ctx: ActionContext) -> dict:\r
    if _meta_list_holds is None:\r
        return {"ok": False, "error": "meta_autopilot_missing"}\r
    return _meta_list_holds(limit=int(ctx.payload.get("limit", 50)))\r
\r
\r
def cap_meta_autopilot_alerts(ctx: ActionContext) -> dict:\r
    if _meta_list_alerts is None:\r
        return {"ok": False, "error": "meta_autopilot_missing"}\r
    return _meta_list_alerts(limit=int(ctx.payload.get("limit", 50)))\r
\r
\r
def cap_meta_autopilot_history(ctx: ActionContext) -> dict:\r
    if _meta_list_history is None:\r
        return {"ok": False, "error": "meta_autopilot_missing"}\r
    return _meta_list_history(limit=int(ctx.payload.get("limit", 100)))\r
\r
\r
def cap_meta_autopilot_release(ctx: ActionContext) -> dict:\r
    if _meta_release_hold is None:\r
        return {"ok": False, "error": "meta_autopilot_missing"}\r
    hold_id = ctx.payload.get("hold_id")\r
    if not hold_id:\r
        return {"ok": False, "error": "missing_hold_id"}\r
    return _meta_release_hold(hold_id)\r
\r
\r
def cap_meta_autopilot_classify(ctx: ActionContext) -> dict:\r
    """Dry-run sensitivity classifier — does not publish."""\r
    if _meta_classify is None:\r
        return {"ok": False, "error": "meta_autopilot_missing"}\r
    text = (ctx.payload.get("text") or "").strip()\r
    if not text:\r
        return {"ok": False, "error": "empty_text"}\r
    return {"ok": True, **_meta_classify(text)}\r
\r
\r
# Social account onboarding (lawful, human-verified — see social_onboarding.py)\r
try:\r
    from social_onboarding import (  # type: ignore\r
        social_platform_status as _social_platform_status,\r
        social_open_signup as _social_open_signup,\r
        social_profile_draft as _social_profile_draft,\r
        social_key_capture as _social_key_capture,\r
        social_connection_test as _social_connection_test,\r
        social_readiness_report as _social_readiness_report,\r
        social_pages_discover as _social_pages_discover,\r
        social_pages_test as _social_pages_test,\r
    )\r
except Exception:  # pragma: no cover\r
    _social_platform_status = None  # type: ignore\r
    _social_open_signup = None  # type: ignore\r
    _social_profile_draft = None  # type: ignore\r
    _social_key_capture = None  # type: ignore\r
    _social_connection_test = None  # type: ignore\r
    _social_readiness_report = None  # type: ignore\r
    _social_pages_discover = None  # type: ignore\r
    _social_pages_test = None  # type: ignore\r
\r
\r
def _social_guard(fn):\r
    if fn is None:\r
        return {"ok": False, "error": "social_onboarding_missing"}\r
    return None\r
\r
\r
def cap_social_platform_status(ctx: ActionContext) -> dict:\r
    g = _social_guard(_social_platform_status)\r
    return g or _social_platform_status(ctx.payload)\r
\r
\r
def cap_social_open_signup(ctx: ActionContext) -> dict:\r
    g = _social_guard(_social_open_signup)\r
    return g or _social_open_signup(ctx.payload)\r
\r
\r
def cap_social_profile_draft(ctx: ActionContext) -> dict:\r
    g = _social_guard(_social_profile_draft)\r
    return g or _social_profile_draft(ctx.payload)\r
\r
\r
def cap_social_key_capture(ctx: ActionContext) -> dict:\r
    g = _social_guard(_social_key_capture)\r
    return g or _social_key_capture(ctx.payload)\r
\r
\r
def cap_social_connection_test(ctx: ActionContext) -> dict:\r
    g = _social_guard(_social_connection_test)\r
    return g or _social_connection_test(ctx.payload)\r
\r
\r
def cap_social_readiness_report(ctx: ActionContext) -> dict:\r
    g = _social_guard(_social_readiness_report)\r
    return g or _social_readiness_report(ctx.payload)\r
\r
\r
def cap_social_pages_discover(ctx: ActionContext) -> dict:\r
    g = _social_guard(_social_pages_discover)\r
    return g or _social_pages_discover(ctx.payload)\r
\r
\r
def cap_social_pages_test(ctx: ActionContext) -> dict:\r
    g = _social_guard(_social_pages_test)\r
    return g or _social_pages_test(ctx.payload)\r
\r
\r
# Meta Autofix (browser_session + invoke_edge_function) — dry-run scaffold\r
try:\r
    from meta_autofix_handlers import (  # type: ignore\r
        dispatch_browser_session as _autofix_browser,\r
        dispatch_invoke_edge_function as _autofix_invoke_edge,\r
        recent_autofix_history as _autofix_history,\r
    )\r
except Exception:  # pragma: no cover\r
    _autofix_browser = None  # type: ignore\r
    _autofix_invoke_edge = None  # type: ignore\r
    _autofix_history = None  # type: ignore\r
\r
\r
def cap_browser_session(ctx: ActionContext) -> dict:\r
    if _autofix_browser is None:\r
        return {"ok": False, "error": "meta_autofix_handlers_missing"}\r
    payload = dict(ctx.payload or {})\r
    payload.setdefault("action_type", ctx.action_type)\r
    return _autofix_browser(payload, action_type=ctx.action_type)\r
\r
\r
def cap_invoke_edge_function(ctx: ActionContext) -> dict:\r
    if _autofix_invoke_edge is None:\r
        return {"ok": False, "error": "meta_autofix_handlers_missing"}\r
    return _autofix_invoke_edge(ctx.payload)\r
\r
\r
def cap_secret_rotate(ctx: ActionContext) -> dict:\r
    """Rotate an allow-listed operational token end-to-end on Ground Zero.\r
\r
    Generates the value locally, publishes only its SHA-256 fingerprint to the\r
    backend, pushes it to the GitHub Actions repo secret via authenticated gh\r
    (stdin, never argv), writes the non-versioned local test env file, runs the\r
    integration suite, and returns NON-SECRET receipts only.\r
    """\r
    try:\r
        from secret_rotate import rotate as _rotate  # type: ignore\r
    except Exception as exc:\r
        return {"ok": False, "error": "secret_rotate_module_missing", "detail": str(exc)}\r
    out = _rotate(dict(ctx.payload or {}))\r
    out["companion_version"] = COMPANION_VERSION\r
    return out\r
\r
\r
def cap_integration_onboard(ctx: ActionContext) -> dict:\r
    """Standing Integration & Credential Manager pass.\r
\r
    Claims due integration tasks (discover / acquire / install / connect /\r
    test / maintain / rotate / expand) and executes them end-to-end. Plaintext\r
    credentials never leave Ground Zero; only fingerprints are published.\r
    """\r
    try:\r
        from integration_manager import run as _run  # type: ignore\r
    except Exception as exc:\r
        return {"ok": False, "error": "integration_manager_module_missing", "detail": str(exc)}\r
    out = _run(dict(ctx.payload or {}))\r
    out["companion_version"] = COMPANION_VERSION\r
    return out\r
\r
\r
\r
\r
# --- Google Drive credential provisioning (credit-independent media engine) --\r
def cap_google_credential_provision(ctx: ActionContext) -> dict:\r
    """Mint a direct Google Drive credential using Jason's signed-in profile.\r
\r
    Removes the last Lovable-credit dependency in the media engine: the\r
    platform's drive-access layer prefers a direct service-account credential\r
    and only falls back to the connector gateway. Runs headless; stops at any\r
    human-only gate (login, MFA, billing, ToS) with a reason code.\r
    """\r
    try:\r
        from google_credential_provision import provision as _provision  # type: ignore\r
    except Exception as exc:\r
        return {"ok": False, "error": "google_credential_module_missing", "detail": str(exc)}\r
    payload = dict(ctx.payload or {})\r
    mode = str(payload.get("mode") or "service_account").strip()\r
    if mode != "service_account":\r
        # Probe and interactive sign-in never carry a private-key payload.\r
        out = _provision(payload)\r
        out.pop("credential_json", None)\r
        return out\r
\r
    # The native capability must never return raw provision() results into the\r
    # desktop_action_requests queue. Install directly in Project K and return\r
    # only a nonsecret, server-acknowledged result.\r
    try:\r
        from google_credential_install import install_provisioned as _install  # type: ignore\r
    except Exception:\r
        return {"ok": False, "stage": "install", "blocker_reason_code": "credential_installer_unavailable"}\r
    return _install(_provision(payload))\r
\r
\r
# --- Paperwork autofill (Unk fills forms; Jason only clears real gates) ----\r
def cap_browser_portal_login(ctx: ActionContext) -> dict:\r
    """Create, sign in to, or resume a funder-portal account/session.\r
\r
    Delegates to portal_login_worker.py, which fetches credentials one-time from\r
    the vault and never accepts legal terms, signs/certifies, pays, or submits.\r
    """\r
    mode_by_action = {\r
        "portal_register_account": "register",\r
        "portal_session_login": "login",\r
        "portal_session_resume": "resume",\r
    }\r
    mode = mode_by_action.get(ctx.action_type)\r
    if not mode:\r
        return {"ok": False, "error": "unsupported_action_type", "action_type": ctx.action_type}\r
\r
    worker = Path(__file__).with_name("portal_login_worker.py")\r
    if not worker.exists():\r
        return {"ok": False, "error": "portal_login_worker_missing"}\r
\r
    payload = dict(ctx.payload or {})\r
    if mode == "register" and not payload.get("registration_receipt_id"):\r
        return {"ok": False, "error": "registration_receipt_id_required"}\r
    if mode in ("login", "resume") and not payload.get("portal_session_id"):\r
        return {"ok": False, "error": "portal_session_id_required"}\r
\r
    # Pass the already-enrolled Ground Zero identity to the child in memory\r
    # only. It never appears in the action payload, command line, result, or log.\r
    device_credentials = load_credentials()\r
    if not device_credentials:\r
        return {"ok": False, "error": "device_credentials_unavailable"}\r
    device_id, device_key = device_credentials\r
    child_env = os.environ.copy()\r
    child_env["UNK_DEVICE_ID"] = device_id\r
    child_env["UNK_DEVICE_KEY"] = device_key\r
    child_env["SUPABASE_ANON_KEY"] = SUPABASE_ANON_KEY\r
\r
    tmp = Path(tempfile.gettempdir()) / f"portal_login_{ctx.action_id}.json"\r
    try:\r
        tmp.write_text(json.dumps(payload), encoding="utf-8")\r
        cmd = [sys.executable, str(worker), "--mode", mode, "--payload-file", str(tmp)]\r
        if os.name == "nt":\r
            cmd.append("--headed")\r
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=1800, env=child_env)\r
        try:\r
            result = json.loads((proc.stdout or "").strip() or "{}")\r
        except Exception:\r
            result = {}\r
        if not result:\r
            return {\r
                "ok": False,\r
                "error": "worker_no_result",\r
                "exit_code": proc.returncode,\r
                "stderr": (proc.stderr or "")[-2000:],\r
            }\r
        result["exit_code"] = proc.returncode\r
        result["companion_version"] = COMPANION_VERSION\r
        return result\r
    except subprocess.TimeoutExpired:\r
        return {"ok": False, "error": "portal_login_timeout", "mode": mode}\r
    except Exception as exc:\r
        return {"ok": False, "error": str(exc)[:400], "mode": mode}\r
    finally:\r
        # Remove the device key from the child environment copy immediately.\r
        child_env.pop("UNK_DEVICE_KEY", None)\r
        device_key = None\r
        try:\r
            tmp.unlink(missing_ok=True)\r
        except Exception:\r
            pass\r
\r
def cap_form_autofill(ctx: ActionContext) -> dict:\r
    """Fill a paperwork form autonomously and return a structured receipt.\r
\r
    Runs HEADLESSLY unless the cloud explicitly sets allow_human_gate=true,\r
    which it only does once per gate. That is what stops partially completed\r
    forms from reopening on Jason's desktop over and over.\r
    """\r
    try:\r
        from form_autofill import autofill as _autofill, dry_run as _autofill_dry  # type: ignore\r
    except Exception as exc:\r
        return {"ok": False, "error": "form_autofill_module_missing", "detail": str(exc)}\r
\r
    payload = dict(ctx.payload or {})\r
    url = str(payload.get("url") or "").strip()\r
    if not url:\r
        return {"ok": False, "error": "missing_url"}\r
    allowed, reason = url_is_allowed(url)\r
    if not allowed:\r
        return {"ok": False, "error": f"url_not_allowed:{reason}", "url": url}\r
\r
    kwargs = {\r
        "url": url,\r
        "fields": payload.get("fields") or [],\r
        "attachments": payload.get("attachments") or [],\r
        "save_selectors": payload.get("save_selectors") or [],\r
        "allow_human_gate": bool(payload.get("allow_human_gate")),\r
        "task_id": payload.get("task_id"),\r
    }\r
    result = _autofill_dry(url=url, fields=kwargs["fields"]) if payload.get("dry_run") \\\r
        else _autofill(**kwargs)\r
    result["companion_version"] = COMPANION_VERSION\r
    return result\r
\r
\r
def cap_meta_autofix_history(ctx: ActionContext) -> dict:\r
    if _autofix_history is None:\r
        return {"ok": False, "error": "meta_autofix_handlers_missing"}\r
    return _autofix_history(limit=int(ctx.payload.get("limit", 50)))\r
\r
\r
# --- Browser-driven Facebook Page publisher (Option 1 launch path) ---------\r
try:\r
    from meta_browser_publisher import (  # type: ignore\r
        publish_facebook_page as _browser_publish_fb,\r
        PAGE_URLS as _FB_PAGE_URLS,\r
        open_signin as _browser_open_signin,\r
        open_signin_platform as _browser_open_signin_platform,\r
        preflight_platform_auth as _browser_preflight_platform,\r
    )\r
except Exception:  # pragma: no cover\r
    _browser_publish_fb = None  # type: ignore\r
    _FB_PAGE_URLS = {}  # type: ignore\r
    _browser_open_signin = None  # type: ignore\r
    _browser_open_signin_platform = None  # type: ignore\r
    _browser_preflight_platform = None  # type: ignore\r
\r
\r
\r
try:\r
    from multi_platform_publisher import (  # type: ignore\r
        publish_facebook_reel as _publish_fb_reel,\r
        publish_instagram_feed as _publish_ig_feed,\r
        publish_instagram_reel as _publish_ig_reel,\r
        publish_linkedin as _publish_linkedin,\r
        publish_youtube_short as _publish_yt_short,\r
        recover_linkedin_permalink as _recover_linkedin_permalink,\r
        harvest_linkedin_profile_posts as _harvest_linkedin_posts,\r
    )\r
except Exception:  # pragma: no cover\r
    _publish_fb_reel = None  # type: ignore\r
    _publish_ig_feed = None  # type: ignore\r
    _publish_ig_reel = None  # type: ignore\r
    _publish_linkedin = None  # type: ignore\r
    _publish_yt_short = None  # type: ignore\r
    _recover_linkedin_permalink = None  # type: ignore\r
    _harvest_linkedin_posts = None  # type: ignore\r
\r
\r
\r
\r
def _post_browser_publish_receipt(job_id: str, outcome: str, res: dict) -> None:\r
    """POST the receipt back to the browser-publish-result edge function."""\r
    try:\r
        creds = load_credentials()\r
        if not creds:\r
            return\r
        device_id, device_key = creds\r
\r
        body = {\r
            "job_id": job_id,\r
            "outcome": outcome,\r
            "published_post_url": res.get("post_url"),\r
            "screenshot_path": res.get("screenshot_path"),\r
            "error": res.get("error"),\r
            "receipt": {\r
                "notes": res.get("notes", []),\r
                "diagnostics": res.get("diagnostics"),\r
                "detail": res.get("detail"),\r
                "trace": res.get("trace"),\r
                "stderr_tail": res.get("stderr_tail"),\r
                "exit_code": res.get("exit_code"),\r
            },\r
        }\r
        requests.post(\r
            f"{FUNCTIONS_BASE}/browser-publish-result",\r
            headers={\r
                "apikey": SUPABASE_ANON_KEY,\r
                "Content-Type": "application/json",\r
                "x-device-id": device_id,\r
                "x-device-key": device_key,\r
            },\r
            json=body,\r
            timeout=20,\r
        )\r
    except Exception as e:  # pragma: no cover\r
        log(f"[browser_publish] receipt post failed: {e}")\r
\r
\r
def _return_publish(ctx: ActionContext, res: dict) -> dict:\r
    job_id = str((ctx.payload or {}).get("job_id") or "")\r
    if job_id:\r
        _post_browser_publish_receipt(job_id, "published" if res.get("ok") else "failed", res)\r
    detail = res.get("detail")\r
    if detail is None:\r
        detail = res.get("trace")\r
    return {\r
        "ok": bool(res.get("ok")),\r
        "post_url": res.get("post_url"),\r
        "screenshot_path": res.get("screenshot_path"),\r
        "error": res.get("error"),\r
        "detail": detail,\r
        "trace": res.get("trace"),\r
        "stdout_tail": res.get("stdout_tail"),\r
        "stderr_tail": res.get("stderr_tail"),\r
        "exit_code": res.get("exit_code"),\r
        "notes": res.get("notes", []),\r
        "diagnostics": res.get("diagnostics"),\r
    }\r
\r
\r
def cap_browser_publish_facebook(ctx: ActionContext) -> dict:\r
    if _browser_publish_fb is None:\r
        return {"ok": False, "error": "meta_browser_publisher_missing"}\r
    payload = ctx.payload or {}\r
    if not payload.get("job_id"):\r
        return {"ok": False, "error": "missing_job_id"}\r
\r
    direct_failure = str(payload.get("direct_publish_failure") or "")\r
    credential_failure_needles = (\r
        "pages_read_engagement",\r
        "pages_manage_posts",\r
        "Missing Meta Page credential",\r
        "Error validating access token",\r
        "Session has expired",\r
        "OAuthException",\r
    )\r
    if any(needle in direct_failure for needle in credential_failure_needles):\r
        repair_notes: list[str] = [f"direct_publish_failed_repairing_token:{direct_failure[:240]}"]\r
        repaired = False\r
        if _configure_meta is not None:\r
            try:\r
                repair = _configure_meta(\r
                    preferred_page_name=str(payload.get("destination_label") or "J. Fortitude"),\r
                    app_id=payload.get("meta_app_id"),\r
                )\r
                if not isinstance(repair, dict):\r
                    repair = {"ok": False, "error": "meta_configure_returned_non_object", "detail": repr(repair)}\r
                repaired = bool(repair.get("ok"))\r
                repair_notes.append(f"meta_configure_ok={repaired}")\r
                repair_notes.extend([f"meta_configure:{n}" for n in repair.get("notes", [])[:8]])\r
                repair_notes.extend(_sync_configured_meta_token_to_backend(repair))\r
                missing = repair.get("missing_permissions") or []\r
                if missing:\r
                    return _return_publish(ctx, {\r
                        "ok": False,\r
                        "error": "meta_token_missing_required_permissions",\r
                        "notes": repair_notes + [f"missing_permissions:{','.join(map(str, missing))}", "blocked_browser_fallback_until_token_is_publishable"],\r
                        "diagnostics": {"missing_permissions": missing, "repair_error": repair.get("error")},\r
                    })\r
            except Exception as repair_exc:\r
                repair_notes.append(f"meta_configure_exception:{repair_exc}")\r
        else:\r
            repair_notes.append("meta_configure_unavailable")\r
\r
        if repaired and _meta_publish_text is not None:\r
            try:\r
                msg = str(payload.get("message") or payload.get("title") or "").strip()\r
                if msg:\r
                    api_res = _meta_publish_text(msg, link=payload.get("link_url"))\r
                    if not isinstance(api_res, dict):\r
                        api_res = {"ok": False, "error": "meta_publish_returned_non_object", "detail": repr(api_res)}\r
                    if api_res.get("ok"):\r
                        post_id = api_res.get("post_id")\r
                        res = {\r
                            "ok": True,\r
                            "post_url": f"https://www.facebook.com/{post_id}" if post_id else None,\r
                            "notes": repair_notes + ["published_after_meta_token_repair", f"post_id={post_id}"],\r
                        }\r
                        return _return_publish(ctx, res)\r
                    repair_notes.append(f"post_repair_api_failed:{api_res.get('error') or api_res.get('body') or api_res.get('status')}")\r
            except Exception as api_exc:\r
                repair_notes.append(f"post_repair_api_exception:{api_exc}")\r
        return _return_publish(ctx, {\r
            "ok": False,\r
            "error": "meta_token_repair_required",\r
            "notes": repair_notes + ["blocked_browser_fallback_for_meta_credential_failure"],\r
            "diagnostics": {"direct_publish_failure": direct_failure[:500]},\r
        })\r
\r
    res = _run_browser_publisher_isolated(\r
        _browser_publish_fb,\r
        page_slug=str(payload.get("page_slug") or "j-fortitude"),\r
        message=str(payload.get("message") or ""),\r
        link_url=payload.get("link_url"),\r
        image_url=payload.get("image_url"),\r
        video_url=payload.get("video_url"),\r
        page_url_override=payload.get("destination_url"),\r
    )\r
    if direct_failure:\r
        res.setdefault("notes", [])\r
        res["notes"] = repair_notes + res.get("notes", []) if 'repair_notes' in locals() else [f"direct_publish_failure:{direct_failure[:240]}"] + res.get("notes", [])\r
    return _return_publish(ctx, res)\r
\r
\r
def cap_browser_signin_facebook(ctx: ActionContext) -> dict:\r
    """Open the persistent Chrome profile at Business Suite so Jason can sign\r
    in. Never posts; used to unblock composer_not_found / login_required."""\r
    if _browser_open_signin is None:\r
        return {"ok": False, "error": "meta_browser_publisher_missing"}\r
    p = ctx.payload or {}\r
    url = str(p.get("url") or "https://business.facebook.com/")\r
    if not (url.startswith("https://business.facebook.com") or url.startswith("https://www.facebook.com")):\r
        return {"ok": False, "error": "url_not_allowed", "url": url}\r
    timeout_seconds = int(p.get("timeout_seconds") or 600)\r
    return _browser_open_signin(url=url, timeout_seconds=timeout_seconds)\r
\r
\r
def _cap_browser_signin_generic(ctx: ActionContext, platform: str) -> dict:\r
    """Shared wrapper for Instagram / LinkedIn sign-in via Unk's persistent\r
    Playwright profile (the same PROFILE_DIR used by the publisher).\r
    Supports payload {sso_provider:'google', sso_email:'...'} to auto-click\r
    Continue-with-Google without typing passwords.\r
    """\r
    if _browser_open_signin_platform is None:\r
        return {"ok": False, "error": "meta_browser_publisher_missing"}\r
    p = ctx.payload or {}\r
    timeout_seconds = int(p.get("timeout_seconds") or p.get("timeout") or 900)\r
    sso_provider = p.get("sso_provider") or None\r
    sso_email = p.get("sso_email") or None\r
    expected_handle = p.get("expected_handle") or p.get("page_slug") or None\r
    force_logout = bool(p.get("force_logout"))\r
    # Visible browser windows are exceptional and must be explicitly requested\r
    # by a current human-gated action. Legacy/stale sign-in jobs stay silent.\r
    interactive = p.get("interactive") is True\r
    if not interactive:\r
        # An unattended sign-in cannot complete a human login. Keep it as a\r
        # bounded session diagnostic so it never monopolizes the single device\r
        # queue and starves grant coordination work.\r
        unattended_limit = int(p.get("unattended_timeout_seconds") or 30)\r
        timeout_seconds = min(timeout_seconds, max(5, unattended_limit))\r
    return _browser_open_signin_platform(\r
        platform=platform, timeout_seconds=timeout_seconds,\r
        sso_provider=sso_provider, sso_email=sso_email,\r
        expected_handle=expected_handle, force_logout=force_logout,\r
        interactive=interactive,\r
    )\r
\r
\r
\r
\r
def cap_browser_signin_instagram(ctx: ActionContext) -> dict:\r
    """Open the persistent Chromium profile at instagram.com/accounts/login/\r
    so Jason can sign in once. Cookies persist for the publisher."""\r
    return _cap_browser_signin_generic(ctx, "instagram")\r
\r
\r
def cap_browser_signin_linkedin(ctx: ActionContext) -> dict:\r
    """Open the persistent Chromium profile at linkedin.com/login so Jason\r
    can sign in once. Cookies persist for the publisher."""\r
    return _cap_browser_signin_generic(ctx, "linkedin")\r
\r
\r
def cap_rescue_windows(ctx: ActionContext) -> dict:\r
    """Drag every off-screen automation browser window back onto the visible\r
    desktop. Fixes 'the taskbar icon is there but clicking does nothing' —\r
    the window was parked at -32000,-32000 by the quiet-window sweeper."""\r
    try:\r
        from unk_window_policy import (\r
            allow_visible_window as _allow,\r
            rescue_offscreen_windows as _rescue,\r
            start_onscreen_rescue as _keep,\r
        )\r
    except Exception as exc:\r
        return {"ok": False, "error": f"window_policy_missing:{exc}"}\r
    hold = int((ctx.payload or {}).get("hold_seconds") or 900)\r
    _allow(True, hold)    # time-boxed hold; background tasks can't cancel it\r
    moved = _rescue(focus=True)\r
    _keep(hold)           # keep them on screen while Jason signs in\r
    return {"ok": True, "windows_restored": moved, "hold_seconds": hold}\r
\r
\r
\r
def cap_browser_preflight_platform(ctx: ActionContext) -> dict:\r
    """Prove that Unk's persistent profile is authenticated on a platform by\r
    launching a *fresh* persistent context and reading its cookies. Returns\r
    {ok, platform, authenticated, state, url, cookie_names[], cookie_count,\r
     sessionid_present|li_at_present, notes[]}. Never posts."""\r
    if _browser_preflight_platform is None:\r
        return {"ok": False, "error": "meta_browser_publisher_missing"}\r
    p = ctx.payload or {}\r
    platform = str(p.get("platform") or "").strip().lower()\r
    if platform not in ("instagram", "linkedin"):\r
        return {"ok": False, "error": "unsupported_platform", "platform": platform}\r
    dwell = int(p.get("dwell_seconds") or 4)\r
    return _browser_preflight_platform(platform=platform, dwell_seconds=dwell)\r
\r
\r
\r
\r
\r
\r
def _resolve_fb_page_url(payload: dict) -> str:\r
    return (\r
        payload.get("destination_url")\r
        or _FB_PAGE_URLS.get(str(payload.get("page_slug") or ""), "")\r
        or "https://www.facebook.com/"\r
    )\r
\r
\r
def _run_browser_publisher_isolated(fn: Callable[..., dict], **kwargs) -> dict:\r
    """Run Playwright sync publishers in a separate Python process.\r
\r
    The desktop companion can run under supervisors that keep asyncio state on\r
    the process. Playwright's sync API can still detect that state even when a\r
    handler is moved to a thread, so browser posting gets a clean interpreter.\r
    """\r
    worker = Path(__file__).resolve().parent / "browser_publish_worker.py"\r
    if not worker.exists():\r
        return {"ok": False, "error": "browser_worker_missing", "path": str(worker)}\r
    payload = {\r
        "module": getattr(fn, "__module__", ""),\r
        "function": getattr(fn, "__name__", ""),\r
        "kwargs": kwargs,\r
    }\r
    try:\r
        proc = subprocess.run(\r
            [sys.executable, str(worker)],\r
            input=json.dumps(payload),\r
            capture_output=True,\r
            text=True,\r
            timeout=45 * 60,\r
            cwd=str(worker.parent),\r
        )\r
        stdout = (proc.stdout or "").strip()\r
        stderr = (proc.stderr or "").strip()\r
        result: dict[str, Any]\r
        try:\r
            # Use the last JSON-looking line so incidental browser/process noise\r
            # does not destroy the result envelope.\r
            line = next((ln for ln in reversed(stdout.splitlines()) if ln.strip().startswith("{")), "")\r
            result = json.loads(line) if line else {}\r
        except Exception:\r
            result = {}\r
        if not result:\r
            result = {"ok": False, "error": "browser_worker_no_json_result"}\r
        result.setdefault("exit_code", proc.returncode)\r
        if stdout:\r
            result.setdefault("stdout_tail", stdout[-4000:])\r
        if stderr:\r
            result.setdefault("stderr_tail", stderr[-4000:])\r
        if proc.returncode not in (0, 2) and result.get("ok") is not True:\r
            result.setdefault("error", "browser_worker_failed")\r
        return result\r
    except subprocess.TimeoutExpired as exc:\r
        return {\r
            "ok": False,\r
            "error": "browser_worker_timeout",\r
            "stdout_tail": (exc.stdout or "")[-4000:] if isinstance(exc.stdout, str) else None,\r
            "stderr_tail": (exc.stderr or "")[-4000:] if isinstance(exc.stderr, str) else None,\r
        }\r
    except Exception as exc:\r
        return {"ok": False, "error": "browser_worker_launch_exception", "detail": str(exc), "trace": traceback.format_exc(limit=6)}\r
\r
\r
def cap_browser_publish_facebook_reel(ctx: ActionContext) -> dict:\r
    if _publish_fb_reel is None:\r
        return {"ok": False, "error": "multi_platform_publisher_missing"}\r
    p = ctx.payload or {}\r
    if not p.get("video_url"):\r
        return {"ok": False, "error": "video_url_required"}\r
    res = _run_browser_publisher_isolated(\r
        _publish_fb_reel,\r
        page_url=_resolve_fb_page_url(p),\r
        video_url=str(p.get("video_url")),\r
        message=str(p.get("message") or p.get("title") or ""),\r
    )\r
    return _return_publish(ctx, res)\r
\r
\r
def cap_browser_publish_instagram(ctx: ActionContext) -> dict:\r
    if _publish_ig_feed is None:\r
        return {"ok": False, "error": "multi_platform_publisher_missing"}\r
    p = ctx.payload or {}\r
    res = _run_browser_publisher_isolated(\r
        _publish_ig_feed,\r
        image_url=p.get("image_url"),\r
        video_url=p.get("video_url"),\r
        message=str(p.get("message") or p.get("title") or ""),\r
    )\r
    return _return_publish(ctx, res)\r
\r
\r
def cap_browser_publish_instagram_reel(ctx: ActionContext) -> dict:\r
    if _publish_ig_reel is None:\r
        return {"ok": False, "error": "multi_platform_publisher_missing"}\r
    p = ctx.payload or {}\r
    if not p.get("video_url"):\r
        return {"ok": False, "error": "video_url_required"}\r
    res = _run_browser_publisher_isolated(\r
        _publish_ig_reel,\r
        video_url=str(p.get("video_url")),\r
        message=str(p.get("message") or p.get("title") or ""),\r
    )\r
    return _return_publish(ctx, res)\r
\r
\r
def cap_browser_publish_linkedin(ctx: ActionContext) -> dict:\r
    if _publish_linkedin is None:\r
        return {"ok": False, "error": "multi_platform_publisher_missing"}\r
    p = ctx.payload or {}\r
    res = _run_browser_publisher_isolated(\r
        _publish_linkedin,\r
        destination_url=p.get("destination_url"),\r
        message=str(p.get("message") or p.get("title") or ""),\r
        image_url=p.get("image_url"),\r
        video_url=p.get("video_url"),\r
        expected_handle=p.get("expected_handle") or p.get("page_slug"),\r
    )\r
    return _return_publish(ctx, res)\r
\r
\r
def cap_recover_linkedin_permalink(ctx: ActionContext) -> dict:\r
    """Post-hoc LinkedIn permalink recovery for an already-submitted post.\r
    Never publishes. Only writes a canonical urn:li:activity URL + screenshot\r
    back to the target browser_publish_jobs row when it can be proven.\r
    """\r
    if _recover_linkedin_permalink is None:\r
        return {"ok": False, "error": "multi_platform_publisher_missing"}\r
    p = ctx.payload or {}\r
    job_id = str(p.get("job_id") or "").strip()\r
    if not job_id:\r
        return {"ok": False, "error": "job_id_required"}\r
    match_terms = p.get("match_terms") if isinstance(p.get("match_terms"), list) else None\r
    res = _run_browser_publisher_isolated(\r
        _recover_linkedin_permalink,\r
        match_title=str(p.get("match_title") or ""),\r
        match_terms=match_terms,\r
        profile_slug=p.get("profile_slug"),\r
        submitted_after_iso=p.get("submitted_after_iso"),\r
    )\r
    permalink = res.get("permalink") or res.get("post_url")\r
    # Post evidence-only or verified receipt back to the shared receipt endpoint.\r
    outcome = "verified_permalink" if (res.get("ok") and permalink and "urn:li:activity:" in str(permalink)) else "evidence_only"\r
    try:\r
        creds = load_credentials()\r
        if creds:\r
            device_id, device_key = creds\r
            body = {\r
                "job_id": job_id,\r
                "outcome": outcome,\r
                "published_post_url": permalink if outcome == "verified_permalink" else None,\r
                "screenshot_path": res.get("screenshot_path"),\r
                "error": res.get("error"),\r
                "receipt": {\r
                    "kind": "linkedin_permalink_recovery",\r
                    "notes": res.get("notes", []),\r
                    "candidates": res.get("candidates", []),\r
                    "matched_title": res.get("matched_title"),\r
                },\r
            }\r
            requests.post(\r
                f"{FUNCTIONS_BASE}/browser-publish-result",\r
                headers={\r
                    "apikey": SUPABASE_ANON_KEY,\r
                    "Content-Type": "application/json",\r
                    "x-device-id": device_id,\r
                    "x-device-key": device_key,\r
                },\r
                json=body,\r
                timeout=20,\r
            )\r
    except Exception as e:  # pragma: no cover\r
        log(f"[recover_linkedin_permalink] receipt post failed: {e}")\r
    return {\r
        "ok": bool(res.get("ok")),\r
        "outcome": outcome,\r
        "permalink": permalink,\r
        "screenshot_path": res.get("screenshot_path"),\r
        "error": res.get("error"),\r
        "notes": res.get("notes", []),\r
        "candidates": res.get("candidates", []),\r
        "matched_title": res.get("matched_title"),\r
    }\r
\r
\r
\r
def cap_browser_publish_youtube_short(ctx: ActionContext) -> dict:\r
    if _publish_yt_short is None:\r
        return {"ok": False, "error": "multi_platform_publisher_missing"}\r
    p = ctx.payload or {}\r
    if not p.get("video_url"):\r
        return {"ok": False, "error": "video_url_required"}\r
    res = _run_browser_publisher_isolated(\r
        _publish_yt_short,\r
        video_url=str(p.get("video_url")),\r
        title=str(p.get("title") or (p.get("message") or "")[:80] or "Untitled Short"),\r
        description=str(p.get("message") or ""),\r
    )\r
    return _return_publish(ctx, res)\r
\r
\r
# --- Browser-driven Meta credential configurator ---------------------------\r
try:\r
    from meta_browser_configurator import configure_meta_via_browser as _configure_meta  # type: ignore\r
except Exception:  # pragma: no cover\r
    _configure_meta = None  # type: ignore\r
\r
\r
def _sync_configured_meta_token_to_backend(res: dict) -> list[str]:\r
    notes: list[str] = []\r
    if not res.get("ok"):\r
        return notes\r
    try:\r
        from meta_credentials import load_meta_credentials  # type: ignore\r
        creds = load_meta_credentials() or {}\r
        page_id = str(creds.get("page_id") or res.get("page_id") or "")\r
        token = str(creds.get("page_access_token") or "")\r
        loaded = load_credentials()\r
        if page_id and token and loaded:\r
            device_id, device_key = loaded\r
            sync = requests.post(\r
                f"{FUNCTIONS_BASE}/meta-token-sync",\r
                headers={\r
                    "apikey": SUPABASE_ANON_KEY,\r
                    "Content-Type": "application/json",\r
                    "X-Device-Id": device_id,\r
                    "X-Device-Key": device_key,\r
                },\r
                json={\r
                    "fb_page_id": page_id,\r
                    "page_name": res.get("page_name") or "J. Fortitude",\r
                    "page_access_token": token,\r
                    "token_scopes": res.get("token_scopes") or [],\r
                    "trusted_source": "me_accounts",\r
                },\r
                timeout=30,\r
            )\r
            notes.append(f"backend_token_sync_http:{sync.status_code}")\r
            if sync.status_code >= 400:\r
                notes.append(f"backend_token_sync_failed:{sync.text[:300]}")\r
    except Exception as sync_exc:\r
        notes.append(f"backend_token_sync_exception:{sync_exc}")\r
    return notes\r
\r
\r
def cap_meta_app_dashboard_configure(ctx: ActionContext) -> dict:\r
    """Configure the Facebook Login for Business Settings for a given app_id.\r
    Toggles Client OAuth Login + Web OAuth Login ON and adds the redirect URI\r
    so subsequent meta_configure_via_browser calls can actually receive a\r
    token in the URL fragment. Runs in the persistent Unk browser profile."""\r
    payload = ctx.payload or {}\r
    app_id = (payload.get("meta_app_id") or "").strip()\r
    if not app_id:\r
        return {"ok": False, "error": "meta_app_id_required"}\r
    try:\r
        from meta_app_dashboard_configurator import configure_app_dashboard  # type: ignore\r
    except Exception as e:\r
        return {"ok": False, "error": f"module_missing:{e}"}\r
    redirect_uri = (payload.get("redirect_uri") or "").strip() or None\r
    return configure_app_dashboard(app_id=app_id, redirect_uri=redirect_uri)\r
\r
\r
def cap_meta_configure_via_browser(ctx: ActionContext) -> dict:\r
\r
    if _configure_meta is None:\r
        return {"ok": False, "error": "meta_browser_configurator_missing"}\r
    payload = ctx.payload or {}\r
    # Doctrine: auto-fix locally. If cloud pushed the app secret, persist it\r
    # into the same store meta_credentials reads from — no Jason .env edits.\r
    pushed_secret = (payload.get("meta_app_secret") or "").strip()\r
    if pushed_secret:\r
        try:\r
            from meta_key_capture import save_secret as _save_meta_secret  # type: ignore\r
            _save_meta_secret("META_APP_SECRET", pushed_secret)\r
        except Exception as _e:\r
            log(f"meta_app_secret_save_failed: %s" % _e)\r
    # Solve-first shortcut: if cloud pushed a Page token + Page ID AND that\r
    # token actually works against Graph API right now, persist it locally and\r
    # skip OAuth. If the token is dead (e.g. the Meta app was rebuilt and the\r
    # server-side secret is stale), fall through to real OAuth instead of\r
    # falsely reporting success.\r
    pushed_token = (payload.get("meta_page_access_token") or "").strip()\r
    pushed_page_id = (payload.get("meta_page_id") or "").strip()\r
    if pushed_token and pushed_page_id and pushed_page_id.isdecimal() and len(pushed_page_id) <= 40:\r
        try:\r
            import requests as _rq\r
            probe = _rq.get(\r
                f"https://graph.facebook.com/v25.0/{pushed_page_id}",\r
                params={"fields": "id,name"},\r
                headers={"Authorization": f"Bearer {pushed_token}"},\r
                timeout=15,\r
                allow_redirects=False,\r
            )\r
            probe_ok = probe.status_code == 200 and str((probe.json() or {}).get("id")) == pushed_page_id\r
        except Exception as pe:\r
            probe_ok = False\r
            log(f"meta_pushed_token_probe_failed: %s" % pe)\r
        if probe_ok:\r
            try:\r
                from meta_browser_configurator import _save_meta_credentials  # type: ignore\r
                save_info = _save_meta_credentials(\r
                    app_id=(payload.get("meta_app_id") or "").strip() or None,\r
                    configuration_id=(payload.get("meta_configuration_id") or "").strip() or None,\r
                    page_id=pushed_page_id,\r
                    page_access_token=pushed_token,\r
                )\r
                res = {\r
                    "ok": True,\r
                    "steps": [{"step": "seeded_from_cloud_secrets_after_probe", "ok": True}],\r
                    "notes": ["skipped_oauth_using_verified_cloud_credentials"],\r
                    "app_id": (payload.get("meta_app_id") or "").strip() or None,\r
                    "configuration_id": (payload.get("meta_configuration_id") or "").strip() or None,\r
                    "page_id": pushed_page_id,\r
                    "page_name": payload.get("preferred_page_name") or "J. Fortitude",\r
                    "page_access_token_preview": (pushed_token[:6] + "…" + pushed_token[-4:]) if len(pushed_token) > 12 else "***",\r
                    "save_info": save_info,\r
                    "app_secret_missing": not pushed_secret,\r
                }\r
                res["notes"].extend(_sync_configured_meta_token_to_backend(res))\r
                return res\r
            except Exception as e:\r
                log(f"meta_seed_from_cloud_failed: %s" % e)\r
                # Fall through to normal OAuth path below.\r
        else:\r
            log("meta_pushed_token_dead_falling_through_to_oauth")\r
\r
    # Preferred deterministic path: Facebook Login for Business code flow.\r
    # Opens the OAuth dialog, captures ?code=, and posts it to the\r
    # meta-oauth-exchange edge function which trades it (with META_APP_SECRET)\r
    # for a long-lived user token, discovers Pages, and writes the Page\r
    # access tokens directly into meta_page_credentials. This replaces the\r
    # fragile implicit-token + dashboard-scraping path.\r
    app_id_for_code = (payload.get("meta_app_id") or "").strip()\r
    if not app_id_for_code:\r
        try:\r
            from meta_browser_configurator import _load_existing_app_id  # type: ignore\r
            app_id_for_code = _load_existing_app_id() or ""\r
        except Exception:\r
            pass\r
    config_id_for_code = (payload.get("meta_configuration_id") or "").strip() or None\r
    if app_id_for_code:\r
        try:\r
            from meta_browser_configurator import oauth_capture_code  # type: ignore\r
            cap = oauth_capture_code(\r
                app_id=app_id_for_code,\r
                configuration_id=config_id_for_code,\r
            )\r
        except Exception as ce:\r
            cap = {"ok": False, "error": f"oauth_capture_code_exception:{ce}"}\r
        if cap.get("ok") and cap.get("code"):\r
            loaded = load_credentials()\r
            headers = {\r
                "apikey": SUPABASE_ANON_KEY,\r
                "Content-Type": "application/json",\r
            }\r
            if loaded:\r
                device_id, device_key = loaded\r
                headers["X-Device-Id"] = device_id\r
                headers["X-Device-Key"] = device_key\r
            try:\r
                exch = requests.post(\r
                    f"{FUNCTIONS_BASE}/meta-oauth-exchange",\r
                    headers=headers,\r
                    json={\r
                        "code": cap["code"],\r
                        "redirect_uri": cap.get("redirect_uri"),\r
                        "app_id": app_id_for_code,\r
                    },\r
                    timeout=60,\r
                )\r
                exch_body = {}\r
                try: exch_body = exch.json()\r
                except Exception: exch_body = {"raw": exch.text[:400]}\r
                return {\r
                    "ok": bool(exch_body.get("ok")),\r
                    "flow": "login_for_business_code_exchange",\r
                    "http_status": exch.status_code,\r
                    "app_id": app_id_for_code,\r
                    "configuration_id": config_id_for_code,\r
                    "exchange_result": exch_body,\r
                    "capture_notes": cap.get("notes"),\r
                    "capture_steps": cap.get("steps"),\r
                    "screenshot_path": cap.get("screenshot_path"),\r
                }\r
            except Exception as ee:\r
                return {\r
                    "ok": False,\r
                    "flow": "login_for_business_code_exchange",\r
                    "error": f"exchange_call_failed:{ee}",\r
                    "capture_notes": cap.get("notes"),\r
                }\r
        else:\r
            # Code capture failed — fall through to legacy path as backup.\r
            log(f"oauth_code_capture_failed:{cap.get('error')}")\r
\r
    res = _configure_meta(\r
        preferred_page_name=payload.get("preferred_page_name") or "J. Fortitude",\r
        app_id=payload.get("meta_app_id"),\r
        configuration_id=payload.get("meta_configuration_id"),\r
    )\r
    res.setdefault("notes", []).extend(_sync_configured_meta_token_to_backend(res))\r
    return res\r
\r
\r
\r
# ---------------------------------------------------------------------------\r
# Self-update + restart (Ground Zero remote maintenance)\r
# ---------------------------------------------------------------------------\r
\r
_RESTART_REQUESTED: dict[str, Any] = {"pending": False, "reason": "", "strategy": "execv"}\r
\r
def _companion_script_dir() -> Path:\r
    return Path(__file__).resolve().parent\r
\r
def cap_self_update(ctx: ActionContext) -> dict:\r
    """Download the latest desktop-companion ZIP and swap the source files.\r
\r
    Payload: { zip_url: str }. Backs up replaced files to ~/.unk-companion/backup-<ts>/\r
    and copies .py/.bat/.sh/.ps1/.md from the ZIP into the running install dir.\r
    A \`restart_companion\` action should follow to load the new code.\r
    """\r
    import io\r
    import shutil\r
    import zipfile\r
\r
    # Restart requests are routed through the self_update capability for\r
    # historical queue reasons; delegate them to the dedicated handler.\r
    if ctx.action_type == "restart_companion":\r
        return cap_restart_companion(ctx)\r
\r
    zip_url = (ctx.payload or {}).get("zip_url", "")\r
    if not isinstance(zip_url, str) or not zip_url.startswith(("http://", "https://")):\r
        return {"ok": False, "error": "bad_zip_url"}\r
\r
    if "pefatniumnrxwbgnwvvh" in zip_url.lower():\r
        return {"ok": False, "error": "retired_legacy_release_source"}\r
\r
    script_dir = _companion_script_dir()\r
    if not (script_dir / "unk_companion.py").exists():\r
        return {"ok": False, "error": "cannot_locate_install_dir", "dir": str(script_dir)}\r
\r
    try:\r
        # Cache-bust: some CDNs serve a stale object for the same path.\r
        bust_url = zip_url + ("&" if "?" in zip_url else "?") + f"cb={int(time.time())}"\r
        r = requests.get(bust_url, timeout=60, headers={"Cache-Control": "no-cache"})\r
        if r.status_code != 200:\r
            return {"ok": False, "error": "download_failed", "http": r.status_code}\r
        raw = r.content\r
        if len(raw) > 50 * 1024 * 1024:\r
            return {"ok": False, "error": "zip_too_large", "bytes": len(raw)}\r
\r
        import hashlib\r
        zip_sha256 = hashlib.sha256(raw).hexdigest()\r
        expect = (ctx.payload or {}).get("expect_zip_sha256")\r
        if expect and expect != zip_sha256:\r
            # Fail closed: we downloaded a different package than the one built.\r
            return {\r
                "ok": False,\r
                "error": "zip_hash_mismatch",\r
                "expected_sha256": expect,\r
                "downloaded_sha256": zip_sha256,\r
                "bytes": len(raw),\r
                "url": bust_url,\r
            }\r
\r
\r
        stage = COMPANION_DIR / f"update-stage-{int(time.time())}"\r
        stage.mkdir(parents=True, exist_ok=True)\r
        with zipfile.ZipFile(io.BytesIO(raw)) as zf:\r
            for name in zf.namelist():\r
                if name.startswith("/") or ".." in Path(name).parts:\r
                    shutil.rmtree(stage, ignore_errors=True)\r
                    return {"ok": False, "error": "bad_zip_entry", "entry": name}\r
            zf.extractall(stage)\r
\r
        entries = [p for p in stage.iterdir()]\r
        src_root = entries[0] if len(entries) == 1 and entries[0].is_dir() else stage\r
\r
        previous_build_ref = None\r
        try:\r
            if RUNNING_BUILD_FILE.exists():\r
                previous_build_ref = json.loads(RUNNING_BUILD_FILE.read_text()).get("build_ref")\r
        except Exception:\r
            previous_build_ref = None\r
\r
        backup = COMPANION_DIR / f"backup-{int(time.time())}"\r
        backup.mkdir(parents=True, exist_ok=True)\r
        swap_exts = {".py", ".bat", ".cmd", ".vbs", ".sh", ".ps1", ".md"}\r
        swapped: list[str] = []\r
        for src in src_root.rglob("*"):\r
            if not src.is_file() or src.suffix.lower() not in swap_exts:\r
                continue\r
            rel = src.relative_to(src_root)\r
            dst = script_dir / rel\r
            if dst.exists():\r
                bkp = backup / rel\r
                bkp.parent.mkdir(parents=True, exist_ok=True)\r
                shutil.copy2(dst, bkp)\r
            dst.parent.mkdir(parents=True, exist_ok=True)\r
            shutil.copy2(src, dst)\r
            swapped.append(str(rel))\r
\r
        # Converge legacy visible launchers before attempting scheduled-task\r
        # repair. Task registration may require elevation on older installs,\r
        # but the signed-in user can always stop their own stale CMD wrappers\r
        # and remove obsolete Startup shortcuts. Never stop Python workers or\r
        # Chrome here, so active Facebook publishing remains untouched.\r
        popup_cleanup_notes: list[str] = []\r
        if os.name == "nt":\r
            try:\r
                cleanup_script = r"""\r
$startup = Join-Path $env:APPDATA 'Microsoft\\Windows\\Start Menu\\Programs\\Startup'\r
try {\r
  Get-CimInstance Win32_Process | Where-Object {\r
    $_.ProcessId -ne $PID -and $_.Name -match '^(cmd|powershell)\\.exe$' -and\r
    $_.CommandLine -match '(launch_unk\\.bat|unk_(audio|mirror)_worker)'\r
  } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }\r
} catch {}\r
try {\r
  Get-ChildItem -Path $startup -Force -ErrorAction SilentlyContinue | Where-Object {\r
    $_.Name -match '^(launch_unk|unk[_ -]?(companion|supervisor|keepalive)).*\\.(bat|cmd|lnk)$'\r
  } | Remove-Item -Force -ErrorAction SilentlyContinue\r
} catch {}\r
"""\r
                cleanup = subprocess.run(\r
                    ["powershell.exe", "-NoProfile", "-NonInteractive", "-WindowStyle", "Hidden", "-Command", cleanup_script],\r
                    capture_output=True,\r
                    text=True,\r
                    timeout=45,\r
                )\r
                popup_cleanup_notes.append(f"legacy_popup_cleanup_exit:{cleanup.returncode}")\r
                if cleanup.stderr:\r
                    popup_cleanup_notes.append(f"legacy_popup_cleanup_stderr:{cleanup.stderr[-500:]}")\r
            except Exception as cleanup_exc:\r
                popup_cleanup_notes.append(f"legacy_popup_cleanup_warning:{cleanup_exc}")\r
\r
        dependency_notes: list[str] = []\r
        try:\r
            dep = subprocess.run(\r
                [\r
                    sys.executable,\r
                    "-m",\r
                    "pip",\r
                    "install",\r
                    "--disable-pip-version-check",\r
                    "requests",\r
                    "pillow",\r
                    "keyring",\r
                    "playwright",\r
                ],\r
                capture_output=True,\r
                text=True,\r
                timeout=180,\r
            )\r
            dependency_notes.append(f"pip_exit:{dep.returncode}")\r
            browser = subprocess.run(\r
                [sys.executable, "-m", "playwright", "install", "chromium"],\r
                capture_output=True,\r
                text=True,\r
                timeout=300,\r
            )\r
            dependency_notes.append(f"chromium_exit:{browser.returncode}")\r
        except Exception as dep_exc:\r
            dependency_notes.append(f"dependency_repair_warning:{dep_exc}")\r
\r
        supervisor_repair_notes: list[str] = []\r
        try:\r
            installer = script_dir / "install_supervisor.ps1"\r
            if os.name == "nt" and installer.exists():\r
                repair = subprocess.run(\r
                    [\r
                        "powershell.exe",\r
                        "-NoProfile",\r
                        "-ExecutionPolicy",\r
                        "Bypass",\r
                        "-File",\r
                        str(installer),\r
                        "-RepairOnly",\r
                        "-SkipVerify",\r
                    ],\r
                    capture_output=True,\r
                    text=True,\r
                    timeout=90,\r
                )\r
                supervisor_repair_notes.append(f"install_supervisor_repair_exit:{repair.returncode}")\r
                if repair.stderr:\r
                    supervisor_repair_notes.append(f"install_supervisor_repair_stderr:{repair.stderr[-500:]}")\r
            elif os.name == "nt":\r
                supervisor_repair_notes.append("install_supervisor_missing")\r
        except Exception as repair_exc:\r
            supervisor_repair_notes.append(f"install_supervisor_repair_warning:{repair_exc}")\r
\r
        shutil.rmtree(stage, ignore_errors=True)\r
\r
        # Two-phase update: if the enqueuer supplied an update_verification_token,\r
        # persist it so the NEXT run of unk_companion (after restart_companion)\r
        # can POST an ack. Also stash the backup dir so cap_rollback_last_update\r
        # knows where to revert to if the platform decides the update failed.\r
        token = (ctx.payload or {}).get("update_verification_token")\r
        if token:\r
            try:\r
                PENDING_UPDATE_TOKEN_FILE.write_text(json.dumps({\r
                    "token": token,\r
                    "staged_at": time.time(),\r
                    "backup_dir": str(backup),\r
                    "new_build_ref": zip_url,\r
                    "previous_build_ref": previous_build_ref,\r
                }))\r
            except Exception as tok_exc:\r
                log(f"pending update token write failed: {tok_exc}")\r
        try:\r
            (COMPANION_DIR / "last_backup.json").write_text(json.dumps({\r
                "backup_dir": str(backup),\r
                "at": time.time(),\r
                "new_build_ref": zip_url,\r
                "previous_build_ref": previous_build_ref,\r
            }))\r
        except Exception:\r
            pass\r
        try:\r
            RUNNING_BUILD_FILE.write_text(json.dumps({\r
                "build_ref": zip_url,\r
                "installed_at": time.time(),\r
                "swapped": swapped,\r
            }))\r
        except Exception as build_exc:\r
            log(f"running build receipt write failed: {build_exc}")\r
\r
        installed_sha = {}\r
        try:\r
            for fname in ("unk_companion.py", "media_mirror_worker.py", "multi_platform_publisher.py"):\r
                fp = script_dir / fname\r
                if fp.exists():\r
                    installed_sha[fname] = hashlib.sha256(fp.read_bytes()).hexdigest()[:16]\r
        except Exception:\r
            pass\r
\r
        return {\r
            "ok": True,\r
            "swapped": swapped,\r
            "swapped_count": len(swapped),\r
            "zip_sha256": zip_sha256,\r
            "zip_bytes": len(raw),\r
            "installed_sha256_prefix": installed_sha,\r
            "backup_dir": str(backup),\r
            "install_dir": str(script_dir),\r
            "dependency_notes": dependency_notes,\r
            "supervisor_repair_notes": supervisor_repair_notes,\r
            "popup_cleanup_notes": popup_cleanup_notes,\r
            "update_verification_token": token if token else None,\r
        }\r
\r
    except Exception as e:\r
        return {"ok": False, "error": "update_failed", "detail": str(e),\r
                "trace": traceback.format_exc(limit=4)}\r
\r
\r
def cap_rollback_last_update(ctx: ActionContext) -> dict:\r
    """Restore files from the most recent self_update backup. Meant to be\r
    called by the recovery loop after desktop-update-verify rolls back."""\r
    import shutil\r
    try:\r
        pointer = COMPANION_DIR / "last_backup.json"\r
        if not pointer.exists():\r
            return {"ok": False, "error": "no_previous_backup"}\r
        pointer_payload = json.loads(pointer.read_text())\r
        backup_dir = Path(pointer_payload.get("backup_dir", ""))\r
        if not backup_dir.exists() or not backup_dir.is_dir():\r
            return {"ok": False, "error": "backup_dir_missing", "path": str(backup_dir)}\r
        script_dir = _companion_script_dir()\r
        restored: list[str] = []\r
        for src in backup_dir.rglob("*"):\r
            if not src.is_file(): continue\r
            rel = src.relative_to(backup_dir)\r
            dst = script_dir / rel\r
            dst.parent.mkdir(parents=True, exist_ok=True)\r
            shutil.copy2(src, dst)\r
            restored.append(str(rel))\r
        try:\r
            previous_build_ref = pointer_payload.get("previous_build_ref")\r
            if previous_build_ref:\r
                RUNNING_BUILD_FILE.write_text(json.dumps({\r
                    "build_ref": previous_build_ref,\r
                    "restored_at": time.time(),\r
                    "rollback_from": pointer_payload.get("new_build_ref"),\r
                }))\r
            elif RUNNING_BUILD_FILE.exists():\r
                RUNNING_BUILD_FILE.unlink()\r
        except Exception as build_restore_exc:\r
            log(f"running build rollback receipt failed: {build_restore_exc}")\r
        # Schedule an immediate restart so the reverted script runs.\r
        _RESTART_REQUESTED["pending"] = True\r
        _RESTART_REQUESTED["reason"] = "rollback_last_update"\r
        return {"ok": True, "restored": restored, "restored_count": len(restored), "from": str(backup_dir)}\r
    except Exception as e:\r
        return {"ok": False, "error": "rollback_failed", "detail": str(e),\r
                "trace": traceback.format_exc(limit=4)}\r
\r
\r
def _restart_already_satisfied(created_at, boot_ts, *, expected_build_ref=None, current_build_ref=None):\r
    """A previously approved restart is already met by a later real boot.\r
\r
    Keep the original action-result and device authentication; never skip a\r
    newer restart, a missing timestamp, or a mismatched required build.\r
    """\r
    from datetime import datetime as _datetime\r
    if not isinstance(created_at, str) or not created_at:\r
        return False\r
    if type(boot_ts) not in (int, float) or boot_ts <= 0:\r
        return False\r
    if expected_build_ref and (not isinstance(expected_build_ref, str)\r
                               or expected_build_ref != current_build_ref):\r
        return False\r
    try:\r
        observed = _datetime.fromisoformat(created_at.replace("Z", "+00:00"))\r
        return bool(observed.tzinfo and float(boot_ts) > observed.timestamp())\r
    except (TypeError, ValueError, OverflowError):\r
        return False\r
\r
\r
def cap_restart_companion(ctx: ActionContext) -> dict:\r
    from_source = ctx.payload if isinstance(ctx.payload, dict) else {}\r
    if _restart_already_satisfied(\r
        ctx.created_at, BOOT_TS,\r
        expected_build_ref=from_source.get("expected_build_ref"),\r
        current_build_ref=_runtime_routing_and_build_evidence().get("companion_build_ref"),\r
    ):\r
        return {"ok": True, "restart_scheduled": False,\r
                "already_satisfied_by_current_boot": True,\r
                "completion_claimed": False}\r
    _RESTART_REQUESTED["pending"] = True\r
    _RESTART_REQUESTED["reason"] = str((ctx.payload or {}).get("reason") or "manual")\r
    strategy = str((ctx.payload or {}).get("strategy") or "execv").lower().strip()\r
    if strategy not in {"execv", "supervisor_exit"}:\r
        strategy = "execv"\r
    _RESTART_REQUESTED["strategy"] = strategy\r
    return {"ok": True, "restart_scheduled": True, "reason": _RESTART_REQUESTED["reason"], "strategy": strategy}\r
\r
\r
def cap_browser_release_locks(ctx: ActionContext) -> dict:\r
    """Force-close all Unk/Playwright Chromium windows using the saved browser profile.\r
\r
    Use this before retrying publish jobs when the browser profile is wedged\r
    (leftover Playwright Chromium holding SingletonLock; publishes fail with\r
    composer_not_found / profile_locked). No-op on non-Windows hosts.\r
    """\r
    notes: list[str] = []\r
    released_via_publisher = False\r
    try:\r
        from meta_browser_publisher import _release_locked_profile  # type: ignore\r
        _release_locked_profile(notes)\r
        released_via_publisher = True\r
    except Exception as e:\r
        notes.append(f"publisher_release_unavailable:{e}")\r
\r
    killed_extra = 0\r
    if os.name == "nt":\r
        try:\r
            proc = subprocess.run(\r
                ["wmic", "process", "where",\r
                 "Name='chrome.exe' or Name='chromium.exe'",\r
                 "get", "ProcessId,CommandLine", "/FORMAT:CSV"],\r
                capture_output=True, text=True, timeout=10,\r
            )\r
            for line in (proc.stdout or "").splitlines():\r
                if ".unk_companion" not in line and "browser_profile" not in line:\r
                    continue\r
                pid = line.strip().split(",")[-1]\r
                if not pid.isdigit():\r
                    continue\r
                subprocess.run(["taskkill", "/PID", pid, "/F"], capture_output=True, timeout=5)\r
                killed_extra += 1\r
            if killed_extra:\r
                notes.append(f"broad_sweep_killed:{killed_extra}")\r
                time.sleep(1.0)\r
        except Exception as e:\r
            notes.append(f"broad_sweep_warning:{e}")\r
\r
    cleared_locks: list[str] = []\r
    try:\r
        from meta_browser_publisher import PROFILE_DIR as _PROFILE_DIR  # type: ignore\r
        for lock_name in ("SingletonLock", "SingletonCookie", "SingletonSocket"):\r
            p = Path(_PROFILE_DIR) / lock_name\r
            if p.exists():\r
                try:\r
                    p.unlink()\r
                    cleared_locks.append(lock_name)\r
                except Exception as e:\r
                    notes.append(f"lock_unlink_warning:{lock_name}:{e}")\r
    except Exception as e:\r
        notes.append(f"profile_dir_unavailable:{e}")\r
\r
    return {\r
        "ok": True,\r
        "released_via_publisher": released_via_publisher,\r
        "extra_processes_killed": killed_extra,\r
        "cleared_locks": cleared_locks,\r
        "notes": notes,\r
    }\r
\r
\r
\r
\r
\r
VENDOR_VAULT_URL = f"{FUNCTIONS_BASE}/vendor-vault"\r
\r
\r
def _fetch_vendor_credential(device_id: str, device_key: str, credential_id: str, reason: str) -> dict:\r
    """Call vendor-vault edge function with device auth to fetch decrypted creds."""\r
    try:\r
        r = requests.post(\r
            VENDOR_VAULT_URL,\r
            headers={\r
                "apikey": SUPABASE_ANON_KEY,\r
                "Content-Type": "application/json",\r
                "X-Device-Id": device_id,\r
                "X-Device-Key": device_key,\r
            },\r
            json={"action": "fetch_decrypted", "credential_id": credential_id, "reason": reason},\r
            timeout=HTTP_TIMEOUT,\r
        )\r
        if r.status_code >= 400:\r
            return {"ok": False, "error": f"http_{r.status_code}", "detail": r.text[:400]}\r
        data = r.json()\r
        if not data.get("ok"):\r
            return {"ok": False, "error": data.get("error") or "unknown_vault_error", "detail": data}\r
        return {"ok": True, "credential": data["credential"]}\r
    except Exception as e:\r
        return {"ok": False, "error": "fetch_exception", "detail": str(e)}\r
\r
\r
EMAIL_VERIFICATION_URL = f"{FUNCTIONS_BASE}/email-verification-fetch-code"\r
\r
\r
def _email_verify_call(device_id: str, device_key: str, payload: dict) -> dict:\r
    """POST to email-verification-fetch-code with device auth. Returns raw JSON."""\r
    try:\r
        r = requests.post(\r
            EMAIL_VERIFICATION_URL,\r
            headers={\r
                "apikey": SUPABASE_ANON_KEY,\r
                "Content-Type": "application/json",\r
                "X-Device-Id": device_id,\r
                "X-Device-Key": device_key,\r
            },\r
            json=payload,\r
            timeout=HTTP_TIMEOUT,\r
        )\r
        try:\r
            data = r.json()\r
        except Exception:\r
            data = {"ok": False, "error": f"http_{r.status_code}", "detail": r.text[:400]}\r
        return data\r
    except Exception as e:\r
        return {"ok": False, "error": "http_exception", "detail": str(e)}\r
\r
\r
def cap_email_fetch_verification_code(ctx: ActionContext) -> dict:\r
    """Fetch the newest one-time code from Gmail matching a service hint."""\r
    creds = load_credentials()\r
    if not creds:\r
        return {"ok": False, "error": "companion_not_enrolled"}\r
    device_id, device_key = creds\r
    payload = dict(ctx.payload or {})\r
    payload.setdefault("action", "fetch")\r
    if not payload.get("service_hint"):\r
        return {"ok": False, "error": "service_hint_required"}\r
    return _email_verify_call(device_id, device_key, payload)\r
\r
\r
def cap_vendor_login(ctx: ActionContext) -> dict:\r
    """Attempt an automated vendor login using a credential from the vault.\r
    On email-based 2FA, Unk auto-fetches the code from Gmail and enters it.\r
    On app-approval / SMS / CAPTCHA challenges, escalates via needs_human.\r
    """\r
    credential_id = str((ctx.payload or {}).get("credential_id") or "")\r
    if not credential_id:\r
        return {"ok": False, "error": "credential_id_required"}\r
    creds = load_credentials()\r
    if not creds:\r
        return {"ok": False, "error": "companion_not_enrolled"}\r
    device_id, device_key = creds\r
\r
    fetched = _fetch_vendor_credential(device_id, device_key, credential_id, "vendor_login_action")\r
    if not fetched.get("ok"):\r
        return fetched\r
\r
    try:\r
        from vendor_browser import login as _vendor_login  # type: ignore\r
    except Exception as e:\r
        return {"ok": False, "error": "vendor_browser_unavailable", "detail": str(e)}\r
\r
    def _fetch_email_code(service_hint: str, sender_hint: str | None = None,\r
                          subject_hint: str | None = None) -> dict:\r
        return _email_verify_call(device_id, device_key, {\r
            "action": "fetch",\r
            "service_hint": service_hint,\r
            "sender_hint": sender_hint,\r
            "subject_hint": subject_hint,\r
            "context": {"credential_id": credential_id},\r
        })\r
\r
    def _report_event(event_id: str, status: str, escalation_reason: str | None = None,\r
                      screenshot_path: str | None = None) -> None:\r
        _email_verify_call(device_id, device_key, {\r
            "action": "update",\r
            "event_id": event_id,\r
            "status": status,\r
            "escalation_reason": escalation_reason,\r
            "screenshot_path": screenshot_path,\r
        })\r
\r
    result = _vendor_login(\r
        credential=fetched["credential"],\r
        fetch_email_code=_fetch_email_code,\r
        report_event=_report_event,\r
    )\r
    return result\r
\r
\r
\r
\r
def cap_vendor_signup(ctx: ActionContext) -> dict:\r
    """Placeholder for vendor account creation. Requires per-site scaffolding."""\r
    payload = ctx.payload or {}\r
    return {\r
        "ok": False,\r
        "error": "not_implemented",\r
        "detail": "vendor_signup requires per-site logic. Add the target site's signup steps to vendor_browser.py.",\r
        "requested": {\r
            "service_name": payload.get("service_name"),\r
            "service_url": payload.get("service_url"),\r
        },\r
    }\r
\r
\r
def cap_vendor_action(ctx: ActionContext) -> dict:\r
    """Placeholder for arbitrary post-login vendor actions (add to cart, checkout, etc.)."""\r
    return {\r
        "ok": False,\r
        "error": "not_implemented",\r
        "detail": "vendor_action requires per-site logic. Add steps to vendor_browser.py.",\r
    }\r
\r
\r
# ---------------------------------------------------------------------------\r
# Media engine — local FFmpeg dependency playbook + derivative generation.\r
#\r
# These run entirely on Ground Zero. No winget, no elevation, no Lovable turn.\r
# ---------------------------------------------------------------------------\r
def _ffmpeg_module():\r
    import importlib\r
    import ffmpeg_bootstrap  # type: ignore\r
    return importlib.reload(ffmpeg_bootstrap)\r
\r
\r
def cap_ffmpeg_ensure(ctx: ActionContext) -> dict:\r
    """Install/verify FFmpeg under the Unk runtime from a checksum-verified build."""\r
    payload = ctx.payload or {}\r
    try:\r
        mod = _ffmpeg_module()\r
        res = mod.ensure(force=bool(payload.get("force")), log=log)\r
        res["companion_version"] = COMPANION_VERSION\r
        return res\r
    except Exception as e:\r
        return {"ok": False, "error": "ffmpeg_ensure_failed", "detail": str(e)}\r
\r
\r
def cap_ffmpeg_health(ctx: ActionContext) -> dict:\r
    """Report install path, version, checksum origin and a live encode proof."""\r
    try:\r
        mod = _ffmpeg_module()\r
        st = mod.status()\r
        st["ok"] = bool(st.get("healthy"))\r
        st["companion_version"] = COMPANION_VERSION\r
        return st\r
    except Exception as e:\r
        return {"ok": False, "error": "ffmpeg_health_failed", "detail": str(e)}\r
\r
\r
def cap_ffmpeg_rollback(ctx: ActionContext) -> dict:\r
    """Flip back to the previously verified FFmpeg install."""\r
    try:\r
        mod = _ffmpeg_module()\r
        return mod.rollback(log=log)\r
    except Exception as e:\r
        return {"ok": False, "error": "ffmpeg_rollback_failed", "detail": str(e)}\r
\r
\r
def cap_media_generate_derivative(ctx: ActionContext) -> dict:\r
    """Produce (or reuse) a platform-ready H.264/AAC derivative from a local master.\r
\r
    payload: {asset_id, master_path, profile?, max_bytes?, max_height?,\r
              platform_policies?, reuse?}\r
    The master is never modified. Returns full derivative metadata for upsert\r
    into \`media_derivatives\`, including per-platform eligibility so a full\r
    interview is never mislabelled as a Reel/Short.\r
    """\r
    payload = ctx.payload or {}\r
    asset_id = str(payload.get("asset_id") or "").strip()\r
    master_path = str(payload.get("master_path") or "").strip()\r
    if not asset_id or not master_path:\r
        return {"ok": False, "error": "asset_id_and_master_path_required"}\r
    try:\r
        import importlib\r
        import media_derivative_worker as mdw  # type: ignore\r
        mdw = importlib.reload(mdw)\r
        res = mdw.build_derivative(\r
            asset_id=asset_id,\r
            master_path=master_path,\r
            profile=payload.get("profile") or mdw.DEFAULT_PROFILE,\r
            max_bytes=int(payload.get("max_bytes") or mdw.DEFAULT_MAX_BYTES),\r
            max_height=int(payload.get("max_height") or 1080),\r
            platform_policies=payload.get("platform_policies") or {},\r
            reuse=payload.get("reuse", True),\r
            log=log,\r
        )\r
        res["companion_version"] = COMPANION_VERSION\r
        return res\r
    except Exception as e:\r
        return {"ok": False, "error": "derivative_generation_failed", "detail": str(e)}\r
\r
\r
def cap_media_make_reel(ctx: ActionContext) -> dict:\r
    """Cut one vertical reel + poster frame from a mirrored master and upload it.\r
\r
    payload: {plan_id, source_asset_id, source_url, start_seconds,\r
              duration_seconds, upload_video_url, upload_thumb_url}\r
    Pure local FFmpeg — no model calls, no Lovable credits. The master is\r
    range-read over HTTPS, never fully downloaded, and never modified.\r
    """\r
    payload = ctx.payload or {}\r
    required = ("plan_id", "source_asset_id", "source_url",\r
                "upload_video_url", "upload_thumb_url")\r
    missing = [k for k in required if not payload.get(k)]\r
    if missing:\r
        return {"ok": False, "error": "missing_payload_fields", "fields": missing}\r
    try:\r
        import importlib\r
        import media_reel_worker as mrw  # type: ignore\r
        mrw = importlib.reload(mrw)\r
        res = mrw.make_reel(\r
            plan_id=str(payload["plan_id"]),\r
            source_asset_id=str(payload["source_asset_id"]),\r
            source_url=str(payload["source_url"]),\r
            start_seconds=float(payload.get("start_seconds") or 0),\r
            duration_seconds=float(payload.get("duration_seconds") or 30),\r
            upload_video_url=str(payload["upload_video_url"]),\r
            upload_thumb_url=str(payload["upload_thumb_url"]),\r
            log=log,\r
        )\r
        res["companion_version"] = COMPANION_VERSION\r
        return res\r
    except Exception as e:\r
        return {"ok": False, "error": "reel_generation_failed", "detail": str(e)}\r
\r
\r
\r
\r
\r
def cap_media_local_inventory(ctx: ActionContext) -> dict:\r
    """Map local master files on Ground Zero: path, size, mtime, probe metadata.\r
\r
    payload: {roots: [path,...], patterns?: [".mp4",".mov"], probe?: bool,\r
              name_contains?: str, limit?: int}\r
    Used to build the Carl Boyd readiness inventory from verified local truth\r
    instead of guessing, and to avoid re-downloading multi-GB masters.\r
    """\r
    payload = ctx.payload or {}\r
    roots = payload.get("roots") or []\r
    if isinstance(roots, str):\r
        roots = [roots]\r
    exts = [e.lower() for e in (payload.get("patterns") or [".mp4", ".mov", ".m4v", ".mkv", ".avi"])]\r
    needle = str(payload.get("name_contains") or "").lower().strip()\r
    do_probe = bool(payload.get("probe", True))\r
    limit = int(payload.get("limit") or 400)\r
\r
    items: list[dict] = []\r
    scanned_roots: list[dict] = []\r
    try:\r
        mod = _ffmpeg_module()\r
    except Exception:\r
        mod = None\r
    for root in roots:\r
        p = Path(str(root))\r
        info = {"root": str(p), "exists": p.exists(), "files": 0}\r
        if not p.exists():\r
            scanned_roots.append(info)\r
            continue\r
        try:\r
            for f in p.rglob("*"):\r
                if len(items) >= limit:\r
                    break\r
                if not f.is_file() or f.suffix.lower() not in exts:\r
                    continue\r
                if needle and needle not in f.name.lower():\r
                    continue\r
                try:\r
                    st = f.stat()\r
                except Exception:\r
                    continue\r
                rec = {\r
                    "path": str(f),\r
                    "file_name": f.name,\r
                    "size_bytes": st.st_size,\r
                    "modified_at": datetime.fromtimestamp(st.st_mtime, tz=timezone.utc).isoformat(),\r
                }\r
                if do_probe and mod:\r
                    pr = mod.probe(str(f))\r
                    if pr.get("ok"):\r
                        rec.update({\r
                            "duration_seconds": pr.get("duration_seconds"),\r
                            "width": pr.get("width"),\r
                            "height": pr.get("height"),\r
                            "container": pr.get("container"),\r
                            "video_codec": pr.get("video_codec"),\r
                            "audio_codec": pr.get("audio_codec"),\r
                        })\r
                    else:\r
                        rec["probe_error"] = pr.get("error")\r
                items.append(rec)\r
                info["files"] += 1\r
        except Exception as e:\r
            info["error"] = str(e)\r
        scanned_roots.append(info)\r
\r
    return {\r
        "ok": True,\r
        "roots": scanned_roots,\r
        "count": len(items),\r
        "items": items,\r
        "ffmpeg_available": bool(mod and mod.read_config().get("ffprobe")),\r
        "companion_version": COMPANION_VERSION,\r
    }\r
\r
\r
def _detect_local_drives(include_system: bool = False) -> list[dict]:\r
    """Enumerate attached drives (external/USB first). Windows + POSIX."""\r
    drives: list[dict] = []\r
    if os.name == "nt":\r
        import ctypes\r
        import string\r
        kernel = ctypes.windll.kernel32\r
        mask = kernel.GetLogicalDrives()\r
        for i, letter in enumerate(string.ascii_uppercase):\r
            if not (mask >> i) & 1:\r
                continue\r
            root = f"{letter}:\\\\"\r
            try:\r
                dtype = kernel.GetDriveTypeW(ctypes.c_wchar_p(root))\r
            except Exception:\r
                dtype = 0\r
            # 2 = removable, 3 = fixed, 4 = network, 5 = cdrom\r
            if dtype not in (2, 3):\r
                continue\r
            is_system = letter.upper() == "C"\r
            if is_system and not include_system:\r
                continue\r
            label = ""\r
            try:\r
                buf = ctypes.create_unicode_buffer(1024)\r
                fsbuf = ctypes.create_unicode_buffer(1024)\r
                kernel.GetVolumeInformationW(\r
                    ctypes.c_wchar_p(root), buf, 1024, None, None, None, fsbuf, 1024)\r
                label = buf.value\r
            except Exception:\r
                pass\r
            drives.append({\r
                "root": root,\r
                "volume_label": label,\r
                "kind": "removable" if dtype == 2 else "fixed",\r
                "is_system": is_system,\r
            })\r
        # Removable/external drives are what Jason means by "my external drive".\r
        drives.sort(key=lambda d: (d["kind"] != "removable", d["root"]))\r
    else:\r
        for base in ("/Volumes", "/media", "/mnt"):\r
            p = Path(base)\r
            if not p.exists():\r
                continue\r
            try:\r
                for child in p.iterdir():\r
                    if child.is_dir():\r
                        drives.append({"root": str(child), "volume_label": child.name,\r
                                       "kind": "removable", "is_system": False})\r
            except Exception:\r
                continue\r
    return drives\r
\r
\r
def _classify_media_local_ingest_receipt(body: object, scanned: int) -> dict:\r
    """Require a durable K ingest event and one verifiable outcome per source file.\r
\r
    A transport 200 is not a completed ingest. Unknown writes must not be\r
    automatically replayed because asset changes may already have committed.\r
    """\r
    unverified = {"ok": False, "error": "ingest_receipt_unverified",\r
                  "retry_prohibited": True}\r
    if not isinstance(body, dict) or body.get("ok") is not True:\r
        return unverified\r
    receipt_id = body.get("audit_receipt_id")\r
    matched, created = body.get("matched"), body.get("created")\r
    if not isinstance(receipt_id, str) or not receipt_id.strip():\r
        return unverified\r
    if (not isinstance(scanned, int) or scanned < 1\r
            or type(matched) is not int or type(created) is not int\r
            or matched < 0 or created < 0 or matched + created > scanned):\r
        return unverified\r
\r
    rows = body.get("results")\r
    if not isinstance(rows, list) or len(rows) != scanned:\r
        return unverified\r
    accepted_rows = [row for row in rows\r
                     if isinstance(row, dict) and row.get("status")\r
                     in ("linked_local_master", "registered_local_master")]\r
    if (len(accepted_rows) != matched + created\r
            or sum(row["status"] == "linked_local_master" for row in accepted_rows) != matched\r
            or sum(row["status"] == "registered_local_master" for row in accepted_rows) != created\r
            or any(not isinstance(row.get("asset_id"), str)\r
                   or not row["asset_id"].strip() for row in accepted_rows)):\r
        return unverified\r
\r
    accepted = matched + created\r
    result = {"ok": accepted == scanned, "audit_receipt_id": receipt_id,\r
              "matched": matched, "created": created, "accepted": accepted,\r
              "rejected": scanned - accepted}\r
    if accepted != scanned:\r
        result.update(error="ingest_manifest_incomplete", retry_prohibited=True)\r
    return result\r
\r
\r
def cap_media_local_ingest(ctx: ActionContext) -> dict:\r
    """Open attached drives, find master video files, and register them upstream.\r
\r
    payload: {roots?: [path,...], include_system?: bool, name_contains?: str,\r
              series_tag?: str, owning_org?: str, owning_program?: str,\r
              approve?: bool, limit?: int, probe?: bool, min_size_mb?: int}\r
\r
    Auto-detects external drives when no roots are given, walks them for video\r
    masters, probes duration locally with ffprobe, then POSTs the manifest to\r
    the media-local-ingest edge function. Existing library rows are relinked by\r
    file name so the multi-gigabyte masters never have to be re-downloaded.\r
    """\r
    payload = ctx.payload or {}\r
    roots = payload.get("roots") or []\r
    if isinstance(roots, str):\r
        roots = [roots]\r
\r
    detected = _detect_local_drives(include_system=bool(payload.get("include_system")))\r
    if not roots:\r
        roots = [d["root"] for d in detected]\r
    if not roots:\r
        return {"ok": False, "error": "no_attached_drives_found",\r
                "hint": "plug the external drive in, or pass roots explicitly"}\r
\r
    label_by_root = {d["root"]: d.get("volume_label") for d in detected}\r
    exts = [e.lower() for e in (payload.get("patterns") or [".mp4", ".mov", ".m4v", ".mkv", ".avi"])]\r
    needle = str(payload.get("name_contains") or "").lower().strip()\r
    limit = int(payload.get("limit") or 400)\r
    min_bytes = int(payload.get("min_size_mb") or 20) * 1024 * 1024\r
    do_probe = bool(payload.get("probe", True))\r
    skip_dirs = {"$recycle.bin", "system volume information", "windows",\r
                 "program files", "program files (x86)", "node_modules", "appdata"}\r
\r
    try:\r
        mod = _ffmpeg_module()\r
    except Exception:\r
        mod = None\r
\r
    items: list[dict] = []\r
    scanned: list[dict] = []\r
    for root in roots:\r
        p = Path(str(root))\r
        info = {"root": str(p), "exists": p.exists(), "files": 0,\r
                "volume_label": label_by_root.get(str(p))}\r
        if not p.exists():\r
            scanned.append(info)\r
            continue\r
        try:\r
            for f in p.rglob("*"):\r
                if len(items) >= limit:\r
                    break\r
                try:\r
                    if any(part.lower() in skip_dirs for part in f.parts):\r
                        continue\r
                    if not f.is_file() or f.suffix.lower() not in exts:\r
                        continue\r
                    st = f.stat()\r
                except Exception:\r
                    continue\r
                if st.st_size < min_bytes:\r
                    continue\r
                if needle and needle not in f.name.lower():\r
                    continue\r
                rec = {\r
                    "path": str(f),\r
                    "file_name": f.name,\r
                    "parent_path": str(f.parent),\r
                    "volume_label": info.get("volume_label"),\r
                    "size_bytes": st.st_size,\r
                    "modified_at": datetime.fromtimestamp(st.st_mtime, tz=timezone.utc).isoformat(),\r
                }\r
                if do_probe and mod:\r
                    pr = mod.probe(str(f))\r
                    if pr.get("ok"):\r
                        rec.update({\r
                            "duration_seconds": pr.get("duration_seconds"),\r
                            "width": pr.get("width"),\r
                            "height": pr.get("height"),\r
                        })\r
                    else:\r
                        rec["probe_error"] = pr.get("error")\r
                items.append(rec)\r
                info["files"] += 1\r
        except Exception as e:\r
            info["error"] = str(e)\r
        scanned.append(info)\r
\r
    if not items:\r
        return {"ok": False, "error": "no_master_files_found", "roots": scanned,\r
                "detected_drives": detected, "companion_version": COMPANION_VERSION}\r
\r
    creds = load_credentials()\r
    if not creds:\r
        return {"ok": False, "error": "device_not_enrolled"}\r
    device_id, device_key = creds\r
\r
    try:\r
        r = requests.post(\r
            f"{FUNCTIONS_BASE}/media-local-ingest",\r
            headers={\r
                "apikey": SUPABASE_ANON_KEY,\r
                "Content-Type": "application/json",\r
                "x-device-id": device_id,\r
                "x-device-key": device_key,\r
            },\r
            json={\r
                "items": items,\r
                "series_tag": payload.get("series_tag"),\r
                "owning_org": payload.get("owning_org"),\r
                "owning_program": payload.get("owning_program"),\r
                "approve": bool(payload.get("approve")),\r
                "device_label": payload.get("device_label"),\r
            },\r
            timeout=180,\r
        )\r
        body = r.json() if r.content else {}\r
    except Exception as e:\r
        return {"ok": False, "error": "ingest_post_failed", "detail": str(e),\r
                "scanned": len(items), "roots": scanned,\r
                "retry_prohibited": True}\r
\r
    if r.status_code >= 400:\r
        return {"ok": False, "error": "ingest_rejected", "status": r.status_code,\r
                "body": body, "scanned": len(items),\r
                "retry_prohibited": bool(body.get("retry_prohibited")) if isinstance(body, dict) else True}\r
\r
    outcome = _classify_media_local_ingest_receipt(body, len(items))\r
    return {\r
        **outcome,\r
        "detected_drives": detected,\r
        "roots": scanned,\r
        "scanned": len(items),\r
        "results": body.get("results", []) if isinstance(body, dict) else [],\r
        "companion_version": COMPANION_VERSION,\r
    }\r
\r
\r
\r
\r
def cap_linkedin_content_migrate(ctx: ActionContext) -> dict:\r
    """Move content off a RETIRED LinkedIn alias profile onto the canonical one.\r
\r
    Read-only on the source profile: harvests recent activity text + permalinks,\r
    then posts the manifest to the linkedin-content-migrate edge function which\r
    records the ledger row and enqueues the repost through the normal publish\r
    rail (identity guard still applies). Never posts directly from here.\r
    """\r
    if _harvest_linkedin_posts is None:\r
        return {"ok": False, "error": "multi_platform_publisher_missing"}\r
    p = ctx.payload or {}\r
    sources = p.get("source_handles")\r
    if isinstance(sources, str):\r
        sources = [sources]\r
    if not sources:\r
        one = p.get("source_handle")\r
        sources = [one] if one else []\r
    if not sources:\r
        return {"ok": False, "error": "source_handles_required"}\r
    limit = int(p.get("limit") or 25)\r
    max_repost = int(p.get("max_repost") or 10)\r
    auto_repost = bool(p.get("auto_repost", True))\r
\r
    creds = load_credentials()\r
    if not creds:\r
        return {"ok": False, "error": "device_not_enrolled"}\r
    device_id, device_key = creds\r
\r
    out = []\r
    for src in sources:\r
        harvest = _run_browser_publisher_isolated(\r
            _harvest_linkedin_posts,\r
            profile_slug=str(src),\r
            limit=limit,\r
        )\r
        entry = {\r
            "source_handle": src,\r
            "harvest_ok": bool(harvest.get("ok")),\r
            "harvest_error": harvest.get("error"),\r
            "items_found": len(harvest.get("items") or []),\r
            "screenshot_path": harvest.get("screenshot_path"),\r
            "notes": (harvest.get("notes") or [])[:10],\r
        }\r
        items = harvest.get("items") or []\r
        if harvest.get("ok") and items:\r
            try:\r
                r = requests.post(\r
                    f"{FUNCTIONS_BASE}/linkedin-content-migrate",\r
                    headers={\r
                        "apikey": SUPABASE_ANON_KEY,\r
                        "Content-Type": "application/json",\r
                        "x-device-id": device_id,\r
                        "x-device-key": device_key,\r
                    },\r
                    json={\r
                        "source_handle": src,\r
                        "items": items,\r
                        "auto_repost": auto_repost,\r
                        "max_repost": max_repost,\r
                    },\r
                    timeout=180,\r
                )\r
                body = r.json() if r.content else {}\r
                entry["ingest_status"] = r.status_code\r
                entry["queued"] = body.get("queued")\r
                entry["target_handle"] = body.get("target_handle")\r
                entry["ingest_error"] = body.get("error")\r
            except Exception as e:\r
                entry["ingest_error"] = f"ingest_post_failed:{e}"\r
        out.append(entry)\r
\r
    return {\r
        "ok": any(e.get("harvest_ok") for e in out),\r
        "sources": out,\r
        "companion_version": COMPANION_VERSION,\r
    }\r
\r
\r
def _sha256_file(path: Path) -> str:\r
    """Return a streaming SHA-256 digest for a downloaded evidence artifact."""\r
    digest = hashlib.sha256()\r
    with path.open("rb") as handle:\r
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):\r
            digest.update(chunk)\r
    return digest.hexdigest()\r
\r
\r
def _portal_source_filename(url: str, index: int) -> str:\r
    """Deterministic safe filename for a verified source URL."""\r
    parsed = urllib.parse.urlparse(url)\r
    name = Path(parsed.path).name or f"official-source-{index}.html"\r
    return re.sub(r"[^A-Za-z0-9._\\\\-]", "_", name)[:180]\r
\r
\r
def cap_portal_traverse(ctx: ActionContext) -> dict:\r
    """Capture official sources, then walk a funder portal read-only.\r
\r
    The broker may supply a source-locked work_plan. Every official source is\r
    downloaded through the existing allowlisted downloader before traversal,\r
    so Ground Zero returns durable artifacts instead of silently ignoring the\r
    evidence packet. Traversal itself remains structurally unable to submit.\r
    """\r
    run_id = str(ctx.payload.get("run_id", "") or "").strip()\r
    url = str(ctx.payload.get("portal_url", "") or "").strip()\r
    if not run_id or not url:\r
        return {"ok": False, "error": "run_id_and_portal_url_required"}\r
\r
    work_plan = ctx.payload.get("work_plan") or {}\r
    if not isinstance(work_plan, dict):\r
        work_plan = {}\r
    official_sources = work_plan.get("official_sources") or []\r
    if not isinstance(official_sources, list):\r
        official_sources = []\r
\r
    source_dir = DOWNLOAD_DIR / "grant-sources" / run_id\r
    source_downloads: list[dict] = []\r
    for index, source_url in enumerate(official_sources, start=1):\r
        if not isinstance(source_url, str) or not source_url.startswith("https://"):\r
            source_downloads.append({\r
                "url": str(source_url)[:300],\r
                "ok": False,\r
                "error": "invalid_official_source_url",\r
            })\r
            continue\r
        source_ctx = ActionContext(\r
            action_id=f"{ctx.action_id}-source-{index}",\r
            capability="download_url_to_folder",\r
            action_type="download_url_to_folder",\r
            payload={\r
                "url": source_url,\r
                "folder": str(source_dir),\r
                "filename": _portal_source_filename(source_url, index),\r
            },\r
        )\r
        outcome = cap_download_url_to_folder(source_ctx)\r
        if outcome.get("ok") is True and outcome.get("path"):\r
            try:\r
                artifact_path = Path(str(outcome["path"]))\r
                outcome["sha256"] = _sha256_file(artifact_path)\r
                outcome["downloaded_at"] = datetime.now(timezone.utc).isoformat()\r
            except Exception as exc:  # noqa: BLE001\r
                outcome["ok"] = False\r
                outcome["error"] = f"source_hash_failed:{str(exc)[:240]}"\r
        source_downloads.append({"url": source_url, **outcome})\r
\r
    worker = Path(__file__).with_name("portal_traversal_worker.py")\r
    if not worker.exists():\r
        return {\r
            "ok": False,\r
            "error": "portal_traversal_worker_missing",\r
            "official_source_downloads": source_downloads,\r
        }\r
    try:\r
        proc = subprocess.run(\r
            [sys.executable, str(worker), "--run-id", run_id, "--url", url],\r
            capture_output=True, text=True, timeout=900,\r
        )\r
        return {\r
            "ok": proc.returncode == 0,\r
            "run_id": run_id,\r
            "exit_code": proc.returncode,\r
            "stdout": (proc.stdout or "")[-4000:],\r
            "stderr": (proc.stderr or "")[-2000:],\r
            "task_instructions_present": bool(ctx.payload.get("instructions")),\r
            "acceptance_tests": work_plan.get("acceptance_tests") or [],\r
            "expected_artifacts": work_plan.get("expected_artifacts") or [],\r
            "official_source_downloads": source_downloads,\r
            "official_sources_requested": len(official_sources),\r
            "official_sources_downloaded": sum(\r
                1 for item in source_downloads if item.get("ok") is True\r
            ),\r
        }\r
    except subprocess.TimeoutExpired:\r
        return {\r
            "ok": False,\r
            "error": "traversal_timeout",\r
            "run_id": run_id,\r
            "official_source_downloads": source_downloads,\r
        }\r
    except Exception as exc:  # noqa: BLE001\r
        return {\r
            "ok": False,\r
            "error": str(exc)[:400],\r
            "run_id": run_id,\r
            "official_source_downloads": source_downloads,\r
        }\r
\r
\r
CAPABILITY_HANDLERS: dict[str, Callable[[ActionContext], dict]] = {\r
\r
    # Tier 1\r
    "capture_screenshot": cap_capture_screenshot,\r
    "read_file": cap_read_file,\r
    "write_file": cap_write_file,\r
    "launch_process": cap_launch_process,\r
    "elevate_powershell_script": cap_elevate_powershell_script,\r
    "run_check": cap_run_check,\r
    "run_local_script": cap_run_local_script,\r
    "platform_persistence_repair": cap_platform_persistence_repair,\r
    # Production repair requests use this equivalent capability name. Keep it\r
    # on the same allowlisted handler; no arbitrary command path is introduced.\r
    "desktop_commander_repair": cap_desktop_commander_repair,\r
\r
    # Tier 2\r
    "open_url": cap_open_url,\r
    "connector_escort": cap_connector_escort,\r
    "portal_traverse_via_browser": cap_portal_traverse,\r
    "open_file": cap_open_file,\r
    "reveal_in_explorer": cap_reveal_in_explorer,\r
    "read_clipboard": cap_read_clipboard,\r
    "write_clipboard": cap_write_clipboard,\r
    # Tier 3 (desktop side)\r
    "append_to_file": cap_append_to_file,\r
    "download_url_to_folder": cap_download_url_to_folder,\r
    # Tier 3 — Meta Graph API publishing (creds loaded from local keyring)\r
    "meta_status": cap_meta_status,\r
    "meta_publish": cap_meta_publish,\r
    "meta_publish_photo": cap_meta_publish_photo,\r
    "meta_publish_video": cap_meta_publish_video,\r
    "meta_publish_reel": cap_meta_publish_reel,\r
    "meta_post_metrics": cap_meta_post_metrics,\r
    "meta_refresh_token": cap_meta_refresh_token,\r
    "meta_recent_log": cap_meta_recent_log,\r
    # Tier 3 — Meta Autopilot (auto-publish w/ guardrail holds + alerts)\r
    "meta_autopilot_publish": cap_meta_autopilot_publish,\r
    "meta_autopilot_holds": cap_meta_autopilot_holds,\r
    "meta_autopilot_alerts": cap_meta_autopilot_alerts,\r
    "meta_autopilot_history": cap_meta_autopilot_history,\r
    "meta_autopilot_release": cap_meta_autopilot_release,\r
    "meta_autopilot_classify": cap_meta_autopilot_classify,\r
    # Social account onboarding (Instagram, Threads, YouTube, LinkedIn, TikTok)\r
    "social_platform_status": cap_social_platform_status,\r
    "social_open_signup": cap_social_open_signup,\r
    "social_profile_draft": cap_social_profile_draft,\r
    "social_key_capture": cap_social_key_capture,\r
    "social_connection_test": cap_social_connection_test,\r
    "social_readiness_report": cap_social_readiness_report,\r
    # Page-level publishing destinations (Facebook Pages discovered under the\r
    # admin's personal profile; personal profile is auth-only and never posted from).\r
    "social_pages_discover": cap_social_pages_discover,\r
    "social_pages_test": cap_social_pages_test,\r
    # Meta Autofix (dry-run until META_AUTOPILOT_ENABLED=true)\r
    "browser_session": cap_browser_session,\r
    "browser_portal_login": cap_browser_portal_login,\r
    # Paperwork queue — autonomous non-signature form filling\r
    "form_autofill": cap_form_autofill,\r
    # Credit-independent Google Drive credential provisioning\r
    "google_credential_provision": cap_google_credential_provision,\r
    "invoke_edge_function": cap_invoke_edge_function,\r
    # Autonomous operational secret rotation (token never leaves Ground Zero)\r
    "secret_rotate": cap_secret_rotate,\r
    # Standing Integration & Credential Manager (onboard + maintain every tool)\r
    "integration_onboard": cap_integration_onboard,\r
\r
    "meta_autofix_history": cap_meta_autofix_history,\r
    # Option 1 — browser-driven Page publishing via Jason's logged-in Chrome\r
    "browser_publish_facebook": cap_browser_publish_facebook,\r
    "browser_signin_facebook": cap_browser_signin_facebook,\r
    "browser_signin_instagram": cap_browser_signin_instagram,\r
    "browser_signin_linkedin": cap_browser_signin_linkedin,\r
    "browser_preflight_platform": cap_browser_preflight_platform,\r
    "rescue_windows": cap_rescue_windows,\r
\r
\r
\r
    "browser_publish_facebook_reel": cap_browser_publish_facebook_reel,\r
    "browser_publish_instagram": cap_browser_publish_instagram,\r
    "browser_publish_instagram_reel": cap_browser_publish_instagram_reel,\r
    "browser_publish_linkedin": cap_browser_publish_linkedin,\r
    "recover_linkedin_permalink": cap_recover_linkedin_permalink,\r
    "linkedin_content_migrate": cap_linkedin_content_migrate,\r
    "browser_publish_youtube_short": cap_browser_publish_youtube_short,\r
\r
    # Browser-driven Meta credential configurator (Graph Explorer → keyring)\r
    "meta_configure_via_browser": cap_meta_configure_via_browser,\r
    "meta_app_dashboard_configure": cap_meta_app_dashboard_configure,\r
\r
    # Remote maintenance — download latest ZIP + re-exec (Ground Zero button)\r
    "self_update": cap_self_update,\r
    "rollback_last_update": cap_rollback_last_update,\r
\r
    # Media engine — local FFmpeg playbook + derivative generation\r
    "ffmpeg_ensure": cap_ffmpeg_ensure,\r
    "ffmpeg_health": cap_ffmpeg_health,\r
    "ffmpeg_rollback": cap_ffmpeg_rollback,\r
    "media_generate_derivative": cap_media_generate_derivative,\r
    "media_make_reel": cap_media_make_reel,\r
    "media_local_inventory": cap_media_local_inventory,\r
    "media_local_ingest": cap_media_local_ingest,\r
\r
    "restart_companion": cap_restart_companion,\r
    "browser_release_locks": cap_browser_release_locks,\r
    # Vendor credential vault (operational accounts — Home Depot Pro, suppliers, etc.)\r
    "vendor_login": cap_vendor_login,\r
    "email_fetch_verification_code": cap_email_fetch_verification_code,\r
\r
    "vendor_signup": cap_vendor_signup,\r
    "vendor_action": cap_vendor_action,\r
}\r
\r
\r
\r
\r
\r
\r
\r
\r
# ---------------------------------------------------------------------------\r
# Action execution + result reporting\r
# ---------------------------------------------------------------------------\r
\r
def report_result(device_id: str, device_key: str, action_id: str, result: dict) -> None:\r
    try:\r
        r = requests.post(\r
            COMPANION_URL,\r
            headers={\r
                "apikey": SUPABASE_ANON_KEY,\r
                "Content-Type": "application/json",\r
                "X-Device-Id": device_id,\r
                "X-Device-Key": device_key,\r
            },\r
            json={"action": "action_result", "action_id": action_id, "result": result},\r
            timeout=HTTP_TIMEOUT,\r
        )\r
        if r.status_code >= 400:\r
            log(f"  result POST -> HTTP {r.status_code} {r.text[:200]}")\r
    except Exception as e:\r
        log(f"  result POST failed: {e}")\r
\r
def execute_action(device_id: str, device_key: str, action: dict) -> None:\r
    ctx = ActionContext(\r
        action_id=action["id"],\r
        capability=action.get("capability", ""),\r
        action_type=action.get("action_type", ""),\r
        payload=action.get("payload") or {},\r
        created_at=action.get("created_at"),\r
    )\r
    log(f"-> action {ctx.action_id} :: {ctx.capability} / {ctx.action_type}" +\r
        (f" created_at={ctx.created_at} boot_ts={BOOT_TS:.1f}" if ctx.action_type=="restart_companion" else ""))\r
    handler = CAPABILITY_HANDLERS.get(ctx.capability)\r
    if not handler:\r
        result = {"ok": False, "error": "unsupported_capability", "capability": ctx.capability}\r
    else:\r
        try:\r
            result = handler(ctx)\r
        except Exception as e:\r
            result = {"ok": False, "error": "handler_exception", "detail": str(e),\r
                      "trace": traceback.format_exc(limit=4)}\r
    log(f"   result: {json.dumps(result)[:300]}")\r
    report_result(device_id, device_key, ctx.action_id, result)\r
\r
# ---------------------------------------------------------------------------\r
# Heartbeat loop\r
# ---------------------------------------------------------------------------\r
\r
def _background_worker_report() -> dict:\r
    """Real process evidence for the always-on sibling workers.\r
\r
    Advertising a capability is not proof of a running worker. Report both\r
    children started by this process and healthy workers reused from the durable\r
    registry so a companion restart never multiplies worker processes.\r
    """\r
    report: dict = {}\r
    for name, script_name, log_name, _loop in _BACKGROUND_WORKERS:\r
        entry: dict = {"script": script_name, "pid": None, "alive": False}\r
        proc = _BACKGROUND_WORKER_PROCS.get(name)\r
        if proc is not None:\r
            entry["pid"] = proc.pid\r
            entry["alive"] = proc.poll() is None\r
            entry["exit_code"] = proc.returncode\r
            entry["reused"] = False\r
        else:\r
            reused_pid = int(_BACKGROUND_WORKER_REUSED.get(name) or 0)\r
            if reused_pid:\r
                entry["pid"] = reused_pid\r
                entry["alive"] = _pid_alive(reused_pid)\r
                entry["reused"] = True\r
        try:\r
            log_path = Path(__file__).parent / log_name\r
            if log_path.exists():\r
                st = log_path.stat()\r
                entry["log"] = log_name\r
                entry["log_bytes"] = st.st_size\r
                entry["log_mtime"] = st.st_mtime\r
        except Exception:\r
            pass\r
        report[name] = entry\r
    return report\r
\r
\r
def _runtime_routing_and_build_evidence() -> dict:\r
    """Report Project K as live destination, without rewriting an old install.\r
    The legacy build URL remains in the local running_build.json audit record.\r
    """\r
    source = ""\r
    try:\r
        if RUNNING_BUILD_FILE.exists():\r
            raw = json.loads(RUNNING_BUILD_FILE.read_text(encoding="utf-8"))\r
            source = str(raw.get("build_ref") or "")\r
    except (OSError, ValueError, TypeError):\r
        source = ""\r
    is_legacy = "pefatniumnrxwbgnwvvh" in source\r
    return {\r
        "production_project_ref": SUPABASE_PROJECT_REF,\r
        "production_companion_url": COMPANION_URL,\r
        "companion_build_ref": source if source and not is_legacy else None,\r
        "installed_build_source_class": "historical_legacy_release" if is_legacy else ("recorded_current_release" if source else "source_unrecorded"),\r
        "historical_build_ref_sha256": hashlib.sha256(source.encode("utf-8")).hexdigest() if is_legacy else None,\r
    }\r
\r
\r
def status_snapshot() -> dict:\r
    return {\r
        **_runtime_routing_and_build_evidence(),\r
        "hostname": socket.gethostname(),\r
        "os": f"{platform.system()} {platform.release()}",\r
        "python": sys.version.split()[0],\r
        "cwd": str(Path.cwd()),\r
        "ts": time.time(),\r
        "pid": os.getpid(),\r
        "instance_id": INSTANCE_ID,\r
        "boot_ts": BOOT_TS,\r
        "companion_version": COMPANION_VERSION,\r
        "keepalive_script_present": (_companion_script_dir() / "unk_keepalive.ps1").exists(),\r
        "background_workers": _background_worker_report(),\r
        "singleton_owner": _read_singleton_lock(),\r
        "capabilities": sorted(CAPABILITY_HANDLERS.keys()),\r
    }\r
\r
\r
def heartbeat(device_id: str, device_key: str) -> dict:\r
    r = requests.post(\r
        COMPANION_URL,\r
        headers={\r
            "apikey": SUPABASE_ANON_KEY,\r
            "Content-Type": "application/json",\r
            "X-Device-Id": device_id,\r
            "X-Device-Key": device_key,\r
        },\r
        json={"action": "heartbeat", "status": status_snapshot()},\r
        timeout=HTTP_TIMEOUT,\r
    )\r
    if r.status_code == 401:\r
        fatal("Device unauthorized. Re-run with --enroll.")\r
    if r.status_code != 200:\r
        raise RuntimeError(f"heartbeat HTTP {r.status_code}: {r.text[:300]}")\r
    return r.json()\r
\r
def _windows_prevent_sleep(enable: bool) -> None:\r
    """Keep Windows awake (screen + system) while the companion is running.\r
    ES_CONTINUOUS=0x80000000, ES_SYSTEM_REQUIRED=0x00000001, ES_AWAYMODE_REQUIRED=0x00000040.\r
    Passing ES_CONTINUOUS alone re-enables normal sleep. No-op on non-Windows."""\r
    if os.name != "nt":\r
        return\r
    try:\r
        import ctypes\r
        if enable:\r
            ES_CONTINUOUS = 0x80000000\r
            ES_SYSTEM_REQUIRED = 0x00000001\r
            ES_AWAYMODE_REQUIRED = 0x00000040\r
            ctypes.windll.kernel32.SetThreadExecutionState(\r
                ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_AWAYMODE_REQUIRED\r
            )\r
            log("sleep guard: Windows sleep + away-mode DISABLED while companion is running.")\r
        else:\r
            ctypes.windll.kernel32.SetThreadExecutionState(0x80000000)\r
    except Exception as e:\r
        log(f"sleep guard: could not set execution state ({e})")\r
\r
\r
HEARTBEAT_SIDECAR = COMPANION_DIR / "heartbeat.json"\r
PENDING_UPDATE_TOKEN_FILE = COMPANION_DIR / "pending_update_token.json"\r
\r
\r
def _write_heartbeat_sidecar(extra: dict | None = None) -> None:\r
    """Atomic write of a small heartbeat sidecar file that the on-device\r
    unk_supervisor.py reads to decide health. No network required."""\r
    try:\r
        payload = {\r
            "at": time.time(),\r
            "iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),\r
            "companion_version": COMPANION_VERSION,\r
            "pid": os.getpid(),\r
            "instance_id": INSTANCE_ID,\r
            "boot_ts": BOOT_TS,\r
            "local_process_alive": True,\r
        }\r
        payload.update(_runtime_routing_and_build_evidence())\r
        if extra: payload.update(extra)\r
        # Windows readers (supervisor, antivirus, health collectors) can\r
        # briefly lock the destination. Use a unique temp file and bounded\r
        # retries so one transient sharing violation cannot erase the signal.\r
        tmp = HEARTBEAT_SIDECAR.with_name(\r
            f".{HEARTBEAT_SIDECAR.name}.{os.getpid()}.{time.time_ns()}.tmp"\r
        )\r
        try:\r
            tmp.write_text(json.dumps(payload), encoding="utf-8")\r
            for attempt in range(5):\r
                try:\r
                    os.replace(tmp, HEARTBEAT_SIDECAR)\r
                    break\r
                except PermissionError:\r
                    if attempt == 4:\r
                        raise\r
                    time.sleep(0.05 * (attempt + 1))\r
        finally:\r
            try:\r
                tmp.unlink(missing_ok=True)\r
            except OSError:\r
                pass\r
    except Exception as e:\r
        log(f"heartbeat sidecar write failed: {e}")\r
\r
\r
def _cloud_backoff_with_local_liveness(seconds: float, consecutive_errors: int) -> None:\r
    """Keep the native watchdog informed during a Project K/cloud outage.\r
\r
    This is a LOCAL process heartbeat only, never a claim that remote Auth,\r
    the Data API, or a platform write worked. Bound each sleep to 20 seconds\r
    (well below the supervisor's 180-second stale threshold) while preserving\r
    the original total retry delay, single-instance owner and cloud failure.\r
    """\r
    remaining = max(0.0, float(seconds))\r
    while remaining > 0:\r
        interval = min(20.0, remaining)\r
        time.sleep(interval)\r
        remaining -= interval\r
        _write_heartbeat_sidecar({\r
            "cloud_ok": False,\r
            "cloud_state": "retry_wait",\r
            "consecutive_cloud_errors": consecutive_errors,\r
        })\r
\r
\r
def _ack_pending_update_token_if_any() -> bool:\r
    """If self_update+restart_companion left us a token, POST an ack to the\r
    platform's desktop-supervisor-report so the two-phase update verifier\r
    can move from 'staged' -> 'verifying'. Delete the token file after."""\r
    if not PENDING_UPDATE_TOKEN_FILE.exists():\r
        return True\r
    try:\r
        payload = json.loads(PENDING_UPDATE_TOKEN_FILE.read_text())\r
        token = payload.get("token")\r
        creds = load_credentials()\r
        if not token or not creds:\r
            return False\r
        did, dkey = creds\r
        r = requests.post(\r
            f"{FUNCTIONS_BASE}/desktop-supervisor-report",\r
            headers={\r
                "apikey": SUPABASE_ANON_KEY,\r
                "Authorization": f"Bearer {SUPABASE_ANON_KEY}",\r
                "Content-Type": "application/json",\r
                "X-Device-Id": did,\r
                "X-Device-Key": dkey,\r
            },\r
            json={"action": "ack_update_token", "token": token},\r
            timeout=HTTP_TIMEOUT,\r
        )\r
        log(f"post-update token ack -> HTTP {r.status_code} {r.text[:200]}")\r
        if r.status_code == 200:\r
            try:\r
                body = r.json()\r
            except Exception:\r
                body = {}\r
            if body.get("ok") is True or body.get("reason") == "token_not_active":\r
                try: PENDING_UPDATE_TOKEN_FILE.unlink()\r
                except Exception: pass\r
                return True\r
        return False\r
    except Exception as e:\r
        log(f"post-update token ack failed: {e}")\r
        return False\r
\r
\r
SINGLETON_LOCK_FILE = COMPANION_DIR / "companion.lock"\r
INSTANCE_REGISTRY_FILE = COMPANION_DIR / "companion_instances.json"\r
\r
\r
def _pid_alive(pid: int) -> bool:\r
    if not pid or pid == os.getpid():\r
        return pid == os.getpid()\r
    try:\r
        if sys.platform == "win32":\r
            r = subprocess.run(["tasklist", "/FI", f"PID eq {pid}"], capture_output=True, text=True, timeout=15)\r
            return str(pid) in (r.stdout or "")\r
        os.kill(pid, 0)\r
        return True\r
    except Exception:\r
        return False\r
\r
\r
def _terminate_pid(pid: int) -> bool:\r
    try:\r
        if sys.platform == "win32":\r
            subprocess.run(["taskkill", "/PID", str(pid), "/F"], capture_output=True, text=True, timeout=20)\r
        else:\r
            os.kill(pid, 9)\r
        return True\r
    except Exception:\r
        return False\r
\r
\r
def _read_singleton_lock() -> dict:\r
    try:\r
        return json.loads(SINGLETON_LOCK_FILE.read_text())\r
    except Exception:\r
        return {}\r
\r
\r
def _write_singleton_lock() -> None:\r
    try:\r
        SINGLETON_LOCK_FILE.write_text(json.dumps({\r
            "pid": os.getpid(),\r
            "instance_id": INSTANCE_ID,\r
            "companion_version": COMPANION_VERSION,\r
            "boot_ts": BOOT_TS,\r
        }))\r
    except Exception as e:\r
        log(f"singleton lock write failed: {e}")\r
\r
\r
def acquire_singleton() -> None:\r
    """Exactly one companion process may own this device.\r
\r
    Duplicate companions (often stale builds left over from restarts) each\r
    claim device actions, so a job can be picked up by an OLD build that no\r
    longer supports the requested capability. Newest boot wins: this process\r
    terminates any older live holder, and refuses to start if a NEWER one is\r
    already running.\r
    """\r
    prior = _read_singleton_lock()\r
    pid = int(prior.get("pid") or 0)\r
    if pid and pid != os.getpid() and _pid_alive(pid):\r
        if float(prior.get("boot_ts") or 0) > BOOT_TS:\r
            log(f"Newer companion already running (pid={pid}, {prior.get('companion_version')}). Exiting.")\r
            raise SystemExit(0)\r
        log(f"Terminating stale companion pid={pid} version={prior.get('companion_version')}")\r
        _terminate_pid(pid)\r
        time.sleep(2)\r
\r
    # Sweep every previously-seen companion PID. The lock only tracks the last\r
    # writer; older builds started before the lock existed are invisible to it\r
    # and would keep claiming device actions with outdated capabilities.\r
    try:\r
        seen = json.loads(INSTANCE_REGISTRY_FILE.read_text()) if INSTANCE_REGISTRY_FILE.exists() else []\r
    except Exception:\r
        seen = []\r
    for other in seen:\r
        try:\r
            opid = int(other)\r
        except Exception:\r
            continue\r
        if opid != os.getpid() and _pid_alive(opid):\r
            log(f"Terminating duplicate companion pid={opid}")\r
            _terminate_pid(opid)\r
    try:\r
        INSTANCE_REGISTRY_FILE.write_text(json.dumps([os.getpid()]))\r
    except Exception:\r
        pass\r
\r
    _write_singleton_lock()\r
\r
\r
\r
def _singleton_still_ours() -> bool:\r
    cur = _read_singleton_lock()\r
    if not cur:\r
        _write_singleton_lock()\r
        return True\r
    return str(cur.get("instance_id")) == INSTANCE_ID\r
\r
\r
def run_loop(device_id: str, device_key: str) -> None:\r
    _windows_prevent_sleep(True)\r
    log(f"Companion online. device_id={device_id} polling every {POLL_SECONDS}s.")\r
    log(f"Capabilities: {sorted(CAPABILITY_HANDLERS.keys())}")\r
    _ack_pending_update_token_if_any()\r
    _write_heartbeat_sidecar({"boot": True})\r
    consecutive_errors = 0\r
    last_cloud_ok = None\r
    while True:\r
        try:\r
            if not _singleton_still_ours():\r
                log("Another companion instance took ownership of this device. Exiting cleanly.")\r
                raise SystemExit(0)\r
\r
            # Local liveness must not depend on the cloud heartbeat. During an\r
            # internet outage the process is still healthy, so write the\r
            # sidecar before the network call to stop supervisor restart loops.\r
            _write_heartbeat_sidecar({"cloud_ok": last_cloud_ok, "cloud_state": "checking",\r
                                      "consecutive_cloud_errors": consecutive_errors})\r
            _ack_pending_update_token_if_any()\r
            data = heartbeat(device_id, device_key)\r
            consecutive_errors = 0  # healthy tick\r
            last_cloud_ok = True\r
            _write_heartbeat_sidecar({"cloud_ok": True, "cloud_state": "connected",\r
                                      "consecutive_cloud_errors": 0})\r
\r
            pending = data.get("pending_actions") or []\r
            if pending:\r
                log(f"heartbeat ok :: {len(pending)} pending action(s)")\r
                for action in pending:\r
                    # Browser publishing can legitimately run longer than the\r
                    # supervisor's stale-heartbeat threshold. Keep local\r
                    # liveness current while an action is executing so the\r
                    # supervisor never kills and replays the same browser job.\r
                    action_done = threading.Event()\r
                    action_id = str(action.get("id") or "unknown")\r
\r
                    def _action_liveness_tick() -> None:\r
                        while not action_done.wait(20):\r
                            _write_heartbeat_sidecar({\r
                                "cloud_ok": True,\r
                                "action_in_progress": action_id,\r
                                "consecutive_cloud_errors": 0,\r
                            })\r
\r
                    liveness_thread = threading.Thread(\r
                        target=_action_liveness_tick,\r
                        name=f"unk-action-liveness-{action_id[:8]}",\r
                        daemon=True,\r
                    )\r
                    liveness_thread.start()\r
                    try:\r
                        execute_action(device_id, device_key, action)\r
                    except Exception as ae:\r
                        log(f"action execution error (continuing): {ae}")\r
                    finally:\r
                        action_done.set()\r
                        liveness_thread.join(timeout=1)\r
                        _write_heartbeat_sidecar({\r
                            "cloud_ok": True,\r
                            "action_in_progress": None,\r
                            "consecutive_cloud_errors": 0,\r
                        })\r
            # Honor a restart_companion request AFTER results are posted.\r
            if _RESTART_REQUESTED.get("pending"):\r
                log(f"Restart requested ({_RESTART_REQUESTED.get('reason')}, strategy={_RESTART_REQUESTED.get('strategy')}).")\r
                if _RESTART_REQUESTED.get("strategy") == "supervisor_exit":\r
                    log("Exiting intentionally so UnkSupervisor proves relaunch.")\r
                    raise SystemExit(0)\r
                log("Re-executing current Python process…")\r
                try:\r
                    time.sleep(1)\r
                    os.execv(sys.executable, [sys.executable, os.path.abspath(__file__), *[a for a in sys.argv[1:] if a not in ("--enroll",)]])\r
                except Exception as re_exc:\r
                    log(f"os.execv failed ({re_exc}); exiting so supervisor can relaunch.")\r
                    raise SystemExit(0)\r
\r
        except KeyboardInterrupt:\r
            log("Stopped by user.")\r
            return\r
        except SystemExit:\r
            # heartbeat() calls fatal() on 401 -> SystemExit. Let the supervisor\r
            # restart us; do NOT die silently.\r
            log("Fatal auth/system exit — asking supervisor for a fresh process.")\r
            raise\r
        except Exception as e:\r
            consecutive_errors += 1\r
            last_cloud_ok = False\r
            _write_heartbeat_sidecar({"cloud_ok": False, "cloud_state": "error",\r
                "consecutive_cloud_errors": consecutive_errors, "last_cloud_error": str(e)[:300]})\r
            backoff = min(POLL_SECONDS * (2 ** min(consecutive_errors, 4)), 300)\r
            log(f"heartbeat error #{consecutive_errors} ({e}); sleeping {backoff}s before retry")\r
            _cloud_backoff_with_local_liveness(backoff, consecutive_errors)\r
            continue\r
        time.sleep(POLL_SECONDS)\r
\r
\r
# ---------------------------------------------------------------------------\r
# Entry point\r
# ---------------------------------------------------------------------------\r
\r
_BACKGROUND_WORKER_PROCS: dict = {}\r
_BACKGROUND_WORKER_REUSED: dict[str, int] = {}\r
\r
# Background workers that must always be alive alongside the companion.\r
# Doctrine: no operator ever launches these by hand. If a worker is missing,\r
# the corresponding rail silently stops.\r
_BACKGROUND_WORKERS = (\r
    ("audio-worker", "media_audio_worker.py", "unk_audio_worker.log", "300"),\r
    ("mirror-worker", "media_mirror_worker.py", "unk_mirror_worker.log", "300"),\r
)\r
\r
\r
def _registered_background_worker_pids() -> dict[str, int]:\r
    try:\r
        raw = json.loads(BACKGROUND_WORKER_REGISTRY_FILE.read_text())\r
        if not isinstance(raw, dict):\r
            return {}\r
        return {\r
            str(name): int(pid)\r
            for name, pid in raw.items()\r
            if str(pid).isdigit() and int(pid) > 0\r
        }\r
    except Exception:\r
        return {}\r
\r
\r
def _discover_background_worker_pids(script_name: str) -> list[int]:\r
    """Find existing Windows workers by exact script basename.\r
\r
    The registry is the fast path. CIM discovery repairs old installations that\r
    predate the registry and lets startup collapse historical duplicates.\r
    """\r
    found: list[int] = []\r
    for name, pid in _registered_background_worker_pids().items():\r
        if name.endswith(script_name) and _pid_alive(pid):\r
            found.append(pid)\r
    if sys.platform != "win32":\r
        return sorted(set(found))\r
    safe = script_name.replace("'", "''")\r
    command = (\r
        "Get-CimInstance Win32_Process -Filter \\"Name LIKE 'python%'\\" | "\r
        f"Where-Object {{ $_.CommandLine -like '*{safe}*' }} | "\r
        "Select-Object -ExpandProperty ProcessId"\r
    )\r
    try:\r
        run = subprocess.run(\r
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", command],\r
            capture_output=True,\r
            text=True,\r
            timeout=30,\r
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),\r
        )\r
        for line in (run.stdout or "").splitlines():\r
            value = line.strip()\r
            if value.isdigit() and int(value) != os.getpid():\r
                found.append(int(value))\r
    except Exception:\r
        pass\r
    return sorted(set(pid for pid in found if _pid_alive(pid)))\r
\r
\r
def _write_background_worker_registry() -> None:\r
    """Atomically update OUR media workers without erasing other owners' PIDs.\r
\r
    The registry is a name->PID mapping, not an array. Another supervisor may\r
    register its own workers (for example ai-worker). Never normalize the\r
    registry on module import or silently discard unknown worker owners.\r
    """\r
    managed = {f"{name}:{script}" for name, script, _log, _loop in _BACKGROUND_WORKERS}\r
    payload: dict[str, int] = {}\r
    try:\r
        if BACKGROUND_WORKER_REGISTRY_FILE.exists():\r
            existing = json.loads(BACKGROUND_WORKER_REGISTRY_FILE.read_text(encoding="utf-8"))\r
            if not isinstance(existing, dict):\r
                raise ValueError("background_worker_registry_not_mapping")\r
            for key, pid in existing.items():\r
                if (isinstance(key, str) and key not in managed\r
                        and not isinstance(pid, bool) and str(pid).isdigit()\r
                        and int(pid) > 0):\r
                    payload[key] = int(pid)\r
    except (OSError, ValueError, TypeError) as exc:\r
        # A malformed/unreadable registry must remain intact for repair;\r
        # overwriting it would erase other workers' recovery evidence.\r
        print(f"[background-workers] registry read failed: {type(exc).__name__}")\r
        return\r
    for name, script_name, _log_name, _loop in _BACKGROUND_WORKERS:\r
        proc = _BACKGROUND_WORKER_PROCS.get(name)\r
        if proc is not None and proc.poll() is None:\r
            payload[f"{name}:{script_name}"] = proc.pid\r
            continue\r
        reused = int(_BACKGROUND_WORKER_REUSED.get(name) or 0)\r
        if reused and _pid_alive(reused):\r
            payload[f"{name}:{script_name}"] = reused\r
    try:\r
        tmp = BACKGROUND_WORKER_REGISTRY_FILE.with_suffix(".json.tmp")\r
        tmp.write_text(json.dumps(payload))\r
        os.replace(tmp, BACKGROUND_WORKER_REGISTRY_FILE)\r
    except Exception as exc:\r
        print(f"[background-workers] registry write failed: {exc}")\r
\r
def _spawn_background_worker(name: str, script_name: str, log_name: str, loop_seconds: str) -> None:\r
    """Reuse one healthy worker and terminate historical duplicates before spawn."""\r
    try:\r
        existing = _discover_background_worker_pids(script_name)\r
        if existing:\r
            keep = existing[-1]\r
            for duplicate in existing[:-1]:\r
                _terminate_pid(duplicate)\r
            _BACKGROUND_WORKER_REUSED[name] = keep\r
            _write_background_worker_registry()\r
            print(\r
                f"[{name}] reused pid={keep}; "\r
                f"removed_duplicates={max(0, len(existing) - 1)}"\r
            )\r
            return\r
\r
        worker = Path(__file__).parent / script_name\r
        if not worker.exists():\r
            print(f"[{name}] script not found at {worker}, skipping")\r
            return\r
        log_path = Path(__file__).parent / log_name\r
        log_fh = open(log_path, "ab")\r
        creationflags = 0\r
        if sys.platform == "win32":\r
            creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)\r
        proc = subprocess.Popen(\r
            [sys.executable, str(worker), "--loop", loop_seconds],\r
            stdout=log_fh, stderr=log_fh,\r
            cwd=str(worker.parent),\r
            creationflags=creationflags,\r
        )\r
        _BACKGROUND_WORKER_PROCS[name] = proc\r
        _write_background_worker_registry()\r
        print(f"[{name}] spawned pid={proc.pid} log={log_path}")\r
    except Exception as exc:\r
        print(f"[{name}] failed to spawn: {exc}")\r
\r
\r
def _spawn_background_workers() -> None:\r
    for name, script_name, log_name, loop_seconds in _BACKGROUND_WORKERS:\r
        _spawn_background_worker(name, script_name, log_name, loop_seconds)\r
\r
\r
def main() -> None:\r
\r
    ap = argparse.ArgumentParser(description="Unk Desktop Companion")\r
    ap.add_argument("--enroll", action="store_true", help="Force re-enrollment")\r
    ap.add_argument("--status", action="store_true", help="One-shot heartbeat then exit")\r
    args = ap.parse_args()\r
\r
    creds = None if args.enroll else load_credentials()\r
    if creds is None:\r
        creds = enroll_interactive()\r
    device_id, device_key = creds\r
\r
    if args.status:\r
        data = heartbeat(device_id, device_key)\r
        print(json.dumps(data, indent=2))\r
        return\r
\r
    acquire_singleton()\r
    _spawn_background_workers()\r
    run_loop(device_id, device_key)\r
\r
\r
if __name__ == "__main__":\r
    try:\r
        main()\r
    except KeyboardInterrupt:\r
        log("Stopped by user.")\r
    except SystemExit:\r
        raise\r
    except Exception as exc:\r
        log(f"FATAL: {exc}")\r
        try:\r
            with LOG_FILE.open("a", encoding="utf-8") as f:\r
                f.write(traceback.format_exc() + "\\n")\r
        except Exception:\r
            pass\r
        pause_before_exit()\r
        raise SystemExit(1)\r
`,Kn=`# install_supervisor.ps1 — one-time durable install for the Unk supervisor.\r
# Registers self-healing Scheduled Tasks:\r
#   - UnkSupervisor runs unk_supervisor.py under the signed-in user session.\r
#   - UnkSupervisorKeepAlive runs every 5 minutes and restarts/recreates\r
#     UnkSupervisor if Windows stops it, the task disappears, or its marker\r
#     goes stale.\r
#   - UnkSupervisorBootKeepAlive runs as SYSTEM at startup when the installer\r
#     has elevation; it repairs/starts the user-session supervisor as soon as\r
#     Windows has an interactive session available.\r
# Also installs a Startup-folder fallback that runs the keepalive script.\r
#\r
# Run from inside the extracted desktop-companion folder:\r
#   powershell -ExecutionPolicy Bypass -File .\\install_supervisor.ps1\r
#\r
# Important: verification failure no longer removes the scheduled tasks. If\r
# network, auth, or dependencies are temporarily bad, the keepalive remains\r
# installed and keeps retrying instead of leaving Ground Zero permanently dead.\r
param(\r
  [switch]$Uninstall,\r
  [switch]$RepairOnly,\r
  [switch]$SkipVerify\r
)\r
\r
$ErrorActionPreference = "Stop"\r
Set-Location -Path $PSScriptRoot\r
\r
# --- Self-relocate out of %TEMP% -------------------------------------------------\r
# Windows wipes %TEMP% on updates / Storage Sense / some sign-ins. If the installer\r
# was launched from an extracted zip in Temp, the resulting Scheduled Task would\r
# point to a folder that vanishes — which is exactly why Unk keeps "breaking every\r
# time I sign in." Copy the whole desktop-companion folder to a durable location\r
# and re-launch ourselves from there before registering anything.\r
$DurableRoot = Join-Path $env:LOCALAPPDATA "UnkCompanion"\r
$currentPath = $PSScriptRoot\r
$isTempPath = ($currentPath -like "*\\Temp\\*") -or ($currentPath -like "$env:TEMP*") -or ($currentPath -like "$env:TMP*")\r
if ($isTempPath -and -not $RepairOnly) {\r
  Write-Host "==> Detected install running from %TEMP%. Relocating to $DurableRoot so Unk survives reboots and temp cleanup." -ForegroundColor Cyan\r
  try {\r
    if (Test-Path $DurableRoot) {\r
      # Remove old copy so we get a clean set of files (preserves ~/.unk-companion state dir, which is elsewhere).\r
      Remove-Item -Path $DurableRoot -Recurse -Force -ErrorAction SilentlyContinue\r
    }\r
    New-Item -ItemType Directory -Force -Path $DurableRoot | Out-Null\r
    Copy-Item -Path (Join-Path $currentPath "*") -Destination $DurableRoot -Recurse -Force\r
    $durableInstaller = Join-Path $DurableRoot "install_supervisor.ps1"\r
    if (Test-Path $durableInstaller) {\r
      Write-Host "==> Re-launching installer from durable path: $durableInstaller" -ForegroundColor Cyan\r
      $argList = @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", "\`"$durableInstaller\`"")\r
      if ($SkipVerify) { $argList += "-SkipVerify" }\r
      & powershell.exe @argList\r
      exit $LASTEXITCODE\r
    }\r
  } catch {\r
    Write-Host "==> Relocate failed ($($_.Exception.Message)); continuing from current path but Unk may break again on next temp cleanup." -ForegroundColor Yellow\r
  }\r
}\r
\r
\r
# --- Self-elevate if scheduled-task registration would require admin ---------\r
# On some Windows configurations Register-ScheduledTask against the root task\r
# path is denied for non-admin users (HRESULT 0x80070005). Unk runs unelevated\r
# by design, so when we detect we are not already admin we re-launch this\r
# installer via Start-Process -Verb RunAs. That triggers a UAC prompt for the\r
# interactive user; after they approve, the elevated copy registers the tasks\r
# and returns. RepairOnly runs (invoked by unk_keepalive) do NOT self-elevate\r
# — they stay unelevated and simply skip if they cannot write.\r
if (-not $RepairOnly) {\r
  try {\r
    $currentIdentity = [Security.Principal.WindowsIdentity]::GetCurrent()\r
    $currentPrincipal = New-Object Security.Principal.WindowsPrincipal($currentIdentity)\r
    $isCurrentAdmin = $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)\r
  } catch { $isCurrentAdmin = $false }\r
  if (-not $isCurrentAdmin) {\r
    Write-Host "==> Not running elevated. Requesting UAC approval to register scheduled tasks..." -ForegroundColor Yellow\r
    $selfPath = $MyInvocation.MyCommand.Path\r
    if (-not $selfPath) { $selfPath = Join-Path $PSScriptRoot "install_supervisor.ps1" }\r
    $argList = @("-NoProfile","-ExecutionPolicy","Bypass","-File","\`"$selfPath\`"")\r
    if ($SkipVerify) { $argList += "-SkipVerify" }\r
    try {\r
      $proc = Start-Process -FilePath "powershell.exe" -ArgumentList $argList -Verb RunAs -Wait -PassThru\r
      Write-Host "==> Elevated installer exit code: $($proc.ExitCode)" -ForegroundColor Cyan\r
      exit $proc.ExitCode\r
    } catch {\r
      Write-Host "==> UAC approval declined or elevation failed: $($_.Exception.Message)" -ForegroundColor Red\r
      exit 1223  # ERROR_CANCELLED\r
    }\r
  }\r
}\r
\r
\r
$TaskName = "UnkSupervisor"\r
$KeepAliveTaskName = "UnkSupervisorKeepAlive"\r
$StartupFolder = Join-Path $env:APPDATA "Microsoft\\Windows\\Start Menu\\Programs\\Startup"\r
$StartupFallback = Join-Path $StartupFolder "UnkSupervisorKeepAlive.vbs"\r
$StartupFallbackLegacy = Join-Path $StartupFolder "UnkSupervisorKeepAlive.cmd"\r
$SupervisorLauncher = Join-Path $PSScriptRoot "UnkSupervisorHidden.vbs"\r
$KeepAliveLauncher = Join-Path $PSScriptRoot "UnkKeepAliveHidden.vbs"\r
$BootKeepAliveLauncher = Join-Path $PSScriptRoot "UnkBootKeepAliveHidden.vbs"\r
\r
$StateDir = Join-Path $env:USERPROFILE ".unk-companion"\r
$KeepAliveLog = Join-Path $StateDir "keepalive.log"\r
\r
function Write-InstallLog([string]$Message, [string]$Color = "Gray") {\r
  Write-Host $Message -ForegroundColor $Color\r
  try {\r
    New-Item -ItemType Directory -Force -Path $StateDir | Out-Null\r
    "[$(Get-Date -Format o)] $Message" | Add-Content -Path $KeepAliveLog -Encoding UTF8\r
  } catch {}\r
}\r
\r
function Get-PythonExe {\r
  # Prefer pythonw.exe so the supervisor runs windowless (no black console flash on logon\r
  # or on every restart). Fall back to python.exe / py.exe if pythonw is not present.\r
  $pyw = (Get-Command pythonw -ErrorAction SilentlyContinue)\r
  if ($pyw) { return $pyw.Source }\r
  $python = (Get-Command python -ErrorAction SilentlyContinue)\r
  if ($python) {\r
    $pywGuess = Join-Path (Split-Path $python.Source -Parent) "pythonw.exe"\r
    if (Test-Path $pywGuess) { return $pywGuess }\r
    return $python.Source\r
  }\r
  $py = (Get-Command py -ErrorAction SilentlyContinue)\r
  if ($py) { return $py.Source }\r
  return $null\r
}\r
\r
\r
function Register-UnkSupervisorTask([string]$PyExe, [string]$SupervisorPath) {\r
  # Keep wscript alive while Python runs so Task Scheduler accurately reports\r
  # Running, but use window style 0 so no console can flash or remain open.\r
  $escapedPy = $PyExe.Replace('"', '""')\r
  $escapedSupervisor = $SupervisorPath.Replace('"', '""')\r
  @"\r
Set WshShell = CreateObject("WScript.Shell")\r
exitCode = WshShell.Run("""$escapedPy"" ""$escapedSupervisor""", 0, True)\r
WScript.Quit exitCode\r
"@ | Set-Content -Path $SupervisorLauncher -Encoding ASCII\r
  $action = New-ScheduledTaskAction -Execute "wscript.exe" -Argument "\`"$SupervisorLauncher\`"" -WorkingDirectory $PSScriptRoot\r
  $triggers = @(\r
    (New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME),\r
    (New-ScheduledTaskTrigger -AtStartup)\r
  )\r
  $settings = New-ScheduledTaskSettingsSet \`\r
    -AllowStartIfOnBatteries \`\r
    -DontStopIfGoingOnBatteries \`\r
    -RestartInterval (New-TimeSpan -Minutes 1) \`\r
    -RestartCount 999 \`\r
    -StartWhenAvailable \`\r
    -ExecutionTimeLimit ([TimeSpan]::Zero) \`\r
    -WakeToRun \`\r
    -Hidden\r
  $principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited\r
  Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $triggers \`\r
    -Settings $settings -Principal $principal -Force | Out-Null\r
\r
  # Add workstation-unlock as an event trigger. PowerShell's ScheduledTasks\r
  # cmdlets do not expose unlock triggers directly, so patch the task XML.\r
  try {\r
    $xml = [xml](Export-ScheduledTask -TaskName $TaskName)\r
    $ns = $xml.Task.NamespaceURI\r
    $hasUnlock = $false\r
    foreach ($t in $xml.Task.Triggers.ChildNodes) {\r
      if ($t.Name -eq 'SessionStateChangeTrigger' -and $t.StateChange -eq 'SessionUnlock') { $hasUnlock = $true }\r
    }\r
    if (-not $hasUnlock) {\r
      $unlock = $xml.CreateElement('SessionStateChangeTrigger', $ns)\r
      $enabled = $xml.CreateElement('Enabled', $ns); $enabled.InnerText = 'true'; $unlock.AppendChild($enabled) | Out-Null\r
      $user = $xml.CreateElement('UserId', $ns); $user.InnerText = "$env:USERDOMAIN\\$env:USERNAME"; $unlock.AppendChild($user) | Out-Null\r
      $state = $xml.CreateElement('StateChange', $ns); $state.InnerText = 'SessionUnlock'; $unlock.AppendChild($state) | Out-Null\r
      $xml.Task.Triggers.AppendChild($unlock) | Out-Null\r
      Register-ScheduledTask -TaskName $TaskName -Xml $xml.OuterXml -Force | Out-Null\r
    }\r
  } catch {\r
    Write-InstallLog "==> Unlock trigger patch warning for \${TaskName}: $($_.Exception.Message)" "Yellow"\r
  }\r
}\r
\r
function Register-UnkKeepAliveTask([string]$KeepAlivePath) {\r
  if (-not (Test-Path $KeepAlivePath)) { return }\r
  $escapedKeepAlive = $KeepAlivePath.Replace('"', '""')\r
  @"\r
Set WshShell = CreateObject("WScript.Shell")\r
exitCode = WshShell.Run("powershell.exe -NoProfile -NonInteractive -WindowStyle Hidden -ExecutionPolicy Bypass -File ""$escapedKeepAlive""", 0, True)\r
WScript.Quit exitCode\r
"@ | Set-Content -Path $KeepAliveLauncher -Encoding ASCII\r
  $action = New-ScheduledTaskAction -Execute "wscript.exe" -Argument "\`"$KeepAliveLauncher\`"" -WorkingDirectory $PSScriptRoot\r
  $repeatTrigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) \`\r
    -RepetitionInterval (New-TimeSpan -Minutes 5) \`\r
    -RepetitionDuration (New-TimeSpan -Days 3650)\r
  $triggers = @(\r
    (New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME),\r
    $repeatTrigger\r
  )\r
  $settings = New-ScheduledTaskSettingsSet \`\r
    -AllowStartIfOnBatteries \`\r
    -DontStopIfGoingOnBatteries \`\r
    -StartWhenAvailable \`\r
    -ExecutionTimeLimit (New-TimeSpan -Minutes 3) \`\r
    -WakeToRun \`\r
    -Hidden\r
  $principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited\r
  Register-ScheduledTask -TaskName $KeepAliveTaskName -Action $action -Trigger $triggers \`\r
    -Settings $settings -Principal $principal -Force | Out-Null\r
\r
  try {\r
    $xml = [xml](Export-ScheduledTask -TaskName $KeepAliveTaskName)\r
    $ns = $xml.Task.NamespaceURI\r
    $unlock = $xml.CreateElement('SessionStateChangeTrigger', $ns)\r
    $enabled = $xml.CreateElement('Enabled', $ns); $enabled.InnerText = 'true'; $unlock.AppendChild($enabled) | Out-Null\r
    $user = $xml.CreateElement('UserId', $ns); $user.InnerText = "$env:USERDOMAIN\\$env:USERNAME"; $unlock.AppendChild($user) | Out-Null\r
    $state = $xml.CreateElement('StateChange', $ns); $state.InnerText = 'SessionUnlock'; $unlock.AppendChild($state) | Out-Null\r
    $xml.Task.Triggers.AppendChild($unlock) | Out-Null\r
    Register-ScheduledTask -TaskName $KeepAliveTaskName -Xml $xml.OuterXml -Force | Out-Null\r
  } catch {\r
    Write-InstallLog "==> Unlock trigger patch warning for \${KeepAliveTaskName}: $($_.Exception.Message)" "Yellow"\r
  }\r
}\r
\r
function Register-UnkSystemBootKeepAlive([string]$KeepAlivePath) {\r
  if (-not (Test-Path $KeepAlivePath)) { return }\r
  try {\r
    $isAdmin = $false\r
    try {\r
      $identity = [Security.Principal.WindowsIdentity]::GetCurrent()\r
      $principal = New-Object Security.Principal.WindowsPrincipal($identity)\r
      $isAdmin = $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)\r
    } catch {}\r
    if (-not $isAdmin) {\r
      Write-InstallLog "==> System boot keepalive skipped; rerun 'Run installer as admin' to add boot-level repair." "Yellow"\r
      return\r
    }\r
    $bootTaskName = "UnkSupervisorBootKeepAlive"\r
    $repairPath = Join-Path $PSScriptRoot "repair_persistence.ps1"\r
    $escapedKeepAlive = $KeepAlivePath.Replace('"', '""')\r
    if (Test-Path $repairPath) {\r
      $escapedRepair = $repairPath.Replace('"', '""')\r
      $bootCommand = "powershell.exe -NoProfile -NonInteractive -WindowStyle Hidden -ExecutionPolicy Bypass -Command ""& '$escapedRepair' -Apply -ActionId boot_keepalive; & '$escapedKeepAlive'"""\r
    } else {\r
      $bootCommand = "powershell.exe -NoProfile -NonInteractive -WindowStyle Hidden -ExecutionPolicy Bypass -File ""$escapedKeepAlive"""\r
    }\r
    @"\r
Set WshShell = CreateObject("WScript.Shell")\r
exitCode = WshShell.Run("$bootCommand", 0, True)\r
WScript.Quit exitCode\r
"@ | Set-Content -Path $BootKeepAliveLauncher -Encoding ASCII\r
    $action = New-ScheduledTaskAction -Execute "wscript.exe" -Argument "\`"$BootKeepAliveLauncher\`"" -WorkingDirectory $PSScriptRoot\r
    $trigger = New-ScheduledTaskTrigger -AtStartup\r
    $settings = New-ScheduledTaskSettingsSet \`\r
      -AllowStartIfOnBatteries \`\r
      -DontStopIfGoingOnBatteries \`\r
      -StartWhenAvailable \`\r
      -ExecutionTimeLimit (New-TimeSpan -Minutes 3) \`\r
      -WakeToRun \`\r
      -Hidden\r
    $principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -RunLevel Highest\r
    Register-ScheduledTask -TaskName $bootTaskName -Action $action -Trigger $trigger \`\r
      -Settings $settings -Principal $principal -Force | Out-Null\r
    Write-InstallLog "==> Registered SYSTEM boot keepalive $bootTaskName" "Cyan"\r
  } catch {\r
    Write-InstallLog "==> System boot keepalive install warning: $($_.Exception.Message)" "Yellow"\r
  }\r
}\r
\r
function Install-StartupFallback([string]$KeepAlivePath) {\r
  if (-not (Test-Path $KeepAlivePath)) { return }\r
  New-Item -ItemType Directory -Force -Path $StartupFolder | Out-Null\r
  # Legacy .cmd flashed a black console window on every logon. Replace with a\r
  # WScript shim (Run flag 0 = hidden) so nothing appears on screen.\r
  try { Remove-Item -Path $StartupFallbackLegacy -Force -ErrorAction SilentlyContinue } catch {}\r
  $psCmd = "powershell.exe -NoProfile -NonInteractive -WindowStyle Hidden -ExecutionPolicy Bypass -File ""$KeepAlivePath"""\r
  @"\r
' UnkSupervisorKeepAlive.vbs — runs the PowerShell keepalive with no visible window.\r
Set WshShell = CreateObject("WScript.Shell")\r
WshShell.Run "$psCmd", 0, False\r
"@ | Set-Content -Path $StartupFallback -Encoding ASCII\r
}\r
\r
\r
if ($Uninstall) {\r
  Write-InstallLog "==> Removing scheduled tasks $TaskName / $KeepAliveTaskName" "Yellow"\r
  try { Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction Stop } catch { Write-Host "Task not present." }\r
  try { Unregister-ScheduledTask -TaskName $KeepAliveTaskName -Confirm:$false -ErrorAction Stop } catch { Write-Host "Keepalive task not present." }\r
  try { Unregister-ScheduledTask -TaskName "UnkSupervisorBootKeepAlive" -Confirm:$false -ErrorAction Stop } catch { Write-Host "Boot keepalive task not present." }\r
  try { Remove-Item -Path $StartupFallback -Force -ErrorAction SilentlyContinue } catch {}\r
  try { Remove-Item -Path $StartupFallbackLegacy,$SupervisorLauncher,$KeepAliveLauncher,$BootKeepAliveLauncher -Force -ErrorAction SilentlyContinue } catch {}\r
  Write-Host "Done."; exit 0\r
}\r
\r
# 1. Find Python\r
$pyExe = Get-PythonExe\r
if (-not $pyExe) {\r
  Write-Host "Python not found. Install Python 3 from https://python.org and re-run." -ForegroundColor Red\r
  exit 1\r
}\r
$supervisorPath = Join-Path $PSScriptRoot "unk_supervisor.py"\r
$keepAlivePath = Join-Path $PSScriptRoot "unk_keepalive.ps1"\r
if (-not (Test-Path $supervisorPath)) {\r
  Write-Host "unk_supervisor.py not found next to this script." -ForegroundColor Red\r
  exit 1\r
}\r
\r
if (-not $RepairOnly) {\r
  Write-InstallLog "==> Ensuring dependencies (requests, pillow, keyring, playwright)..." "Cyan"\r
  & $pyExe -m pip install --quiet --disable-pip-version-check requests pillow keyring playwright | Out-Null\r
  try { & $pyExe -m playwright install chromium | Out-Null } catch { Write-InstallLog "Playwright browser install skipped/failed; companion will retry when needed." "Yellow" }\r
\r
  # 2. Stop any competing launch_unk.bat window quietly (best-effort).\r
  try {\r
    Get-CimInstance Win32_Process -Filter "Name='cmd.exe'" | Where-Object {\r
      $_.CommandLine -match "launch_unk.bat"\r
    } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }\r
  } catch {}\r
\r
  # Stop old foreground companion processes so the supervisor is the single owner.\r
  try {\r
    Get-CimInstance Win32_Process | Where-Object {\r
      $_.CommandLine -match "unk_companion\\.py" -and $_.ProcessId -ne $PID\r
    } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }\r
  } catch {}\r
}\r
\r
# Convergence cleanup: old task registrations could leave several visible\r
# consoles and supervisors. Stop only Unk-owned processes; never touch Chrome\r
# or unrelated terminals, so active Facebook publishing remains unaffected.\r
try {\r
  Get-CimInstance Win32_Process | Where-Object {\r
    $_.ProcessId -ne $PID -and (\r
      ($_.Name -match '^(cmd|powershell)\\.exe$' -and $_.CommandLine -match '(launch_unk\\.bat|unk_(audio|mirror)_worker|unk_(companion|supervisor|keepalive))') -or\r
      ($_.Name -match '^python(w)?\\.exe$' -and $_.CommandLine -match 'unk_supervisor\\.py')\r
    )\r
  } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }\r
} catch {}\r
\r
# Remove every known legacy Startup launcher. Shortcuts and BAT/CMD copies can\r
# otherwise recreate the old visible console loop at each sign-in even though\r
# the canonical scheduled task is already healthy.\r
try {\r
  Get-ChildItem -Path $StartupFolder -Force -ErrorAction SilentlyContinue | Where-Object {\r
    $_.Name -match '^(launch_unk|unk[_ -]?(companion|supervisor|keepalive)).*\\.(bat|cmd|lnk)$'\r
  } | Remove-Item -Force -ErrorAction SilentlyContinue\r
} catch {}\r
\r
# 3. Register self-healing scheduled tasks + Startup fallback.\r
try {\r
  $existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue\r
  if ($existing -and $existing.State -eq "Running") {\r
    Write-InstallLog "==> Restarting existing $TaskName before repair" "Cyan"\r
    Stop-ScheduledTask -TaskName $TaskName | Out-Null\r
    Start-Sleep -Seconds 2\r
  }\r
} catch {}\r
Write-InstallLog "==> Registering scheduled task $TaskName" "Cyan"\r
Register-UnkSupervisorTask -PyExe $pyExe -SupervisorPath $supervisorPath\r
Write-InstallLog "==> Registering keepalive task $KeepAliveTaskName" "Cyan"\r
Register-UnkKeepAliveTask -KeepAlivePath $keepAlivePath\r
Register-UnkSystemBootKeepAlive -KeepAlivePath $keepAlivePath\r
Install-StartupFallback -KeepAlivePath $keepAlivePath\r
\r
try {\r
  Start-ScheduledTask -TaskName $TaskName | Out-Null\r
} catch {\r
  $current = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue\r
  if (-not $current -or $current.State -ne "Running") { throw }\r
}\r
\r
if ($RepairOnly -or $SkipVerify) {\r
  Write-InstallLog "==> Supervisor/keepalive tasks repaired. Verification skipped." "Green"\r
  exit 0\r
}\r
\r
Write-InstallLog "==> Task started. Waiting up to 90s for first verified heartbeat..." "Cyan"\r
\r
$heartbeatFile = Join-Path $env:USERPROFILE ".unk-companion\\heartbeat.json"\r
$startedAt = [double]((Get-Date -UFormat %s))\r
$deadline = (Get-Date).AddSeconds(90)\r
$ok = $false\r
while ((Get-Date) -lt $deadline) {\r
  if (Test-Path $heartbeatFile) {\r
    try {\r
      $data = Get-Content $heartbeatFile -Raw | ConvertFrom-Json\r
      $age = [double]((Get-Date -UFormat %s)) - [double]$data.at\r
      $boot = $false\r
      try { $boot = [bool]$data.boot } catch {}\r
      if ($age -lt 120 -and [double]$data.at -ge $startedAt -and -not $boot) { $ok = $true; break }\r
    } catch {}\r
  }\r
  Start-Sleep -Seconds 3\r
}\r
\r
if ($ok) {\r
  Write-Host "==> Verified heartbeat received. Unk supervisor + keepalive are installed and running." -ForegroundColor Green\r
  Write-Host "    Logs: $env:USERPROFILE\\.unk-companion\\supervisor.log"\r
  Write-Host "    Keepalive: $env:USERPROFILE\\.unk-companion\\keepalive.log"\r
  Write-Host "    Uninstall: powershell -File .\\install_supervisor.ps1 -Uninstall"\r
} else {\r
  Write-Host "==> No verified heartbeat in 90s. Keeping supervisor + keepalive installed so they continue retrying." -ForegroundColor Yellow\r
  Write-Host "    Check $env:USERPROFILE\\.unk-companion\\supervisor.log and keepalive.log for details." -ForegroundColor Yellow\r
  exit 0\r
}\r
`,zn=`# unk_keepalive.ps1 — Windows Scheduled Task self-healer for UnkSupervisor.\r
# Runs every 5 minutes plus at logon. It repairs/starts the supervisor, keeps\r
# the durable Unk <-> OpenAI bridge alive, and restores the independent Remote\r
# Desktop Commander relay when its user-session agent is absent.\r
\r
$ErrorActionPreference = "SilentlyContinue"\r
Set-Location -Path $PSScriptRoot\r
\r
$TaskName = "UnkSupervisor"\r
$StateDir = Join-Path $env:USERPROFILE ".unk-companion"\r
$LogFile = Join-Path $StateDir "keepalive.log"\r
$MarkerFile = Join-Path $StateDir "supervisor_alive.marker"\r
$Installer = Join-Path $PSScriptRoot "install_supervisor.ps1"\r
$PersistenceRepair = Join-Path $PSScriptRoot "repair_persistence.ps1"\r
$PowerReceiptFile = Join-Path $StateDir "persistence_repair_latest.json"\r
$PowerRepairCadenceSeconds = 3600\r
$BridgeWorker = Join-Path $PSScriptRoot "unk_ai_bridge.py"\r
$BridgeFallbackWorker = Join-Path $PSScriptRoot "unk_ai_bridge_daemon.py"\r
$FixerWorker = Join-Path $PSScriptRoot "unk_fixer_worker.py"\r
$MirrorWorker = Join-Path $PSScriptRoot "media_mirror_worker.py"\r
$MirrorWorkerProtocol = "2026-11-01-lease-ack-v1"\r
$MirrorWorkerStdout = Join-Path $StateDir "media_mirror_worker.stdout.log"\r
$MirrorWorkerStderr = Join-Path $StateDir "media_mirror_worker.stderr.log"\r
$MirrorHealthReceipt = Join-Path $StateDir "media_mirror_worker_health.json"\r
$CanonicalMirrorOrigin = "https://kwbegsybeyyxfmavjswv.supabase.co"\r
$RemoteRelayReceipt = Join-Path $StateDir "remote_desktop_commander_watchdog.json"\r
$RemoteRelayRunnerReceipt = Join-Path $StateDir "remote_desktop_commander_relay_latest.json"\r
$RemoteDesktopCommanderPackage = '@wonderwhy-er/desktop-commander@latest'\r
$RemoteRelayScript = Join-Path $PSScriptRoot "remote_desktop_commander_relay.ps1"\r
$RemoteRelayTaskName = "UnkRemoteDesktopCommanderRelay"\r
$RemoteRelayTaskSpecVersion = "2026-11-07-v7-redacted-device-log-signals"\r
\r
function Log([string]$Message) {\r
  try {\r
    New-Item -ItemType Directory -Force -Path $StateDir | Out-Null\r
    "[$(Get-Date -Format o)] $Message" | Add-Content -Path $LogFile -Encoding UTF8\r
  } catch {}\r
}\r
\r
function Write-MediaMirrorHealthReceipt([string]$State, [int]$WorkerProcessId = 0) {\r
  # An observed process or a successful Scheduled Task tick never proves that\r
  # Storage bytes were transferred. Keep a separate redacted health snapshot.\r
  try {\r
    New-Item -ItemType Directory -Force -Path $StateDir | Out-Null\r
    @{\r
      checked_at = (Get-Date).ToString('o')\r
      state = $State\r
      process_visible = ($WorkerProcessId -gt 0)\r
      process_id = $WorkerProcessId\r
      transfer_verified = $false\r
      canonical_origin = $CanonicalMirrorOrigin\r
    } | ConvertTo-Json -Depth 3 | Set-Content -Path $MirrorHealthReceipt -Encoding UTF8\r
  } catch {\r
    Log "Media mirror health receipt unavailable; error_class=$($_.Exception.GetType().Name)"\r
  }\r
}\r
\r
function Write-RemoteRelayReceipt([hashtable]$Receipt) {\r
  try {\r
    New-Item -ItemType Directory -Force -Path $StateDir | Out-Null\r
    $Receipt['checked_at'] = (Get-Date).ToString('o')\r
    $Receipt['package'] = $RemoteDesktopCommanderPackage\r
    $Receipt['task_name'] = $RemoteRelayTaskName\r
    $Receipt['task_spec_version'] = $RemoteRelayTaskSpecVersion\r
    $Receipt | ConvertTo-Json -Depth 6 | Set-Content -Path $RemoteRelayReceipt -Encoding UTF8\r
  } catch {}\r
}\r
\r
function MarkerAgeSeconds {\r
  if (-not (Test-Path $MarkerFile)) { return $null }\r
  try { return [int]((Get-Date) - (Get-Item $MarkerFile).LastWriteTime).TotalSeconds } catch { return $null }\r
}\r
\r
function ReceiptAgeSeconds([string]$Path) {\r
  if (-not (Test-Path $Path)) { return $null }\r
  try { return [int]((Get-Date) - (Get-Item $Path).LastWriteTime).TotalSeconds } catch { return $null }\r
}\r
\r
function Get-RemoteDesktopCommanderProcesses {\r
  try {\r
    return @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object {\r
      $cmd = [string]$_.CommandLine\r
      $cmd -and\r
      ($cmd -match '(?i)desktop-commander') -and\r
      ($cmd -match '(?i)(^|\\s)remote(\\s|$)')\r
    })\r
  } catch { return @() }\r
}\r
\r
function Find-RemoteDesktopCommanderProcess {\r
  return Get-RemoteDesktopCommanderProcesses | Select-Object -First 1\r
}\r
\r
function Find-TaskOwnedRemoteDesktopCommanderProcess {\r
  try {\r
    $processes = @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue)\r
    if ($processes.Count -eq 0) { return $null }\r
\r
    $runnerPattern = [regex]::Escape($RemoteRelayScript)\r
    $runners = @($processes | Where-Object {\r
      $cmd = [string]$_.CommandLine\r
      $cmd -and\r
      ($cmd -match '(?i)powershell(?:\\.exe)?') -and\r
      ($cmd -match $runnerPattern)\r
    })\r
    if ($runners.Count -eq 0) { return $null }\r
\r
    $byPid = @{}\r
    foreach ($process in $processes) {\r
      $byPid[[int]$process.ProcessId] = $process\r
    }\r
\r
    foreach ($relay in @($processes | Where-Object {\r
      $cmd = [string]$_.CommandLine\r
      $cmd -and\r
      ($cmd -match '(?i)desktop-commander') -and\r
      ($cmd -match '(?i)(^|\\s)remote(\\s|$)')\r
    })) {\r
      $cursor = $relay\r
      $visited = @{}\r
      for ($depth = 0; $depth -lt 16; $depth++) {\r
        $parentPid = [int]$cursor.ParentProcessId\r
        if ($parentPid -le 0 -or $visited.ContainsKey($parentPid)) { break }\r
        $visited[$parentPid] = $true\r
\r
        $runner = $runners | Where-Object { [int]$_.ProcessId -eq $parentPid } | Select-Object -First 1\r
        if ($runner) {\r
          return [pscustomobject]@{ Relay = $relay; Runner = $runner }\r
        }\r
\r
        if (-not $byPid.ContainsKey($parentPid)) { break }\r
        $cursor = $byPid[$parentPid]\r
      }\r
    }\r
  } catch {}\r
  return $null\r
}\r
\r
function Ensure-AIBridge {\r
  $worker = if (Test-Path $BridgeWorker) { $BridgeWorker } elseif (Test-Path $BridgeFallbackWorker) { $BridgeFallbackWorker } else { $null }\r
  if (-not $worker) {\r
    Log "AI bridge ensure skipped; bridge worker not installed."\r
    return\r
  }\r
  try {\r
    $leaf = [IO.Path]::GetFileName($worker)\r
    $running = Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object {\r
      $_.CommandLine -and $_.CommandLine -like "*$leaf*"\r
    } | Select-Object -First 1\r
    if ($running) { return }\r
\r
    $py = Get-Command pythonw -ErrorAction SilentlyContinue\r
    if (-not $py) { $py = Get-Command python -ErrorAction SilentlyContinue }\r
    if (-not $py) { $py = Get-Command py -ErrorAction SilentlyContinue }\r
    if (-not $py) {\r
      Log "AI bridge ensure failed; Python not found."\r
      return\r
    }\r
    $arg = if ($leaf -eq "unk_ai_bridge.py") { "--worker" } else { "" }\r
    if ($arg) {\r
      Start-Process -FilePath $py.Source -ArgumentList @("-u", $worker, $arg) -WorkingDirectory $PSScriptRoot -WindowStyle Hidden | Out-Null\r
    } else {\r
      Start-Process -FilePath $py.Source -ArgumentList @("-u", $worker) -WorkingDirectory $PSScriptRoot -WindowStyle Hidden | Out-Null\r
    }\r
    Log "AI bridge start requested. worker=$leaf"\r
  } catch {\r
    Log "AI bridge ensure failed: $($_.Exception.Message)"\r
  }\r
}\r
\r
\r
function Ensure-FixerWorker {\r
  if (-not (Test-Path $FixerWorker)) {\r
    Log "Fixer ensure skipped; worker not installed."\r
    return\r
  }\r
  try {\r
    $leaf = [IO.Path]::GetFileName($FixerWorker)\r
    $running = Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object {\r
      $_.CommandLine -and $_.CommandLine -like "*$leaf*"\r
    } | Select-Object -First 1\r
    if ($running) { return }\r
\r
    $py = Get-Command pythonw -ErrorAction SilentlyContinue\r
    if (-not $py) { $py = Get-Command python -ErrorAction SilentlyContinue }\r
    if (-not $py) { $py = Get-Command py -ErrorAction SilentlyContinue }\r
    if (-not $py) {\r
      Log "Fixer ensure failed; Python not found."\r
      return\r
    }\r
    Start-Process -FilePath $py.Source -ArgumentList @("-u", $FixerWorker) -WorkingDirectory $PSScriptRoot -WindowStyle Hidden | Out-Null\r
    Log "Fixer start requested. worker=$leaf"\r
  } catch {\r
    Log "Fixer ensure failed: $($_.Exception.Message)"\r
  }\r
}\r
\r
function Ensure-MediaMirrorWorker {\r
  # The existing Unk keepalive is the sole startup owner. SYSTEM never launches\r
  # private-media processes under a different identity or credential store.\r
  if ($env:USERNAME -eq "SYSTEM") { return }\r
  if (-not (Test-Path $MirrorWorker)) {\r
    Log "Media mirror worker is not installed; no process started."\r
    Write-MediaMirrorHealthReceipt 'worker_not_installed'\r
    return\r
  }\r
\r
  # An older installed worker lacks exact lease fencing and completion ACK rules.\r
  # Read source metadata only: never execute, replace, or fetch worker credentials.\r
  try {\r
    $workerHeader = @(Get-Content -LiteralPath $MirrorWorker -TotalCount 90 -ErrorAction Stop)\r
    if ($workerHeader -cnotcontains ('MEDIA_MIRROR_WORKER_PROTOCOL = "' + $MirrorWorkerProtocol + '"')) {\r
      Log "Media mirror startup rejected: local worker protocol drift."\r
      Write-MediaMirrorHealthReceipt 'worker_protocol_mismatch'\r
      return\r
    }\r
  } catch {\r
    Log "Media mirror startup rejected: worker protocol could not be inspected."\r
    Write-MediaMirrorHealthReceipt 'worker_protocol_unavailable'\r
    return\r
  }\r
  if (([string]$env:MEDIA_MIRROR_ENABLED).Trim().ToLowerInvariant() -ne "true") {\r
    Write-MediaMirrorHealthReceipt 'mirror_disabled'\r
    return\r
  }\r
  $configuredMirrorOrigin = ([string]$env:SUPABASE_URL).TrimEnd("/")\r
  if ([string]::IsNullOrWhiteSpace($configuredMirrorOrigin)) {\r
    # SUPABASE_URL is optional: the worker itself defaults to the fixed owner K\r
    # root. Never infer or accept an explicitly configured alternate host.\r
    $configuredMirrorOrigin = $CanonicalMirrorOrigin\r
  }\r
  if ($configuredMirrorOrigin -cne $CanonicalMirrorOrigin) {\r
    Log "Media mirror startup rejected: non-canonical Supabase origin."\r
    Write-MediaMirrorHealthReceipt 'noncanonical_origin'\r
    return\r
  }\r
  # Check presence only. Never log/retrieve/provision or pass a private key as\r
  # a command-line argument. The child inherits its already-authorized environment.\r
  if ([string]::IsNullOrWhiteSpace([string]$env:SUPABASE_SERVICE_ROLE_KEY) -or\r
      [string]::IsNullOrWhiteSpace([string]$env:MEDIA_MIRROR_WORKER_ID)) {\r
    Log "Media mirror startup unavailable: required runtime configuration absent."\r
    Write-MediaMirrorHealthReceipt 'missing_runtime_configuration'\r
    return\r
  }\r
  # Match this keepalive's exact installed worker, not another installation's\r
  # same-named Python process with different credentials or destination.\r
  $expectedWorkerPattern = '(?i)(^|[\\s"])' + [regex]::Escape([string]$MirrorWorker) + '(?=$|[\\s"])'\r
  try {\r
    $running = Get-CimInstance Win32_Process -ErrorAction Stop | Where-Object {\r
      ([string]$_.Name -match '^pythonw?(?:[0-9]+(?:\\.[0-9]+)?)?\\.exe(?=$)') -and\r
      ([string]$_.CommandLine -match $expectedWorkerPattern)\r
    } | Select-Object -First 1\r
    if ($running) {\r
      Write-MediaMirrorHealthReceipt 'running_unverified' ([int]$running.ProcessId)\r
      return\r
    }\r
  } catch {\r
    Log "Media mirror process visibility unavailable; no duplicate launch attempted."\r
    Write-MediaMirrorHealthReceipt 'process_visibility_unavailable'\r
    return\r
  }\r
  $python = Get-Command pythonw -ErrorAction SilentlyContinue\r
  if (-not $python) { $python = Get-Command python -ErrorAction SilentlyContinue }\r
  if (-not $python) {\r
    Log "Media mirror runtime unavailable: Python not found."\r
    Write-MediaMirrorHealthReceipt 'python_unavailable'\r
    return\r
  }\r
  try {\r
    New-Item -ItemType Directory -Force -Path $StateDir | Out-Null\r
    $proc = Start-Process -FilePath $python.Source -ArgumentList @("-u", ('"{0}"' -f $MirrorWorker), "--loop", "300") -WorkingDirectory $PSScriptRoot -WindowStyle Hidden -RedirectStandardOutput $MirrorWorkerStdout -RedirectStandardError $MirrorWorkerStderr -PassThru\r
    Start-Sleep -Seconds 2\r
    if (-not $proc -or -not (Get-Process -Id $proc.Id -ErrorAction SilentlyContinue)) {\r
      Log "Media mirror worker exited during startup; inspect local redacted worker logs."\r
      Write-MediaMirrorHealthReceipt 'startup_exited'\r
      return\r
    }\r
    Log "Media mirror worker process started pid=$($proc.Id); transfer and durable receipts not yet verified."\r
    Write-MediaMirrorHealthReceipt 'started_unverified' ([int]$proc.Id)\r
  } catch {\r
    Log "Media mirror worker start failed; error_class=$($_.Exception.GetType().Name)"\r
    Write-MediaMirrorHealthReceipt 'startup_error'\r
  }\r
}\r
\r
function Ensure-RemoteDesktopCommanderTask {\r
  if ($env:USERNAME -eq "SYSTEM") { return $false }\r
  if (-not (Test-Path $RemoteRelayScript)) {\r
    Log "Remote Desktop Commander scheduled runner unavailable; relay script missing."\r
    return $false\r
  }\r
\r
  try {\r
    $relayArgs = "-NoProfile -NonInteractive -WindowStyle Hidden -ExecutionPolicy Bypass -File \`"$RemoteRelayScript\`""\r
    $task = Get-ScheduledTask -TaskName $RemoteRelayTaskName -ErrorAction SilentlyContinue\r
    $drift = New-Object System.Collections.Generic.List[string]\r
    $unmanagedRelayMigrated = $false\r
\r
    if (-not $task) {\r
      $drift.Add('task_missing') | Out-Null\r
    } else {\r
      $existingAction = $task.Actions | Select-Object -First 1\r
      if (-not $existingAction) {\r
        $drift.Add('action_missing') | Out-Null\r
      } else {\r
        $execute = [string]$existingAction.Execute\r
        $arguments = [string]$existingAction.Arguments\r
        $workingDirectory = [string]$existingAction.WorkingDirectory\r
        if ($execute -notmatch '(?i)(^|\\\\)powershell\\.exe$') { $drift.Add('action_execute_mismatch') | Out-Null }\r
        if ($arguments -ne $relayArgs) { $drift.Add('action_arguments_mismatch') | Out-Null }\r
        if ($workingDirectory -and ($workingDirectory.TrimEnd('\\\\') -ne $PSScriptRoot.TrimEnd('\\\\'))) { $drift.Add('working_directory_mismatch') | Out-Null }\r
      }\r
\r
      $settings = $task.Settings\r
      if (-not $settings) {\r
        $drift.Add('settings_missing') | Out-Null\r
      } else {\r
        if ([int]$settings.RestartCount -lt 999) { $drift.Add('restart_count_mismatch') | Out-Null }\r
        $restartInterval = [string]$settings.RestartInterval\r
        if ($restartInterval -notin @('PT1M','00:01:00')) { $drift.Add('restart_interval_mismatch') | Out-Null }\r
        $executionLimit = [string]$settings.ExecutionTimeLimit\r
        if ($executionLimit -notin @('PT0S','00:00:00')) { $drift.Add('execution_time_limit_mismatch') | Out-Null }\r
        if (-not [bool]$settings.StartWhenAvailable) { $drift.Add('start_when_available_disabled') | Out-Null }\r
      }\r
\r
      $hasLogonTrigger = @($task.Triggers | Where-Object {\r
        $_.CimClass -and ([string]$_.CimClass.CimClassName -eq 'MSFT_TaskLogonTrigger')\r
      }).Count -gt 0\r
      if (-not $hasLogonTrigger) { $drift.Add('logon_trigger_missing') | Out-Null }\r
\r
      $logonType = [string]$task.Principal.LogonType\r
      if ($logonType -notin @('Interactive','InteractiveToken')) { $drift.Add('principal_not_interactive') | Out-Null }\r
    }\r
\r
    # An updated runner file is not active while the old Scheduled Task\r
    # process keeps running. Reconcile the description revision to activate\r
    # the installed recovery fix without a second scheduler or relay.\r
    if ($task -and -not ([string]$task.Description).Contains($RemoteRelayTaskSpecVersion)) {\r
      $drift.Add('runner_version_mismatch') | Out-Null\r
    }\r
\r
    if ($drift.Count -gt 0) {\r
      if ($task -and $task.State -eq 'Running') {\r
        Stop-ScheduledTask -TaskName $RemoteRelayTaskName -ErrorAction SilentlyContinue | Out-Null\r
        Start-Sleep -Seconds 1\r
      }\r
\r
      $desiredAction = New-ScheduledTaskAction -Execute "powershell.exe" -Argument $relayArgs -WorkingDirectory $PSScriptRoot\r
      $desiredTrigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME\r
      $desiredSettings = New-ScheduledTaskSettingsSet \`\r
        -AllowStartIfOnBatteries \`\r
        -DontStopIfGoingOnBatteries \`\r
        -RestartInterval (New-TimeSpan -Minutes 1) \`\r
        -RestartCount 999 \`\r
        -StartWhenAvailable \`\r
        -ExecutionTimeLimit ([TimeSpan]::Zero) \`\r
        -Hidden\r
      $desiredPrincipal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited\r
      $description = "J Fortitude Remote Desktop Commander relay spec $RemoteRelayTaskSpecVersion"\r
      Register-ScheduledTask -TaskName $RemoteRelayTaskName -Action $desiredAction -Trigger $desiredTrigger \`\r
        -Settings $desiredSettings -Principal $desiredPrincipal -Description $description -Force | Out-Null\r
      Log "Reconciled dedicated Remote Desktop Commander relay task. drift=$($drift -join ',') spec=$RemoteRelayTaskSpecVersion"\r
      $task = Get-ScheduledTask -TaskName $RemoteRelayTaskName -ErrorAction SilentlyContinue\r
    }\r
\r
    if (-not $task) { return $false }\r
\r
    $ownedRelay = Find-TaskOwnedRemoteDesktopCommanderProcess\r
    if ($task.State -eq 'Running' -and -not $ownedRelay) {\r
      Log "Remote Desktop Commander task is Running without a task-owned relay child; restarting task ownership."\r
      Stop-ScheduledTask -TaskName $RemoteRelayTaskName -ErrorAction SilentlyContinue | Out-Null\r
      Start-Sleep -Seconds 1\r
      $task = Get-ScheduledTask -TaskName $RemoteRelayTaskName -ErrorAction SilentlyContinue\r
    }\r
\r
    if ($task.State -ne "Running") {\r
      $relayProcesses = @(Get-RemoteDesktopCommanderProcesses)\r
      # Jwoffice can also have a previously installed primary Remote Desktop\r
      # Commander Scheduled Task. Never kill its relay as "unmanaged" just\r
      # because this secondary Unk task is idle: two restart loops can\r
      # otherwise terminate each other's working child process.\r
      $primaryTask = Get-ScheduledTask -TaskName 'JFortitude-RemoteDesktopCommander' -ErrorAction SilentlyContinue\r
      if ($primaryTask -and $primaryTask.State -eq "Running" -and $relayProcesses.Count -gt 0) {\r
        Log "Primary Remote Desktop Commander task is running with a relay; preserving existing process. Execution remains unverified."\r
        Write-RemoteRelayReceipt @{ ok = $false; state = 'primary_relay_owner_execution_unverified'; primary_task_name = 'JFortitude-RemoteDesktopCommander'; primary_task_running = $true; relay_present = $true; dedicated_task = $false; execution_probe_required = $true }\r
        return $true  # handled by the existing primary task; do not launch fallback\r
      }\r
      if ($relayProcesses.Count -gt 0) {\r
        # Unknown process ownership is not evidence that a relay is disposable.\r
        # Preserve the already-running transport rather than starting a competing\r
        # relay. Execution readiness still requires a real remote tool-call probe.\r
        $relayPids = @($relayProcesses | ForEach-Object { [int]$_.ProcessId })\r
        Log "Preserving relay with unverified task owner. pids=$($relayPids -join ',')."\r
        Write-RemoteRelayReceipt @{ ok = $false; state = 'unowned_relay_execution_unverified'; relay_present = $true; dedicated_task = $false; execution_probe_required = $true }\r
        return $true\r
      }\r
      Start-ScheduledTask -TaskName $RemoteRelayTaskName | Out-Null\r
      Start-Sleep -Seconds 3\r
      $task = Get-ScheduledTask -TaskName $RemoteRelayTaskName -ErrorAction SilentlyContinue\r
    }\r
\r
    $ownedRelay = Find-TaskOwnedRemoteDesktopCommanderProcess\r
    if ($task -and $task.State -eq "Running" -and $ownedRelay) {\r
      $runnerReceiptState = 'missing'\r
      $runnerReceiptAgeSeconds = ReceiptAgeSeconds $RemoteRelayRunnerReceipt\r
      try {\r
        if (Test-Path $RemoteRelayRunnerReceipt) {\r
          $runnerReceipt = Get-Content $RemoteRelayRunnerReceipt -Raw -ErrorAction Stop | ConvertFrom-Json\r
          $runnerReceiptState = [string]$runnerReceipt.state\r
        }\r
      } catch {\r
        $runnerReceiptState = 'unreadable'\r
      }\r
\r
      # Process supervision is proven, but neither Task Scheduler nor a remote\r
      # presence ping proves that the local MCP execution plane can forward a\r
      # command. Keep the task alive while reporting readiness fail-closed.\r
      Write-RemoteRelayReceipt @{\r
        ok = $false\r
        state = 'task_owned_relay_execution_unverified'\r
        process_supervised = $true\r
        task_owner_pid = [int]$ownedRelay.Runner.ProcessId\r
        relay_pid = [int]$ownedRelay.Relay.ProcessId\r
        dedicated_task = $true\r
        persisted_session = $true\r
        runner_receipt_state = $runnerReceiptState\r
        runner_receipt_age_seconds = $runnerReceiptAgeSeconds\r
        execution_probe_required = $true\r
        task_reconciled = ($drift.Count -gt 0)\r
        drift_reasons = @($drift)\r
        unmanaged_relay_migrated = $unmanagedRelayMigrated\r
      }\r
      return $true\r
    }\r
\r
    $relayProcess = Find-RemoteDesktopCommanderProcess\r
    Log "Remote Desktop Commander dedicated task/relay is not task-owned. task_state=$($task.State) relay_present=$([bool]$relayProcess)"\r
    Write-RemoteRelayReceipt @{ ok = $false; state = 'task_or_relay_not_task_owned'; dedicated_task = $true; task_state = [string]$task.State; relay_present = [bool]$relayProcess; execution_probe_required = $true; task_reconciled = ($drift.Count -gt 0); drift_reasons = @($drift); unmanaged_relay_migrated = $unmanagedRelayMigrated }\r
    return $false\r
  } catch {\r
    Log "Remote Desktop Commander dedicated task repair failed: $($_.Exception.Message)"\r
    Write-RemoteRelayReceipt @{ ok = $false; state = 'task_registration_or_start_failed'; dedicated_task = $true; reason = $_.Exception.Message }\r
    return $false\r
  }\r
}\r
\r
function Ensure-RemoteDesktopCommander {\r
  # Remote Desktop Commander stores the paired-device session under the user\r
  # profile and its remote agent is intentionally foreground by default. Run\r
  # this only in the interactive user's context; the boot/SYSTEM keepalive must\r
  # not create a second device identity or use another user's credential store.\r
  if ($env:USERNAME -eq "SYSTEM") {\r
    Write-RemoteRelayReceipt @{ ok = $false; state = 'deferred_to_user_session'; reason = 'system_context_not_allowed' }\r
    return\r
  }\r
\r
  try {\r
    # The dedicated Scheduled Task is the canonical owner. Reconcile/start it\r
    # even if a legacy relay process is already present; unmanaged processes are\r
    # migrated into task ownership so restart policy cannot remain bypassed.\r
    if (Ensure-RemoteDesktopCommanderTask) { return }\r
\r
    # Scheduled-task reconciliation can fail while an independently owned\r
    # relay still exists. Do not spawn a competing device session in the\r
    # fallback: this recovery owns no such process and cannot safely kill it.\r
    # A live authenticated tool call is still required to prove delivery.\r
    $existingRelays = @(Get-RemoteDesktopCommanderProcesses)\r
    if ($existingRelays.Count -gt 0) {\r
      Log "Preserving existing relay after scheduled-task repair failure; fallback suppressed. Remote tool execution remains unverified."\r
      Write-RemoteRelayReceipt @{ ok = $false; state = 'fallback_suppressed_existing_relay_execution_unverified'; relay_present = $true; dedicated_task = $false; execution_probe_required = $true }\r
      return\r
    }\r
\r
    $npx = Get-Command npx.cmd -ErrorAction SilentlyContinue\r
    if (-not $npx) { $npx = Get-Command npx -ErrorAction SilentlyContinue }\r
    if (-not $npx) {\r
      Log "Remote Desktop Commander ensure failed; npx not found."\r
      Write-RemoteRelayReceipt @{ ok = $false; state = 'not_running'; reason = 'npx_not_found' }\r
      return\r
    }\r
\r
    # Fallback direct launch remains available only if dedicated task ownership\r
    # cannot be established. The next healthy keepalive will attempt migration\r
    # back into the task rather than accepting fallback as a permanent state.\r
    $comspec = if ($env:ComSpec) { $env:ComSpec } else { 'C:\\Windows\\System32\\cmd.exe' }\r
    if (-not (Test-Path $comspec)) {\r
      Log "Remote Desktop Commander ensure failed; cmd.exe not found."\r
      Write-RemoteRelayReceipt @{ ok = $false; state = 'not_running'; reason = 'cmd_not_found' }\r
      return\r
    }\r
\r
    $stdout = Join-Path $StateDir 'remote_desktop_commander.stdout.log'\r
    $stderr = Join-Path $StateDir 'remote_desktop_commander.stderr.log'\r
    $command = "npx --yes $RemoteDesktopCommanderPackage remote --persist-session"\r
    $proc = Start-Process -FilePath $comspec -ArgumentList @('/d','/s','/c',$command) -WindowStyle Hidden -PassThru -RedirectStandardOutput $stdout -RedirectStandardError $stderr\r
    Start-Sleep -Seconds 3\r
\r
    $stillRunning = Get-Process -Id $proc.Id -ErrorAction SilentlyContinue\r
    if ($stillRunning) {\r
      Log "Remote Desktop Commander relay fallback start requested. pid=$($proc.Id) package=$RemoteDesktopCommanderPackage"\r
      Write-RemoteRelayReceipt @{ ok = $false; state = 'fallback_start_execution_unverified'; pid = [int]$proc.Id; started = $true; persisted_session = $true; windows_cmd_wrapper = $true; dedicated_task = $false; execution_probe_required = $true }\r
    } else {\r
      $tail = ''\r
      try { $tail = ((Get-Content $stderr -Tail 20 -ErrorAction SilentlyContinue) -join "\`n") } catch {}\r
      Log "Remote Desktop Commander relay exited during fallback startup."\r
      Write-RemoteRelayReceipt @{ ok = $false; state = 'startup_exited'; started = $true; windows_cmd_wrapper = $true; dedicated_task = $false; error_tail = $tail }\r
    }\r
  } catch {\r
    Log "Remote Desktop Commander ensure failed: $($_.Exception.Message)"\r
    Write-RemoteRelayReceipt @{ ok = $false; state = 'watchdog_error'; reason = $_.Exception.Message }\r
  }\r
}\r
\r
function Assert-PowerPosture {\r
  if (-not (Test-Path $PersistenceRepair)) {\r
    Log "Power posture repair skipped; repair_persistence.ps1 missing."\r
    return\r
  }\r
  $age = ReceiptAgeSeconds $PowerReceiptFile\r
  if ($null -ne $age -and $age -lt $PowerRepairCadenceSeconds) { return }\r
  try {\r
    $actionId = if ($env:USERNAME -eq "SYSTEM") { "boot_keepalive" } else { "keepalive_tick" }\r
    $out = & powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -File $PersistenceRepair -Apply -ActionId $actionId 2>&1 | Out-String\r
    $tail = $out.Substring([Math]::Max(0, $out.Length - 800))\r
    Log "Power posture assertion completed. action=$actionId receipt_age_secs=$age output_tail=$tail"\r
  } catch {\r
    Log "Power posture assertion failed: $($_.Exception.Message)"\r
  }\r
}\r
\r
\r
# The installed companion is a long-lived copy, not a read-through to GitHub.\r
# A stale installation can keep heartbeating the forbidden legacy source even\r
# after the canonical package has been corrected. Repair exactly that known\r
# config drift, then let the existing supervisor restart ONE Unk process.\r
# Never touch Kim's private planner, queue, or inference workers.\r
# The installed supervisor may also retain a Lovable-managed reporting origin.\r
# Use the same canonical target as the companion and never allow an inherited\r
# UNK_SUPABASE_URL to redirect privileged supervisor reports to legacy.\r
function Repair-StaleUnkSupervisorRoute {\r
  $scriptFile = Join-Path $PSScriptRoot "unk_supervisor.py"\r
  if (-not (Test-Path -LiteralPath $scriptFile)) { return }\r
  try {\r
    $installed = [System.IO.File]::ReadAllText($scriptFile)\r
    $canonicalRef = 'SUPABASE_URL = "https://kwbegsybeyyxfmavjswv.supabase.co"'\r
    if ($installed.Contains($canonicalRef) -and\r
        -not $installed.Contains('SUPABASE_URL = os.environ.get("UNK_SUPABASE_URL")')) { return }\r
    $blockRegex = [regex]::new('(?ms)^SUPABASE_URL = [^\\r\\n]+.{0,1400}?(?=\\r?\\nSTART_REQUEST_FILE = )')\r
    $matches = $blockRegex.Matches($installed)\r
    if ($matches.Count -ne 1 -or\r
        -not $matches[0].Value.Contains('SUPABASE_ANON_KEY =') -or\r
        -not $matches[0].Value.Contains('REPORT_URL =') -or\r
        -not ($matches[0].Value.Contains('https://pefatniumnrxwbgnwvvh.supabase.co') -or\r
              $matches[0].Value.Contains('os.environ.get("UNK_SUPABASE_URL")'))) {\r
      Log "Unk supervisor K-route recovery deferred: unexpected installed config."\r
      return\r
    }\r
    $canonicalBlock = @'\r
SUPABASE_URL = "https://kwbegsybeyyxfmavjswv.supabase.co"\r
SUPABASE_ANON_KEY = os.environ.get("UNK_SUPABASE_ANON_KEY") or "sb_publishable_71YhGNn088MamieIZXBAaw_kv3w4wc9"\r
REPORT_URL = f"{SUPABASE_URL}/functions/v1/desktop-supervisor-report"\r
'@\r
    $patched = $blockRegex.Replace($installed, $canonicalBlock, 1)\r
    if (-not $patched.Contains($canonicalRef) -or\r
        $patched.Contains('https://pefatniumnrxwbgnwvvh.supabase.co')) {\r
      Log "Unk supervisor K-route recovery refused: post-write target invalid."\r
      return\r
    }\r
    $temporary = "$scriptFile.project-k.tmp.py"\r
    $backup = "$scriptFile.before-project-k-$(Get-Date -Format 'yyyyMMddHHmmss').bak"\r
    [System.IO.File]::WriteAllText($temporary, $patched, (New-Object System.Text.UTF8Encoding($false)))\r
    python -m py_compile $temporary 2>&1 | Out-Null\r
    if ($LASTEXITCODE -ne 0) {\r
      Remove-Item -LiteralPath $temporary -Force -ErrorAction SilentlyContinue\r
      Log "Unk supervisor K-route recovery deferred: Python syntax failed."\r
      return\r
    }\r
    [System.IO.File]::Replace($temporary, $scriptFile, $backup)\r
    Log "Unk supervisor reporting route repaired atomically to owner Project K."\r
    # Only the existing supervisor process may be stopped; its registered\r
    # UnkSupervisor task and keepalive retain independent restart ownership.\r
    $live = @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object {\r
      $_.Name -match '^python' -and $_.CommandLine -match 'unk_supervisor[.]py'\r
    })\r
    if ($live.Count -eq 1) {\r
      Stop-Process -Id $live[0].ProcessId -ErrorAction Stop\r
      Log "Unk supervisor stale process stopped for existing scheduled-task restart."\r
    } elseif ($live.Count -gt 1) {\r
      Log "Unk supervisor K-route installed; duplicate processes require existing-task reconciliation."\r
    }\r
  } catch {\r
    Log "Unk supervisor K-route recovery failed; error_class=$($_.Exception.GetType().Name)"\r
  }\r
}\r
\r
function Repair-StaleUnkCompanionRoute {\r
  $scriptFile = Join-Path $PSScriptRoot "unk_companion.py"\r
  if (-not (Test-Path -LiteralPath $scriptFile)) {\r
    Log "Unk K-route recovery deferred: installed companion missing."\r
    return\r
  }\r
  try {\r
    $installed = [System.IO.File]::ReadAllText($scriptFile)\r
    $newRef = 'SUPABASE_PROJECT_REF = "kwbegsybeyyxfmavjswv"'\r
    $oldRef = 'SUPABASE_PROJECT_REF = "pefatniumnrxwbgnwvvh"'\r
    if ($installed.Contains($newRef) -and -not $installed.Contains($oldRef)) { return }\r
    if (-not $installed.Contains($oldRef)) {\r
      Log "Unk K-route recovery deferred: unrecognized installed target."\r
      return\r
    }\r
    # This bounded match covers only the original public routing block; do not\r
    # replace unrelated credentials, runtime capabilities, or user-owned state.\r
    $blockRegex = [regex]::new('(?ms)^SUPABASE_PROJECT_REF = "pefatniumnrxwbgnwvvh".{0,1200}?(?=\\r?\\nPOLL_SECONDS = )')\r
    $found = $blockRegex.Matches($installed)\r
    if ($found.Count -ne 1 -or\r
        -not $found[0].Value.Contains('FUNCTIONS_BASE =') -or\r
        -not $found[0].Value.Contains('COMPANION_URL =')) {\r
      Log "Unk K-route recovery deferred: ambiguous legacy routing block."\r
      return\r
    }\r
    $canonicalBlock = @'\r
SUPABASE_PROJECT_REF = "kwbegsybeyyxfmavjswv"\r
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY", "").strip() or "sb_publishable_71YhGNn088MamieIZXBAaw_kv3w4wc9"\r
FUNCTIONS_BASE = f"https://{SUPABASE_PROJECT_REF}.functions.supabase.co"\r
COMPANION_URL = f"{FUNCTIONS_BASE}/desktop-companion"\r
'@\r
    $patched = $blockRegex.Replace($installed, $canonicalBlock, 1)\r
    if ($patched.Contains($oldRef) -or -not $patched.Contains($newRef)) {\r
      Log "Unk K-route recovery refused: target verification failed."\r
      return\r
    }\r
    $temporary = "$scriptFile.project-k.tmp.py"\r
    $backup = "$scriptFile.before-project-k-$(Get-Date -Format 'yyyyMMddHHmmss').bak"\r
    [System.IO.File]::WriteAllText($temporary, $patched, (New-Object System.Text.UTF8Encoding($false)))\r
    python -m py_compile $temporary 2>&1 | Out-Null\r
    if ($LASTEXITCODE -ne 0) {\r
      Remove-Item -LiteralPath $temporary -Force -ErrorAction SilentlyContinue\r
      Log "Unk K-route recovery deferred: candidate Python syntax check failed."\r
      return\r
    }\r
    [System.IO.File]::Replace($temporary, $scriptFile, $backup)\r
    Log "Unk companion installed routing repaired atomically to owner Project K."\r
    # A running Python interpreter retains its OLD loaded routing constants.\r
    # Stop precisely one old Unk child; existing supervisor owns restart and\r
    # heartbeat verification. No second scheduler or companion is created.\r
    $live = @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object {\r
      $_.Name -match '^python' -and $_.CommandLine -match 'unk_companion[.]py'\r
    })\r
    if ($live.Count -eq 1) {\r
      Stop-Process -Id $live[0].ProcessId -ErrorAction Stop\r
      Log "Unk companion legacy process stopped for supervised K-route restart."\r
    } elseif ($live.Count -gt 1) {\r
      Log "Unk K-route repair installed; multiple child processes require existing supervisor reconciliation."\r
    }\r
  } catch {\r
    Log "Unk K-route recovery failed; error_class=$($_.Exception.GetType().Name)"\r
  }\r
}\r
\r
try {\r
  Repair-StaleUnkCompanionRoute\r
  Repair-StaleUnkSupervisorRoute\r
  Assert-PowerPosture\r
  Ensure-AIBridge\r
  Ensure-FixerWorker\r
  Ensure-MediaMirrorWorker\r
  Ensure-RemoteDesktopCommander\r
\r
  $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue\r
\r
  $needsReinstall = $false\r
  if ($task) {\r
    try {\r
      $actionArg = ($task.Actions | Select-Object -First 1).Arguments\r
      if ($actionArg -match '"?([A-Za-z]:\\\\[^"]+unk_supervisor\\.py)"?') {\r
        $scriptPath = $Matches[1]\r
        if (-not (Test-Path $scriptPath)) {\r
          Log "Registered supervisor script missing: $scriptPath; will reinstall from durable copy."\r
          $needsReinstall = $true\r
        }\r
      }\r
    } catch {}\r
  }\r
\r
  if (-not $task -or $needsReinstall) {\r
    if ($env:USERNAME -eq "SYSTEM") {\r
      Log "Supervisor task missing/stale, but running as SYSTEM; waiting for user-session keepalive to repair."\r
      exit 0\r
    }\r
    Log "Supervisor task missing or stale; repairing task registration."\r
    $durableInstaller = Join-Path (Join-Path $env:LOCALAPPDATA "UnkCompanion") "install_supervisor.ps1"\r
    $localInstaller = Join-Path $PSScriptRoot "install_supervisor.ps1"\r
    $installer = if (Test-Path $durableInstaller) { $durableInstaller } elseif (Test-Path $localInstaller) { $localInstaller } else { $null }\r
    if ($installer) {\r
      & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $installer -RepairOnly -SkipVerify | Out-Null\r
    }\r
    $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue\r
  }\r
\r
  if (-not $task) {\r
    Log "Supervisor task still missing after repair attempt."\r
    exit 1\r
  }\r
\r
  $age = MarkerAgeSeconds\r
  $stale = ($null -eq $age) -or ($age -gt 240)\r
  if ($task.State -ne "Running" -or $stale) {\r
    Log "Starting supervisor task. state=$($task.State) marker_age_secs=$age"\r
    if ($task.State -eq "Running") {\r
      Stop-ScheduledTask -TaskName $TaskName | Out-Null\r
      Start-Sleep -Seconds 2\r
    }\r
    try {\r
      Start-ScheduledTask -TaskName $TaskName | Out-Null\r
      Log "Supervisor start requested by keepalive."\r
    } catch {\r
      Log "Supervisor start failed from keepalive: $($_.Exception.Message)"\r
    }\r
  } else {\r
    Log "Supervisor healthy. state=$($task.State) marker_age_secs=$age"\r
  }\r
} catch {\r
  Log "Keepalive failure: $($_.Exception.Message)"\r
  exit 1\r
}\r
`,Vn={launched:{label:"Companion launched",tone:"bg-blue-500/15 text-blue-700 dark:text-blue-300",icon:e.jsx(ge,{className:"h-3.5 w-3.5"})},restarted:{label:"Auto-restarted",tone:"bg-amber-500/15 text-amber-700 dark:text-amber-300",icon:e.jsx(oe,{className:"h-3.5 w-3.5"})},heartbeat_stale_restart:{label:"Heartbeat stale → restart",tone:"bg-amber-500/15 text-amber-700 dark:text-amber-300",icon:e.jsx(je,{className:"h-3.5 w-3.5"})},update_staged:{label:"Update staged",tone:"bg-slate-500/15 text-slate-700 dark:text-slate-300",icon:e.jsx(zt,{className:"h-3.5 w-3.5"})},update_verified:{label:"Update verified",tone:"bg-emerald-500/15 text-emerald-700 dark:text-emerald-300",icon:e.jsx(ee,{className:"h-3.5 w-3.5"})},update_rolled_back:{label:"Update rolled back",tone:"bg-red-500/15 text-red-700 dark:text-red-300",icon:e.jsx(Ne,{className:"h-3.5 w-3.5"})},escalation:{label:"Escalation",tone:"bg-red-500/15 text-red-700 dark:text-red-300",icon:e.jsx(ie,{className:"h-3.5 w-3.5"})},supervisor_online:{label:"Supervisor online",tone:"bg-emerald-500/15 text-emerald-700 dark:text-emerald-300",icon:e.jsx(ee,{className:"h-3.5 w-3.5"})},supervisor_stopped:{label:"Supervisor stopped",tone:"bg-slate-500/15 text-slate-700 dark:text-slate-300",icon:e.jsx(Ct,{className:"h-3.5 w-3.5"})},process_start_requested:{label:"Process start requested",tone:"bg-blue-500/15 text-blue-700 dark:text-blue-300",icon:e.jsx(ge,{className:"h-3.5 w-3.5"})},process_start_receipt:{label:"Process start receipt",tone:"bg-emerald-500/15 text-emerald-700 dark:text-emerald-300",icon:e.jsx(ee,{className:"h-3.5 w-3.5"})},process_start_failed:{label:"Process start failed",tone:"bg-red-500/15 text-red-700 dark:text-red-300",icon:e.jsx(Ne,{className:"h-3.5 w-3.5"})},install_verified:{label:"Install verified",tone:"bg-emerald-500/15 text-emerald-700 dark:text-emerald-300",icon:e.jsx(ee,{className:"h-3.5 w-3.5"})},task_self_healed:{label:"Task self-healed",tone:"bg-amber-500/15 text-amber-700 dark:text-amber-300",icon:e.jsx($e,{className:"h-3.5 w-3.5"})},keepalive_started_supervisor:{label:"Keepalive started supervisor",tone:"bg-blue-500/15 text-blue-700 dark:text-blue-300",icon:e.jsx($e,{className:"h-3.5 w-3.5"})}};function Jn({deviceId:r}){const[t,s]=w.useState([]),[o,i]=w.useState(!0);return w.useEffect(()=>{let n=!1;async function c(){const{data:l}=await C.from("desktop_supervisor_events").select("id, event_kind, message, evidence, created_at").eq("device_id",r).order("created_at",{ascending:!1}).limit(20);n||(s(l??[]),i(!1))}c();const d=setInterval(c,3e4);return()=>{n=!0,clearInterval(d)}},[r]),e.jsxs(W,{children:[e.jsx(vr,{className:"pb-2",children:e.jsx(yr,{className:"text-sm",children:"Supervisor timeline"})}),e.jsx(br,{className:"text-sm",children:o?e.jsx("p",{className:"text-muted-foreground",children:"Loading…"}):t.length===0?e.jsxs("p",{className:"text-muted-foreground",children:["No supervisor events yet. Once ",e.jsx("code",{children:"setup_unk.ps1"})," installs the supervisor and keepalive task, launched/restart/update events will appear here."]}):e.jsx("ol",{className:"space-y-2",children:t.map(n=>{const c=Vn[n.event_kind]??{label:n.event_kind,tone:"bg-slate-500/15",icon:e.jsx(je,{className:"h-3.5 w-3.5"})};return e.jsxs("li",{className:"flex items-start gap-2",children:[e.jsxs(P,{className:c.tone+" gap-1",children:[c.icon,c.label]}),e.jsxs("div",{className:"flex-1 min-w-0",children:[n.message&&e.jsx("div",{className:"text-xs",children:n.message}),e.jsx("div",{className:"text-[10px] text-muted-foreground",children:new Date(n.created_at).toLocaleString()})]})]},n.id)})})})]})}const Yn=24*60*60*1e3;async function Zn(){const r=Date.now(),t=new Date(r-Yn).toISOString(),[s,o,i,n,c,d,l]=await Promise.all([Ze(),C.from("desktop_devices").select("id, device_name, status, last_heartbeat_at, kind").neq("kind","mobile_approver").neq("status","revoked"),C.from("desktop_action_requests").select("id",{count:"exact",head:!0}).eq("status","failed").eq("failure_reason","facebook_login_required_in_browser_profile").gte("created_at",t),C.from("desktop_action_requests").select("id",{count:"exact",head:!0}).eq("capability","browser_release_locks").in("status",["pending","approved","auto_approved"]).is("executed_at",null),C.from("recovery_escalations").select("id",{count:"exact",head:!0}).eq("status","open"),C.rpc("recovery_queue_health"),C.from("desktop_action_requests").select("id",{count:"exact",head:!0}).in("capability",["publish_facebook","publish_instagram","meta_publish"]).eq("status","failed").gte("created_at",t)]),m=o.data??[],f=s.desktop.ok?s.desktop.total_active===0?{key:"heartbeat",label:"Desktop heartbeat",state:"red",detail:"No desktop enrolled",owner:"Founder"}:s.desktop.fresh>0?{key:"heartbeat",label:"Desktop heartbeat",state:"green",detail:`${s.desktop.fresh}/${s.desktop.total_active} online · last ${Math.round(s.desktop.heartbeat_age_seconds??0)}s ago`}:{key:"heartbeat",label:"Desktop heartbeat",state:"red",detail:`No fresh heartbeat in ${Math.round(Or/1e3)}s`,owner:"Founder — start companion"}:{key:"heartbeat",label:"Desktop heartbeat",state:"unknown",detail:"Status unavailable — query failed"},g=s.supervisor.state==="unknown"?{key:"supervisor",label:"Supervisor",state:"unknown",detail:"Status unavailable — query failed"}:s.supervisor.state==="running"?{key:"supervisor",label:"Supervisor",state:"green",detail:s.supervisor.reason}:s.supervisor.state==="recovering"?{key:"supervisor",label:"Supervisor",state:"yellow",detail:s.supervisor.reason,owner:"Unk — auto-retry"}:s.supervisor.state==="human_action"?{key:"supervisor",label:"Supervisor",state:"red",detail:s.supervisor.reason,owner:"Founder — re-run installer"}:{key:"supervisor",label:"Supervisor",state:"red",detail:s.supervisor.reason,owner:"Founder"},h=n.count??0,k=h>0?{key:"browser",label:"Browser unlocked",state:"yellow",detail:`${h} browser lock release pending`,owner:"Unk — auto-resolves next heartbeat"}:{key:"browser",label:"Browser unlocked",state:"green",detail:"No stuck browser sessions"},v=i.count??0,y=l.count??0,L=v>0?{key:"meta",label:"Meta credentials",state:"yellow",detail:`Facebook sign-in expired — ${v} publish(es) waiting`,owner:"Founder — re-sign-in (2 min)"}:y>10?{key:"meta",label:"Meta credentials",state:"yellow",detail:`${y} Meta publish failure(s) in 24h — check root cause`,owner:"Ops — investigate"}:{key:"meta",label:"Meta credentials",state:"green",detail:"Sign-in fresh, publishes clean"},S=c.count??0,u=d.data??{},x=u.unique_actionable??0,N=u.jason_needed??0,j=u.runtime_failures??0,R=u.bookkeeping_only??0,T=u.state??"healthy",B=S>0?{key:"recovery",label:"Recovery queue",state:"red",detail:`${S} escalation(s) open`,owner:"Founder — review",href:"/grant-engine/recovery-queue?filter=open"}:N>0?{key:"recovery",label:"Recovery queue",state:"yellow",detail:`${N} task(s) need your input`,owner:"Founder",href:"/grant-engine/recovery-queue?filter=jason"}:j>0?{key:"recovery",label:"Recovery queue",state:"yellow",detail:`${j} active runtime failure(s)`,owner:"Unk — auto-retry",href:"/grant-engine/recovery-queue?filter=open"}:x>R?{key:"recovery",label:"Recovery queue",state:"yellow",detail:`${x-R} engineering-owned condition(s) open`,owner:"Engineering — repair required",href:"/grant-engine/recovery-queue?filter=open"}:T==="degraded"?{key:"recovery",label:"Recovery queue",state:"yellow",detail:x>0?`${x} bookkeeping condition(s) need review`:"Recovery health degraded — source query needs review",owner:"Engineering — review required",href:"/grant-engine/recovery-queue?filter=open"}:{key:"recovery",label:"Recovery queue",state:"green",detail:R>0?`${x} unique condition(s) · ${R} bookkeeping only`:"0 open",href:"/grant-engine/recovery-queue?filter=open"},K=[f,g,k,L,B],J=new Set(["heartbeat","supervisor","recovery"]),U=K.some(I=>I.state==="red"&&J.has(I.key)),p=K.some(I=>I.state==="yellow")||K.some(I=>I.state==="red"),_=U?"red":p?"yellow":"green",$=m.filter(I=>I.status==="active").map(I=>{const M=[],Z=I.last_heartbeat_at&&r-new Date(I.last_heartbeat_at).getTime()<Or;Z||M.push("Heartbeat stale"),s.supervisor.state==="human_action"&&M.push("Supervisor needs human action"),v>0&&M.push("Facebook sign-in expired");let ne="trusted";return!Z||s.supervisor.state==="human_action"||v>0&&m.length===1||N>0?ne="attention":(s.supervisor.state==="recovering"||h>0||j>0)&&(ne="degraded"),ne==="trusted"&&M.length===0&&M.push("All checks passed"),{device_id:I.id,device_name:I.device_name,level:ne,reasons:M}});return{overall:_,checks:K,devices:$,generated_at:new Date().toISOString()}}const Qn={green:{badge:"border-emerald-500/40 text-emerald-700 bg-emerald-500/5",icon:se,label:"OK"},yellow:{badge:"border-amber-500/40 text-amber-700 bg-amber-500/5",icon:ie,label:"Watch"},red:{badge:"border-destructive/50 text-destructive bg-destructive/5",icon:Qe,label:"Blocked"},unknown:{badge:"border-muted-foreground/30 text-muted-foreground",icon:ie,label:"—"}},Xn={trusted:{dot:"🟢",label:"Trusted",badge:"border-emerald-500/40 text-emerald-700"},degraded:{dot:"🟡",label:"Degraded",badge:"border-amber-500/40 text-amber-700"},attention:{dot:"🔴",label:"Needs attention",badge:"border-destructive/50 text-destructive"}};function es(){const[r,t]=w.useState(null),[s,o]=w.useState(!1),i=async()=>{o(!0);try{t(await Zn())}catch(m){console.warn("[TrustUnkPanel]",m)}finally{o(!1)}};w.useEffect(()=>{i();const m=setInterval(i,6e4);return()=>clearInterval(m)},[]);const n=((r==null?void 0:r.checks)??[]).filter(m=>m.state==="yellow"),c=((r==null?void 0:r.checks)??[]).filter(m=>m.state==="red"),d=r?r.overall==="green"?"Trust Unk today":r.overall==="yellow"?c.length+n.length===1?`Trust Unk — 1 thing to check: ${[...c,...n][0].label.toLowerCase()}`:`Trust Unk — ${c.length+n.length} things to check`:c.length===1?`Hold off — fix ${c[0].label.toLowerCase()} first`:`Hold off — ${c.length} outages to resolve`:"Checking…",l=(r==null?void 0:r.overall)==="green"?"text-emerald-600":(r==null?void 0:r.overall)==="yellow"?"text-amber-700":(r==null?void 0:r.overall)==="red"?"text-destructive":"text-muted-foreground";return e.jsxs(W,{className:"p-4 md:p-5 space-y-4 border-2",children:[e.jsxs("div",{className:"flex items-start justify-between flex-wrap gap-3",children:[e.jsxs("div",{className:"min-w-0 flex-1",children:[e.jsxs("div",{className:"text-xs uppercase tracking-widest text-muted-foreground flex items-center gap-1",children:[e.jsx(ee,{className:"h-3.5 w-3.5"})," Executive trust check"]}),e.jsx("h2",{className:"text-xl md:text-2xl font-serif mt-1",children:"Can I trust Unk today?"}),e.jsx("p",{className:`text-2xl md:text-3xl font-semibold mt-1 leading-tight ${l}`,children:d})]}),e.jsxs(E,{size:"sm",variant:"ghost",onClick:i,disabled:s,children:[e.jsx(oe,{className:`h-3 w-3 mr-1 ${s?"animate-spin":""}`})," Refresh"]})]}),e.jsxs("div",{className:"grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-2",children:[((r==null?void 0:r.checks)??[]).map(m=>{const f=Qn[m.state],g=f.icon,h=e.jsxs(e.Fragment,{children:[e.jsxs("div",{className:"flex items-center gap-1.5 text-xs font-medium",children:[e.jsx(g,{className:"h-3.5 w-3.5"}),e.jsx("span",{children:m.label})]}),e.jsx("div",{className:"text-[11px] mt-1 opacity-90",children:m.detail}),m.state!=="green"&&m.owner&&e.jsxs("div",{className:"text-[10px] mt-1 opacity-75",children:["Owner: ",m.owner]}),m.href&&e.jsxs("span",{className:"mt-2 inline-flex items-center gap-1 text-[10px] font-medium underline underline-offset-2",children:["Open recovery queue ",e.jsx(At,{className:"h-3 w-3"})]})]});return m.href?e.jsx(Pt,{to:m.href,"aria-label":`${m.label}: ${m.detail}. Open recovery queue`,className:`block rounded-lg border p-3 text-left transition-colors hover:bg-foreground/5 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring ${f.badge}`,children:h},m.key):e.jsx("div",{className:`rounded-lg border p-3 ${f.badge}`,children:h},m.key)}),!r&&Array.from({length:5}).map((m,f)=>e.jsx("div",{className:"rounded-lg border p-3 h-20 animate-pulse bg-muted/30"},f))]}),r&&r.devices.length>0&&e.jsxs("div",{className:"pt-2 border-t space-y-2",children:[e.jsx("div",{className:"text-xs uppercase tracking-widest text-muted-foreground",children:"Supervisor confidence per desktop"}),e.jsx("div",{className:"grid gap-2 sm:grid-cols-2",children:r.devices.map(m=>{const f=Xn[m.level];return e.jsxs("div",{className:"flex items-start justify-between gap-2 rounded border p-2 text-xs",children:[e.jsxs("div",{className:"min-w-0",children:[e.jsxs("div",{className:"font-medium truncate",children:[f.dot," ",m.device_name]}),e.jsx("div",{className:"text-[11px] text-muted-foreground mt-0.5",children:m.reasons.join(" · ")})]}),e.jsx(P,{variant:"outline",className:f.badge,children:f.label})]},m.device_id)})})]}),r&&e.jsxs("div",{className:"text-[10px] text-muted-foreground",children:["Snapshot ",new Date(r.generated_at).toLocaleTimeString()," · auto-refresh 60s"]})]})}async function rs(){const r=await Ze();return{publish:{queued:r.publishing.queued,running:r.publishing.dispatched,completed:r.publishing.published_24h,failed:r.publishing.failed_24h},receipts:{successes:r.publishing.verified_receipts_24h,screenshots:r.publishing.screenshots_24h,post_urls:r.publishing.post_urls_24h},campaign:{published:r.publishing.verified_stv_receipts,target:Vt},window_hours:ze,heartbeat_ok:r.desktop.fresh>0,desktop_detail:r.desktop.total_active===0?"no desktop enrolled":`${r.desktop.fresh}/${r.desktop.total_active} fresh · last ${Math.round(r.desktop.heartbeat_age_seconds??0)}s ago`,generated_at:new Date().toISOString()}}function ts({label:r,c:t,icon:s}){return e.jsxs("div",{className:"rounded-lg border p-3",children:[e.jsxs("div",{className:"flex items-center gap-1.5 text-xs font-medium text-muted-foreground",children:[e.jsx(s,{className:"h-3.5 w-3.5"})," ",r]}),e.jsxs("div",{className:"mt-2 grid grid-cols-4 gap-1 text-center",children:[e.jsxs("div",{children:[e.jsx("div",{className:"text-lg font-bold",children:t.queued}),e.jsx("div",{className:"text-[10px] text-muted-foreground",children:"Queued"})]}),e.jsxs("div",{children:[e.jsx("div",{className:"text-lg font-bold text-amber-600",children:t.running}),e.jsx("div",{className:"text-[10px] text-muted-foreground",children:"Running"})]}),e.jsxs("div",{children:[e.jsx("div",{className:`text-lg font-bold ${t.completed>0?"text-emerald-600":"text-muted-foreground"}`,children:t.completed}),e.jsx("div",{className:"text-[10px] text-muted-foreground",children:"Done"})]}),e.jsxs("div",{children:[e.jsx("div",{className:`text-lg font-bold ${t.failed>0?"text-destructive":"text-muted-foreground"}`,children:t.failed}),e.jsx("div",{className:"text-[10px] text-muted-foreground",children:"Failed"})]})]})]})}function ns(){const[r,t]=w.useState(null),[s,o]=w.useState(!1),i=async()=>{o(!0);try{t(await rs())}catch(l){console.warn("[VerifiedWorkPanel]",l)}finally{o(!1)}};w.useEffect(()=>{i();const l=setInterval(i,6e4);return()=>clearInterval(l)},[]);const n=r!=null&&r.heartbeat_ok&&r.publish.completed===0&&r.receipts.successes===0&&r.receipts.post_urls===0,c=r?[{label:"Publish jobs created",ok:r.publish.queued+r.publish.running+r.publish.completed+r.publish.failed>0},{label:"Unk claimed jobs (dispatched)",ok:r.publish.running+r.publish.completed+r.publish.failed>0},{label:"Browser reached publisher",ok:r.publish.completed+r.publish.failed>0},{label:"Post button clicked (receipt)",ok:r.receipts.successes>0||r.publish.completed>0},{label:"Post URL returned",ok:r.receipts.post_urls>0},{label:"Screenshot captured",ok:r.receipts.screenshots>0}]:[],d=c.find(l=>!l.ok);return e.jsxs(W,{className:`p-4 md:p-5 space-y-4 border-2 ${n?"border-destructive/60":""}`,children:[e.jsxs("div",{className:"flex items-start justify-between flex-wrap gap-3",children:[e.jsxs("div",{children:[e.jsxs("div",{className:"text-xs uppercase tracking-widest text-muted-foreground flex items-center gap-1",children:[e.jsx(Cr,{className:"h-3.5 w-3.5"})," Verified work · last ",(r==null?void 0:r.window_hours)??ze,"h"]}),e.jsx("h2",{className:"text-xl md:text-2xl font-serif mt-1",children:"Is Unk actually publishing?"}),e.jsx("p",{className:`text-3xl font-bold mt-1 ${r?r.publish.completed>0?"text-emerald-600":r.heartbeat_ok?"text-destructive":"text-muted-foreground":"text-muted-foreground"}`,children:r==null?"…":r.publish.completed>0?`Yes — ${r.publish.completed} verified publish(es)`:r.heartbeat_ok?"No verified work":"No — Unk offline"})]}),e.jsxs(E,{size:"sm",variant:"ghost",onClick:i,disabled:s,children:[e.jsx(oe,{className:`h-3 w-3 mr-1 ${s?"animate-spin":""}`})," Refresh"]})]}),r&&e.jsxs("div",{className:"grid gap-3 md:grid-cols-2 lg:grid-cols-3",children:[e.jsx(ts,{label:"Publish jobs (24h)",c:r.publish,icon:Cr}),e.jsxs("div",{className:"rounded-lg border p-3",children:[e.jsxs("div",{className:"flex items-center gap-1.5 text-xs font-medium text-muted-foreground",children:[e.jsx(ge,{className:"h-3.5 w-3.5"})," Desktop"]}),e.jsx("div",{className:"mt-2 text-sm",children:r.desktop_detail})]}),e.jsxs("div",{className:"rounded-lg border p-3",children:[e.jsxs("div",{className:"flex items-center gap-1.5 text-xs font-medium text-muted-foreground",children:[e.jsx(se,{className:"h-3.5 w-3.5"})," Browser receipts"]}),e.jsxs("div",{className:"mt-2 grid grid-cols-3 gap-1 text-center",children:[e.jsxs("div",{children:[e.jsx("div",{className:`text-lg font-bold ${r.receipts.successes>0?"text-emerald-600":"text-muted-foreground"}`,children:r.receipts.successes}),e.jsx("div",{className:"text-[10px] text-muted-foreground",children:"Success"})]}),e.jsxs("div",{className:"flex flex-col items-center",children:[e.jsx("div",{className:`text-lg font-bold ${r.receipts.screenshots>0?"text-emerald-600":"text-muted-foreground"}`,children:r.receipts.screenshots}),e.jsxs("div",{className:"text-[10px] text-muted-foreground flex items-center gap-0.5",children:[e.jsx(It,{className:"h-2.5 w-2.5"}),"Shots"]})]}),e.jsxs("div",{className:"flex flex-col items-center",children:[e.jsx("div",{className:`text-lg font-bold ${r.receipts.post_urls>0?"text-emerald-600":"text-muted-foreground"}`,children:r.receipts.post_urls}),e.jsxs("div",{className:"text-[10px] text-muted-foreground flex items-center gap-0.5",children:[e.jsx(Qt,{className:"h-2.5 w-2.5"}),"URLs"]})]})]})]}),e.jsxs("div",{className:"rounded-lg border p-3",children:[e.jsxs("div",{className:"flex items-center gap-1.5 text-xs font-medium text-muted-foreground",children:[e.jsx(Ye,{className:"h-3.5 w-3.5"})," Campaign progress"]}),e.jsxs("div",{className:"mt-3 text-center",children:[e.jsxs("div",{className:`text-3xl font-bold ${r.campaign.published>0?"text-emerald-600":"text-destructive"}`,children:[r.campaign.published,"/",r.campaign.target]}),e.jsx("div",{className:"text-[10px] text-muted-foreground mt-1",children:"Published this window"})]})]})]}),n&&e.jsxs("div",{className:"rounded-lg border-2 border-destructive/60 bg-destructive/5 p-4 space-y-3",children:[e.jsxs("div",{className:"flex items-start gap-2",children:[e.jsx(Ot,{className:"h-5 w-5 text-destructive shrink-0 mt-0.5"}),e.jsxs("div",{className:"flex-1",children:[e.jsx("div",{className:"font-semibold text-destructive",children:"Investigation open"}),e.jsxs("div",{className:"text-sm mt-0.5",children:["Why has a healthy Unk produced zero verified publishes in the last ",r==null?void 0:r.window_hours,"h?"]}),e.jsx("div",{className:"text-xs text-muted-foreground mt-1",children:"Heartbeat is green but no post URLs, screenshots, or completed publish jobs exist. The publishing workflow is not operational. Walk the pipeline — first missing receipt = broken stage."})]})]}),e.jsx("div",{className:"grid gap-1.5 pl-7",children:c.map((l,m)=>{const f=d===l,g=l.ok?se:Qe;return e.jsxs("div",{className:`flex items-center gap-2 text-xs ${l.ok?"text-emerald-700":f?"text-destructive font-medium":"text-muted-foreground"}`,children:[e.jsxs("span",{className:"font-mono text-[10px] opacity-60",children:[m+1,"."]}),e.jsx(g,{className:"h-3.5 w-3.5"}),e.jsx("span",{children:l.label}),f&&e.jsx(P,{variant:"destructive",className:"ml-1 text-[10px] py-0",children:"Breaks here"})]},l.label)})})]}),r&&e.jsxs("div",{className:"text-[10px] text-muted-foreground",children:["Snapshot ",new Date(r.generated_at).toLocaleTimeString()," · auto-refresh 60s · window ",r.window_hours,"h"]})]})}const ss={unk:"bg-blue-100 text-blue-800 border-blue-200",lovable:"bg-purple-100 text-purple-800 border-purple-200",chatgpt:"bg-emerald-100 text-emerald-800 border-emerald-200",jason:"bg-amber-100 text-amber-800 border-amber-200",monitoring:"bg-slate-100 text-slate-800 border-slate-200"},os={diagnosing:"bg-slate-100 text-slate-700",plan_ready:"bg-blue-100 text-blue-800",implementing:"bg-amber-100 text-amber-800",verifying:"bg-purple-100 text-purple-800",completed:"bg-emerald-100 text-emerald-800",wont_fix:"bg-red-100 text-red-800"},is={recover:"L1 · Recover",repair:"L2 · Repair",prevention:"L3 · Prevention"};function as(){const{toast:r}=Ce(),t=C,[s,o]=w.useState([]),[i,n]=w.useState([]),[c,d]=w.useState(null),[l,m]=w.useState(!0),[f,g]=w.useState(!1),[h,k]=w.useState(null),[v,y]=w.useState(!1),[L,S]=w.useState(!1),[u,x]=w.useState({symptom:"",incident_ref:"",failure_class:"",category:"",owner:"lovable",level:"repair",status:"diagnosing",root_cause:"",repair_plan:"",architecture_changes:"",doctrine_updated:"",regression_test:"",regression_test_passed:!1,regression_prevented:!1,reproduction_method:"",reproduction_result:"not_attempted",post_repair_success_evidence:"",elimination_verified:!1,mission_name:"",mission_baseline:"",mission_current:"",mission_target:"",mission_evidence:"",mission_resumed:!1});async function N(){m(!0);const[p,_,$]=await Promise.all([t.from("mesh_repairs").select("*").order("created_at",{ascending:!1}).limit(50),t.from("mesh_failure_recurrence").select("*").order("total_repairs",{ascending:!1}).limit(20),Ze()]);p.error&&r({title:"Load failed",description:p.error.message,variant:"destructive"}),o(p.data??[]),n(_.data??[]),d($),m(!1)}w.useEffect(()=>{N()},[]);const j=w.useMemo(()=>{if(!c)return new Map;const p=new Map;for(const _ of s)p.set(_.id,Jt({failure_class:_.failure_class,status:_.status,created_at:_.created_at},c));return p},[s,c]);async function R(p,_){const $=`Auto-reconciled from live OpsStatus at ${new Date().toISOString()}: ${_}`,{error:I}=await t.from("mesh_repairs").update({status:"completed",completed_at:new Date().toISOString(),post_repair_success_evidence:$,elimination_verified:!0,mission_resumed:!0,mission_evidence:_}).eq("id",p.id);if(I){r({title:"Update failed",description:I.message,variant:"destructive"});return}r({title:`${p.repair_code} marked recovered by live evidence`}),N()}const T=w.useMemo(()=>{let p=0,_=0;for(const $ of s){if($.status==="completed"||$.status==="wont_fix")continue;const I=j.get($.id);(I==null?void 0:I.live_state)==="recovered_by_evidence"?p++:_++}return{recovered:p,remaining:_}},[s,j]),B=w.useMemo(()=>{const p=s.length,_=s.filter(Z=>!["completed","wont_fix"].includes(Z.status)).length,$=s.filter(Z=>Z.regression_prevented).length,I=s.filter(Z=>Z.elimination_verified).length,M=i.filter(Z=>Z.verdict==="redesign_required"||Z.architectural_flag).length;return{total:p,open:_,prevented:$,eliminated:I,architectural:M}},[s,i]);function K(){k(null),x({symptom:"",incident_ref:"",failure_class:"",category:"",owner:"lovable",level:"repair",status:"diagnosing",root_cause:"",repair_plan:"",architecture_changes:"",doctrine_updated:"",regression_test:"",regression_test_passed:!1,regression_prevented:!1,reproduction_method:"",reproduction_result:"not_attempted",post_repair_success_evidence:"",elimination_verified:!1,mission_name:"",mission_baseline:"",mission_current:"",mission_target:"",mission_evidence:"",mission_resumed:!1})}function J(p){k(p),x({symptom:p.symptom,incident_ref:p.incident_ref??"",failure_class:p.failure_class??"",category:p.category??"",owner:p.owner,level:p.level,status:p.status,root_cause:p.root_cause??"",repair_plan:p.repair_plan??"",architecture_changes:p.architecture_changes??"",doctrine_updated:p.doctrine_updated??"",regression_test:p.regression_test??"",regression_test_passed:p.regression_test_passed,regression_prevented:p.regression_prevented,reproduction_method:p.reproduction_method??"",reproduction_result:p.reproduction_result??"not_attempted",post_repair_success_evidence:p.post_repair_success_evidence??"",elimination_verified:p.elimination_verified,mission_name:p.mission_name??"",mission_baseline:p.mission_baseline??"",mission_current:p.mission_current??"",mission_target:p.mission_target??"",mission_evidence:p.mission_evidence??"",mission_resumed:p.mission_resumed}),g(!0)}async function U(){if(!u.symptom.trim()){r({title:"Symptom required",variant:"destructive"});return}if(u.status==="completed"&&!u.elimination_verified){r({title:"Evidence of Elimination required",description:"Reproduce the failure (or use a representative test) and record post-repair success before marking completed.",variant:"destructive"});return}if(u.status==="completed"&&!u.mission_resumed){r({title:"Mission Evidence required",description:"A repair is complete only when the blocked mission has resumed. Set Mission resumed with baseline → current progress and evidence.",variant:"destructive"});return}y(!0);const p={...u,incident_ref:u.incident_ref||null,failure_class:u.failure_class||null,category:u.category||null,root_cause:u.root_cause||null,repair_plan:u.repair_plan||null,architecture_changes:u.architecture_changes||null,doctrine_updated:u.doctrine_updated||null,regression_test:u.regression_test||null,reproduction_method:u.reproduction_method||null,post_repair_success_evidence:u.post_repair_success_evidence||null,mission_name:u.mission_name||null,mission_baseline:u.mission_baseline||null,mission_current:u.mission_current||null,mission_target:u.mission_target||null,mission_evidence:u.mission_evidence||null};u.status==="completed"&&(p.completed_at=new Date().toISOString());const _=h?t.from("mesh_repairs").update(p).eq("id",h.id):t.from("mesh_repairs").insert(p),{error:$}=await _;if(y(!1),$){r({title:"Save failed",description:$.message,variant:"destructive"});return}r({title:h?"Repair updated":"Repair logged"}),g(!1),K(),N()}return e.jsxs(W,{className:"p-6",children:[e.jsxs("div",{className:"flex items-start justify-between mb-4",children:[e.jsxs("div",{children:[e.jsxs("div",{className:"flex items-center gap-2",children:[e.jsx($e,{className:"h-5 w-5 text-purple-700"}),e.jsx("h2",{className:"text-lg font-bold",children:"Repair Engineering Ledger"})]}),e.jsxs("p",{className:"text-sm text-muted-foreground mt-1",children:["Detect → Diagnose → Recover → ",e.jsx("b",{children:"Repair"})," → Verify → ",e.jsx("b",{children:"Prevent"}),". An incident is not resolved until recovery succeeded, root-cause repair completed, and the regression test passed."]})]}),e.jsxs("div",{className:"flex gap-2",children:[e.jsxs(E,{variant:"outline",size:"sm",onClick:N,disabled:l,children:[e.jsx(oe,{className:`h-4 w-4 mr-1 ${l?"animate-spin":""}`}),"Refresh"]}),e.jsxs(Ft,{open:f,onOpenChange:p=>{g(p),p||K()},children:[e.jsx(Dt,{asChild:!0,children:e.jsxs(E,{size:"sm",onClick:K,children:[e.jsx(Yr,{className:"h-4 w-4 mr-1"})," Log repair"]})}),e.jsxs(Lt,{className:"max-w-2xl max-h-[85vh] overflow-y-auto",children:[e.jsx(Ut,{children:e.jsx(Mt,{children:h?`Edit ${h.repair_code}`:"New repair"})}),e.jsxs("div",{className:"space-y-3",children:[e.jsxs("div",{children:[e.jsx(z,{children:"Symptom *"}),e.jsx(le,{rows:2,value:u.symptom,onChange:p=>x(_=>({..._,symptom:p.target.value})),placeholder:"What broke, observed externally?"})]}),e.jsxs("div",{className:"grid grid-cols-2 gap-3",children:[e.jsxs("div",{children:[e.jsx(z,{children:"Incident ref"}),e.jsx(te,{value:u.incident_ref,onChange:p=>x(_=>({..._,incident_ref:p.target.value})),placeholder:"INC-2026-0042"})]}),e.jsxs("div",{children:[e.jsx(z,{children:"Failure class"}),e.jsx(te,{value:u.failure_class,onChange:p=>x(_=>({..._,failure_class:p.target.value})),placeholder:"browser_selector_drift"})]}),e.jsxs("div",{children:[e.jsx(z,{children:"Category"}),e.jsx(te,{value:u.category,onChange:p=>x(_=>({..._,category:p.target.value})),placeholder:"publishing / desktop / grants"})]}),e.jsxs("div",{children:[e.jsx(z,{children:"Owner"}),e.jsxs(De,{value:u.owner,onValueChange:p=>x(_=>({..._,owner:p})),children:[e.jsx(Le,{children:e.jsx(Ue,{})}),e.jsx(Me,{children:["unk","lovable","chatgpt","jason","monitoring"].map(p=>e.jsx(ce,{value:p,children:p},p))})]})]}),e.jsxs("div",{children:[e.jsx(z,{children:"Level"}),e.jsxs(De,{value:u.level,onValueChange:p=>x(_=>({..._,level:p})),children:[e.jsx(Le,{children:e.jsx(Ue,{})}),e.jsxs(Me,{children:[e.jsx(ce,{value:"recover",children:"L1 · Recover (minutes)"}),e.jsx(ce,{value:"repair",children:"L2 · Repair (hours)"}),e.jsx(ce,{value:"prevention",children:"L3 · Prevention (days)"})]})]})]}),e.jsxs("div",{children:[e.jsx(z,{children:"Status"}),e.jsxs(De,{value:u.status,onValueChange:p=>x(_=>({..._,status:p})),children:[e.jsx(Le,{children:e.jsx(Ue,{})}),e.jsx(Me,{children:["diagnosing","plan_ready","implementing","verifying","completed","wont_fix"].map(p=>e.jsx(ce,{value:p,children:p},p))})]})]})]}),e.jsxs("div",{children:[e.jsx(z,{children:"Root cause"}),e.jsx(le,{rows:2,value:u.root_cause,onChange:p=>x(_=>({..._,root_cause:p.target.value})),placeholder:"Why did this happen — not the symptom, the cause."})]}),e.jsxs("div",{children:[e.jsx(z,{children:"Repair plan (L2)"}),e.jsx(le,{rows:3,value:u.repair_plan,onChange:p=>x(_=>({..._,repair_plan:p.target.value})),placeholder:"Update selector XPATH in multi_platform_publisher.py; deploy new version."})]}),e.jsxs("div",{children:[e.jsx(z,{children:"Architecture changes"}),e.jsx(le,{rows:2,value:u.architecture_changes,onChange:p=>x(_=>({..._,architecture_changes:p.target.value}))})]}),e.jsxs("div",{children:[e.jsx(z,{children:"Doctrine updated (L3)"}),e.jsx(le,{rows:2,value:u.doctrine_updated,onChange:p=>x(_=>({..._,doctrine_updated:p.target.value})),placeholder:"Browser flows now smoke-tested nightly."})]}),e.jsxs("div",{children:[e.jsx(z,{children:"Regression test"}),e.jsx(le,{rows:2,value:u.regression_test,onChange:p=>x(_=>({..._,regression_test:p.target.value})),placeholder:"Nightly smoke test against Meta composer."})]}),e.jsxs("div",{className:"flex gap-4 pt-2 flex-wrap",children:[e.jsxs("label",{className:"flex items-center gap-2 text-sm",children:[e.jsx("input",{type:"checkbox",checked:u.regression_test_passed,onChange:p=>x(_=>({..._,regression_test_passed:p.target.checked}))}),"Regression test passed"]}),e.jsxs("label",{className:"flex items-center gap-2 text-sm",children:[e.jsx("input",{type:"checkbox",checked:u.regression_prevented,onChange:p=>x(_=>({..._,regression_prevented:p.target.checked}))}),"Regression prevented"]})]}),e.jsxs("div",{className:"rounded border-2 border-purple-200 bg-purple-50/40 p-3 mt-2 space-y-3",children:[e.jsxs("div",{className:"flex items-center gap-2 text-sm font-semibold text-purple-900",children:[e.jsx(ir,{className:"h-4 w-4"})," Evidence of Elimination (required to complete)"]}),e.jsx("p",{className:"text-xs text-muted-foreground",children:"Prove the specific failure mode is gone. Reproduce the original failure (or run a representative test), then confirm a valid input succeeds afterward."}),e.jsxs("div",{children:[e.jsx(z,{children:"Reproduction method"}),e.jsx(le,{rows:2,value:u.reproduction_method,onChange:p=>x(_=>({..._,reproduction_method:p.target.value})),placeholder:"Inject invalid Meta token and confirm detection→recovery→escalation path fires."})]}),e.jsxs("div",{className:"grid grid-cols-2 gap-3",children:[e.jsxs("div",{children:[e.jsx(z,{children:"Reproduction result"}),e.jsxs(De,{value:u.reproduction_result,onValueChange:p=>x(_=>({..._,reproduction_result:p})),children:[e.jsx(Le,{children:e.jsx(Ue,{})}),e.jsxs(Me,{children:[e.jsx(ce,{value:"failure_reproduced",children:"Failure reproduced (best)"}),e.jsx(ce,{value:"representative_test",children:"Representative test"}),e.jsx(ce,{value:"failure_not_reproduced",children:"Failure NOT reproduced"}),e.jsx(ce,{value:"not_attempted",children:"Not attempted"})]})]})]}),e.jsxs("label",{className:"flex items-end gap-2 text-sm pb-2",children:[e.jsx("input",{type:"checkbox",checked:u.elimination_verified,onChange:p=>x(_=>({..._,elimination_verified:p.target.checked}))}),"Elimination verified"]})]}),e.jsxs("div",{children:[e.jsx(z,{children:"Post-repair success evidence"}),e.jsx(le,{rows:2,value:u.post_repair_success_evidence,onChange:p=>x(_=>({..._,post_repair_success_evidence:p.target.value})),placeholder:"Valid token → publish job completed with URL https://…"})]})]}),e.jsxs("div",{className:"rounded border-2 border-emerald-200 bg-emerald-50/40 p-3 mt-2 space-y-3",children:[e.jsxs("div",{className:"flex items-center gap-2 text-sm font-semibold text-emerald-900",children:[e.jsx(_r,{className:"h-4 w-4"})," Mission Evidence (required to complete)"]}),e.jsx("p",{className:"text-xs text-muted-foreground",children:"A repair is not complete because the bug disappeared. It is complete when the mission that was blocked has resumed with measurable, verified progress."}),e.jsxs("div",{children:[e.jsx(z,{children:"Blocked mission"}),e.jsx(te,{value:u.mission_name,onChange:p=>x(_=>({..._,mission_name:p.target.value})),placeholder:"STV publishing campaign / grant XYZ / participant onboarding"})]}),e.jsxs("div",{className:"grid grid-cols-3 gap-3",children:[e.jsxs("div",{children:[e.jsx(z,{children:"Baseline"}),e.jsx(te,{value:u.mission_baseline,onChange:p=>x(_=>({..._,mission_baseline:p.target.value})),placeholder:"0/28"})]}),e.jsxs("div",{children:[e.jsx(z,{children:"Current"}),e.jsx(te,{value:u.mission_current,onChange:p=>x(_=>({..._,mission_current:p.target.value})),placeholder:"3/28"})]}),e.jsxs("div",{children:[e.jsx(z,{children:"Target"}),e.jsx(te,{value:u.mission_target,onChange:p=>x(_=>({..._,mission_target:p.target.value})),placeholder:"28/28"})]})]}),e.jsxs("div",{children:[e.jsx(z,{children:"Mission evidence"}),e.jsx(le,{rows:2,value:u.mission_evidence,onChange:p=>x(_=>({..._,mission_evidence:p.target.value})),placeholder:"3 verified post URLs, mesh_verifications rows, recovery queue empty"})]}),e.jsxs("label",{className:"flex items-center gap-2 text-sm font-semibold text-emerald-900",children:[e.jsx("input",{type:"checkbox",checked:u.mission_resumed,onChange:p=>x(_=>({..._,mission_resumed:p.target.checked}))}),"Mission resumed — real-world outcome verified"]})]})]}),e.jsxs(Bt,{children:[e.jsx(E,{variant:"outline",onClick:()=>g(!1),children:"Cancel"}),e.jsx(E,{onClick:U,disabled:v,children:v?"Saving…":h?"Save":"Log repair"})]})]})]})]})]}),e.jsxs("div",{className:"grid grid-cols-2 md:grid-cols-5 gap-3 mb-4",children:[e.jsx(ke,{icon:e.jsx($e,{className:"h-4 w-4"}),label:"Total repairs",value:l?"—":B.total}),e.jsx(ke,{icon:e.jsx(Ye,{className:"h-4 w-4 text-amber-700"}),label:l?"Open":`Open (${T.remaining} truly)`,value:l?"—":B.open,tone:"amber"}),e.jsx(ke,{icon:e.jsx(ir,{className:"h-4 w-4 text-purple-700"}),label:"Elimination verified",value:l?"—":B.eliminated,tone:"purple"}),e.jsx(ke,{icon:e.jsx(ee,{className:"h-4 w-4 text-emerald-700"}),label:"Regressions prevented",value:l?"—":B.prevented,tone:"emerald"}),e.jsx(ke,{icon:e.jsx(Ke,{className:"h-4 w-4 text-red-700"}),label:"Architectural flags",value:l?"—":B.architectural,tone:"red"})]}),T.recovered>0&&e.jsx("div",{className:"mb-4 rounded border-2 border-emerald-300 bg-emerald-50 p-3 text-sm",children:e.jsxs("div",{className:"flex items-start gap-2",children:[e.jsx(se,{className:"h-4 w-4 text-emerald-700 mt-0.5 shrink-0"}),e.jsxs("div",{className:"flex-1",children:[e.jsxs("div",{className:"font-semibold text-emerald-900",children:[T.recovered," incident",T.recovered===1?"":"s"," recovered by live evidence"]}),e.jsx("div",{className:"text-xs text-emerald-800 mt-0.5",children:"Current heartbeat, supervisor state, and verified receipts prove these are no longer blocking. Click the green chip on each to confirm the recovery in the ledger."})]})]})}),i.length>0&&e.jsxs("div",{className:"mb-5 rounded border bg-slate-50/50 p-3",children:[e.jsxs("div",{className:"flex items-center gap-2 mb-2 text-sm font-semibold",children:[e.jsx(Ke,{className:"h-4 w-4 text-red-700"}),"Failure Recurrence Rate",e.jsx("span",{className:"text-xs font-normal text-muted-foreground",children:"— 3+ repeats with no prevention win = redesign, not another patch."})]}),e.jsx("div",{className:"space-y-1",children:i.map(p=>{const _={redesign_required:"bg-red-100 text-red-800 border-red-300",monitor_architecture:"bg-amber-100 text-amber-800 border-amber-300",watch:"bg-blue-100 text-blue-800 border-blue-300",stable:"bg-emerald-100 text-emerald-800 border-emerald-300"}[p.verdict];return e.jsxs("div",{className:"flex items-center justify-between gap-3 text-sm py-1 border-b last:border-0",children:[e.jsxs("div",{className:"flex items-center gap-2 flex-1 min-w-0",children:[e.jsx(P,{variant:"outline",className:_,children:p.verdict.replace(/_/g," ")}),e.jsx("span",{className:"font-mono text-xs truncate",children:p.failure_class})]}),e.jsxs("div",{className:"flex items-center gap-4 text-xs text-muted-foreground whitespace-nowrap",children:[e.jsxs("span",{children:[p.total_repairs," repairs"]}),e.jsxs("span",{children:[p.recurrences_90d," in 90d"]}),e.jsxs("span",{className:"text-emerald-700",children:[p.prevention_wins," prevented"]})]})]},p.failure_class)})})]}),(()=>{const p=s.filter(M=>M.owner==="monitoring"),_=p.filter(M=>!["completed","wont_fix"].includes(M.status)).length,$=p.filter(M=>!["completed","wont_fix"].includes(M.status)).sort((M,Z)=>M.created_at.localeCompare(Z.created_at))[0],I=$?Math.round((Date.now()-new Date($.created_at).getTime())/6e4):null;return p.length===0?null:e.jsx("div",{className:"mb-4 rounded border bg-slate-50/60 p-3",children:e.jsxs("div",{className:"flex items-start justify-between gap-3",children:[e.jsxs("div",{className:"flex-1 min-w-0",children:[e.jsxs("div",{className:"text-sm font-semibold flex items-center gap-2",children:[e.jsx(ee,{className:"h-4 w-4 text-slate-600"}),"Operations Monitoring"]}),e.jsxs("div",{className:"mt-1 text-xs text-muted-foreground space-x-3",children:[e.jsxs("span",{children:[_," open verification claim",_===1?"":"s"]}),e.jsxs("span",{children:[p.length-_," confirmed"]}),I!==null&&e.jsxs("span",{children:["Oldest open: ",I," min"]}),e.jsxs("span",{children:[p.length," total records"]})]})]}),e.jsxs("div",{className:"flex gap-2",children:[e.jsx("a",{href:"/grant-engine/operations-log",children:e.jsx(E,{variant:"outline",size:"sm",children:"View detailed log"})}),e.jsx(E,{variant:"ghost",size:"sm",onClick:()=>S(M=>!M),children:L?"Hide inline":`Show ${p.length} inline`})]})]})})})(),l?e.jsx("div",{className:"text-sm text-muted-foreground",children:"Loading…"}):(()=>{const p=L?s:s.filter(_=>_.owner!=="monitoring");return p.length===0?e.jsxs("div",{className:"rounded border border-dashed p-6 text-center text-sm text-muted-foreground",children:[e.jsx(ie,{className:"h-5 w-5 mx-auto mb-2 opacity-60"}),"No actionable repairs. Monitoring-generated records are in the detailed log."]}):e.jsx("div",{className:"space-y-2",children:p.map(_=>{const $=j.get(_.id),I=($==null?void 0:$.live_state)==="recovered_by_evidence";return e.jsx("div",{className:`rounded border p-3 hover:bg-muted/40 cursor-pointer ${I?"border-emerald-300 bg-emerald-50/40":""}`,onClick:()=>J(_),children:e.jsxs("div",{className:"flex items-start justify-between gap-3",children:[e.jsxs("div",{className:"flex-1 min-w-0",children:[e.jsxs("div",{className:"flex flex-wrap items-center gap-2 mb-1",children:[e.jsx("span",{className:"font-mono text-xs font-semibold",children:_.repair_code}),e.jsx(P,{variant:"outline",className:os[_.status],children:_.status}),e.jsx(P,{variant:"outline",className:ss[_.owner],children:_.owner}),e.jsx(P,{variant:"outline",children:is[_.level]}),I&&e.jsxs(P,{variant:"outline",className:"bg-emerald-100 text-emerald-900 border-emerald-400 cursor-pointer hover:bg-emerald-200",onClick:M=>{M.stopPropagation(),R(_,$.note)},title:"Click to mark recovered in the ledger",children:[e.jsx(se,{className:"h-3 w-3 mr-1"})," recovered by live evidence — click to confirm"]}),_.elimination_verified&&e.jsxs(P,{variant:"outline",className:"bg-purple-50 text-purple-800 border-purple-200",children:[e.jsx(ir,{className:"h-3 w-3 mr-1"})," elimination ✓"]}),_.regression_test_passed&&e.jsxs(P,{variant:"outline",className:"bg-emerald-50 text-emerald-800 border-emerald-200",children:[e.jsx(se,{className:"h-3 w-3 mr-1"})," regression ✓"]}),_.mission_resumed&&e.jsxs(P,{variant:"outline",className:"bg-emerald-100 text-emerald-900 border-emerald-300",children:[e.jsx(_r,{className:"h-3 w-3 mr-1"})," mission resumed"]}),_.architectural_flag&&e.jsxs(P,{variant:"outline",className:"bg-red-100 text-red-800 border-red-300",children:[e.jsx(Ke,{className:"h-3 w-3 mr-1"})," architectural"]}),_.prior_repairs_in_class>0&&e.jsxs(P,{variant:"outline",className:"bg-amber-50 text-amber-700 border-amber-200",children:["recurrence #",_.prior_repairs_in_class+1]})]}),e.jsx("div",{className:"text-sm font-medium truncate",children:_.symptom}),I&&($==null?void 0:$.note)&&e.jsxs("div",{className:"text-xs text-emerald-800 mt-1",children:[e.jsx("span",{className:"font-medium",children:"Live evidence:"})," ",$.note]}),_.root_cause&&e.jsxs("div",{className:"text-xs text-muted-foreground mt-1 line-clamp-2",children:[e.jsx("span",{className:"font-medium text-foreground",children:"Root cause:"})," ",_.root_cause]})]}),e.jsx("div",{className:"text-xs text-muted-foreground whitespace-nowrap",children:new Date(_.created_at).toLocaleDateString()})]})},_.id)})})})()]})}function ke({icon:r,label:t,value:s,tone:o="slate"}){const i={slate:"bg-slate-50",amber:"bg-amber-50",emerald:"bg-emerald-50",purple:"bg-purple-50",red:"bg-red-50"}[o]??"bg-slate-50";return e.jsxs("div",{className:`rounded border p-3 ${i}`,children:[e.jsxs("div",{className:"flex items-center gap-2 text-xs text-muted-foreground",children:[r,e.jsx("span",{children:t})]}),e.jsx("div",{className:"text-2xl font-bold mt-1",children:s})]})}const Mr=90,ur=5,Br=C;async function ls(r){const{count:t,error:s}=await r;return s?null:t??0}async function cs(){const r=await Ze();let t,s;if(!r.desktop.ok)t=null,s="Status unavailable — desktop evidence query failed";else if(r.desktop.total_active===0)t=null,s="Not enough data — no desktop enrolled";else{t=Math.round(r.desktop.fresh/r.desktop.total_active*100);const T=r.desktop.latest_heartbeat_at?new Date(r.desktop.latest_heartbeat_at).toLocaleTimeString():"∅";s=`${r.desktop.fresh}/${r.desktop.total_active} desktops fresh (window ${r.desktop.fresh_window_seconds}s) · latest heartbeat ${T} (${r.desktop.heartbeat_age_seconds??"∅"}s ago) · supervisor: ${r.supervisor.reason}`}const o=r.publishing.verified_receipts_24h+r.publishing.failed_24h;let i,n;r.publishing.ok?o===0?(i=null,n=`Not enough data — 0 verified receipts and 0 failures in last ${ze}h`):(i=Math.round(r.publishing.verified_receipts_24h/o*100),n=`${r.publishing.verified_receipts_24h} verified · ${r.publishing.failed_24h} failed (${ze}h) · ${r.publishing.verified_stv_receipts} STV all-time`):(i=null,n="Status unavailable — publishing evidence query failed");const c=await ls(Br.from("mesh_repairs").select("id",{count:"exact",head:!0}).eq("status","completed")),d=c!==null&&r.recovery_queue.ok,l=r.recovery_queue.ok?r.recovery_queue.open_actionable:0,m=d?c+l:0,f=!d||m===0?null:Math.round(c/m*100),g=c===null?"Status unavailable — completed-repair evidence query failed":r.recovery_queue.ok?m===0?"Not enough data — no repairs logged":`${c} completed · ${l} actionable · ${r.recovery_queue.reason}`:"Status unavailable — recovery queue evidence query failed",{data:h,error:k}=await Br.from("mesh_failure_recurrence").select("verdict, recurrences_90d"),v=k?-1:(h??[]).length,y=k?0:(h??[]).filter(T=>["redesign_required","monitor_architecture"].includes(T.verdict)).length,L=v<=0?null:Math.max(0,Math.round(100-y/v*100)),S=k?`Status unavailable — recurrence evidence query failed: ${k.message}`:v===0?"Not enough data — no recurrence classes tracked":`${y}/${v} classes flagged for architecture review`,u=r.publishing.verified_stv_receipts,x=r.mission_completion.target,N=!r.publishing.ok||x===0||u===0?null:Math.min(100,Math.round(u/x*100)),j=r.publishing.ok?x===0?"Not enough data — no mission target configured":u===0?"Not enough data — 0 verified STV receipts yet":`${u}/${x} verified STV receipts`:"Status unavailable — verified mission receipt evidence query failed";return{factors:[{key:"trust",label:"Operational Trust",score:t,icon:ee,detail:s},{key:"work",label:"Verified Work",score:i,icon:se,detail:n},{key:"repair",label:"Repair Effectiveness",score:f,icon:$e,detail:g},{key:"recurrence",label:"Failure Recurrence",score:L,icon:Ke,detail:S},{key:"mission",label:"Mission Completion",score:N,icon:_r,detail:j}],ops:r}}function ds(){const[r,t]=w.useState(null),[s,o]=w.useState(!1),[i,n]=w.useState(null),[c,d]=w.useState(null);async function l(){o(!0),d(null);try{const{factors:y}=await cs();t(y),n(new Date)}catch(y){console.warn("[MissionReliability]",y),d(y instanceof Error?y.message:String(y)),t(null)}finally{o(!1)}}w.useEffect(()=>{l();const y=setInterval(()=>void l(),12e4);return()=>clearInterval(y)},[]);const m=w.useMemo(()=>(r==null?void 0:r.filter(y=>y.score!==null).length)??0,[r]),f=w.useMemo(()=>{if(!r||r.length!==ur)return null;const y=r.filter(L=>L.score!==null);return y.length!==r.length?null:Math.round(y.reduce((L,S)=>L+S.score,0)/ur)},[r]),g=f!==null,h=g&&f<Mr,k=g?f>=90?"emerald":f>=75?"amber":"red":"amber",v={emerald:"text-emerald-700 bg-emerald-50 border-emerald-200",amber:"text-amber-800 bg-amber-50 border-amber-200",red:"text-red-800 bg-red-50 border-red-200"};return c?e.jsx(W,{className:"p-5 border-amber-500/40 bg-amber-500/5",children:e.jsxs("div",{className:"flex items-start gap-2",children:[e.jsx(ie,{className:"h-5 w-5 text-amber-700 mt-0.5"}),e.jsxs("div",{children:[e.jsx("div",{className:"font-semibold",children:"Mission Reliability could not be verified"}),e.jsx("div",{className:"mt-1 text-xs text-muted-foreground",children:c}),e.jsxs(E,{variant:"outline",size:"sm",className:"mt-3",onClick:l,disabled:s,children:[e.jsx(oe,{className:`h-4 w-4 mr-1 ${s?"animate-spin":""}`})," Retry"]})]})]})}):e.jsxs(W,{className:"p-6",children:[e.jsxs("div",{className:"flex items-start justify-between mb-4 gap-3 flex-wrap",children:[e.jsxs("div",{className:"min-w-0",children:[e.jsxs("div",{className:"flex items-center gap-2",children:[e.jsx(Ar,{className:"h-5 w-5 text-primary"}),e.jsx("h2",{className:"text-lg font-bold",children:"Mission Reliability"})]}),e.jsx("p",{className:"text-sm text-muted-foreground mt-1",children:"Can the platform run unattended and leave behind verified mission progress? All five factors must be measured before a composite exists."})]}),e.jsxs(E,{variant:"outline",size:"sm",onClick:l,disabled:s,children:[e.jsx(oe,{className:`h-4 w-4 mr-1 ${s?"animate-spin":""}`})," Refresh"]})]}),e.jsx("div",{className:`rounded-lg border-2 p-5 mb-4 ${v[k]}`,children:e.jsxs("div",{className:"flex items-center justify-between",children:[e.jsxs("div",{children:[e.jsx("div",{className:"text-xs font-semibold uppercase tracking-widest opacity-80",children:"Composite score"}),e.jsxs("div",{className:"flex items-baseline gap-3 mt-1 flex-wrap",children:[e.jsx("div",{className:"text-5xl font-bold tabular-nums",children:f===null?"—":`${f}%`}),e.jsx(P,{variant:"outline",className:"bg-white/60",children:g?f>=90?"Healthy":f>=75?"Watch":"Improvement mode":`Not fully measured · ${m}/${ur}`})]}),!g&&e.jsx("div",{className:"text-xs opacity-80 mt-1",children:"Partial evidence is never averaged into a platform reliability score."}),i&&e.jsxs("div",{className:"text-[11px] opacity-70 mt-1",children:["Updated ",i.toLocaleTimeString()]})]}),e.jsx(Ar,{className:"h-16 w-16 opacity-30"})]})}),h&&e.jsx("div",{className:"rounded border-2 border-red-300 bg-red-50 p-4 mb-4",children:e.jsxs("div",{className:"flex items-start gap-2",children:[e.jsx(ie,{className:"h-5 w-5 text-red-700 mt-0.5 flex-shrink-0"}),e.jsxs("div",{children:[e.jsxs("div",{className:"font-bold text-red-900 mb-1",children:["Improvement Mode — reliability below ",Mr,"%"]}),e.jsx("p",{className:"text-sm text-red-800 mb-2",children:"Prioritize open repairs before adding unrelated features."})]})]})}),e.jsx("div",{className:"space-y-2",children:(r??[]).map(y=>{const L=y.icon,S=y.score===null?"text-amber-700":y.score>=90?"text-emerald-700":y.score>=75?"text-amber-700":"text-red-700";return e.jsxs("div",{className:"rounded border p-3",children:[e.jsxs("div",{className:"flex items-center justify-between mb-1.5 gap-2 flex-wrap",children:[e.jsxs("div",{className:"flex items-center gap-2",children:[e.jsx(L,{className:`h-4 w-4 ${S}`}),e.jsx("span",{className:"text-sm font-semibold",children:y.label})]}),e.jsx("span",{className:`text-sm font-bold tabular-nums ${S}`,children:y.score===null?"Unmeasured":`${y.score}%`})]}),y.score!==null&&e.jsx(Wt,{value:y.score,className:"h-1.5 mb-1.5"}),e.jsx("div",{className:"text-xs text-muted-foreground",children:y.detail})]},y.key)})})]})}const qe=r=>r?new Date(r).toLocaleString():"—";function ps(r){return r==="verified"?e.jsx(P,{className:"bg-emerald-600",children:"Verified"}):r==="rolled_back"?e.jsx(P,{variant:"destructive",children:"Rolled back"}):r==="verifying"?e.jsx(P,{className:"bg-blue-600",children:"Verifying…"}):r==="staged"?e.jsx(P,{variant:"secondary",children:"Staged"}):e.jsx(P,{variant:"outline",children:r})}function us({deviceId:r,runningVersion:t,runningBuildRef:s,lastHeartbeatAt:o,latestBuildUrl:i}){const[n,c]=w.useState(null),[d,l]=w.useState(null),[m,f]=w.useState(!0),[g,h]=w.useState(!1),[k,v]=w.useState(0);w.useEffect(()=>{let R=!0;return(async()=>{f(!0);const[{data:T},{data:B}]=await Promise.all([C.from("desktop_update_verifications").select("*").eq("device_id",r).order("created_at",{ascending:!1}).limit(1),C.from("desktop_update_verifications").select("*").eq("device_id",r).eq("status","verified").order("verified_at",{ascending:!1}).limit(1)]);R&&(c((T==null?void 0:T[0])??null),l((B==null?void 0:B[0])??null),f(!1))})(),()=>{R=!1}},[r,k]);const y=async()=>{if(!N){Se.error(j);return}if(confirm("Force-accept this staged build only because Ground Zero is online and its fresh heartbeat reports the staged build. Continue?")){h(!0);try{const{data:R,error:T}=await C.functions.invoke("desktop-update-verify",{body:{action:"force_accept",device_id:r}});T||R!=null&&R.error?Se.error((R==null?void 0:R.error)||(T==null?void 0:T.message)||"Force-accept failed"):(Se.success("Build force-accepted"),v(B=>B+1))}finally{h(!1)}}},L=i.split("/").pop()??i,S=!!o&&Date.now()-new Date(o).getTime()<=2*60*1e3,u=!!n&&["rolled_back","staged","verifying"].includes(n.status),x=!!n&&!!s&&(!n.new_build_ref||s===n.new_build_ref),N=u&&S&&x,j=u?S?s?x?"Ground Zero is online and reporting the staged build.":"Ground Zero is not reporting the staged build.":"Ground Zero is online, but the heartbeat has no running build receipt yet.":"Start or restart Ground Zero first; force-accept is locked until a fresh heartbeat arrives.":"No staged, verifying, or rolled-back build is waiting for rescue.";return e.jsxs("div",{className:"rounded border bg-muted/20 p-3 space-y-2 text-xs",children:[e.jsxs("div",{className:"flex items-center gap-1 text-xs font-medium",children:[e.jsx(Xt,{className:"h-3 w-3"})," Version receipt"]}),e.jsxs("div",{className:"grid grid-cols-1 md:grid-cols-2 gap-y-1 gap-x-4",children:[e.jsxs("div",{children:[e.jsx("span",{className:"text-muted-foreground",children:"Verified running: "}),t?e.jsx("span",{className:"font-mono",children:t}):e.jsx("span",{className:"text-muted-foreground",children:"unknown (no heartbeat)"})]}),e.jsxs("div",{className:"truncate",title:i,children:[e.jsx("span",{className:"text-muted-foreground",children:"Latest build asset: "}),e.jsx("span",{className:"font-mono",children:L})]}),e.jsxs("div",{className:"md:col-span-2 truncate",title:s??void 0,children:[e.jsx("span",{className:"text-muted-foreground",children:"Running build receipt: "}),e.jsx("span",{className:"font-mono",children:s??"none reported"})]}),e.jsxs("div",{children:[e.jsx("span",{className:"text-muted-foreground",children:"Last update result: "}),m?"…":n?ps(n.status):e.jsx("span",{className:"text-muted-foreground",children:"never updated"})]}),e.jsxs("div",{children:[e.jsx("span",{className:"text-muted-foreground",children:"Last verified update: "}),m?"…":d?e.jsxs("span",{className:"inline-flex items-center gap-1",children:[e.jsx(se,{className:"h-3 w-3 text-emerald-600"}),qe(d.verified_at)]}):e.jsx("span",{className:"text-muted-foreground",children:"none on record"})]})]}),n&&e.jsxs("div",{className:"border-t pt-2 grid grid-cols-1 md:grid-cols-2 gap-y-1 gap-x-4",children:[e.jsxs("div",{className:"truncate",title:n.prev_build_ref??void 0,children:[e.jsx("span",{className:"text-muted-foreground",children:"From: "}),e.jsx("span",{className:"font-mono",children:n.prev_build_ref??"—"})]}),e.jsxs("div",{className:"truncate",title:n.new_build_ref??void 0,children:[e.jsx("span",{className:"text-muted-foreground",children:"To: "}),e.jsx("span",{className:"font-mono",children:n.new_build_ref??"—"})]}),e.jsxs("div",{children:[e.jsx("span",{className:"text-muted-foreground",children:"Staged: "}),qe(n.created_at)]}),e.jsxs("div",{children:[e.jsx("span",{className:"text-muted-foreground",children:"Token ack: "}),n.token_ack_at?e.jsxs("span",{className:"inline-flex items-center gap-1",children:[e.jsx(se,{className:"h-3 w-3 text-emerald-600"})," ",qe(n.token_ack_at)]}):e.jsxs("span",{className:"inline-flex items-center gap-1 text-muted-foreground",children:[e.jsx(Ye,{className:"h-3 w-3"})," waiting"]})]}),e.jsxs("div",{children:[e.jsx("span",{className:"text-muted-foreground",children:"Heartbeats seen: "}),n.heartbeats_seen??0," / 2"]}),n.status==="rolled_back"&&e.jsxs("div",{className:"md:col-span-2 text-red-700 inline-flex items-start gap-1",children:[e.jsx(Qe,{className:"h-3 w-3 mt-0.5"}),e.jsxs("span",{children:["Rolled back: ",n.rollback_reason??"no reason recorded"," (",qe(n.rolled_back_at),")"]})]}),(n.status==="rolled_back"||n.status==="staged"||n.status==="verifying")&&e.jsxs("div",{className:"md:col-span-2 pt-1",children:[e.jsxs(E,{size:"sm",variant:"outline",onClick:y,disabled:g||!N,children:[g?e.jsx(Vr,{className:"h-3 w-3 mr-1 animate-spin"}):e.jsx(ee,{className:"h-3 w-3 mr-1"}),"Force accept live staged build"]}),e.jsx("p",{className:"text-[11px] text-muted-foreground mt-1",children:j})]})]})]})}function _s(){var f;const{toast:r}=Ce(),[t,s]=w.useState(!1),[o,i]=w.useState(null),[n,c]=w.useState(null),[d,l]=w.useState(null),m=async()=>{s(!0),i(null),l(null);try{const{data:g,error:h}=await C.functions.invoke("desktop-heartbeat-watchdog",{body:{manual:!0}});if(h)throw h;const k=g??{};i(k),c(new Date().toISOString());const{data:v}=await C.from("infrastructure_events").select("id, failure_class, title, description, detected_at, resumed_at, auto_resolved").order("detected_at",{ascending:!1}).limit(1).maybeSingle();v&&l(v),r({title:"Watchdog complete",description:`Checked ${k.checked??0} stale device(s), alerted ${k.alerted??0}.`})}catch(g){const h=(g==null?void 0:g.message)??String(g);i({ok:!1,error:h}),r({title:"Watchdog failed",description:h,variant:"destructive"})}finally{s(!1)}};return e.jsxs(W,{className:"p-5 space-y-3",children:[e.jsxs("div",{className:"flex items-start justify-between gap-3 flex-wrap",children:[e.jsxs("div",{children:[e.jsxs("h2",{className:"text-lg font-semibold flex items-center gap-2",children:[e.jsx(Ne,{className:"h-4 w-4 text-amber-500"})," Recovery Watchdog"]}),e.jsx("p",{className:"text-xs text-muted-foreground",children:"Runs the backend repair pass on demand: classifies any stale desktop, writes an Infrastructure Recovery receipt, and closes prior events if heartbeat returned."})]}),e.jsxs(E,{onClick:m,disabled:t,size:"sm",children:[t?e.jsx(Vr,{className:"h-4 w-4 mr-2 animate-spin"}):e.jsx(Ne,{className:"h-4 w-4 mr-2"}),t?"Running…":"Run recovery watchdog now"]})]}),o&&e.jsxs("div",{className:"rounded-md border p-3 space-y-2",children:[e.jsxs("div",{className:"flex items-center gap-2 text-sm",children:[o.ok?e.jsx(se,{className:"h-4 w-4 text-emerald-500"}):e.jsx(Ne,{className:"h-4 w-4 text-rose-500"}),e.jsx("span",{className:"font-medium",children:o.ok?"Receipt":"Failed"}),n&&e.jsxs("span",{className:"text-xs text-muted-foreground",children:["· ",new Date(n).toLocaleTimeString()]}),o.ok&&e.jsxs(e.Fragment,{children:[e.jsxs(P,{variant:"outline",children:["checked ",o.checked??0]}),e.jsxs(P,{variant:o.alerted?"destructive":"outline",children:["alerted ",o.alerted??0]})]})]}),o.error&&e.jsx("div",{className:"text-xs text-rose-500",children:o.error}),o.results&&o.results.length>0&&e.jsx("ul",{className:"text-xs space-y-1",children:o.results.map((g,h)=>e.jsxs("li",{className:"flex items-center gap-2",children:[e.jsx("span",{className:"font-medium",children:g.device}),e.jsx(P,{variant:"secondary",children:g.action}),g.minutes_silent!=null&&e.jsxs("span",{className:"text-muted-foreground",children:["silent ",g.minutes_silent,"m"]})]},h))}),o.ok&&(((f=o.results)==null?void 0:f.length)??0)===0&&e.jsx("div",{className:"text-xs text-muted-foreground",children:"Nothing stale. All active desktop companions reported within the heartbeat window."})]}),d&&e.jsxs("div",{className:"rounded-md border p-3 text-xs",children:[e.jsxs("div",{className:"flex items-center gap-2",children:[e.jsx("span",{className:"font-medium",children:"Latest infrastructure event"}),e.jsx(P,{variant:"outline",children:d.failure_class}),d.resumed_at?e.jsx(P,{variant:"outline",children:"resumed"}):e.jsx(P,{variant:"destructive",children:"open"})]}),e.jsx("div",{className:"mt-1",children:d.title}),d.description&&e.jsx("div",{className:"text-muted-foreground mt-0.5",children:d.description}),e.jsx("div",{className:"text-[11px] text-muted-foreground mt-1",children:new Date(d.detected_at).toLocaleString()})]})]})}const Wr={meta_token:"Meta / Facebook Token",meta_dashboard:"Meta Dashboard",companion:"Desktop Companion",publish_queue:"Publish Queue",browser_signin:"Browser Sign-in",connector_token:"Connector Tokens",edge_function:"Edge Functions",stuck_job:"Stuck Jobs",ai_budget:"AI Budget",cron_heartbeat:"Cron Heartbeat"},Gr=(r,t)=>r==="healthy"?e.jsx(P,{className:"bg-emerald-600 hover:bg-emerald-600",children:"Healthy"}):r==="repaired"?e.jsx(P,{className:"bg-blue-600 hover:bg-blue-600",children:"Auto-repaired"}):r==="repair_queued"?e.jsx(P,{className:"bg-amber-600 hover:bg-amber-600",children:"Repair queued"}):r==="unhealable"?e.jsx(P,{variant:"destructive",children:"Needs Jason"}):r==="escalated"?e.jsx(P,{variant:"destructive",children:"Escalated"}):e.jsx(P,{variant:"outline",children:r});function ms(){const[r,t]=w.useState([]),[s,o]=w.useState([]),[i,n]=w.useState(!1),c=async()=>{const[{data:g},{data:h}]=await Promise.all([C.from("platform_heal_status").select("*"),C.from("platform_heal_events").select("id, domain, check_key, status, severity, detected_issue, repair_action, triggered_by, created_at").order("created_at",{ascending:!1}).limit(15)]);t(g??[]),o((h??[]).map(k=>({...k,last_checked_at:k.created_at})))};w.useEffect(()=>{c();const g=setInterval(c,3e4);return()=>clearInterval(g)},[]);const d=async()=>{var g;n(!0);try{const{data:h,error:k}=await C.functions.invoke("publish-preflight-heal",{body:{triggered_by:"manual"}});if(k)throw k;const v=((g=h==null?void 0:h.blockers)==null?void 0:g.length)??0;Se[v?"warning":"success"](v?`Heal ran. ${v} blocker(s) need Jason.`:"Self-heal complete. All green."),await c()}catch(h){Se.error(`Self-heal failed: ${(h==null?void 0:h.message)??h}`)}finally{n(!1)}},l=["meta_token","meta_dashboard","companion","publish_queue","browser_signin","connector_token","edge_function","stuck_job","ai_budget","cron_heartbeat"],m=new Map(r.map(g=>[g.domain,g])),f=r.find(g=>g.status==="unhealable"||g.status==="escalated");return e.jsxs(W,{children:[e.jsxs(vr,{className:"flex flex-row items-center justify-between",children:[e.jsxs("div",{className:"flex items-center gap-2",children:[f?e.jsx(ie,{className:"h-5 w-5 text-destructive"}):e.jsx(ee,{className:"h-5 w-5 text-emerald-600"}),e.jsx(yr,{children:"Platform Self-Heal"})]}),e.jsxs("div",{className:"flex items-center gap-2",children:[e.jsx(E,{size:"sm",variant:"ghost",asChild:!0,children:e.jsx("a",{href:"/grant-engine/self-heal",children:"Full center →"})}),e.jsxs(E,{size:"sm",variant:"outline",onClick:d,disabled:i,children:[e.jsx(oe,{className:`h-4 w-4 mr-2 ${i?"animate-spin":""}`}),"Run heal now"]})]})]}),e.jsxs(br,{className:"space-y-4",children:[e.jsx("div",{className:"grid grid-cols-1 md:grid-cols-2 gap-2",children:l.map(g=>{const h=m.get(g);return e.jsxs("div",{className:"flex items-start justify-between border rounded-md p-3",children:[e.jsxs("div",{className:"min-w-0",children:[e.jsx("div",{className:"font-medium text-sm",children:Wr[g]??g}),h!=null&&h.detected_issue?e.jsx("div",{className:"text-xs text-muted-foreground mt-1 truncate",children:h.detected_issue}):e.jsx("div",{className:"text-xs text-muted-foreground mt-1",children:h!=null&&h.last_checked_at?`Checked ${new Date(h.last_checked_at).toLocaleTimeString()}`:"Not yet checked"}),(h==null?void 0:h.repair_action)&&e.jsx("div",{className:"text-xs mt-1",children:h.repair_action})]}),e.jsx("div",{className:"ml-2 shrink-0",children:h?Gr(h.status,h.severity):e.jsx(P,{variant:"outline",children:"—"})})]},g)})}),e.jsxs("div",{children:[e.jsxs("div",{className:"flex items-center gap-2 text-sm font-medium mb-2",children:[e.jsx(je,{className:"h-4 w-4"})," Recent heal activity"]}),e.jsxs("div",{className:"space-y-1 max-h-64 overflow-y-auto text-xs",children:[s.length===0&&e.jsx("div",{className:"text-muted-foreground",children:"No heal events yet."}),s.map(g=>e.jsxs("div",{className:"flex items-start justify-between gap-2 border-b pb-1",children:[e.jsxs("div",{className:"min-w-0",children:[e.jsx("span",{className:"font-mono text-[10px] text-muted-foreground mr-2",children:new Date(g.last_checked_at).toLocaleTimeString()}),e.jsx("span",{className:"font-medium",children:Wr[g.domain]??g.domain}),e.jsxs("span",{className:"text-muted-foreground",children:[" · ",g.check_key]}),g.detected_issue&&e.jsx("div",{className:"text-muted-foreground truncate",children:g.detected_issue}),g.repair_action&&e.jsx("div",{children:g.repair_action})]}),e.jsx("div",{className:"shrink-0",children:Gr(g.status,g.severity)})]},g.id))]})]})]})]})}const _t={green:"bg-emerald-500",yellow:"bg-amber-500",red:"bg-rose-500",gray:"bg-muted-foreground/40"},hs={green:"text-emerald-700 dark:text-emerald-300",yellow:"text-amber-700 dark:text-amber-300",red:"text-rose-700 dark:text-rose-300",gray:"text-muted-foreground"};function He({light:r,label:t}){const s=(r==null?void 0:r.status)??"gray",o=r!=null&&r.evidence_at?new Date(r.evidence_at).toLocaleString():null,i=(r==null?void 0:r.reason)??(r==null?void 0:r.url)??(r==null?void 0:r.path)??(r==null?void 0:r.source_id)??null,n=[`${t}: ${s}`,o?`evidence: ${o}`:null,i?`source: ${i}`:null].filter(Boolean).join(" · ");return e.jsxs("span",{className:"inline-flex items-center gap-1.5",title:n,children:[e.jsx("span",{className:`h-2.5 w-2.5 rounded-full ${_t[s]}`}),e.jsx("span",{className:`text-[11px] ${hs[s]}`,children:t})]})}function fs(){var h,k;const[r,t]=w.useState(null),[s,o]=w.useState([]),[i,n]=w.useState(!1),[c,d]=w.useState(null);async function l(){const[{data:v},{data:y}]=await Promise.all([C.from("operational_lights_v1").select("*").maybeSingle(),C.from("publishing_pipeline_lights").select("*").order("created_at",{ascending:!1}).limit(10)]);t(v??null),o(y??[])}w.useEffect(()=>{l();const v=setInterval(l,3e4);return()=>clearInterval(v)},[]);async function m(){n(!0),d(null);const{data:v,error:y}=await C.functions.invoke("media-waiting-dispatcher",{body:{max_jobs:1}});if(n(!1),y){d(`Dispatcher error: ${y.message}`);return}d(`Dispatcher ran: ${(v==null?void 0:v.dispatched)??0} job(s) dispatched (single proof run).`),l()}if(!r)return null;const f=((h=r.light_overall)==null?void 0:h.status)??"gray",g=r.last_heartbeat_at?en(new Date(r.last_heartbeat_at),{addSuffix:!0}):"never";return e.jsxs(W,{children:[e.jsxs(vr,{className:"flex flex-row items-center justify-between space-y-0 pb-2",children:[e.jsx(yr,{className:"text-base",children:"Publishing trunk · evidence-backed"}),e.jsx(P,{className:f==="green"?"bg-emerald-600 text-white":f==="yellow"?"bg-amber-500 text-white":f==="red"?"bg-rose-600 text-white":"bg-muted text-muted-foreground",children:f.toUpperCase()})]}),e.jsxs(br,{className:"space-y-3 text-sm",children:[e.jsxs("div",{className:"flex flex-wrap gap-4",children:[e.jsx(He,{light:r.light_ground_zero,label:`Ground Zero (${g})`}),e.jsx(He,{light:r.light_dispatch,label:`Dispatch ${r.claimed_green}/${r.jobs_in_window}`}),e.jsx(He,{light:r.light_browser,label:`Browser reached ${r.publisher_green}`}),e.jsx(He,{light:r.light_publishing,label:`Verified ${r.verified_green} (url-only ${r.url_green})`})]}),e.jsx("div",{className:"text-[11px] text-muted-foreground border-l-2 border-muted pl-2",children:(k=r.light_overall)==null?void 0:k.rule}),s.length>0&&e.jsxs("div",{className:"mt-2 space-y-1.5",children:[e.jsx("div",{className:"text-[10px] uppercase tracking-widest text-muted-foreground",children:"Per-job pipeline (last 10)"}),e.jsx("div",{className:"overflow-x-auto",children:e.jsxs("table",{className:"w-full text-[11px]",children:[e.jsx("thead",{children:e.jsxs("tr",{className:"text-muted-foreground",children:[e.jsx("th",{className:"text-left pr-2 pb-1",children:"job"}),e.jsx("th",{className:"pb-1",children:"create"}),e.jsx("th",{className:"pb-1",children:"claim"}),e.jsx("th",{className:"pb-1",children:"browser"}),e.jsx("th",{className:"pb-1",children:"click"}),e.jsx("th",{className:"pb-1",children:"url"}),e.jsx("th",{className:"pb-1",children:"shot"}),e.jsx("th",{className:"pb-1",children:"verified"}),e.jsx("th",{className:"pb-1 text-left pl-2",children:"note"})]})}),e.jsx("tbody",{children:s.map(v=>{var L,S;const y=v.error||v.last_dispatch_error||((L=v.light_publisher_reached)==null?void 0:L.reason)||((S=v.light_claimed)==null?void 0:S.reason)||v.status;return e.jsxs("tr",{className:"border-t border-muted/40",children:[e.jsxs("td",{className:"pr-2 py-1 font-mono",children:[v.job_id.slice(0,8),"·",v.platform]}),[v.light_created,v.light_claimed,v.light_publisher_reached,v.light_post_clicked,v.light_url_returned,v.light_screenshot,v.light_verified].map((u,x)=>{const N=(u==null?void 0:u.status)??"gray",j=u!=null&&u.evidence_at?new Date(u.evidence_at).toLocaleString():null,R=(u==null?void 0:u.reason)??(u==null?void 0:u.url)??(u==null?void 0:u.path)??(u==null?void 0:u.source_id)??"";return e.jsx("td",{className:"text-center py-1",title:`${N}${j?` · ${j}`:""}${R?` · ${R}`:""}`,children:e.jsx("span",{className:`inline-block h-2 w-2 rounded-full ${_t[N]}`})},x)}),e.jsx("td",{className:"pl-2 py-1 text-muted-foreground truncate max-w-[240px]",title:y??"",children:y})]},v.job_id)})})]})})]}),e.jsxs("div",{className:"flex items-center gap-2 pt-2",children:[e.jsx(E,{size:"sm",variant:"outline",onClick:m,disabled:i,children:i?"Running…":"Run dispatcher (1 job)"}),e.jsx("span",{className:"text-[11px] text-muted-foreground",children:"Cron: every 1 min. Manual run claims one job only (no burst)."})]}),c&&e.jsx("div",{className:"text-xs text-muted-foreground",children:c})]})]})}const qr="unk_remote_access_prefs_v1",Hr={provider:"quick_assist",anydesk_id:"",teamviewer_id:"",rustdesk_id:""};function gs(){const{toast:r}=Ce(),[t,s]=w.useState(Hr);w.useEffect(()=>{try{const n=localStorage.getItem(qr);n&&s({...Hr,...JSON.parse(n)})}catch{}},[]);const o=n=>{s(n);try{localStorage.setItem(qr,JSON.stringify(n))}catch{}},i=async(n,c)=>{try{await navigator.clipboard.writeText(n),r({title:`${c} copied`})}catch{r({title:"Copy failed",variant:"destructive"})}};return e.jsxs(W,{className:"p-4 space-y-4",children:[e.jsxs("div",{className:"flex items-start gap-3",children:[e.jsx("div",{className:"rounded-md bg-primary/10 p-2",children:e.jsx(mr,{className:"h-5 w-5 text-primary"})}),e.jsxs("div",{className:"flex-1",children:[e.jsxs("div",{className:"flex items-center gap-2 flex-wrap",children:[e.jsx("h3",{className:"font-semibold",children:"Remote into Ground Zero from your phone"}),e.jsxs(P,{variant:"secondary",className:"gap-1",children:[e.jsx(ee,{className:"h-3 w-3"})," Recommended"]})]}),e.jsx("p",{className:"text-sm text-muted-foreground mt-1",children:"When Meta shows a 2FA prompt, permission dialog, or login checkpoint, open your desktop from your phone and approve it live. Uses a trusted remote-desktop app — no custom streaming to break."}),e.jsxs("div",{className:"mt-2 flex items-start gap-2 rounded-md border border-amber-500/30 bg-amber-500/10 p-2 text-xs",children:[e.jsx(ie,{className:"h-4 w-4 text-amber-600 flex-shrink-0 mt-0.5"}),e.jsxs("span",{children:[e.jsx("b",{children:"Network blocks Google?"})," Chrome Remote Desktop needs"," ",e.jsx("code",{children:"remotedesktop.google.com"}),". Use ",e.jsx("b",{children:"Quick Assist"})," (built into Windows, Microsoft domains only) or ",e.jsx("b",{children:"RustDesk"})," (open source, own relays / self-hostable) instead."]})]})]})]}),e.jsxs("div",{className:"grid gap-3 md:grid-cols-3 lg:grid-cols-5",children:[e.jsx(we,{active:t.provider==="quick_assist",onSelect:()=>o({...t,provider:"quick_assist"}),title:"Quick Assist",subtitle:"Built into Windows · no install"}),e.jsx(we,{active:t.provider==="rustdesk",onSelect:()=>o({...t,provider:"rustdesk"}),title:"RustDesk",subtitle:"Open source · self-hostable"}),e.jsx(we,{active:t.provider==="chrome_remote_desktop",onSelect:()=>o({...t,provider:"chrome_remote_desktop"}),title:"Chrome Remote Desktop",subtitle:"Google account · may be blocked"}),e.jsx(we,{active:t.provider==="anydesk",onSelect:()=>o({...t,provider:"anydesk"}),title:"AnyDesk",subtitle:"Free personal · fast"}),e.jsx(we,{active:t.provider==="teamviewer",onSelect:()=>o({...t,provider:"teamviewer"}),title:"TeamViewer",subtitle:"Free personal"})]}),t.provider==="quick_assist"&&e.jsxs("div",{className:"rounded-md border p-3 space-y-3 text-sm",children:[e.jsx("p",{className:"text-muted-foreground",children:"Quick Assist is built into Windows 10/11 and uses Microsoft's own servers — it works on most networks that block Google Remote Desktop. No install on the desktop. You do need the Quick Assist / Remote Help app or a web browser on your phone signed into a Microsoft account."}),e.jsxs("ol",{className:"list-decimal ml-4 space-y-1 text-muted-foreground",children:[e.jsxs("li",{children:["On your ",e.jsx("b",{children:"phone"}),", open Quick Assist (install from the Microsoft Store on Android; on iOS use the Remote Help web flow below), sign in with a Microsoft account, tap ",e.jsx("b",{children:"Help someone"}),", and copy the 6-digit security code."]}),e.jsxs("li",{children:["On ",e.jsx("b",{children:"Ground Zero"}),", press ",e.jsx("kbd",{children:"Ctrl + Windows + Q"}),' (or search "Quick Assist" in Start), click ',e.jsx("b",{children:"Get help"}),", and paste the code."]}),e.jsx("li",{children:"Approve the connection on Ground Zero, then approve the Meta prompt from your phone."})]}),e.jsxs("div",{className:"flex gap-2 flex-wrap",children:[e.jsx(E,{asChild:!0,size:"sm",children:e.jsx("a",{href:"ms-quick-assist:",rel:"noreferrer",children:"Open Quick Assist on this device"})}),e.jsx(E,{asChild:!0,size:"sm",variant:"secondary",children:e.jsxs("a",{href:"https://apps.microsoft.com/detail/9p7bp5vnwkx5",target:"_blank",rel:"noreferrer",children:["Get Quick Assist (Windows Store) ",e.jsx(_e,{className:"h-3 w-3 ml-1"})]})}),e.jsx(E,{asChild:!0,size:"sm",variant:"secondary",children:e.jsxs("a",{href:"https://play.google.com/store/apps/details?id=com.microsoft.rdc.androidx",target:"_blank",rel:"noreferrer",children:["Android: Windows App ",e.jsx(_e,{className:"h-3 w-3 ml-1"})]})}),e.jsx(E,{asChild:!0,size:"sm",variant:"secondary",children:e.jsxs("a",{href:"https://apps.apple.com/app/windows-app-mobile/id714464092",target:"_blank",rel:"noreferrer",children:["iOS: Windows App ",e.jsx(_e,{className:"h-3 w-3 ml-1"})]})})]}),e.jsx("p",{className:"text-xs text-muted-foreground",children:"Quick Assist sessions are one-time. For always-on access without a code, pick RustDesk or AnyDesk."})]}),t.provider==="rustdesk"&&e.jsxs("div",{className:"rounded-md border p-3 space-y-3 text-sm",children:[e.jsx("p",{className:"text-muted-foreground",children:"RustDesk is open source, works peer-to-peer, and — critically — you can point it at your own relay server, so it survives networks that block commercial remote-desktop vendors. Free forever, no account required."}),e.jsxs("ol",{className:"list-decimal ml-4 space-y-1 text-muted-foreground",children:[e.jsxs("li",{children:["Install RustDesk on Ground Zero and set a strong ",e.jsx("b",{children:"permanent password"})," in Settings → Security."]}),e.jsx("li",{children:"Copy the 9-digit RustDesk ID shown on the main screen and paste it below."}),e.jsx("li",{children:"Install RustDesk on your phone, enter the ID + password, approve Meta prompts live."}),e.jsx("li",{children:"Optional: if the default public relays are blocked too, self-host a relay (docs link below) and set it in both clients."})]}),e.jsxs("div",{className:"space-y-1",children:[e.jsx(z,{htmlFor:"rustdesk_id",children:"Ground Zero RustDesk ID"}),e.jsxs("div",{className:"flex gap-2",children:[e.jsx(te,{id:"rustdesk_id",inputMode:"numeric",placeholder:"123 456 789",value:t.rustdesk_id,onChange:n=>o({...t,rustdesk_id:n.target.value})}),e.jsx(E,{variant:"secondary",onClick:()=>i(t.rustdesk_id,"RustDesk ID"),disabled:!t.rustdesk_id,children:e.jsx(he,{className:"h-4 w-4"})})]})]}),e.jsxs("div",{className:"flex gap-2 flex-wrap",children:[e.jsx(E,{asChild:!0,size:"sm",children:e.jsxs("a",{href:"https://rustdesk.com/download",target:"_blank",rel:"noreferrer",children:["Download RustDesk ",e.jsx(_e,{className:"h-3 w-3 ml-1"})]})}),e.jsx(E,{asChild:!0,size:"sm",variant:"outline",children:e.jsxs("a",{href:"https://rustdesk.com/docs/en/self-host/",target:"_blank",rel:"noreferrer",children:["Self-host relay ",e.jsx(_e,{className:"h-3 w-3 ml-1"})]})})]})]}),t.provider==="chrome_remote_desktop"&&e.jsxs("div",{className:"rounded-md border p-3 space-y-3 text-sm",children:[e.jsxs("p",{className:"text-muted-foreground",children:["The ",e.jsx("code",{children:"/access"})," page only lists computers you have already set up as a host. First time? Use ",e.jsx("b",{children:"Set up"})," below to install the host on Ground Zero, or use"," ",e.jsx("b",{children:"Quick Share"})," for a one-time session with an access code (no install needed). If ",e.jsx("code",{children:"remotedesktop.google.com"})," is blocked on your network, switch to Quick Assist or RustDesk above."]}),e.jsxs("ol",{className:"list-decimal ml-4 space-y-1 text-muted-foreground",children:[e.jsxs("li",{children:["On Ground Zero (Windows), open the ",e.jsx("b",{children:"Set up"})," link below in Chrome, click ",e.jsx("b",{children:"Turn on"}),' under "Set up remote access", download the installer, and set a PIN.']}),e.jsxs("li",{children:["Install ",e.jsx("b",{children:"Chrome Remote Desktop"})," from the App Store / Play Store on your phone. Sign in with the same Google account."]}),e.jsxs("li",{children:["After setup, Ground Zero appears on the ",e.jsx("b",{children:"Access"})," page and in the phone app. Tap it, enter the PIN, approve Meta prompts live."]}),e.jsxs("li",{children:["No time to set up the host? Open ",e.jsx("b",{children:"Quick Share"})," on Ground Zero, generate a one-time code, then enter it on your phone at the same page."]})]}),e.jsxs("div",{className:"flex gap-2 flex-wrap",children:[e.jsx(E,{asChild:!0,size:"sm",children:e.jsxs("a",{href:"https://remotedesktop.google.com/home",target:"_blank",rel:"noreferrer",children:["Set up (first time) ",e.jsx(_e,{className:"h-3 w-3 ml-1"})]})}),e.jsx(E,{asChild:!0,size:"sm",variant:"secondary",children:e.jsxs("a",{href:"https://remotedesktop.google.com/access",target:"_blank",rel:"noreferrer",children:["Access my computers ",e.jsx(_e,{className:"h-3 w-3 ml-1"})]})}),e.jsx(E,{asChild:!0,size:"sm",variant:"secondary",children:e.jsxs("a",{href:"https://remotedesktop.google.com/support",target:"_blank",rel:"noreferrer",children:["Quick Share (one-time code) ",e.jsx(_e,{className:"h-3 w-3 ml-1"})]})}),e.jsx(E,{asChild:!0,size:"sm",variant:"outline",children:e.jsx("a",{href:"https://apps.apple.com/app/chrome-remote-desktop/id944025852",target:"_blank",rel:"noreferrer",children:"iOS app"})}),e.jsx(E,{asChild:!0,size:"sm",variant:"outline",children:e.jsx("a",{href:"https://play.google.com/store/apps/details?id=com.google.chromeremotedesktop",target:"_blank",rel:"noreferrer",children:"Android app"})})]})]}),t.provider==="anydesk"&&e.jsxs("div",{className:"rounded-md border p-3 space-y-3 text-sm",children:[e.jsxs("ol",{className:"list-decimal ml-4 space-y-1 text-muted-foreground",children:[e.jsxs("li",{children:["Install AnyDesk on Ground Zero (Windows) and set ",e.jsx("b",{children:"Unattended access"})," with a password."]}),e.jsx("li",{children:"Copy the 9-digit AnyDesk ID shown on the desktop app and paste it below."}),e.jsx("li",{children:"Install AnyDesk on your phone, then use the button below to open the session directly."})]}),e.jsxs("div",{className:"space-y-1",children:[e.jsx(z,{htmlFor:"anydesk_id",children:"Ground Zero AnyDesk ID"}),e.jsxs("div",{className:"flex gap-2",children:[e.jsx(te,{id:"anydesk_id",inputMode:"numeric",placeholder:"123 456 789",value:t.anydesk_id,onChange:n=>o({...t,anydesk_id:n.target.value})}),e.jsx(E,{variant:"secondary",onClick:()=>i(t.anydesk_id,"AnyDesk ID"),disabled:!t.anydesk_id,children:e.jsx(he,{className:"h-4 w-4"})})]})]}),e.jsxs("div",{className:"flex gap-2 flex-wrap",children:[e.jsx(E,{asChild:!0,size:"sm",disabled:!t.anydesk_id,children:e.jsx("a",{href:`anydesk:${t.anydesk_id.replace(/\s+/g,"")}`,children:"Connect from this phone"})}),e.jsx(E,{asChild:!0,size:"sm",variant:"outline",children:e.jsx("a",{href:"https://anydesk.com/en/downloads",target:"_blank",rel:"noreferrer",children:"Downloads"})})]})]}),t.provider==="teamviewer"&&e.jsxs("div",{className:"rounded-md border p-3 space-y-3 text-sm",children:[e.jsxs("ol",{className:"list-decimal ml-4 space-y-1 text-muted-foreground",children:[e.jsxs("li",{children:["Install TeamViewer on Ground Zero and enable ",e.jsx("b",{children:"Easy access"})," so you don't have to approve every connect."]}),e.jsx("li",{children:"Copy your TeamViewer ID and paste it below."}),e.jsx("li",{children:"Install TeamViewer on your phone. Use the button below to launch the session."})]}),e.jsxs("div",{className:"space-y-1",children:[e.jsx(z,{htmlFor:"tv_id",children:"Ground Zero TeamViewer ID"}),e.jsxs("div",{className:"flex gap-2",children:[e.jsx(te,{id:"tv_id",inputMode:"numeric",placeholder:"1 234 567 890",value:t.teamviewer_id,onChange:n=>o({...t,teamviewer_id:n.target.value})}),e.jsx(E,{variant:"secondary",onClick:()=>i(t.teamviewer_id,"TeamViewer ID"),disabled:!t.teamviewer_id,children:e.jsx(he,{className:"h-4 w-4"})})]})]}),e.jsxs("div",{className:"flex gap-2 flex-wrap",children:[e.jsx(E,{asChild:!0,size:"sm",disabled:!t.teamviewer_id,children:e.jsx("a",{href:`teamviewer8://remotecontrol?device=${t.teamviewer_id.replace(/\s+/g,"")}`,children:"Connect from this phone"})}),e.jsx(E,{asChild:!0,size:"sm",variant:"outline",children:e.jsx("a",{href:"https://www.teamviewer.com/en-us/download/",target:"_blank",rel:"noreferrer",children:"Downloads"})})]})]}),e.jsx("p",{className:"text-xs text-muted-foreground",children:"Tip: keep the remote-desktop host running on Ground Zero at all times. When Unk needs a human for Meta 2FA or permissions, the /approvals push will tap your phone — open the remote app and approve it in seconds."})]})}function we({active:r,onSelect:t,title:s,subtitle:o}){return e.jsxs("button",{type:"button",onClick:t,className:`text-left rounded-md border p-3 transition ${r?"border-primary bg-primary/5":"hover:border-muted-foreground/40"}`,children:[e.jsx("div",{className:"font-medium text-sm",children:s}),e.jsx("div",{className:"text-xs text-muted-foreground",children:o})]})}const Te="https://kwbegsybeyyxfmavjswv.supabase.co/functions/v1/companion-package?build=latest",mt=`${Te}&meta=1`,ht=/^[0-9a-f]{64}$/i;function xs(r){if(!ht.test(r))throw new Error(`Invalid companion package SHA256: ${r}`);return`${Te}&sha=${r.toLowerCase()}`}async function vs(){const r=await fetch(mt,{cache:"no-store",headers:{"Cache-Control":"no-store",Pragma:"no-cache"}});if(!r.ok)throw new Error(`companion-package metadata failed [${r.status}]: ${await r.text()}`);const t=await r.json(),s=String((t==null?void 0:t.sha256)??"").trim().toLowerCase();if(!ht.test(s))throw new Error("companion-package metadata returned no valid 64-hex sha256 — refusing to update.");return{build:String((t==null?void 0:t.build)??"latest"),bytes:Number((t==null?void 0:t.bytes)??0),sha256:s,buildUrl:xs(s)}}function Kr(r){return`$m=Invoke-RestMethod -UseBasicParsing -Uri '${mt}' -Headers @{'Cache-Control'='no-store'};$sha=("" + $m.sha256).Trim().ToLower();if($sha -notmatch '^[0-9a-f]{64}$'){throw 'companion-package metadata returned no valid sha256'};$u='${Te}&sha=' + $sha;Invoke-WebRequest -UseBasicParsing -Uri $u -OutFile ${r} -Headers @{'Cache-Control'='no-store'};$local=(Get-FileHash ${r} -Algorithm SHA256).Hash.ToLower();if($local -ne $sha){throw "SHA256 mismatch: expected $sha got $local"};`}const ys=`Unk Connector Escort — Google Drive

Goal: add/link a SECOND Google Drive connection for jason@blackarchives.org.

1. In Lovable, open the workspace-level Connectors area.
2. Search/select Google Drive — not Gmail, Calendar, Docs, or general Google.
3. Choose + Add connection / Connect another account.
4. On Google, choose Use another account and sign in as jason@blackarchives.org.
5. Keep Drive read permission selected and approve.
6. Return to Lovable and finish linking the new connection to this project.
7. Tell Lovable chat: "I did it" so the agent can verify another google_drive row.

If you only see Gmail or Calendar afterward, repeat under Google Drive.`,de=C,pe=r=>r!==null&&typeof r=="object"&&!Array.isArray(r)?r:{},bs=90*1e3,zr=r=>r.status==="active"&&!!r.last_heartbeat_at&&Date.now()-new Date(r.last_heartbeat_at).getTime()<bs,ue=r=>r?new Date(r).toLocaleString():"—",Gs=()=>{Gt({title:"Desktop Command Center — Living OS",description:"Enroll, monitor, and command the J. Fortitude desktop companion under your existing trust + approval model.",path:"/grant-engine/desktop-command",image:"/placeholder.svg"});const{toast:r}=Ce(),[t,s]=w.useState([]),[o,i]=w.useState([]),[n,c]=w.useState([]),[d,l]=w.useState([]),[m,f]=w.useState({}),[g,h]=w.useState({}),[k,v]=w.useState(!1),[y,L]=w.useState(null),[S,u]=w.useState(""),[x,N]=w.useState(!1),[j,R]=w.useState(null),[T,B]=w.useState(0),[K,J]=w.useState(!1),[U,p]=w.useState(!1),[_,$]=w.useState(!1),[I,M]=w.useState(null),[Z,ne]=w.useState(!1),Y=async()=>{v(!0);const[a,b,O,D,F,G]=await Promise.all([C.from("desktop_devices").select("*").order("created_at",{ascending:!1}),C.from("desktop_action_requests").select("id, capability, action_type, intent_summary, risk_level, status, created_at").in("status",["approved","auto_approved"]).is("executed_at",null).or(`expires_at.is.null,expires_at.gt.${new Date().toISOString()}`).order("created_at",{ascending:!1}).limit(20),de.from("desktop_action_templates").select("*").eq("enabled",!0).order("sort_order",{ascending:!0}),de.from("desktop_action_audit_log").select("id, created_at, event_type, capability, action_type, template_slug, risk_level, actor, user_id, note, action_request_id").order("created_at",{ascending:!1}).limit(50),de.from("mobile_push_subscriptions").select("device_id, last_seen_at, last_notified_at, last_error").is("revoked_at",null),de.from("desktop_supervisor_events").select("device_id, event_kind, message, created_at").order("created_at",{ascending:!1}).limit(500)]);s(a.data??[]),i(b.data??[]),c(O.data??[]),l(D.data??[]),f(Object.fromEntries((F.data??[]).filter(H=>H.device_id).map(H=>[H.device_id,{last_seen_at:H.last_seen_at,last_notified_at:H.last_notified_at,last_error:H.last_error}])));const V={};for(const H of G.data??[])!H.device_id||V[H.device_id]||(V[H.device_id]={event_kind:H.event_kind,message:H.message,created_at:H.created_at});h(V),v(!1);const q=new Date(Date.now()-24*60*60*1e3).toISOString(),{count:A}=await C.from("desktop_action_requests").select("id",{count:"exact",head:!0}).eq("status","failed").eq("failure_reason","facebook_login_required_in_browser_profile").gte("created_at",q);B(A??0)},ft=async()=>{J(!0);try{const{data:a,error:b}=await C.functions.invoke("stv-retry-login-blocked",{body:{open_signin:!0}});if(b)throw b;r({title:"Sign-in launched",description:String(pe(a).message??"Unk is opening Business Suite in his browser. Sign in, then click 'Retry login-blocked jobs'.")}),Y()}catch(a){r({title:"Sign-in launch failed",description:String((a==null?void 0:a.message)??a),variant:"destructive"})}finally{J(!1)}},gt=async()=>{p(!0);try{const{data:a,error:b}=await C.functions.invoke("stv-retry-login-blocked",{body:{}});if(b)throw b;const O=Number(pe(a).requeued_count??0);r({title:O>0?`Re-queued ${O} job(s)`:"Nothing to retry",description:O>0?"Unk will publish them on the next sweep.":"No login-blocked jobs in the last 24h."}),Y()}catch(a){r({title:"Retry failed",description:String((a==null?void 0:a.message)??a),variant:"destructive"})}finally{p(!1)}},xt=async()=>{var a;$(!0);try{const{data:b}=await C.auth.getUser(),O=(a=b.user)==null?void 0:a.id;if(!O)throw new Error("Not signed in.");const D=new Date().toISOString(),F=new Date(Date.now()+60*60*1e3).toISOString(),{error:G}=await de.from("desktop_action_requests").insert({user_id:O,capability:"browser_release_locks",action_type:"browser_release_locks",intent_summary:"Force-close all Unk/Playwright Facebook browser windows",payload:{reason:"manual_pre_retry"},risk_level:"low",status:"approved",requested_by:"lovable",approved_at:D,approved_by:O,expires_at:F});if(G)throw G;r({title:"Force-close queued",description:"Unk will kill any Playwright Chromium windows using his browser profile on the next heartbeat (~15s)."}),setTimeout(()=>void Y(),3e3)}catch(b){r({title:"Force-close failed to queue",description:String((b==null?void 0:b.message)??b),variant:"destructive"})}finally{$(!1)}},vt=async a=>{const b=a.device_name||a.hostname||"Ground Zero";if(confirm(`Ask the installed Ground Zero supervisor to restart the local companion process on ${b}?

This does not mark the update verified. It must return a process-start receipt and a fresh heartbeat first.`)){M(a.id);try{const{data:O,error:D}=await de.rpc("request_ground_zero_process_start",{_device_id:a.id,_mode:"restart"});if(D)throw D;r({title:"Start/restart requested",description:String(pe(O).message??"Waiting for the installed supervisor to return process, log, and heartbeat receipts.")}),await Y()}catch(O){r({title:"Recovery request failed",description:String((O==null?void 0:O.message)??O),variant:"destructive"})}finally{M(null)}}};w.useEffect(()=>{Y();const a=setInterval(Y,15e3);return()=>clearInterval(a)},[]);const yt=async()=>{const a=S.trim();if(!a){r({title:"Name required",description:"Give this desktop a friendly name first.",variant:"destructive"});return}N(!0);const b=4,O=F=>{const G=pe(F),V=pe(G.context),q=String(G.message??F??"").toLowerCase(),A=Number(G.status??V.status??0);return A&&A>=400&&A<500&&A!==408&&A!==429?!1:q.includes("failed to send a request")||q.includes("failed to fetch")||q.includes("networkerror")||q.includes("load failed")||q.includes("timeout")||q.includes("temporarily")||q.includes("unavailable")||q.includes("boot")||A===0||A===408||A===429||A>=500&&A<=599};let D=null;try{for(let F=1;F<=b;F++)try{const{data:G,error:V}=await C.functions.invoke("desktop-enroll-start",{body:{device_name:a}});if(V)throw V;F>1?r({title:"Enrollment code created",description:`Recovered after ${F} attempts. Run the companion and paste the code.`}):r({title:"Enrollment code created",description:"Run the companion on the desktop and paste this code."}),u(""),await Y();return}catch(G){if(D=G,F===b||!O(G))throw G;const V=Math.min(8e3,500*2**(F-1))+Math.floor(Math.random()*250);r({title:"Reconnecting…",description:`Edge function not ready (attempt ${F}/${b}). Retrying in ${Math.round(V/1e3)}s.`}),await new Promise(q=>setTimeout(q,V))}}catch(F){r({title:"Enrollment failed",description:`${String((F==null?void 0:F.message)??F)} — tried ${b} times. Please try again in a moment.`,variant:"destructive"})}finally{N(!1)}},bt=async a=>{if(!confirm("Revoke this device? The companion will lose access immediately."))return;const{error:b}=await C.from("desktop_devices").update({status:"revoked",revoked_at:new Date().toISOString(),revoked_reason:"manual"}).eq("id",a);if(b){r({title:"Revoke failed",description:b.message,variant:"destructive"});return}r({title:"Device revoked"}),Y()},kt=async a=>{if(!confirm("Delete this device record entirely?"))return;const{error:b}=await C.from("desktop_devices").delete().eq("id",a);if(b){r({title:"Delete failed",description:b.message,variant:"destructive"});return}Y()},[nr,$r]=w.useState(null),wt=async a=>{var D;const b=a.device_name||a.hostname||"this companion",O=a.last_heartbeat_at?(Date.now()-new Date(a.last_heartbeat_at).getTime())/6e4:1/0;if(O>5){r({title:"Cannot update — device offline",description:`Last heartbeat ${isFinite(O)?Math.round(O)+" min ago":"never"}. Wait for it to come back online before updating.`,variant:"destructive"});return}if(confirm(`Push the latest Companion build to ${b} and verify it comes back healthy?

Two-phase update: Unk will self-update, restart, ack a one-time token, then must produce 2 clean heartbeats within 5 minutes. If not, the platform auto-rolls back to the previous build and opens a critical governance signal.`)){$r(a.id);try{const{data:F}=await C.auth.getUser(),G=(D=F.user)==null?void 0:D.id;if(!G)throw new Error("Not signed in.");const V=new Date().toISOString(),q=new Date(Date.now()+60*60*1e3).toISOString(),A=await vs(),{data:H,error:X}=await C.functions.invoke("desktop-update-verify",{body:{action:"stage_update",device_id:a.id,requested_by:G,new_build_ref:A.buildUrl}});if(X)throw X;const Q=pe(H).token;if(typeof Q!="string"||!Q)throw new Error("desktop-update-verify did not return a token");const{error:Rr}=await C.from("desktop_action_requests").insert({user_id:G,capability:"self_update",action_type:"self_update",intent_summary:`Update companion on ${b} to build ${A.build} (${A.sha256.slice(0,12)}…, two-phase verify)`,payload:{zip_url:A.buildUrl,expect_zip_sha256:A.sha256,target_device_id:a.id,update_verification_token:Q},risk_level:"medium",status:"auto_approved",requested_by:"lovable",approved_at:V,expires_at:q});if(Rr)throw Rr;const{error:Tr}=await C.from("desktop_action_requests").insert({user_id:G,capability:"restart_companion",action_type:"restart_companion",intent_summary:`Restart companion on ${b} after self_update (two-phase verify)`,payload:{reason:"post_self_update",target_device_id:a.id},risk_level:"low",status:"auto_approved",requested_by:"lovable",approved_at:V,expires_at:q});if(Tr)throw Tr;r({title:"Update staged & verifying",description:`${b} will self-update, restart, and must post 2 clean heartbeats within 5 min or auto-rollback.`}),setTimeout(()=>void Y(),3e3)}catch(F){r({title:"Update failed to queue",description:String((F==null?void 0:F.message)??F),variant:"destructive"})}finally{$r(null)}}},Nt=a=>{const b=document.createElement("textarea");b.value=a,b.setAttribute("readonly",""),b.style.position="fixed",b.style.left="-9999px",b.style.top="0",document.body.appendChild(b),b.focus(),b.select(),b.setSelectionRange(0,a.length);const O=document.execCommand("copy");return b.remove(),O},sr=async(a,b)=>{try{await navigator.clipboard.writeText(a),r({title:`${b} copied`});return}catch{if(Nt(a)){r({title:`${b} copied`});return}window.prompt(`Copy this ${b.toLowerCase()} manually:`,a),r({title:"Copy manually",description:"A copy box opened with the text selected."})}},Ie=async a=>{try{const b=a==="unk_companion.py"?Hn:a==="install_supervisor.ps1"?Kn:a==="unk_keepalive.ps1"?zn:qn,O=new Blob([b],{type:a.endsWith(".py")?"text/x-python;charset=utf-8":a.endsWith(".ps1")?"text/x-powershell;charset=utf-8":"text/markdown;charset=utf-8"}),D=URL.createObjectURL(O),F=document.createElement("a");F.href=D,F.download=a,document.body.appendChild(F),F.click(),F.remove(),setTimeout(()=>URL.revokeObjectURL(D),1e3),r({title:"Download started",description:a})}catch(b){r({title:"Download failed",description:String((b==null?void 0:b.message)??b),variant:"destructive"})}},St=()=>{try{const a=["@echo off","REM Self-elevating installer for the full Unk supervisor package","net session >nul 2>&1","if %errorlevel% neq 0 (",`  powershell -Command "Start-Process '%~f0' -Verb RunAs"`,"  exit /b",")","echo Downloading and running full Unk supervisor package as admin...",`powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop';$d=Join-Path $env:TEMP ('unk-supervisor-' + [guid]::NewGuid());New-Item -ItemType Directory -Force $d|Out-Null;$z=Join-Path $d 'desktop-companion.zip';${Kr("$z")}Expand-Archive -Force $z $d;$i=Get-ChildItem $d -Recurse -Filter install_supervisor.ps1|Select-Object -First 1;if(!$i){throw 'install_supervisor.ps1 not found after unzip'};cd $i.DirectoryName;& powershell.exe -NoProfile -ExecutionPolicy Bypass -File $i.FullName"`,"echo.","echo Done. You can close this window.","pause",""].join(`\r
`),b=new Blob([a],{type:"application/octet-stream"}),O=URL.createObjectURL(b),D=document.createElement("a");D.href=O,D.download="Run_Supervisor_Installer_As_Admin.cmd",document.body.appendChild(D),D.click(),D.remove(),setTimeout(()=>URL.revokeObjectURL(O),1e3),r({title:"Admin runner downloaded",description:"Double-click Run_Supervisor_Installer_As_Admin.cmd, then click Yes on the UAC prompt."})}catch(a){r({title:"Download failed",description:String((a==null?void 0:a.message)??a),variant:"destructive"})}},Oe=a=>a==="calendar_create_event"||a==="email_draft",Et=async a=>{var D;const b=Oe(a.capability),O=b?`Run "${a.title}"?

This is a CLOUD action (${a.risk_level} risk). It runs server-side via the connector gateway — no desktop required.`:a.requires_approval?`Launch "${a.title}"?

This is ${a.risk_level.toUpperCase()} risk and requires admin approval before the companion executes it.`:`Launch "${a.title}"?

This ${a.risk_level} risk template is pre-approved and will run on the next heartbeat.`;if(confirm(O)){L(a.slug);try{const{data:F}=await C.auth.getUser(),G=(D=F.user)==null?void 0:D.id;if(!G)throw new Error("Not signed in.");if(b){const{data:H,error:X}=await C.functions.invoke("cloud-action-dispatch",{body:{capability:a.capability,template_slug:a.slug,intent_summary:a.title,risk_level:a.risk_level,payload:a.default_payload??{}}});if(X)throw X;const Q=pe(H).ok===!0;r({title:Q?"Cloud action complete":"Cloud action failed",description:Q?`${a.title} ran via ${String(pe(H).provider??"connector gateway")}.`:String(pe(H).error??"Unknown error"),variant:Q?void 0:"destructive"}),Y();return}const V=new Date().toISOString(),q=!a.requires_approval,{error:A}=await de.from("desktop_action_requests").insert({user_id:G,capability:a.capability,action_type:a.action_type,intent_summary:a.title,payload:{...a.default_payload??{},allowed_path:a.allowed_path,expected_artifact:a.expected_artifact,template_slug:a.slug},risk_level:a.risk_level,status:q?"approved":"pending",requested_by:"unk-template",approved_at:q?V:null,approved_by:q?G:null,template_slug:a.slug});if(A)throw A;r({title:q?"Action queued":"Approval requested",description:q?"Companion will pick this up on the next heartbeat.":"Approve it in Governance to release it to the companion."}),Y()}catch(F){r({title:"Launch failed",description:String((F==null?void 0:F.message)??F),variant:"destructive"})}finally{L(null)}}},$t=async()=>{var a;ne(!0);try{const{data:b}=await C.auth.getUser(),O=(a=b.user)==null?void 0:a.id;if(!O)throw new Error("Not signed in.");const D=new Date().toISOString(),F=new Date(Date.now()+60*60*1e3).toISOString(),G={user_id:O,risk_level:"low",status:"approved",requested_by:"connector-escort",approved_at:D,approved_by:O,expires_at:F},{error:V}=await de.from("desktop_action_requests").insert({...G,capability:"write_clipboard",action_type:"connector_checklist_clipboard",intent_summary:"Copy Google Drive connector checklist for Jason",payload:{text:ys},template_slug:"connector_escort_google_drive_blackarchives_clipboard"});if(V)throw V;const{error:q}=await de.from("desktop_action_requests").insert({...G,capability:"open_url",action_type:"connector_escort_open_lovable",intent_summary:"Open Lovable so Jason can reach workspace Connectors",payload:{url:"https://lovable.app"},template_slug:"connector_escort_google_drive_blackarchives_open"});if(q)throw q;r({title:"Unk escort queued",description:"Unk will copy the Drive checklist and open Lovable on the next heartbeat."}),Y()}catch(b){r({title:"Escort failed to queue",description:String((b==null?void 0:b.message)??b),variant:"destructive"})}finally{ne(!1)}},or=t.filter(a=>a.kind!=="mobile_approver"),jr=t.filter(a=>a.kind==="mobile_approver"),jt=or.filter(a=>a.status==="active").length,Fe=or.filter(zr).length,Rt=jr.filter(a=>a.status==="active").length,Tt=jr.filter(a=>{var b;return a.status==="active"&&m[a.id]&&!((b=m[a.id])!=null&&b.last_error)}).length;return e.jsxs("div",{className:"space-y-6 p-4 md:p-6 max-w-6xl mx-auto",children:[e.jsxs("header",{className:"space-y-2",children:[e.jsxs("div",{className:"flex items-center gap-2 text-sm text-muted-foreground",children:[e.jsx(mr,{className:"h-4 w-4"})," Desktop Companion · Phase 1"]}),e.jsx("h1",{className:"text-2xl md:text-3xl font-semibold",children:"Desktop Command Center"}),e.jsx("p",{className:"text-sm text-muted-foreground max-w-3xl",children:"Enroll Unk's hands on your Windows machine. Every action flows through the existing permission profiles, trust ledger, and approval gate — nothing executes that you (or an admin) haven't approved. Phase 2 will ship the companion script that pairs with the codes minted here."})]}),e.jsx(es,{}),e.jsx(ms,{}),e.jsx(fs,{}),e.jsx(ds,{}),e.jsx(ns,{}),e.jsx(as,{}),e.jsx(_s,{}),e.jsx(Yt,{}),e.jsx(Zt,{}),e.jsxs("div",{className:"grid grid-cols-2 md:grid-cols-4 gap-3",children:[e.jsxs(W,{className:"p-4",children:[e.jsx("div",{className:"text-xs text-muted-foreground",children:"Desktop companions"}),e.jsxs("div",{className:"text-2xl font-semibold",children:[jt,"/",or.length]})]}),e.jsxs(W,{className:"p-4",children:[e.jsx("div",{className:"text-xs text-muted-foreground",children:"Desktop online"}),e.jsx("div",{className:"text-2xl font-semibold text-emerald-600",children:Fe})]}),e.jsxs(W,{className:"p-4",children:[e.jsx("div",{className:"text-xs text-muted-foreground",children:"Phone approvers"}),e.jsxs("div",{className:"text-2xl font-semibold text-emerald-600",children:[Tt,"/",Rt]})]}),e.jsxs(W,{className:"p-4",children:[e.jsx("div",{className:"text-xs text-muted-foreground",children:"Pending actions"}),e.jsx("div",{className:"text-2xl font-semibold",children:o.length})]})]}),e.jsx(Kt,{}),e.jsxs(W,{className:"p-4 space-y-3",children:[e.jsxs("div",{className:"flex items-center gap-2 text-sm font-medium",children:[e.jsx(Yr,{className:"h-4 w-4"})," Enroll a new desktop"]}),e.jsx("p",{className:"text-xs text-muted-foreground",children:"Step 1: download the companion script onto the Windows PC. Step 2: give the desktop a name and create a one-time enrollment code (valid 15 minutes). Step 3: run the companion and paste the code. The companion receives a long-lived device key that's stored only on that machine."}),e.jsxs("div",{className:"flex flex-wrap gap-2",children:[e.jsx(E,{size:"sm",variant:"outline",onClick:()=>Ie("unk_companion.py"),children:"Download Python script"}),e.jsx(E,{size:"sm",variant:"outline",onClick:()=>Ie("install_supervisor.ps1"),children:"Download supervisor installer"}),e.jsx(E,{size:"sm",variant:"outline",onClick:()=>Ie("unk_keepalive.ps1"),children:"Download keepalive repair"}),e.jsx(E,{size:"sm",onClick:St,children:"Run installer as admin"}),e.jsx(E,{size:"sm",variant:"ghost",onClick:()=>Ie("README.md"),children:"Download README"})]}),e.jsxs("div",{className:"flex flex-col sm:flex-row gap-2",children:[e.jsxs("div",{className:"flex-1",children:[e.jsx(z,{htmlFor:"device-name",className:"sr-only",children:"Device name"}),e.jsx(te,{id:"device-name",placeholder:"e.g. Jason's Windows desktop",value:S,onChange:a=>u(a.target.value)})]}),e.jsx(E,{onClick:yt,disabled:x,children:x?"Creating…":"Create enrollment code"})]})]}),e.jsx(Gn,{onEnrolled:()=>void Y()}),e.jsx(gs,{}),j&&e.jsxs(W,{className:"p-4 border-amber-500/50 bg-amber-500/5 space-y-2",children:[e.jsxs("div",{className:"flex items-center gap-2 text-sm font-medium text-amber-700",children:[e.jsx(Be,{className:"h-4 w-4"})," Device key (shown once)"]}),e.jsx("p",{className:"text-xs text-muted-foreground",children:"Save this in the companion's config. It will not be shown again."}),e.jsx("code",{className:"block text-xs bg-background border rounded p-2 break-all",children:j.device_key}),e.jsxs(E,{size:"sm",variant:"outline",onClick:()=>sr(j.device_key,"Device key"),children:[e.jsx(he,{className:"h-3 w-3 mr-1"})," Copy"]}),e.jsx(E,{size:"sm",variant:"ghost",onClick:()=>R(null),children:"Dismiss"})]}),e.jsxs("section",{className:"space-y-3",children:[e.jsx("div",{className:"flex items-center justify-between flex-wrap gap-2",children:e.jsxs("div",{children:[e.jsxs("h2",{className:"text-lg font-semibold flex items-center gap-2",children:[e.jsx(Pr,{className:"h-4 w-4"})," Bot Action Templates"]}),e.jsx("p",{className:"text-xs text-muted-foreground",children:"One-tap prebuilt desktop requests. Low-risk templates auto-approve; high-risk wait for the approval gate."})]})}),e.jsx(W,{className:"p-3 space-y-3",children:e.jsxs("div",{className:"flex items-start justify-between gap-3 flex-wrap",children:[e.jsxs("div",{className:"space-y-1",children:[e.jsxs("div",{className:"text-sm font-medium flex items-center gap-2",children:[e.jsx(Be,{className:"h-4 w-4"})," Unk Connector Escort"]}),e.jsx("div",{className:"text-xs text-muted-foreground max-w-2xl",children:"Opens Lovable and puts the Google Drive connection checklist on the desktop clipboard for the human-only consent step."})]}),e.jsxs(E,{size:"sm",onClick:$t,disabled:Z||Fe===0,children:[e.jsx(ge,{className:"h-3 w-3 mr-1"}),Z?"Queuing…":"Have Unk guide it"]})]})}),n.length===0?e.jsx(W,{className:"p-4 text-sm text-muted-foreground",children:"No templates available."}):e.jsx("div",{className:"grid grid-cols-1 md:grid-cols-2 gap-3",children:n.map(a=>{const b=a.risk_level==="high"?"border-destructive/50 text-destructive":a.risk_level==="medium"?"border-amber-500/40 text-amber-700":"border-emerald-500/40 text-emerald-700";return e.jsxs(W,{className:"p-3 space-y-2",children:[e.jsxs("div",{className:"flex items-start justify-between gap-2",children:[e.jsxs("div",{className:"min-w-0",children:[e.jsx("div",{className:"text-sm font-medium truncate",children:a.title}),a.description&&e.jsx("div",{className:"text-xs text-muted-foreground line-clamp-2",children:a.description})]}),e.jsxs("div",{className:"flex flex-col items-end gap-1 shrink-0",children:[e.jsx(P,{variant:"outline",className:b,children:a.risk_level}),a.requires_approval&&e.jsxs(P,{variant:"outline",className:"border-muted-foreground/30 text-[10px]",children:[e.jsx(ee,{className:"h-3 w-3 mr-1"})," approval"]})]})]}),e.jsxs("div",{className:"grid grid-cols-2 gap-2 text-[11px] text-muted-foreground",children:[e.jsxs("div",{children:[e.jsx("span",{className:"font-medium text-foreground",children:"Capability:"})," ",a.capability]}),e.jsxs("div",{children:[e.jsx("span",{className:"font-medium text-foreground",children:"Action:"})," ",a.action_type]}),a.allowed_path&&e.jsxs("div",{className:"col-span-2 truncate",children:[e.jsx("span",{className:"font-medium text-foreground",children:"Path:"})," ",a.allowed_path]}),a.expected_artifact&&e.jsxs("div",{className:"col-span-2",children:[e.jsx("span",{className:"font-medium text-foreground",children:"Artifact:"})," ",a.expected_artifact]})]}),e.jsx("div",{className:"flex justify-end",children:e.jsxs(E,{size:"sm",onClick:()=>Et(a),disabled:y===a.slug||!Oe(a.capability)&&Fe===0,title:!Oe(a.capability)&&Fe===0?"No online device — companion offline.":void 0,children:[e.jsx(ge,{className:"h-3 w-3 mr-1"}),y===a.slug?"Launching…":Oe(a.capability)?"Run cloud":a.requires_approval?"Request":"Run"]})})]},a.id)})})]}),e.jsxs("section",{className:"space-y-3",children:[e.jsxs("div",{className:"flex items-center justify-between",children:[e.jsx("h2",{className:"text-lg font-semibold",children:"Devices"}),e.jsxs(E,{size:"sm",variant:"ghost",onClick:Y,disabled:k,children:[e.jsx(oe,{className:`h-3 w-3 mr-1 ${k?"animate-spin":""}`})," Refresh"]})]}),t.length===0&&e.jsx(W,{className:"p-6 text-sm text-muted-foreground text-center",children:"No devices enrolled yet. Create an enrollment code above to get started."}),t.map(a=>{var V,q;const b=a.kind==="mobile_approver",O=!b&&zr(a),D=b?m[a.id]:null,F=b&&a.status==="active"&&!!D&&!D.last_error,G=b?Jr:mr;return e.jsxs(W,{className:"p-4 space-y-3",children:[e.jsxs("div",{className:"flex items-start justify-between gap-3 flex-wrap",children:[e.jsxs("div",{children:[e.jsxs("div",{className:"font-medium flex items-center gap-2",children:[e.jsx(G,{className:"h-4 w-4"})," ",a.device_name]}),e.jsx("div",{className:"text-xs text-muted-foreground",children:b?`Phone approver · ${D?"push subscription active":"push subscription not found"}`:`${a.hostname??"—"} · ${a.os??"OS unknown"}`})]}),e.jsx("div",{className:"flex gap-2 flex-wrap",children:a.status==="active"?b?F?e.jsxs(P,{variant:"outline",className:"border-emerald-500/40 text-emerald-700",children:[e.jsx(Ir,{className:"h-3 w-3 mr-1"})," Approver ready"]}):e.jsxs(P,{variant:"outline",className:"border-amber-500/40 text-amber-700",children:[e.jsx(Ir,{className:"h-3 w-3 mr-1"})," Enrolled — push missing"]}):O?e.jsxs(P,{variant:"outline",className:"border-emerald-500/40 text-emerald-700",children:[e.jsx(je,{className:"h-3 w-3 mr-1"})," Online — running"]}):e.jsxs(P,{variant:"outline",className:"border-amber-500/40 text-amber-700",children:[e.jsx(je,{className:"h-3 w-3 mr-1"})," Enrolled — companion not running"]}):a.status==="pending"?e.jsx(P,{variant:"outline",className:"border-amber-500/40 text-amber-700",children:b?"Phone QR pending":"Pending pairing"}):e.jsx(P,{variant:"outline",className:"border-destructive/40 text-destructive",children:"Revoked"})})]}),a.status==="pending"&&a.enrollment_code&&e.jsxs("div",{className:"rounded border border-amber-500/40 bg-amber-500/5 p-3 space-y-2",children:[e.jsxs("div",{className:"text-xs text-amber-700 flex items-center gap-1",children:[e.jsx(Be,{className:"h-3 w-3"})," Enrollment code (paste in companion)"]}),e.jsxs("div",{className:"flex items-center gap-2",children:[e.jsx("code",{className:"text-lg font-mono tracking-widest bg-background border rounded px-2 py-1",children:a.enrollment_code}),e.jsx(E,{size:"sm",variant:"outline",onClick:()=>sr(a.enrollment_code,"Code"),children:e.jsx(he,{className:"h-3 w-3"})})]}),e.jsxs("div",{className:"text-[11px] text-muted-foreground",children:["Expires ",ue(a.enrollment_code_expires_at)]}),b?e.jsxs("div",{className:"text-[11px] text-amber-700/90 border-t border-amber-500/30 pt-2",children:[e.jsx("strong",{children:"Phone approver pending."})," Finish this from the phone QR/link flow. Phones do not send desktop heartbeats."]}):e.jsxs("div",{className:"text-[11px] text-amber-700/90 border-t border-amber-500/30 pt-2",children:[e.jsx("strong",{children:"Desktop only."})," This code is for the Windows/Mac",e.jsx("code",{className:"mx-1 px-1 bg-background border rounded",children:"unk_companion.py"}),"installer. A phone cannot check in here — phones won't run the companion. To turn a phone into an approver, use the ",e.jsx("em",{children:"Enroll a phone (approver)"}),"card above (QR code flow). If this row was meant for a phone, hit"," ",e.jsx("strong",{children:"Revoke"})," — it will never check in."]})]}),a.status==="active"&&b&&e.jsxs("div",{className:"grid grid-cols-2 md:grid-cols-4 gap-3 text-xs",children:[e.jsxs("div",{children:[e.jsx("div",{className:"text-muted-foreground",children:"Enrolled"}),e.jsx("div",{children:ue(a.enrolled_at)})]}),e.jsxs("div",{children:[e.jsx("div",{className:"text-muted-foreground",children:"Push verified"}),e.jsx("div",{children:ue((D==null?void 0:D.last_seen_at)??null)})]}),e.jsxs("div",{children:[e.jsx("div",{className:"text-muted-foreground",children:"Last notified"}),e.jsx("div",{children:ue((D==null?void 0:D.last_notified_at)??null)})]}),e.jsxs("div",{children:[e.jsx("div",{className:"text-muted-foreground",children:"Device ID"}),e.jsx("div",{className:"font-mono text-[10px] truncate",children:a.id})]}),(D==null?void 0:D.last_error)&&e.jsxs("div",{className:"col-span-2 md:col-span-4 text-amber-700",children:["Push diagnostic: ",D.last_error]})]}),a.status==="active"&&!b&&(()=>{const A=g[a.id],H=A?(Date.now()-new Date(A.created_at).getTime())/6e4:null;let X="Never reported",Q="text-muted-foreground";return A&&(A.event_kind==="escalation"?(X="Escalated",Q="text-red-600 font-medium"):A.event_kind==="supervisor_stopped"?(X="Stopped",Q="text-amber-700 font-medium"):A.event_kind==="process_start_requested"?(X="Start pending",Q="text-red-600 font-medium"):A.event_kind==="process_start_failed"?(X="Start failed",Q="text-red-600 font-medium"):["supervisor_online","supervisor_poll","process_start_receipt"].includes(A.event_kind)&&H!==null&&H<5?(X="Running",Q="text-emerald-700 font-medium"):A.event_kind==="manual_ping_requested"?(X="Ping pending",Q="text-red-600 font-medium"):(X=`Stale (${H!==null?Math.round(H):"?"}m ago)`,Q="text-amber-700")),e.jsxs(e.Fragment,{children:[e.jsxs("div",{className:"grid grid-cols-2 md:grid-cols-4 gap-3 text-xs",children:[e.jsxs("div",{children:[e.jsx("div",{className:"text-muted-foreground",children:"Enrolled"}),e.jsx("div",{children:ue(a.enrolled_at)})]}),e.jsxs("div",{children:[e.jsx("div",{className:"text-muted-foreground",children:"Last heartbeat"}),e.jsx("div",{children:ue(a.last_heartbeat_at)})]}),e.jsxs("div",{children:[e.jsx("div",{className:"text-muted-foreground",children:"Last IP"}),e.jsx("div",{children:a.last_ip??"—"})]}),e.jsxs("div",{children:[e.jsx("div",{className:"text-muted-foreground",children:"Device ID"}),e.jsx("div",{className:"font-mono text-[10px] truncate",children:a.id})]})]}),e.jsxs("div",{className:"mt-2 flex flex-wrap items-center gap-3 text-xs rounded border bg-muted/20 px-3 py-2",children:[e.jsxs("div",{children:[e.jsx("span",{className:"text-muted-foreground",children:"Supervisor: "}),e.jsx("span",{className:Q,children:X})]}),e.jsxs("div",{className:"text-muted-foreground",children:["Last event: ",A?ue(A.created_at):"—",A!=null&&A.event_kind?` · ${A.event_kind}`:""]}),(A==null?void 0:A.message)&&e.jsxs("div",{className:"text-muted-foreground truncate max-w-full md:max-w-[420px]",title:A.message,children:['"',A.message,'"']}),e.jsx(E,{size:"sm",variant:"outline",className:"h-6 px-2 text-[11px] ml-auto",onClick:()=>Y(),children:"Verify supervisor"}),e.jsxs(E,{size:"sm",variant:"secondary",className:"h-6 px-2 text-[11px]",onClick:()=>vt(a),disabled:I===a.id,title:"Ask the installed supervisor to kill/relaunch unk_companion.py and return process/log/heartbeat receipts.",children:[e.jsx(ge,{className:"h-3 w-3 mr-1"}),I===a.id?"Requesting…":"Start/Restart Ground Zero"]})]})]})})(),!b&&a.status==="active"&&e.jsx(us,{deviceId:a.id,runningVersion:typeof((V=a.last_status)==null?void 0:V.companion_version)=="string"?a.last_status.companion_version:null,runningBuildRef:typeof((q=a.last_status)==null?void 0:q.companion_build_ref)=="string"?a.last_status.companion_build_ref:null,lastHeartbeatAt:a.last_heartbeat_at,latestBuildUrl:Te}),a.status==="active"&&!b&&a.last_status&&Object.keys(a.last_status).length>0&&e.jsxs("details",{className:"text-xs",children:[e.jsx("summary",{className:"cursor-pointer text-muted-foreground",children:"Last reported status"}),e.jsx("pre",{className:"mt-2 bg-muted/40 rounded p-2 overflow-auto text-[11px]",children:JSON.stringify(a.last_status,null,2)})]}),!b&&a.status!=="revoked"&&(!O||a.status==="pending")&&(()=>{const A=a.enrollment_code??"PASTE_CODE_HERE",H='$ErrorActionPreference="Stop";$d="$HOME\\Downloads";$z="$d\\desktop-companion.zip";'+Kr("$z")+`Expand-Archive -Force $z $d;$s=Get-ChildItem $d -Recurse -Filter setup_unk.ps1|Select-Object -First 1;if(!$s){throw "setup_unk.ps1 not found after unzip"};cd $s.DirectoryName;powershell -ExecutionPolicy Bypass -File $s.FullName ${A}`;return e.jsxs("div",{className:"rounded border bg-muted/30 p-3 space-y-2",children:[e.jsxs("div",{className:"text-xs font-medium flex items-center gap-1",children:[e.jsx(Pr,{className:"h-3 w-3"})," One-command install (Windows PowerShell)"]}),e.jsxs("div",{className:"text-[11px] text-muted-foreground",children:["Downloads the zip, extracts to ",e.jsx("code",{children:"Downloads\\desktop-companion"}),', installs Python deps, and launches the companion — all in one paste. Open PowerShell (Start → "PowerShell") and paste:']}),e.jsxs("div",{className:"flex items-start gap-2",children:[e.jsx("pre",{className:"flex-1 text-[11px] bg-background border rounded p-2 overflow-x-auto whitespace-pre-wrap break-all",children:H}),e.jsx(E,{size:"sm",variant:"outline",onClick:()=>sr(H,"Command"),children:e.jsx(he,{className:"h-3 w-3"})})]}),!a.enrollment_code&&e.jsxs("div",{className:"text-[11px] text-amber-700",children:["No live enrollment code on this device — replace ",e.jsx("code",{children:"PASTE_CODE_HERE"})," with a fresh code from the enroll card above."]})]})})(),e.jsxs("div",{className:"flex gap-2 justify-end flex-wrap",children:[!b&&a.status!=="revoked"&&(!O||a.status==="pending")&&e.jsx(E,{size:"sm",variant:"secondary",asChild:!0,children:e.jsx("a",{href:Te,download:"desktop-companion.zip",children:"Download Companion (.zip)"})}),!b&&a.status==="active"&&O&&e.jsxs(E,{size:"sm",variant:"default",disabled:nr===a.id,onClick:()=>wt(a),title:"Push the latest ZIP to this companion and restart it",children:[e.jsx(oe,{className:`h-3 w-3 mr-1 ${nr===a.id?"animate-spin":""}`}),nr===a.id?"Queuing…":"Update & Restart"]}),a.status!=="revoked"&&e.jsxs(E,{size:"sm",variant:"outline",onClick:()=>bt(a.id),children:[e.jsx(ee,{className:"h-3 w-3 mr-1"})," Revoke"]}),e.jsxs(E,{size:"sm",variant:"ghost",onClick:()=>kt(a.id),children:[e.jsx(qt,{className:"h-3 w-3 mr-1"})," Delete"]})]}),!b&&a.status!=="pending"&&e.jsx("div",{className:"mt-3",children:e.jsx(Jn,{deviceId:a.id})})]},a.id)})]}),e.jsxs("section",{className:"space-y-3",children:[e.jsx("h2",{className:"text-lg font-semibold",children:"Approved actions waiting to execute"}),o.length===0?e.jsx(W,{className:"p-6 text-sm text-muted-foreground text-center",children:"No approved-but-unexecuted desktop actions. New actions appear here once approved through the existing gate."}):o.map(a=>e.jsxs(W,{className:"p-3 flex items-start justify-between gap-3",children:[e.jsxs("div",{className:"space-y-1",children:[e.jsx("div",{className:"text-sm font-medium",children:a.intent_summary??a.action_type}),e.jsxs("div",{className:"text-xs text-muted-foreground",children:[a.capability," · ",a.action_type]})]}),e.jsxs("div",{className:"flex flex-col items-end gap-1",children:[a.risk_level&&e.jsx(P,{variant:"outline",className:a.risk_level==="critical"||a.risk_level==="high"?"border-destructive/50 text-destructive":"border-muted-foreground/30",children:a.risk_level}),e.jsx("div",{className:"text-[11px] text-muted-foreground",children:ue(a.created_at)})]})]},a.id))]}),e.jsxs("section",{className:"space-y-3",children:[e.jsxs("h2",{className:"text-lg font-semibold flex items-center gap-2",children:[e.jsx(Be,{className:"h-4 w-4"})," Facebook sign-in retry"]}),e.jsx(W,{className:"p-4 space-y-3",children:e.jsxs("div",{className:"flex flex-wrap items-center justify-between gap-3",children:[e.jsxs("div",{className:"text-sm",children:[e.jsx("div",{className:"font-medium",children:T>0?`${T} publish job(s) blocked on Facebook sign-in (last 24h)`:"No Facebook sign-in blocks in the last 24h"}),e.jsxs("div",{className:"text-xs text-muted-foreground mt-0.5",children:["If Unk's browser isn't signed into Business Suite, publish jobs fail with"," ",e.jsx("code",{className:"text-[11px]",children:"facebook_login_required_in_browser_profile"}),". Click ",e.jsx("em",{children:"Open sign-in"}),", sign in inside Unk's Chrome window, then click ",e.jsx("em",{children:"Retry"}),"."]})]}),e.jsxs("div",{className:"flex flex-wrap gap-2",children:[e.jsx(E,{size:"sm",variant:"destructive",onClick:xt,disabled:_,title:"Kills any Playwright Chromium windows using Unk's Facebook browser profile so the next publish can launch cleanly.",children:_?"Force-closing…":"Force-close browser windows"}),e.jsx(E,{size:"sm",variant:"outline",onClick:ft,disabled:K,children:K?"Opening…":"Open sign-in"}),e.jsx(E,{size:"sm",onClick:gt,disabled:U||T===0,children:U?"Re-queueing…":"Retry login-blocked jobs"})]})]})})]}),e.jsxs("section",{className:"space-y-3",children:[e.jsxs("div",{className:"flex items-center justify-between",children:[e.jsxs("h2",{className:"text-lg font-semibold flex items-center gap-2",children:[e.jsx(Ht,{className:"h-4 w-4"})," Execution audit log"]}),e.jsxs("span",{className:"text-xs text-muted-foreground",children:["Last ",d.length," events"]})]}),d.length===0?e.jsx(W,{className:"p-6 text-sm text-muted-foreground text-center",children:"No template launches recorded yet. Every request, approval, dispatch, success, and failure shows up here automatically."}):e.jsx(W,{className:"divide-y",children:d.map(a=>{var D;const b=a.event_type==="succeeded"?se:a.event_type==="failed"||a.event_type==="rejected"||a.event_type==="revoked"?Qe:a.event_type==="dispatched"?ge:a.event_type==="approved"?ee:Ye,O=a.event_type==="succeeded"?"text-emerald-600":a.event_type==="failed"||a.event_type==="rejected"||a.event_type==="revoked"?"text-destructive":a.event_type==="approved"?"text-emerald-600":a.event_type==="dispatched"?"text-amber-600":"text-muted-foreground";return e.jsxs("div",{className:"flex items-start gap-3 p-3 text-xs",children:[e.jsx(b,{className:`h-4 w-4 mt-0.5 shrink-0 ${O}`}),e.jsxs("div",{className:"min-w-0 flex-1",children:[e.jsxs("div",{className:"flex items-center gap-2 flex-wrap",children:[e.jsx("span",{className:`font-medium uppercase tracking-wide ${O}`,children:a.event_type}),e.jsx("span",{className:"font-medium text-foreground",children:a.template_slug??a.action_type??a.capability}),a.risk_level&&e.jsx(P,{variant:"outline",className:"text-[10px] py-0",children:a.risk_level})]}),a.note&&e.jsx("div",{className:"text-muted-foreground mt-0.5 line-clamp-2",children:a.note}),e.jsxs("div",{className:"text-[10px] text-muted-foreground mt-0.5",children:[ue(a.created_at)," · actor: ",e.jsx("span",{className:"font-mono",children:a.actor??((D=a.user_id)==null?void 0:D.slice(0,8))??"system"})]})]})]},a.id)})})]}),e.jsxs(W,{className:"p-4 border-dashed text-xs text-muted-foreground flex gap-2",children:[e.jsx(ie,{className:"h-4 w-4 shrink-0 mt-0.5"}),e.jsxs("div",{children:["Phase 1 is the platform side only. The Windows companion (Phase 2) is not yet running, so devices will stay ",e.jsx("em",{children:"pending"})," or ",e.jsx("em",{children:"offline"})," until it's paired. Hard rules carry over from the bot lifecycle: no admin/elevated execution, allow-listed paths only, every action requires an approved request, and high-risk actions stay approval-gated."]})]})]})};export{xs as companionBuildUrlForSha,Gs as default,vs as fetchCompanionPackageMeta};
