import streamlit as st
import numpy as np
import pandas as pd
import json
import plotly.graph_objects as go
import os
import glob
import pickle

# 缓存函数机制
def cache_warper(file_name,func, *args, **kwargs):
    cache_combined_geofile_path = os.path.join('data', f'{file_name}.pickle') # 缓存文件路径,放在 data 文件夹下
    res = None    # 用于存储函数结果
    # 检查缓存文件是否存在
    if os.path.exists(cache_combined_geofile_path):
        with open(cache_combined_geofile_path, 'rb') as f:
            res = pickle.load(f)    # 将缓存内容读取到res
            print("load from cache!")
        return res
    else:
        print("load from disk!")
        res = func(*args, **kwargs)
        with open(cache_combined_geofile_path, 'wb') as f:
            pickle.dump(res, f)    # 将结果res序列化保存到文件中
    return res

# 缓存函数示例：从文件夹读取区县级别GeoJSON数据并合并
@st.cache_data    #Streamlit内置缓存装饰器，用于缓存函数返回值，避免重复计算
def load_district_geojson(district_geofiles_folder: str):   # 只要输入参数 district_geofiles_folder 不变，函数结果会从缓存中读取。
    combined_features = []
    geojson_files = glob.glob(os.path.join(district_geofiles_folder, '*.json'))

    for file in geojson_files:
        with open(file, encoding='utf8') as f:
            geofile = json.load(f)
            if geofile.get('type') == 'FeatureCollection':
                if 'features' in geofile:
                    combined_features.extend(geofile['features'])
                else:
                    st.warning(f"文件 {file} 中缺少 'features' 键。")
            elif geofile.get('type') == 'Feature':
                combined_features.append(geofile)
            else:
                st.warning(f"文件 {file} 的类型为 {geofile.get('type')}，未识别。")

    combined_geofile = {
        "type": "FeatureCollection",
        "features": combined_features
    }

    return combined_geofile

# 缓存函数示例：读取省级GeoJSON数据
@st.cache_data
def load_province_geojson(province_geofile_path: str):
    with open(province_geofile_path, encoding='utf8') as f:
        geofile = json.load(f)
        if geofile.get('type') == 'FeatureCollection':
            if 'features' in geofile:
                return geofile
            else:
                st.warning(f"文件 {province_geofile_path} 中缺少 'features' 键。")
                return {
                    "type": "FeatureCollection",
                    "features": []
                }
        elif geofile.get('type') == 'Feature':
            return {
                "type": "FeatureCollection",
                "features": [geofile]
            }
        else:
            st.warning(f"文件 {province_geofile_path} 的类型为 {geofile.get('type')}，未识别。")
            return {
                "type": "FeatureCollection",
                "features": []
            }


class SamplesData:
    """
    从数据库中获取到的所有数据
    """
    def __init__(self, table_schema, table_name, aoa_se_selected=None):
        self.table_schema = table_schema
        self.table_name = table_name
        self.data_df = self.__get_data_df_from_database()
        self.aoa_se_series = pd.unique(self.data_df['AOA_SE'])

        # 如果指定了 AOA_SE，则根据选择的 AOA_SE 过滤数据
        if aoa_se_selected is not None:
            if aoa_se_selected == "SUN+SUS":
                # 当用户选择合并熟期时，筛选出AOA_SE为SUN或SUS的数据
                self.data_df = self.data_df[self.data_df['AOA_SE'].isin(['SUN', 'SUS'])]
            else:
                # 否则按照单一熟期进行筛选
                self.data_df = self.data_df[self.data_df['AOA_SE'] == aoa_se_selected]
        self.sample_series, self.ck_series, self.location_series = self.__get_sample_and_ck_list()

    def __get_data_df_from_database(self):
        conn = st.connection("postgres")
        #通过 st.connection("postgres") 使用 secrets.toml 文件中配置的数据库凭据建立连接。
        query = f'''
       SELECT p.*, l."Latitude", l."Longitude", l."County"
            FROM "{self.table_schema}"."{self.table_name}" AS p
            JOIN "{self.table_schema}"."TDLocation2024" AS l
            ON p."Location" = l."Location"
        '''
        data_df = conn.query(query)
        return data_df

    def __get_sample_and_ck_list(self):
        data_df = self.data_df
        name_series = pd.unique(data_df["CName"])  # 获取所有唯一的品种名称
        sample_series = name_series  # 样本品种列表，包括所有品种
        ck_series = name_series      # 对照品种列表，包括所有品种
        location_series = pd.unique(data_df["Location"])  # 获取所有唯一地点的名称
        county_series = pd.unique(data_df["County"])
        return sample_series, ck_series, location_series


