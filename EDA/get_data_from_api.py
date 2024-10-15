import pandas as pd
from datetime import date
from tqdm import tqdm
from datetime import timedelta
import warnings

warnings.filterwarnings("ignore")

def build_url(days):
   urls = []
   base_url = "https://data.sfgov.org/resource/wg3w-h783.csv?$where=report_datetime between '{0}' and '{1}' &$order=report_datetime DESC &$order=report_datetime DESC"
   # do it one time a day
   for i in range(2, days):
      start_day = pd.Timestamp(date.today() - timedelta(days = i))
      end_day = pd.Timestamp(date.today() - timedelta(days = i-1))
      base_url = base_url.format(start_day.date(), end_day.date())
      base_url = base_url.replace(" ","%20")
      base_url = base_url.replace("'","%27")
      urls.append(base_url)
   return urls


def getData(total_days=1500):
   # getting the connection to the database
   # connection = kwargs['connection']
   
   # getting the urls
   df = pd.DataFrame()
   urls = build_url(total_days)
   for url in tqdm(urls):
      day = pd.read_csv(url)
      df = pd.concat([df, day])

   # # selecting the columns
   # df = df[['incident_id', 'incident_description', 'incident_datetime', 'incident_day_of_week', 'incident_category', 'incident_subcategory', 'report_datetime', 'report_type_code','report_type_description', 'police_district', 'latitude', 'longitude', 'resolution']]
   #
   # # some transformations
   # df['incident_datetime'] = pd.to_datetime(df['incident_datetime'])
   # df['report_datetime'] = pd.to_datetime(df['report_datetime'])
   # df['incident_category'] = df['incident_category'].apply(str)
   # df['incident_subcategory'] = df['incident_subcategory'].apply(str)
   # df['incident_description'] = df['incident_description'].apply(lambda d: d.replace(',', '-') )
   # df['incident_category'] = df['incident_category'].apply(lambda d: d.replace(',', '-') )
   # df['incident_subcategory'] = df['incident_subcategory'].apply(lambda d: d.replace(',', '-') )
   # df['incident_category'].fillna('', inplace=True)
   # df['incident_subcategory'].fillna('', inplace=True)
   # df.drop_duplicates(inplace=True)
   # df.loc[df['incident_category']=='nan', ['incident_subcategory', 'incident_category']] = ''
   #
   # adding data to a staging table
   # if(len(df)>0):
   #    df.to_sql('crimes', connection, if_exists='replace', index=False )
   df.to_csv(f'../Data/crime_records_{total_days}.csv', index=False)


if __name__ == "__main__":
   getData()