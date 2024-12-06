# -*- coding: utf-8 -*-            
# @Time : 2024/11/29 08:32
#  :harmione
# @FileName: TD性状透视图.py
# @Software: PyCharm
from email.policy import default
from random import sample

import numpy as np
import streamlit as st
import pandas as pd

class Plotter:
    def __init__(self,query_statement):
        self.query_statement = query_statement
        self.data_df = self.__get_data_df()
        self.AOAname_list = self.__get_AOAname_list()
        self.trait_column_name_to_chinese_name_dict = {'YLD14_TD': '产量(kg/亩)',
                                                       'KERTPCT_TD': '霉变粒率比例(%)',
                                                       'MST': '水分(%)',
                                                       'GLS': '灰斑病(等级)',
                                                       'CLB': '大斑病(等级)',
                                                       'STKRPCT_TD': '青枯病比例(%)',
                                                       'PHT': '株高(cm)',
                                                       'EHT': '穗位(cm)',
                                                       'STKLPCT_TD': '茎倒比例(%)',
                                                       'TDPPCT_TD': '倒伏倒折比例(%)',
                                                       'BARPCT_TD': '空杆比例(%)',
                                                       'EARTPCT_TD': '穗腐比例(%)',
                                                       'HUSKCOV': '苞叶覆盖度(等级)',
                                                       'KERSR': '结实性(等级)',
                                                       'TIPFILL': '秃尖(等级)',
                                                       'RSTCOM': '普通锈病(等级)',
                                                       'CULSPT': '弯孢叶斑病(等级)',
                                                       'STAGRN': '持绿性(等级)',
                                                       'SHBLSC': '纹枯病(等级)',
                                                       'CWLSPT': '白斑病(等级)',
                                                       'BSPPCT_TD': '褐斑病比例(%)',
                                                       'DEEARPER_TD': '畸形穗比例(%)',
                                                       'EARSIZE': '果穗大小(等级)',
                                                       'INDARA': '玉米螟(等级)'
                                                       }
        # 转为字典格式存储    汉字作为key，英文缩写作为value
        self.chinese_name_to_trait_column_name_dict = {v: k for (k, v) in
                                                       self.trait_column_name_to_chinese_name_dict.items()}

    def __get_data_df(self):
        # 连接并根据传来的查询语句获取对应的数据集
        conn = st.connection("postgres")
        self.data_df = conn.query(self.query_statement)
        return self.data_df

    def __get_AOAname_list(self):
        # 获取生态亚区列表
        AOAname_list = list(filter(None, pd.unique(self.data_df["AOA_S"]).tolist()))
        return AOAname_list

    def get_sample_name_list(self, selected_AOAname):
        # 根据熟期 找到对应样本的数据集【样本点为我们所谓的目标点，CK是测试点】
        sample_name_list = list(filter(None, pd.unique(self.data_df[(self.data_df["AOA_S"] == selected_AOAname)
                                                       ]["VarNam"]).tolist()))
        return sample_name_list

    def get_sample_data_df(self, selected_AOAname):
        # 过滤选择Pheno表中样本的数据                                                      目标样本名的列表
        sample_pheno_df = self.data_df[((self.data_df["AOA_S"]).isin(selected_AOAname))]
        return sample_pheno_df

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

    def __get_sub_tilte(self, sub_title):
        # 设置每个对比性状单独的表名
        # st.subheader(sub_title)
          # markdown 自定义样式
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
        st.markdown(f'<p class = "custom-sub-title">{sub_title}</p>', unsafe_allow_html=True)
        return sub_title

    def get_dropdown_menu_bar(self):
        column_list = st.columns((2, 3))
        with column_list[0]:
            selected_AOA_list = st.multiselect(
                '选择生态亚区',
                self.AOAname_list,
                default=self.AOAname_list[0]
            )
        with column_list[1]:
            selected_trait_column_list = st.multiselect(
                '选择性状',
                self.trait_column_name_to_chinese_name_dict.values(),
                default=list(self.trait_column_name_to_chinese_name_dict.values())[0:3]  # 默认选择第一个
            )
            if len(selected_trait_column_list) == 0:
                # 未选择情况下 的异常判断
                selected_trait_column_list = [list(self.trait_column_name_to_chinese_name_dict.values())[0]]
        selected_trait_list = [self.chinese_name_to_trait_column_name_dict[selected_trait_column]
                                      for selected_trait_column in selected_trait_column_list]  # 将选择的中文名转换回对应的字段名称
        return selected_AOA_list, selected_trait_list

    def highlight_index(self, s,sample_name_set, color='yellow'):
        # 生成一个与列数相同的样式列表
        styles = ['' for _ in range(len(s) + 1)]  # +1 是为了包含索引列
        if s.name in sample_name_set:
            styles[0] = f'background-color: {color}'  # 为索引列设置背景色
            for i in range(1, len(s) + 1):
                styles[i] = f'background-color: {color}'  # 为数据列设置背景色
        return styles

    def format_float(self, x):   #float类型数据格式化，保留一位小数
        if isinstance(x, float):
            return f'{x:.1f}'.rstrip('0').rstrip('.')
        return x

    def plot(self):
        self.__get_title("TD性状透视图2024")
        selected_AOA_list, selected_trait_column_list = self.get_dropdown_menu_bar()
        sample_data_df = self.get_sample_data_df(selected_AOA_list)

        for trait_name in selected_trait_column_list:
            self.__get_sub_tilte(self.trait_column_name_to_chinese_name_dict[trait_name])
            Location_set = pd.unique(sample_data_df["Location_TD"])
            sample_name_set = pd.unique(sample_data_df['VarNam'])
            trait_summary_df = pd.DataFrame()
            flag_percent =0
            if "%" in self.trait_column_name_to_chinese_name_dict[trait_name]:
                flag_percent =1
            for sample_name in sample_name_set:
                summary_dict ={}
                for loc_name in Location_set:
                    try:
                        sample_trait_mean_value =np.mean(sample_data_df[(sample_data_df['VarNam'] == sample_name) & (sample_data_df['Location_TD'] == loc_name)][trait_name].tolist())
                    except:
                        sample_trait_mean_value = 0
                        print("Nan")
                    if flag_percent ==1:
                        summary_dict[loc_name]= [sample_trait_mean_value*100]
                    else:
                        summary_dict[loc_name] = [sample_trait_mean_value]
                summary_df = pd.DataFrame(summary_dict)   # 将dict数据转化为DataFrame格式    按列拼接数据
                trait_summary_df = pd.concat([trait_summary_df, summary_df],ignore_index=True)  # 按行拼接数据
            # 将样本名称列表作为dataframe的索引
            trait_summary_df.index = sample_name_set
            # 将该测试点的所有品种的数值求和取均值
            mean_dict = {}
            for loc_name in Location_set:
                mean_dict[loc_name] = [np.mean(trait_summary_df[loc_name])]
            mean_summary_df = pd.DataFrame(mean_dict, index=['平均数'])
            final_trait_summary_df = pd.concat([mean_summary_df, trait_summary_df])
            #保留1位小数
            final_trait_summary_df = final_trait_summary_df.applymap(self.format_float)
            # 给索引行增添颜色
           # style_df = final_trait_summary_df.style.apply(self.highlight_index, axis=1)
            # 展示
            st.dataframe(final_trait_summary_df)

        st.markdown("""
                        ##### 注释：
                        - 下拉菜单：
                            - “选择生态亚区（熟期）”、“选择性状”两个下拉菜单来指定想要查询的生态亚区和性状，均可多选；
                        - 透视图表格：展示所有品种在特定生态亚区（熟期）下的特定性状的数值：
                            - 第一列 表示所包含的品种名称，除第一个“平均数”表示的是特定的地点下所有品种的数值均值；
                            - 第一行 表示所包含的测试点名称，为选择的生态亚区下所包含的。
                        """)


if __name__ == '__main__':
#def main():
    st.set_page_config(layout='wide')
    query_statement = """
    select * from "DWS"."TDPheno2024" 
    """
    plotfunc = Plotter(query_statement)
    plotfunc.plot()