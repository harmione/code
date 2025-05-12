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
from networkx.drawing import rescale_layout_dict
from numpy.ma.core import choose


class Plotter:
    def __init__(self,query_statement):
        if 'hidden_rows' not in st.session_state:
            st.session_state.hidden_rows = set()
        self.query_statement = query_statement
        self.data_df = self.__get_data_df()
        self.AOAname_list = self.__get_AOAname_list()
        self.trait_column_name_to_chinese_name_dict = {'STKRPCT_TD': '青枯病比例(%)',
                                                        'YLD14_TD': '产量(kg/亩)',
                                                       'KERTPCT_TD': '霉变粒率比例(%)',
                                                       'MST': '水分(%)',
                                                       'GLS': '灰斑病(等级)',
                                                       'CLB': '大斑病(等级)',
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
        sample_name_list = list(filter(None, pd.unique(self.data_df[(self.data_df["AOA_S"].isin(selected_AOAname))
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
        st.markdown(
            """
                <style>
                .custom-sub-title {
                    font-size: 21px;
                    font-weight: bold;
                    margin-left:230px;    #左侧边距
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
                default=list(self.trait_column_name_to_chinese_name_dict.values())[0:1]  # 默认选择第一个
            )
            if len(selected_trait_column_list) == 0:
                # 未选择情况下 的异常判断
                selected_trait_column_list = [list(self.trait_column_name_to_chinese_name_dict.values())[0]]
        selected_trait_list = [self.chinese_name_to_trait_column_name_dict[selected_trait_column]
                                      for selected_trait_column in selected_trait_column_list]  # 将选择的中文名转换回对应的字段名称

        column_list = st.columns((1,2))
        with column_list[0]:
            selected_sample_name = st.selectbox(
                '选择目标品种',
                self.get_sample_name_list(self.AOAname_list)
            )
        with column_list[1]:
            selected_CK_names = st.multiselect(
                '选择对照品种',
                self.get_sample_name_list(self.AOAname_list),
                default = self.get_sample_name_list(self.AOAname_list)[1]
            )
        return selected_AOA_list, selected_trait_list,selected_sample_name, selected_CK_names

    def highlight_first_column(self,row):
        # 创建与行长度相等的列表，仅第一列应用颜色  [包括平均数 及 品种名称]
        return ['background-color: {}'.format("#F0FFF0") if i == 0 else 'background-color: {}'.format("#FFFAF0") for i in range(len(row))]

    def format_float(self, x):   # float类型数据格式化，保留一位小数
        if isinstance(x, float):
            return f'{x:.1f}'.rstrip('0').rstrip('.')
        return x

    def stkrpct_color_cells(self,row):  # 青枯病
        style_list = ['' for _ in row]
        for i in range(1,len(row)):
            if row[i] == '':
                continue
            else:
                val = float(row[i])
                if 0 <= val <= 5:
                    style_list[i]= "background-color:#228B22"  # 高抗
                elif 5 < val <= 10:
                    style_list[i]= "background-color:#7FFF00"  # 抗
                elif 10 < val <= 20:
                    style_list[i]= "background-color:yellow"  # 中抗
                elif 20 < val <= 30:
                    style_list[i]= "background-color:#FFA500"  # 感S
                elif 30 < val:
                    style_list[i]="background-color:red"  # 高感HS
        return style_list

    def pht_color_cells(self,row):    # 株高
        style_list = ['' for _ in row]
        for i in range(1, len(row)):
            if row[i] == '':
                continue
            else:
                val = float(row[i])
                if 240 <= val <= 260:
                    style_list[i] = "background-color:#228B22"  # 极好
                elif 260 < val <= 280:
                    style_list[i] = "background-color:#7FFF00"  # 较好
                elif 280 < val <= 300:
                    style_list[i] = "background-color:yellow"  # 中等
                elif 300 < val <= 320:
                    style_list[i] = "background-color:#FFA500"  # 风险S
                elif 320 < val <= 350:
                    style_list[i] = "background-color:red"  # 高风险HS
        return style_list

    def eht_color_cells(self,row):   # 穗位
        style_list = ['' for _ in row]
        for i in range(1, len(row)):
            if row[i] == '':
                continue
            else:
                val = float(row[i])
                if 0 <= val <= 80:
                    style_list[i] = "background-color:#228B22"  # 极好
                elif 80 < val <= 100:
                    style_list[i] = "background-color:#7FFF00"  # 较好
                elif 100 < val <= 120:
                    style_list[i] = "background-color:yellow"  # 中等
                elif 120 < val <= 140:
                    style_list[i] = "background-color:#FFA500"  # 风险S
                elif 140 < val <= 200:
                    style_list[i] = "background-color:red"  # 高风险HS
        return style_list

    def leaf_colors_cells(self,row):    # 叶部病害
        style_list = ['' for _ in row]
        for i in range(1, len(row)):
            if row[i] == '':
                continue
            else:
                val = float(row[i])
                if 7.5 < val <= 9.0:
                    style_list[i] = "background-color:#228B22"  # 高抗
                elif 5.5 < val <= 7.5:
                    style_list[i] = "background-color:#7FFF00"  # 抗
                elif 3.5 < val <= 5.5:
                    style_list[i] = "background-color:yellow"  # 中抗
                elif 1.5 < val <= 3.5:
                    style_list[i] = "background-color:#FFA500"  # 感S
                elif 1.0 <= val <= 1.5:
                    style_list[i] = "background-color:red"  # 高感HS
        return style_list

    def huskcov_color_cells(self,row):   #  苞叶覆盖度
        style_list = ['' for _ in row]
        for i in range(1, len(row)):
            if row[i] == '':
                continue
            else:
                val = float(row[i])
                if 7.5 < val <= 9.0:
                    style_list[i] = "background-color:#228B22"  # 高抗
                elif 6.5 < val <= 7.5:
                    style_list[i] = "background-color:#7FFF00"  # 抗
                elif 5.0 < val <= 6.5:
                    style_list[i] = "background-color:yellow"  # 中抗
                elif 3.5 < val <= 5.0:
                    style_list[i] = "background-color:#FFA500"  # 感S
                elif 1.0 <= val <= 3.5:
                    style_list[i] = "background-color:red"  # 高感HS
        return style_list

    def kersr_color_cells(self,row):   # 结实性
        style_list = ['' for _ in row]
        for i in range(1, len(row)):
            if row[i] == '':
                continue
            else:
                val = float(row[i])
                if 7.5 < val <= 9.0:
                    style_list[i] = "background-color:#228B22"  # 高抗
                elif 6.5 < val <= 7.5:
                    style_list[i] = "background-color:#7FFF00"  # 抗
                elif 5.0 < val <= 6.5:
                    style_list[i] = "background-color:yellow"  # 中抗
                elif 3.5 < val <= 5.0:
                    style_list[i] = "background-color:#FFA500"  # 感S
                elif 1.0 <= val <= 3.5:
                    style_list[i] = "background-color:red"  # 高感HS
        return style_list

    def tipfill_color_cells(self,row):  # 秃尖
        style_list = ['' for _ in row]
        for i in range(1, len(row)):
            if row[i] == '':
                continue
            else:
                val = float(row[i])
                if 8 < val <= 9.0:
                    style_list[i] = "background-color:#228B22"  # 高抗
                elif 7 < val <= 8:
                    style_list[i] = "background-color:#7FFF00"  # 抗
                elif 6.0 < val <= 7.0:
                    style_list[i] = "background-color:yellow"  # 中抗
                elif 5.0 < val <= 6.0:
                    style_list[i] = "background-color:#FFA500"  # 感S
                elif 1.0 <= val <= 5.0:
                    style_list[i] = "background-color:red"  # 高感HS
        return style_list

    def tdppct_color_cells(self,row):  # 倒伏倒折
        style_list = ['' for _ in row]
        for i in range(1, len(row)):
            if row[i] == '':
                continue
            else:
                val = float(row[i])
                if 0 <= val <= 5:
                    style_list[i] = "background-color:#228B22"  # 高抗
                elif 5 < val <= 10:
                    style_list[i] = "background-color:#7FFF00"  # 抗
                elif 10 < val <= 15:
                    style_list[i] = "background-color:yellow"  # 中抗
                elif 15 < val <= 30:
                    style_list[i] = "background-color:#FFA500"  # 感S
                elif 30 < val:
                    style_list[i] = "background-color:red"  # 高感HS
        return style_list

    def indara_color_cells(self,row):   #玉米螟
        style_list = ['' for _ in row]
        for i in range(1, len(row)):
            if row[i] == '':
                continue
            else:
                val = float(row[i])
                if 7.5 < val <= 9.0:
                    style_list[i] = "background-color:#228B22"  # 高抗
                elif 6.5 < val <= 7.5:
                    style_list[i] = "background-color:#7FFF00"  # 抗
                elif 5.0 < val <= 6.5:
                    style_list[i] = "background-color:yellow"  # 中抗
                elif 3.5 < val <= 5.0:
                    style_list[i] = "background-color:#FFA500"  # 感S
                elif 1.0 <= val <= 3.5:
                    style_list[i] = "background-color:red"  # 高感HS
        return style_list

    def kertpct_color_cells_HHH(self,row): # 霉变粒率 黄淮海
        style_list = ['' for _ in row]
        for i in range(1, len(row)):
            if row[i] == '':
                continue
            else:
                val = float(row[i])
                if 0.0 < val <= 0.5:
                    style_list[i] = "background-color:#228B22"  # 高抗
                elif 0.5 < val <= 1.0:
                    style_list[i] = "background-color:#7FFF00"  # 抗
                elif 1.0 < val <= 2.0:
                    style_list[i] = "background-color:yellow"  # 中抗
                elif 2.1 < val <= 4.0:
                    style_list[i] = "background-color:#FFA500"  # 感S
                elif 4.1 < val <= 100:
                    style_list[i] = "background-color:red"  # 高感HS
        return style_list

    def kertpct_color_cells_DHB(self,row):    # 霉变粒率 东华北
        style_list = ['' for _ in row]
        for i in range(1, len(row)):
            if row[i] == '':
                continue
            else:
                val = float(row[i])
                if 0.0 < val <= 0.5:
                    style_list[i] = "background-color:#228B22"  # 高抗
                elif 0.5 < val <= 1.0:
                    style_list[i] = "background-color:#7FFF00"  # 抗
                elif 1.0 < val <= 1.5:
                    style_list[i] = "background-color:yellow"  # 中抗
                elif 1.5 < val <= 2.0:
                    style_list[i] = "background-color:#FFA500"  # 感S
                elif 2.0 < val <= 100:
                    style_list[i] = "background-color:red"  # 高感HS
        return style_list

    # 点对点分析
    def point_to_point_analysis(self,df):
        # 获取地点的名称
        locations = df.columns[1:]
        # 筛选第一列的内容
        target_name = df.iloc[1, 0]
        cknames = df.iloc[2:, 0].values
        results = []  # 暂存结果
        # 遍历每个对照品种
        for ckname in cknames:
            # 找到目标品种和对照品种的行索引
            target_row = df[df.iloc[:, 0] == target_name]
            control_row = df[df.iloc[:, 0] == ckname]

            # 获取交集地点（两品种数据均有效且为数值的地点）
            valid_locations = []
            for loc in locations:
                target_val = target_row[loc].values[0]
                control_val = control_row[loc].values[0]
                # 检查两品种数据是否非空且可转换为数值
                try:
                    target_numeric = pd.to_numeric(target_val, errors='coerce')  # 将无法转换为数值的值直接转为NaN
                    control_numeric = pd.to_numeric(control_val, errors='coerce')
                    if pd.notna(target_numeric) and pd.notna(control_numeric):
                        valid_locations.append(loc)
                except:
                    continue

            # 交集点数
            point_count = len(valid_locations)

            if point_count > 0:  # 只有当有交集时才计算
                try:
                    # 目标品种和对照品种在交集地点的数据
                    target_values = pd.to_numeric(target_row[valid_locations].values[0], errors='coerce')
                    control_values = pd.to_numeric(control_row[valid_locations].values[0], errors='coerce')

                    # 计算均值
                    target_mean = np.mean(target_values)
                    control_mean = np.mean(control_values)

                    # 计算均值差（目标品种 - 对照品种）
                    mean_diff = target_mean - control_mean

                    # 计算极值
                    target_max = np.max(target_values)
                    target_min = np.min(target_values)
                    control_max = np.max(control_values)
                    control_min = np.min(control_values)
                    # 存储结果
                    results.append({
                        '目标品种': target_name,
                        '对照品种': ckname,
                        '对比点次': f"{point_count:.0f}",
                        '目标品种均值': f"{target_mean:.2f}",
                        '对照品种均值': f"{control_mean:.2f}",
                        '均值差': f"{mean_diff:.2f}",
                        '目标品种极大值': f"{target_max:.2f}",
                        '目标品种极小值': f"{target_min:.2f}",
                        '对照品种极大值': f"{control_max:.2f}",
                        '对照品种极小值': f"{control_min:.2f}"
                    })
                except Exception as e:
                    print(f"Error processing {target_name} vs {ckname}: {str(e)}")
                    continue
            else:
                print(f"No valid intersection points for {target_name} vs {ckname}.")
                results.append({'目标品种': target_name,
                        '对照品种': ckname,
                        '对比点次': f"{point_count:.0f}",
                        '目标品种均值': f"{target_mean:.2f}",
                        '对照品种均值': f"{control_mean:.2f}",
                        '均值差': f"{mean_diff:.2f}",
                        '目标品种极大值': f"{target_max:.2f}",
                        '目标品种极小值': f"{target_min:.2f}",
                        '对照品种极大值': f"{control_max:.2f}",
                        '对照品种极小值': f"{control_min:.2f}"})
        # 转换为 DataFrame 输出结果
        results_df = pd.DataFrame(results)
        # 对齐 results_df，使其第一行与 df 的第三行对齐
        # 在 results_df 顶部添加两行空数据
        n_rows_styled = len(df)
        n_rows_results = len(results_df)
        aligned_results_df = pd.DataFrame(
            np.nan,
            index=range(n_rows_styled),
            columns=results_df.columns
        )
        # 将 results_df 的数据插入，从索引 2 开始（对应 styled_df 的第三行）
        if n_rows_results > 0:
            # 确保只插入与 filtered_df 品种顺序一致的结果
            filtered_varieties = df.iloc[1:, 0].values  # 从第二行开始的品种名称
            result_indices = []
            for i, row in results_df.iterrows():
                if row['对照品种'] in filtered_varieties:
                    result_indices.append(i)
            if result_indices:
                aligned_results_df.iloc[2:2 + len(result_indices), :] = results_df.iloc[result_indices].values

        # 拼接 styled_df 和 aligned_results_df
        combined_df = pd.concat([df, aligned_results_df], axis=1)

        return combined_df

    # 差异点分析
    def difference_point_analysis(self, df):
        """
        差异点分析函数 - 只分析两个品种数值不同的性状点
        保持与 point_to_point_analysis 相似的输出结构和逻辑

        参数:
            df: DataFrame, 包含品种名称(第一列)和各地点性状数据

        返回:
            包含差异点分析结果的DataFrame，与原数据合并
        """
        # 获取地点的名称(从第二列开始)
        locations = df.columns[1:]
        # 获取目标品种名称(第二行第一列)
        target_name = df.iloc[1, 0]
        # 获取对照品种名称列表(从第三行开始)
        cknames = df.iloc[2:, 0].values

        results = []  # 暂存结果

        # 遍历每个对照品种
        for ckname in cknames:
            # 找到目标品种和对照品种的行索引
            target_row = df[df.iloc[:, 0] == target_name]
            control_row = df[df.iloc[:, 0] == ckname]

            # 获取差异地点(两品种数据均有效、可转换为数值且数值不同的地点)
            diff_locations = []
            target_diff_values = []
            control_diff_values = []
            if ckname == 'SK6H':
                sgjskjfks =1
            for loc in locations:
                target_val = target_row[loc].values[0]
                control_val = control_row[loc].values[0]

                # 检查两品种数据是否非空、可转换为数值且不同
                try:
                    target_numeric = pd.to_numeric(target_val, errors='coerce')
                    control_numeric = pd.to_numeric(control_val, errors='coerce')

                    if (pd.notna(target_numeric) and
                            pd.notna(control_numeric) and
                            (target_numeric != control_numeric)):
                        diff_locations.append(loc)
                        target_diff_values.append(target_numeric)
                        control_diff_values.append(control_numeric)
                except:
                    continue

            # 差异点数
            diff_point_count = len(diff_locations)

            if diff_point_count > 0:  # 只有当有差异点时才计算
                try:
                    # 计算均值(仅使用差异点)
                    target_mean = np.mean(target_diff_values)
                    control_mean = np.mean(control_diff_values)

                    # 计算均值差(目标品种 - 对照品种)
                    mean_diff = target_mean - control_mean

                    # 计算极值(仅使用差异点)
                    target_max = np.max(target_diff_values)
                    target_min = np.min(target_diff_values)
                    control_max = np.max(control_diff_values)
                    control_min = np.min(control_diff_values)

                    # 计算差异率(差异点占所有有效点的比例)
                    # 首先计算总有效点数(两品种都有有效数据的点)
                    valid_locations = [
                        loc for loc in locations
                        if (pd.notna(pd.to_numeric(target_row[loc].values[0], errors='coerce')) and
                            pd.notna(pd.to_numeric(control_row[loc].values[0], errors='coerce')))
                    ]
                    total_valid_points = len(valid_locations)
                    diff_ratio = diff_point_count / total_valid_points if total_valid_points > 0 else 0

                    # 存储结果(保持与原函数相似的格式，增加差异点相关信息)
                    results.append({
                        '目标品种': target_name,
                        '对照品种': ckname,
                        '对比点次': f"{total_valid_points:.0f}",  # 两品种都有有效数据的总点数
                        '差异点次': f"{diff_point_count:.0f}",  # 新增: 数值不同的点数
                        '差异率(%)': f"{diff_ratio * 100:.2f}",  # 新增: 差异点占比
                        '目标品种均值': f"{target_mean:.2f}",
                        '对照品种均值': f"{control_mean:.2f}",
                        '均值差': f"{mean_diff:.2f}",
                        '目标品种极大值': f"{target_max:.2f}",
                        '目标品种极小值': f"{target_min:.2f}",
                        '对照品种极大值': f"{control_max:.2f}",
                        '对照品种极小值': f"{control_min:.2f}",
                        '差异点列表': ', '.join(diff_locations) if diff_locations else '无'  # 新增: 差异点名称
                    })
                except Exception as e:
                    print(f"Error processing {target_name} vs {ckname}: {str(e)}")
                    continue
            else:
                print(f"No difference points found for {target_name} vs {ckname} (all values are same or invalid).")
                results.append({'目标品种': target_name,
                                '对照品种': ckname,
                                '对比点次': 0,  # 两品种都有有效数据的总点数
                                '差异点次': 0,  # 新增: 数值不同的点数
                                '差异率(%)': 0,  # 新增: 差异点占比
                                '目标品种均值': f"{target_mean:.2f}",
                                '对照品种均值': f"{control_mean:.2f}",
                                '均值差': f"{mean_diff:.2f}",
                                '目标品种极大值': f"{target_max:.2f}",
                                '目标品种极小值': f"{target_min:.2f}",
                                '对照品种极大值': f"{control_max:.2f}",
                                '对照品种极小值': f"{control_min:.2f}",
                                '差异点列表': ', '.join(diff_locations) if diff_locations else '无'  })

        # 转换为 DataFrame 输出结果
        results_df = pd.DataFrame(results)

        # 对齐 results_df，使其与原数据格式一致
        n_rows_original = len(df)
        n_rows_results = len(results_df)

        aligned_results_df = pd.DataFrame(
            np.nan,
            index=range(n_rows_original),
            columns=results_df.columns
        )

        # 将 results_df 的数据插入，从索引 2 开始(对应原数据的第三行)
        if n_rows_results > 0:
            # 确保只插入与 df 品种顺序一致的结果
            filtered_varieties = df.iloc[2:, 0].values  # 从第三行开始的品种名称
            result_indices = []

            for i, row in results_df.iterrows():
                if row['对照品种'] in filtered_varieties:
                    result_indices.append(i)

            if result_indices:
                aligned_results_df.iloc[2:2 + len(result_indices), :] = results_df.iloc[result_indices].values

        # 拼接原数据和结果
        combined_df = pd.concat([df, aligned_results_df], axis=1)

        return combined_df


    def plot(self):
        self.__get_title("TD性状透视图2025")

        selected_AOA_list, selected_trait_column_list,selected_sample_name,selected_CK_names = self.get_dropdown_menu_bar()

        sample_data_df = self.get_sample_data_df(selected_AOA_list)
        for trait_name in selected_trait_column_list:  # 遍历性状
            self.__get_sub_tilte(self.trait_column_name_to_chinese_name_dict[trait_name])
            Location_set = pd.unique(sample_data_df["Location_TD"])
            sample_name_set = pd.unique(sample_data_df['VarNam'])
            ## 选择目标品种
            if selected_sample_name in sample_name_set:
            # 用户手动选择目标品种，会自动将该品种提至首行
                idx = np.where(sample_name_set == selected_sample_name)[0][0]
                sample_name_set = np.concatenate(([sample_name_set[idx]],
                                                  np.delete(sample_name_set, idx)))
            ## 选择对照品种
            # 将 selected_CK_names 依次排列在 selected_sample_name 之后
            # 提取当前 sample_name_set 中不在 selected_CK_names 和 selected_sample_name 中的元素
            remaining_names = [name for name in sample_name_set if
                               name not in [selected_sample_name] + selected_CK_names]
            # 重新构建 sample_name_set
            # 顺序: selected_sample_name -> selected_CK_names -> 剩余元素
            sample_name_set = np.concatenate(([selected_sample_name],
                                              selected_CK_names,
                                              remaining_names))

            trait_summary_df = pd.DataFrame()
            flag_percent =0  # 百分比性状的标识
            if "%" in self.trait_column_name_to_chinese_name_dict[trait_name]:
                flag_percent =1
            for sample_name in sample_name_set:  # 遍历品种名称
                summary_dict ={}
                for loc_name in Location_set:
                    try:
                        sample_trait_mean_value =np.mean(sample_data_df[(sample_data_df['VarNam'] == sample_name) & (sample_data_df['Location_TD'] == loc_name)][trait_name].tolist())
                    except:
                        sample_trait_mean_value = 0
                    if flag_percent == 1:
                        # 将percent类型的转为百分比形式展示
                        summary_dict[loc_name]= [sample_trait_mean_value*100]
                    else:
                        summary_dict[loc_name] = [sample_trait_mean_value]
                summary_df = pd.DataFrame(summary_dict)   # 将dict数据转化为DataFrame格式
                trait_summary_df = pd.concat([trait_summary_df, summary_df],ignore_index=True)  # 一行一行拼接数据
            # 将全为nan的地点列过滤掉    也要更新地点列表
            trait_summary_df = trait_summary_df.dropna(axis=1,how='all')
            remain_locations = set(trait_summary_df.columns)
            updated_location_set = set(Location_set).intersection(remain_locations)
            # 将该测试点的所有品种的数值求和取均值
            mean_dict = {}
            for loc_name in updated_location_set:
                mean_dict[loc_name] = [np.mean(trait_summary_df[loc_name])]
            mean_summary_df = pd.DataFrame(mean_dict)
            summary_df = pd.concat([mean_summary_df, trait_summary_df])
            # 将Nan换为空
            summary_df = summary_df.fillna('')
            #保留1位小数
            summary_df = summary_df.applymap(self.format_float)
            # 将 品种名 和平均数 放在 第一列上
            sample_name_list = list(sample_name_set)
            sample_name_list.insert(0, '平均数')
            summary_df.insert(0,'品种名称', sample_name_list)

            # 根据平均数的大小，对测试点进行按照大小排序  即按照列排序
            row_index = 0
            sorted_location = summary_df.iloc[row_index].sort_values(ascending=False).index
            sorted_df = summary_df[sorted_location]


            # 重置索引
            sorted_df.reset_index(drop=True, inplace=True)
            ##### 设置"点对点全点分析"比较  用对比的两个品种全部交集点的数据进行比较。
            # 分析按钮
            # if st.button("点对点全点分析",key=trait_name+'point2point_button'):
            #     sorted_df = self.point_to_point_analysis(sorted_df)
            # if st.button("差异点分析",key=trait_name+'diffpoint_button'):
            #     sorted_df = self.difference_point_analysis(sorted_df)

            # 设置两列索引
            col0,col1 = st.columns((1, 6))

            available_indices = list(sorted_df.index)
            # 因为第0行是平均数的行 必须保留
            if 0 in available_indices:
                available_indices.remove(0)

            with col0:
                # 多选框，选项为品种的索引
                selected_indices = st.multiselect(
                    '选择id进行隐藏该行数据',
                    available_indices,  # 使用 DataFrame 的索引作为选项
                    key=trait_name+'id'      # 需要设置动态的key参数，确保键唯一
                )
                st.session_state.hidden_rows = set(selected_indices)
                # 使用 <br> 标签插入多行间距
                st.markdown("<br><br>", unsafe_allow_html=True)
                select_location = st.multiselect(
                    '选择地点进行隐藏该列数据',
                    sorted_location[1:],
                    #default =None,
                    default='平度',
                    key= trait_name+'location'
                )
            filtered_df = sorted_df
            with col1:

                # 为几个分析设计其对应的布局
                col11, col12,col13,col14 = st.columns((1,1,3,2))
                # 在列中放置按钮并获取点击状态
                with col11:
                    point2point_clicked = st.button("点对点全点分析", key=trait_name + 'point2point_button')
                with col12:
                    diffpoint_clicked = st.button("差异点分析", key=trait_name + 'diffpoint_button')
                with col13:
                    keypoint_choose = st.multiselect(
                                        '',
                                        sorted_location[1:],
                                        placeholder="选择关键点",
                                        label_visibility="collapsed")  # 移除label的占位
                with col14:
                    keypoint_clicked = st.button("关键点分析", key=trait_name + 'keypoint_button')
                # 根据 selected_indices 显示或隐藏对应的行
                if st.session_state.hidden_rows and select_location is not None:   #id和地点都被选择
                    filtered_df = filtered_df.drop(columns=select_location)   # 移除地点
                    if point2point_clicked:
                        filtered_df = self.point_to_point_analysis(filtered_df)
                    if diffpoint_clicked:
                        filtered_df = self.difference_point_analysis(filtered_df)
                    filtered_df = filtered_df.drop(index=list(st.session_state.hidden_rows))    # 移除id索引
                elif select_location is not None:    # 地点被选择
                    filtered_df = filtered_df.drop(columns=select_location)
                    if point2point_clicked:
                        filtered_df = self.point_to_point_analysis(filtered_df)
                    if diffpoint_clicked:
                        filtered_df = self.difference_point_analysis(filtered_df)
                elif st.session_state.hidden_rows:  # id索引被选择
                    if point2point_clicked:
                        filtered_df = self.point_to_point_analysis(filtered_df)
                    if diffpoint_clicked:
                        filtered_df = self.difference_point_analysis(filtered_df)
                    filtered_df = filtered_df.drop(index=list(st.session_state.hidden_rows))  # 移除id索引
                else:         # 地点和 id索引均没有被选择
                    if point2point_clicked:
                        filtered_df = self.point_to_point_analysis(filtered_df)
                    if diffpoint_clicked:
                        filtered_df = self.difference_point_analysis(filtered_df)

                # 显示结果，只对前 n 列原数据  进行上色  对后面的分析数据不执行
                column_length = (len(sorted_location) - len(select_location)) if select_location is not None else len(sorted_location)
                styled_columns = filtered_df.columns[:column_length]  #  排除掉点对点分析、差异点分析等的那些列

                # 对第一列的品种名称及平均数 进行整体添加背景色
                styled_df = filtered_df.style.apply(self.highlight_first_column, axis=1,subset=styled_columns)   # axis=1 返回需要是list或数组

                # 给透视图的性状上色
                if trait_name == 'STKRPCT_TD':  # 青枯病
                    styled_df = styled_df.apply(self.stkrpct_color_cells,axis=1,subset=styled_columns)
                if trait_name == 'PHT':  # 株高
                    styled_df = styled_df.apply(self.pht_color_cells, axis=1,subset=styled_columns)
                if trait_name == 'EHT':  # 穗位
                    styled_df = styled_df.apply(self.eht_color_cells, axis=1,subset=styled_columns)
                if trait_name in ['GLS','CLB','RSTCOM','CULSPT','CWLSPT']:  # 叶部病害（大斑病、灰斑病、普通锈病、白斑病、弯孢叶斑病）  没按照顺序
                    styled_df = styled_df.apply(self.leaf_colors_cells, axis=1,subset=styled_columns)
                if trait_name == 'HUSKCOV':  # 苞叶覆盖度
                    styled_df = styled_df.apply(self.huskcov_color_cells, axis=1,subset=styled_columns)
                if trait_name == 'KERSR':    # 结实性
                    styled_df = styled_df.apply(self.kersr_color_cells, axis=1,subset=styled_columns)
                if trait_name == 'TIPFILL':  # 秃尖
                    styled_df = styled_df.apply(self.tipfill_color_cells, axis=1,subset=styled_columns)
                if trait_name == 'TDPPCT_TD':  # 倒伏倒折
                    styled_df = styled_df.apply(self.tdppct_color_cells, axis=1,subset=styled_columns)
                if trait_name == 'INDARA':  # 玉米螟
                    styled_df = styled_df.apply(self.indara_color_cells, axis=1,subset=styled_columns)
                if trait_name == 'KERTPCT': # 霉变粒率
                    #  一般来说，分析的时候只选择一个生态亚区，来分析，但是若选择了两个，则可能会存在不同的上色标准
                    sub1 = ['北方超早', '北方极早', '北方早熟', '东华北中早', '东华北中熟', '东华北中晚']
                    sub2 = ['黄淮南', '黄淮北']

                    if pd.Series(selected_AOA_list).isin(sub1).any():
                        styled_df = styled_df.apply(self.kertpct_color_cells_HHH, axis=1,subset=styled_columns)
                    elif pd.Series(selected_AOA_list).isin(sub2).any():
                        styled_df = styled_df.apply(self.kertpct_color_cells_DHB, axis=1,subset=styled_columns)

                # 显示过滤后的 DataFrame
                st.dataframe(styled_df, height=700)

        st.markdown("""
                        ##### 注释：
                        - 下拉菜单：
                            - “选择生态亚区（熟期）”、“选择性状”两个下拉菜单来指定想要查询的生态亚区和性状，均可多选；
                        - 透视图表格：展示所有品种在特定生态亚区（熟期）下的特定性状的数值：
                            - 第一列 表示所包含的品种名称，除第一个“平均数”表示的是特定的地点下所有的品种；
                            - 第一行 表示所包含的测试点名称，为选择的生态亚区下所包含的。
                            - 数据： 除“平均数”行是对应的一行为某一测试点下所有品种的性状数据均值，其余为某一品种在某一测试点下的性状数据均值。
                                     %制类型的性状，其数据均为XX.XX%
                        - 默认对测试点的性状平均值进行排序，按从大到小的顺序排列测试点。
                        """)


if __name__ == '__main__':
#def main():
    st.set_page_config(layout='wide')
    query_statement = """
    select * from "DWS"."TDPheno2024" 
    """
    df = Plotter(query_statement)
    df.plot()