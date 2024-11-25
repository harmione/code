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
        # 连接并根据传来的查询语句获取对应的数据集
        conn = st.connection("postgres")
        self.data_df = conn.query(self.query_statement)
        return self.data_df

    def __get_AOAname_list(self):
        # 获取生态亚区数据
        AOAname_list = list(filter(None,pd.unique(self.data_df["AOA_S"]).tolist()))
        return  AOAname_list

    def get_ck_name_list(self, selected_AOAname):
        # 根据生态亚区（AOA） 查询样本名称
        ck_name_list = list(filter(None, pd.unique(self.data_df[(self.data_df["AOA_S"] == selected_AOAname)
                                                                ]["VarNam"]).tolist()))  # 过滤掉None
        return ck_name_list


class PhenoTable:
    def __init__(self, query_statement):
        self.query_statement = query_statement
        self.data_df = self.__get_data_df()  # 直接获取了所有的数据
        self.year_list = self.__get_year_list()

    def __get_year_list(self):
        # 获取所有的年份，并取唯一值，显示为列表
        year_list = pd.unique(self.data_df["Year"]).tolist()
        return year_list

    def __get_data_df(self):
        # 连接并根据传来的查询语句获取对应的数据集
        conn = st.connection("postgres")
        data_df = conn.query(self.query_statement)
        return data_df

    def get_sample_name_list(self, selected_AOAname):
        # 根据熟期 找到对应样本的数据集【21号确认是entryBookname为原打算选择的测试点】【样本点为我们所谓的目标点，CK是测试点】
        sample_name_list = list(filter(None, pd.unique(self.data_df[(self.data_df["AOA_S"] == selected_AOAname)
                                                                    ]["VarNam"]).tolist()))
        return sample_name_list

    def get_sample_pheno_df(self, selected_year_list, selected_AOAname, selected_target_name_list):
        # 过滤选择Pheno表中样本的数据                                                      目标样本名的列表
        sample_pheno_df = self.data_df[(self.data_df["Year"].isin(selected_year_list)) &
                                       (self.data_df["AOA_S"] == selected_AOAname) &
                                       (self.data_df["VarNam"].isin(selected_target_name_list))]
        return sample_pheno_df

    def get_percent_pressure_bookname_num(self, selected_year_list, selected_AOAname, trait_column_name):
        #百分比表的   获取压力测试点的数据 （认为：压力点数=发生点次 某性状发生则为1，不发生为0）       trait_Column_name 选择的特征对应的列（性状列）
        pressure_loc_name_num = 0
        origin_data_df = self.data_df[(self.data_df["Year"].isin(selected_year_list)) &
                               (self.data_df["AOA_S"] == selected_AOAname) ]
        Location_set = set(origin_data_df["Location_TD"])   # set 无序 不重复   存的是地点（省市）
        for loc_name in Location_set:
            data_df = origin_data_df[origin_data_df["Location_TD"] == loc_name]
            if (~(data_df[trait_column_name].notna())).all(): # 数据全为Nan 直接返回
                continue
            elif any(data_df[trait_column_name] > 0):
                ## 判断至少有一个点大于0%     #百分比制的 越小越好，最小为0%
                pressure_loc_name_num += 1
        return pressure_loc_name_num

    def get_grade_pressure_bookname_num(self, selected_year_list,selected_AOAname, trait_column_name):
        # 打分（等级）表的   获取压力测试点的数据 （认为：压力点数=发生点次）               trait_Column_name 选择的特征对应的列（性状列）
        pressure_loc_name_num = 0
        origin_data_df = self.data_df[(self.data_df["Year"].isin(selected_year_list)) &
                               (self.data_df["AOA_S"] == selected_AOAname)]
        Location_set = set(origin_data_df["Location_TD"])
        for loc_name in Location_set:
            data_df = origin_data_df[origin_data_df["Location_TD"] == loc_name]
            if (~(data_df[trait_column_name].notna())).all(): # 数据全为Nan 直接返回
                continue
            elif any(data_df[trait_column_name] != 9):
                ## 判断是否任何值不等于9           ## 打分越大越好  9为最大
                pressure_loc_name_num += 1
        return pressure_loc_name_num

    def get_ck_pheno_df(self, selected_year_list, selected_AOAname, selected_ck_name_list):
        # 过滤选择Pheno的对照表中样本的数据                                         对照样本名的列表
        ck_pheno_df = self.data_df[(self.data_df["Year"].isin(selected_year_list)) &
                                   (self.data_df["AOA_S"] == selected_AOAname) &
                                   (self.data_df["VarNam"].isin([selected_ck_name_list]))]
        return ck_pheno_df



