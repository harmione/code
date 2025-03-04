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
        if 'hidden_rows' not in st.session_state:
            st.session_state.hidden_rows = set()
        self.query_statement = query_statement
        self.data_df = self.__get_data_df()
        self.AOAname_list = self.__get_AOAname_list()
        self.trait_column_name_to_chinese_name_dict = {'YLD14_TD': '产量(kg/亩)',
                                                       'STKRPCT_TD': '青枯病比例(%)',
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
                    margin-left:200px;    #左侧边距
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


    def plot(self):
        self.__get_title("TD性状透视图2025")
        selected_AOA_list, selected_trait_column_list,selected_sample_name,selected_CK_names = self.get_dropdown_menu_bar()
        ###############################  selected_CK_name和selected_sample_name未作处理

        sample_data_df = self.get_sample_data_df(selected_AOA_list)
        for trait_name in selected_trait_column_list:
            self.__get_sub_tilte(self.trait_column_name_to_chinese_name_dict[trait_name])
            Location_set = pd.unique(sample_data_df["Location_TD"])
            sample_name_set = pd.unique(sample_data_df['VarNam'])
            if selected_sample_name in sample_name_set:
                # 若用户手动选择目标品种，会自动将该品种提至首行
                idx = np.where(sample_name_set == selected_sample_name)[0][0]
                sample_name_set = np.concatenate(([sample_name_set[idx]],
                                                  np.delete(sample_name_set, idx)))
            #将 selected_CK_names 依次排列在 selected_sample_name 之后
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
                    default =None,
                    key= trait_name+'location'
                )

            with col1:
                # 根据 selected_indices 显示或隐藏对应的行
                filtered_df = sorted_df.drop(
                    index=list(st.session_state.hidden_rows)) if st.session_state.hidden_rows else sorted_df
                # 对选了的地点，进行移除操作
                if select_location is not None:
                    filtered_df = filtered_df.drop(
                        columns=select_location
                    )

                # 对第一列的品种名称及平均数 进行整体添加背景色
                styled_df = filtered_df.style.apply(self.highlight_first_column, axis=1)   # axis=1 返回需要是list或数组
                # 给透视图的性状上色
                if trait_name == 'STKRPCT_TD':  # 青枯病
                    styled_df = styled_df.apply(self.stkrpct_color_cells,axis=1)
                if trait_name == 'PHT':  # 株高
                    styled_df = styled_df.apply(self.pht_color_cells, axis=1)
                if trait_name == 'EHT':  # 穗位
                    styled_df = styled_df.apply(self.eht_color_cells, axis=1)
                if trait_name in ['GLS','CLB','RSTCOM','CULSPT','CWLSPT']:  # 叶部病害（大斑病、灰斑病、普通锈病、白斑病、弯孢叶斑病）  没按照顺序
                    styled_df = styled_df.apply(self.leaf_colors_cells, axis=1)
                if trait_name == 'HUSKCOV':  # 苞叶覆盖度
                    styled_df = styled_df.apply(self.huskcov_color_cells, axis=1)
                if trait_name == 'KERSR':    # 结实性
                    styled_df = styled_df.apply(self.kersr_color_cells, axis=1)
                if trait_name == 'TIPFILL':  # 秃尖
                    styled_df = styled_df.apply(self.tipfill_color_cells, axis=1)
                if trait_name == 'TDPPCT_TD':  # 倒伏倒折
                    styled_df = styled_df.apply(self.tdppct_color_cells, axis=1)
                if trait_name == 'INDARA':  # 玉米螟
                    styled_df = styled_df.apply(self.indara_color_cells, axis=1)
                #  一般来说，分析的时候只选择一个生态亚区，来分析，但是若选择了两个，则可能会存在不同的上色标准     这里需要修改
                sub1 = ['北方超早', '北方极早', '北方早熟', '东华北中早', '东华北中熟', '东华北中晚']
                sub2 = ['黄淮南', '黄淮北']

                if pd.Series(selected_AOA_list).isin(sub1).any():
                    styled_df = styled_df.apply(self.kertpct_color_cells_HHH, axis=1)
                elif pd.Series(selected_AOA_list).isin(sub2).any():
                    styled_df = styled_df.apply(self.kertpct_color_cells_DHB, axis=1)

                # 设置"点对点全点分析"比较  用上ckname 和 没有style样式的 filtered_df
                for name in filtered_df.iloc[1:,0]:      # 用iloc()方法来迭代dataframe
                    varname = name



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