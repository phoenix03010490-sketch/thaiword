#!/usr/bin/env python3
"""Generate simplified-Chinese display overlays without rewriting VOLUBILIS originals.
Uses ICU Traditional-Simplified transliteration (uconv), required only when regenerating.
"""
import json, pathlib, re, subprocess
ROOT=pathlib.Path(__file__).resolve().parents[1]
manifest=json.loads((ROOT/'data/manifest.json').read_text('utf-8'))
words={}
for part in manifest['parts']:
 for row in json.loads((ROOT/part['file']).read_text('utf-8')):
  if row.get('zh'):words[row['thai']]=row['zh']
keys=list(words)
values=[words[k].replace('\u00a0',' ').replace('\r',' ').replace('\n',' ') for k in keys]
trans=subprocess.run(['uconv','-x','Traditional-Simplified'],input='\n'.join(values)+'\n',text=True,check=True,capture_output=True).stdout.splitlines()
assert len(trans)==len(keys),(len(trans),len(keys))
out={}
for key,line in zip(keys,trans):
 parts=[x.strip() for piece in re.split('[；;]',line) for x in re.split(r'\s+/\s+|\s*[/／]\s*',piece) if x.strip()]
 result=[]
 for item in parts:
  item=re.sub(r'\s+',' ',item).strip(' ,，。;；')
  if item and item not in result:result.append(item)
 if result:out[key]='；'.join(result[:3])
p=ROOT/'data/zh-clean-v3.json'
p.write_text(json.dumps(out,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf-8')
print('clean Chinese entries:',len(out),'output bytes:',p.stat().st_size)
