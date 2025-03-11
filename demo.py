'''
Description: 
Author: zhangweilong
Date: 2025-02-25 11:48:29
LastEditTime: 2025-03-11 10:37:08
LastEditors: zhangweilong
'''
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

from city_code import city_data# 导入 city_code 模块

# 配置 Chrome 为无头模式
chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--disable-gpu')

# 设置 ChromeDriver 路径
chromedriver = "./chromedriver-win64/chromedriver.exe" 

# 创建 ChromeDriver 服务
service = webdriver.ChromeService(executable_path=chromedriver)
# 创建 Chrome 浏览器实例，并指定 ChromeDriver 路径
driver = webdriver.Chrome(options=chrome_options,service=service)

try:
    # 打开相关城市的天气页面
    city_code = city_data["上海"]["上海"]["上海"]["AREAID"] # 上海 看city.js文件 101020100
    url = f'https://www.weather.com.cn/weather1d/{city_code}.shtml'
    driver.get(url)

    # 设置浏览器窗口大小
    driver.set_window_size(2400, 800)

    # 等待一段时间，确保页面完全加载，这里设置为 5 秒
    import time
    time.sleep(5)

    # 截取页面截图
    screenshot_path = 'weather_screenshot.png'
    driver.save_screenshot(screenshot_path)
    res = driver.execute_script("return dataSK;")
    print(res)

except Exception as e:
    print(f'发生错误: {e}')

finally:
    # 关闭浏览器
    driver.quit()