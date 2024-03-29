#!/usr/bin/env python
# coding: utf-8
import numpy as np
import pandas as pd
from keras.models import Sequential
from keras.layers import Dense, Dropout
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score
import time

from sklearn.covariance import EllipticEnvelope
from sklearn.preprocessing import LabelEncoder

import warnings
warnings.filterwarnings('ignore')

# 1. Data preprocessing #

path = '../medical_noshow.csv'
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
#  원 핫 인코딩 개념을 이용해서 핸드캡을 범주형 데이터로 변환
Handicap = pd.get_dummies(df['Handcap'], prefix = 'Handicap')
# 핸드캡 칼럼을 핸디캡 더미 변수로 변환(변수명에 i만 추가됨 주의)
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
##### 전처리 완료 #####



##### 훈련 구성 시작 #####
x_train, x_test, y_train, y_test = train_test_split(
x, y, test_size = 0.2, shuffle=True, random_state=42
)
print(x_train.shape, y_train.shape)
print(x_test.shape, y_test.shape)

##### 모델 구성 ##### 
# ver 4 기준 입력층:linear, 은닉층:relu *2 에서 최상
# ver 5 에서는 노드 수와 Dropout 추가해서 최적화 해볼 것
model = Sequential()
model.add(Dense(16, input_dim=16, activation='linear'))
model.add(Dropout(0.2))
model.add(Dense(64, activation='relu'))
model.add(Dropout(0.2))
model.add(Dense(64, activation='relu'))
model.add(Dense(1, activation='sigmoid')) 

# 컴파일, 훈련
model.compile(loss='binary_crossentropy', 
              optimizer='adam', 
              metrics=['accuracy'])

##earlyStopping
from keras.callbacks import EarlyStopping, ModelCheckpoint
earlyStopping = EarlyStopping(monitor='val_loss', patience=32, mode='min',
                              verbose=1, restore_best_weights=True ) # restore_best_weights의 기본값은 false이므로 true로 반드시 변경

# Model Check point
mcp = ModelCheckpoint(
    monitor='val_loss',
    mode='auto',
    verbose=1,
    save_best_only=True,
    filepath='./mcp/noshow_ver5_layer2_bat32_input16_hidden64_dropout20.hdf5'
    ######################################
    # 훈련전에 mcp파일 명 변경 잊지 말기!! #
    ######################################
)

batch_size=32
start_time = time.time()
model.fit(x_train, y_train, epochs=500, batch_size=batch_size, 
          validation_split=0.2, 
          callbacks=[earlyStopping, mcp],
          verbose=1)
end_time = time.time() - start_time

loss, acc = model.evaluate(x_test, y_test)

model.summary()
print('소요시간 : ', end_time)
print('batch_size : ', batch_size)
print('loss : ', loss)
print('acc : ', acc)
print('noShow MLP')

# y_pred = model.predict(x_test)
# y_test['noshowPred'] = y_pred
# print(y_test.head())

# Epoch 00071: val_loss did not improve from 0.05350
# 1106/1106 [==============================] - 4s 4ms/step - loss: 0.0503 - accuracy: 0.9734 - val_loss: 0.0551 - val_accuracy: 0.9721
# Epoch 00071: early stopping
# 691/691 [==============================] - 2s 3ms/step - loss: 0.0522 - accuracy: 0.9725
# Model: "sequential"
# _________________________________________________________________
# Layer (type)                 Output Shape              Param #
# =================================================================
# dense (Dense)                (None, 16)                272       
# _________________________________________________________________
# dense_1 (Dense)              (None, 32)                544
# _________________________________________________________________
# dense_2 (Dense)              (None, 32)                1056
# _________________________________________________________________
# dense_3 (Dense)              (None, 1)                 33
# =================================================================
# Total params: 1,905
# Trainable params: 1,905
# Non-trainable params: 0
# _________________________________________________________________
# batch_size :  32
# loss :  0.052245061844587326
# acc :  0.9724936485290527 # ver4 기준 최적 모델
# 소요시간 :  345.04135298728943

