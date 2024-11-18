import numpy as np
import streamlit as st
import pandas as pd
from pygments import highlight


class CKTable:
    def __init__(self, query_statement):
        self.query_statement = query_statement
        self.data_df = self.__get_data_df()
        self.entrybookname_list = self.__get_entrybookname_list()

    def __get_data_df(self):
        conn = st.connection("postgres")
        self.data_df = conn.query(self.query_statement)
        return self.data_df

    # 获取生态亚区
    def __get_entrybookname_list(self):
        entrybookname_list = pd.unique(self.data_df["AOA"]).tolist()
        return entrybookname_list

    # 获取对照试验点样本名list
    def get_ck_name_list(self, selected_entrybookname_list):
        ck_name_list = pd.unique(self.data_df[self.data_df["AOA"].isin(selected_entrybookname_list)]["Name"]).tolist()
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
    def get_sample_name_list(self, selected_entrybookname_list):
        sample_name_list = pd.unique(self.data_df[self.data_df["EntryBookName"].isin(selected_entrybookname_list)]
                                     ["Varnam"]).tolist()
        return sample_name_list

    def get_sample_pheno_df(self, selected_year_list, selected_entrybookname, selected_target_name_list):
        sample_pheno_df = self.data_df[(self.data_df["Year"].isin(selected_year_list)) &
                                       (self.data_df["EntryBookName"] == selected_entrybookname) &
                                       (self.data_df["Varnam"].isin(selected_target_name_list))]
        return sample_pheno_df

    def get_ck_pheno_df(self, selected_year_list, selected_entrybookname, selected_ck_name_list):
        ck_pheno_df = self.data_df[(self.data_df["Year"].isin(selected_year_list)) &
                                   (self.data_df["EntryBookName"] == selected_entrybookname) &
                                   (self.data_df["Varnam"].isin([selected_ck_name_list]))]
        return ck_pheno_df

    def get_percent_pressure_bookname_num(self, selected_year_list, selected_entrybookname, trait_column_name):
        # 百分比表的 压力点次
        pressure_bookname_num = 0
        data_df = self.data_df[(self.data_df["Year"].isin(selected_year_list)) &
                               (self.data_df["EntryBookName"] == selected_entrybookname)]
        bookname_set = set(data_df["BookName"])
        for bookname in bookname_set:
            data_df = data_df[data_df["BookName"] == bookname]
            if any(data_df[trait_column_name] > 0):     #百分比制的 越小越好，最小为0%
                pressure_bookname_num += 1
        return pressure_bookname_num

    def get_grade_pressure_bookname_num(self, selected_year_list, selected_entrybookname, trait_column_name):
        # 打分级表的 压力点次
        pressure_bookname_num = 0
        data_df = self.data_df[(self.data_df["Year"].isin(selected_year_list)) &
                               (self.data_df["EntryBookName"] == selected_entrybookname)]
        bookname_set = set(data_df["BookName"])
        for bookname in bookname_set:
            data_df = data_df[data_df["BookName"] == bookname]
            if any(data_df[trait_column_name] != 9):     ## 暂时为打分越大越好  9为最大
                pressure_bookname_num += 1
        return pressure_bookname_num

class DataFrameColor:
    # 根据规则进行上色功能     主要针对均值和上色率
    def __init__(self, dataframe):
        #  此处的dataframe = summary_data_df
        self.dataframe = dataframe

    def color_cells(self, row):
        # 按照评分规则进行完善
        colors = []  # 便利获取所有的行
        for value in row:
            if isinstance(value, float) and value >= 0.9:
                colors.append("background-color:green")
            elif isinstance(value, float) and value >= 0.7:
                colors.append("background-color:yellow")
            elif isinstance(value, float):
                colors.append('background-color:blue')
            else:
                colors.append('')
        # color = 'background-color:yellow' if val['品种综合评分']>0.7 else 'background-color:blue'    # 单一的
        return colors

    def plot(self):
        # 可以选择在此处完成颜色添加
        dataframe = self.dataframe
        st.dataframe(dataframe, hide_index=True)    # 隐藏索引列
        # 应用颜色填充
        style_df = dataframe.style.apply(self.color_cells,axis=1)    # axis=1 按列方向进行应用
        # 展示带颜色的DataFrame
        st.write(style_df)


