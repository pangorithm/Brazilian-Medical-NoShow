import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import time
import warnings

from sklearn.svm import SVC, LinearSVC
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score, cross_val_predict
from sklearn.preprocessing import MinMaxScaler, LabelEncoder
from sklearn.covariance import EllipticEnvelope

warnings.filterwarnings('ignore')

# Data preprocessing #

path = './medical_noshow.csv'
df = pd.read_csv(path)
# CSV 파일을 읽어와서 DataFrame으로 저장

# print(medical_noshow.columns)
# print(medical_noshow.head(10))

print('Count of rows', str(df.shape[0]))
print('Count of Columns', str(df.shape[1]))
# 데이터프레임의 크기와 칼럼의 수를 출력

df = df.fillna(np.nan)  # 결측값 nan으로 채우기

for column_name in df.columns:
    print(column_name+":",len(df[column_name].unique()))
# 데이터프레임의 각 칼럼에 대해 유일한 값의 수를 출력

df['ScheduledDay'] = pd.to_datetime(df['ScheduledDay']).dt.date
df['AppointmentDay'] = pd.to_datetime(df['AppointmentDay']).dt.date
# 'ScheduledDay' 칼럼과 'AppointmentDay' 열을 날짜 형식으로 변환

df['Day_diff'] = (df['AppointmentDay'] - df['ScheduledDay']).dt.days
# 'Day_diff' 칼럼을 생성하여 약속 일자와 예약 일자의 차이를 계산
print("Day_diff값 목록 \n",df['Day_diff'].unique())
# Day_diff' 칼럼의 유일한 값을 출력
print(df[df['Day_diff']<0]['No-show'])
# Day_diff<0 인 데이터는 노쇼로 처리했음을 확인

df.info()
print(df['No-show'][0:10])
# 각 컬럼의 데이터 타입 확인
ob_col = list(df.dtypes[df.dtypes=='object'].index) 
### data type이 object인 data들의 index를 ob_col 리스트에 저장
for col in ob_col:
    df[col] = LabelEncoder().fit_transform(df[col].values)
# object인 데이터를 숫자형 데이터로 변환
df.info()
print(df['No-show'][0:10])
# [ no : 0, yes : 1 ]으로 정수화 되었음을 확인
# 각 컬럼의 데이터 타입 확인

df['PreviousApp'] = df.groupby(['PatientId']).cumcount()
# 'PatientId'가 같은 데이터끼리 그룹으로 묶어서 개수를 카운트 -> 각 환자별 이전 약속 수를 계산
# 이 값으로 'PreviousApp' 열을 생성

df['PreviousNoShow'] = (df[df['PreviousApp'] > 0].groupby(['PatientId'])['No-show'].cumsum() / df[df['PreviousApp'] > 0]['PreviousApp'])
# 이전에 예약한 기록이 있는 환자들만 선택,
# 'PatientId'가 같은 데이터끼리 그룹으로 묶어서 환자별로 고려,
# 이전에 noShow한 횟수의 합/이전에 예약한 횟수 = 해당 환자의 noShow 비율 계산
# 'PreviousNoShow' 칼럼을 생성하여 이전 약속에서의 No-show 비율 칼럼 생성

df['PreviousNoShow'] = df['PreviousNoShow'].fillna(0)
# 'PreviousNoShow' 칼럼의 NaN 값을 0으로 채운다. 
# 즉, 첫 예약자는 이전에 noShow 안한것으로 간주

# Number of Appointments Missed by Patient
df['Num_App_Missed'] = df.groupby('PatientId')['No-show'].cumsum()
# 'PatientId'가 같은 데이터끼리 그룹으로 묶어서 환자별로 고려,
# 'Num_App_Missed' 각 환자별 누적 No-show 수를 계산한 칼럼을 생성


