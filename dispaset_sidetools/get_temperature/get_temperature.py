import pandas as pd

input_folder = '../../Inputs/'
output_folder = '../../Outputs/'

data = pd.read_csv(input_folder + 'temp_2016_land.csv')
data.drop(columns='Unnamed: 0', inplace=True)

date_str = '1/1/2016'
start = pd.to_datetime(date_str)
hourly_periods = 8784
drange = pd.date_range(start, periods=hourly_periods, freq='H')

data['date']=drange
data.set_index('date',drop=True,inplace=True)

# data.to_csv(output_folder + 'temp_2016.csv')


aa = pd.read_csv(output_folder + 'temp_2016.csv', index_col=0)