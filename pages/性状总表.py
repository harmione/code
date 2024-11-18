from email.policy import default

import numpy as np
import streamlit as st
import pandas as pd
import sqlalchemy     # 映射数据库和python的综合ORM关系框架
from numpy.f2py.auxfuncs import istrue
# import pdb   # 设置断点

class CKTable:
    def __init__(self, query_statement):
        self.query_statement = query_statement
        self.data_df = self.__get_data_df()
        self.AOAname_list = self.__get_AOAname_list()
        #self.entrybookname_list = self.__get_entrybookname_list()

    def __get_data_df(self):
        # 连接并根据传来的查询语句获取对应的数据集
        conn = st.connection("postgres")
        self.data_df = conn.query(self.query_statement)
        return self.data_df

    def __get_AOAname_list(self):
        # 获取生态亚区数据   唯一
        # origin_entrybookname_list = pd.unique(self.data_df["AOA"]).tolist()     ##### 存在None，需过滤掉
        # entrybookname_list = list(filter(None,origin_entrybookname_list))
        # return entrybookname_list
        AOAname_list = list(filter(None,pd.unique(self.data_df["AOA"]).tolist()))
        return  AOAname_list

    def get_entrybookname_list(self, selected_AOAname):
        # 根据生态亚区（AOA） 从对照表中查询测试点名称
        entrybookname_list = list(filter(None,pd.unique(self.data_df[self.data_df["AOA"]==selected_AOAname]["EntryBookName"]).tolist()))   # 过滤掉None
        #ck_name_list = pd.unique(self.data_df[self.data_df["AOA"] == selected_entrybookname]["VarNam"]).tolist()
        return entrybookname_list

    def get_ck_name_list(self,selected_AOAname, selected_entrybookname):   # 没问题了
        # 根据生态亚区（AOA）和测试点 查询样本名称
        ck_name_list = list(filter(None,pd.unique(self.data_df[(self.data_df["AOA"]==selected_AOAname)
                                                               & (self.data_df["EntryBookName"] == selected_entrybookname)
                                   ]["Varnam"]).tolist()))   # 过滤掉None     要修改
        #ck_name_list = pd.unique(self.data_df[self.data_df["AOA"] == selected_AOAname]["VarNam"]).tolist()
        return ck_name_list


class DataFrameColor:
    # 根据规则进行上色功能     主要针对均值和上色率
    def __init__(self, dataframe):
        #  此处的dataframe = summary_data_df
        self.dataframe = dataframe

    def color_cells(self, row):
        # 按照评分规则进行完善
        colors =[]    # 便利获取所有的行
        for value in row:
            if isinstance(value,float) and value >=0.9:
                colors.append("background-color:green")
            elif isinstance(value,float) and value>=0.7:
                colors.append("background-color:yellow")
            elif isinstance(value,float):
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
        # st.write(style_df)