class DataFrameColor:
    # 根据规则进行上色功能     主要针对均值和上色率
    def __init__(self, dataframe):
        #  此处的dataframe = summary_data_df
        self.dataframe = dataframe

    # 产量均值列上色
    def yld_color_cells(self,row):
        # 初始化一个与行中单元格数量相同的空列表
        colors = []
        for val in row:
            result = (float(val) - float(row.iloc[0])) / float(row.iloc[0])
            if 0.1 < result:
                colors.append("background-color:#228B22")  # 极好
            elif 0.05 < result <= 0.1:
                colors.append("background-color:#7FFF00")  # 较好
            elif -0.05 <= result <= 0.05:
                colors.append("background-color:yellow")  # 中等
            elif -0.1 <= result < -0.05:
                colors.append("background-color:#FFA500")  # 风险S
            elif result < -0.1:
                colors.append("background-color:red")  # 高风险HS
            else:
                colors.append("")
        return pd.Series(colors)

    # 株高均值上色
    def pht_color_cells(self,row):
        # 初始化一个与行中单元格数量相同的空列表
        colors = []
        for val in row:
            val = float(val)
            if 240 <= val <=260:
                colors.append("background-color:#228B22")  # 极好
            elif 260 < val <= 280:
                colors.append("background-color:#7FFF00")  # 较好
            elif 280 < val <= 300:
                colors.append("background-color:yellow")  # 中等
            elif 300 < val <= 320:
                colors.append("background-color:#FFA500")  # 风险S
            elif 320< val <= 350 :
                colors.append("background-color:red")  # 高风险HS
            else:
                colors.append("")
        return pd.Series(colors)

    # 穗位均值上色
    def eht_color_cells(self,row):
        colors = []
        for val in row:
            val = float(val)
            if 0 <= val <= 80:
                colors.append("background-color:#228B22")  # 极好
            elif 80 < val <= 100:
                colors.append("background-color:#7FFF00")  # 较好
            elif 100 < val <= 120:
                colors.append("background-color:yellow")  # 中等
            elif 120 < val <= 140:
                colors.append("background-color:#FFA500")  # 风险S
            elif 140 < val <= 200:
                colors.append("background-color:red")  # 高风险HS
            else:
                colors.append("")
        return pd.Series(colors)

    # 倒伏倒折率列 上色
    def tdppct_color_cells(self,row):
        colors=[]
        for val in row:
            val = float(val)
            if 0<= val <=5:
                colors.append("background-color:#228B22")  # 高抗
            elif 5 < val <= 10:
                colors.append("background-color:#7FFF00")  # 抗
            elif 10 < val <= 15:
                colors.append("background-color:yellow")  # 中抗
            elif 15 < val <= 30:
                colors.append("background-color:#FFA500")  # 感S
            elif 30 < val:
                colors.append("background-color:red")  # 高感HS
            else:
                colors.append("")
        return pd.Series(colors)

    # 青枯病比率  均值列 上色
    def stkrpct_color_cells(self,row):
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

    # 叶部病害 均值列 上色  包括： 大斑，灰斑， 锈病，白斑，弯包叶斑
    def Leaf_colors_cells(self,row):
        colors = []
        for val in row:
            val = float(val)
            if 7.5 < val <= 9.0:
                colors.append("background-color:#228B22")  # 高抗
            elif 5.5< val <= 7.5:
                colors.append("background-color:#7FFF00")  # 抗
            elif 3.5 < val <= 5.5:
                colors.append("background-color:yellow")  # 中抗
            elif 1.5< val <= 3.5:
                colors.append("background-color:#FFA500")  # 感S
            elif 1.0 <= val <=1.5:
                colors.append("background-color:red")  # 高感HS
            else:
                colors.append("")
        return pd.Series(colors)

    # 结实性  均值列 上色
    def kersr_colors_cells(self, row):
        colors = []
        for val in row:
            val = float(val)
            if 7.5 < val <= 9.0:
                colors.append("background-color:#228B22")  # 高抗
            elif 6.5 < val <= 7.5:
                colors.append("background-color:#7FFF00")  # 抗
            elif 5.0 < val <= 6.5:
                colors.append("background-color:yellow")  # 中抗
            elif 3.5 < val <= 5.0:
                colors.append("background-color:#FFA500")  # 感S
            elif 1.0 <= val <= 3.5:
                colors.append("background-color:red")  # 高感HS
            else:
                colors.append("")
        return pd.Series(colors)

    # 苞叶覆盖度
    def huskcov_colors_cells(self,row):
        colors = []
        for val in row:
            val = float(val)
            if 7.5 < val <= 9.0:
                colors.append("background-color:#228B22")  # 高抗
            elif 6.5 < val <= 7.5:
                colors.append("background-color:#7FFF00")  # 抗
            elif 5.0 < val <= 6.5:
                colors.append("background-color:yellow")  # 中抗
            elif 3.5 < val <= 5.0:
                colors.append("background-color:#FFA500")  # 感S
            elif 1.0 <= val <= 3.5:
                colors.append("background-color:red")  # 高感HS
            else:
                colors.append("")
        return pd.Series(colors)

    # 玉米螟 均值列 上色
    def indara_colors_cells(self,row):
        colors = []
        for val in row:
            val = float(val)
            if 7.5 < val <= 9.0:
                colors.append("background-color:#228B22")  # 高抗
            elif 6.5 < val <= 7.5:
                colors.append("background-color:#7FFF00")  # 抗
            elif 5.0 < val <= 6.5:
                colors.append("background-color:yellow")  # 中抗
            elif 3.5 < val <= 5.0:
                colors.append("background-color:#FFA500")  # 感S
            elif 1.0 <= val <= 3.5:
                colors.append("background-color:red")  # 高感HS
            else:
                colors.append("")
        return pd.Series(colors)


    # 秃尖 均值列 上色
    def tipfill_colors_cells(self,row):
        colors = []
        for val in row:
            val = float(val)
            if 8 < val <= 9.0:
                colors.append("background-color:#228B22")  # 高抗
            elif 7 < val <= 8:
                colors.append("background-color:#7FFF00")  # 抗
            elif 6.0 < val <= 7.0:
                colors.append("background-color:yellow")  # 中抗
            elif 5.0 < val <= 6.0:
                colors.append("background-color:#FFA500")  # 感S
            elif 1.0 <= val <= 5.0:
                colors.append("background-color:red")  # 高感HS
            else:
                colors.append("")
        return pd.Series(colors)

    # 东北霉变粒率 均值列上色
    def kertpct_colors_cells_DHB(self,row):
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

    def plot(self):
        # 可以选择在此处完成颜色添加
        dataframe = self.dataframe
        # st.dataframe(dataframe, hide_index=False)  # 隐藏索引列
        # 应用颜色填充
        dataframe.reset_index(drop=True, inplace=True)
        style_df = dataframe.style
        style_df = dataframe.style.apply(self.yld_color_cells,subset=['产量均值'])
        if '株高均值' in dataframe.columns:
            style_df = style_df.apply(self.pht_color_cells, subset=['株高均值'])
        if '穗位均值' in dataframe.columns:
            style_df = style_df.apply(self.eht_color_cells, subset=['穗位均值'])
        if '青枯病均值[%制]' in dataframe.columns:
            style_df = style_df.apply(self.stkrpct_color_cells, subset=['青枯病均值[%制]'])
        if '倒伏倒折均值[%制]' in dataframe.columns:
            style_df = style_df.apply(self.tdppct_color_cells,subset=['倒伏倒折均值[%制]'])
        if '大斑病均值' in dataframe.columns:       #大斑，灰斑， 锈病，白斑，弯包叶斑
            style_df = style_df.apply(self.Leaf_colors_cells, subset=['大斑病均值'])
        if '灰斑病均值' in dataframe.columns:       #大斑，灰斑， 锈病，白斑，弯包叶斑
            style_df = style_df.apply(self.Leaf_colors_cells, subset=['灰斑病均值'])
        if '普通锈病均值' in dataframe.columns:       #大斑，灰斑， 锈病，白斑，弯包叶斑
            style_df = style_df.apply(self.Leaf_colors_cells, subset=['普通锈病均值'])
        if '白斑病均值' in dataframe.columns:       #大斑，灰斑， 锈病，白斑，弯包叶斑
            style_df = style_df.apply(self.Leaf_colors_cells, subset=['白斑病均值'])
        if '弯孢叶斑病均值' in dataframe.columns:       #大斑，灰斑， 锈病，白斑，弯包叶斑
            style_df = style_df.apply(self.Leaf_colors_cells, subset=['弯孢叶斑病均值'])
        if '结实性均值' in dataframe.columns:
            style_df = style_df.apply(self.kersr_colors_cells, subset=['结实性均值'])
        if '苞叶覆盖度均值' in dataframe.columns:
            style_df = style_df.apply(self.huskcov_colors_cells, subset=['苞叶覆盖度均值'])
        if '玉米螟均值' in dataframe.columns:
            style_df = style_df.apply(self.indara_colors_cells, subset=['玉米螟均值'])
        if '秃尖均值' in dataframe.columns:
            style_df = style_df.apply(self.tipfill_colors_cells, subset=['秃尖均值'])
        if '霉变粒率均值[%制]' in dataframe.columns:
            sub1 = ['北方超早', '北方极早', '北方早熟', '东华北中早', '东华北中熟', '东华北中晚']
            sub2 = ['黄淮南','黄淮北']
            if dataframe['生态亚区'].isin(sub2).any():
                style_df = style_df.apply(self.kertpct_colors_cells_HHH, subset=['霉变粒率均值[%制]'])
            elif dataframe['生态亚区'].isin(sub1).any() :
                style_df = style_df.apply(self.kertpct_colors_cells_DHB, subset=['霉变粒率均值[%制]'])

        # 展示带颜色的DataFrame
        st.dataframe(style_df)
        #st.dataframe(style_df)



