"""Visualization of NB and BC data.
"""

from pathlib import Path
import requests
import pandas as pd
import matplotlib.pyplot as plt
from data_nb import AGE_GROUPS, NUM_ZONES


class VisualNB():
    """Visual NB."""

    bc_url = 'http://www.bccdc.ca/Health-Info-Site/Documents/'
    bc_filename = 'BCCDC_COVID19_Dashboard_Case_Details.csv'
    age_groups_bc = {
        0: '<10', 10: '10-19', 20: '20-29', 30: '30-39', 40: '40-49', 50: '50-59',
        60: '60-69', 70: '70-79', 80: '80-89', 90: '90+', 100: 'Unknown'
    }
    dataframe_nb = None
    dataframe_bc = None

    def load(self, filename='dataNB.csv'):
        """Load the local NB data."""
        dataframe = pd.read_csv(filename)
        age_keys = {descr: val for val, descr in AGE_GROUPS.items()}
        dataframe['AgeKey'] = dataframe['AgeGroup'].apply(
            lambda x: age_keys[x])
        # Sum up zones
        df0 = dataframe.groupby(['Date', 'AgeKey'])['Count'].sum().rename('Count').reset_index()
        self.dataframe_nb = [df0]
        # Seperate zones
        for zone in range(1, NUM_ZONES + 1):
            df_sub = dataframe[dataframe['Zone'] ==
                               zone][['Date', 'AgeKey', 'Count']]
            self.dataframe_nb.append(df_sub)

    def plot(self, start='2020-01-01', end='2021-12-31'):
        """Plot graphs according to the local NB data."""
        # Show date range
        dataframe = self.dataframe_nb[0]
        df_truncated = dataframe[(dataframe['Date'] >= start) & (dataframe['Date'] <= end)]
        # Make bar plots by zones
        age_list = list(AGE_GROUPS.keys())
        age_descrs = list(AGE_GROUPS.values())
        fig_size_scale = 5
        num_row, num_col = 2, 4
        plt.figure(figsize=(fig_size_scale*num_col,
                   fig_size_scale*num_row))
        for zone, dataframe in enumerate(self.dataframe_nb):
            df_truncated = dataframe[(dataframe['Date'] >= start) & (
                dataframe['Date'] <= end)]
            age_count = []
            for age in AGE_GROUPS:
                total = df_truncated[df_truncated['AgeKey'] == age]['Count'].sum()
                age_count.append(total)
            fig_axes = plt.subplot(num_row, num_col, zone + 1)
            if zone == 0:
                fig_axes.bar(age_descrs, age_count, color='tab:orange', tick_label=age_list)
                fig_axes.set_title('All Zones')
            else:
                fig_axes.bar(age_descrs, age_count, color='tab:blue', tick_label=age_list)
                fig_axes.set_title(f'Zone {zone}')

    def download_bc(self, url=None, filename=None, overwrite=False):
        """Download BC data."""
        path = self._get_bc_file_path(filename)
        if overwrite is False and path.exists():  # Use existing BC file.
            return
        url = url or self.bc_url + self.bc_filename
        response = requests.get(url).content.decode('utf-8')
        with path.open("w", encoding="utf-8") as fwrite:
            fwrite.write(response)

    def load_bc(self, filename=None):
        """Load the local BC data."""
        path = self._get_bc_file_path(filename)
        dataframe = pd.read_csv(path)
        age_keys_bc = {descr: val for val, descr in self.age_groups_bc.items()}
        dataframe['AgeKey'] = dataframe['Age_Group'].apply(lambda x: age_keys_bc[x])
        dataframe_grouped = dataframe.groupby(['Reported_Date', 'AgeKey'])
        self.dataframe_bc = dataframe_grouped.size().rename('Count').reset_index()

    def _get_bc_file_path(self, filename):
        path = Path(filename) if filename else Path('__file__').parent / 'data' / self.bc_filename
        return path

    def plot_nb_bc(self, start='2020-01-01', end='2021-12-31'):
        """Plot garphs according to NB and BC data."""
        df_nb = self.dataframe_nb[0]
        df_nb_truncated = df_nb[(df_nb['Date'] >= start) & (df_nb['Date'] <= end)]
        df_bc = self.dataframe_bc
        df_bc_truncated = df_bc[(df_bc['Reported_Date'] >= start) & (df_bc['Reported_Date'] <= end)]
        first_date = min(df_nb_truncated.iloc[0]['Date'], df_bc_truncated.iloc[0]['Reported_Date'])
        last_date = max(df_nb_truncated.iloc[-1]['Date'], df_bc_truncated.iloc[-1]['Reported_Date'])
        print(f'From {first_date} to {last_date}')

        fig_size_scale = 5
        num_row_per_subplot, num_col_per_subplot = 1, 2
        plt.figure(figsize=(fig_size_scale*num_col_per_subplot, fig_size_scale*num_row_per_subplot))

        self._plot_nb(df_nb_truncated, num_row_per_subplot, num_col_per_subplot)
        self._plot_bc(df_bc_truncated, num_row_per_subplot, num_col_per_subplot)

    def _plot_nb(self, df_nb_truncated, num_row_per_subplot, num_col_per_subplot):
        age_descrs = list(AGE_GROUPS.values())
        age_count = []
        for age in AGE_GROUPS:
            total = df_nb_truncated[df_nb_truncated['AgeKey'] == age]['Count'].sum()
            age_count.append(total)
        fig_axes = plt.subplot(num_row_per_subplot, num_col_per_subplot, 1)
        fig_axes.bar(age_descrs, age_count, color='tab:orange', tick_label=age_descrs)
        fig_axes.set_xticklabels(fig_axes.get_xticklabels(), rotation=90)
        fig_axes.set_title('NB')

    def _plot_bc(self, df_bc_truncated, num_row_per_subplot, num_col_per_subplot):
        age_descrs_bc = list(self.age_groups_bc.values())
        age_count = []
        for age in self.age_groups_bc:
            total = df_bc_truncated[df_bc_truncated['AgeKey'] == age]['Count'].sum()
            age_count.append(total)
        fig_axes = plt.subplot(num_row_per_subplot, num_col_per_subplot, 2)
        fig_axes.bar(age_descrs_bc, age_count, color='tab:pink', tick_label=age_descrs_bc)
        fig_axes.set_xticklabels(fig_axes.get_xticklabels(), rotation=90)
        fig_axes.set_title('BC')


if __name__ == '__main__':
    vis = VisualNB()
    vis.load()
    vis.plot()
    vis.download_bc()
    vis.load_bc()
    vis.plot_nb_bc()
