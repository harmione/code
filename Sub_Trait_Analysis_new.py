import numpy as np
import streamlit as st
import pandas as pd

import importlib.util
from streamlit_authenticator import Authenticate



class CKTable:
    def __init__(self, query_statement):
        self.query_statement = query_statement
        self.data_df = self.__get_data_df()
        self.AOAname_list = self.__get_AOAname_list()

    def __get_data_df(self):
        conn = st.connection("postgres")
        aaaa = self.query_statement
        self.data_df = conn.query(self.query_statement)
        return self.data_df

    # 获取生态亚区列表
    def __get_AOAname_list(self):
        AOAname_list = pd.unique(self.data_df["AOA_S"]).tolist()
        return AOAname_list

    # 获取对照试验点样本名list
    def get_ck_name_list(self, selected_AOAname_list):
        ck_name_list = pd.unique(self.data_df[self.data_df["AOA_S"].isin(selected_AOAname_list)]["VarNam"]).tolist()
        return ck_name_list


class PhenoTable:
    def __init__(self, query_statement):
        self.query_statement = query_statement
        self.data_df = self.__get_data_df()
        self.year_list = self.__get_year_list()

    def __get_year_list(self):
        year_list = pd.unique(self.data_df["Year"]).tolist()
        return year_list

    def __get_data_df(self):
        conn = st.connection("postgres")
        data_df = conn.query(self.query_statement)
        return data_df

    # 获取目标试验点的样本名list
    def get_sample_name_list(self, selected_AOAname_list):
        # 过滤 值为None的
        sample_name_list = list(filter(None,pd.unique(self.data_df[self.data_df["AOA_S"].isin(selected_AOAname_list)]
                                     ["VarNam"]).tolist()))
        return sample_name_list

    def get_sample_pheno_df(self, selected_year_list, selected_AOAname, selected_target_name_list):
        sample_pheno_df = self.data_df[(self.data_df["Year"].isin(selected_year_list)) &
                                       (self.data_df["AOA_S"] == selected_AOAname) &
                                       (self.data_df["VarNam"].isin(selected_target_name_list))]
        return sample_pheno_df

    def get_ck_pheno_df(self, selected_year_list, selected_AOAname, selected_ck_name_list):
        ck_pheno_df = self.data_df[(self.data_df["Year"].isin(selected_year_list)) &
                                   (self.data_df["AOA_S"] == selected_AOAname) &
                                   (self.data_df["VarNam"].isin([selected_ck_name_list]))]
        return ck_pheno_df

    def get_percent_pressure_bookname_num(self, selected_year_list, selected_AOAname, trait_column_name):
        # 百分比表的 压力点次
        pressure_bookname_num = 0
        data_df = self.data_df[(self.data_df["Year"].isin(selected_year_list)) &
                               (self.data_df["AOA_S"] == selected_AOAname)]
        location_set = set(data_df["Location_TD"])
        for loc_name in location_set:
            data_df = data_df[data_df["Location_TD"] == loc_name]
            if any(data_df[trait_column_name] > 0):     #百分比制的 越小越好，最小为0%
                pressure_bookname_num += 1
        return pressure_bookname_num

    def get_grade_pressure_bookname_num(self, selected_year_list, selected_AOAname, trait_column_name):
        # 打分级表的 压力点次
        pressure_bookname_num = 0
        data_df = self.data_df[(self.data_df["Year"].isin(selected_year_list)) &
                               (self.data_df["AOA_S"] == selected_AOAname)]
        location_set = set(data_df["Location_TD"])
        for loc_name in location_set:
            data_df = data_df[data_df["Location_TD"] == loc_name]
            if any(data_df[trait_column_name] != 9):     ## 打分越大越好  9为最大
                pressure_bookname_num += 1
        return pressure_bookname_num


