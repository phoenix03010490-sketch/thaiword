#!/usr/bin/env python3
"""ThaiWord v3 reproducible study overlay from licensed datasets.
Never alters the VOLUBILIS dictionary or the user's browser data.
Run on GitHub Actions, or set THAIWORD_READER_FILE/THAIWORD_PHUPHA_FILE for local tests.
"""
import csv, io, json, os, pathlib, sys, time, unicodedata, urllib.request
ROOT=pathlib.Path(__file__).resolve().parents[1]
URLS={
 'reader':'https://thaireader.app/learner/v42/list.tsv',
 'phupha':'https://raw.githubusercontent.com/PyThaiNLP/Phupha-Word-freq/main/wordfreq.csv',
 'examples':'https://thaireader.app/learner/v42/examples.tsv',
}
BUCKETS={500:0,1000:1,2000:2,3000:3,5000:4}
def norm(s):return unicodedata.normalize('NFC',str(s or '').strip())
def fetch(key,required=False):
 env=os.environ.get('THAIWORD_'+key.upper()+'_FILE')
 if env:return pathlib.Path(env).read_text(encoding='utf-8-sig')
 for attempt in range(3):
  try:
   req=urllib.request.Request(URLS[key],headers={'User-Agent':'ThaiWord-learning-v3/1.0'})
   with urllib.request.urlopen(req,timeout=60) as r:content=r.read()
   return content.decode('utf-8-sig')
  except Exception as e:
   print(f'{key}: attempt {attempt+1}: {e}',file=sys.stderr)
   time.sleep(attempt+1)
 if required:raise RuntimeError('Cannot obtain '+key+' original dataset')
 return ''
def pick(row,*names):
 for name in names:
  if row.get(name):return row[name]
 return ''
def main():
 manifest=json.loads((ROOT/'data/manifest.json').read_text(encoding='utf-8'))
 master=[]
 for part in manifest['parts']:
  for row in json.loads((ROOT/part['file']).read_text(encoding='utf-8')):
   if row.get('thai'):master.append((norm(row['thai']),int(row.get('tier') or 99),int(row.get('rank') or 999999999)))
 if len(master)!=manifest['headwords'] or len({x[0] for x in master})!=manifest['headwords']:raise ValueError('dictionary rows mismatch')
 reader,phupha,id_to_word={}, {},{}
 raw=fetch('reader')
 if raw:
  for row in csv.DictReader(io.StringIO(raw),delimiter='\t'):
   thai=norm(row.get('word'))
   try:bucket=int(row.get('bucket',''))
   except (ValueError,TypeError):continue
   if thai and bucket in BUCKETS:
    reading=norm(row.get('reading'))
    reader[thai]={'bucket':bucket,'reading':reading}
    if row.get('id'):id_to_word[row['id']]=thai
  if len(reader)<4000:raise ValueError('ThaiReader file unexpectedly small; refusing questionable data')
 raw=fetch('phupha')
 if raw:
  for row in csv.DictReader(io.StringIO(raw)):
   w=norm(row.get('word'))
   try:num=int(float(row.get('count','-1')))
   except (ValueError,TypeError):continue
   if w and num>=0:phupha[w]=num
  if len(phupha)<40000:raise ValueError('Phupha file unexpectedly small; refusing questionable data')
 if not reader and not phupha:raise RuntimeError('No authentic frequency sources obtained; refusing fictitious ranking')
 sentences={}
 raw=fetch('examples') if reader else ''
 if raw:
  for row in csv.DictReader(io.StringIO(raw),delimiter='\t'):
   if str(row.get('pick','')).strip().lower() not in ('1','true','yes'):continue
   word=norm(pick(row,'word','headword','entry','entry_word'))
   if not word:word=id_to_word.get(str(pick(row,'word_id','entry_id','id')).strip(),'')
   th=norm(pick(row,'th','thai','thai_text','text_th','sentence_th','sentence','example_th'))
   en=norm(pick(row,'en','english','translation','sentence_en','example_en'))
   if word in reader and th and len(th)<450 and word not in sentences:sentences[word]={'th':th,'en':en}
 def key(row):
  word,tier,rank=row
  if word in reader:
   return (0,BUCKETS[reader[word]['bucket']],-phupha.get(word,-1),rank,word)
  if word in phupha:
   return (1,-phupha[word],tier,rank,word)
  return (2,tier,rank,0,word)
 master.sort(key=key)
 order=[row[0] for row in master]
 out={'version':3,'headwords':len(order),'method':'ThaiReader v42 graded spoken-word buckets; Phupha 2025 Common Crawl token counts within tiers and for remaining matches; dictionary fallback for unmatched. Not an exact conversational frequency rank.',
 'reader_matched':sum(w in reader for w in order),'phupha_matched':sum(w in phupha for w in order),'reader_entries':len(reader),'phupha_entries':len(phupha),
 'examples_matched':len(sentences),'sources':{'reader':URLS['reader'],'phupha':URLS['phupha'],'examples':URLS['examples']},
 'order':order,'readings':{w:reader[w]['reading'] for w in order if w in reader and reader[w]['reading']},
 'buckets':{w:reader[w]['bucket'] for w in order if w in reader},'examples':sentences}
 path=ROOT/'data/study-overlay-v3.json'
 path.write_text(json.dumps(out,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf-8')
 print('Built',len(order),'headwords; ThaiReader',out['reader_matched'],'Phupha',out['phupha_matched'],'examples',out['examples_matched'])
 if not reader:print('WARNING: ThaiReader missing; only Phupha website-count ranking.',file=sys.stderr)
 if not phupha:print('WARNING: Phupha missing; no within-level corpus count.',file=sys.stderr)
if __name__=='__main__':main()
