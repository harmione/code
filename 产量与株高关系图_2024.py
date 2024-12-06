import os
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import plotly.colors as pc
from urllib.parse import quote_plus
from sqlalchemy import create_engine


class DataProcessor:
    #加载和处理数据
    # def __init__(self, varieties_path, controls_path):
    #     # 初始化数据路径和数据框
    #     self.varieties_path = varieties_path
    #     self.controls_path = controls_path
    #     self.varieties_df = None
    #     self.controls_df = None

    def __init__(self, engine):
        self.engine = engine
        self.varieties_df = None
        self.controls_df = None

    def load_data(self):
        # 只加载必要的列，并指定数据类型，避免不必要的内存消耗
        # self.varieties_df = pd.read_csv(self.varieties_path,dtype={'Year': int, 'AOA': str, 'Type': str, 'Name': str, 'PredVal_YLD14': float, 'PredVal_MST': float,'CKpct_YLD14':float,'CKpct_MST':float})
        # self.controls_df = pd.read_csv(self.controls_path,dtype={'Year': int, 'AOA': str, 'EntryBookPrj':str, 'TrialType':str, 'Varnam': str, 'CheckNo': str})
        # FROM "DWS"."RNDPhenoAnalysis"

        varieties_query = """
        SELECT "Year", "EntryBookPrj", "TrialType", "Varnam", "PredVal_YLD14", "PredVal_PHT", "CKpct_YLD14", "CKpct_PHT", 
        "BookName"
        FROM "test"."ANOVA.Trial-PCM.EstimatedValue.EntryBookPrj"
        WHERE "BookName"='All' AND "CK"='CKmean'
        """
        #WHERE "Location"='All' AND   "Type" NOT IN ('TC1','TC2')

        controls_query = """
        SELECT DISTINCT "Year", "EntryBookPrj", "TrialType", "Varnam", "CheckNo"
        FROM "DWS"."Pheno"
        WHERE "BookPrj"<>'TD' AND "CheckNo" IS NOT NULL AND "EntryBookPrj" IS NOT NULL
        """
        self.varieties_df = pd.read_sql(varieties_query, self.engine)
        self.varieties_df['Year'] = self.varieties_df['Year'].astype(int) #把年份转成整数
        self.controls_df = pd.read_sql(controls_query, self.engine)
        self.controls_df['Year'] = self.controls_df['Year'].astype(int)

    def process_data(self):
        # 对 controls_df 进行处理，提取有用的对照品种信息
        controls_filtered = self.controls_df[self.controls_df['CheckNo'].notnull()]
        control_varieties = controls_filtered.drop_duplicates(subset=['Year', 'EntryBookPrj', 'Varnam'])
        #drop_duplicates 方法从筛选后的数据中去除重复项，确保每个 Year (年份) 和 AOA (成熟期) 组合中的对照品种 Varnam 只出现一次

        # 合并处理后的对照组数据
        self.varieties_df = self.varieties_df.merge(
            control_varieties[['Year', 'EntryBookPrj', 'Varnam']],
            left_on=['Year', 'EntryBookPrj', 'Varnam'],
            right_on=['Year', 'EntryBookPrj', 'Varnam'],
            how='left',
            indicator=True
            #indicator=True 添加了一个额外的列 _merge 来指示每行数据是如何合并的。
            # 如果一行来自于两个数据框的匹配合并，_merge 列的值为 both。
        )
        # 标记对照品种
        self.varieties_df['Control'] = (self.varieties_df['_merge'] == 'both')
        #这行代码创建一个新的列 Control，通过判断 _merge 列是否为 both 来标记对照品种。
        # 如果是 both，则 Control 列为 True，表示该记录是对熟期和品种名匹配的对照品种，否则为 False。
        self.varieties_df.drop(columns=['_merge'], inplace=True)
        #最后，使用 drop 方法移除 _merge 列，因为此列已经不再需要，它只是用来辅助标记对照品种的。