class Plot:
    def __init__(self, ckTable: CKTable, phenoTable: PhenoTable):
        self.ckTable = ckTable
        self.phenoTable = phenoTable
        self.trait_column_name_to_chinese_name_dict = {
                                                       'YLD14_TD': '产量(kg/亩)',
                                                       'MST': '水分(%)',
                                                       # 'PHT': '株高(cm)',
                                                       # 'EHT': '穗位(cm)',
                                                       'STKRPCT_TD': '青枯病比例(%)',
                                                       'STKLPCT_TD': '茎倒比例(%)',
                                                       'ERTLPCT_TD':'前倒(%)',
                                                       'LRTLPCT_TD': '后倒(%)',
                                                       'BARPCT_TD': '空杆比例(%)',
                                                       'EARTPCT_TD': '穗腐比例(%)',
                                                       'KERTPCT_TD': '霉变粒率比例(%)',
                                                       'CLB': '大斑病(等级)',
                                                       'GLS': '灰斑病(等级)',
                                                       'CWLSPT': '白斑病(等级)',
                                                       'HUSKCOV': '苞叶覆盖度(等级)',
                                                       'KERSR': '结实性(等级)',
                                                       'TIPFILL': '秃尖(等级)'
                                                       }
        self.chinese_name_to_trait_column_name_dict = {v: k for (k, v) in
                                                       self.trait_column_name_to_chinese_name_dict.items()}

    def __get_dropdown_men_bar(self):
        column_list = st.columns((1, 1, 1))
        with column_list[0]:
            selected_year_list = st.multiselect(
                '年份',
                self.phenoTable.year_list,
                default=self.phenoTable.year_list[0]
            )
            if len(selected_year_list) == 0:
                selected_year_list = [self.phenoTable.year_list[0]]
        with column_list[1]:
            selected_AOAname_list = st.multiselect(
                '生态亚区',
                self.ckTable.AOAname_list,
                default=self.ckTable.AOAname_list[0:2]
            )
        with column_list[2]:
            selected_trait_column_list = st.multiselect(
                '性状',
                self.trait_column_name_to_chinese_name_dict.values(),
                default=list(self.trait_column_name_to_chinese_name_dict.values())[0]
            )
            if len(selected_trait_column_list) == 0:
                selected_trait_column_list = [list(self.trait_column_name_to_chinese_name_dict.values())[0]]
        selected_trait_column_list = [self.chinese_name_to_trait_column_name_dict[selected_trait_column]
                                      for selected_trait_column in selected_trait_column_list]
        column_list = st.columns((1, 5))
        with column_list[0]:
            selected_ck_name = st.selectbox(
                '对照品种',
                self.ckTable.get_ck_name_list(selected_AOAname_list)
            )
        with column_list[1]:
            selected_target_name_list = st.multiselect(
                '目标品种',
                self.phenoTable.get_sample_name_list(selected_AOAname_list),
                default=self.phenoTable.get_sample_name_list(selected_AOAname_list)[1:3]
            )
            if len(selected_target_name_list) == 0:
                selected_target_name_list = [self.phenoTable.get_sample_name_list(selected_AOAname_list)[0]]
        return (selected_year_list, selected_AOAname_list, selected_trait_column_list, selected_ck_name,
                selected_target_name_list)

    def get_sample_data_df(self, year_list, AOAname_list, name_list, trait_column):
        data_df = self.phenoTable.data_df
        data_df = data_df[~pd.isna(data_df[trait_column])]
        sample_data_df = data_df[data_df["Year"].isin(year_list) & data_df["AOA_S"].isin(AOAname_list)
                                 & data_df["VarNam"].isin(name_list)]
        return sample_data_df

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

   # 获取数值型的 统计信息   不包括水分的
    def get_num_trait_summary(self, year, AOAname_list, sample_data_df, ck_data_df, trait_column_name):
        self.__get_sub_tilte(self.trait_column_name_to_chinese_name_dict[trait_column_name])    # 子标题
        threshold = st.slider("阈值选择", min_value=0, max_value=300, value=0)
        sample_name_set, ck_name= pd.unique(sample_data_df['VarNam']), pd.unique(ck_data_df['VarNam'])[0]  # 样本和对照品种名称的数据

        num_trait_summary_df = pd.DataFrame()  # 存储num型结果数据
        for aoa_name in AOAname_list:
            ck_bookname_set = pd.unique(ck_data_df[(ck_data_df['VarNam'] == ck_name) & (ck_data_df['AOA_S'] == aoa_name)]["Location_TD"])  # 种的地点
            temp_num_trait_summary_df = pd.DataFrame()  # 存储num型结果数据
            for sample_name in sample_name_set:
                single_sample_num_trait_summary_dict = {}
                sample_bookname_set = pd.unique(sample_data_df[(sample_data_df['VarNam'] == sample_name) & (sample_data_df['AOA_S'] == aoa_name)]["Location_TD"])  # 样本测试点的集合
                ck_bookname_num, sample_bookname_num = len(ck_bookname_set), len(sample_bookname_set)
                if ck_bookname_num ==0 and sample_bookname_num ==0:
                     continue
                bookname_intersection_set = set(ck_bookname_set).intersection(sample_bookname_set)   # 取对照和目标测试点的交集
                bookname_intersection_num = len(bookname_intersection_set)
                sample_trait_value_list, ck_trait_value_list, increase_num = [], [], 0  # 初始化
                for loc_name in bookname_intersection_set:     # 对照样本与目标样本在同一测试点下的比较  故要选取 对照样本所在测试点与 目标样本所在测试点的交集
                    try:
                        sample_trait_value = sample_data_df[(sample_data_df['VarNam'] == sample_name) & (sample_data_df['Location_TD'] == loc_name)][trait_column_name].tolist()[0]
                    except:
                        print(sample_data_df)
                    ck_trait_value = ck_data_df[(ck_data_df['VarNam'] == ck_name) & (ck_data_df['Location_TD'] == loc_name)][trait_column_name].tolist()[0]
                    sample_trait_value_list.append(sample_trait_value)
                    ck_trait_value_list.append(ck_trait_value)
                    if sample_trait_value - ck_trait_value > threshold:       #####  num制类型这  是大于阈值
                        increase_num += 1
                if bookname_intersection_num != 0:
                    increase_rate = increase_num / bookname_intersection_num * 100    # 赢率
                else:
                    increase_rate = np.nan
                sample_trait_mean_value = np.mean(sample_trait_value_list)
                ck_trait_mean_value = np.mean(ck_trait_value_list)
                difference_value = sample_trait_mean_value - ck_trait_mean_value
                difference_rate = difference_value / ck_trait_mean_value
                single_sample_num_trait_summary_dict["年份"] = year
                single_sample_num_trait_summary_dict["生态亚区"] = aoa_name
                single_sample_num_trait_summary_dict["目标品种"] = sample_name
                single_sample_num_trait_summary_dict[f"目标品种种植点次"] = sample_bookname_num
                single_sample_num_trait_summary_dict["对比品种"] = ck_name
                single_sample_num_trait_summary_dict[f"对照品种种植点次"] = ck_bookname_num
                single_sample_num_trait_summary_dict[f"对比点数"] = bookname_intersection_num
                single_sample_num_trait_summary_dict[f"增产点数"] = increase_num
                single_sample_num_trait_summary_dict[f"赢率(%)"] = increase_rate
                single_sample_num_trait_summary_dict[f"目标品种产量均值"] = sample_trait_mean_value
                single_sample_num_trait_summary_dict[f"对比品种产量均值"] = ck_trait_mean_value
                single_sample_num_trait_summary_dict[f"增减产值"] = difference_value
                single_sample_num_trait_summary_dict[f"增减产(%)"] = difference_rate *100
                single_sample_num_trait_summary_dict[f'综合判定'] = np.nan
                single_sample_num_trait_summary_df = pd.DataFrame(single_sample_num_trait_summary_dict)  # 将dict数据转化为DataFrame格式
                temp_num_trait_summary_df = pd.concat([temp_num_trait_summary_df, single_sample_num_trait_summary_df],
                                                 ignore_index=True)  # 数据拼接（每行为一个样本）
            num_trait_summary_df = pd.concat([num_trait_summary_df, temp_num_trait_summary_df],axis=0)
        return num_trait_summary_df

    # 水分summary计算    没有阈值选择项、增长量、赢率 相关
    def get_mst_trait_summary(self, year, AOAname_list, sample_data_df, ck_data_df, trait_column_name):
        self.__get_sub_tilte(self.trait_column_name_to_chinese_name_dict[trait_column_name])
        sample_name_set, ck_name= pd.unique(sample_data_df['VarNam']), pd.unique(ck_data_df['VarNam'])[0]
        num_trait_summary_df = pd.DataFrame()
        for aoa_name in AOAname_list:
            ck_bookname_set = pd.unique(
                ck_data_df[(ck_data_df['VarNam'] == ck_name) & (ck_data_df['AOA_S'] == aoa_name)][
                    "Location_TD"])  # 种的地点
            temp_num_trait_summary_df = pd.DataFrame()  # 存储num型结果数据
            for sample_name in sample_name_set:
                single_sample_num_trait_summary_dict = {}
                sample_bookname_set = pd.unique(
                    sample_data_df[(sample_data_df['VarNam'] == sample_name) & (sample_data_df['AOA_S'] == aoa_name)][
                        "Location_TD"])  # 样本测试点的集合
                ck_bookname_num, sample_bookname_num = len(ck_bookname_set), len(sample_bookname_set)
                if ck_bookname_num == 0 and sample_bookname_num == 0: # 若以生态亚区里对照和目标样本都没种植，跳过
                    continue
                bookname_intersection_set = set(ck_bookname_set).intersection(sample_bookname_set)

                bookname_intersection_num = len(bookname_intersection_set)
                sample_trait_value_list, ck_trait_value_list = [], []
                for loc_name in bookname_intersection_set:
                    try:
                        sample_trait_value = sample_data_df[
                            (sample_data_df['VarNam'] == sample_name) & (sample_data_df['Location_TD'] == loc_name)][
                            trait_column_name].tolist()[0]
                    except:
                        print(sample_data_df)
                    ck_trait_value = ck_data_df[(ck_data_df['VarNam'] == ck_name) & (ck_data_df['Location_TD'] == loc_name)][
                        trait_column_name].tolist()[0]
                    sample_trait_value_list.append(sample_trait_value)
                    ck_trait_value_list.append(ck_trait_value)
                sample_trait_mean_value = np.mean(sample_trait_value_list)
                ck_trait_mean_value = np.mean(ck_trait_value_list)
                difference_value = sample_trait_mean_value - ck_trait_mean_value
                difference_rate = difference_value / ck_trait_mean_value * 100
                single_sample_num_trait_summary_dict["年份"] = year
                single_sample_num_trait_summary_dict["生态亚区"] = aoa_name
                single_sample_num_trait_summary_dict["目标品种"] = sample_name
                single_sample_num_trait_summary_dict[f"目标品种种植点次"] = sample_bookname_num
                single_sample_num_trait_summary_dict["对比品种"] = ck_name
                single_sample_num_trait_summary_dict[f"对照品种种植点次"] = ck_bookname_num
                single_sample_num_trait_summary_dict[f"对比点数"] = bookname_intersection_num
                single_sample_num_trait_summary_dict[f"目标品种收获水分均值[%制]"] = sample_trait_mean_value *100
                single_sample_num_trait_summary_dict[f"对比品种收获水分均值[%制]"] = ck_trait_mean_value *100
                single_sample_num_trait_summary_dict[f"收获水分差值[%制]"] = difference_value *100
                single_sample_num_trait_summary_dict[f'综合判定'] = np.nan
                single_sample_num_trait_summary_df = pd.DataFrame(single_sample_num_trait_summary_dict)
                temp_num_trait_summary_df = pd.concat([temp_num_trait_summary_df, single_sample_num_trait_summary_df],
                                                 ignore_index=True)    #忽略原有索引
            num_trait_summary_df = pd.concat([num_trait_summary_df, temp_num_trait_summary_df], axis=0)
        return num_trait_summary_df

    # 百分制 summary计算
    def get_percent_trait_summary(self, year, AOAname_list, sample_data_df, ck_data_df, trait_column_name):
        self.__get_sub_tilte(self.trait_column_name_to_chinese_name_dict[trait_column_name])
        threshold = st.slider(f"{self.trait_column_name_to_chinese_name_dict[trait_column_name]}阈值选择", min_value=0, max_value=100, value=0)
        sample_name_set, ck_name= pd.unique(sample_data_df['VarNam']), pd.unique(ck_data_df['VarNam'])[0]

        percent_trait_summary_df = pd.DataFrame()
        for aoa_name in AOAname_list:
            ck_bookname_set = pd.unique(ck_data_df[(ck_data_df['VarNam'] == ck_name) & (ck_data_df['AOA_S'] == aoa_name)]["Location_TD"])  # 种的地点
            temp_percent_trait_summary_df = pd.DataFrame()
            for sample_name in sample_name_set:
                single_sample_num_trait_summary_dict = {}
                sample_bookname_set = pd.unique(sample_data_df[(sample_data_df['VarNam'] == sample_name) & (sample_data_df['AOA_S'] == aoa_name)]["Location_TD"])  # 样本测试点的集合
                ck_bookname_num, sample_bookname_num = len(ck_bookname_set), len(sample_bookname_set)
                if ck_bookname_num == 0 and sample_bookname_num == 0:
                    continue
                bookname_intersection_set = set(ck_bookname_set).intersection(sample_bookname_set)
                bookname_intersection_num = len(bookname_intersection_set)
                sample_trait_value_list, ck_trait_value_list, increase_num = [], [], 0
                for loc_name in bookname_intersection_set:
                    try:
                        sample_trait_value = sample_data_df[
                            (sample_data_df['VarNam'] == sample_name) & (sample_data_df['Location_TD'] == loc_name)][
                            trait_column_name].tolist()[0]
                    except:
                        print(sample_data_df)
                    ck_trait_value = ck_data_df[(ck_data_df['VarNam'] == ck_name) & (ck_data_df['Location_TD'] == loc_name)][
                        trait_column_name].tolist()[0]
                    sample_trait_value_list.append(sample_trait_value)
                    ck_trait_value_list.append(ck_trait_value)
                    if (sample_trait_value - ck_trait_value)*100 < threshold:        ##### 百分制这里是    小于阈值        因为数据库里带%的性状存的都是小数，所以这边*100 来和阈值作比较
                        increase_num += 1
                if bookname_intersection_num != 0:
                    increase_rate = increase_num / bookname_intersection_num * 100
                else:
                    increase_rate = np.nan
                sample_trait_mean_value = np.mean(sample_trait_value_list)
                ck_trait_mean_value = np.mean(ck_trait_value_list)
                difference_value = sample_trait_mean_value - ck_trait_mean_value
                # difference_rate = difference_value / ck_trait_mean_value
                single_sample_num_trait_summary_dict["年份"] = year
                single_sample_num_trait_summary_dict["生态亚区"] = aoa_name
                single_sample_num_trait_summary_dict["目标品种"] = sample_name
                single_sample_num_trait_summary_dict[f"目标品种种植点次"] = sample_bookname_num
                single_sample_num_trait_summary_dict["对比品种"] = ck_name
                single_sample_num_trait_summary_dict[f"对照品种种植点次"] = ck_bookname_num
                single_sample_num_trait_summary_dict[f"对比点数"] = bookname_intersection_num
                single_sample_num_trait_summary_dict[f"赢点数"] = increase_num
                single_sample_num_trait_summary_dict[f"赢率(%)[%制]"] = increase_rate
                single_sample_num_trait_summary_dict[f"目标品种均值[%制]"] = sample_trait_mean_value * 100
                single_sample_num_trait_summary_dict[f"对比品种均值[%制]"] = ck_trait_mean_value  * 100
                single_sample_num_trait_summary_dict[f"均值差值[%制]"] = difference_value * 100
                single_sample_num_trait_summary_dict[f'目标品种极小值[%制]'] = (np.min(sample_trait_value_list)*100) if len(sample_trait_value_list) != 0 else np.nan
                single_sample_num_trait_summary_dict[f"对照品种极小值[%制]"] = (np.min(ck_trait_value_list)*100) if len(ck_trait_value_list) != 0 else np.nan
                single_sample_num_trait_summary_dict[f'极小值差值[%制]'] = (np.min(sample_trait_value_list) - np.min(ck_trait_value_list)*100) if len(sample_trait_value_list) != 0 and len(ck_trait_value_list) != 0 else np.nan
                single_sample_num_trait_summary_dict[f"目标品种极大值[%制]"] = (np.max(sample_trait_value_list)*100) if len(sample_trait_value_list) != 0 else np.nan
                single_sample_num_trait_summary_dict[f'目标品种极大值[%制]'] = (np.max(ck_trait_value_list)*100) if len(ck_trait_value_list) != 0 else np.nan
                single_sample_num_trait_summary_dict[f'极大值差值[%制]'] = (np.max(sample_trait_value_list) - np.max(ck_trait_value_list)*100) if len(sample_trait_value_list) != 0 and len(ck_trait_value_list) != 0 else np.nan
                single_sample_num_trait_summary_dict[f'综合判定'] = np.nan
                single_sample_num_trait_summary_df = pd.DataFrame(single_sample_num_trait_summary_dict)
                temp_percent_trait_summary_df = pd.concat([temp_percent_trait_summary_df, single_sample_num_trait_summary_df],
                                                 ignore_index=True)
            percent_trait_summary_df = pd.concat([percent_trait_summary_df, temp_percent_trait_summary_df], axis=0)
        return percent_trait_summary_df.round(3)

    # 打等级制 summary计算
    def get_grade_trait_summary(self, year, AOAname_list, sample_data_df, ck_data_df, trait_column_name):
        self.__get_sub_tilte(self.trait_column_name_to_chinese_name_dict[trait_column_name])
        threshold = st.slider(f"{self.trait_column_name_to_chinese_name_dict[trait_column_name]}阈值选择", min_value=1, max_value=9, value=0)   # 阈值设置
        sample_name_set, ck_name= pd.unique(sample_data_df['VarNam']), pd.unique(ck_data_df['VarNam'])[0]

        grade_trait_summary_df = pd.DataFrame()
        for aoa_name in AOAname_list:
            temp_grade_trait_summary_df = pd.DataFrame()
            ck_bookname_set = pd.unique(ck_data_df[(ck_data_df['VarNam'] == ck_name) & (ck_data_df['AOA_S'] == aoa_name)]["Location_TD"])  # 种的地点
            for sample_name in sample_name_set:
                single_sample_num_trait_summary_dict = {}
                sample_bookname_set = pd.unique(sample_data_df[(sample_data_df['VarNam'] == sample_name) & (sample_data_df['AOA_S'] == aoa_name)]["Location_TD"])  # 样本测试点的集合
                ck_bookname_num, sample_bookname_num = len(ck_bookname_set), len(sample_bookname_set)

                bookname_intersection_set = set(ck_bookname_set).intersection(sample_bookname_set)
                if ck_bookname_num == 0 and sample_bookname_num == 0:
                    continue
                bookname_intersection_num = len(bookname_intersection_set)
                sample_trait_value_list, ck_trait_value_list, increase_num = [], [], 0
                for loc_name in bookname_intersection_set:
                    try:
                        sample_trait_value = sample_data_df[
                            (sample_data_df['VarNam'] == sample_name) & (sample_data_df['Location_TD'] == loc_name)][
                            trait_column_name].tolist()[0]
                    except:
                        print(sample_data_df)
                    ck_trait_value = ck_data_df[(ck_data_df['VarNam'] == ck_name) & (ck_data_df['Location_TD'] == loc_name)][
                        trait_column_name].tolist()[0]
                    sample_trait_value_list.append(sample_trait_value)
                    ck_trait_value_list.append(ck_trait_value)
                    if sample_trait_value - ck_trait_value > threshold:     ##### 等级表中   是 大于阈值
                        increase_num += 1
                if bookname_intersection_num != 0:
                    increase_rate = increase_num / bookname_intersection_num * 100
                else:
                    increase_rate = np.nan
                sample_trait_mean_value = np.mean(sample_trait_value_list)
                ck_trait_mean_value = np.mean(ck_trait_value_list)
                difference_value = sample_trait_mean_value - ck_trait_mean_value
                # difference_rate = difference_value / ck_trait_mean_value
                single_sample_num_trait_summary_dict["年份"] = year
                single_sample_num_trait_summary_dict["生态亚区"] = aoa_name
                single_sample_num_trait_summary_dict["目标品种"] = sample_name
                single_sample_num_trait_summary_dict[f"目标品种种植点次"] = sample_bookname_num
                single_sample_num_trait_summary_dict["对比品种"] = ck_name
                single_sample_num_trait_summary_dict[f"对照品种种植点次"] = ck_bookname_num
                single_sample_num_trait_summary_dict[f"对比点数"] = bookname_intersection_num
                single_sample_num_trait_summary_dict[f"赢点数"] = increase_num
                single_sample_num_trait_summary_dict[f"赢率(%)"] = increase_rate                           #上色
                single_sample_num_trait_summary_dict[f"目标品种均值"] = sample_trait_mean_value
                single_sample_num_trait_summary_dict[f"对比品种均值"] = ck_trait_mean_value
                single_sample_num_trait_summary_dict[f"均值差值"] = difference_value                         # 上色
                single_sample_num_trait_summary_dict[f'目标品种极小值'] = np.min(sample_trait_value_list) if len(sample_trait_value_list) != 0 else np.nan
                single_sample_num_trait_summary_dict[f"对照品种极小值"] = np.min(ck_trait_value_list) if len(ck_trait_value_list) != 0 else np.nan
                single_sample_num_trait_summary_dict[f'极小值差值'] = np.min(sample_trait_value_list) - np.min(ck_trait_value_list) if len(sample_trait_value_list) != 0 and len(ck_trait_value_list) != 0 else np.nan
                single_sample_num_trait_summary_dict[f"目标品种极大值"] = np.max(sample_trait_value_list) if len(sample_trait_value_list) != 0 else np.nan
                single_sample_num_trait_summary_dict[f'目标品种极大值'] = np.max(ck_trait_value_list) if len(ck_trait_value_list) != 0 else np.nan
                single_sample_num_trait_summary_dict[f'极大值差值'] = np.max(sample_trait_value_list) - np.max(ck_trait_value_list) if len(sample_trait_value_list) != 0 and len(ck_trait_value_list) != 0 else np.nan
                single_sample_num_trait_summary_dict[f'综合判定'] = np.nan
                single_sample_num_trait_summary_df = pd.DataFrame(single_sample_num_trait_summary_dict)
                temp_grade_trait_summary_df = pd.concat([temp_grade_trait_summary_df, single_sample_num_trait_summary_df],
                                                 ignore_index=True)
            grade_trait_summary_df = pd.concat([grade_trait_summary_df, temp_grade_trait_summary_df], axis=0)
        return grade_trait_summary_df


    def yld_color_cells1(self,row):
        row[0] = float(row[0])
        row[1] = float(row[1])
        if row[0] > 5:
            if row[1]>= 50:
                return ["background-color:#228B22","background-color:#228B22"]
            else:
                return ["background-color:#228B22","background-color:#7FFF00"]
        elif -5 < row[0] <= 5:
            if row[1]>= 50:
                return ["background-color:white","background-color:yellow"]
            else:
                return ["background-color:white","background-color:#FFA500"]
        elif row[0] < -5:
            if row[1]>= 50:
                return ["background-color:red", "background-color:pink"]
            else:
                return ["background-color:red", "background-color:red"]
        else:
            return ["",""]

    def stkrpct_color_cells1(self, row):  # 青枯病 的赢率及均值差值列上色
        row[0] = float(row[0])
        row[1] = float(row[1])
        if row[0] > 10:
            if row[1]>= 50:
                return ["background-color:red", "background-color:pink"]
            else:
                return ["background-color:red", "background-color:red"]
        elif -10 < row[0] <= 10:
            if row[1]>= 50:
                return ["background-color:white","background-color:yellow"]
            else:
                return ["background-color:white","background-color:#FFA500"]
        elif row[0] < -10:
            if row[1]>= 50:
                return ["background-color:#228B22", "background-color:#228B22"]
            else:
                return ["background-color:#228B22", "background-color:#7FFF00"]
        else:
            return ["",""]

    def kertpct_color_cells1(self, row):   #霉变粒率病 的赢率及均值差值列上色
        row[0] = float(row[0])
        row[1] = float(row[1])
        if row[0] <- 0.5:
            if row[1]>= 50:
                return ["background-color:#228B22","background-color:#228B22"]
            else:
                return ["background-color:#228B22","background-color:#7FFF00"]
        elif -0.5 < row[0] <= 0.5:
            if row[1]>= 50:
                return ["background-color:white","background-color:yellow"]
            else:
                return ["background-color:white","background-color:#FFA500"]
        elif row[0] > 0.5:
            if row[1]>= 50:
                return ["background-color:red", "background-color:pink"]
            else:
                return ["background-color:red", "background-color:red"]
        else:
            return ["",""]

    def ertlpct_color_cells1(self, row):   #前倒 的赢率及均值差值列上色
        row[0] = float(row[0])
        row[1] = float(row[1])
        if row[0] < -20.0:
            if row[1]>= 50:
                return ["background-color:#228B22","background-color:#228B22"]
            else:
                return ["background-color:#228B22","background-color:#7FFF00"]
        elif -20.0 < row[0] <= 20.0:
            if row[1]>= 50:
                return ["background-color:white","background-color:yellow"]
            else:
                return ["background-color:white","background-color:#FFA500"]
        elif row[0] > 20.0:
            if row[1]>= 50:
                return ["background-color:red", "background-color:pink"]
            else:
                return ["background-color:red", "background-color:red"]
        else:
            return ["",""]

    def lrtlpct_color_cells1(self,row): #后倒 的赢率及均值差值列上色
        row[0] = float(row[0])
        row[1] = float(row[1])
        if row[0] < -10.0:
            if row[1]>= 50:
                return ["background-color:#228B22","background-color:#228B22"]
            else:
                return ["background-color:#228B22","background-color:#7FFF00"]
        elif -10.0 < row[0] <= 10.0:
            if row[1]>= 50:
                return ["background-color:white","background-color:yellow"]
            else:
                return ["background-color:white","background-color:#FFA500"]
        elif row[0] > 10.0:
            if row[1]>= 50:
                return ["background-color:red", "background-color:pink"]
            else:
                return ["background-color:red", "background-color:red"]
        else:
            return ["",""]

    def Leaf_color_cells1(self,row):  # 叶部病害的均值差值和赢率列 上色
        row[0] = float(row[0])
        row[1] = float(row[1])
        if row[0] > 1.5:
            if row[1]>= 50:
                return ["background-color:#228B22","background-color:#228B22"]
            else:
                return ["background-color:#228B22","background-color:#7FFF00"]
        elif -1.5 < row[0] <= 1.5:
            if row[1]>= 50:
                return ["background-color:white","background-color:yellow"]
            else:
                return ["background-color:white","background-color:#FFA500"]
        elif row[0] < -1.5:
            if row[1]>= 50:
                return ["background-color:red", "background-color:pink"]
            else:
                return ["background-color:red", "background-color:red"]
        else:
            return ["",""]


    def ertlpct_and_lrtlpct_color_cells(self,row):   # 前倒和后倒的均值列上色  均用 倒伏倒折率那个
        colors = []
        for val in row:
            val = float(val)
            if 0 <= val <= 5:
                colors.append("background-color:#228B22")  # 高抗
            elif 5 < val  <= 10:
                colors.append("background-color:#7FFF00")  # 抗
            elif 10 < val <= 15:
                colors.append("background-color:yellow")  # 中抗
            elif 15 < val  <= 30:
                colors.append("background-color:#FFA500")  # 感S
            elif 30 < val:
                colors.append("background-color:red")  # 高感HS
            else:
                colors.append("")
        return pd.Series(colors)


    def stkrpct_color_cells(self,row): # 青枯病的均值列上色
        colors = []
        for val in row:
            val = float(val)
            if 0 <= val <= 5:
                colors.append("background-color:#228B22")  # 高抗
            elif 5 < val <= 10:
                colors.append("background-color:#7FFF00")  # 抗
            elif 10 < val <= 20:
                colors.append("background-color:yellow")  # 中抗
            elif 20 < val <= 30:
                colors.append("background-color:#FFA500")  # 感S
            elif 30 < val:
                colors.append("background-color:red")  # 高感HS
            else:
                colors.append("")
        return pd.Series(colors)

        # 东北霉变粒率 均值列上色

    def kertpct_colors_cells_DHB(self, row):
        colors = []
        for val in row:
            val = float(val)
            if 0.0 < val <= 0.5:
                colors.append("background-color:#228B22")  # 高抗
            elif 0.5 < val <= 1.0:
                colors.append("background-color:#7FFF00")  # 抗
            elif 1.0 < val <= 1.5:
                colors.append("background-color:yellow")  # 中抗
            elif 1.5 < val <= 2.0:
                colors.append("background-color:#FFA500")  # 感S
            elif 2.0 < val <= 100:
                colors.append("background-color:red")  # 高感HS
            else:
                colors.append("")
        return pd.Series(colors)

        # 黄淮的霉变粒率  均值列上色

    def kertpct_colors_cells_HHH(self, row):
        colors = []
        for val in row:
            val = float(val)
            if 0.0 < val <= 0.5:
                colors.append("background-color:#228B22")  # 高抗
            elif 0.5 < val <= 1.0:
                colors.append("background-color:#7FFF00")  # 抗
            elif 1.0 < val <= 2.0:
                colors.append("background-color:yellow")  # 中抗
            elif 2.1 < val <= 4.0:
                colors.append("background-color:#FFA500")  # 感S
            elif 4.1 < val <= 100:
                colors.append("background-color:red")  # 高感HS
            else:
                colors.append("")
        return pd.Series(colors)

    def Leaf_color_cells(self, row):     # 叶部病害的均值列上色
        colors = []
        for val in row:
            val = float(val)
            if 7.5 < val <= 9.0:
                colors.append("background-color:#228B22")  # 高抗
            elif 5.5 < val <= 7.5:
                colors.append("background-color:#7FFF00")  # 抗
            elif 3.5 < val <= 5.5:
                colors.append("background-color:yellow")  # 中抗
            elif 1.5 < val <= 3.5:
                colors.append("background-color:#FFA500")  # 感S
            elif 1.0 <= val <= 1.5:
                colors.append("background-color:red")  # 高感HS
            else:
                colors.append("")
        return pd.Series(colors)

    def format_float(self, x):   #float类型数据格式化，保留一位小数
        if isinstance(x, float):
            return f'{x:.1f}'.rstrip('0').rstrip('.')
        return x

    def plot(self):
        (selected_year_list, selected_AOAname_list, selected_trait_column_list, selected_ck_name,
         selected_target_name_list) = self.__get_dropdown_men_bar()
        for trait_column_name in selected_trait_column_list:
            sample_data_df = self.get_sample_data_df(selected_year_list, selected_AOAname_list,
                                                     selected_target_name_list, trait_column_name)
            ck_data_df = self.get_sample_data_df(selected_year_list, selected_AOAname_list,
                                                 [selected_ck_name], trait_column_name)
            if len(sample_data_df) == 0 or len(ck_data_df) == 0:
                continue
            if "YLD" in trait_column_name:
                trait_summary_df = self.get_num_trait_summary(selected_year_list, selected_AOAname_list,
                                                                  sample_data_df, ck_data_df, trait_column_name)
                trait_summary_df.reset_index(drop=True, inplace=True)  # 重置索引
                trait_summary_df = trait_summary_df.applymap(self.format_float)
                style_df = trait_summary_df.style
                if "增减产(%)" in trait_summary_df.columns:
                    style_df = style_df.apply(self.yld_color_cells1,axis =1,subset=['增减产(%)','赢率(%)'])
                    #style_df = style_df.background_gradient(cmap='RdYlGn', subset=['增减产(%)', '赢率(%)'])    # 渐变色有问题，会覆盖之前的色
                st.dataframe(style_df)
            elif "MST" in trait_column_name:
                trait_summary_df = self.get_mst_trait_summary(selected_year_list, selected_AOAname_list,
                                                              sample_data_df, ck_data_df, trait_column_name)
                trait_summary_df.reset_index(drop=True, inplace=True)
                trait_summary_df = trait_summary_df.applymap(self.format_float)
                st.dataframe(trait_summary_df)
            elif "%" in self.trait_column_name_to_chinese_name_dict[trait_column_name]:
                trait_summary_df = self.get_percent_trait_summary(selected_year_list, selected_AOAname_list,
                                                                  sample_data_df, ck_data_df, trait_column_name)
                trait_summary_df = trait_summary_df.applymap(self.format_float)
                trait_summary_df.reset_index(drop=True, inplace=True)
                style_df = trait_summary_df.style
                if "青枯病比例(%)" in self.trait_column_name_to_chinese_name_dict[trait_column_name]:
                    style_df = style_df.apply(self.stkrpct_color_cells, subset=['目标品种均值[%制]'])
                    style_df = style_df.apply(self.stkrpct_color_cells1, axis=1, subset=['均值差值[%制]', '赢率(%)[%制]'])
                if "霉变粒率比例(%)" in self.trait_column_name_to_chinese_name_dict[trait_column_name]:
                    sub1 = ['北方超早', '北方极早', '北方早熟', '东华北中早', '东华北中熟', '东华北中晚']
                    sub2 = ['黄淮南', '黄淮北']
                    if trait_summary_df['生态亚区'].isin(sub2).any():
                        style_df = style_df.apply(self.kertpct_colors_cells_HHH, subset=['目标品种均值[%制]'])
                    elif trait_summary_df['生态亚区'].isin(sub1).any():
                        style_df = style_df.apply(self.kertpct_colors_cells_DHB, subset=['目标品种均值[%制]'])
                    style_df = style_df.apply(self.kertpct_color_cells1, axis=1, subset=['均值差值[%制]', '赢率(%)[%制]'])
                if "前倒(%)" in self.trait_column_name_to_chinese_name_dict[trait_column_name]:
                    style_df = style_df.apply(self.ertlpct_and_lrtlpct_color_cells, subset=['目标品种均值[%制]'])
                    style_df = style_df.apply(self.ertlpct_color_cells1, axis=1, subset=['均值差值[%制]', '赢率(%)[%制]'])
                if "后倒(%)" in self.trait_column_name_to_chinese_name_dict[trait_column_name]:
                    style_df = style_df.apply(self.ertlpct_and_lrtlpct_color_cells, subset=['目标品种均值[%制]'])
                    style_df = style_df.apply(self.lrtlpct_color_cells1, axis=1, subset=['均值差值[%制]', '赢率(%)[%制]'])
                st.dataframe(style_df)

            else:    # 等级类型的
                trait_summary_df = self.get_grade_trait_summary(selected_year_list, selected_AOAname_list,
                                                                  sample_data_df, ck_data_df, trait_column_name)
                trait_summary_df.reset_index(drop=True, inplace=True)
                trait_summary_df = trait_summary_df.applymap(self.format_float)
                style_df = trait_summary_df.style
                if '大斑病(等级)' in self.trait_column_name_to_chinese_name_dict[trait_column_name]:  # 大斑，灰斑， 锈病，白斑，弯包叶斑
                    style_df = style_df.apply(self.Leaf_color_cells, subset=['目标品种均值'])
                    style_df = style_df.apply(self.Leaf_color_cells1, axis=1, subset=['均值差值', '赢率(%)'])
                if '灰斑病(等级)' in self.trait_column_name_to_chinese_name_dict[trait_column_name]:  # 大斑，灰斑， 锈病，白斑，弯包叶斑
                    style_df = style_df.apply(self.Leaf_color_cells, subset=['目标品种均值'])
                    style_df = style_df.apply(self.Leaf_color_cells1, axis=1, subset=['均值差值', '赢率(%)'])
                if '普通锈病(等级)' in self.trait_column_name_to_chinese_name_dict[trait_column_name]:  # 大斑，灰斑， 锈病，白斑，弯包叶斑
                    style_df = style_df.apply(self.Leaf_color_cells, subset=['目标品种均值'])
                    style_df = style_df.apply(self.Leaf_color_cells1, axis=1, subset=['均值差值', '赢率(%)'])
                if '白斑病(等级)' in self.trait_column_name_to_chinese_name_dict[trait_column_name]:  # 大斑，灰斑， 锈病，白斑，弯包叶斑
                    style_df = style_df.apply(self.Leaf_color_cells, subset=['目标品种均值'])
                    style_df = style_df.apply(self.Leaf_color_cells1, axis=1, subset=['均值差值', '赢率(%)'])
                if '弯孢叶斑病(等级)' in self.trait_column_name_to_chinese_name_dict[trait_column_name]:  # 大斑，灰斑， 锈病，白斑，弯包叶斑
                    style_df = style_df.apply(self.Leaf_color_cells, subset=['目标品种均值'])
                    style_df = style_df.apply(self.Leaf_color_cells1, axis=1, subset=['均值差值', '赢率(%)'])
                st.dataframe(style_df)

if __name__ == '__main__':
# def main():
    st.set_page_config(layout='wide')
    ck_query_statement = """
                         select * from "DWS"."TDPheno2024"
                          """
    pheno_query_statement = """
                            select * from "DWS"."TDPheno2024" 
                            """
    ckTable = CKTable(ck_query_statement)
    phenoTable = PhenoTable(pheno_query_statement)
    plot = Plot(ckTable, phenoTable)
    plot.plot()

