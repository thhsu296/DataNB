"""Retrieving and parsing NB data.
"""

import csv
import os
import re
from collections import defaultdict, Counter
from urllib.parse import urljoin

import requests


AGE_GROUPS = {
    0: '<20', 20: '20-29', 30: '30-39', 40: '40-49', 50: '50-59',
    60: '60-69', 70: '70-79', 80: '80-89', 90: '90+'
}
NUM_ZONES = 7


class DataNB():
    """Data NB."""

    parent = r'https://www2.gnb.ca/content/gnb/en/news/'
    word_to_int = Counter({
        'one': 1, 'an': 1, 'the': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
        'six': 6, 'seven': 7, 'eight': 8, 'nine': 9,
        'ten': 10, 'eleven': 11, 'twelve': 12, 'thirteen': 13, 'fourteen': 14, 'fifteen': 15,
        'sixteen': 16, 'seventeen': 17, 'eighteen': 18, 'nineteen': 19, 'twenty': 20,
    })
    chunk_data = defaultdict(dict)
    info = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))

    # Compile regular expressions
    re_link = re.compile(r""" # Get link and description
        <a\s
        href="(?P<link>.+?)"
        .*?>
        (?P<descr>.+?)</a>
    """, re.VERBOSE)

    re_name = re.compile(r'.*/(?P<name>.+)$')  # Get the filename from the link

    re_total = re.compile(r"""
        (?P<total>\w+)\snew\scase
    """, re.VERBOSE)

    re_descr = re.compile(r"""
        name="dcterms.title"\scontent=
        "(?P<descr>.*?)"
    """, re.VERBOSE)

    re_num_age = re.compile(r""" # Get number of cases and the corresponding age
        (?P<num>\w+) 
        \s(?:individual|people)
        .*?(?P<age>(?:\d0|19|9))
    """, re.VERBOSE)

    re_page = re.compile(r'news_release.*html')  # Valid page name

    re_chunk_list = [
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

    re_date = re.compile(r"""
        "post_date">
        (?P<dd>\d{2})-(?P<mm>\d{2})-(?P<yy>\d{2}) # Get the date dd-mm-yy
        </span>.*
    """, re.VERBOSE)

    re_zone = re.compile(r"""
        Zone\s(?P<zone>\d)
    """, re.VERBOSE)

    def _get_abs_url(self, suffix_url: str):
        return urljoin(self.parent, suffix_url)

    def _get_name(self, chunk: str):
        return self.re_name.match(chunk).groupdict()['name']

    def _get_total(self, chunck: str):
        chunck = chunck.lower()
        if self.re_total.search(chunck):
            total_str = self.re_total.search(chunck).groupdict()['total']
            if total_str.isnumeric():
                return int(total_str)
            # This also covers "No case" and "Without a case"
            return self.word_to_int[total_str]
        return 0

    def _get_descr(self, chunck: str):
        return self.re_descr.search(chunck).groupdict()['descr']

    def _get_num_age(self, chunck: str):
        chunck = chunck.lower()
        num, age = self.re_num_age.search(chunck).groups()
        if age in ('9', '19', '10'):
            age = '0'
        return self.word_to_int[num], int(age)

    def _get_chunk(self, text: str):
        lmax = 5000  # Max accepted length
        for re_chunk in self.re_chunk_list:
            if re_chunk.search(text):
                chunk = re_chunk.search(text).groupdict()['chunk']
                if len(chunk) > lmax:
                    return ''
                return chunk
        return ''

    def _get_date(self, chunk: str):
        date_dict = self.re_date.search(chunk).groupdict()
        return "20{yy}-{mm}-{dd}".format(**date_dict)

    def _get_zone(self, chunk: str):
        zone = self.re_zone.search(chunk).groupdict()['zone']
        return int(zone)

    def _is_page(self, chunk: str):
        if self.re_page.match(chunk):
            return True
        return False

    def download(self, folder_name='data'):
        """download files."""
        url0 = self._get_abs_url('news.html')
        suffix = r'?mainContent_par_newslist_update_start={k}'
        if not os.path.exists(folder_name):
            os.mkdir(folder_name)
        filename_list = os.listdir(folder_name)
        for k in range(0, 400, 50):
            url_news = url0 + suffix.format(k=k) if k > 0 else url0
            url_list = self._get_url_list(k, url_news, filename_list)
            self._save_files(url_list, folder_name)
            if not url_list:
                break
        print('Completed download.\n')

    def _get_url_list(self, k, url_news, filename_list):
        news = requests.get(url_news).content.decode('utf-8')
        related_count = 0
        url_list = []
        for url, descr in self.re_link.findall(news):
            if self._get_total(descr):
                related_count += 1
                filename = self._get_name(url)
                if filename not in filename_list:
                    url_list.append(url)
        page_num = k // 50
        print(f'Page #{page_num} has {related_count} related items.')
        return url_list

    def _save_files(self, url_list, folder_name):
        print('downloading {len(url_list)} itmes...')
        for url in url_list:
            abs_url = self._get_abs_url(url)
            path = os.path.join(folder_name, self._get_name(url))
            with open(path, 'w', encoding='utf-8') as fwrite:
                doc = requests.get(abs_url).content.decode('utf-8')
                fwrite.write(doc)
        print('Completed downloading files.')

    def load(self, folder_name='data'):
        """load files."""
        f_list = sorted(filter(self._is_page, os.listdir(folder_name)))
        with open('chunks.txt', 'w', encoding='utf-8') as fw:
            for fname in f_list:
                path = os.path.join(folder_name, fname)
                with open(path, 'r', encoding='utf-8') as f:
                    doc = f.read()
                date = self._get_date(doc)
                descr = self._get_descr(doc)
                chunk = self._get_chunk(doc)
                total = self._get_total(descr)
                fw.write('='*50 + '\n' + fname + '\n\n' + chunk + '\n')
                if not chunk:
                    print(f'Failed to slice {fname}\n')
                self.chunk_data[date]['filename'] = fname
                self.chunk_data[date]['total'] = total
                self.chunk_data[date]['chunk'] = chunk

    def patch(self, patch_name='patch.csv'):
        """patch for the data."""
        if not os.path.exists(patch_name):
            return {}
        patch_data = defaultdict(lambda: defaultdict(dict))
        with open(patch_name, 'r', encoding="utf-8") as csvfile:
            reader = csv.reader(csvfile)
            next(reader)  # Skip the header
            for row in reader:
                date = row[0].strip()
                zone, age, count = map(int, row[1:])
                patch_data[date][zone][age] = count
        return patch_data

    def parse(self, folder_name='data', patch_name='patch.csv'):
        """parse the local files in the folder."""
        self.load(folder_name)
        date_list = sorted(self.chunk_data.keys())
        patch_data = self.patch(patch_name)
        for date in date_list:
            self._parse_by_date(date, patch_data)
        print('Completed parsing sources.\n')

    def _parse_by_date(self, date, patch_data):
        chunk = self.chunk_data[date]['chunk']
        cnt = 0
        has_zone = False
        for paragraph in chunk.split('\n'):
            if self.re_zone.search(paragraph):
                zone = self._get_zone(paragraph)
                date_zone_info = self.info[date][zone]
                has_zone = True
            if self.re_num_age.search(paragraph) and has_zone:
                num, age = self._get_num_age(paragraph)
                date_zone_info[age] += num
                cnt += num
        if date in patch_data:
            for zone in range(1, NUM_ZONES + 1):
                cnt -= sum(self.info[date][zone].values() or [0])
                cnt += sum(patch_data[date][zone].values() or [0])
                self.info[date][zone].update(patch_data[date][zone])
        filename = self.chunk_data[date]['filename']
        total = self.chunk_data[date]['total']
        if cnt != total:
            message = f'Warning: {filename} ({date}). Total is {total}, but counted {cnt}'
            print(message)

    def save(self, file_name='dataNB.csv'):
        """save parsed data to file."""
        header = ['Date', 'Zone', 'AgeGroup', 'Count']
        date_list = sorted(self.info.keys())
        with open(file_name, 'w', encoding="utf-8") as fwriter:
            writer = csv.writer(fwriter)
            writer.writerow(header)
            for date in date_list:
                for zone in range(1, NUM_ZONES + 1):
                    for age, age_descr in AGE_GROUPS.items():
                        count = self.info[date][zone][age]
                        if count:
                            row = [date, zone, age_descr, count]
                            writer.writerow(row)
        print('Completed saving file.')


if __name__ == '__main__':
    nb = DataNB()
    nb.download(folder_name='data')
    nb.parse(folder_name='data', patch_name='patch.csv')
    nb.save(file_name='dataNB.csv')
