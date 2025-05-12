import streamlit as st
st.set_page_config(layout='wide')
from pagess import (
diaplay,
TDd,
TDf,
TDfx,
TDzb,
cl,
water
)

# 定义边栏导航菜单选项
pages = {
    "R&D测试品种性状展示": diaplay,
    "TD_品种对比地图": TDd,
    "TD全国测试点分布":TDf,
    "TD分性状分析":TDfx,
    "TD性状总表分析":TDzb,
    "产量与株高关系图":cl,
    "产量与水分关系图":water

}

# 创建边栏导航菜单
selection = st.sidebar.radio("导航菜单", list(pages.keys()))

# 根据用户选择加载相应的页面内容
page = pages[selection]
page.main()