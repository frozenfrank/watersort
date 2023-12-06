b={}
for i in [0]*int(input()):f,l,d=input().split();b[d]=max((int(l),f),b.get(d,(-1,)))
print(len(b),*sorted([f for (_,f) in b.values()]),sep='\n')