import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import time

from sklearn.model_selection import train_test_split, StratifiedKFold, GridSearchCV
from sklearn.preprocessing import MinMaxScaler, StandardScaler, PowerTransformer
from sklearn.ensemble import VotingClassifier
from sklearn.metrics import accuracy_score
from sklearn.preprocessing import LabelEncoder

from xgboost import XGBClassifier
from lightgbm import LGBMClassifier
from catboost import CatBoostClassifier

from sklearn.covariance import EllipticEnvelope

import warnings
warnings.filterwarnings('ignore')

# 1. Data preprocessing #

path = './medical_noshow.csv'
df = pd.read_csv(path)

df.AppointmentDay = pd.to_datetime(df.AppointmentDay).dt.date
df.ScheduledDay = pd.to_datetime(df.ScheduledDay).dt.date
df['PeriodBetween'] = df.AppointmentDay - df.ScheduledDay

# convert derived datetime to int
df['PeriodBetween'] = df['PeriodBetween'].dt.days

df['diseaseCount'] = df.Hipertension + df.Diabetes + df.Alcoholism

df = df.dropna(axis = 0)    # nan값을 가진 행 드랍

outliers = EllipticEnvelope(contamination=.1)      
# 이상치 탐지 모델 생성
outliers.fit(df[['Age']])      
# 이상치 탐지 모델 훈련
predictions = outliers.predict(df[['Age']])       
# 이상치 판별 결과
outlier_indices = np.where(predictions == -1)[0]    
# 이상치로 판별된 행의 인덱스를 추출
df.loc[outlier_indices, 'Age']  = np.nan    #이상치를 nan처리
# 데이터프레임에서 이상치 행을 삭제
print(df[df['PeriodBetween'] < 0])
df[df['PeriodBetween'] < 0] = np.nan    #이상치를 nan처리
df = df.fillna(np.nan)    #비어있는 데이터를 nan처리

df = df.dropna(axis = 0)    # nan값을 가진 행 드랍

# print(datasets.PeriodBetween.describe())
x = medical_noshow[['PatientId', 'AppointmentID', 'Gender',   'ScheduledDay', 
              'AppointmentDay', 'PeriodBetween', 'Age', 'Neighbourhood', 
              'Scholarship', 'diseaseCount', 'Hipertension', 'Diabetes', 'Alcoholism', 
              'Handcap', 'SMS_received']]
y = medical_noshow[['No-show']]

# print(x.info())
# print(y.info())

## 1-1. correlation hit map ##

sns.set(font_scale = 1)
sns.set(rc = {'figure.figsize':(12, 8)})
sns.heatmap(data = medical_noshow.corr(), square = True, annot = True, cbar = True)
plt.show()

## 1-2. drop useless data ##

x = x.drop(['PatientId', 'AppointmentID','ScheduledDay', 'Hipertension', 'Diabetes', 'Alcoholism'], axis=1)
print(x.describe())
# print(x.shape)

# print("이상치 정리 후\n",x.describe())
# print(x.shape, y.shape)

## 1-3. encoding object to int ##

encoder = LabelEncoder()

### char -> number
ob_col = list(x.dtypes[x.dtypes=='object'].index) ### data type이 object인 data들의 index를 ob_col 리스트에 저장
# print(ob_col)

for col in ob_col:
    x[col] = LabelEncoder().fit_transform(x[col].values)
y = LabelEncoder().fit_transform(y.values)

# print(x.describe())
# print('y:', y[0:8], '...')
# print(x.info())

## 1-4. fill na data ##

print(x.describe())

## 1-5. check dataset ##

print('head : \n',x.head(7))
print('y : ',y[0:7]) ### y : np.array

x_train, x_test, y_train, y_test = train_test_split(
    x, y, train_size=0.6, test_size=0.2, random_state=100, shuffle=True
)

scaler = PowerTransformer()
x_train = scaler.fit_transform(x_train)
x_test = scaler.transform(x_test)