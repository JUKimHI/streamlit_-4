import streamlit as st
import pandas as pd
import altair as alt
import plotly.express as px
import json

#######################
# 페이지 설정
st.set_page_config(
    page_title="대한민국 지방세 변화 대시보드",
    page_icon="💸",
    layout="wide",
    initial_sidebar_state="expanded")

alt.themes.enable("dark")

#######################

# 데이터 불러오기
df = pd.read_csv('./2023_시도별_지방세_구성비율_처리x.csv', encoding='UTF-8') # csv 파일 불러오기

korea_geojson = json.load(open('./시도 경계.json', encoding="UTF-8")) # json 파일 불러오기

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

#######################

# 사이드바 설정

with st.sidebar:
    st.title('💸 대한민국 지방세 변화 대시보드')
    
    year_list = list(df.year.unique())[::-1]  # 연도 리스트를 내림차순으로 정렬
    category_list = list(df.category.unique())  # 카테고리 리스트
    
    selected_year = st.selectbox('연도 선택', year_list) # selectbox에서 연도 선택
    selected_category = st.selectbox('카테고리 선택', category_list) # selectbox에서 카테고리 선택

    df_selected_year = df.query('year == @selected_year & category == @selected_category') # 선택한 연도와 카테고리에 해당하는 데이터만 가져오기
    df_selected_year_sorted = df_selected_year.sort_values(by="tax", ascending=False) # 선택한 연도와 카테고리에 해당하는 데이터를 세금을을 기준으로 내림차순 정렬

    color_theme_list = ['blues', 'cividis', 'greens', 'inferno', 'magma', 'plasma', 'reds', 'rainbow', 'turbo', 'viridis']
    selected_color_theme = st.selectbox('컬러 테마 선택', color_theme_list)

#######################

# Heatmap 그래프
def make_heatmap(input_df, input_y, input_x, input_color, input_color_theme):
    heatmap = alt.Chart(input_df).mark_rect().encode(
            y=alt.Y(f'{input_y}:O', axis=alt.Axis(title="연도", titleFontSize=18, titlePadding=15, titleFontWeight=900, labelAngle=0)),
            x=alt.X(f'{input_x}:O', axis=alt.Axis(title="", titleFontSize=18, titlePadding=15, titleFontWeight=900)),
            color=alt.Color(f'max({input_color}):Q',
                             legend=None,
                             scale=alt.Scale(scheme=input_color_theme)),
            stroke=alt.value('black'),
            strokeWidth=alt.value(0.25),
        ).properties(width=900
        ).configure_axis(
        labelFontSize=12,
        titleFontSize=12
        ) 
    # height=300
    return heatmap

# Choropleth map
def make_choropleth(input_df, input_gj, input_column, input_color_theme):
    choropleth = px.choropleth_mapbox(input_df,
                               geojson=input_gj,
                               locations='시도별', 
                               featureidkey='properties.NAME',
                               mapbox_style='carto-darkmatter',
                               zoom=5, 
                               center = {"lat": 35.9, "lon": 126.98},
                               color=input_column, 
                               color_continuous_scale=input_color_theme,
                               range_color=(0, max(input_df.tax)),
                               labels={'tax':'세금', '시도별':'시도명'},
                               hover_data=['시도별', 'tax']
                              )
    choropleth.update_geos(fitbounds="locations", visible=False)
    choropleth.update_layout(
        template='plotly_dark',
        plot_bgcolor='rgba(0, 0, 0, 0)',
        paper_bgcolor='rgba(0, 0, 0, 0)',
        margin=dict(l=0, r=0, t=0, b=0),
        height=350
    )
    return choropleth

# 도넛 차트
def make_donut(input_response, input_text, input_color):
  if input_color == 'blue':
      chart_color = ['#29b5e8', '#155F7A']
  if input_color == 'green':
      chart_color = ['#27AE60', '#12783D']
  if input_color == 'orange':
      chart_color = ['#F39C12', '#875A12']
  if input_color == 'red':
      chart_color = ['#E74C3C', '#781F16']
    
  source = pd.DataFrame({
      "Topic": ['', input_text],
      "% value": [100-input_response, input_response]
  })
  source_bg = pd.DataFrame({
      "Topic": ['', input_text],
      "% value": [100, 0]
  })
    
  plot = alt.Chart(source).mark_arc(innerRadius=45, cornerRadius=25).encode(
      theta="% value",
      color= alt.Color("Topic:N",
                      scale=alt.Scale(
                          #domain=['A', 'B'],
                          domain=[input_text, ''],
                          # range=['#29b5e8', '#155F7A']),  # 31333F
                          range=chart_color),
                      legend=None),
  ).properties(width=130, height=130)
    
  text = plot.mark_text(align='center', color="#29b5e8", font="Lato", fontSize=32, fontWeight=700, fontStyle="italic").encode(text=alt.value(f'{input_response} %'))
  plot_bg = alt.Chart(source_bg).mark_arc(innerRadius=45, cornerRadius=20).encode(
      theta="% value",
      color= alt.Color("Topic:N",
                      scale=alt.Scale(
                          # domain=['A', 'B'],
                          domain=[input_text, ''],
                          range=chart_color),  # 31333F
                      legend=None),
  ).properties(width=130, height=130)
  return plot_bg + plot + text # 백그라운드, 차트, 텍스트를 합쳐서 그래프 생성

