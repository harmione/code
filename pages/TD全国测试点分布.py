# 绘制Location和AOA_SE标记的地图
import streamlit as st
import pandas as pd
import numpy as np
import json
import plotly.graph_objects as go
import plotly.express as px


class LocationInformationTable:
    """
    从数据库中获取到的所有数据
    """
    def __init__(self, table_schema, table_name):
        self.table_schema = table_schema
        self.table_name = table_name
        self.unique_AOA_SE_list = None
        self.data_df = self.__get_data_df_from_database()
        self.__get_unique_AOA_SE_list()

    def __get_data_df_from_database(self):
        conn = st.connection("postgres")
        data_df = conn.query(f'select * from "{self.table_schema}"."{self.table_name}"')
        return data_df

    def __get_unique_AOA_SE_list(self):
        self.unique_AOA_SE_list = pd.unique(self.data_df['AOA_SE']).tolist()
        return self.unique_AOA_SE_list


class GeoData:
    def __init__(self):
        self.geofile_path = 'data/geojson/中华人民共和国.json'
        self.geofile_data_dict = self.__get_geofile_content_dict()
        self.country_town_name_list = self.__get_country_town_name_list()
        self.country_town_name_to_coordinates_dict = self.__get_country_town_name_to_coordinates_dict()

    def __get_geofile_content_dict(self):
        with open(self.geofile_path, encoding='utf8') as f:
            geofile_data_dict = json.load(f)
            return geofile_data_dict

    def __get_country_town_name_list(self):
        country_town_name_list = []
        geofile_data_dict = self.__get_geofile_content_dict()
        for feature in geofile_data_dict['features']:
            country_town_name_list.append(feature['properties']['name'])
        return country_town_name_list

    def __get_country_town_name_to_coordinates_dict(self):
        country_town_name_to_coordinates_dict = {'北京市': [116.405285, 40.304989],
                                                 '天津市': [117.290182, 39.125596],
                                                 '河北省': [115.502461, 39.045474],
                                                 '山西省': [112.349248, 37.857014],
                                                 '内蒙古自治区': [110.570801, 41.318311],
                                                 '辽宁省': [123.429096, 41.596767],
                                                 '吉林省': [125.8245, 43.886841],
                                                 '黑龙江省': [127.942464, 46.756967],
                                                 '上海市': [121.472644, 31.031706],
                                                 '江苏省': [120.167413, 32.041544],
                                                 '浙江省': [120.053576, 29.287459],
                                                 '安徽省': [117.183042, 31.86119],
                                                 '福建省': [118.006239, 26.075302],
                                                 '江西省': [115.301378, 27.704858],
                                                 '山东省': [117.910884, 36.330537],
                                                 '河南省': [113.430888, 34.085237],
                                                 '湖北省': [112.298572, 30.984355],
                                                 '湖南省': [111.482279, 27.19409],
                                                 '广东省': [114.280637, 23.525178],
                                                 '广西壮族自治区': [108.920004, 23.82402],
                                                 '海南省': [109.63119, 19.031971],
                                                 '重庆市': [107.504962, 29.533155],
                                                 '四川省': [102.565735, 30.659462],
                                                 '贵州省': [106.813478, 26.578343],
                                                 '云南省': [101.712251, 24.440609],
                                                 '西藏自治区': [88.132212, 31.060361],
                                                 '陕西省': [108.548024, 34.263161],
                                                 '甘肃省': [96.123557, 40.058039],
                                                 '青海省': [96.278916, 35.423178],
                                                 '宁夏回族自治区': [106.278179, 37.16637],
                                                 '新疆维吾尔自治区': [85.617733, 40.992818],
                                                 '台湾省': [120.909062, 23.844332],
                                                 '香港特别行政区': [114.153355, 22.410048],
                                                 '澳门特别行政区': [113.56909, 22.158951]}
        return country_town_name_to_coordinates_dict



class MapPlot:
    def __init__(self, GeoData, locationInformationTable: LocationInformationTable):
        self.geoData = GeoData()
        self.locationInformationTable = locationInformationTable
        self.data_df = self.locationInformationTable.data_df
        self.unique_AOA_SE_list = self.locationInformationTable.unique_AOA_SE_list

    def __get_mapbox_plot_layer(self, fig):
        fig.add_trace(go.Choroplethmapbox(
            featureidkey="properties.name",
            geojson=self.geoData.geofile_data_dict,
            locations=self.geoData.country_town_name_list,
            z=np.zeros(len(self.geoData.country_town_name_list)),
            colorscale=[[0, 'rgb(255, 255, 255)'], [1, 'rgb(252, 255, 255)']],
            reversescale=False,
            showscale=False
        ))
        # add specific map layer
        # fig.add_trace(go.Choroplethmapbox(
        #     featureidkey='properties.name',
        #     geojson_backup=self.geoData.geofile_data_dict,
        #     reversescale=False
        # ))
        fig.update_layout(
            mapbox_style="white-bg",
            mapbox_zoom=3.9,
            mapbox_center={"lat": 37.32, "lon": 108.55}
        )
        return fig

    def __get_province_annotation_layer(self, fig):
        # 地图中省份标注图
        for province_name in self.geoData.country_town_name_to_coordinates_dict.keys():
            longitude, latitude = self.geoData.country_town_name_to_coordinates_dict[province_name]
            fig.add_trace(go.Scattermapbox(
                lat=[latitude],  # Latitude data for Annotation 2
                lon=[longitude],  # Longitude data for Annotation 2
                mode='text',
                text=[province_name],
                textfont=dict(
                    size=16,
                    color='rgb(0, 0, 0)'  # Text color
                ),
                showlegend=False,  # Show legend for this trace
                # name="注释测试"  # Legend title for Annotation 2
            ))
        return fig

    def __get_scatter_plot_layer(self, fig):
        color_scheme = px.colors.qualitative.Vivid  # 或其他推荐方案
        for index, AOA_SE in enumerate(self.unique_AOA_SE_list):
            selected_data_df = self.data_df[(self.data_df['AOA_SE'] == AOA_SE)]
            fig.add_trace(go.Scattermapbox(
                lat=selected_data_df["Latitude"],  # Latitude data
                lon=selected_data_df["Longitude"],  # Longitude data
                mode='markers',
                marker={"opacity": 0.7
                         , "size": 15
                         , "symbol": 'circle'
                        ,  'color': color_scheme[index % len(color_scheme)]
                        },
                text=selected_data_df["Location"],
                # marker_size=self.sampleData.sample_trait_value_series[increase_sample_index_array] / 40,
                name=AOA_SE,
                showlegend=True
            ))
        return fig

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

    def map_plot(self):
        self.__get_title("TD测试点和熟期分布")
        fig = go.Figure()
        # add map plot layer
        fig = self.__get_mapbox_plot_layer(fig)
        fig = self.__get_province_annotation_layer(fig)
        fig = self.__get_scatter_plot_layer(fig)
        fig.update_layout(
            width=2000,
            height=1200
        )
        return fig


#if __name__ == '__main__':
def main():
    #st.set_page_config(layout='wide')
    locationInformationTable = LocationInformationTable(table_schema='DWS', table_name='TDLocation2024')
    mapPlot = MapPlot(GeoData, locationInformationTable)
    st.plotly_chart(mapPlot.map_plot())
    st.markdown("""
                    ##### 注释：
                    - 地图：
                        - 每个点表示一个测试点；
                        - 相同颜色的测试点，表示所属相同的熟期；
                    """)