class Plot:
    def __init__(self, ckTable: CKTable, phenoTable: PhenoTable):
        # 构造函数 接受小ck和小pheno参数对象
        self.ckTable = ckTable
        self.phenoTable = phenoTable
        # self.num_trait_list = ['YLD14', 'MST', 'PHT', 'EHT']
        # self.grade_trait_list = ['STKLPCT', 'PMDPCT', 'BARPCT', 'EARTPCT', 'KERTPCT', 'NCLB', 'GLS', 'HUSKCOV', 'KERSR',
        #                          'TIPFILL']
        # 用于将形状名称转中文展示
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
        # 性状的权重系数字典  ## 目前暂不知是否需要更改
        self.trait_weight_coefficient_dict = {
            'YLD14_TD': 1,
            'KERTPCT_TD': 1,
            'MST': 1,
            'GLS': 1,
            'CLB': 1,
            'STKRPCT_TD': 1,
            'PHT': 1,
            'EHT': 1,
            'STKLPCT_TD': 1,
            'TDPPCT_TD': 1,
            'BARPCT_TD': 1,
            'EARTPCT_TD': 1,
            'HUSKCOV': 1,
            'KERSR': 1,
            'TIPFILL': 1,
            'RSTCOM': 1,
            'CULSPT': 1,
            'STAGRN': 1,
            'SHBLSC': 1,
            'CWLSPT': 1,
            'BSPPCT_TD': 1,
            'DEEARPER_TD': 1,
            'EARSIZE': 1,
            'INDARA':1
        }

    def get_dropdown_menu_bar(self):
        # 设置生成下拉菜单栏  multiselect 和 selectbox都是
        # multiselect 可以选一个或多个
        # selectbox   只能从多选框中选一个
        # 第一排的布局
        column_list = st.columns((2, 1, 3, 1))   #设置页面布局的宽度比例
        with column_list[0]:
            selected_year_list = st.multiselect(
                '年份',
                self.phenoTable.year_list,
                default=self.phenoTable.year_list[-1]     ## 后面看是否需要设置最新一年为默认年份，若需要，改为-1
            )
            # 异常处理
            if len(selected_year_list) == 0:  # 若未选择，默认选择第一个年份
                selected_year_list = [self.phenoTable.year_list[0]]
        with column_list[1]:
            selected_AOAname = st.selectbox(
                '生态亚区',
                self.ckTable.AOAname_list
            )
        with column_list[2]:
            selected_trait_column_list = st.multiselect(
                '性状',
                self.trait_column_name_to_chinese_name_dict.values(),
                default=list(self.trait_column_name_to_chinese_name_dict.values())[0:3]    #默认选择第一个
            )
            if len(selected_trait_column_list) == 0:
                # 未选择情况下 的异常判断
                selected_trait_column_list = [list(self.trait_column_name_to_chinese_name_dict.values())[0]]
        selected_trait_column_list = [self.chinese_name_to_trait_column_name_dict[selected_trait_column]
                                      for selected_trait_column in selected_trait_column_list]    # 将选择的中文名转换回对应的字段名称
        with column_list[3]:
            selected_caculate_method = st.selectbox(
                '点次统计方式',
                ["测试点取交集", "测试点取并集"]
            )

        # 第二排的布局设置
        column_list = st.columns((1, 5))
        with column_list[0]:
            selected_ck_name = st.selectbox(
                '对照品种',
                self.ckTable.get_ck_name_list(selected_AOAname)
            )
        with column_list[1]:
            selected_target_name_list = st.multiselect(
                '目标品种',
                self.phenoTable.get_sample_name_list(selected_AOAname),
                default= self.phenoTable.get_sample_name_list(selected_AOAname)[1]   # 默认
            )
            if len(selected_target_name_list) == 0:
                selected_target_name_list = [self.phenoTable.get_sample_name_list(selected_AOAname)[0]]

        return (selected_year_list,selected_AOAname, selected_target_name_list, selected_ck_name,
                selected_trait_column_list, selected_caculate_method)     # 返回6个框选择的值


    def __data_preprocessing(self, sample_data_df, ck_data_df, caculate_method):
        # 数据预处理：根据选择的数据处理方法，对数据中的测试点提取交集数据或者并集数据；
        sample_bookname_set, ck_bookname_set = set(sample_data_df["Location_TD"]), set(ck_data_df["Location_TD"])     # 再仔细检查一下
        bookname_set = None
        if "交集" in caculate_method:
            bookname_set = sample_bookname_set & ck_bookname_set
        if "并集" in caculate_method:
            bookname_set = ck_bookname_set | sample_bookname_set
        sample_data_df = sample_data_df[sample_data_df["Location_TD"].isin(bookname_set)]  # 拿到选择的测试点的样本数据
        ck_data_df = ck_data_df[ck_data_df["Location_TD"].isin(bookname_set)]              # 拿到选择的对照点的样本数据
        return sample_data_df, ck_data_df

    def format_float(self, x):
        if isinstance(x, float):
            return f'{x:.1f}'.rstrip('0').rstrip('.')
        return x

    def __single_sample_num_summary_caculate(self, origin_single_sample_data_df, origin_ck_data_df, trait_column_name_list):
        # 单一样本 数值型 统计信息计算  【包括产量性状类】
        single_sample_summary_df = pd.DataFrame({
            '品种综合评分': [np.nan],
            '产量排序': [np.nan]
        })
        temp_single_sample_summary_df = None
        for trait_column_name in trait_column_name_list:
            single_sample_plot_count = len(origin_single_sample_data_df)
            single_sample_data_df = origin_single_sample_data_df[~pd.isna(origin_single_sample_data_df[trait_column_name])]
            ck_data_df = origin_ck_data_df[~pd.isna(origin_ck_data_df[trait_column_name])]
            single_sample_trait_count = len(single_sample_data_df)
            single_sample_trait_mean = np.mean(single_sample_data_df[trait_column_name])   # 没问题
            ck_trait_mean = np.mean(ck_data_df[trait_column_name])
            single_sample_trait_max = np.max(single_sample_data_df[trait_column_name])
            single_sample_trait_min = np.min(single_sample_data_df[trait_column_name])
            trait_column_name = self.trait_column_name_to_chinese_name_dict[trait_column_name].split("(")[0]   # 切片只要性状名称 不需要所为哪一类别
            difference = (single_sample_trait_mean - ck_trait_mean)/ck_trait_mean
            single_sample_trait_summary_df = pd.DataFrame({
                '品种名称': origin_single_sample_data_df["VarNam"].unique() if len(origin_single_sample_data_df["VarNam"].unique()) != 0 else [np.nan],
                '对照名称': origin_ck_data_df["VarNam"].unique() if len(origin_ck_data_df["VarNam"].unique()) != 0 else [np.nan],
                '年份': ','.join((origin_single_sample_data_df["Year"].unique() if len(
                    origin_single_sample_data_df["Year"].unique()) != 0 else [np.nan]).astype('U')),
                '生态亚区': origin_single_sample_data_df['AOA_S'].unique() if len(origin_single_sample_data_df['AOA_S'].unique()) != 0 else [np.nan],
                '种植点次': single_sample_plot_count,
                f'{trait_column_name}统计点次': single_sample_trait_count,
                f'{trait_column_name}均值': single_sample_trait_mean,
                f'{trait_column_name}标准化': [np.nan],
                f'{trait_column_name}比对差异':[difference],
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
     #   single_sample_summary_df= single_sample_summary_df.applymap(self.format_float)
        return single_sample_summary_df

    def __single_sample_grade_summary_caculate(self, origin_single_sample_data_df, origin_ck_data_df, trait_column_name_list,
                                               selected_year_list, selected_AOAname):
        # 单一样本 打分等级的 统计信息计算
        single_sample_summary_df = pd.DataFrame({
            '品种综合评分': [np.nan],
            '产量排序': [np.nan]
        })
        temp_single_sample_summary_df = None
        for trait_column_name in trait_column_name_list:
            single_sample_plot_count = len(origin_single_sample_data_df)  # 统计样本种植的点的数量
            single_sample_data_df = origin_single_sample_data_df[~pd.isna(origin_single_sample_data_df[trait_column_name])]
            ck_data_df = origin_ck_data_df[~pd.isna(origin_ck_data_df[trait_column_name])]   # 过滤移除所有该列上有缺失值的行

            pressure_bookname_num = self.phenoTable.get_grade_pressure_bookname_num(selected_year_list,
                                                                                    selected_AOAname, trait_column_name)
            single_sample_trait_count = len(single_sample_data_df['Location_TD'].unique())  # 统计有该性状的点的数量
            occur_incidence_rate = single_sample_trait_count / pressure_bookname_num * 100 if pressure_bookname_num != 0 else np.nan
            single_sample_trait_mean = np.mean(single_sample_data_df[trait_column_name])
            ck_trait_mean = np.mean(ck_data_df[trait_column_name])
            single_sample_trait_max = np.max(single_sample_data_df[trait_column_name])
            single_sample_trait_min = np.min(single_sample_data_df[trait_column_name])
            trait_column_name = self.trait_column_name_to_chinese_name_dict[trait_column_name].split("(")[0]
            difference = single_sample_trait_mean - ck_trait_mean
            single_sample_trait_summary_df = pd.DataFrame({
                '品种名称': origin_single_sample_data_df["VarNam"].unique() if len(
                    origin_single_sample_data_df["VarNam"].unique()) != 0 else [np.nan],
                '对照名称': origin_ck_data_df["VarNam"].unique() if len(
                    origin_ck_data_df["VarNam"].unique()) != 0 else [np.nan],
                '年份': ','.join((origin_single_sample_data_df["Year"].unique()).astype('U')) if len(origin_single_sample_data_df["Year"].unique()) != 0 else [np.nan],
                '生态亚区': origin_single_sample_data_df['AOA_S'].unique() if len(
                    origin_single_sample_data_df['AOA_S'].unique()) != 0 else [np.nan],
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
      #  single_sample_summary_df = single_sample_summary_df.applymap(self.format_float)
        return single_sample_summary_df

    def __single_sample_percent_summary_caculate(self, origin_single_sample_data_df, origin_ck_data_df, trait_column_name_list,
                                               selected_year_list, selected_AOAname):
        single_sample_summary_df = pd.DataFrame({
            '品种综合评分': [np.nan],
            '产量排序': [np.nan]
        })
        temp_single_sample_summary_df = None
        for trait_column_name in trait_column_name_list:    # 遍历所有的性状列
            single_sample_plot_count = len(origin_single_sample_data_df)    # 统计样本种植的点的数量
            single_sample_data_df = origin_single_sample_data_df[~pd.isna(origin_single_sample_data_df[trait_column_name])]   # 进行过滤 样本集中移除包含缺失值的所有行【因为性状是列，样本及对照数据按行来】
            ck_data_df = origin_ck_data_df[~pd.isna(origin_ck_data_df[trait_column_name])]    # 移除 对照集中为缺失值的所有行
            # 获取压力点次（或发生点次）
            pressure_bookname_num = self.phenoTable.get_percent_pressure_bookname_num(selected_year_list, selected_AOAname,
                                                                                     trait_column_name)
            single_sample_trait_count = len(single_sample_data_df['Location_TD'].unique())  # 统计有该性状的点的数量
            # 发生率 = 某测试点A性状的发生点次/所有测试点的发生点次         注：分母只是和测试点有关 不管发生哪个性状 都算
            occur_incidence_rate = single_sample_trait_count / pressure_bookname_num * 100 if pressure_bookname_num != 0 else np.nan
            single_sample_trait_mean = np.mean(single_sample_data_df[trait_column_name])   # 单一样本的性状均值
            ck_trait_mean = np.mean(ck_data_df[trait_column_name])                         # 单一对照的性状均值
            single_sample_trait_max = np.max(single_sample_data_df[trait_column_name])
            single_sample_trait_min = np.min(single_sample_data_df[trait_column_name])
            trait_column_name = self.trait_column_name_to_chinese_name_dict[trait_column_name].split("比例")[0]
            difference = single_sample_trait_mean - ck_trait_mean
            single_sample_trait_summary_df = pd.DataFrame({
                '品种名称': origin_single_sample_data_df["VarNam"].unique() if len(
                    origin_single_sample_data_df["VarNam"].unique()) != 0 else [np.nan],
                '对照名称': origin_ck_data_df["VarNam"].unique() if len(origin_ck_data_df["VarNam"].unique()) != 0 else [np.nan],
                '年份': ','.join((origin_single_sample_data_df["Year"].unique()).astype('U')) if len(
                    origin_single_sample_data_df["Year"].unique()) != 0 else [np.nan],
                '生态亚区': origin_single_sample_data_df['AOA_S'].unique() if len(
                    origin_single_sample_data_df['AOA_S'].unique()) != 0 else [np.nan],
                '种植点次': single_sample_plot_count,
                f'有{trait_column_name}压力的点次': pressure_bookname_num,
                f'{trait_column_name}发生率(%)': [occur_incidence_rate],
                f'{trait_column_name}极大值[%制]': single_sample_trait_max *100,
                f'{trait_column_name}极小值[%制]': single_sample_trait_min *100,
                f'{trait_column_name}标准化': [np.nan],
                f'{trait_column_name}均值[%制]': [single_sample_trait_mean *100]
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
      #  single_sample_summary_df = single_sample_summary_df.applymap(self.format_float)
        return single_sample_summary_df

    def __get_normalized_trait_data_df(self, summary_data_df, trait_column_name_list):
        # 将数据统计信息进行标准化（不区分哪种表）
        for trait_column_name in trait_column_name_list:
            if '%' in self.trait_column_name_to_chinese_name_dict[trait_column_name] and '水分' not in self.trait_column_name_to_chinese_name_dict[trait_column_name]:
                flag = 1
            else:
                flag = 0
            trait_column_name = self.trait_column_name_to_chinese_name_dict[trait_column_name].split("(")[0].split('比例')[0]
            # z-score标准化 = （原值-均值）/标准差
            if flag == 1 :
                temp_num= summary_data_df[f"{trait_column_name}均值[%制]"].astype(float)
                summary_data_df[f"{trait_column_name}标准化"] = (temp_num - np.mean(temp_num)) / np.std(temp_num)
            else:
                temp_num = summary_data_df[f"{trait_column_name}均值"].astype(float)
                summary_data_df[f"{trait_column_name}标准化"] =(temp_num - np.mean(temp_num)) / np.std(temp_num)
        summary_data_df = summary_data_df.applymap(self.format_float)
        return summary_data_df

    # 对照排序                                                                         #__表示私有方法，定义在类内， 接受一个类型为DataFrame类型的参数summary_data_df
    def __get_yld_order_data_df(self, summary_data_df: pd.DataFrame) -> pd.DataFrame:  # 返回一个类型为pandas.DataFrame的对象
        # 对产量排序   并让对照数据置顶默认第一行
        trait_column_name = "产量均值"
        summary_data_df["产量排序"] = summary_data_df[trait_column_name].rank(ascending=False, method='min')
        ck_summary_data_df = summary_data_df.iloc[0:1, :]  # 对照数据默认是第一行        # iloc是Pandas下的根据索引切片操作，可以同时控制行和列
        sample_summary_data_df = summary_data_df.iloc[1:, :]
        sample_summary_data_df = sample_summary_data_df.sort_values(by=[trait_column_name],
                                                                    ascending=False)  # 对样本的数据进行降序排序
        summary_data_df = pd.concat([ck_summary_data_df, sample_summary_data_df], axis=0)  # 进行拼接
        summary_data_df = summary_data_df.applymap(self.format_float)
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
                if "比例" in chinese_trait_column_name:
                    temp = chinese_trait_column_name
                    chinese_trait_column_name = temp.replace("比例","")
                score = score + float(row[chinese_trait_column_name+"标准化"]) * self.trait_weight_coefficient_dict[trait_column_name]    # 标准化值* 特定权重系数
            return score

        summary_data_df["品种综合评分"] = summary_data_df.apply(lambda row: score_caculate(row), axis=1)   # apply方法作用于每一行，并将结果存储在 品种综合评分列里
        summary_data_df = summary_data_df.applymap(self.format_float)
        return summary_data_df
    
    def num_trait_summary(self, sample_data_df, ck_data_df, trait_column_name_list, selected_caculate_method):
        # 数值型的聚合结果
        summary_data_df = None
        sample_data_df, ck_data_df = self.__data_preprocessing(sample_data_df, ck_data_df, selected_caculate_method)    # 交并选择，获取对应的数据集
        sample_data_df = pd.concat([ck_data_df, sample_data_df], axis=0)      # 垂直方向拼接 对照和目标样本集
        for sample_name in sample_data_df["VarNam"].unique():   # 遍历测试点的唯一样本名
            single_sample_data_df = sample_data_df[sample_data_df["VarNam"] == sample_name]
            single_sample_summary_df = self.__single_sample_num_summary_caculate(single_sample_data_df, ck_data_df,
                                                                                 trait_column_name_list)    # 获取num型数据统计信息   某个样本所有测试点的数据
            summary_data_df = pd.concat([summary_data_df, single_sample_summary_df])
        summary_data_df = self.__get_normalized_trait_data_df(summary_data_df, trait_column_name_list)
        return summary_data_df


    def grade_trait_summary(self, sample_data_df, ck_data_df, trait_column_name_list, selected_caculate_method,
                            selected_year_list, selected_AOAname):
        # 打分的聚合结果
        summary_data_df = None
        sample_data_df, ck_data_df = self.__data_preprocessing(sample_data_df, ck_data_df, selected_caculate_method)
        sample_data_df = pd.concat([ck_data_df, sample_data_df], axis=0)
        for sample_name in sample_data_df["VarNam"].unique():
            single_sample_data_df = sample_data_df[sample_data_df["VarNam"] == sample_name]
            single_sample_summary_df = self.__single_sample_grade_summary_caculate(single_sample_data_df, ck_data_df,
                                                                                   trait_column_name_list,
                                                                                   selected_year_list,
                                                                                   selected_AOAname)  # 后两者与压力点次计算和发生率有关系
            summary_data_df = pd.concat([summary_data_df, single_sample_summary_df])
        summary_data_df = self.__get_normalized_trait_data_df(summary_data_df, trait_column_name_list)
        return summary_data_df
    
    
    def percent_trait_summary(self, sample_data_df, ck_data_df, trait_column_name_list, selected_caculate_method,
                              selected_year_list, selected_AOAname):
        # 百分制的表的聚合结果
        summary_data_df = None
        sample_data_df, ck_data_df = self.__data_preprocessing(sample_data_df, ck_data_df, selected_caculate_method)
        sample_data_df = pd.concat([ck_data_df, sample_data_df], axis=0)
        for sample_name in sample_data_df["VarNam"].unique():
            single_sample_data_df = sample_data_df[sample_data_df["VarNam"] == sample_name]
            single_sample_summary_df = self.__single_sample_percent_summary_caculate(single_sample_data_df, ck_data_df,
                                                                                     trait_column_name_list,
                                                                                     selected_year_list,
                                                                                     selected_AOAname)  # 后两者与压力点次计算和发生率有关系
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
        (selected_year_list, selected_AOAname, selected_target_name_list, selected_ck_name,
         selected_trait_column_list, selected_caculate_method) = self.get_dropdown_menu_bar()

        # 将选择的性状 按数值型、百分比型、等级型进行分组    【可能多选，或者单选 不同类型的】
        num_trait_column_list, percent_trait_column_list, grade_trait_column_list = (
            self.__get_grouped_trait_column_list(selected_trait_column_list))
        sample_data_df = self.phenoTable.get_sample_pheno_df(selected_year_list, selected_AOAname,
                                                             selected_target_name_list)
        ck_data_df = self.phenoTable.get_ck_pheno_df(selected_year_list, selected_AOAname, selected_ck_name)
        num_summary_data_df = self.num_trait_summary(sample_data_df, ck_data_df, num_trait_column_list,
                                                     selected_caculate_method)
        grade_summary_data_df = self.grade_trait_summary(sample_data_df, ck_data_df, grade_trait_column_list,
                                                         selected_caculate_method, selected_year_list, selected_AOAname)
        percent_summary_data_df = self.percent_trait_summary(sample_data_df, ck_data_df, percent_trait_column_list,
                                                             selected_caculate_method, selected_year_list,
                                                             selected_AOAname)
        summary_data_df = None
        # 合并两个DataFrame,进行左连接（在grade及percent中 均拼接在num型数据统计信息的右边）
        if len(grade_summary_data_df.columns) > 2:  # 因为有两个固定的列一定会输出【品种综合评分、产量排序】
            summary_data_df = pd.merge(left=num_summary_data_df,
                                       right=grade_summary_data_df,
                                       on=["品种综合评分", "产量排序", "品种名称", "对照名称", "年份", "生态亚区",
                                           "种植点次"],
                                       how='left')
        else:
            summary_data_df = num_summary_data_df
        if len(percent_summary_data_df.columns) > 2:  # 因为有两个固定的列一定会输出【品种综合评分、产量排序】  同上
            summary_data_df = pd.merge(left=summary_data_df,
                                       right=percent_summary_data_df,
                                       on=["品种综合评分", "产量排序", "品种名称", "对照名称", "年份", "生态亚区", "种植点次"],
                                       how='left')
        summary_data_df = self.__get_yld_order_data_df(summary_data_df)  # 按产量排序
        summary_data_df = self.__get_sample_score_data_df(summary_data_df, selected_trait_column_list)  # 获取综合评分
        DataFrameColor(dataframe=summary_data_df).plot()
        #st.dataframe(summary_data_df, hide_index=True)
        
if __name__ == '__main__':
#def main():
    st.set_page_config(layout='wide')  # 页面设置宽屏布局
    # 对照
    ck_query_statement = """
     select * from "DWS"."TDPheno2024" d
    """
    pheno_query_statement = """
       select * from "DWS"."TDPheno2024" d
       """
    ckTable = CKTable(ck_query_statement)
    phenoTable = PhenoTable(pheno_query_statement)
    plotfuc = Plot(ckTable, phenoTable)
    plotfuc.plot()