# Epoch 00078: val_loss did not improve from 0.05525
# 2211/2211 [==============================] - 10s 4ms/step - loss: 0.0547 - accuracy: 0.9710 - val_loss: 0.0557 - val_accuracy: 0.9705
# Epoch 00078: early stopping
# 691/691 [==============================] - 2s 3ms/step - loss: 0.0530 - accuracy: 0.9695
# Model: "sequential"
# _________________________________________________________________
# Layer (type)                 Output Shape              Param #
# =================================================================
# dense (Dense)                (None, 16)                272       
# _________________________________________________________________
# dense_1 (Dense)              (None, 32)                544
# _________________________________________________________________
# dropout (Dropout)            (None, 32)                0
# _________________________________________________________________
# dense_2 (Dense)              (None, 32)                1056
# _________________________________________________________________
# dense_3 (Dense)              (None, 1)                 33
# =================================================================
# Total params: 1,905
# Trainable params: 1,905
# Non-trainable params: 0
# _________________________________________________________________
# batch_size :  32
# loss :  0.053008805960416794
# acc :  0.969462513923645
# 소요시간 :  744.7154424190521

# Epoch 00051: val_loss did not improve from 0.05630
# 2211/2211 [==============================] - 10s 5ms/step - loss: 0.0587 - accuracy: 0.9699 - val_loss: 0.0569 - val_accuracy: 0.9659
# Epoch 00051: early stopping
# 691/691 [==============================] - 2s 3ms/step - loss: 0.0547 - accuracy: 0.9694
# Model: "sequential"
# _________________________________________________________________
# Layer (type)                 Output Shape              Param #
# =================================================================
# dense (Dense)                (None, 16)                272
# _________________________________________________________________
# dense_1 (Dense)              (None, 32)                544
# _________________________________________________________________
# dropout (Dropout)            (None, 32)                0
# _________________________________________________________________
# dense_2 (Dense)              (None, 32)                1056
# _________________________________________________________________
# dropout_1 (Dropout)          (None, 32)                0
# _________________________________________________________________
# dense_3 (Dense)              (None, 32)                1056
# _________________________________________________________________
# dense_4 (Dense)              (None, 1)                 33
# =================================================================
# Total params: 2,961
# Trainable params: 2,961
# Non-trainable params: 0
# _________________________________________________________________
# batch_size :  32
# loss :  0.054687727242708206
# acc :  0.9694172739982605
# 소요시간 :  515.9504854679108

# model = Sequential()
# model.add(Dense(32, input_dim=16, activation='linear'))
# model.add(Dense(64, activation='relu'))
# model.add(Dense(64, activation='relu'))
# model.add(Dense(1, activation='sigmoid')) 
# Epoch 00088: val_loss did not improve from 0.05436
# 2211/2211 [==============================] - 9s 4ms/step - loss: 0.0485 - accuracy: 0.9746 - val_loss: 0.0563 - val_accuracy: 0.9705
# Epoch 00088: early stopping
# 691/691 [==============================] - 2s 3ms/step - loss: 0.0528 - accuracy: 0.9712
# batch_size :  32
# loss :  0.052751485258340836
# acc :  0.9712269306182861 # 과적합으로 인해 결과 하락
# 소요시간 :  803.8933537006378

# model = Sequential()
# model.add(Dense(32, input_dim=16, activation='linear'))
# model.add(Dense(64, activation='relu'))
# model.add(Dropout(0.2))
# model.add(Dense(64, activation='relu'))
# model.add(Dense(1, activation='sigmoid')) 
# Epoch 00156: val_loss did not improve from 0.05311
# 2211/2211 [==============================] - 10s 4ms/step - loss: 0.0519 - accuracy: 0.9727 - val_loss: 0.0543 - val_accuracy: 0.9726
# Epoch 00156: early stopping
# 691/691 [==============================] - 2s 3ms/step - loss: 0.0515 - accuracy: 0.9734
# batch_size :  32
# loss :  0.05150332674384117
# acc :  0.9733985066413879
# 소요시간 :  1411.1894390583038

