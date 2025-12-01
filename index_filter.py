"""
指数分类筛选模块
支持上证指数50、沪深300、中证500、中证1000等指数的成分股筛选
"""

import pandas as pd

# 指数代码映射
INDEX_CODES = {
    "上证50": "000016.SH",
    "沪深300": "000300.SH",
    "中证500": "000905.SH",
    "中证1000": "000852.SH"
}

def get_available_indexes():
    """获取可用的指数列表"""
    return list(INDEX_CODES.keys())

def get_index_code(index_name):
    """根据指数名称获取指数代码"""
    return INDEX_CODES.get(index_name)

def is_valid_index(index_name):
    """检查指数名称是否有效"""
    return index_name in INDEX_CODES

def get_index_constituents(fetcher, index_codes):
    """
    获取指定指数的成分股列表

    Args:
        fetcher: StockDataFetcher实例，用于调用Tushare API
        index_codes: 指数代码列表

    Returns:
        pandas DataFrame，包含指数成分股信息
    """
    if not index_codes:
        return pd.DataFrame()

    constituents_list = []

    for index_code in index_codes:
        try:
            # 获取指数成分股
            df = fetcher.pro.index_weight(index_code=index_code, trade_date='')
            if not df.empty:
                # 添加指数名称列
                df['index_code'] = index_code
                constituents_list.append(df)
        except Exception as e:
            print(f"获取指数{index_code}成分股失败: {e}")

    if constituents_list:
        # 合并所有指数成分股
        combined_df = pd.concat(constituents_list, ignore_index=True)
        # 只保留股票代码和指数代码列
        return combined_df[['con_code', 'index_code']].rename(columns={'con_code': 'ts_code'})

    return pd.DataFrame()

def filter_stocks_by_indexes(stock_list, index_constituents):
    """
    根据指数成分股筛选股票列表

    Args:
        stock_list: pandas DataFrame，包含股票列表数据，必须包含'ts_code'列
        index_constituents: pandas DataFrame，包含指数成分股信息，必须包含'ts_code'列

    Returns:
        pandas DataFrame，筛选后的股票列表
    """
    if index_constituents.empty or stock_list.empty:
        return stock_list

    # 提取所有指数成分股的股票代码
    index_stocks = set(index_constituents['ts_code'].unique())

    # 筛选属于指数成分股的股票
    return stock_list[stock_list['ts_code'].isin(index_stocks)]

def filter_stocks_by_index_names(fetcher, stock_list, index_names):
    """
    根据指数名称筛选股票列表（综合方法）

    Args:
        fetcher: StockDataFetcher实例
        stock_list: pandas DataFrame，股票列表数据
        index_names: 指数名称列表，或None/空列表表示不筛选

    Returns:
        pandas DataFrame，筛选后的股票列表
    """
    if not index_names:
        return stock_list

    # 验证指数名称有效性
    valid_index_names = [name for name in index_names if is_valid_index(name)]
    if not valid_index_names:
        print("没有有效的指数名称，跳过指数筛选")
        return stock_list

    # 获取指数代码
    index_codes = [get_index_code(name) for name in valid_index_names]

    # 获取指数成分股
    index_constituents = get_index_constituents(fetcher, index_codes)

    # 根据指数成分股筛选
    return filter_stocks_by_indexes(stock_list, index_constituents)

if __name__ == "__main__":
    # 测试功能
    print("可用指数列表：")
    for i, index_name in enumerate(get_available_indexes(), 1):
        print(f"{i:2d}. {index_name} ({INDEX_CODES[index_name]})")

    print(f"\n指数总数：{len(get_available_indexes())}")

    # 测试指数验证
    test_indexes = ["沪深300", "中证500", "不存在的指数"]
    for index in test_indexes:
        print(f"\n'{index}' 是否为有效指数：{is_valid_index(index)}")

    # 测试获取指数代码
    for index in test_indexes:
        code = get_index_code(index)
        print(f"'{index}' 的指数代码：{code}")