# Convert tax to text 
def format_number(num):
    if num > 1000000:
        if not num % 1000000:
            return f'{num // 1000000} M'
        return f'{round(num / 1000000, 1)} M'
    return f'{num // 1000} K'

# Calculation year-over-year tax migrations
def calculate_tax_difference(input_df, input_year, input_category):
  selected_year_data = input_df.query('year == @input_year & category == @input_category').reset_index()
  previous_year_data = input_df.query('year == @input_year-1 & category == @input_category').reset_index()
  selected_year_data['tax_difference'] = selected_year_data['tax'].sub(previous_year_data['tax'], fill_value=0)
  selected_year_data['tax_difference_abs'] = abs(selected_year_data['tax_difference'])
  return pd.concat([
    selected_year_data['시도별'], 
    selected_year_data['tax'], 
    selected_year_data['tax_difference'], 
    selected_year_data['tax_difference_abs']
    ], axis=1).sort_values(by='tax_difference', ascending=False)

#######################
# 대시보드 레이아웃
col = st.columns((1.5, 4.5, 2), gap='medium')

with col[0]: # 왼쪽
    st.markdown('#### 증가/감소')

    df_tax_difference_sorted = calculate_tax_difference(df, selected_year, selected_category)

    if selected_year > 2017:
        first_state_name = df_tax_difference_sorted.시도별.iloc[0]
        first_state_tax = format_number(df_tax_difference_sorted.tax.iloc[0])
        first_state_delta = format_number(df_tax_difference_sorted.tax_difference.iloc[0])
    else:
        first_state_name = '-'
        first_state_tax = '-'
        first_state_delta = ''
    st.metric(label=first_state_name, value=first_state_tax, delta=first_state_delta)

    if selected_year > 2017:
        last_state_name = df_tax_difference_sorted.시도별.iloc[-1]
        last_state_tax = format_number(df_tax_difference_sorted.tax.iloc[-1])   
        last_state_delta = format_number(df_tax_difference_sorted.tax_difference.iloc[-1])   
    else:
        last_state_name = '-'
        last_state_tax = '-'
        last_state_delta = ''
    st.metric(label=last_state_name, value=last_state_tax, delta=last_state_delta)

    
    st.markdown('#### 변동 시도 비율')

    if selected_year > 2017:
        # Filter states with tax difference > 5000
        # df_greater_50000 = df_tax_difference_sorted[df_tax_difference_sorted.tax_difference_absolute > 50000]
        df_greater_5000 = df_tax_difference_sorted[df_tax_difference_sorted.tax_difference > 5000]
        df_less_5000 = df_tax_difference_sorted[df_tax_difference_sorted.tax_difference < -5000]
        
        # % of States with tax difference > 5000
        states_migration_greater = round((len(df_greater_5000)/df_tax_difference_sorted.시도별.nunique())*100)
        states_migration_less = round((len(df_less_5000)/df_tax_difference_sorted.시도별.nunique())*100)
        donut_chart_greater = make_donut(states_migration_greater, '전입', 'green')
        donut_chart_less = make_donut(states_migration_less, '전출', 'red')
    else:
        states_migration_greater = 0
        states_migration_less = 0
        donut_chart_greater = make_donut(states_migration_greater, '전입', 'green')
        donut_chart_less = make_donut(states_migration_less, '전출', 'red')

    migrations_col = st.columns((0.2, 1, 0.2))
    with migrations_col[1]:
        st.write('증가')
        st.altair_chart(donut_chart_greater)
        st.write('감소')
        st.altair_chart(donut_chart_less)

with col[1]:
    st.markdown('#### ' + str(selected_year) + '년 ' + '세금'+str(selected_category))
    
    choropleth = make_choropleth(df_selected_year, korea_geojson, 'tax', selected_color_theme)
    st.plotly_chart(choropleth, use_container_width=True)
    
    heatmap = make_heatmap(df, 'year', '시도별', 'tax', selected_color_theme)
    st.altair_chart(heatmap, use_container_width=True)

with col[2]:
    st.markdown('#### 시도별 ' + str(selected_category))

    st.dataframe(df_selected_year_sorted,
                 column_order=("시도별", "tax"),
                 hide_index=True,
                 width=500,
                 column_config={
                    "시도별": st.column_config.TextColumn(
                        "시도명",
                    ),
                    "tax": st.column_config.ProgressColumn(
                        str(selected_category),
                        format="%f",
                        min_value=0,
                        max_value=max(df_selected_year_sorted.tax),
                     )}
                 )
    
    with st.expander('정보', expanded=True):
        st.write('''
            - 데이터: [지방재정 통합공개 시스템](https://www.lofin365.go.kr/portal/LF3131404.do/).
            - :orange[**증가/감소**]: 선택 연도에서 가장 많이 증가/감소한 시도 
            - :orange[**변동 시도 비율**]: 선택 연도에서 세금이 50억 이상 증가/감소한 시도의 비율
            - 증가/감소와 변동 시도 비율은 카테고리 금액에서만 의미 있음.(비중은 단위(%)가 작기때문)
            ''')