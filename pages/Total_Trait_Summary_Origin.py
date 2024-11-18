import numpy as np
import streamlit as st
import pandas as pd


class CKTable:
    def __init__(self, query_statement):
        self.query_statement = query_statement
        self.data_df = self.__get_data_df()
        self.entrybookname_list = self.__get_entrybookname_list()

    def __get_data_df(self):
        conn = st.connection("postgres")
        self.data_df = conn.query(self.query_statement)
        return self.data_df

    def __get_entrybookname_list(self):
        entrybookname_list = pd.unique(self.data_df["AOA"]).tolist()
        return entrybookname_list

    def get_ck_name_list(self, selected_entrybookname):
        ck_name_list = pd.unique(self.data_df[self.data_df["AOA"] == selected_entrybookname]["Name"]).tolist()
        return ck_name_list


class DataFrameColor:
    def __init__(self, dataframe):
        self.dataframe = dataframe

    def plot(self):
        # 可以选择在此处完成颜色添加
        dataframe = self.dataframe
        st.dataframe(dataframe, hide_index=True)


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

    def get_sample_name_list(self, selected_entrybookname):
        sample_name_list = pd.unique(self.data_df[self.data_df["EntryBookName"] ==
                                                  selected_entrybookname]["Varnam"]).tolist()
        return sample_name_list

    def get_sample_pheno_df(self, selected_year_list, selected_entrybookname, selected_target_name_list):
        sample_pheno_df = self.data_df[(self.data_df["Year"].isin(selected_year_list)) &
                                       (self.data_df["EntryBookName"] == selected_entrybookname) &
                                       (self.data_df["Varnam"].isin(selected_target_name_list))]
        return sample_pheno_df

    def get_percent_pressure_bookname_num(self, selected_year_list, selected_entrybookname, trait_column_name):
        pressure_bookname_num = 0
        data_df = self.data_df[(self.data_df["Year"].isin(selected_year_list)) &
                               (self.data_df["EntryBookName"] == selected_entrybookname)]
        bookname_set = set(data_df["BookName"])
        for bookname in bookname_set:
            data_df = data_df[data_df["BookName"] == bookname]
            if any(data_df[trait_column_name] > 0):
                pressure_bookname_num += 1
        return pressure_bookname_num

    def get_grade_pressure_bookname_num(self, selected_year_list, selected_entrybookname, trait_column_name):
        pressure_bookname_num = 0
        data_df = self.data_df[(self.data_df["Year"].isin(selected_year_list)) &
                               (self.data_df["EntryBookName"] == selected_entrybookname)]
        bookname_set = set(data_df["BookName"])
        for bookname in bookname_set:
            data_df = data_df[data_df["BookName"] == bookname]
            if any(data_df[trait_column_name] != 9):
                pressure_bookname_num += 1
        return pressure_bookname_num

    def get_ck_pheno_df(self, selected_year_list, selected_entrybookname, selected_ck_name_list):
        ck_pheno_df = self.data_df[(self.data_df["Year"].isin(selected_year_list)) &
                                   (self.data_df["EntryBookName"] == selected_entrybookname) &
                                   (self.data_df["Varnam"].isin([selected_ck_name_list]))]
        return ck_pheno_df


