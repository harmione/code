# 绘制Location和AOA标记的地图
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
        self.data_df = self.__get_data_df_from_database()
        self.data_df = self.__filter_data_df()

    def __get_data_df_from_database(self):
        conn = st.connection("postgres")
        data_df = conn.query(f'select * from "{self.table_schema}"."{self.table_name}" where "Longitude" is not null '
                             f'and "Latitude" is not null')
        return data_df

    def __filter_data_df(self):
        data_df = self.data_df[pd.notna(self.data_df["Longitude"]) & pd.notna(self.data_df["Latitude"])]
        return data_df

    def get_bookPrj_list(self, year):
        bookPrj_list = pd.unique(self.data_df.query(f"Year == {year}")["BookPrj"])
        return bookPrj_list


class BookPrjTable:
    def __init__(self, table_schema, table_name):
        self.table_schema = table_schema
        self.table_name = table_name
        self.data_df = self.__get_data_df_from_database()

    def __get_data_df_from_database(self):
        conn = st.connection("postgres")
        data_df = conn.query(f'select * from "{self.table_schema}"."{self.table_name}"')
        data_df["SelfCNPrjName"] = data_df["SelfCNPrjName"] + "站"
        return data_df

    def get_bookPrj_data_df(self, year):
        self.data_df = self.data_df.sort_values(by="Latitude", ascending=False)
        bookPrj_data_df = self.data_df.query(f"Year == {year} and BookPrj != 'MB'")
        return bookPrj_data_df


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
    def __init__(self, geoData: GeoData, locationInformationTable: LocationInformationTable,
                 bookPrjTable: BookPrjTable):
        self.geoData = geoData
        self.locationInformationTable = locationInformationTable
        self.bookPrjTable = bookPrjTable
        self.data_df = self.locationInformationTable.data_df

    def __change_cnprjname_list_to_bookprj_name_list(self, cnprjname_list):
        cnprjname_to_bookprj_name_dict = {}
        for index, row in self.bookPrjTable.data_df[["BookPrj", "CNPrjName"]].iterrows():
            bookprj, cnprj_name = row["BookPrj"], row["CNPrjName"]
            if cnprj_name not in cnprjname_to_bookprj_name_dict.keys():
                cnprjname_to_bookprj_name_dict[cnprj_name] = bookprj
        bookprj_name_list = [cnprjname_to_bookprj_name_dict[cnprjname] for cnprjname in cnprjname_list]
        return bookprj_name_list

    def __side_bar_layout(self):
        col1, col2, col3, col4 = st.columns([1, 1, 1, 6])
        with col1:
            select_fig_class = st.selectbox(
                '选择图表类别',
                ["育种站和测试点", "育种站", "测试点"]
            )
        with col2:
            is_show_province_name = st.selectbox(
                '是否显示省份名称',
                ["是", "否"]
            )
        with col3:
            select_year = st.selectbox(
                '选择年份'
                , sorted(self.data_df['Year'].dropna().unique().astype(int), reverse=True)
            )
        cnprjname_list = self.bookPrjTable.get_bookPrj_data_df(select_year)["CNPrjName"]
        with col4:
            select_cnprjname_list = st.multiselect(
                '选择育种站'
                , cnprjname_list
                , default=[item for item in cnprjname_list if item in ['北安','哈尔滨','长春','沈阳','太原']]
            )
        select_bookprj_list = self.__change_cnprjname_list_to_bookprj_name_list(cnprjname_list=select_cnprjname_list)
        return select_fig_class, select_year, select_bookprj_list, is_show_province_name

    def __get_mapbox_plot_layer(self, fig):
        fig.add_trace(go.Choroplethmapbox(
            featureidkey="properties.name",
            geojson=self.geoData.geofile_data_dict,
            locations=self.geoData.country_town_name_list,
            z=np.zeros(len(self.geoData.country_town_name_list)),
            colorscale=[[0, 'rgb(255, 255, 255)'], [1, 'rgb(252, 255, 255)']],
            reversescale=False,
            showscale=False,
            hoverinfo='none'
        ))
        # add specific map layer
        # fig.add_trace(go.Choroplethmapbox(
        #     featureidkey='properties.name',
        #     geojson_backup=self.geoData.geofile_data_dict,
        #     reversescale=False
        # ))
        fig.update_layout(
            title="育种站及测试点分布",
            mapbox_style="white-bg",
            mapbox_zoom=3.9,
            mapbox_center={"lat": 37.32, "lon": 108.55}
        )
        return fig

    def __get_provice_annotation_layer(self, fig):
        # 地图中省份标注图
        for provice_name in self.geoData.country_town_name_to_coordinates_dict.keys():
            longitude, latitude = self.geoData.country_town_name_to_coordinates_dict[provice_name]
            fig.add_trace(go.Scattermapbox(
                lat=[latitude],  # Latitude data for Annotation 2
                lon=[longitude],  # Longitude data for Annotation 2
                mode='text',
                text=[provice_name],
                textfont=dict(
                    size=12,
                    color='rgba(0, 0, 0, 0.8)'  # Text color
                ),
                showlegend=False,  # Show legend for this trace
                hoverinfo='none'
                # name="注释测试"  # Legend title for Annotation 2
            ))
        return fig

    def __get_marker_name(self, temp_bookprj_data_df, data_df):
        if len(data_df) == 0:
            return f'{temp_bookprj_data_df["SelfCNPrjName"].tolist()[0]}''({0})'
        else:
            cn_entry_book_prj = temp_bookprj_data_df["SelfCNPrjName"].tolist()[0]
            book_name_num = len(data_df)
            marker_name = f'{cn_entry_book_prj}({book_name_num})'
            return marker_name

    def __get_scatter_plot_layer(self, fig, selected_fig_class, year, bookprj_list):
        color_list = px.colors.qualitative.D3 + px.colors.qualitative.Safe
        selected_data_df = self.data_df[(self.data_df['BookPrj'].isin(bookprj_list)) & (self.data_df['Year'] == year)]
        bookprj_data_df = self.bookPrjTable.get_bookPrj_data_df(year)
        for index, entryBookPrj in enumerate(bookprj_list):
            temp_bookprj_data_df = bookprj_data_df[bookprj_data_df['BookPrj'] == entryBookPrj]
            location_data_df = selected_data_df[selected_data_df['BookPrj'] == entryBookPrj]
            if "育种站" in selected_fig_class and "测试点" not in selected_fig_class:
                fig.add_trace(go.Scattermapbox(
                    lat=temp_bookprj_data_df['Latitude'],  # Latitude data
                    lon=temp_bookprj_data_df["Longitude"],  # Longitude data
                    mode='markers',
                    marker={"opacity": 1.0
                            , "size": 16
                            , "symbol": 'circle'
                            , 'color': color_list[index]},
                    text=temp_bookprj_data_df["SelfCNPrjName"],  # 在鼠标悬停时显示 EntryBookPrj 的内容
                    hoverinfo='text',  # 确保显示悬浮信息
                    hoverlabel=dict(
                        font_size=30  # 设置悬浮标签字体大小
                    ),
                    name=self.__get_marker_name(temp_bookprj_data_df, location_data_df),
                    showlegend=True
                ))
            if "育种站" in selected_fig_class and "测试点" in selected_fig_class:
                is_show_legend = True if len(location_data_df) == 0 else False
                fig.add_trace(go.Scattermapbox(
                    lat=temp_bookprj_data_df['Latitude'],  # Latitude data
                    lon=temp_bookprj_data_df["Longitude"],  # Longitude data
                    mode='markers',
                    marker={"opacity": 0.5
                        , "size": 25
                        , "symbol": 'circle'
                        , 'color': color_list[index]},
                    text=temp_bookprj_data_df["SelfCNPrjName"],  # 在鼠标悬停时显示 EntryBookPrj 的内容
                    hoverinfo='text',  # 确保显示悬浮信息
                    hoverlabel=dict(
                        font_size=30  # 设置悬浮标签字体大小
                    ),
                    name=self.__get_marker_name(temp_bookprj_data_df, location_data_df),
                    showlegend=is_show_legend
                ))
            if "测试点" in selected_fig_class:
                fig.add_trace(go.Scattermapbox(
                    lat=location_data_df['Latitude'],  # Latitude data
                    lon=location_data_df["Longitude"],  # Longitude data
                    mode='markers',
                    marker={"opacity": 0.7
                        , "size": 12
                        , "symbol": 'circle'
                        , 'color': color_list[index]},
                    text=location_data_df["Location"],  # 在鼠标悬停时显示 EntryBookPrj 的内容
                    hoverinfo='text',  # 确保显示悬浮信息
                    hoverlabel=dict(
                        font_size=30  # 设置悬浮标签字体大小
                    ),
                    name=self.__get_marker_name(temp_bookprj_data_df, location_data_df),
                    showlegend=True
                ))
            # if len(location_data_df) > 0:
            #     fig.add_trace(go.Scattermapbox(
            #         lat=special_data_df['Latitude'],  # Latitude data
            #         lon=special_data_df['Longitude'],  # Longitude data
            #         mode='markers',
            #         marker={"opacity": 0.7
            #                 , "size": 25
            #                 , "symbol": 'circle'
            #                 , 'color': color_list[index]
            #                 # , 'color': 'red'
            #                 },
            #         text=special_data_df["LocationSelf"],  # 在鼠标悬停时显示 EntryBookPrj 的内容
            #         hoverinfo='text',  # 确保显示悬浮信息
            #         hoverlabel=dict(
            #             font_size=30  # 设置悬浮标签字体大小
            #         ),
            #         name=entryBookPrj,
            #         showlegend=False
            #     ))
            # else:
            #     fig.add_trace(go.Scattermapbox(
            #         lat=special_data_df['Latitude'],  # Latitude data
            #         lon=special_data_df['Longitude'],  # Longitude data
            #         mode='markers',
            #         marker={"opacity": 0.7
            #             , "size": 25
            #             , "symbol": 'circle'
            #             , 'color': color_list[index]
            #                 # , 'color': 'red'
            #                 },
            #         text=special_data_df["LocationSelf"],  # 在鼠标悬停时显示 EntryBookPrj 的内容
            #         hoverinfo='text',  # 确保显示悬浮信息
            #         hoverlabel=dict(
            #             font_size=30  # 设置悬浮标签字体大小
            #         ),
            #         name=self.__get_marker_name(special_data_df),
            #         showlegend=True
            #     ))
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

    def __get_sub_tilte(self, data_df: pd.DataFrame, selected_year, selected_type):
        sub_title = f''
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

    def map_plot(self):
        self.__get_title("育种站及测试点分布")
        selected_fig_class, selected_year, selected_bookprj_list, is_show_province_name = self.__side_bar_layout()
        fig = go.Figure()
        fig = self.__get_mapbox_plot_layer(fig)
        if is_show_province_name == "是":
            fig = self.__get_provice_annotation_layer(fig)
        fig = self.__get_scatter_plot_layer(fig, selected_fig_class=selected_fig_class, year=selected_year,
                                            bookprj_list=selected_bookprj_list)
        fig.update_layout(
            width=2000,
            height=1000
        )
        return fig


if __name__ == '__main__':
    st.set_page_config(layout='wide')
    locationInformationTable = LocationInformationTable(table_schema='DWS', table_name='LocationInformationOri')
    bookPrjTable = BookPrjTable(table_schema='DWS', table_name='BookPrjLocation')
    mapPlot = MapPlot(GeoData(), locationInformationTable, bookPrjTable)
    st.plotly_chart(mapPlot.map_plot())
    st.markdown("""
                ##### 注释：
                - 地图：
                    - 每个点表示一个测试点；
                    - 相同颜色的测试点，表示所属相同的育种站；
                    - 较大的点表示育种站所在位置。
                """)