def create_db_engine():
    # Make sure you replace the .env path if needed or directly assign the values
    env_file_path = '.env'
    env_data_dict = {}
    with open(env_file_path, 'r') as f: #用with 语句打开文件，这样可以保证文件在读取后会被正确关闭。
        for line in f:  #遍历文件的每一行来读取环境变量
            if line.strip() and not line.startswith('#'): #这个条件语句用来忽略空行或以 # 开头的注释行。
                key, value = line.strip().split('=', 1)
                #对每一行使用 = 分隔符分割成键和值，并分别存储到 key 和 value 变量中。
                # split('=', 1) 确保分割只在第一个 = 处发生，这对于处理包含 = 的值很有用。
                env_data_dict[key] = value
                #strip() 方法不需要任何参数，它将去除字符串两端的所有空白字符。
                #你也可以指定一个字符串作为参数，方法将移除字符串两端所有包含这些字符的组合。
                #例如，line.strip('abc')将会移除字符串两端所有的 'a'、'b'、'c' 字符及其组合。

    db_password = quote_plus(env_data_dict.get("DB_PASSWORD"))  # URL encoding the password
    engine = create_engine(
        f'postgresql://{env_data_dict.get("DB_USER")}:{db_password}@{env_data_dict.get("DB_HOST")}:'
        f'{env_data_dict.get("DB_PORT")}/{env_data_dict.get("DB_NAME")}' #postgresql://{user}:{password}@{host}:{port}/{dbname}
    ) #使用 quote_plus 函数对密码进行 URL 编码。这是因为如果密码中包含特殊字符（如 @, :, / 等），直接用于 URL 时可能会引起解析错误。
    return engine

