# -*- coding: utf-8 -*-            
# @Time : 2024/11/27 16:15
#  :harmione
# @FileName: 品种在不同熟期下的性状展示柱状图_2024.py
# @Software: PyCharm
import streamlit as st
import pandas as pd
import plotly.express as px

class CKTable:
    def __init__(self, query_statement):
        self.query_statement = query_statement
        self.data_df = self.__get_data_df()
        self.AOAname_list = self.__get_AOAname_list()

    def __get_data_df(self):
        # 连接并根据传来的查询语句获取对应的数据集
        conn = st.connection("postgres")
        self.data_df = conn.query(self.query_statement)
        return self.data_df

    def __get_AOAname_list(self):
        # 获取生态亚区数据
        AOAname_list = list(filter(None, pd.unique(self.data_df["AOA_S"]).tolist()))
        return AOAname_list

    def get_ck_name_list(self, selected_AOAname):
        # 根据生态亚区（AOA） 查询样本名称
        ck_name_list = list(filter(None, pd.unique(self.data_df[(self.data_df["AOA_S"] == selected_AOAname)
                                                   ]["VarNam"]).tolist()))  # 过滤掉None
        return ck_name_list


class PhenoTable:
    def __init__(self, query_statement):
        self.query_statement = query_statement
        self.data_df = self.__get_data_df()  # 直接获取了所有的数据

    def __get_data_df(self):
        # 连接并根据传来的查询语句获取对应的数据集
        conn = st.connection("postgres")
        data_df = conn.query(self.query_statement)
        return data_df

    def get_sample_name_list(self, selected_AOAname):
        # 根据熟期 找到对应样本的数据集【样本点为我们所谓的目标点，CK是测试点】
        sample_name_list = list(filter(None, pd.unique(self.data_df[(self.data_df["AOA_S"] == selected_AOAname)
                                                       ]["VarNam"]).tolist()))
        return sample_name_list

    def get_sample_data_df(self, selected_AOAname, selected_target_name_list):
        # 过滤选择Pheno表中样本的数据                                                      目标样本名的列表
        sample_pheno_df = self.data_df[(self.data_df["AOA_S"] == selected_AOAname) &
                                       (self.data_df["VarNam"].isin(selected_target_name_list))]
        return sample_pheno_df

    def get_ck_data_df(self, selected_AOAname, selected_ck_name_list):
        # 过滤选择Pheno的对照表中样本的数据                                         对照样本名的列表
        ck_pheno_df = self.data_df[(self.data_df["AOA_S"] == selected_AOAname) &
                                   (self.data_df["VarNam"].isin([selected_ck_name_list]))]
        return ck_pheno_df

    def get_all_data_df(self, sample_name, ck_name_list, aoa):
        sample_data_df = self.get_sample_data_df(aoa,sample_name )
        ck_data_df = self.get_ck_data_df(aoa,ck_name_list)
        all_data_df = pd.concat([sample_data_df, ck_data_df], axis=0)
        return all_data_df


