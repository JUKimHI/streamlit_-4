import streamlit as st
import pandas as pd
import altair as alt
import plotly.express as px
import json

# 데이터 불러오기

df = pd.read_csv('./2023_시도별_지방세_구성비율_처리x.csv', encoding='UTF-8') # csv 파일 불러오기

#######################
# 데이터 전처리
df.drop(0, inplace=True) # 0번째 행(합계) 삭제
df.reset_index(drop=True, inplace=True) # 인덱스 재설정

# 연도 컬럼 리스트 (2018년부터 2023년까지)
year_columns = ['2018년_금액', '2019년_금액', '2020년_금액', '2021년_금액', '2022년_금액', '2023년_금액']

# 모든 연도 열에 대해 천 단위 구분기호(,)를 제거하고 숫자로 변환
for col in year_columns:
    df[col] = df[col].replace({',': ''}, regex=True)  # 천 단위 구분기호(,) 제거

df = df.melt(
    id_vars=['시도별'], 
    var_name='property', 
    value_name='tax',
)

df[['year', 'category']] = df['property'].str.split('년_', expand=True) # 속성을 연도와 구분으로 나누기
df.drop('property', axis=1, inplace=True) # 속성 열 삭제

# df['tax'] = df['tax'].str.replace(',', '').astype('float') # 세금을 쉼표를 삭제한 후 실수로 변환 (문자열 -> 실수)
df['tax'] = df['tax'].astype('float')
df['year'] = df['year'].astype('int') # 연도를 정수로 변환 (문자열 -> 정수)

df = df[['시도별', 'year', 'category', 'tax']] # 열 순서 변경

# 'category' 컬럼에서 '비중' 값을 제거
df = df[df['category'] != '비중']

# 인덱스 재정렬
df = df.reset_index(drop=True)

#######################

with st.sidebar:
    st.title('💸 지역별 지방세 그림으로 보기 💸')
    
    year_list = list(df.year.unique())[::-1]  # 연도 리스트를 내림차순으로 정렬
    
    selected_year = st.selectbox('연도 선택', year_list) # selectbox에서 연도 선택
    
    df_selected_year = df.query('year == @selected_year') # 선택한 연도에 해당하는 데이터만 가져오기
    df_selected_year_sorted = df_selected_year.sort_values(by="tax", ascending=False) # 선택한 연도에 해당하는 데이터를 세금을 기준으로 내림차순 정렬

#######################

# 다양한 plot과 시계열 분석
st.write('# 시도별 세금의 다양한 그림') # 제목

selected_plot = st.selectbox('plot 선택', ['bar','pie']) # selectbox에서 plot 선택

# 열 생성
col = st.columns(1)  # 1개의 열 생성

# bar, pie plot별 그림그리기
# bar plot
if selected_plot=='bar':
    with col[0]:
        st.write('# bar')
        def make_bar(input_df, input_x, input_y):
            bar = alt.Chart(input_df).mark_bar(size=40).encode(
                x=alt.X(f'{input_x}'),
                y=alt.Y(f'{input_y}')
            ).properties(
                width=550,
                height=500,
                title='시도별 세금'
            )
            return bar
        bar = make_bar(df_selected_year, '시도별', 'tax')
        st.altair_chart(bar, use_container_width=True)
# pie plot
if selected_plot=='pie':
    with col[0]:
        st.write('# pie')
        if selected_plot=='pie':
            fig = px.pie(df_selected_year,
                        values='tax',
                        names='시도별',
                        hole = 0.5,
                        title='시도별 세금')
            fig.update_traces(textposition='inside', textinfo='percent+label') # 텍스트 위치와 정보 추가
            st.plotly_chart(fig, use_container_width=True)

# 시계열 분석(line plot을 활용한한)
with col[0]:
    st.write('# 시계열 분석')
    fig2 = px.line(
        df,
        x = 'year', y = 'tax',
        color='시도별',
        height=500, width=100,
        template='gridon'
    )
    st.plotly_chart(fig2,use_container_width=True)