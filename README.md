# Fetching New Brunswidk COVID-19 Data
Fetching data of the COVID-19 cases in New Brunswick, Canada

## The Task

The objective ot this script
is to convert reports,
which were written in descriptive senances,
of daily new COVID-19 cases in New Brunswick
into a table of the following form.

### Output:
>| | Z1.A00 | Z2.A20 | Z2.A30 | ... | Z2.A00 | Z2.A20 | Z4.A30 | ... |
>|---:|--:|--:|--:|--:|--:|--:|--:|--:|
>|  2020-12-04 | 1 | 0 | 0 | ... | 0 | 1 | 3 | ... |
>|  2020-12-03 | 1 | 0 | 1 | ... | 1 | 3 | 0 | ... |

Each label __Z*x*.A*y*__
indicates a zone __*x*__ and a age group __*y*__,
and the age groups are 0-19, 20-29, 30-39, ..., 80-89,
and above 90.
For instance,
**Z1.A30** means **Zone 1** and **Age 30-39**.
Entries in the table are the number of new cases
for the corresponding dates and labels.

The descriptive sentences
are from webpages reporting
daily new cases of COVID-19 in
the Government of New Brunswick
[website](https://www2.gnb.ca/content/gnb/en/corporate/promo/covid-19/news.html).

In the Government of New Brunswick
[website](https://www2.gnb.ca/content/gnb/en/corporate/promo/covid-19/news.html),
the post of the report has the following form.
Note that not all items
are related to new cases.

### Input 1:
> <h2>Recent News Releases</h2>
> <span>04 December 2020</span>
> <div><a href="https://www2.gnb.ca/content/gnb/en/corporate/promo/covid-19/news/news_release.2020.12.0658.html">Eight new cases of COVID-19</a></div>
> <span>03 December 2020</span>
> <div><a href="https://www2.gnb.ca/content/gnb/en/corporate/promo/covid-19/news/news_release.2020.12.0654.html">Six new cases / outbreak in Zone 5 over / COVID-19 vaccine planning / holiday guidance</a></div>
> <span>03 December 2020</span>
> <div><a href="https://www2.gnb.ca/content/gnb/en/corporate/promo/covid-19/news/news_release.2020.12.0653.html">Residents can now report damages related to flooding</a></div>

In each report of new cases,
cases are categorized by zones and age levels.
However, the formats of the reports
may vary from day to day.
As shown it the two examples below,
hey may be itemized
when the number of cases is larger,
or may be stated in a single line
when there are only a few cases.

The number of cases are itemized 
in the report on December 4th, 2020:

### Input 2(a):
><h2>Eight new cases of COVID-19</h2><span class="post_date">04 December 2020</span><div class="articleBody"><p>FREDERICTON (GNB) – Public Health reported eight new cases of COVID-19 today.</p>
><p>The cases are as follows:</p>
><ul>
><li>one individual 30-39 in Zone 1 (Moncton region);</li>
><li>one individual 50-59 in Zone 2 (Saint John region);</li>
><li>one individual 60-69 in Zone 2 (Saint John region);</li>
><li>one individual 60-69 in Zone 3 (Fredericton region);</li>
><li>three people 19 and under in Zone 4 (Edmundston region); and</li>
><li>one individual 40-49 in Zone 4 (Edmundston region).</li>
></ul>
><p>All cases are self-isolating and under investigation.</p>

The report December 12th, 2020:

### Input 2(b):
> <h2>One new case of COVID-19</h2>
> <span>12 December 2020</span>
> <p>FREDERICTON (GNB) – Public Health reported one new case of COVID-19 today.</p>
> <p>The new case is an individual 20 to 29 in Zone 2 (Saint John region), who is self-isolating.</p>

The taks consists of two parts.
The first part
is to fetch related items from
the news posting website,
and the second part is
to extract information from the descriptive sentances.


## Usage

This script can download 
webpages that reports new cases
from the Government of New Brunswick website
to a local foler,
and then create a *.csv* file
containing a table of number of new cases.


To run this script in a **terminal**,
simply type the following command.

```sh
python dataNB.py
```

Alternatively,
inside any other __*Python* script__,
type the following codes.

```python
import dataNB
obj = dataNB(foldername='store',filename='dataNB.csv')
obj.download()
obj.parse()
obj.save()
```

By deault,
the resulted table will be saved as
"dataNB.csv" (with 0's) and "dataNB_drop.csv" (dropped 0's) in the working folder,
and all related webpages will be stored in the subfolder "./store".
The files "chunks.txt" and "log.txt"
will also be generated
for screening possible errors.

## Procedures

Here is a description of the procedures of the module.
It mainly relies on
[**Regular Expression**](https://docs.python.org/3/library/re.html),
or **regex**,
which is a powerful tool
for pattern string search.
It can be imported in Pyhon
by calling ```import re```.

### The download() mehtod

The webpage *news.html*
contains a number of hyperlinks,
which are of the following form.

```html
<div class="h3">
<a href="/content/gnb/en/corporate/promo/covid-19/news/news_release.2020.12.0715.html"
title="Public Health reported two new cases of COVID-19 today.">
Two new cases of COVID-19</a></div>
...
<div class="h3">
<a href="/content/gnb/en/corporate/promo/covid-19/news/news_release.2020.12.0654.html"
title="Public Health reported six new cases of COVID-19 today.">
Six new cases / outbreak in Zone 5 over / COVID-19 vaccine planning / holiday guidance
</a></div>
...
```

Besides the **URL**,
the **description** of the link is also needed
in order to determine whether
the corresponding page is reporting new cases.
The following regex, named reLink,
extracts those two factors from each hyperlink.

```Python
reLink = re.compile(r"""
    <a\s
    href="(?P<link>.+?)"
    .*?>
    (?P<descr>.+?)</a>
""", re.VERBOSE)
```

The ```.findall()``` method of the regex
is used to parse all hyperlinks in the webpage
in the following code.

```Python
url = r'https://www2.gnb.ca/content/gnb/en/corporate/promo/covid-19/news.html'
s = requests.get(url).content.decode('utf-8')
uList = [ ]
for link, descr in reLink.findall(s):
    if getTotal(descr): # Check that the webpage reports new cases
        uList.append(link)
```

Message of the following form
will appear to show the progress
of the downloading process.

```
Page #0 has 47 related items: 0 already exist; downloading 47 itmes... Done.
Page #1 has 44 related items: 0 already exist; downloading 44 itmes... Done.
Page #2 has 34 related items: 0 already exist; downloading 34 itmes... Done.
Page #3 has 24 related items: 0 already exist; downloading 24 itmes... Done.
Page #4 has 8 related items: 0 already exist; downloading 8 itmes... Done.
Page #5 has 14 related items: 0 already exist; downloading 14 itmes... Done.
Page #6 has 0 related items: 0 already exist; downloading 0 itmes... Done.
```

### The parse() mehtod

Because reports of new cases have various formats,
multiple regular expressions are needed.

### Regex 1.
The first regex captures
the part of the html document
from a headline containing "new case"
to the line before
a paragraph not containing letter "Z".


```Python
re.compile(r"""
    (?P<chunk>
    <p><b>[^<]*[Nn]ew\s[Cc]ases?</b></p>\n
    .*?Zone.*?)
    (?=<p>[^Z]*?</p>)
""", re.VERBOSE | re.DOTALL),
```

For instance,
the following paragraph
matches this pattern string.

```html
<p><b>New cases</b></p>
<p>Public Heath reported four new cases of COVID-19 today.</p>
<p>The three cases in Zone 1 (Moncton region) are as follows:</p>
<ul>
<li>one individual 19 and under; and;</li>
</ul>
<ul>
<li>two people 20 to 29.</li>
</ul>
<p>The other case is an individual 30 to 39 in Zone 2 (Saint John region).</p>
```

### Regex 2.
The second regex
captures the part
starting from a paragraph 
containing "Public Health"
to the line before
a paragraph not containing letter "Z".

```Python
re.compile(r"""
    (?P<chunk>
    <p>[^<]*?Public\sHeal?th.*?</p>\n
    .*?Zone.*?)
    (?=<p>[^Z]*?</p>)
""", re.VERBOSE | re.DOTALL),
```

Note that the term 'Heal?th' matches both "Heath" and "Health".
This covers typo "Heath" that appeared in some of the reports.

The following paragraph
matches this pattern string.

```html
<p>FREDERICTON (GNB) – Public Health reported eight new cases of COVID-19 today.</p>
<p>The cases are as follows:</p>
<ul>
<li>one individual 30-39 in Zone 1 (Moncton region);</li>
<li>one individual 50-59 in Zone 2 (Saint John region);</li>
<li>one individual 60-69 in Zone 2 (Saint John region);</li>
<li>one individual 60-69 in Zone 3 (Fredericton region);</li>
<li>three people 19 and under in Zone 4 (Edmundston region); and</li>
<li>one individual 40-49 in Zone 4 (Edmundston region).</li>
</ul>
```

### Regex 3.
The third regex
deals with the case
where all needed information
are presented in a single line,
which may happen when
the number of cases is small.
This regex captures
the single line cotaining "Public Health".

```Python
re.compile(r"""
(?P<chunk>
<p>[^<]*?Public\sHealth[^<]*?report[^<]*? #
[^<]*?Zone[^<]*?
</p>)
""", re.VERBOSE | re.DOTALL),
```

The following paragraph
matches this pattern string.

```html
<p>The new case is an individual 19 and under in Zone 3 (Fredericton region),
related to an international travel-related case and who is self-isolating.</p>
```

### Combination of the three regex.
Each webpage
is tested by all listed regex one by one
until suceed or exhausted.
As many regex as needed can be added.

```Python
reChunkList = [
    re.compile( ... ), # reChunk1
    re.compile( ... ), # reChunk2
    re.compile( ... ), # reChunk3
]
def getChunk(s:str):
    for r in reChunkList:
        if r.search(s):
            return r.search(s).groupdict()['chunk']
    return ''
```

The following code
stores the chunks in a hashtable.

```Python
self.chunkData = collections.defaultdict(dict)
for i,fname in enumerate(fList):
    path = os.path.join(localstore,fname)
    with open(path,'r') as f:
        doc = f.read()
    date = self.getDate(doc)
    descr = self.getDescr(doc)
    chunk = self.getChunk(doc)
    total = self.getTotal(descr)
    self.chunkData[date]['filename'] = fname
    self.chunkData[date]['total'] = total
    self.chunkData[date]['chunk'] = chunk
```

## Grinding Chunks

After a proper chunk
is sliced from each webpage,
the number for cases
in each zone for each age group
needs to be extracted
line by line.
The following two regex
read those three factors.

```Python
reNumAge = re.compile(r""" # Get number of cases and the corresponding age
    (?P<num>\w+) 
    \s(?:individual|people)
    .*?(?P<age>(?:\d0|19))
""", re.VERBOSE)

def getNumAge(s: str):
    s = s.lower()
    num, age = reNumAge.search(s).groups()
    return w2d[num], int(age)
```

```Python
reZone = re.compile(r"""
    Zone\s(?P<zone>\d)
""", re.VERBOSE)

def getZone(s: str):
    zone = reZone.search(s).groupdict()['zone']
    return int(zone)
```

The following code
stores the infomation of each
chunks, labeled by dates, in a hashtable.

```Python
dateList = sorted(self.chunkData.keys())
for date in dateList:
    fname = self.chunkData[date]['filename']
    total = self.chunkData[date]['total']
    chunk = self.chunkData[date]['chunk']
    d = {}
    for s in chunk.split('\n'):
        if self.reZone.search(s):
            zone = self.getZone(s)
            d = self.info[date][zone]
        elif self.reNumAge.search(s) and d:
            num, age = self.getNumAge(s)
            d[age] += num
```

### The save() method

Extracted data are stored
in the hash table *info*.
The script can save it in a *.csv* file.

```Python
# info[date][zone][age] = number of new cases
info = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
def save():
    headerList = ['date'] + [f'Z{i}A{j}' for i in range(1,numZones+1) for j in self.ageLevels]
    header = ', '.join(headerList)
    dList = sorted(info.keys(), reverse=True)
    with open('DataNB.csv', 'w') as f:
        f.write(header + '\n')
        for date in dList:
            d = info[date]
            row = [date] + [str(d[i][j]) for i in range(1,numZones+1) for j in ageLevels]
            s = ', '.join(row)
            f.write(s + '\n')
```

## Edge Cases

A small portion of the webpages were written
in formats that are not captured but this script.
For instance,
in "news_release.2020.03.0164.html"
the ages of indivisuals
were not given.

Fortunately,
thanks to the coherent writing style
of the Government of New Brunswick,
those edge cases are not too many,
and are within a reasonable amount
to be handeled manually.