class SampleData:
    """
    单个样本数据
    """
    def __init__(self, sample, ck_sample, location_list, aoa_se_selected):
        self.sample = sample
        self.ck_sample = ck_sample
        self.location_list = location_list
        self.trait = "YLD14_TD"
        self.aoa_se_selected = aoa_se_selected
        self.data_df = self.__get_data_df()
        self.sample_data_df = self.__get_sample_data_df()

        self.ck_sample_data_df = None  # 初始化为空
        self.growth_compared_to_ck_array = None  # 初始化为空
        # 仅当 ck_sample 不为 None 时计算
        if self.ck_sample is not None:
            self.ck_sample_data_df = self.__get_ck_data_df()
            self.growth_compared_to_ck_array = self.__get_growth_compared_to_ck_array()

        self.sample_location_series = self.sample_data_df['Location']
        self.sample_county_series = self.sample_data_df['County']

        # 提取样本特征值并保留两位小数。
        self.sample_trait_value_series = np.round(self.sample_data_df[self.trait], 2)
        # 获取样本的经纬度数组
        self.sample_longitude_array, self.sample_latitude_array = self.__get_sample_longitude_and_latitude_array()

    def update_ck_sample(self, ck_sample):
        self.ck_sample = ck_sample
        self.ck_sample_data_df = self.__get_ck_data_df()
        self.growth_compared_to_ck_array = self.__get_growth_compared_to_ck_array()

    def __aggregate_duplicate_entries(self, data_df):
        # 定义需要计算平均值的数值列
        numeric_columns = ['YLD14_TD']  # 根据您的实际情况，添加其他需要计算均值的数值列

        # 定义需要保留的非数值列
        non_numeric_columns = ['Location', 'CName', 'AOA_SE', 'Latitude', 'Longitude','County']

        # 对数据按照 'Location' 和 'CName' 进行分组，计算数值列的均值，非数值列取第一条记录
        data_df = data_df.groupby(['Location', 'CName'], as_index=False).agg(
            {col: 'mean' for col in numeric_columns} |
            {col: 'first' for col in non_numeric_columns}
        )

        return data_df

    def __get_data_df(self):
        # 直接使用从 SamplesData 中获取的数据，避免重复读取
        data_df = SamplesData(
            table_schema='DWS', table_name='TDPheno2024',
            aoa_se_selected=self.aoa_se_selected  # 传入 aoa_se_selected
        ).data_df

        data_df = data_df[data_df["Location"].isin(self.location_list)]

        # 添加数据聚合步骤
        data_df = self.__aggregate_duplicate_entries(data_df)
        return data_df

    def __get_sample_data_df(self):
        sample_data_df = self.data_df[(self.data_df['CName'] == self.sample)]
        return sample_data_df

    def __get_ck_data_df(self):
        ck_data_df = self.data_df[self.data_df["CName"] == self.ck_sample]
        return ck_data_df

    def __get_growth_compared_to_ck_array(self):
        growth_compared_to_ck_list, trait = [], self.trait
        for index, sample in self.sample_data_df.iterrows():
            sample_location = sample['Location']
            # 获取对应地点的对照样本数据
            ck_sample_data_df = self.ck_sample_data_df[
                self.ck_sample_data_df['Location'] == sample_location
            ]
            sample_trait_value = sample[trait]
            if not ck_sample_data_df.empty:
                ck_sample_trait_value = ck_sample_data_df[trait].values[0]
                if ck_sample_trait_value != 0:
                    # 计算增长百分比
                    growth_percentage = round((sample_trait_value - ck_sample_trait_value) / ck_sample_trait_value * 100, 2)
                else:
                    growth_percentage = np.nan
                growth = growth_percentage
            else:
                # 如果对应地点没有对照数据，则标记为 NaN
                growth = np.nan
            growth_compared_to_ck_list.append(growth)
        return np.array(growth_compared_to_ck_list)

    def __get_sample_longitude_and_latitude_array(self):
        sample_longitude_array = self.sample_data_df['Longitude'].astype(float).values
        sample_latitude_array = self.sample_data_df['Latitude'].astype(float).values
        return sample_longitude_array, sample_latitude_array