class Plot:
    def __init__(self, ckTable: CKTable, phenoTable: PhenoTable):
        self.ckTable = ckTable
        self.phenoTable = phenoTable
        # self.num_trait_list = ['YLD14', 'MST', 'PHT', 'EHT']
        # self.grade_trait_list = ['STKLPCT', 'PMDPCT', 'BARPCT', 'EARTPCT', 'KERTPCT', 'NCLB', 'GLS', 'HUSKCOV', 'KERSR',
        #                          'TIPFILL']
        self.trait_column_name_to_chinese_name_dict = {'YLD14': '产量(kg/亩)',
                                                       'MST': '水分(%)',
                                                       'PHT': '株高(cm)',
                                                       'EHT': '穗位(cm)',
                                                       'STKLPCT': '茎倒比例(%)',
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
        self.trait_weight_coefficient_dict = {
            'YLD14': 1,
            'MST': -1,  # 水分赋值注意符号
            'PHT': 1,
            'EHT': 1,
            'STKLPCT': 1,
            'PMDPCT': 1,
            'BARPCT': 1,
            'EARTPCT': 1,
            'KERTPCT': 1,
            'NCLB': 1,
            'GLS': 1,
            'HUSKCOV': 1,
            'KERSR': 1,
            'TIPFILL': 1
        }

    def get_dropdown_menu_bar(self):
        column_list = st.columns((2, 1, 3, 1))
        with column_list[0]:
            selected_year_list = st.multiselect(
                '年份',
                self.phenoTable.year_list,
                default=self.phenoTable.year_list[0]
            )
            if len(selected_year_list) == 0:
                selected_year_list = [self.phenoTable.year_list[0]]
        with column_list[1]:
            selected_entrybookname = st.selectbox(
                '生态亚区',
                self.ckTable.entrybookname_list
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
        with column_list[3]:
            selected_caculate_method = st.selectbox(
                '点次统计方式',
                ["测试点取交集", "测试点取并集"]
            )
        column_list = st.columns((1, 5))
        with column_list[0]:
            selected_ck_name = st.selectbox(
                '对照品种',
                self.ckTable.get_ck_name_list(selected_entrybookname)
            )
        with column_list[1]:
            selected_target_name_list = st.multiselect(
                '目标品种',
                self.phenoTable.get_sample_name_list(selected_entrybookname),
                default=self.phenoTable.get_sample_name_list(selected_entrybookname)[0]
            )
            if len(selected_target_name_list) == 0:
                selected_target_name_list = [self.phenoTable.get_sample_name_list(selected_entrybookname)[0]]
        return (selected_year_list, selected_entrybookname, selected_target_name_list, selected_ck_name,
                selected_trait_column_list, selected_caculate_method)

    def __data_preprocessing(self, sample_data_df, ck_data_df, caculate_method):
        # 数据预处理：根据选择的数据处理方法，对数据中的测试点提取交集数据或者并集数据；
        sample_bookname_set, ck_bookname_set = set(sample_data_df["BookName"]), set(ck_data_df["BookName"])
        bookname_set = None
        if "交集" in caculate_method:
            bookname_set = sample_bookname_set & ck_bookname_set
        if "并集" in caculate_method:
            bookname_set = ck_bookname_set | sample_bookname_set
        sample_data_df = sample_data_df[sample_data_df["BookName"].isin(bookname_set)]
        ck_data_df = ck_data_df[ck_data_df["BookName"].isin(bookname_set)]
        return sample_data_df, ck_data_df

    def __single_sample_num_summary_caculate(self, single_sample_data_df, ck_data_df, trait_column_name_list):
        single_sample_summary_df = pd.DataFrame({
            '品种综合评分': [np.nan],
            '产量排序': [np.nan]
        })
        temp_single_sample_summary_df = None
        for trait_column_name in trait_column_name_list:
            single_sample_plot_count = len(single_sample_data_df)
            single_sample_data_df = single_sample_data_df[~pd.isna(single_sample_data_df[trait_column_name])]
            ck_data_df = ck_data_df[~pd.isna(ck_data_df[trait_column_name])]
            single_sample_trait_count = len(single_sample_data_df)
            single_sample_trait_mean = np.mean(single_sample_data_df[trait_column_name])
            ck_trait_mean = np.mean(ck_data_df[trait_column_name])
            single_sample_trait_max = np.max(single_sample_data_df[trait_column_name])
            single_sample_trait_min = np.min(single_sample_data_df[trait_column_name])
            trait_column_name = self.trait_column_name_to_chinese_name_dict[trait_column_name].split("(")[0]
            difference = single_sample_trait_mean - ck_trait_mean
            single_sample_trait_summary_df = pd.DataFrame({
                '品种名称': single_sample_data_df["Varnam"].unique() if len(single_sample_data_df["Varnam"].unique()) != 0 else [np.nan],
                '对照名称': ck_data_df["Varnam"].unique() if len(ck_data_df["Varnam"].unique()) != 0 else [np.nan],
                '年份': single_sample_data_df["Year"].unique() if len(single_sample_data_df["Year"].unique()) != 0 else [np.nan],
                '生态亚区': single_sample_data_df['EntryBookName'].unique() if len(single_sample_data_df['EntryBookName'].unique()) != 0 else [np.nan],
                '种植点次': single_sample_plot_count,
                f'{trait_column_name}统计点次': single_sample_trait_count,
                f'{trait_column_name}均值': single_sample_trait_mean,
                f'{trait_column_name}标准化': [np.nan],
                f'{trait_column_name}比对差异': [difference],
                f'{trait_column_name}极大值': single_sample_trait_max,
                f'{trait_column_name}极小值': single_sample_trait_min
            })
            single_sample_trait_summary_df[["品种名称", "对照名称", "生态亚区"]] = (
                single_sample_trait_summary_df[["品种名称", "对照名称", "生态亚区"]].astype(object))
            if temp_single_sample_summary_df is None:
                temp_single_sample_summary_df = single_sample_trait_summary_df
            else:
                temp_single_sample_summary_df = pd.merge(left=temp_single_sample_summary_df,
                                                         right=single_sample_trait_summary_df,
                                                         on=["品种名称", "对照名称", "年份", "生态亚区", "种植点次"],
                                                         how='left')
        single_sample_summary_df = pd.concat([single_sample_summary_df, temp_single_sample_summary_df], axis=1)
        return single_sample_summary_df

    def __single_sample_grade_summary_caculate(self, single_sample_data_df, ck_data_df, trait_column_name_list,
                                               selected_year_list, selected_entrybookname):
        single_sample_summary_df = pd.DataFrame({
            '品种综合评分': [np.nan],
            '产量排序': [np.nan]
        })
        temp_single_sample_summary_df = None
        for trait_column_name in trait_column_name_list:
            single_sample_plot_count = len(single_sample_data_df)
            single_sample_data_df = single_sample_data_df[~pd.isna(single_sample_data_df[trait_column_name])]
            ck_data_df = ck_data_df[~pd.isna(ck_data_df[trait_column_name])]
            pressure_bookname_num = self.phenoTable.get_grade_pressure_bookname_num(selected_year_list, selected_entrybookname
                                                                              , trait_column_name)
            single_sample_trait_count = len(single_sample_data_df)
            occur_incidence_rate = single_sample_trait_count / pressure_bookname_num * 100 if pressure_bookname_num != 0 else np.nan
            single_sample_trait_mean = np.mean(single_sample_data_df[trait_column_name])
            ck_trait_mean = np.mean(ck_data_df[trait_column_name])
            single_sample_trait_max = np.max(single_sample_data_df[trait_column_name])
            single_sample_trait_min = np.min(single_sample_data_df[trait_column_name])
            trait_column_name = self.trait_column_name_to_chinese_name_dict[trait_column_name].split("(")[0]
            difference = single_sample_trait_mean - ck_trait_mean
            single_sample_trait_summary_df = pd.DataFrame({
                '品种名称': single_sample_data_df["Varnam"].unique() if len(
                    single_sample_data_df["Varnam"].unique()) != 0 else [np.nan],
                '对照名称': ck_data_df["Varnam"].unique() if len(ck_data_df["Varnam"].unique()) != 0 else [np.nan],
                '年份': single_sample_data_df["Year"].unique() if len(
                    single_sample_data_df["Year"].unique()) != 0 else [np.nan],
                '生态亚区': single_sample_data_df['EntryBookName'].unique() if len(
                    single_sample_data_df['EntryBookName'].unique()) != 0 else [np.nan],
                '种植点次': single_sample_plot_count,
                f'有{trait_column_name}压力的点次': pressure_bookname_num,
                f'{trait_column_name}发生率(%)': [occur_incidence_rate],
                f'{trait_column_name}极大值': single_sample_trait_max,
                f'{trait_column_name}极小值': single_sample_trait_min,
                f'{trait_column_name}标准化': [np.nan],
                f'{trait_column_name}均值': [single_sample_trait_mean]
            })
            single_sample_trait_summary_df[["品种名称", "对照名称", "生态亚区"]] = (
                single_sample_trait_summary_df[["品种名称", "对照名称", "生态亚区"]].astype(object))
            if temp_single_sample_summary_df is None:
                temp_single_sample_summary_df = single_sample_trait_summary_df
            else:
                temp_single_sample_summary_df = pd.merge(left=temp_single_sample_summary_df,
                                                         right=single_sample_trait_summary_df,
                                                         on=["品种名称", "对照名称", "年份", "生态亚区", "种植点次"],
                                                         how='left')
        single_sample_summary_df = pd.concat([single_sample_summary_df, temp_single_sample_summary_df], axis=1)
        return single_sample_summary_df

    def __single_sample_percent_summary_caculate(self, single_sample_data_df, ck_data_df, trait_column_name_list,
                                               selected_year_list, selected_entrybookname):
        single_sample_summary_df = pd.DataFrame({
            '品种综合评分': [np.nan],
            '产量排序': [np.nan]
        })
        temp_single_sample_summary_df = None
        for trait_column_name in trait_column_name_list:
            single_sample_plot_count = len(single_sample_data_df)
            single_sample_data_df = single_sample_data_df[~pd.isna(single_sample_data_df[trait_column_name])]
            ck_data_df = ck_data_df[~pd.isna(ck_data_df[trait_column_name])]
            pressure_bookname_num = self.phenoTable.get_percent_pressure_bookname_num(selected_year_list, selected_entrybookname
                                                                              , trait_column_name)
            single_sample_trait_count = len(single_sample_data_df)
            occur_incidence_rate = single_sample_trait_count / pressure_bookname_num * 100 if pressure_bookname_num != 0 else np.nan
            single_sample_trait_mean = np.mean(single_sample_data_df[trait_column_name])
            ck_trait_mean = np.mean(ck_data_df[trait_column_name])
            single_sample_trait_max = np.max(single_sample_data_df[trait_column_name])
            single_sample_trait_min = np.min(single_sample_data_df[trait_column_name])
            trait_column_name = self.trait_column_name_to_chinese_name_dict[trait_column_name].split("比例")[0]
            difference = single_sample_trait_mean - ck_trait_mean
            single_sample_trait_summary_df = pd.DataFrame({
                '品种名称': single_sample_data_df["Varnam"].unique() if len(
                    single_sample_data_df["Varnam"].unique()) != 0 else [np.nan],
                '对照名称': ck_data_df["Varnam"].unique() if len(ck_data_df["Varnam"].unique()) != 0 else [np.nan],
                '年份': single_sample_data_df["Year"].unique() if len(
                    single_sample_data_df["Year"].unique()) != 0 else [np.nan],
                '生态亚区': single_sample_data_df['EntryBookName'].unique() if len(
                    single_sample_data_df['EntryBookName'].unique()) != 0 else [np.nan],
                '种植点次': single_sample_plot_count,
                f'有{trait_column_name}压力的点次': pressure_bookname_num,
                f'{trait_column_name}发生率(%)': [occur_incidence_rate],
                f'{trait_column_name}极大值': single_sample_trait_max,
                f'{trait_column_name}极小值': single_sample_trait_min,
                f'{trait_column_name}标准化': [np.nan],
                f'{trait_column_name}均值': [single_sample_trait_mean]
            })
            single_sample_trait_summary_df[["品种名称", "对照名称", "生态亚区"]] = (
                single_sample_trait_summary_df[["品种名称", "对照名称", "生态亚区"]].astype(object))
            if temp_single_sample_summary_df is None:
                temp_single_sample_summary_df = single_sample_trait_summary_df
            else:
                temp_single_sample_summary_df = pd.merge(left=temp_single_sample_summary_df,
                                                         right=single_sample_trait_summary_df,
                                                         on=["品种名称", "对照名称", "年份", "生态亚区", "种植点次"],
                                                         how='left')
        single_sample_summary_df = pd.concat([single_sample_summary_df, temp_single_sample_summary_df], axis=1)
        return single_sample_summary_df

    def __get_normalized_trait_data_df(self, summary_data_df, trait_column_name_list):
        for trait_column_name in trait_column_name_list:
            trait_column_name = self.trait_column_name_to_chinese_name_dict[trait_column_name].split("(")[0].split('比例')[0]
            summary_data_df[f"{trait_column_name}标准化"] = ((summary_data_df[f"{trait_column_name}均值"] -
                                                              np.mean(summary_data_df[f"{trait_column_name}均值"])) /
                                                             np.std(summary_data_df[f"{trait_column_name}均值"]))
        return summary_data_df

    # 对照排序
    def __get_yld_order_data_df(self, summary_data_df: pd.DataFrame) -> pd.DataFrame:
        # 产量排序
        trait_column_name = "产量均值"
        summary_data_df["产量排序"] = summary_data_df[trait_column_name].rank(ascending=False, method='min')
        ck_summary_data_df = summary_data_df.iloc[0:1, :]
        sample_summary_data_df = summary_data_df.iloc[1:, :]
        sample_summary_data_df = sample_summary_data_df.sort_values(by=[trait_column_name], ascending=False)
        summary_data_df = pd.concat([ck_summary_data_df, sample_summary_data_df], axis=0)
        return summary_data_df

    def __get_sample_score_data_df(self, summary_data_df: pd.DataFrame, trait_column_name_list) -> pd.DataFrame:
        not_null_trait_column_name_list = []
        for trait_column_name in trait_column_name_list:
            chinese_trait_column_name = self.trait_column_name_to_chinese_name_dict[trait_column_name].split("(")[0].split("比例")[0]
            if summary_data_df[f"{chinese_trait_column_name}标准化"].isnull().sum() == 0:
                not_null_trait_column_name_list.append(trait_column_name)

        def score_caculate(row: pd.DataFrame):
            score = 0
            for trait_column_name in not_null_trait_column_name_list:
                chinese_trait_column_name = self.trait_column_name_to_chinese_name_dict[trait_column_name].split("(")[0]
                score = score + row[chinese_trait_column_name + "标准化"] * self.trait_weight_coefficient_dict[trait_column_name]
            return score

        summary_data_df["品种综合评分"] = summary_data_df.apply(lambda row: score_caculate(row), axis=1)
        return summary_data_df

    def num_trait_summary(self, sample_data_df, ck_data_df, trait_column_name_list, selected_caculate_method):
        # 聚合结果
        summary_data_df = None
        sample_data_df, ck_data_df = self.__data_preprocessing(sample_data_df, ck_data_df, selected_caculate_method)
        sample_data_df = pd.concat([ck_data_df, sample_data_df], axis=0)
        for sample_name in sample_data_df["Varnam"].unique():
            single_sample_data_df = sample_data_df[sample_data_df["Varnam"] == sample_name]
            single_sample_summary_df = self.__single_sample_num_summary_caculate(single_sample_data_df, ck_data_df,
                                                                                 trait_column_name_list)
            summary_data_df = pd.concat([summary_data_df, single_sample_summary_df])
        summary_data_df = self.__get_normalized_trait_data_df(summary_data_df, trait_column_name_list)
        return summary_data_df

    def grade_trait_summary(self, sample_data_df, ck_data_df, trait_column_name_list, selected_caculate_method,
                            selected_year_list, selected_entrybookname):
        summary_data_df = None
        sample_data_df, ck_data_df = self.__data_preprocessing(sample_data_df, ck_data_df, selected_caculate_method)
        sample_data_df = pd.concat([ck_data_df, sample_data_df], axis=0)
        for sample_name in sample_data_df["Varnam"].unique():
            single_sample_data_df = sample_data_df[sample_data_df["Varnam"] == sample_name]
            single_sample_summary_df = self.__single_sample_grade_summary_caculate(single_sample_data_df, ck_data_df,
                                                                                   trait_column_name_list,
                                                                                   selected_year_list,
                                                                                   selected_entrybookname)
            summary_data_df = pd.concat([summary_data_df, single_sample_summary_df])
        summary_data_df = self.__get_normalized_trait_data_df(summary_data_df, trait_column_name_list)
        return summary_data_df

    def percent_trait_summary(self, sample_data_df, ck_data_df, trait_column_name_list, selected_caculate_method,
                            selected_year_list, selected_entrybookname):
        summary_data_df = None
        sample_data_df, ck_data_df = self.__data_preprocessing(sample_data_df, ck_data_df, selected_caculate_method)
        sample_data_df = pd.concat([ck_data_df, sample_data_df], axis=0)
        for sample_name in sample_data_df["Varnam"].unique():
            single_sample_data_df = sample_data_df[sample_data_df["Varnam"] == sample_name]
            single_sample_summary_df = self.__single_sample_percent_summary_caculate(single_sample_data_df, ck_data_df,
                                                                                   trait_column_name_list,
                                                                                   selected_year_list,
                                                                                   selected_entrybookname)
            summary_data_df = pd.concat([summary_data_df, single_sample_summary_df])
        summary_data_df = self.__get_normalized_trait_data_df(summary_data_df, trait_column_name_list)
        return summary_data_df

    def __get_grouped_trait_column_list(self, selected_trait_column_list):
        num_trait_column_list, percent_trait_column_list, grade_trait_column_list = [], [], []
        selected_trait_column_list = [self.trait_column_name_to_chinese_name_dict[trait_column_name]
                                      for trait_column_name in selected_trait_column_list]
        for selected_trait_column_name in selected_trait_column_list:
            if "%" in selected_trait_column_name and "水分" not in selected_trait_column_name:
                percent_trait_column_list.append(self.chinese_name_to_trait_column_name_dict[selected_trait_column_name])
            elif "等级" in selected_trait_column_name:
                grade_trait_column_list.append(self.chinese_name_to_trait_column_name_dict[selected_trait_column_name])
            else:
                num_trait_column_list.append(self.chinese_name_to_trait_column_name_dict[selected_trait_column_name])
        return num_trait_column_list, percent_trait_column_list, grade_trait_column_list

    def plot(self):
        (selected_year_list, selected_entrybookname, selected_target_name_list, selected_ck_name,
         selected_trait_column_list, selected_caculate_method) = self.get_dropdown_menu_bar()
        # selected_ck_name = 'XY1219'
        # selected_trait_column_list = list(self.trait_column_name_to_chinese_name_dict.keys())
        # print(selected_trait_column_list)
        # selected_trait_column_list = ["YLD14", "BARPCT"]
        num_trait_column_list, percent_trait_column_list, grade_trait_column_list = (
            self.__get_grouped_trait_column_list(selected_trait_column_list))
        sample_data_df = self.phenoTable.get_sample_pheno_df(selected_year_list, selected_entrybookname,
                                                             selected_target_name_list)
        ck_data_df = self.phenoTable.get_ck_pheno_df(selected_year_list, selected_entrybookname, selected_ck_name)
        num_summary_data_df = self.num_trait_summary(sample_data_df, ck_data_df, num_trait_column_list,
                                                 selected_caculate_method)
        grade_summary_data_df = self.grade_trait_summary(sample_data_df, ck_data_df, grade_trait_column_list,
                                                 selected_caculate_method, selected_year_list, selected_entrybookname)
        percent_summary_data_df = self.percent_trait_summary(sample_data_df, ck_data_df, percent_trait_column_list,
                                                             selected_caculate_method, selected_year_list,
                                                             selected_entrybookname)
        summary_data_df = None
        if len(grade_summary_data_df.columns) > 2:  # 因为有两个固定的列一定会输出
            summary_data_df = pd.merge(left=num_summary_data_df,
                                       right=grade_summary_data_df,
                                       on=["品种综合评分", "产量排序", "品种名称", "对照名称", "年份", "生态亚区", "种植点次"],
                                       how='left')
        else:
            summary_data_df = num_summary_data_df
        if len(percent_summary_data_df.columns) > 2:
            summary_data_df = pd.merge(left=summary_data_df,
                                       right=percent_summary_data_df,
                                       on=["品种综合评分", "产量排序", "品种名称", "对照名称", "年份", "生态亚区", "种植点次"],
                                       how='left')
        summary_data_df = self.__get_yld_order_data_df(summary_data_df)
        summary_data_df = self.__get_sample_score_data_df(summary_data_df, selected_trait_column_list)
        DataFrameColor(dataframe=summary_data_df).plot()
        # st.dataframe(summary_data_df, hide_index=True)


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

