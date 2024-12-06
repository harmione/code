# 优异品种（TD）性状展示
import numpy as np
import streamlit as st
import pandas as pd
import plotly.express as px


class CKPhenoSummaryTable:
    def __init__(self, table_schema, table_name):
        self.table_schema = table_schema  # TD试验对照信息表所在的schema
        self.table_name = table_name  # TD试验对照信息表名称
        self.without_outlier_ck_table_name = without_outlier_ck_table_name
        self.data_df = None  # 获取到的原始数据
        self.__get_sample_data_df()
        self.ck_unique_year_list = self.__get_unique_year_list()

    def __get_sample_data_df(self):
        conn = st.connection("postgres")
        self.data_df = conn.query(f"""
            with loc as (
                select distinct 
                    li."Location", 
                    li."BookName",
                    coalesce(li."Location",li."BookName") as "LocationSelf", 
                    li."Longitude",
                    li."Latitude"
                from 
                    "DWS"."LocationInformationOri" li
                where 
                    "Year" > 2022 and "BookPrj" <> 'TD' and "Location" !='HLJSC'
                ),
                sta as (
                    select distinct 
                        bpl."BookPrj",
                        bpl."SelfCNPrjName",
                        bpl."Longitude",
                        bpl."Latitude"
                    from 
                        "DWS"."BookPrjLocation" bpl 
                    where 
                        "Year" > 2022 and "BookPrj" <> 'TD'
                )
            select 
                loc."LocationSelf", 
                loc."BookName",
                loc."Longitude" as "LocationLongitude",
                loc."Latitude" as "LocationLatitude" ,
                sta."SelfCNPrjName" as "CNPrjName", 
                sta."Longitude" as "StationLongitude",
                sta."Latitude" as "StationLatitude",
                pc.* 
            from 
                "{self.table_schema}"."{self.table_name}" pc 
            left join loc on loc."BookName" = pc."BookName"
            left join sta on sta."BookPrj" = pc."BookPrj"
            where pc."BookPrj" not like '%TD%' and pc."BookName" =loc."BookName"
            order by loc."Latitude" desc ,sta."Latitude" desc
                """)
        self.data_df = self.data_df[(self.data_df['Trait'] == 'YLD14')]
        print(self.data_df)
        return self.data_df

    def __get_unique_year_list(self):
        ck_unique_year_list = pd.unique(self.data_df["Year"])
        return ck_unique_year_list

    def get_unique_station_name_list(self, year):
        data_df = self.data_df
        data_df = data_df[data_df["Year"] == year]
        # ck_unique_station_name_list = pd.unique(data_df["CNPrjName"]).tolist()
        ck_unique_station_name_list = pd.unique(
            data_df.sort_values(by="StationLatitude", ascending=False)["CNPrjName"]).tolist()
        return ck_unique_station_name_list

    def get_ck_name_list(self, year, station_name):
        data_df = self.data_df[(self.data_df["Year"] == year) & (self.data_df["CNPrjName"] == station_name)]
        data_df = data_df[pd.notnull(data_df["CV"])]
        ck_name_list = pd.unique(data_df["Varnam"]).tolist()
        return ck_name_list