class GeoData:
    def __init__(self):
        self.district_geofiles_folder = 'data/geojson/全国区县'
        # 使用缓存的函数加载区县和省级数据
        self.district_geofile_data_dict = cache_warper('ldg',load_district_geojson,self.district_geofiles_folder)
        self.district_town_name_list = self.__get_district_town_name_list()

        # 省级GeoJSON文件路径
        self.province_geofile_path = 'data/geojson/中华人民共和国_省.json'
        self.province_geofile_data_dict = cache_warper('lpg',load_province_geojson,self.province_geofile_path)
        self.province_town_name_list = self.__get_province_town_name_list()

    def __get_district_town_name_list(self):
        district_town_name_list = []
        for feature in self.district_geofile_data_dict['features']:
            if 'properties' in feature and 'name' in feature['properties']:
                district_town_name_list.append(feature['properties']['name'])
            else:
                st.warning("某个Feature缺少 'properties.name' 信息。")
        return district_town_name_list

    def __get_province_town_name_list(self):
        province_town_name_list = []
        for feature in self.province_geofile_data_dict['features']:
            if 'properties' in feature and 'name' in feature['properties']:
                province_town_name_list.append(feature['properties']['name'])
            else:
                st.warning("某个Feature缺少 'properties.name' 信息。")
        return province_town_name_list