# print("handcap 종류 : ",df['Handcap'].unique())
df['Handcap'] = pd.Categorical(df['Handcap'])
# 핸드캡을 범주형 데이터로 변환
Handicap = pd.get_dummies(df['Handcap'], prefix = 'Handicap')
# 핸드캡 칼럼을 핸디캡 더미 변수로 변환
# prefix='Handicap'는 생성된 더미 변수의 이름에 'Handicap' 접두사를 붙이도록 지정
df = pd.concat([df, Handicap], axis=1)
# 데이터 프레임에 핸디캡 변수를 추가, 데이터 프레임을 열방향으로 병합
df.drop(['Handcap','ScheduledDay','AppointmentDay', 'AppointmentID','PatientId','Neighbourhood'], axis=1, inplace=True)
# 불필요한 칼럼 삭제, inplace=True 파라미터를 통해 원본 데이터프레임 수정
print(df.describe())

df = df[(df.Age >= 0) & (df.Age <= 100)]
df.info()
# 'Age' 열의 값이 0 이상 100 이하인 행만 선택 # 이외의 값은 이상치로 판정

x = df.drop(['No-show'], axis=1)
y = df['No-show']
from sklearn.preprocessing import MinMaxScaler
scaler = MinMaxScaler()
x = scaler.fit_transform(x)
# Min-Max 스케일링을 사용하여 특성 값을 0과 1 사이로 조정
##### Complete Data Preprocessing #####

x_train, x_test, y_train, y_test = train_test_split(
    x, y, test_size=0.2, shuffle=True, random_state=77
)

### kfold ###
n_splits = 5
random_state = 42
kfold = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=random_state)

scaler = MinMaxScaler()
scaler.fit(x_train)
x_train = scaler.transform(x_train)
x_test = scaler.transform(x_test)

param = [
    {'n_estimators': [100,200], 'learning_rate' : [0.1, 0.01, 0.2],
     'max_depth' : [2,3], 'gamma': [0,1,2],
     'min_child_weight': [0.01,0.01,0.1], 'subsample' : [0.1,0.2],
     'colsample_bytree' : [0.1,0.2], 'colsample_bylevel' : [0.1,0.2],
     'colsample_bynode' : [0.1,0.2], 'reg_alpha' : [0.1,0.01],
     'reg_lambda' : [0.1,0.01]}   
        ]

#2. 모델구성
from xgboost import XGBClassifier
from sklearn.model_selection import GridSearchCV
rf_model = XGBClassifier()
model = GridSearchCV(rf_model, param, cv=kfold, verbose=1,
                     refit=True, n_jobs=-1)

#3. 훈련
import time
start_time = time.time()
model.fit(x_train, y_train)
end_time = time.time() - start_time

print('최적의 파라미터 : ', model.best_params_)
print('최적의 매개변수 : ', model.best_estimator_)
print('베스트 스코어 : ', model.best_score_)
print('모델 스코어 : ', model.score(x_test, y_test))
print('걸린 시간 : ', end_time, '초')
print('XGBoost -> GridSearchCV')

##1. 
# 최적의 파라미터 :  {'min_samples_leaf': 5, 'n_estimators': 100}
# 최적의 매개변수 :  RandomForestClassifier(min_samples_leaf=5)
# 베스트 스코어 :  0.9583333333333334
# 모델 스코어 :  0.9666666666666667
# 걸린 시간 :  6.060913324356079 초

##2. 그리드서치 다 넣었을 때 값
# 최적의 파라미터 :  {'min_samples_leaf': 3, 'n_estimators': 100}
# 최적의 매개변수 :  RandomForestClassifier(min_samples_leaf=3)
# 베스트 스코어 :  0.975
# 모델 스코어 :  0.9666666666666667
# 걸린 시간 :  10.51404595375061 초

##3.
# 최적의 파라미터 :  {'max_depth': 6, 'min_samples_split': 10}
# 최적의 매개변수 :  RandomForestClassifier(max_depth=6, min_samples_split=10)
# 베스트 스코어 :  0.9666666666666668
# 모델 스코어 :  0.9666666666666667
# 걸린 시간 :  16.38246512413025 초

# #4. 출력(평가, 예측)

# result = model.score(x_test, y_test)
# print('acc : ', result)

# score = cross_val_score(model, x_train, y_train, cv=kfold)   # cv='cross validation'
# print('cv acc : ', score)

# y_predict = cross_val_predict(model, x_test, y_test, cv=kfold)
# print('cv pred : ', y_predict)

# acc = accuracy_score(y_test, y_predict)
# print('cv pred acc : ', acc)