class Plot:
    def __init__(self, ckTable: CKTable, phenoTable: PhenoTable):
        self.ckTable = ckTable
        self.phenoTable = phenoTable
        self.trait_column_name_to_chinese_name_dict = {'YLD14': '产量(kg/亩)',
                                                       'MST': '水分(%)',
                                                       # 'PHT': '株高(cm)',
                                                       # 'EHT': '穗位(cm)',
                                                       'STKLPCT': '茎倒比例(%)',
                                                       'PMDPCT': '青枯病比例(%)',
                                                       'BARPCT': '空杆比例(%)',
                                                       'EARTPCT': '穗腐比例(%)',
                                                       'KERTPCT': '穗腐/霉变粒比例(%)',
                                                       'NCLB': '大斑病(等级)',
                                                       'GLS': '灰斑病(等级)',
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
            selected_entrybookname_list = st.multiselect(
                '生态亚区',
                self.ckTable.entrybookname_list,
                default=self.ckTable.entrybookname_list[0:2]
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
                self.ckTable.get_ck_name_list(selected_entrybookname_list)
            )
        with column_list[1]:
            selected_target_name_list = st.multiselect(
                '目标品种',
                self.phenoTable.get_sample_name_list(selected_entrybookname_list),
                default=self.phenoTable.get_sample_name_list(selected_entrybookname_list)[0]
            )
            if len(selected_target_name_list) == 0:
                selected_target_name_list = [self.phenoTable.get_sample_name_list(selected_entrybookname_list)[0]]
        return (selected_year_list, selected_entrybookname_list, selected_trait_column_list, selected_ck_name,
                selected_target_name_list)

    def get_sample_data_df(self, year_list, entrybookname_list, name_list, trait_column):
        data_df = self.phenoTable.data_df
        data_df = data_df[~pd.isna(data_df[trait_column])]
        sample_data_df = data_df[data_df["Year"].isin(year_list) & data_df["EntryBookName"].isin(entrybookname_list)
                                 & data_df["Varnam"].isin(name_list)]
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
    def get_num_trait_summary(self, year, entrybookname_list, sample_data_df, ck_data_df, trait_column_name):
        self.__get_sub_tilte(self.trait_column_name_to_chinese_name_dict[trait_column_name])    # 子标题
        threshold = st.slider("阈值选择", min_value=0, max_value=300, value=0)
        sample_name_set, ck_name= pd.unique(sample_data_df['Varnam']), pd.unique(ck_data_df['Varnam'])[0]  # 样本和对照品种名称的数据
        ck_bookname_set = pd.unique(ck_data_df[ck_data_df['Varnam'] == ck_name]["BookName"])
        num_trait_summary_df = pd.DataFrame()   # 存储num型结果数据
        aoa_name = ["" + f"{item} " for item in entrybookname_list][0]
        for sample_name in sample_name_set:
            single_sample_num_trait_summary_dict = {}
            sample_bookname_set = pd.unique(sample_data_df[sample_data_df['Varnam'] == sample_name]["BookName"])  # 样本测试点的集合
            bookname_intersection_set = set(ck_bookname_set).intersection(sample_bookname_set)   # 取对照和目标测试点的交集
            ck_bookname_num, sample_bookname_num = len(ck_bookname_set), len(sample_bookname_set)
            bookname_intersection_num = len(bookname_intersection_set)
            #                                               增加量
            sample_trait_value_list, ck_trait_value_list, increase_num = [], [], 0  # 初始化
            for bookname in bookname_intersection_set:     # 对照样本与目标样本在同一测试点下的比较  故要选取 对照样本所在测试点与 目标样本所在测试点的交集
                try:
                    sample_trait_value = sample_data_df[sample_data_df['Varnam'] == sample_name
                                                             & sample_data_df['BookName'] == bookname][
                        trait_column_name].tolist()[0]
                except:
                    print(sample_data_df)
                ck_trait_value = ck_data_df[ck_data_df['Varnam'] == sample_name
                                                 & sample_data_df['BookName'] == bookname][
                    trait_column_name].tolist()[0]
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
            # trait_name = self.trait_column_name_to_chinese_name_dict[trait_column_name]
            single_sample_num_trait_summary_dict["年份"] = year
            single_sample_num_trait_summary_dict["生态亚区"] = aoa_name
            single_sample_num_trait_summary_dict["目标品种"] = sample_name
            single_sample_num_trait_summary_dict[f"目标品种种植点次"] = sample_bookname_num
            single_sample_num_trait_summary_dict["对比品种"] = ck_name
            single_sample_num_trait_summary_dict[f"对照品种种植点次"] = ck_bookname_num
            single_sample_num_trait_summary_dict[f"对比点数"] = bookname_intersection_num
            single_sample_num_trait_summary_dict[f"增产点数"] = increase_num
            single_sample_num_trait_summary_dict[f"赢率（%）"] = increase_rate                                   # 要上色
            single_sample_num_trait_summary_dict[f"目标品种产量均值"] = sample_trait_mean_value
            single_sample_num_trait_summary_dict[f"对比品种产量均值"] = ck_trait_mean_value
            single_sample_num_trait_summary_dict[f"增减产值"] = difference_value
            single_sample_num_trait_summary_dict[f"增减产（%）"] = difference_rate                                # 要上色
            single_sample_num_trait_summary_dict[f'综合判定'] = np.nan                     ########## 要完善
            single_sample_num_trait_summary_df = pd.DataFrame(single_sample_num_trait_summary_dict)  # 将dict数据转化为DataFrame格式
            num_trait_summary_df = pd.concat([num_trait_summary_df, single_sample_num_trait_summary_df],
                                             ignore_index=True)  # 数据拼接（每行为一个样本）
        return num_trait_summary_df

    # 水分summary计算    没有阈值选择项、增长量、赢率 相关
    def get_mst_trait_summary(self, year, entrybookname_list, sample_data_df, ck_data_df, trait_column_name):
        self.__get_sub_tilte(self.trait_column_name_to_chinese_name_dict[trait_column_name])
        sample_name_set, ck_name= pd.unique(sample_data_df['Varnam']), pd.unique(ck_data_df['Varnam'])[0]
        ck_bookname_set = pd.unique(ck_data_df[ck_data_df['Varnam'] == ck_name]["BookName"])
        num_trait_summary_df = pd.DataFrame()
        aoa_name = ["" + f"{item} " for item in entrybookname_list][0]
        for sample_name in sample_name_set:
            single_sample_num_trait_summary_dict = {}
            sample_bookname_set = pd.unique(sample_data_df[sample_data_df['Varnam'] == sample_name]["BookName"])
            bookname_intersection_set = set(ck_bookname_set).intersection(sample_bookname_set)
            ck_bookname_num, sample_bookname_num = len(ck_bookname_set), len(sample_bookname_set)
            bookname_intersection_num = len(bookname_intersection_set)
            sample_trait_value_list, ck_trait_value_list = [], []
            for bookname in bookname_intersection_set:
                sample_trait_value = sample_data_df[sample_data_df['Varnam'] == sample_name
                                                         & sample_data_df['BookName'] == bookname][
                    trait_column_name].tolist()[0]
                ck_trait_value = ck_data_df[ck_data_df['Varnam'] == sample_name
                                                 & sample_data_df['BookName'] == bookname][
                    trait_column_name].tolist()[0]
                sample_trait_value_list.append(sample_trait_value)
                ck_trait_value_list.append(ck_trait_value)
            sample_trait_mean_value = np.mean(sample_trait_value_list)
            ck_trait_mean_value = np.mean(ck_trait_value_list)
            difference_value = sample_trait_mean_value - ck_trait_mean_value
            difference_rate = difference_value / ck_trait_mean_value * 100
            # trait_name = self.trait_column_name_to_chinese_name_dict[trait_column_name]
            single_sample_num_trait_summary_dict["年份"] = year
            single_sample_num_trait_summary_dict["生态亚区"] = aoa_name
            single_sample_num_trait_summary_dict["目标品种"] = sample_name
            single_sample_num_trait_summary_dict[f"目标品种种植点次"] = sample_bookname_num
            single_sample_num_trait_summary_dict["对比品种"] = ck_name
            single_sample_num_trait_summary_dict[f"对照品种种植点次"] = ck_bookname_num
            single_sample_num_trait_summary_dict[f"对比点数"] = bookname_intersection_num
            single_sample_num_trait_summary_dict[f"目标品种收获水分均值"] = sample_trait_mean_value
            single_sample_num_trait_summary_dict[f"对比品种收获水分均值"] = ck_trait_mean_value
            single_sample_num_trait_summary_dict[f"收获水分差值"] = difference_value                              # 要上色
            single_sample_num_trait_summary_dict[f'综合判定'] = np.nan                  ########## 要完善
            single_sample_num_trait_summary_df = pd.DataFrame(single_sample_num_trait_summary_dict)
            num_trait_summary_df = pd.concat([num_trait_summary_df, single_sample_num_trait_summary_df],
                                             ignore_index=True)    #忽略原有索引
        return num_trait_summary_df

    # 百分制 summary计算
    def get_percent_trait_summary(self, year, entrybookname_list, sample_data_df, ck_data_df, trait_column_name):
        self.__get_sub_tilte(self.trait_column_name_to_chinese_name_dict[trait_column_name])
        threshold = st.slider(f"{self.trait_column_name_to_chinese_name_dict[trait_column_name]}阈值选择", min_value=0, max_value=100, value=0)
        sample_name_set, ck_name= pd.unique(sample_data_df['Varnam']), pd.unique(ck_data_df['Varnam'])[0]
        ck_bookname_set = pd.unique(ck_data_df[ck_data_df['Varnam'] == ck_name]["BookName"])
        percent_trait_summary_df = pd.DataFrame()
        aoa_name = ["" + f"{item} " for item in entrybookname_list][0]
        for sample_name in sample_name_set:
            single_sample_num_trait_summary_dict = {}
            sample_bookname_set = pd.unique(sample_data_df[sample_data_df['Varnam'] == sample_name]["BookName"])
            bookname_intersection_set = set(ck_bookname_set).intersection(sample_bookname_set)
            ck_bookname_num, sample_bookname_num = len(ck_bookname_set), len(sample_bookname_set)
            bookname_intersection_num = len(bookname_intersection_set)
            sample_trait_value_list, ck_trait_value_list, increase_num = [], [], 0
            for bookname in bookname_intersection_set:
                sample_trait_value = sample_data_df[sample_data_df['Varnam'] == sample_name
                                                         & sample_data_df['BookName'] == bookname][
                    trait_column_name].tolist()[0]
                ck_trait_value = ck_data_df[ck_data_df['Varnam'] == sample_name
                                                 & sample_data_df['BookName'] == bookname][
                    trait_column_name].tolist()[0]
                sample_trait_value_list.append(sample_trait_value)
                ck_trait_value_list.append(ck_trait_value)
                if sample_trait_value - ck_trait_value < threshold:        ##### 百分制这里是    小于阈值
                    increase_num += 1
            if bookname_intersection_num != 0:
                increase_rate = increase_num / bookname_intersection_num * 100
            else:
                increase_rate = np.nan
            sample_trait_mean_value = np.mean(sample_trait_value_list)
            ck_trait_mean_value = np.mean(ck_trait_value_list)
            difference_value = sample_trait_mean_value - ck_trait_mean_value
            # difference_rate = difference_value / ck_trait_mean_value
            # trait_name = self.trait_column_name_to_chinese_name_dict[trait_column_name]
            single_sample_num_trait_summary_dict["年份"] = year
            single_sample_num_trait_summary_dict["生态亚区"] = aoa_name
            single_sample_num_trait_summary_dict["目标品种"] = sample_name
            single_sample_num_trait_summary_dict[f"目标品种种植点次"] = sample_bookname_num
            single_sample_num_trait_summary_dict["对比品种"] = ck_name
            single_sample_num_trait_summary_dict[f"对照品种种植点次"] = ck_bookname_num
            single_sample_num_trait_summary_dict[f"对比点数"] = bookname_intersection_num
            single_sample_num_trait_summary_dict[f"赢点数"] = increase_num
            single_sample_num_trait_summary_dict[f"赢率（%）"] = increase_rate                    # 上色
            single_sample_num_trait_summary_dict[f"目标品种均值"] = sample_trait_mean_value
            single_sample_num_trait_summary_dict[f"对比品种均值"] = ck_trait_mean_value
            single_sample_num_trait_summary_dict[f"均值差值"] = difference_value                  # 上色
            single_sample_num_trait_summary_dict[f'目标品种极小值'] = np.min(sample_trait_value_list) if len(sample_trait_value_list) != 0 else np.nan
            single_sample_num_trait_summary_dict[f"对照品种极小值"] = np.min(ck_trait_value_list) if len(ck_trait_value_list) != 0 else np.nan
            single_sample_num_trait_summary_dict[f'极小值差值'] = np.min(sample_trait_value_list) - np.min(ck_trait_value_list) if len(sample_trait_value_list) != 0 and len(ck_trait_value_list) != 0 else np.nan
            single_sample_num_trait_summary_dict[f"目标品种极大值"] = np.max(sample_trait_value_list) if len(sample_trait_value_list) != 0 else np.nan
            single_sample_num_trait_summary_dict[f'目标品种极大值'] = np.max(ck_trait_value_list) if len(ck_trait_value_list) != 0 else np.nan
            single_sample_num_trait_summary_dict[f'极大值差值'] = np.max(sample_trait_value_list) - np.max(ck_trait_value_list) if len(sample_trait_value_list) != 0 and len(ck_trait_value_list) != 0 else np.nan
            single_sample_num_trait_summary_dict[f'综合判定'] = np.nan                    ########## 要完善
            single_sample_num_trait_summary_df = pd.DataFrame(single_sample_num_trait_summary_dict)
            percent_trait_summary_df = pd.concat([percent_trait_summary_df, single_sample_num_trait_summary_df],
                                             ignore_index=True)
        return percent_trait_summary_df

    # 打等级制 summary计算
    def get_grade_trait_summary(self, year, entrybookname_list, sample_data_df, ck_data_df, trait_column_name):
        self.__get_sub_tilte(self.trait_column_name_to_chinese_name_dict[trait_column_name])
        threshold = st.slider(f"{self.trait_column_name_to_chinese_name_dict[trait_column_name]}阈值选择", min_value=0, max_value=10, value=0)   # 阈值设置确认一下
        sample_name_set, ck_name= pd.unique(sample_data_df['Varnam']), pd.unique(ck_data_df['Varnam'])[0]
        ck_bookname_set = pd.unique(ck_data_df[ck_data_df['Varnam'] == ck_name]["BookName"])
        grade_trait_summary_df = pd.DataFrame()
        aoa_name = ["" + f"{item} " for item in entrybookname_list][0]
        for sample_name in sample_name_set:
            single_sample_num_trait_summary_dict = {}
            sample_bookname_set = pd.unique(sample_data_df[sample_data_df['Varnam'] == sample_name]["BookName"])
            bookname_intersection_set = set(ck_bookname_set).intersection(sample_bookname_set)
            ck_bookname_num, sample_bookname_num = len(ck_bookname_set), len(sample_bookname_set)
            bookname_intersection_num = len(bookname_intersection_set)
            sample_trait_value_list, ck_trait_value_list, increase_num = [], [], 0
            for bookname in bookname_intersection_set:
                sample_trait_value = sample_data_df[sample_data_df['Varnam'] == sample_name
                                                         & sample_data_df['BookName'] == bookname][
                    trait_column_name].tolist()[0]
                ck_trait_value = ck_data_df[ck_data_df['Varnam'] == sample_name
                                                 & sample_data_df['BookName'] == bookname][
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
            # trait_name = self.trait_column_name_to_chinese_name_dict[trait_column_name]
            single_sample_num_trait_summary_dict["年份"] = year
            single_sample_num_trait_summary_dict["生态亚区"] = aoa_name
            single_sample_num_trait_summary_dict["目标品种"] = sample_name
            single_sample_num_trait_summary_dict[f"目标品种种植点次"] = sample_bookname_num
            single_sample_num_trait_summary_dict["对比品种"] = ck_name
            single_sample_num_trait_summary_dict[f"对照品种种植点次"] = ck_bookname_num
            single_sample_num_trait_summary_dict[f"对比点数"] = bookname_intersection_num
            single_sample_num_trait_summary_dict[f"赢点数"] = increase_num
            single_sample_num_trait_summary_dict[f"赢率（%）"] = increase_rate                           #上色
            single_sample_num_trait_summary_dict[f"目标品种均值"] = sample_trait_mean_value
            single_sample_num_trait_summary_dict[f"对比品种均值"] = ck_trait_mean_value
            single_sample_num_trait_summary_dict[f"均值差值"] = difference_value                         # 上色
            single_sample_num_trait_summary_dict[f'目标品种极小值'] = np.min(sample_trait_value_list) if len(sample_trait_value_list) != 0 else np.nan
            single_sample_num_trait_summary_dict[f"对照品种极小值"] = np.min(ck_trait_value_list) if len(ck_trait_value_list) != 0 else np.nan
            single_sample_num_trait_summary_dict[f'极小值差值'] = np.min(sample_trait_value_list) - np.min(ck_trait_value_list) if len(sample_trait_value_list) != 0 and len(ck_trait_value_list) != 0 else np.nan
            single_sample_num_trait_summary_dict[f"目标品种极大值"] = np.max(sample_trait_value_list) if len(sample_trait_value_list) != 0 else np.nan
            single_sample_num_trait_summary_dict[f'目标品种极大值'] = np.max(ck_trait_value_list) if len(ck_trait_value_list) != 0 else np.nan
            single_sample_num_trait_summary_dict[f'极大值差值'] = np.max(sample_trait_value_list) - np.max(ck_trait_value_list) if len(sample_trait_value_list) != 0 and len(ck_trait_value_list) != 0 else np.nan
            single_sample_num_trait_summary_dict[f'综合判定'] = np.nan                      ########## 要完善
            single_sample_num_trait_summary_df = pd.DataFrame(single_sample_num_trait_summary_dict)
            grade_trait_summary_df = pd.concat([grade_trait_summary_df, single_sample_num_trait_summary_df],
                                             ignore_index=True)
        return grade_trait_summary_df

    def add_color(self,row):
        style_color =[]
        if 1<row[f"对照品种种植点次"]<6:
            style_color.append('background-color:yellow')
        else:
            'gfdg'
        return [style_color]

    def plot(self):
        (selected_year_list, selected_entrybookname_list, selected_trait_column_list, selected_ck_name,
         selected_target_name_list) = self.__get_dropdown_men_bar()
        # selected_trait_column_list = self.trait_column_name_to_chinese_name_dict.keys()
        for trait_column_name in selected_trait_column_list:
            sample_data_df = self.get_sample_data_df(selected_year_list, selected_entrybookname_list,
                                                     selected_target_name_list, trait_column_name)
            ck_data_df = self.get_sample_data_df(selected_year_list, selected_entrybookname_list,
                                                 [selected_ck_name], trait_column_name)
            if len(sample_data_df) == 0 or len(ck_data_df) == 0:
                continue
            if "YLD" in trait_column_name:
                trait_summary_df = self.get_num_trait_summary(selected_year_list, selected_entrybookname_list,
                                                                  sample_data_df, ck_data_df, trait_column_name)
               # st.dataframe(trait_summary_df)
                style_df = trait_summary_df.style.apply(self.add_color,axis=1,subset =[f"对照品种种植点次"])
                st.dataframe(style_df)
            elif "MST" in trait_column_name:
                trait_summary_df = self.get_mst_trait_summary(selected_year_list, selected_entrybookname_list,
                                                              sample_data_df, ck_data_df, trait_column_name)
                st.dataframe(trait_summary_df)
            elif "%" in self.trait_column_name_to_chinese_name_dict[trait_column_name]:
                trait_summary_df = self.get_percent_trait_summary(selected_year_list, selected_entrybookname_list,
                                                                  sample_data_df, ck_data_df, trait_column_name)
                st.dataframe(trait_summary_df)
            else:
                trait_summary_df = self.get_grade_trait_summary(selected_year_list, selected_entrybookname_list,
                                                                  sample_data_df, ck_data_df, trait_column_name)
                st.dataframe(trait_summary_df)
        # DataFrameColor(dataframe=trait_summary_df).plot


if __name__ == '__main__':
    st.set_page_config(layout='wide')
    ck_query_statement = """
        select * from "DWS"."TDCK"
        """
    pheno_query_statement = """
        select * from "DWS"."Pheno" p where p."EntryBookPrj" = 'TD'
        """
    ckTable = CKTable(ck_query_statement)
    phenoTable = PhenoTable(pheno_query_statement)
    plot = Plot(ckTable, phenoTable)
    plot.plot()