class MapPlot:
    def __init__(self, sample, location_list,  aoa_se_selected, show_county, show_ratio):
        # self.sampleData = cache_warper('MP_ssd',SampleData,sample, None, location_list, aoa_se_selected)
        # 这里不能用同一份缓存，因为SampleData的参数不同
        self.sampleData = SampleData(sample, None, location_list, aoa_se_selected)
        self.geoData = GeoData()

        self.show_county = show_county
        self.show_ratio = show_ratio


    def __get_mapbox_plot_layer(self, fig):
        # 添加省级边界图层（深色线条，无填充）
        fig.add_trace(go.Choroplethmapbox(
            featureidkey="properties.name",
            geojson=self.geoData.province_geofile_data_dict,
            locations=self.geoData.province_town_name_list,
            z=np.zeros(len(self.geoData.province_town_name_list)),
            colorscale=[[0, 'rgba(0,0,0,0)'], [1, 'rgba(0,0,0,0)']],  # 透明填充
            marker_line_color='darkblue',  # 深色边界线
            marker_line_width=2,  # 边界线宽度
            showscale=False
        ))

        # 添加区县级边界图层（浅色线条，无填充）
        fig.add_trace(go.Choroplethmapbox(
            featureidkey="properties.name",
            geojson=self.geoData.district_geofile_data_dict,
            locations=self.geoData.district_town_name_list,
            z=np.zeros(len(self.geoData.district_town_name_list)),
            colorscale=[[0, 'rgba(0,0,0,0)'], [1, 'rgba(0,0,0,0)']],  # 透明填充
            marker_line_color='lightgray',  # 浅色边界线
            marker_line_width=0.5,  # 边界线宽度
            showscale=False
        ))

        # 添加区域上色层，用于展示样本的数值
        fig.add_trace(go.Choroplethmapbox(
            featureidkey='properties.name',
            geojson=self.geoData.district_geofile_data_dict,
            locations=self.sampleData.sample_location_series,
            z=self.sampleData.sample_trait_value_series,
            name=self.sampleData.trait,
            reversescale=False,
            showscale=False,
            colorscale='Viridis',
            marker_opacity=0.5,
            marker_line_width=0
        ))

        fig.update_layout(
            mapbox_style="white-bg",
            #mapbox_style="open-street-map",
            mapbox_zoom=5, # 缩放级别
            mapbox_center={"lat": 43, "lon": 122}
        )
        return fig

    def __get_scatter_plot_layer(self, fig):
        # 绘制散点图层
        growth_array = self.sampleData.growth_compared_to_ck_array
        # 注意处理 NaN 值
        valid_indices = ~np.isnan(growth_array)

        growth_array = growth_array[valid_indices]
        latitude_array = self.sampleData.sample_latitude_array[valid_indices]
        longitude_array = self.sampleData.sample_longitude_array[valid_indices]
        trait_value_array = self.sampleData.sample_trait_value_series.values[valid_indices]
        #location_array = self.sampleData.sample_location_series.values[valid_indices]
        county_array = self.sampleData.sample_county_series.values[valid_indices]

        increase_sample_index_array = growth_array > 2
        decrease_sample_index_array = growth_array < -2
        neutral_sample_index_array = (growth_array >= -2) & (growth_array <= 2)

        # print("增产点数量：", np.sum(increase_sample_index_array))
        # print("减产点数量：", np.sum(decrease_sample_index_array))
        # print("变化在±2%内点数量：", np.sum(neutral_sample_index_array))

        #设置点大小的上下限
        # 定义最大和最小增长比例
        max_growth = 20
        min_growth = -20

        # 限制增长比例在 ±20% 以内
        clamped_growth_array = np.clip(growth_array, min_growth, max_growth)

        # 定义点大小的最小值和最大值
        min_size = 5
        max_size = 20

        # 根据 clamped_growth_array 计算点大小
        # 0% 增长对应 min_size，20% 或 -20% 增长对应 max_size
        size_array = (np.abs(clamped_growth_array) / max_growth) * (max_size - min_size) + min_size

        # 根据show_county和show_ratio构建文本标注
        text_array = []
        for growth, county in zip(growth_array, county_array):
            text_parts = []
            if self.show_ratio:
                text_parts.append(f'{growth:+.2f}%')
            if self.show_county:
                text_parts.append(county)
            # 如果两个都不显示，则为空字符串
            text_item = ' '.join(text_parts) if text_parts else ''
            text_array.append(text_item)
        text_array = np.array(text_array)

        # 根据增产/减产/无显著变化分类
        text_increase = text_array[increase_sample_index_array]
        text_decrease = text_array[decrease_sample_index_array]
        text_neutral = text_array[neutral_sample_index_array]

        # 根据用户勾选情况决定模式
        # 如果 show_county 或 show_ratio 至少有一个为 True，则显示文本
        if self.show_county or self.show_ratio:
            # 标签直接显示在地图上
            mode = 'markers+text'
            textposition = 'top center'
        else:
            # 如果两个都不勾选，则不显示文本
            mode = 'markers'
            text_increase = None
            text_decrease = None
            text_neutral = None
            textposition = None


        # 有增加的点标注(增产 - 绿色）
        fig.add_trace(go.Scattermapbox(
            lat=latitude_array[increase_sample_index_array],
            lon=longitude_array[increase_sample_index_array],
            mode=mode,
            marker=dict(
                color='rgb(34, 139, 34)',  # 绿色
                opacity=1,  # 透明度
                size=size_array[increase_sample_index_array]  # 使用计算后的点大小
            ),
            text=text_increase,
            textposition=textposition,
            hoverinfo='text',
            hovertext=text_array[increase_sample_index_array],
            name="增产>2%",
            showlegend=True
        ))

        # 有降低的点标注(减产 - 红色）
        fig.add_trace(go.Scattermapbox(
            lat=latitude_array[decrease_sample_index_array],
            lon=longitude_array[decrease_sample_index_array],
            mode=mode,
            marker=dict(
                color='rgb(255, 0, 0)',  # 红色
                opacity=1,
                size=size_array[decrease_sample_index_array]  # 使用计算后的点大小
            ),
            text=text_decrease,
            textposition=textposition,
            hoverinfo='text',
            hovertext=text_array[decrease_sample_index_array],
            # marker_size=trait_value_array[decrease_sample_index_array] / 40,
            name="减产>2%",
            showlegend=True
        ))

        # 变化在 ±2% 内的点标注（黄色）
        fig.add_trace(go.Scattermapbox(
            lat=latitude_array[neutral_sample_index_array],
            lon=longitude_array[neutral_sample_index_array],
            mode=mode,
            marker=dict(
                color='rgb(255, 223, 0)',  # 黄色
                opacity=1,
                size=size_array[neutral_sample_index_array]  # 使用计算后的点大小
            ),
            text=text_neutral,
            textposition=textposition,
            hoverinfo='text',
            hovertext=text_array[neutral_sample_index_array],
            name="变化在 ±2% 内",
            showlegend=True,
            hoverlabel=dict(namelength=0),
        ))
        return fig

    def map_plot(self,ck_sample):
        self.sampleData.update_ck_sample(ck_sample)  # 更新对照品种并重新计算数据
        # 创建地图并添加所有图层，最终返回绘制好的 fig 图形。
        fig = go.Figure()
        # 添加地图图层
        fig = self.__get_mapbox_plot_layer(fig)
        # 添加散点图层
        fig = self.__get_scatter_plot_layer(fig)
        # 更新布局，设置三列布局下的地图大小
        fig.update_layout(
            width=500,
            height=600,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="center",
                x=0.5
            ),
            title={
                'text': f'{self.sampleData.sample}和{ck_sample}的产量对比',
                'y': 0.98,
                'x': 0.5,
                'xanchor': 'center',
                'yanchor': 'top',
                'font': dict(
                    size=20,
                    color='black'
                )
            }
        )

        return fig