class StreamlitPlotter:
    def __init__(self, CKPhenoSummaryTable, ck_table_name, without_outlier_ck_table_name):
        self.ck_table_name = ck_table_name
        self.without_outlier_ck_table_name = without_outlier_ck_table_name
        self.ckPhenoSummaryTable = CKPhenoSummaryTable(table_schema=ck_table_schema,
                                                       table_name=without_outlier_ck_table_name)
        self.data_df = self.ckPhenoSummaryTable.data_df
        self.ck_unique_year_list = self.ckPhenoSummaryTable.ck_unique_year_list

    def __init(self, is_delete_outliers="是"):
        if is_delete_outliers == "是":
            self.ckPhenoSummaryTable = CKPhenoSummaryTable(table_schema=ck_table_schema,
                                                           table_name=self.without_outlier_ck_table_name)
            self.data_df = self.ckPhenoSummaryTable.data_df
            self.ck_unique_year_list = self.ckPhenoSummaryTable.ck_unique_year_list
        else:
            self.ckPhenoSummaryTable = CKPhenoSummaryTable(table_schema=ck_table_schema,
                                                           table_name=self.ck_table_name)
            self.data_df = self.ckPhenoSummaryTable.data_df
            self.ck_unique_year_list = self.ckPhenoSummaryTable.ck_unique_year_list
        return is_delete_outliers

    def __select_box_layout(self):
        column_list = st.columns(5)
        with column_list[0]:
            is_delete_outliers = st.selectbox('是否去除异常值',
                                              ['是', '否'])
            self.__init(is_delete_outliers=is_delete_outliers)
        with column_list[1]:
            selected_year = st.selectbox('年份', sorted(list(self.ck_unique_year_list), reverse=True))
        with column_list[2]:
            selected_station = st.selectbox('育种站',self.ckPhenoSummaryTable.get_unique_station_name_list(selected_year))
        return selected_year, selected_station

    def __get_title(self, title_content):
        st.markdown(
            """
                <style>
                .custom-title {
                    font-size: 30px;
                    font-weight: bold;
                }
                </style>
            """
            , unsafe_allow_html=True)
        st.markdown(f'<p class = "custom-title">{title_content}</p>', unsafe_allow_html=True)
        return

    def __get_sub_tilte(self, tile):
        st.markdown(
            """
                <style>
                .custom-sub-title {
                    font-size: 21px;
                    font-weight: bold;
                }
                </style>
            """
            , unsafe_allow_html=True)
        st.markdown(f'<p class = "custom-sub-title">{tile}</p>', unsafe_allow_html=True)
        return tile

    def get_figure(self):
        self.__get_title("对照品种产量变异系数")
        selected_year, selected_station = self.__select_box_layout()
        ck_name_list = self.ckPhenoSummaryTable.get_ck_name_list(selected_year, selected_station)
        self.__get_sub_tilte("对照品种产量变异系数统计结果可视化")
        column_list = st.columns(2)
        index = 0
        for ck_name in ck_name_list:
            data_df = self.data_df[(self.data_df["Year"] == selected_year)
                                   & (self.data_df["CNPrjName"] == selected_station)
                                   & (self.data_df["Varnam"] == ck_name)]
            columns_to_check = [col for col in data_df.columns if col not in ['LocationLongitude', 'LocationLatitude']]
            data_df = data_df.drop_duplicates(subset=columns_to_check)
            location_order_list = pd.unique(
                data_df.sort_values(by="LocationLatitude", ascending=False)["LocationSelf"]).tolist()
            if len(data_df) > 0:
                with column_list[index % 2]:
                    # 创建分组柱状图
                    fig = px.bar(
                        data_df,
                        x='LocationSelf',
                        y='CV',
                        text_auto=False,
                        color='TrialType',
                        barmode='group',
                        hover_data={'LocationSelf': True, 'CV': True, 'TrialType': True, 'Obs': True},
                        category_orders={
                            "TrialType": ["TC1", "TC2", "P1", "P2", "P3", "P4", "TD1", "TD2"],
                            "LocationSelf": location_order_list
                        },
                        title=f"{selected_station} - {ck_name}",
                        color_discrete_sequence=px.colors.qualitative.D3
                    )
                    # 配置
                    fig.update_layout(
                        title={'y': 0.9
                               , 'x': 0.53
                               , 'xanchor': 'center'
                               , 'yanchor': 'top'
                               , 'font': dict(size=18)}  # 标题居中
                        , legend={
                            'orientation': 'h'
                            , 'yanchor': 'bottom'
                            , 'y': 1.02
                            , 'xanchor': 'center'
                            , 'x': 0.5
                            , 'font': dict(size=14)
                        }
                        , legend_title=None  # legend 不显示标题（legend的列名）
                        , hoverlabel=dict(
                            font_size=18  # 设置悬浮标签字体大小
                        )
                        , xaxis=dict(
                            title='测试点'  # 横轴标题
                            , titlefont=dict(size=16, color='black')  # 标题字体大小
                            , showline=True  # 显示轴线
                            , linewidth=2  # 轴线宽度
                            , linecolor='black'  # 轴线颜色
                            , tickfont=dict(size=16, color='black')  # 坐标轴刻度字体大小
                            , ticks='outside'  # 刻度线设置外侧
                            , tickcolor='black'
                            , ticklen=5
                        )
                        , yaxis=dict(
                            title="变异系数（%）"  # 纵轴标题
                            , titlefont=dict(size=16, color='black')  # 标题字体大小
                            , showline=True  # 显示轴线
                            , linewidth=2  # 轴线宽度
                            , linecolor='black'  # 轴线颜色
                            , automargin=True
                            , ticks='outside'  # 刻度线设置外侧
                            # , ticklen = 5  # 刻度线长度
                            , tickcolor='black'
                            , tickfont=dict(size=16, color='black')  # 坐标轴刻度字体大小
                            , autorange=True
                            , dtick =5
                        )
                    )
                    # 更新悬停模版
                    fig.update_traces(#text=data_df['CV'],  # 设置要显示在柱子上的标注
                                      #textposition='inside',
                                      # textfont_color='black',
                                      # hovertemplate="观测数: %{customdata[1]}<extra></extra>"
                                      hovertemplate="<b>%{x}</b><br>变异系数: %{y:.2f}%<br>试验类型: %{customdata[0]}<br>观测数: %{customdata[1]}<extra></extra>"
                                      )
                    st.plotly_chart(fig)
                index += 1
        self.__get_sub_tilte("对照品种产量变异系数统计结果")
        data_df = self.data_df[(self.data_df["Year"] == selected_year) & (self.data_df["CNPrjName"] == selected_station)]
        data_df = data_df[["Year", "CNPrjName", "LocationSelf", "TrialType", "Varnam", "Obs", "CV"]]
        data_df.columns = ["年份", "育种站", "测试点", "试验类型", "对照品种名称", "观测数", "变异系数（%）"]
        data_df["年份"] = data_df["年份"].astype(str)
        st.dataframe(data_df, hide_index=True)
        st.markdown("""
                ##### 注释：
                - 下拉菜单：
                    - 是否去除异常值： 如果选择是，将会使用去除异常值后的数据计算变异系数，反之则使用原始数据计算变异系数；
                - 柱状图：展示不同测试点和不同试验类型下，对照品种的变异系数情况（变异系数越高，说明试验环境之间差异越大，比如：土壤肥力、气候、
                    种子纯度等）
                    - 纵坐标：变异系数 = （标准差 / 均值） * 100%
                """)
        return


if __name__ == '__main__':
    st.set_page_config(layout='wide')
    ck_table_schema = 'DWS'
    ck_table_name = 'CKPhenoCV'
    without_outlier_ck_table_name = 'CKPhenoCVWithoutOutlier'
    streamlitPlotter = StreamlitPlotter(CKPhenoSummaryTable, ck_table_name, without_outlier_ck_table_name)
    streamlitPlotter.get_figure()