class Plotter:
    def __init__(self, ckTable: CKTable, phenoTable: PhenoTable):
        # 构造函数 接受小ck和小pheno参数对象
        self.ckTable = ckTable
        self.phenoTable = phenoTable
        # 用于将形状名称转中文展示
        self.trait_column_name_to_chinese_name_dict = {'YLD14_TD': '产量(kg/亩)',
                                                       'KERTPCT_TD': '霉变粒率比例(%)',
                                                       'MST': '水分(%)',
                                                       'GLS': '灰斑病(等级)',
                                                       'CLB': '大斑病(等级)',
                                                       'STKRPCT_TD': '青枯病比例(%)',
                                                       'STKLPCT_TD': '茎倒比例(%)',
                                                       'EARTPCT_TD': '穗腐比例(%)',
                                                       'HUSKCOV': '苞叶覆盖度(等级)',
                                                       'KERSR': '结实性(等级)',
                                                       'TIPFILL': '秃尖(等级)'
                                                       }
        # 转为字典格式存储    汉字作为key，英文缩写作为value
        self.chinese_name_to_trait_column_name_dict = {v: k for (k, v) in
                                                       self.trait_column_name_to_chinese_name_dict.items()}

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

    def get_dropdown_menu_bar(self):
        # 设置生成下拉菜单栏
        # multiselect 可以选一个或多个
        # selectbox   只能从多选框中选一个

        column_list = st.columns((2, 3))  # 设置页面布局的宽度比例
        with column_list[0]:
            selected_AOAname = st.selectbox(
                '选择生态亚区',
                self.ckTable.AOAname_list
            )
        with column_list[1]:
            selected_trait_list = st.multiselect(
                '选择性状',
                self.trait_column_name_to_chinese_name_dict.values(),
                default=list(self.trait_column_name_to_chinese_name_dict.values())[0:3]  # 默认选择第一个
            )
        selected_trait_list = [self.chinese_name_to_trait_column_name_dict[selected_trait_column]
                                      for selected_trait_column in selected_trait_list]
        column_list = st.columns((1, 5))  # 设置页面布局的宽度比例
        with column_list[0]:
            selected_ck_name = st.selectbox(
                '选择对照品种',
                self.ckTable.get_ck_name_list(selected_AOAname)
            )
        with column_list[1]:
            selected_target_list = st.multiselect(
                '目标品种',
                self.phenoTable.get_sample_name_list(selected_AOAname),
                default=self.phenoTable.get_sample_name_list(selected_AOAname)[1:3]
            )

        return (selected_AOAname,selected_trait_list, selected_ck_name,selected_target_list)  # 返回选择的值

    def get_sample_data_df(self, AOAname_list, name_list, trait_column):
        data_df = self.phenoTable.data_df
        data_df = data_df[~pd.isna(data_df[trait_column])]
        sample_data_df = data_df[(data_df["AOA_S"]==AOAname_list)
                                 & data_df["VarNam"].isin(name_list)]
        return sample_data_df

    def plot(self):
        self.__get_title(title_content="测试品种在不同熟期下的性状展示（柱状图）_2024")
        selected_AOAname,selected_trait_list, selected_ck_name,selected_target_name_list=self.get_dropdown_menu_bar()
        for trait_name in selected_trait_list:
            sample_data_df = self.get_sample_data_df(selected_AOAname,selected_target_name_list, trait_name)
            ck_data_df = self.get_sample_data_df(selected_AOAname,[selected_ck_name], trait_name)
            if len(sample_data_df) == 0 or len(ck_data_df) == 0:
                continue
            all_data_df = pd.concat([ck_data_df,sample_data_df], axis=0)
            fig = px.bar(all_data_df, x='Location_TD', y=trait_name, color='CName', barmode='group'
                         ,
                         title=f"{trait_name.split('(')[0]}比较"
                         , color_discrete_sequence=px.colors.qualitative.D3)
            fig.update_layout(
                title={'y': 0.9,
                       'x': 0.53,
                       'xanchor': 'center',
                       'yanchor': 'top',
                       'font': dict(size=18)}  # 标题居中
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
                , margin=dict(t=150)
                , xaxis=dict(
                    title='测试地点'  # 横轴标题
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
                    title=trait_name  # 纵轴标题
                    , titlefont=dict(size=16, color='black')  # 标题字体大小
                    , showline=True  # 显示轴线
                    , linewidth=2  # 轴线宽度
                    , linecolor='black'  # 轴线颜色
                    , range=[all_data_df[trait_name].min() * 0.9, all_data_df[trait_name].max() * 1.05]
                    , automargin=True
                    , ticks='outside'  # 刻度线设置外侧
                    # , ticklen = 5  # 刻度线长度
                    , tickcolor='black'
                    , tickfont=dict(size=16, color='black')  # 坐标轴刻度字体大小
                )
            )
            fig.update_traces(hoverinfo='none', hovertemplate=None)
            st.plotly_chart(fig)
        st.markdown("""
                            ##### 注释：
                            - 下拉菜单：选择绘图使用的数据：
                                - “选择生态亚区（熟期）”、“选择性状”、“选择对照品种”、“选择目标品种”四个下拉菜单来指定想要查询的生态亚区和性状及对照和目标品种；
                            - 柱形图：展示测试品种在特定生态亚区（熟期）下与对照品种的性状对比：
                                - 横坐标为测试地点，纵坐标为性状；
                                - 每组柱状图中，蓝色标注的为对照品种，其它为测试目标品种。
                            """)


if __name__ == '__main__':
#def main():
    st.set_page_config(layout='wide')

    ck_query_statement = """
         select * from "DWS"."TDPheno2024" d
        """
    pheno_query_statement = """
           select * from "DWS"."TDPheno2024" d
           """
    ckTable = CKTable(ck_query_statement)
    phenoTable = PhenoTable(pheno_query_statement)
    streamlitPlotter = Plotter( ckTable, phenoTable)
    streamlitPlotter.plot()