class UI:
    #显示界面
    def __init__(self, data_processor):
        #初始化数据处理器和选定的熟期
        self.data_processor = data_processor
        self.selected_years = []
        self.selected_periods = []
        self.selected_types = []
        self.selected_data_type = '性状绝对值'


    def set_page_config(self):
        #设置页面布局wide并随浏览器大小更改
        st.set_page_config(layout="wide")

    def display_title(self, title_content):
        #显示自定义样式的标题
        st.markdown(
            """
                <style>
                .custom-title {
                    font-size: 30px;
                    font-weight: bold;
                }
                </style>
            """,
            unsafe_allow_html=True
        )
        st.markdown(f'<p class="custom-title">{title_content}</p>', unsafe_allow_html=True)
        # st.title('产量水分分布图')
        # st.title 是 Streamlit 中用于显示标题的函数，但它不允许自定义样式如字体大小和加粗。
        # 如果你需要自定义样式，那么 st.markdown 是一个更灵活的选择

    def display_filters(self):
        # 年份、熟期、试验类型保持所有选项都显示的逻辑
        df = self.data_processor.varieties_df
        available_years = sorted(df['Year'].unique())

        # 定义熟期的优先顺序
        period_order = [
            'EMSP',  # 早熟春玉米区
            'MMSP',  # 中熟春玉米区
            'LMSP',  # 晚熟春玉米区
            'NCSU',  # 夏玉米北部区
            'MCSU',  # 夏玉米中部区
            'SCSU',  # 夏玉米南部区
            'SWCN',  # 西南玉米区
            'SP',  # 春玉米区
            'SU'  # 夏玉米区
        ]

        type_order = [
            'TC1','TC2','P1','P2','P3','P4'
        ]

        # 自定义排序方法，按period_order排序，不在period_order中的按字母排序
        def sort_periods(periods):
            return sorted(periods, key=lambda x: (period_order.index(x) if x in period_order else len(period_order), x))

        # 自定义排序方法，按type_order排序，不在type_order中的按字母排序
        def sort_types(types):
            return sorted(types, key=lambda x: (type_order.index(x) if x in type_order else len(type_order), x))

        # 获取所有的熟期并排序
        available_periods = sort_periods(df['EntryBookPrj'].unique())
        available_periods = ['ALL'] + available_periods

        available_types = sort_types(df['TrialType'].unique())
        available_types = ['ALL'] + available_types


        # 创建多列布局
        col0, col1, col2, col3, col4 = st.columns(5)

        with col0:
            self.selected_data_type = st.selectbox('数据类型', ['性状绝对值', '与对照相对值'])

        # 选择年份
        with col1:
            self.selected_years = st.multiselect('年份:', available_years, default=available_years[:2])
            if 'ALL' in self.selected_years:
                self.selected_years = available_years[1:]

        # 如果选择了年份，则根据年份筛选可用的熟期，并保持排序逻辑
        if self.selected_years:
            filtered_periods = df[df['Year'].isin(self.selected_years)]['EntryBookPrj'].unique()
            available_periods = sort_periods(filtered_periods)
            available_periods = ['ALL'] + available_periods

        # 选择熟期
        with col2:
            self.selected_periods = st.multiselect('育种站:', available_periods, default=['CC'])
            if 'ALL' in self.selected_periods:
                self.selected_periods = available_periods[1:]
                # 选择除 'ALL' 以外的所有选项.[1:] 表示从列表的第一个索引（即索引为 1 的元素）开始，选择列表中所有剩余的元素。
                # 索引0是ALL选项

        # 根据选择的年份和熟期过滤可用的试验类型
        if self.selected_years and self.selected_periods:
            filtered_types = df[
                (df['Year'].isin(self.selected_years)) &
                (df['EntryBookPrj'].isin(self.selected_periods))
                ]['TrialType'].unique()
            available_types = sort_types(filtered_types)
            available_types = ['ALL'] + available_types

        # 选择试验类型
        with col3:
            self.selected_types = st.multiselect('试验类型:', available_types, default='P1')
            if 'ALL' in self.selected_types:
                self.selected_types = available_types[1:]

        # 根据前面的选择动态筛选品种名称
        filtered_df = df[
            (df['Year'].isin(self.selected_years)) &
            (df['EntryBookPrj'].isin(self.selected_periods)) &
            (df['TrialType'].isin(self.selected_types))
            ]
        available_names = ['ALL'] + sorted(filtered_df['Varnam'].unique())

        with col4:
            self.selected_names = st.multiselect('品种名称:', available_names, default='ALL')
            if 'ALL' in self.selected_names:
                self.selected_names = available_names[1:]

    def display_charts(self):
        #根据用户选择的条件显示图表
        filtered_df = self.data_processor.varieties_df[
            (self.data_processor.varieties_df['Year'].isin(self.selected_years)) &
            (self.data_processor.varieties_df['EntryBookPrj'].isin(self.selected_periods)) &
            (self.data_processor.varieties_df['TrialType'].isin(self.selected_types))
            ]

        # 如果选择了品种，则只过滤测试品种，不影响对照品种
        if 'ALL' not in self.selected_names:
            filtered_df = filtered_df[filtered_df['Varnam'].isin(self.selected_names) | filtered_df['Control']]

        if self.selected_data_type == '性状绝对值':
            y_column = 'PredVal_YLD14'
            x_column = 'PredVal_PHT'
            y_label = '产量(kg/亩)'
            x_label = '株高(cm)'
        else:
            y_column = 'CKpct_YLD14'
            x_column = 'CKpct_PHT'
            y_label = '相对产量值'
            x_label = '相对株高值'

        grouped_df = filtered_df.groupby(['Year', 'EntryBookPrj', 'TrialType'])
        num_cols = 2  # 每行显示的图表数量
        col_count = 0
        cols = None

        for (year, EntryBookPrj, trial_type), df_group in grouped_df:
            if col_count % num_cols == 0:
                cols = st.columns(num_cols)

            fig = go.Figure()

            # 分离测试品种和对照品种
            control_group = df_group[df_group['Control']]
            test_group = df_group[~df_group['Control']]

            # 添加测试品种
            fig.add_trace(go.Scatter(
                x=test_group[x_column],
                y=test_group[y_column],
                mode='markers+text',
                name='测试品种',
                marker=dict(color='blue', symbol='circle', size=10),
                text=test_group['Varnam'],
                textposition='top center',
                #hoverinfo='none',# 这里设置为 'none' 以去掉悬浮效果
                # 在 Python 中，最后一个项目后的逗号是可选的
            ))

            #添加对照组
            fig.add_trace(go.Scatter(
                x=control_group[x_column],
                y=control_group[y_column],
                mode='markers+text',
                name='对照品种',
                marker=dict(color='red', symbol='circle', size=10),
                text=control_group['Varnam'],
                textposition='top center',
                #hoverinfo='none',
                #showlegend=False if control_name in fig.data else True,  # 只在第一次显示图例,避免重复显示堆叠
            ))

            # 更新布局
            fig.update_layout(
                autosize=True,
                height=800,  # 固定图表的高度
                title={
                    'text': f'年份:{year}   育种站:{EntryBookPrj}   试验类型:{trial_type}', #图表的标题文本
                    'y': 0.96, #标题在 y 轴上的位置，0.9 表示在图表顶部下方 10% 处。
                    'x': 0.56, #标题在 x 轴上的位置，0.56 表示略偏右（从左向右56%的位置）
                    'xanchor': 'center', #水平对齐方式，设为 'center' 表示标题相对于 x 位置居中对齐。
                    'yanchor': 'top', #垂直对齐方式，设为 'top' 表示标题相对于 y 位置顶端对齐。
                    'font': dict(size=18) #字体
                },
                font=dict(color='black'), # 全局字体颜色设置为黑色
                legend={ #图例的设置
                    'orientation': 'h', # 图例的排列方式，设为 'h' 表示水平排列
                    'yanchor': 'bottom', # 图例在 y 轴上的对齐方式，设为 'bottom' 表示图例的底部与 y 位置对齐。
                    'y': 1.01, #图例在 y 轴上的位置，1.02 表示在图表顶部稍上方。
                    'xanchor': 'center',#图例在 x 轴上的对齐方式，设为 'center' 表示图例的中心与 x 位置对齐
                    'x': 0.5,  #图例在 x 轴上的对齐方式，设为 'center' 表示图例的中心与 x 位置对齐
                    'font': dict(size=14) #设置图例文本的字体大小，这里设为 14。
                },
                xaxis=dict(
                    title=x_label, # 横轴标题
                    titlefont=dict(size=16, color='black'), # 标题字体大小
                    showline=True, # 显示轴线
                    linewidth=2, # 轴线宽度
                    linecolor='black', # 轴线颜色
                    tickfont=dict(size=16, color='black'), #设置刻度字体的大小和颜色，这里设为 16 和黑色。
                    ticks='outside',  # 刻度线设置外侧
                    tickcolor='black', #设置刻度线的颜色，这里设为黑色。
                    ticklen=5, #设置刻度线的长度，这里设为 5
                    #scaleanchor='y',  # 锁定横纵坐标的比例
                    #scaleratio=1  # 保持 1:1 的比例
                    tickformat='.2f',  # 保留两位小数显示
                ),
                yaxis=dict(
                    title=y_label,
                    titlefont=dict(size=16, color='black'),
                    showline=True, # 显示轴线
                    linewidth=2,  # 轴线宽度
                    linecolor='black',  # 轴线颜色
                    automargin=True,
                    ticks='outside', # 刻度线设置外侧
                    ticklen=5, # 刻度线长度
                    tickcolor='black',
                    tickfont=dict(size=16, color='black'), # 坐标轴刻度字体大小
                    range=[df_group[y_column].min() * 0.97, df_group[y_column].max() * 1.05],
                    # 乘以 0.9 将最小值缩小 10%，以便图表的 y 轴下界稍微低于实际数据中的最小值。这样做可以留出一些空间，
                    # 乘以 1.05 将最大值放大 10%，以便图表的 y 轴上界稍微高于实际数据中的最大值
                    #tickformat = '.2f',  # 保留两位小数显示
                )
            )

            # 显示图表在指定的列中
            cols[col_count % num_cols].plotly_chart(fig,use_container_width=True)
            col_count += 1
        st.markdown("""
                ##### 注释：
                - 下拉菜单：选择绘图使用的数据
                    - 数据类型：
                        - 与对照相对值 = 测试品种性状值/对照品种性状值 *100
                        - 性状绝对值：性状的实际测量值
                    - 熟期：EMSP：早熟春玉米区；MMSP：中熟春玉米区；LMSP：晚熟春玉米区；NCSU：夏玉米北部区；MCSU：夏玉米中部区；SCSU：夏玉米南部区；SWCN：西南玉米区；SP：春玉米区；SU:夏玉米区
                    - 品种名称：选择想看的品种名称，支持手动输入
                - 对照品种固定在图中
                """)

#if __name__ == "__main__":
def main():
    #主程序块：加载和处理数据，然后显示用户界面

    # current_dir = os.path.dirname(__file__)
    # varieties_path = os.path.join(current_dir, '..', 'data', 'DWS_RNDPhenoAnalysis.csv')
    # controls_path = os.path.join(current_dir, '..', 'data', 'DWS_Pheno.csv')

    engine = create_db_engine()
    # data_processor = DataProcessor(varieties_path, controls_path)
    data_processor = DataProcessor(engine)
    data_processor.load_data()
    data_processor.process_data()

    ui = UI(data_processor)
    #ui.set_page_config()
    ui.display_title("产量与株高关系图_2024")
    ui.display_filters()
    ui.display_charts()
