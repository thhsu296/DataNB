import requests
import csv
import pandas as pd
import matplotlib.pyplot as plt
# from collections import defaultdict, Counter

class VisualNB():
    def __init__(self):
        self.ageGroups = {0: '<20', 20: '20-29', 30: '30-39', 40: '40-49', 50: '50-59',
                          60: '60-69', 70: '70-79', 80: '80-89', 90: '90+'}
        self.ageGroups_BC = {0: '<10', 10: '10-19', 20: '20-29', 30: '30-39', 40: '40-49', 50: '50-59',
                             60: '60-69', 70: '70-79', 80: '80-89', 90: '90+', 100: 'Unknown'}
        self.numZones = 7

    def load(self, fileName='dataNB.csv'):
        df = pd.read_csv(fileName)
        ageKeys = {descr: val for val,descr in self.ageGroups.items()}
        df['AgeKey'] = df['AgeGroup'].apply(lambda x: ageKeys[x])
        # Sum up zones
        df0 = df.groupby(['Date','AgeKey'])['Count'].sum().rename('Count').reset_index()
        self.dfZone = [df0]
        # Seperate zones
        for zone in range(1,self.numZones+1):
            df_sub = df[df['Zone']==zone][['Date','AgeKey','Count']]
            self.dfZone.append(df_sub)
        return None

    def plot(self, start='2020-01-01', end='2021-12-31'):
        # Show date range
        df = self.dfZone[0]
        df_truncated = df[(df['Date'] >= start) & (df['Date'] <= end)]
        first = df_truncated.iloc[0]['Date']
        last = df_truncated.iloc[-1]['Date']
        print(f'NB: from {first} to {last}')
        # Make bar plots by zones
        ageList = list(self.ageGroups.keys())
        ageDescrs = list(self.ageGroups.values())
        r = 5
        n, m = 2, 4
        plt.figure(figsize=(r*m,r*n))
        for k, df in enumerate(self.dfZone):
            df_truncated = df[(df['Date'] >= start) & (df['Date'] <= end)]
            arr = []
            for age in self.ageGroups:
                total = df_truncated[df_truncated['AgeKey']==age]['Count'].sum()
                arr.append(total)
            ax = plt.subplot(n,m,k+1)
            if k == 0:
                ax.bar(ageDescrs, arr, color='tab:orange', tick_label=ageList)
                ax.set_title('All Zones')
            else:
                ax.bar(ageDescrs, arr, color='tab:blue', tick_label=ageList)
                ax.set_title(f'Zone {k}')

    def download_BC(self, url='http://www.bccdc.ca/Health-Info-Site/Documents/BCCDC_COVID19_Dashboard_Case_Details.csv'):
        response = requests.get(url).content.decode('utf-8')
        filename = url.split('/')[-1]
        with open(filename, 'w') as f:
            f.write(response)
    
    def load_BC(self, fileName='BCCDC_COVID19_Dashboard_Case_Details.csv'):
        df = pd.read_csv(fileName)
        ageKeys_BC = {descr: val for val,descr in self.ageGroups_BC.items()}
        df['AgeKey'] = df['Age_Group'].apply(lambda x: ageKeys_BC[x])
        self.df_BC = df.groupby(['Reported_Date','AgeKey']).size().rename('Count').reset_index()

    def plot_BC(self, start='2020-01-01', end='2021-12-31'):
        # Show date range
        df_NB = self.dfZone[0]
        df_NB_truncated = df_NB[(df_NB['Date'] >= start) & (df_NB['Date'] <= end)]
        first_NB = df_NB_truncated.iloc[0]['Date']
        last_NB = df_NB_truncated.iloc[-1]['Date']
        df_BC = self.df_BC
        df_BC_truncated = df_BC[(df_BC['Reported_Date'] >= start) & (df_BC['Reported_Date'] <= end)]
        first_BC = df_BC_truncated.iloc[0]['Reported_Date']
        last_BC = df_BC_truncated.iloc[-1]['Reported_Date']
        first, last = min(first_NB, first_BC), max(last_NB, last_BC)
        print(f'From {first} to {last}')
        # Make bar plots
        r = 5
        n, m = 1, 2
        plt.figure(figsize=(r*m,r*n))
        # NB
        # ageList = list(self.ageGroups.keys())
        ageDescrs = list(self.ageGroups.values())
        arr = []
        for age in self.ageGroups:
            total = df_NB_truncated[df_NB_truncated['AgeKey']==age]['Count'].sum()
            arr.append(total)
        ax = plt.subplot(n,m,1)
        ax.bar(ageDescrs, arr, color='tab:orange', tick_label=ageDescrs)
        ax.set_xticklabels(ax.get_xticklabels(),rotation=90)
        ax.set_title('NB')
        # BC
        # ageList_BC = list(self.ageGroups_BC.keys())
        ageDescrs_BC = list(self.ageGroups_BC.values())
        arr = []
        for age in self.ageGroups_BC:
            total = df_BC_truncated[df_BC_truncated['AgeKey']==age]['Count'].sum()
            arr.append(total)
        ax = plt.subplot(n,m,2)
        ax.bar(ageDescrs_BC, arr, color='tab:pink', tick_label=ageDescrs_BC)
        ax.set_xticklabels(ax.get_xticklabels(),rotation=90)
        ax.set_title('BC')

if __name__ == '__main__':
    vis = VisualNB()
    vis.load()
    vis.plot()
    vis.download_BC()
    vis.load_BC()
    vis.plot_BC()