# model = Sequential()
# model.add(Dense(64, input_dim=16, activation='linear'))
# model.add(Dense(128, activation='relu'))
# model.add(Dropout(0.2))
# model.add(Dense(128, activation='relu'))
# model.add(Dense(1, activation='sigmoid')) 
# Epoch 00096: val_loss did not improve from 0.05353
# 2211/2211 [==============================] - 9s 4ms/step - loss: 0.0519 - accuracy: 0.9727 - val_loss: 0.0545 - val_accuracy: 0.9727
# Epoch 00096: early stopping
# 691/691 [==============================] - 2s 3ms/step - loss: 0.0519 - accuracy: 0.9729
# 소요시간 :  900.7635307312012
# batch_size :  32
# loss :  0.05189896374940872
# acc :  0.9728555679321289

# model = Sequential()
# model.add(Dense(32, input_dim=16, activation='linear'))
# model.add(Dense(128, activation='relu'))
# model.add(Dropout(0.2))
# model.add(Dense(128, activation='relu'))
# model.add(Dense(1, activation='sigmoid')) 
# Epoch 00085: val_loss did not improve from 0.05410
# 2211/2211 [==============================] - 9s 4ms/step - loss: 0.0514 - accuracy: 0.9731 - val_loss: 0.0562 - val_accuracy: 0.9722
# Epoch 00085: early stopping
# 691/691 [==============================] - 2s 3ms/step - loss: 0.0516 - accuracy: 0.9727
# 소요시간 :  784.7384386062622
# batch_size :  32
# loss :  0.05160897597670555
# acc :  0.9726746082305908

# model = Sequential()
# model.add(Dense(64, input_dim=16, activation='linear'))
# model.add(Dense(64, activation='relu'))
# model.add(Dropout(0.2))
# model.add(Dense(64, activation='relu'))
# model.add(Dense(1, activation='sigmoid')) 
# Epoch 00107: val_loss did not improve from 0.05329
# 2211/2211 [==============================] - 9s 4ms/step - loss: 0.0519 - accuracy: 0.9728 - val_loss: 0.0541 - val_accuracy: 0.9718
# Epoch 00107: early stopping
# 691/691 [==============================] - 2s 3ms/step - loss: 0.0520 - accuracy: 0.9730
# 소요시간 :  995.503630399704
# batch_size :  32
# loss :  0.05195314437150955
# acc :  0.9729912877082825

# model = Sequential()
# model.add(Dense(64, input_dim=16, activation='linear'))
# model.add(Dropout(0.2))
# model.add(Dense(64, activation='relu'))
# model.add(Dropout(0.2))
# model.add(Dense(64, activation='relu'))
# model.add(Dense(1, activation='sigmoid')) 
# Epoch 00076: val_loss did not improve from 0.05301
# 2211/2211 [==============================] - 9s 4ms/step - loss: 0.0525 - accuracy: 0.9721 - val_loss: 0.0543 - val_accuracy: 0.9727
# Epoch 00076: early stopping
# 691/691 [==============================] - 2s 3ms/step - loss: 0.0518 - accuracy: 0.9730
# 소요시간 :  714.9711000919342
# batch_size :  32
# loss :  0.05183543637394905
# acc :  0.9729912877082825

# model = Sequential()
# model.add(Dense(16, input_dim=16, activation='linear'))
# model.add(Dropout(0.2))
# model.add(Dense(64, activation='relu'))
# model.add(Dropout(0.2))
# model.add(Dense(64, activation='relu'))
# model.add(Dense(1, activation='sigmoid')) 
# Epoch 00157: val_loss did not improve from 0.05229
# 2211/2211 [==============================] - 10s 4ms/step - loss: 0.0531 - accuracy: 0.9715 - val_loss: 0.0530 - val_accuracy: 0.9723
# Epoch 00157: early stopping
# 691/691 [==============================] - 2s 3ms/step - loss: 0.0511 - accuracy: 0.9736
# 소요시간 :  1574.3082158565521
# batch_size :  32
# loss :  0.05109154060482979
# acc :  0.9736247062683105