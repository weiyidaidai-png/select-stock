import pandas as pd
from stock_data import StockDataFetcher
from sw_industries import get_sw_industries, is_valid_industry

class StockAnalyzer:
    """股票分析器"""

    def __init__(self, fetcher=None):
        self.fetcher = fetcher or StockDataFetcher()

    def calculate_ma_diff(self, ts_code, long_period=20, short_period=5):
        """计算单只股票的均线差异"""
        try:
            # 获取最近足够多的数据
            days_needed = max(long_period, short_period) + 10  # 确保有足够数据计算均线
            df = self.fetcher.get_recent_data(ts_code, days_needed)

            # 自动跳过时间不足的股票
            if df.empty or len(df) < max(long_period, short_period):
                # print(f"跳过股票 {ts_code}: 数据不足 (需要 {max(long_period, short_period)} 天，实际 {len(df)} 天)")
                return None

            # 计算长期和短期移动平均线
            df['ma_long'] = df['close'].rolling(window=long_period).mean()
            df['ma_short'] = df['close'].rolling(window=short_period).mean()

            # 获取最新的均线值
            latest_data = df.iloc[-1]
            ma_long = latest_data['ma_long']
            ma_short = latest_data['ma_short']
            current_price = latest_data['close']

            # 避免除以零
            if ma_long == 0:
                return None

            # 计算短期均线与长期均线的差异百分比
            ma_diff_percent = ((ma_short - ma_long) / ma_long) * 100

            return {
                'ts_code': ts_code,
                'current_price': current_price,
                'ma_long': ma_long,
                'ma_short': ma_short,
                'ma_diff_percent': ma_diff_percent
            }
        except Exception as e:
            # print(f"分析股票{ts_code}失败: {e}")
            return None

    def analyze_stocks(self, stock_list=None, long_period=20, diff_threshold=5, short_period=5, pre_industries=None, pre_indexes=None):
        """
        批量分析股票，支持行业和指数预筛选

        Args:
            stock_list: 股票列表DataFrame，若为None则自动获取
            long_period: 长期均值周期（天）
            diff_threshold: 差异百分比阈值
            short_period: 短期均值周期（天）
            pre_industries: 行业预筛选列表，或None表示不筛选
            pre_indexes: 指数预筛选列表，或None表示不筛选

        Returns:
            pandas DataFrame，包含分析结果，增加行业字段
        """
        if stock_list is None:
            stock_list = self.fetcher.get_stock_list(pre_industries, pre_indexes)

        if stock_list.empty:
            return pd.DataFrame()

        results = []
        total = len(stock_list)
        
        print(f"开始分析 {total} 只股票...")

        for i, stock in stock_list.iterrows():
            ts_code = stock['ts_code']
            name = stock['name']
            industry = stock['industry']

            # 计算均线差异
            ma_diff_data = self.calculate_ma_diff(ts_code, long_period, short_period)

            if ma_diff_data and ma_diff_data['ma_diff_percent'] is not None:
                # 将行业信息添加到结果中
                ma_diff_data['name'] = name
                ma_diff_data['industry'] = industry
                results.append(ma_diff_data)

            # 打印进度
            progress = (i + 1) / total * 100
            if (i + 1) % 50 == 0 or (i + 1) == total:
                print(f"分析进度: {progress:.1f}% ({i + 1}/{total})")

        if not results:
            print("没有符合条件的股票")
            return pd.DataFrame()

        # 转换为DataFrame并按差异百分比排序
        result_df = pd.DataFrame(results)
        result_df = result_df.sort_values('ma_diff_percent', ascending=False)

        # 重置索引
        result_df = result_df.reset_index(drop=True)

        # 添加排名列
        result_df['rank'] = result_df.index + 1

        print(f"分析完成，共找到 {len(result_df)} 只符合条件的股票")
        return result_df

    def get_industry_statistics(self, analysis_result):
        """
        获取行业统计信息

        Args:
            analysis_result: 分析结果DataFrame

        Returns:
            pandas DataFrame，包含行业统计信息
        """
        if analysis_result.empty:
            return pd.DataFrame()

        # 按行业分组统计
        industry_stats = analysis_result.groupby('industry').agg(
            count=('ts_code', 'size'),
            avg_diff=('ma_diff_percent', 'mean'),
            max_diff=('ma_diff_percent', 'max'),
            min_diff=('ma_diff_percent', 'min')
        ).sort_values('count', ascending=False)

        # 重置索引
        industry_stats = industry_stats.reset_index()

        # 格式化数值
        industry_stats['avg_diff'] = industry_stats['avg_diff'].round(2)
        industry_stats['max_diff'] = industry_stats['max_diff'].round(2)
        industry_stats['min_diff'] = industry_stats['min_diff'].round(2)

        return industry_stats

    def filter_by_industries(self, analysis_result, industries):
        """
        根据行业筛选分析结果

        Args:
            analysis_result: 分析结果DataFrame
            industries: 行业名称列表

        Returns:
            pandas DataFrame，筛选后的分析结果
        """
        if analysis_result.empty or not industries:
            return analysis_result

        # 验证行业名称有效性
        valid_industries = [ind for ind in industries if is_valid_industry(ind)]
        
        if not valid_industries:
            print("没有有效的行业名称，返回全部结果")
            return analysis_result

        # 筛选指定行业的股票
        filtered_result = analysis_result[analysis_result['industry'].isin(valid_industries)]
        print(f"行业后筛选: 从 {len(analysis_result)} 只股票中筛选出 {len(filtered_result)} 只 ({', '.join(valid_industries)})")
        
        return filtered_result

if __name__ == "__main__":
    # 测试功能
    analyzer = StockAnalyzer()

    # 测试单只股票分析
    print("测试单只股票分析...")
    ma_diff = analyzer.calculate_ma_diff('000001.SZ')
    if ma_diff:
        print(f"股票 000001.SZ 分析结果:")
        print(f"当前价格: {ma_diff['current_price']:.2f}")
        print(f"20日均线: {ma_diff['ma_long']:.2f}")
        print(f"5日均线: {ma_diff['ma_short']:.2f}")
        print(f"差异百分比: {ma_diff['ma_diff_percent']:.2f}%")

    # 测试批量分析（只分析少量股票用于测试）
    print("\n测试批量分析...")
    try:
        # 获取少量股票进行测试
        stock_list = analyzer.fetcher.get_stock_list().head(10)
        result = analyzer.analyze_stocks(stock_list)
        print(f"分析结果: {len(result)} 只股票符合条件")
        
        if not result.empty:
            print("\n前5名股票:")
            print(result[['rank', 'name', 'ts_code', 'ma_diff_percent', 'industry']].head())
    except Exception as e:
        print(f"批量分析测试失败: {e}")
