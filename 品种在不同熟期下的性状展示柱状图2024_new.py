# -*- coding: utf-8 -*-            
# @Time : 2024/12/3 09:05
#  :harmione
# @FileName: 品种在不同暑期下的性状展示柱状图.py
# @Software: PyCharm

import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

class Plotter:
    def __init__(self, query_statement):
        # 构造函数
        self.query_statement = query_statement
        conn = st.connection("postgres")
        self.data_df = self.__get_data_df()
        self.year_list = self.__get_year_list()
        self.AOAname_list = self.__get_AOAname_list()
        self.trait_column_name_to_chinese_name_dict = {
                                                        'PMDPCT': '青枯病比例(%)',
                                                        'YLD14': '产量(kg/亩)',
                                                        'MST': '水分(%)',
                                                        'PHT': '株高(cm)',
                                                        'EHT': '穗位(cm)',
                                                        'ERTLPCT':'前倒(%)',
                                                        'GSPPCT':'茎折(%)',
                                                        'RSTSOU':'南方锈病(等级)',
                                                        'GLS': '灰斑病(等级)',
                                                        'CLB': '大斑病(等级)',
                                                        'KERTPCT': '霉变粒率比例(%)',
                                                       'STKLPCT': '茎倒比例(%)',
                                                       'EARTPCT': '穗腐比例(%)',
                                                       'HUSKCOV': '苞叶覆盖度(等级)',
                                                       'KERSR': '结实性(等级)',
                                                       'TIPFILL': '秃尖(等级)'
                                                       }
        # 转为字典格式存储    汉字作为key，英文缩写作为value
        self.chinese_name_to_trait_column_name_dict = {v: k for (k, v) in
                                                       self.trait_column_name_to_chinese_name_dict.items()}

    def __get_data_df(self):
        # 连接并根据传来的查询语句获取对应的数据集
        conn = st.connection("postgres")
        data_df = conn.query(self.query_statement)
        return data_df

    def __get_year_list(self):
        # 获取年份
        year_list = list(filter(None, pd.unique(self.data_df["Year"]).tolist()))
        return year_list

    def __get_AOAname_list(self):
        # 获取生态亚区数据
        AOAname_list = list(filter(None, pd.unique(self.data_df["EntryBookPrj"]).tolist()))
        return AOAname_list

    def get_EntryBookname_list(self,selected_AOAname,name_list):
        # 根据生态亚区和品种名 查询 区组
       entrybookname_list = list(filter(None, pd.unique(self.data_df[(self.data_df["EntryBookPrj"]==selected_AOAname) &
                                                                     (self.data_df["Varnam"].isin(name_list if isinstance(name_list, list) else [name_list]))]["EntryBookName"]).tolist()))
       return entrybookname_list

    def get_var_name_list(self, AOAname):
        # 根据生态亚区（AOA） 查询样本名称
        name_list = list(filter(None, pd.unique(self.data_df[
                                                    (self.data_df["EntryBookPrj"] == AOAname)
                                                   ]["Varnam"].tolist())))  # 过滤掉None
        return name_list

    def get_ck_name_list(self, AOAname, entrybookname,target_name_list):
        ck_name_list = list(filter(None, pd.unique(self.data_df[(self.data_df["EntryBookPrj"]==AOAname) &
                                                                     (self.data_df["EntryBookName"].isin(entrybookname if isinstance(entrybookname, list) else [entrybookname]))
                                                        ]["CK"]).tolist()))
        # 除去CKmean和在Varnam中没有数据的 ，只保留剩余的对照品种名。
        result_list=[]
        for name in ck_name_list:
            if self.data_df["Varnam"].isin([name]).any() and name != "CKmean":
                result_list.append(name)
        return result_list


    def get_use_data_df(self,AOAname,entrybookname,name_list, trait_name,years,types):
        # 获取经过条件筛选后的数据集，CK和目标品种的数据都从这获取，name_list有区别。
        data_df = self.data_df
        try:
            data_df = data_df[~pd.isna(data_df[trait_name])]
            result_data_df = data_df[(data_df["EntryBookPrj"] == AOAname)
                                     & (data_df["EntryBookName"].isin(entrybookname if isinstance(entrybookname, list) else [entrybookname]))
                                     & (data_df["Year"].isin(years if isinstance(years, list) else [years]))
                                     & (data_df["TrialType"].isin(types if isinstance(types, list) else [types]))
                                     & (data_df["Varnam"].isin(name_list if isinstance(name_list, list) else [name_list]))]
        except:
            result_data_df = pd.DataFrame()
        return result_data_df

    def get_dropdown_menu_bar(self):
        # 设置生成下拉菜单栏
        # multiselect 可以选一个或多个
        # selectbox   只能从多选框中选一个
        column_list = st.columns((1,1,1,1,3))  # 设置页面布局的宽度比例
        with column_list[0]:
            selected_data_type = st.selectbox(
                '数据类型',
                ['性状绝对值','性状相对值']
            )
        with column_list[1]:
            selected_years = st.selectbox(
                '年份',
                self.year_list,
            )
            if len(selected_years) == 0:
                selected_years = [self.year_list[0]]
        with column_list[2]:
            selected_AOAname = st.selectbox(
                '生态亚区',
                self.AOAname_list
            )
        # 选择试验类型
        available_types = list(filter(None, pd.unique(self.data_df["TrialType"]).tolist()))
        available_types.insert(0,"ALL")
        with column_list[3]:
            selected_types = st.multiselect('试验类型:',
                                            available_types,
                                            default="ALL")
        if 'ALL' in selected_types:
            selected_types = available_types[1:]
        with column_list[4]:
            selected_trait_list = st.multiselect(
                '性状',
                self.trait_column_name_to_chinese_name_dict.values(),
                default=list(self.trait_column_name_to_chinese_name_dict.values())[0]  # 默认选择第一个
            )
        selected_trait_list = [self.chinese_name_to_trait_column_name_dict[selected_trait_column]
                               for selected_trait_column in selected_trait_list]


        column_list = st.columns((3,2,3))  # 设置页面布局的宽度比例

        with column_list[0]:
            selected_tar_name_list = st.selectbox(
                '目标品种',
                self.get_var_name_list(selected_AOAname),
                #default=self.get_var_name_list(selected_AOAname)[1:3]
            )
        with column_list[1]:
            selected_entrybookname = st.selectbox(
                '区组',
                self.get_EntryBookname_list(selected_AOAname,selected_tar_name_list)
            )
        self.ck_name_list = self.get_ck_name_list(selected_AOAname,selected_entrybookname,selected_tar_name_list)
        with column_list[2]:
            selected_ck_name = st.selectbox(
                '对照品种',
                self.ck_name_list,
            )

        return (selected_data_type,selected_years,selected_AOAname,selected_types,selected_entrybookname,
                selected_ck_name, selected_tar_name_list,selected_trait_list)  # 返回选择的值

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

    def plot(self):
        self.__get_title(title_content="IBP测试品种在不同暑期下的性状展示柱状图_2024")
        selected_data_type, selected_years, selected_AOAname, selected_types, selected_entrybookname,selected_ck_name, selected_target_name, selected_trait_list = self.get_dropdown_menu_bar()
        for trait_name in selected_trait_list:
            # 判断 数据类型 和 是性状还是病害
            if trait_name in ["YLD14", "MST", "EHT", "PHT"]:
                if selected_data_type == "性状相对值":
                    trait_name = "CKpct_" + trait_name
                elif selected_data_type == "性状绝对值":
                    trait_name = "PredVal_" + trait_name
            else:
                if selected_data_type == "性状绝对值":
                    trait_name = "mean_" + trait_name
            #根据选择的条件，筛选数据集
            sample_data_df = self.get_use_data_df(selected_AOAname,selected_entrybookname,selected_target_name, trait_name,selected_years,selected_types)
            ck_data_df = self.get_use_data_df(selected_AOAname,selected_entrybookname,self.ck_name_list, trait_name,selected_years,selected_types)   # 获取的是几个ck所有的名字的整体数据

            if len(sample_data_df) == 0 or len(ck_data_df) == 0:
                continue
            BookName_list = list(filter(None, pd.unique(sample_data_df["BookName"]).tolist()))  # 获取地点的列表
            total_data_rows = []
            for bookname in BookName_list:
                trait_value_dict = {}
                if bookname == "All":
                    trait_value_dict["bookname"] = "总体平均"
                else:
                    trait_value_dict["bookname"] = pd.unique(sample_data_df[sample_data_df["BookName"] ==bookname]["LocationSelf"])[0]

                for ck_name in self.ck_name_list:
                    print(ck_name)
                    try:
                        trait_value_dict[ck_name] = pd.unique(ck_data_df[(ck_data_df["BookName"] == bookname) & (ck_data_df["Varnam"] == ck_name)& (ck_data_df["CK"] == selected_ck_name)][trait_name])[0]
                    except:
                        print(bookname +"没有对照"+ck_name+"的数据")
                        trait_value_dict[ck_name] = 0.0
                #for tar_name in selected_target_name_list:
                try:
                    trait_value_dict[selected_target_name] = pd.unique(sample_data_df[(sample_data_df["BookName"] ==bookname)&(sample_data_df["Varnam"] == selected_target_name) & (sample_data_df["CK"] == selected_ck_name)][trait_name])[0] # 该地点的目标品种的性状值
                except:
                    print(bookname +"没有目标"+selected_target_name+"的数据")
                    trait_value_dict[selected_target_name] = 0.0
                total_data_rows.append(trait_value_dict)
            total_data_df = pd.DataFrame(total_data_rows)

            color_list = self.ck_name_list + [selected_target_name]
            fig = px.bar(
                total_data_df,
                x='bookname',
                y=color_list,
                text_auto=True,
                barmode='group',
                title=f"{trait_name.split('(')[0]}比较",
                color_discrete_sequence=px.colors.qualitative.D3)
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
                    , titlefont=dict(size=18, color='black')  # 标题字体大小
                    , showline=True  # 显示轴线
                    , linewidth=2  # 轴线宽度
                    , linecolor='black'  # 轴线颜色
                    , tickfont=dict(size=16, color='black')  # 坐标轴刻度字体大小
                    , ticks='outside'  # 刻度线设置外侧
                    , tickcolor='black'
                    , ticklen=5
                    , tickformat = '.2f'  # 保留两位小数显示
                )
                , yaxis=dict(
                    title=trait_name  # 纵轴标题
                    , titlefont=dict(size=16, color='black')  # 标题字体大小
                    , showline=True  # 显示轴线
                    , linewidth=2  # 轴线宽度
                    , linecolor='black'  # 轴线颜色
                    , range=[total_data_df.iloc[:,1:].min().min() * 0.9, total_data_df.iloc[:,1:].max().max() * 1.05]
                    , automargin=True
                    , ticks='outside'  # 刻度线设置外侧
                    # , ticklen = 5  # 刻度线长度
                    , tickcolor='black'
                    , tickfont=dict(size=16, color='black')  # 坐标轴刻度字体大小
                    , tickformat='.2f',
                )
            )
            fig.update_traces( text=total_data_df.iloc[:,1:],  # 设置要显示在柱子上的标注
                textposition='inside',
                textfont_color='black',
                textfont_size=16,
            )
            st.plotly_chart(fig)

if __name__ == '__main__':
#def main():
    st.set_page_config(layout='wide')
    query_statement = """
                   with loc as (
                       select distinct 
                           li."Location",
                           li."BookName" as "LocBookName",  -- 使用别名避免冲突
                           coalesce(li."Location", li."BookName") as "LocationSelf"
                       from 
                           "DWS"."LocationInformationOri" li
                       where 
                           "Year" > 2022 and "BookPrj" <> 'TD' and "Location" != 'HLJSC'
                   )
                   select 
                       p.*, 
                       loc."Location", 
                       loc."LocBookName",  -- 使用别名避免冲突
                       loc."LocationSelf"
                   from 
                       "test"."ANOVA.Trial-PCM.EstimatedValue.EntryBookPrj" p 
                   left join 
                       loc on loc."LocBookName" = p."BookName"  -- 使用别名进行连接
                       --where p."EntryBookPrj" = 'BA';
                      """
    streamlitPlotter = Plotter(query_statement)
    streamlitPlotter.plot()