class PhenoTable:
    def __init__(self, query_statement):
        self.query_statement = query_statement
        self.data_df = self.__get_data_df()         # 直接获取了所有的数据
        self.year_list = self.__get_year_list()

    def __get_year_list(self):
        #获取所有的年份，并取唯一值，显示为列表
        year_list = pd.unique(self.data_df["Year"]).tolist()
        return year_list

    def __get_data_df(self):
        # 连接并根据传来的查询语句获取对应的数据集
        conn = st.connection("postgres")
        data_df = conn.query(self.query_statement)
        return data_df

    def get_sample_name_list(self,selected_AOAname, selected_entrybookname):
        # 根据生态亚区和试验点 找到对应样本的数据集【21号确认是entryBookname为原打算选择的测试点】【样本点为我们所谓的目标点，CK是测试点】
        sample_name_list = list(filter(None, pd.unique(self.data_df[(self.data_df["AOA"] == selected_AOAname)
                                                 & (self.data_df["EntryBookName"] == selected_entrybookname)
                                                 ]["Varnam"]).tolist()))
        # sample_name_list = pd.unique(self.data_df[self.data_df["AOA"] ==
        #                                           selected_entrybookname]["Varnam"]).tolist()
        return sample_name_list

    def get_sample_pheno_df(self, selected_year_list, selected_AOAname,selected_entrybookname, selected_target_name_list):
        # 过滤选择Pheno表中样本的数据                                                      目标样本名的列表
        sample_pheno_df = self.data_df[(self.data_df["Year"].isin(selected_year_list)) &
                                       (self.data_df["AOA"] == selected_AOAname) &
                                       (self.data_df["EntryBookName"] == selected_entrybookname) &
                                       (self.data_df["Varnam"].isin(selected_target_name_list))]
        return sample_pheno_df

    def get_percent_pressure_bookname_num(self, selected_year_list, selected_AOAname,selected_entrybookname, trait_column_name):
        #百分比表的   获取压力测试点的数据 （认为：压力点数=发生点次 某性状发生则为1，不发生为0）       trait_Column_name 选择的特征对应的列（性状列）
        pressure_bookname_num = 0
        data_df = self.data_df[(self.data_df["Year"].isin(selected_year_list)) &
                               (self.data_df["AOA"] == selected_AOAname) &
                               (self.data_df["EntryBookName"] == selected_entrybookname)]
        bookname_set = set(data_df["BookName"])   # set 无序 不重复
        for bookname in bookname_set:
            data_df = data_df[data_df["BookName"] == bookname]
            if any(data_df[trait_column_name] > 0):
                ## 判断至少有一个点大于0     #百分比制的 越小越好，最小为0%
                pressure_bookname_num += 1
        return pressure_bookname_num

    def get_grade_pressure_bookname_num(self, selected_year_list,selected_AOAname, selected_entrybookname, trait_column_name):
        # 打分（等级）表的   获取压力测试点的数据 （认为：压力点数=发生点次）               trait_Column_name 选择的特征对应的列（性状列）
        pressure_bookname_num = 0
        data_df = self.data_df[(self.data_df["Year"].isin(selected_year_list)) &
                               (self.data_df["AOA"] == selected_AOAname) &
                               (self.data_df["EntryBookName"] == selected_entrybookname)]
        bookname_set = set(data_df["BookName"])
        for bookname in bookname_set:
            data_df = data_df[data_df["BookName"] == bookname]
            if any(data_df[trait_column_name] != 9):
                ## 判断是否任何值不等于9           ## 暂时为打分越大越好  9为最大
                pressure_bookname_num += 1
        return pressure_bookname_num

    def get_ck_pheno_df(self, selected_year_list, selected_AOAname, selected_entrybookname, selected_ck_name_list):
        # 过滤选择Pheno的对照表中样本的数据                                         对照样本名的列表
        ck_pheno_df = self.data_df[(self.data_df["Year"].isin(selected_year_list)) &
                                   (self.data_df["AOA"] == selected_AOAname) &
                                   (self.data_df["EntryBookName"] == selected_entrybookname) &
                                   (self.data_df["Varnam"].isin([selected_ck_name_list]))]
        return ck_pheno_df


