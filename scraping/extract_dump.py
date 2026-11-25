import json,sys
f,out=sys.argv[1],sys.argv[2]
t=json.load(open(f))[0]['text']
s,_=json.JSONDecoder().raw_decode(t)
body=s.split('__BEGIN__\n',1)[1].split('\n__END__',1)[0]
hdr='host\tpath\tcat\tid\tname\tsale_price\tprice_or_list\trating\tpromo\tsubtitle\turl'
lines=[l for l in body.split('\n') if l.strip()]
open(out,'w').write(hdr+'\n'+'\n'.join(lines)+'\n')
print(len(lines), set(len(l.split('\t')) for l in lines), len(set(l.split('\t')[3] for l in lines)))