class MapStreamlit:
    def __init__(self, table_schema='DWS', table_name='TDPheno2024'):
        # 首先实例化 SamplesData 获取 AOA_SE 列表
        self.samplesData = SamplesData(table_schema=table_schema, table_name=table_name)
        aoa_se_list = self.samplesData.aoa_se_series.tolist()

        # 获取用户选择的 AOA_SE，增加SUN+SUS选项
        aoa_se_selected = self.__get_aoa_se_selection(aoa_se_list)

        # 根据选择的 AOA_SE 重新实例化 SamplesData，过滤数据
        self.samplesData = SamplesData(table_schema=table_schema, table_name=table_name,
                                       aoa_se_selected=aoa_se_selected)


        sample_name, ck_names, location_list, show_county, show_ratio = self.__side_bar_layout()
        self.mapPlot = MapPlot(sample_name, location_list, aoa_se_selected, show_county, show_ratio)

        self.__body_layout(ck_names)

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
        st.markdown(f'<p class="custom-title">{title_content}</p>', unsafe_allow_html=True)

    def __get_aoa_se_selection(self, aoa_se_list):
        # 添加 AOA_SE 的单选框
        aoa_se_options = aoa_se_list + ["SUN+SUS"]  # 在原有的熟期列表基础上追加一个合并选项
        aoa_se_selected = st.sidebar.selectbox('AOA_SE熟期', aoa_se_options)
        return aoa_se_selected

    def __side_bar_layout(self):
        # 获取所有品种列表
        variety_list = self.samplesData.sample_series.tolist()
        # 选择品种
        sample_name = st.sidebar.selectbox(
            '品种',
            variety_list
        )
        # 从品种列表中移除已选择的品种，防止选择相同的品种作为对照
        ck_options = [variety for variety in variety_list if variety != sample_name]
        # 选择对照品种
        ck_names = st.sidebar.multiselect(
            '对照品种',
            ck_options,
            default=ck_options[:3]  # 默认选择前三个品种
        )

        # 地区选择
        location_list = self.samplesData.location_series.tolist()
        if st.sidebar.checkbox('手动选择地区'):
            location_list = st.sidebar.multiselect(
                '请输入需要展示的地区',
                location_list,
                default=location_list
            )
        # 增加图例显示选项
        show_county = st.sidebar.checkbox('显示地点(County)', value=True)
        show_ratio = st.sidebar.checkbox('显示比例(增长百分比)', value=True)

        return sample_name, ck_names, location_list, show_county, show_ratio

    def __body_layout(self, ck_names):
        self.__get_title(title_content="品种性状展示（地图）")
        # fig = self.mapPlot.map_plot(ck_sample=ck_names[0])  # 仅显示第一个对照品种的地图
        # st.plotly_chart(fig, use_container_width=True)

        # 动态生成地图图表并按三列显示
        with st.container():
            columns = st.columns(3)  # Set three columns in the layout
            for i, ck_name in enumerate(ck_names):
                col_index = i % 3
                with columns[col_index]:  # 放置每个对照品种地图
                    fig = self.mapPlot.map_plot(ck_sample=ck_name)
                    st.plotly_chart(fig, use_container_width=True)


if __name__ == '__main__':
    # 设置页面为宽屏
    st.set_page_config(layout='wide')
    # 运行 MapStreamlit 类
    mapStreamlit = MapStreamlit(table_schema='DWS', table_name='TDPheno2024')