class Plot:
    def __init__(self, ckTable: CKTable, phenoTable: PhenoTable):
        # 构造函数 接受小ck和小pheno参数对象
        self.ckTable = ckTable
        self.phenoTable = phenoTable
        # self.num_trait_list = ['YLD14', 'MST', 'PHT', 'EHT']
        # self.grade_trait_list = ['STKLPCT', 'PMDPCT', 'BARPCT', 'EARTPCT', 'KERTPCT', 'NCLB', 'GLS', 'HUSKCOV', 'KERSR',
        #                          'TIPFILL']
        # 用于将形状名称转中文展示
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
                                                       'TIPFILL': '秃尖(等级)',
                                                       'RSTCOM': '普通锈病(等级)',
                                                       'CULSPT': '弯孢叶斑病(等级)',
                                                       'STAGRN': '持绿性(等级)',
                                                       'SHBLSC': '纹枯病(等级)',
                                                       'CWLSPT': '白斑病(等级)',
                                                       'BSPPCT': '褐斑病比例(%)',
                                                       # 'aaa': '畸形穗比例(%)',
                                                       # 'aaab': '果穗大小(等级)'
                                                       }
        # 转为字典格式存储    汉字作为key，英文缩写作为value
        self.chinese_name_to_trait_column_name_dict = {v: k for (k, v) in
                                                       self.trait_column_name_to_chinese_name_dict.items()}
        # 性状的权重系数字典  ## 目前暂不知是否需要更改
        self.trait_weight_coefficient_dict = {
            'YLD14': 1,
            'MST': -1,  # 水分赋值注意符号
            'PHT': 1,
            'EHT': 1,
            'STKLPCT': 1,
            'BARPCT': 1,
            'EARTPCT': 1,
            'KERTPCT': 1,
            'NCLB': 1,
            'GLS': 1,
            'HUSKCOV': 1,
            'KERSR': 1,
            'TIPFILL': 1,
            'RSTCOM': 1,
            'CULSPT': 1,
            'STAGRN': 1,
            'SHBLSC': 1,
            'CWLSPT': 1,
            'BSPPCT': 1,
            # 'aaa': 1,
            # 'aaab': 1
        }

    def get_dropdown_menu_bar(self):
        # 设置生成下拉菜单栏  multiselect和selectbox都是
        # multiselect 可以选一个或多个
        # selectbox   只能从多选框中选一个
        # 第一排的布局
        column_list = st.columns((2, 1, 2, 1))   #设置页面布局的宽度比例
        with column_list[0]:
            selected_year_list = st.multiselect(
                '年份',
                self.phenoTable.year_list,
                default=self.phenoTable.year_list[0]     ## 后面看是否需要设置最新一年为默认年份，若需要，改为-1
            )
            # 异常处理
            if len(selected_year_list) == 0:  # 若未选择，默认选择第一个年份
                selected_year_list = [self.phenoTable.year_list[0]]
        # with column_list[1]:
        #     selected_entrybookname = st.selectbox(
        #         '生态亚区',
        #         self.ckTable.entrybookname_list
        #     )
        with column_list[1]:
            selected_AOAname = st.selectbox(
                '生态亚区',
                self.ckTable.AOAname_list
            )
        with column_list[2]:
            selected_entrybookname = st.selectbox(
                '测试点',
                self.ckTable.get_entrybookname_list(selected_AOAname)
            )
        with column_list[3]:
            selected_caculate_method = st.selectbox(
                '点次统计方式',
                ["测试点取交集", "测试点取并集"]
            )
         #   新增第二排
        column_list = st.columns((4,1))
        with column_list[0]:
            selected_trait_column_list = st.multiselect(
                '性状',
                self.trait_column_name_to_chinese_name_dict.values(),
                default=list(self.trait_column_name_to_chinese_name_dict.values())[0]    #默认选择第一个
            )
            if len(selected_trait_column_list) == 0:
                # 未选择情况下 的异常判断
                selected_trait_column_list = [list(self.trait_column_name_to_chinese_name_dict.values())[0]]
        selected_trait_column_list = [self.chinese_name_to_trait_column_name_dict[selected_trait_column]
                                      for selected_trait_column in selected_trait_column_list]    # 将选择的中文名转换回对应的字段名称
        # 第二排的布局设置
        column_list = st.columns((1, 5))
        with column_list[0]:
            selected_ck_name = st.selectbox(
                '对照品种',
                self.ckTable.get_ck_name_list(selected_AOAname,selected_entrybookname),
                # default = self.ckTable.get_ck_name_list(selected_entrybookname)[0]           #################################################### 新增的对照品种为空情况
            )
        with column_list[1]:
            selected_target_name_list = st.multiselect(
                '目标品种',
                self.phenoTable.get_sample_name_list(selected_AOAname,selected_entrybookname),
                default=self.phenoTable.get_sample_name_list(selected_AOAname,selected_entrybookname)[1]   # 默认
            )
            if len(selected_target_name_list) == 0:
                selected_target_name_list = [self.phenoTable.get_sample_name_list(selected_AOAname,selected_entrybookname)[0]]

        return (selected_year_list,selected_AOAname, selected_entrybookname, selected_target_name_list, selected_ck_name,
                selected_trait_column_list, selected_caculate_method)     # 返回7个框选择的值

    def __data_preprocessing(self, sample_data_df, ck_data_df, caculate_method):
        # 数据预处理：根据选择的数据处理方法，对数据中的测试点提取交集数据或者并集数据；
        sample_bookname_set, ck_bookname_set = set(sample_data_df["BookName"]), set(ck_data_df["BookName"])
        bookname_set = None
        if "交集" in caculate_method:
            bookname_set = sample_bookname_set & ck_bookname_set
        if "并集" in caculate_method:
            bookname_set = ck_bookname_set | sample_bookname_set
        sample_data_df = sample_data_df[sample_data_df["BookName"].isin(bookname_set)]  # 拿到选择的测试点的样本数据
        ck_data_df = ck_data_df[ck_data_df["BookName"].isin(bookname_set)]              # 拿到选择的对照点的样本数据
        return sample_data_df, ck_data_df

    def __single_sample_num_summary_caculate(self, single_sample_data_df, ck_data_df, trait_column_name_list):
        # 单一样本 数值型 统计信息计算  【包括产量性状类】
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
            trait_column_name = self.trait_column_name_to_chinese_name_dict[trait_column_name].split("(")[0]   # 切片只要性状名称 不需要所为哪一类别
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
                f'{trait_column_name}比对差异':[difference],        # 待增加判断，判断对照品种选的是否是NAN
                f'{trait_column_name}极大值': single_sample_trait_max,
                f'{trait_column_name}极小值': single_sample_trait_min
            })
            single_sample_trait_summary_df[["品种名称", "对照名称", "生态亚区"]] = (
                single_sample_trait_summary_df[["品种名称", "对照名称", "生态亚区"]].astype(object))    # 转为对象类型
            if temp_single_sample_summary_df is None:
                # 开始拼接，第一次直接赋值
                temp_single_sample_summary_df = single_sample_trait_summary_df
            else:
                # 从第二次后开始进行合并拼接
                temp_single_sample_summary_df = pd.merge(left=temp_single_sample_summary_df,
                                                         right=single_sample_trait_summary_df,
                                                         on=["品种名称", "对照名称", "年份", "生态亚区", "种植点次"],
                                                         how='left')
        # 将（“品种综合评分”，“产量排序”）与其他的形状特征进行水平方向（按列）的合并拼接
        single_sample_summary_df = pd.concat([single_sample_summary_df, temp_single_sample_summary_df], axis=1)
        return single_sample_summary_df

    def __single_sample_grade_summary_caculate(self, single_sample_data_df, ck_data_df, trait_column_name_list,
                                               selected_year_list, selected_AOAname, selected_entrybookname):
        # 单一样本 打分等级的 统计信息计算     ## 可能需要修改相关的计算和显示
        single_sample_summary_df = pd.DataFrame({
            '品种综合评分': [np.nan],
            '产量排序': [np.nan]
        })
        temp_single_sample_summary_df = None
        for trait_column_name in trait_column_name_list:
            single_sample_plot_count = len(single_sample_data_df)
            single_sample_data_df = single_sample_data_df[~pd.isna(single_sample_data_df[trait_column_name])]
            ck_data_df = ck_data_df[~pd.isna(ck_data_df[trait_column_name])]   # 过滤移除所有该列上有缺失值的行
            pressure_bookname_num = self.phenoTable.get_grade_pressure_bookname_num(selected_year_list,
                                                                                    selected_AOAname,
                                                                                    selected_entrybookname
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
                                               selected_year_list, selected_AOAname, selected_entrybookname):
        single_sample_summary_df = pd.DataFrame({
            '品种综合评分': [np.nan],
            '产量排序': [np.nan]
        })
        temp_single_sample_summary_df = None
        for trait_column_name in trait_column_name_list:    # 遍历所有的性状列
            single_sample_plot_count = len(single_sample_data_df)    # 按行统计样本的数量
            single_sample_data_df = single_sample_data_df[~pd.isna(single_sample_data_df[trait_column_name])]   # 进行过滤 样本集中移除包含缺失值的所有行【因为性状是列，样本及对照数据按行来】
            ck_data_df = ck_data_df[~pd.isna(ck_data_df[trait_column_name])]    # 移除 对照集中为缺失值的所有行
            # 获取压力点次（或发生点次）
            pressure_bookname_num = self.phenoTable.get_percent_pressure_bookname_num(selected_year_list, selected_AOAname,
                                                                                      selected_entrybookname, trait_column_name)
            single_sample_trait_count = len(single_sample_data_df)
            # 发生率 = 某测试点A性状的发生点次/所有测试点的发生点次         注：分母只是和测试点有关 不管发生哪个性状 都算
            occur_incidence_rate = single_sample_trait_count / pressure_bookname_num * 100 if pressure_bookname_num != 0 else np.nan
            single_sample_trait_mean = np.mean(single_sample_data_df[trait_column_name])   # 单一样本的性状均值
            ck_trait_mean = np.mean(ck_data_df[trait_column_name])                         # 单一对照的性状均值
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
        # 将数据统计信息进行标准化（不区分哪种表）
        for trait_column_name in trait_column_name_list:
            trait_column_name = self.trait_column_name_to_chinese_name_dict[trait_column_name].split("(")[0].split('比例')[0]
            # z-score标准化 = （原值-均值）/标准差
            summary_data_df[f"{trait_column_name}标准化"] = ((summary_data_df[f"{trait_column_name}均值"] -
                                                              np.mean(summary_data_df[f"{trait_column_name}均值"])) /
                                                             np.std(summary_data_df[f"{trait_column_name}均值"]))
        return summary_data_df

    # 对照排序                                                                         #__表示私有方法，定义在类内， 接受一个类型为DataFrame类型的参数summary_data_df
    def __get_yld_order_data_df(self, summary_data_df: pd.DataFrame) -> pd.DataFrame:   # 返回一个类型为pandas.DataFrame的对象
        # 对产量排序   并让对照数据置顶默认第一行
        trait_column_name = "产量均值"
        summary_data_df["产量排序"] = summary_data_df[trait_column_name].rank(ascending=False, method='min')
        ck_summary_data_df = summary_data_df.iloc[0:1, :]    # 对照数据默认是第一行        # iloc是Pandas下的根据索引切片操作，可以同时控制行和列
        sample_summary_data_df = summary_data_df.iloc[1:, :]
        sample_summary_data_df = sample_summary_data_df.sort_values(by=[trait_column_name], ascending=False)     # 对样本的数据进行降序排序
        summary_data_df = pd.concat([ck_summary_data_df, sample_summary_data_df], axis=0)     # 进行拼接
        return summary_data_df

    def __get_sample_score_data_df(self, summary_data_df: pd.DataFrame, trait_column_name_list) -> pd.DataFrame:
        # 综合评分获取相关数据
        not_null_trait_column_name_list = []
        for trait_column_name in trait_column_name_list:
            chinese_trait_column_name = self.trait_column_name_to_chinese_name_dict[trait_column_name].split("(")[0].split("比例")[0]    # split将字符串分割成列表
            if summary_data_df[f"{chinese_trait_column_name}标准化"].isnull().sum() == 0:  # 若没有缺失值，记录没缺失值的列名
                not_null_trait_column_name_list.append(trait_column_name)

        def score_caculate(row: pd.DataFrame):
            # 计算评价总分
            score = 0
            for trait_column_name in not_null_trait_column_name_list:
                chinese_trait_column_name = self.trait_column_name_to_chinese_name_dict[trait_column_name].split("(")[0]
                score = score + row[chinese_trait_column_name + "标准化"] * self.trait_weight_coefficient_dict[trait_column_name]    # 标准化值* 特定权重系数
            return score

        summary_data_df["品种综合评分"] = summary_data_df.apply(lambda row: score_caculate(row), axis=1)   # apply方法作用于每一行，并将结果存储在 品种综合评分列里
        return summary_data_df

    def num_trait_summary(self, sample_data_df, ck_data_df, trait_column_name_list, selected_caculate_method):
        # 数值型的聚合结果
        summary_data_df = None
        sample_data_df, ck_data_df = self.__data_preprocessing(sample_data_df, ck_data_df, selected_caculate_method)    # 交并选择，获取对应的数据集
        sample_data_df = pd.concat([ck_data_df, sample_data_df], axis=0)      # 垂直方向拼接 对照和目标样本集
        for sample_name in sample_data_df["Varnam"].unique():   # 遍历测试点的唯一样本名
            single_sample_data_df = sample_data_df[sample_data_df["Varnam"] == sample_name]
            single_sample_summary_df = self.__single_sample_num_summary_caculate(single_sample_data_df, ck_data_df,
                                                                                 trait_column_name_list)    # 获取num型数据统计信息
            summary_data_df = pd.concat([summary_data_df, single_sample_summary_df])
        summary_data_df = self.__get_normalized_trait_data_df(summary_data_df, trait_column_name_list)
        return summary_data_df

    def grade_trait_summary(self, sample_data_df, ck_data_df, trait_column_name_list, selected_caculate_method,
                            selected_year_list, selected_AOAname, selected_entrybookname):
        # 打分的聚合结果
        summary_data_df = None
        sample_data_df, ck_data_df = self.__data_preprocessing(sample_data_df, ck_data_df, selected_caculate_method)
        sample_data_df = pd.concat([ck_data_df, sample_data_df], axis=0)
        for sample_name in sample_data_df["Varnam"].unique():
            single_sample_data_df = sample_data_df[sample_data_df["Varnam"] == sample_name]
            single_sample_summary_df = self.__single_sample_grade_summary_caculate(single_sample_data_df, ck_data_df,
                                                                                   trait_column_name_list,
                                                                                   selected_year_list,
                                                                                   selected_AOAname,
                                                                                   selected_entrybookname)   # 后两者与压力点次计算和发生率有关系
            summary_data_df = pd.concat([summary_data_df, single_sample_summary_df])
        summary_data_df = self.__get_normalized_trait_data_df(summary_data_df, trait_column_name_list)
        return summary_data_df

    def percent_trait_summary(self, sample_data_df, ck_data_df, trait_column_name_list, selected_caculate_method,
                            selected_year_list, selected_AOAname, selected_entrybookname):
        # 百分制的表的聚合结果
        summary_data_df = None
        sample_data_df, ck_data_df = self.__data_preprocessing(sample_data_df, ck_data_df, selected_caculate_method)
        sample_data_df = pd.concat([ck_data_df, sample_data_df], axis=0)
        for sample_name in sample_data_df["Varnam"].unique():
            single_sample_data_df = sample_data_df[sample_data_df["Varnam"] == sample_name]
            single_sample_summary_df = self.__single_sample_percent_summary_caculate(single_sample_data_df, ck_data_df,
                                                                                   trait_column_name_list,
                                                                                   selected_year_list,
                                                                                   selected_AOAname,
                                                                                   selected_entrybookname)  # 后两者与压力点次计算和发生率有关系
            summary_data_df = pd.concat([summary_data_df, single_sample_summary_df])
        summary_data_df = self.__get_normalized_trait_data_df(summary_data_df, trait_column_name_list)
        return summary_data_df

    def __get_grouped_trait_column_list(self, selected_trait_column_list):
        # 将 性状列进行分组
        num_trait_column_list, percent_trait_column_list, grade_trait_column_list = [], [], []
        # 获取选择的性状列的名字
        selected_trait_column_list = [self.trait_column_name_to_chinese_name_dict[trait_column_name]
                                      for trait_column_name in selected_trait_column_list]
        for selected_trait_column_name in selected_trait_column_list:
            if "%" in selected_trait_column_name and "水分" not in selected_trait_column_name:    # 筛选出只包含% 不包含水分的列
                percent_trait_column_list.append(self.chinese_name_to_trait_column_name_dict[selected_trait_column_name])
            elif "等级" in selected_trait_column_name:
                grade_trait_column_list.append(self.chinese_name_to_trait_column_name_dict[selected_trait_column_name])
            else:
                num_trait_column_list.append(self.chinese_name_to_trait_column_name_dict[selected_trait_column_name])
        return num_trait_column_list, percent_trait_column_list, grade_trait_column_list

    def plot(self):
        # 先获取在页面上选择的6个框的数据的返回值
        (selected_year_list, selected_AOAname, selected_entrybookname, selected_target_name_list, selected_ck_name,
         selected_trait_column_list, selected_caculate_method) = self.get_dropdown_menu_bar()
        # selected_ck_name = 'XY1219'
        # selected_trait_column_list = list(self.trait_column_name_to_chinese_name_dict.keys())
        # print(selected_trait_column_list)
        # selected_trait_column_list = ["YLD14", "BARPCT"]

        # 将选择的性状 按数值型、百分比型、等级型进行分组    【可能多选，或者单选 不同类型的】
        num_trait_column_list, percent_trait_column_list, grade_trait_column_list = (
            self.__get_grouped_trait_column_list(selected_trait_column_list))
        sample_data_df = self.phenoTable.get_sample_pheno_df(selected_year_list,selected_AOAname, selected_entrybookname,
                                                             selected_target_name_list)
        ck_data_df = self.phenoTable.get_ck_pheno_df(selected_year_list, selected_AOAname,selected_entrybookname, selected_ck_name)
        num_summary_data_df = self.num_trait_summary(sample_data_df, ck_data_df, num_trait_column_list,
                                                 selected_caculate_method)
        grade_summary_data_df = self.grade_trait_summary(sample_data_df, ck_data_df, grade_trait_column_list,
                                                 selected_caculate_method, selected_year_list,
                                                 selected_AOAname, selected_entrybookname)
        percent_summary_data_df = self.percent_trait_summary(sample_data_df, ck_data_df, percent_trait_column_list,
                                                             selected_caculate_method, selected_year_list,
                                                             selected_AOAname, selected_entrybookname)
        summary_data_df = None
        # 合并两个DataFrame,进行左连接（在grade及percent中 均拼接在num型数据统计信息的右边）
        if len(grade_summary_data_df.columns) > 2:  # 因为有两个固定的列一定会输出【品种综合评分、产量排序】
            summary_data_df = pd.merge(left=num_summary_data_df,
                                       right=grade_summary_data_df,
                                       on=["品种综合评分", "产量排序", "品种名称", "对照名称", "年份", "生态亚区", "种植点次"],
                                       how='left')
        else:
            summary_data_df = num_summary_data_df
        if len(percent_summary_data_df.columns) > 2:   # 因为有两个固定的列一定会输出【品种综合评分、产量排序】  同上
            summary_data_df = pd.merge(left=summary_data_df,
                                       right=percent_summary_data_df,
                                       on=["品种综合评分", "产量排序", "品种名称", "对照名称", "年份", "生态亚区", "种植点次"],
                                       how='left')
        summary_data_df = self.__get_yld_order_data_df(summary_data_df)     # 按产量排序
        summary_data_df = self.__get_sample_score_data_df(summary_data_df, selected_trait_column_list)    # 获取综合评分
        DataFrameColor(dataframe=summary_data_df).plot()
        # st.dataframe(summary_data_df, hide_index=True)


if __name__ == '__main__':
    st.set_page_config(layout='wide')  # 页面设置宽屏布局
    # 对照的也从pheno中出
    ck_query_statement = """
     select * from "DWS"."Pheno" p where p."EntryBookPrj" = 'TD'
    """

    pheno_query_statement = """
    select * from "DWS"."Pheno" p where p."EntryBookPrj" = 'TD'
    """
    # pdb.set_trace()    # 设置断点
    ckTable = CKTable(ck_query_statement)
    phenoTable = PhenoTable(pheno_query_statement)
    plot = Plot(ckTable, phenoTable)
    plot.plot()


# 使用streamlit run xxx.py在命令行运行
