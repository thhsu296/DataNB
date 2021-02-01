import re
from urllib.parse import urljoin
import requests
import sys
import os
from collections import defaultdict, Counter
import pandas as pd
import json

class dataNB():
    def __init__(self, folderName='store', fileName='DataNB.csv'):
        # Stored information
        self.parent = r'https://www2.gnb.ca/content/gnb/en/corporate/promo/covid-19/' # Absolute URL
        self.folderName = folderName
        self.fileName = fileName
        self.ageLevels = [19,29,39,49,59,69,79,89,90]
        self.numZones = 6
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
            .*?(?P<age>(?:\d9|90))
        """, re.VERBOSE)

        self.rePage = re.compile(r'news_release.*html') # Valid page name

        self.reChunkList = [
            re.compile(r""" # 0. With headline containing "new case"
            (?P<chunk>
            <p><b>[^<]*[Nn]ew\s[Cc]ases?</b></p>\n
            .*?Zone.*?)
            (?=<p>[^Z]*?</p>)
            """, re.VERBOSE | re.DOTALL),
            re.compile(r""" # 1. Preceded by a paragraph cotaining "Public Health"
            (?P<chunk>
            <p>[^<]*?Public\s(?:dog)?Heal?th.*?</p>\n # Covers the typo "Heath" in 2020.11.0615, 0607 and 0644
            .*?Zone.*?)
            (?=<p>[^Z]*?</p>)
            """, re.VERBOSE | re.DOTALL),
            re.compile(r""" # 2. Reported in a single line cotaining "Public Health"
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
            return self.w2d[w] # This also covers "No case" and "Without a case"
        return 0

    def getDescr(self, s:str):
        return self.reDescr.search(s).groupdict()['descr']

    def getNumAge(self, s: str):
        s.lower()
        num, age = self.reNumAge.search(s).groups()
        return self.w2d[num], int(age)

    def getChunk(self, s:str):
        for r in self.reChunkList:
            if r.search(s):
                return r.search(s).groupdict()['chunk']
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
        localstore = os.path.join(os.getcwd(), folderName)
        if not os.path.exists(localstore):
            os.mkdir(localstore)
        fList = os.listdir(localstore)
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
                path = os.path.join(localstore, fname)
                with open(path,'w') as fw:
                    doc = requests.get(url).content.decode('utf-8')
                    fw.write(doc)
            print('Done.')
            if not uList: break
        return None
    
    def load(self):
        localstore = os.path.join(os.getcwd(), self.folderName)
        fList = sorted(filter(self.isPage, os.listdir(localstore)))
        self.chunkData = defaultdict(dict)
        for i,fname in enumerate(fList):
            path = os.path.join(localstore,fname)
            with open(path,'r') as f:
                doc = f.read()
            date = self.getDate(doc)
            descr = self.getDescr(doc)
            chunk = self.getChunk(doc)
            total = self.getTotal(descr)
            if len(chunk) > 5000 or not chunk:
                chunk = chunk[:200] + '\n...\n' + chunk[-200:]
                print('='*50)
                print(i,fname,'\n')
                print(chunk)
            self.chunkData[date]['filename'] = fname
            self.chunkData[date]['total'] = total
            self.chunkData[date]['chunk'] = chunk
        # with open('dataChunks.json','w') as f:
        #     json.dump(dataChunks, f)
        return None
    
    def parse(self):
        self.load()
        dateList = sorted(self.chunkData.keys())
        for date in dateList:
            chunk = self.chunkData[date]['chunk']
            cnt = num = 0
            hasZone = False
            for s in chunk.split('\n'):
                if self.reZone.search(s) and self.reNumAge.search(s):
                    num, age = self.getNumAge(s)
                    zone = self.getZone(s)
                    self.info[date][zone][age] += num
                    cnt += num
                    #print(zone,age,num, s+'\n')
                elif self.reZone.search(s):
                    zone = self.getZone(s)
                    d = self.info[date][zone]
                    hasZone = True
                elif self.reNumAge.search(s) and hasZone:
                    num, age = self.getNumAge(s)
                    d[age] += num
                    cnt += num
                    #print(zone,age,num, s+'\n')
            # fname = self.chunkData[date]['filename']
            # total = self.chunkData[date]['total']
            # if cnt != total:
            #     print(f'Warning: Does not add up for {fname} ({date}). Total is {total}, but counted {cnt}.')
            #     print('\n',chunk)

    def save(self, filename='dataNB.csv'):
        n = self.numZones
        headerList = ['date'] + [f'Z{i}A{j}' for i in range(1,n+1) for j in self.ageLevels]
        header = ', '.join(headerList)
        dList = sorted(self.info.keys(), reverse=True)
        with open('dataNB.csv', 'w') as f:
            f.write(header + '\n')
            for date in dList:
                d = self.info[date]
                row = [date] + [str(d[i][j]) for i in range(1,n+1) for j in self.ageLevels]
                s = ', '.join(row)
                f.write(s + '\n')

if __name__ == '__main__':
    obj = dataNB(folderName='store', fileName='DataNB.csv')
    obj.download()
    obj.parse()
    obj.save()