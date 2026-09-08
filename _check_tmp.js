const fs=require('fs');
const s=fs.readFileSync('index.html','utf8');
const re=/<script(?![^>]*type=)[^>]*>([\s\S]*?)<\/script>/g;
let m,i=0,err=0;
while((m=re.exec(s))){i++;const code=m[1].trim();if(!code)continue;
  try{new Function(code)}catch(e){err++;console.log('block',i,'ERROR:',e.message)}}
console.log('js blocks:',i,'errors:',err);
