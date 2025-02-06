import streamlit as st
import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import PatternFill
import tempfile
import os

def process_inventory_data(file_path):
    """ 处理库存数据 """
    xls = pd.ExcelFile(file_path)
    sheet_name = xls.sheet_names[0]  # 取第一个工作表
    df = pd.read_excel(file_path, sheet_name=sheet_name)

    # 使用第一行作为列名
    df.columns = df.iloc[0]
    df = df[1:].reset_index(drop=True)

    # 调整列名
    columns = df.columns.to_list()
    stl_count, pa_count = 0, 0
    for i in range(len(columns)):
        if columns[i] == "易捷快递:STL-Warehouse":
            stl_count += 1
            columns[i] = "易捷快递:STL-Warehouse-海外仓库存" if stl_count == 1 else "易捷快递:STL-Warehouse-海外仓在途库存"
        if columns[i] == "易捷快递:PA Warehouse":
            pa_count += 1
            columns[i] = "易捷快递:PA Warehouse-海外仓库存" if pa_count == 1 else "易捷快递:PA Warehouse-海外仓在途库存"
    df.columns = columns

    # 填充 NaN 值
    df = df.fillna(0)

    # 筛选符合条件的 SKU 组
    df_filtered = pd.DataFrame(columns=df.columns)
    unique_skus = df["SKU"].unique()
    for sku in unique_skus:
        sku_group = df[df["SKU"] == sku]

        # 筛选逻辑
        condition1 = (sku_group["FBA可用天数"] <= 20) & (sku_group["FBA可用天数"] > 0)
        condition2 = (sku_group["FBA可用+入库天数"] <= 40) & (sku_group["FBA可用+入库天数"] > 0)
        max_warehouse_stock = sku_group[["易捷快递:STL-Warehouse-海外仓库存", "易捷快递:PA Warehouse-海外仓库存"]].max(axis=1)
        max_sales_threshold = sku_group[["近7天日均销量", "近2天日均销量"]].max(axis=1) * 5
        condition3 = max_warehouse_stock > max_sales_threshold

        if any(condition1 | condition2) and any(condition3):
            df_filtered = pd.concat([df_filtered, sku_group, pd.DataFrame([[""] * len(df.columns)], columns=df.columns)], ignore_index=True)

    # 创建临时文件保存处理结果
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
    df_filtered.to_excel(temp_file.name, index=False)
    return temp_file.name

# Streamlit 页面配置
st.set_page_config(page_title="库存筛选工具", layout="wide")

st.title("📊 库存筛选自动化工具")
st.write("请上传 Excel 文件，系统将自动处理，并提供下载。")

# 上传文件
uploaded_file = st.file_uploader("📂 选择 Excel 文件", type=["xlsx"])

if uploaded_file is not None:
    st.success("📊 文件上传成功，正在处理数据...")
    processed_file_path = process_inventory_data(uploaded_file)

    # 提供下载按钮
    with open(processed_file_path, "rb") as file:
        st.download_button(label="📥 下载处理后的 Excel 文件", data=file, file_name="库存管理_筛选.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    # 删除临时文件
    os.remove(processed_file_path)

