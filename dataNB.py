import re
from urllib.parse import urljoin
import requests
import sys
import os
from collections import defaultdict, Counter
import pandas as pd
import json

class dataNB():
    def __init__(self):
        # Stored information
        self.parent = r'https://www2.gnb.ca/content/gnb/en/corporate/promo/covid-19/' # Absolute URL
        self.ageLevels = [0,20,30,40,50,60,70,80,90]
        self.numZones = 7
        self.w2d = Counter({
            'one':1, 'an':1, 'the': 1, 'two':2, 'three':3, 'four':4, 'five':5,
            'six':6, 'seven':7, 'eight':8, 'nine':9,
            'ten':10, 'eleven':11, 'twelve':12, 'thirteen':13, 'fourteen':14, 'fifteen':15,
            'sixteen':16, 'seventeen':17, 'eighteen':18, 'nineteen':19, 'twenty':20,
        }) # Unlisted numbers will be counted as 0
        self.chunkData = defaultdict(dict)
        self.info = defaultdict(lambda: defaultdict(lambda: defaultdict(int))) # info[date][zone][age] = number of cases

        # Compile regular expressions
        self.reLink = re.compile(r""" # Get link and description
            <a\s
            href="(?P<link>.+?)"
            .*?>
            (?P<descr>.+?)</a>
        """, re.VERBOSE)

        self.reName = re.compile(r'.*/(?P<name>.+)$') # Get the filename from the link

        self.reTotal = re.compile(r"""
            (?P<total>\w+)\snew\scase
        """, re.VERBOSE)

        self.reDescr = re.compile(r"""
            name="dcterms.title"\scontent=
            "(?P<descr>.*?)"
        """, re.VERBOSE)

        self.reNumAge = re.compile(r""" # Get number of cases and the corresponding age
            (?P<num>\w+) 
            \s(?:individual|people)
            .*?(?P<age>(?:\d0|19|9))
        """, re.VERBOSE)

        self.rePage = re.compile(r'news_release.*html') # Valid page name

        self.reChunkList = [
            re.compile(r""" # 0. With headline containing "new case"
            (?P<chunk>
            <p><b>[^<]*[Nn]ew\s[Cc]ases?</b></p>\n
            .*?Zone.*?)
            (?=<p>[^Z]*?</p>)
            """, re.VERBOSE | re.DOTALL),
            re.compile(r""" # 1. Preceded by a paragraph cotaining "FREDERICTON (GNB)"
            (?P<chunk>
            <p>FREDERICTON\s\(GNB\).*?</p>\n
            .*?Zone.*?)
            (?=<p>[^Z]*?</p>)
            """, re.VERBOSE | re.DOTALL),
            re.compile(r""" # 2. Preceded by a paragraph cotaining "Public Health"
            (?P<chunk>
            <p>[^<]*?Public\sHeal?th.*?</p>\n # Covers the typo "Heath" in 2020.11.0615, 0607 and 0644
            .*?Zone.*?)
            (?=<p>[^Z]*?</p>)
            """, re.VERBOSE | re.DOTALL),
            re.compile(r""" # 3. Reported in a single line cotaining "Public Health"
            (?P<chunk>
            <p>[^<]*?Public\sHealth[^<]*?report[^<]*? #
            [^<]*?Zone[^<]*?
            </p>)
            """, re.VERBOSE | re.DOTALL),
        ]

        self.reDate = re.compile(r"""
            "post_date">
            (?P<dd>\d{2})-(?P<mm>\d{2})-(?P<yy>\d{2}) # Get the date dd-mm-yy
            </span>.*
        """, re.VERBOSE)

        self.reZone = re.compile(r"""
            Zone\s(?P<zone>\d)
        """, re.VERBOSE)

    def getAbs(self, s: str):
        return urljoin(self.parent, s)
    
    def getName(self, s:str):
        return self.reName.match(s).groupdict()['name']

    def getTotal(self, s: str):
        s = s.lower()
        if self.reTotal.search(s):
            w = self.reTotal.search(s).groupdict()['total']
            if w.isnumeric():
                return int(w)
            return self.w2d[w] # This also covers "No case" and "Without a case"
        return 0

    def getDescr(self, s:str):
        return self.reDescr.search(s).groupdict()['descr']

    def getNumAge(self, s: str):
        s = s.lower()
        num, age = self.reNumAge.search(s).groups()
        if age in ('9','19','10'):
            age = '0'
        return self.w2d[num], int(age)

    def getChunk(self, s:str):
        lmax = 5000 # Max accepted length
        for r in self.reChunkList:
            if r.search(s):
                w = r.search(s).groupdict()['chunk']
                if len(w) > lmax: return ''
                return w
        return ''

    def getDate(self, s:str):
        dd, mm, yy = self.reDate.search(s).groups()
        return '-'.join([yy,mm,dd])

    def getZone(self, s: str):
        zone = self.reZone.search(s).groupdict()['zone']
        return int(zone)
    
    def isPage(self, s:str):
        if self.rePage.match(s):
            return True
        return False
    
    def download(self, folderName='store'):
        url0 = self.getAbs('news.html')
        suffix = r'?mainContent_par_newslist_update_start={k}'
        if not os.path.exists( folderName ):
            os.mkdir( folderName )
        fList = os.listdir( folderName )
        for k in range(0,400,50):
            urlNews = url0 + suffix.format(k=k) if k > 0 else url0
            news = requests.get(urlNews).content.decode('utf-8')
            cntRelated = 0
            uList = []
            for link, descr in self.reLink.findall(news):
                if self.getTotal(descr):
                    cntRelated += 1
                    fname = self.getName(link)
                    if fname not in fList:
                        uList.append(link)
            print('Page #{a} has {b} related items: {c} already exist; downloading {d} itmes...'
                    .format(a=k//50, b=cntRelated, c=cntRelated-len(uList), d=len(uList)), end=' '
                )
            for link in uList:
                url = self.getAbs(link)
                fname = self.getName(link)
                path = os.path.join( folderName, fname )
                with open(path,'w') as fw:
                    doc = requests.get(url).content.decode('utf-8')
                    fw.write(doc)
            print('Done.')
            if not uList: break
        return None
    
    def load(self, folderName='store'):
        fList = sorted(filter(self.isPage, os.listdir(folderName)))
        with open('chunks.txt','w') as fw:
            for fname in fList:
                path = os.path.join(folderName,fname)
                with open(path,'r') as f:
                    doc = f.read()
                date = self.getDate(doc)
                descr = self.getDescr(doc)
                chunk = self.getChunk(doc)
                total = self.getTotal(descr)
                fw.write('='*50 + '\n' + fname + '\n\n' + chunk + '\n')
                if not chunk:
                    print(f'Failed to slice {fname}\n')
                self.chunkData[date]['filename'] = fname
                self.chunkData[date]['total'] = total
                self.chunkData[date]['chunk'] = chunk
            return None

    def patch(self, patchName='patch.csv'):
        if not os.path.exists( patchName ):
            return dict()
        with open(patchName,'r') as f:
            doc = f.read()
        docRows = doc.split('\n')
        header = docRows[0].split(',')[1:]
        patchData = defaultdict(lambda: defaultdict(dict))
        for row in docRows[1:]:
            row = row.split(',')
            date, nums = row[0][2:], row[1:]
            for s, n in zip(header, nums):
                s = s.replace(' ','')
                n = n.replace(' ','')
                if s not in ('Total','Off') and n:
                    z, a = int(s[1]), int(s[-2:])
                    patchData[date][z][a] = int(n)
        return patchData

    def parse(self, folderName='store', patchName='patch.csv'):
        self.load()
        dateList = sorted(self.chunkData.keys())
        patchData = self.patch()
        with open('log.txt','w') as flog:
            for date in dateList:
                chunk = self.chunkData[date]['chunk']
                cnt = num = 0
                hasZone = False
                for s in chunk.split('\n'):
                    if self.reZone.search(s):
                        zone = self.getZone(s)
                        d = self.info[date][zone]
                        hasZone = True
                    if self.reNumAge.search(s) and hasZone:
                        num, age = self.getNumAge(s)
                        d[age] += num
                        cnt += num
                        #print(zone,age,num, s+'\n')
                if date in patchData:
                    for z in range(1, self.numZones + 1):
                        cnt -= sum( self.info[date][z].values() or [0] )
                        cnt += sum( patchData[date][z].values() or [0] )
                        self.info[date][z].update( patchData[date][z] )
                fname = self.chunkData[date]['filename']
                total = self.chunkData[date]['total']
                if cnt != total:
                    message = f'Warning: {fname} ({date}). Total is {total}, but counted {cnt}'
                    print(message)
                    flog.write(message + '\n')
                    self.chunkData[date]['off'] = 'v'
                else:
                    self.chunkData[date]['off'] = ''

    def save(self, fileName='DataNB.csv'):
        n = self.numZones
        headerList = ['Date','Total','Off'] + [f'Z{i}.A{j:02d}' for i in range(1,n+1) for j in self.ageLevels]
        header = ', '.join(headerList)
        dList = sorted(self.info.keys())
        fname = fileName
        if '.csv' in fname:
            fname = fname.replace('.csv','')
        with open(fname + '_0.csv', 'w') as f, open(fname + '.csv', 'w') as fDrop:
            f.write(header + '\n')
            fDrop.write(header + '\n')
            for date in dList:
                d = self.info[date]
                total = str(self.chunkData[date]['total'])
                off = self.chunkData[date]['off']
                row = ['20'+date, total, off] + [str(d[i][j]) for i in range(1,n+1) for j in self.ageLevels]
                s = ', '.join(row)
                f.write(s + '\n')
                rowDrop = ['20'+date, total, off] + [str(d[i][j]) if d[i][j] else '' for i in range(1,n+1) for j in self.ageLevels]
                sDrop = ', '.join(rowDrop)
                fDrop.write(sDrop + '\n')

if __name__ == '__main__':
    obj = dataNB()
    obj.download( folderName='store' )
    obj.parse( folderName='store', patchName='patch.csv' )
    obj.save( fileName='DataNB.csv' )