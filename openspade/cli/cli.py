#!/usr/bin/env python3
import click
import sys
from typing import Optional
from openspade.gateway.binance_connector import BinanceConnector
from capital_pool import CapitalPool, GridStrategy, DCAStrategy
from tests.risk_manager import RiskManager, RiskConfig
from openspade.db.database_extension import init_capital_pool_tables
from openspade.messsage.notification import (
    NotificationManager,
    NotificationMessage,
    NotificationPriority
)


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """OpenSpade - Binance Futures Trading System CLI"""
    pass


@cli.group()
def binance():
    """Binance API 相关命令"""
    pass


@binance.command()
@click.option('--api-key', help='Binance API Key')
@click.option('--api-secret', help='Binance API Secret')
def balance(api_key: Optional[str], api_secret: Optional[str]):
    """查看账户余额"""
    connector = BinanceConnector(api_key=api_key, api_secret=api_secret)
    
    spot_balance = connector.get_spot_balance()
    futures_balance = connector.get_futures_balance()
    total = connector.get_total_assets()
    
    click.echo("=" * 50)
    click.echo("账户余额概览")
    click.echo("=" * 50)
    click.echo(f"现货账户 (USDT): {spot_balance:.2f}")
    click.echo(f"合约账户 (USDT): {futures_balance:.2f}")
    click.echo(f"总计 (USDT): {total:.2f}")
    click.echo("=" * 50)


@binance.command()
@click.option('--api-key', help='Binance API Key')
@click.option('--api-secret', help='Binance API Secret')
def positions(api_key: Optional[str], api_secret: Optional[str]):
    """查看当前持仓"""
    connector = BinanceConnector(api_key=api_key, api_secret=api_secret)
    positions = connector.get_positions()
    
    click.echo("=" * 80)
    click.echo("当前持仓")
    click.echo("=" * 80)
    
    has_position = False
    for pos in positions:
        pos_amt = float(pos.get('positionAmt', 0))
        if pos_amt != 0:
            has_position = True
            click.echo(f"交易对: {pos.get('symbol')}")
            click.echo(f"持仓数量: {pos_amt}")
            click.echo(f"未实现盈亏: {pos.get('unRealizedProfit')}")
            click.echo(f"持仓方向: {'多头' if pos_amt > 0 else '空头'}")
            click.echo("-" * 80)
    
    if not has_position:
        click.echo("当前无持仓")


@cli.group()
def capital():
    """资金池管理命令"""
    pass


@capital.command()
@click.argument('total', type=float)
def init(total: float):
    """初始化资金池
    
    TOTAL: 资金池总金额 (USDT)
    """
    pool = CapitalPool(total_assets=total)
    init_capital_pool_tables()
    
    click.echo("=" * 50)
    click.echo("资金池初始化成功")
    click.echo("=" * 50)
    click.echo(f"总资金: {pool.total_assets:.2f} USDT")
    click.echo(f"可用资金: {pool.available_funds:.2f} USDT")
    click.echo("=" * 50)


@capital.command()
@click.argument('strategy_id')
@click.argument('symbol')
@click.argument('amount', type=float)
@click.option('--grid-num', default=10, help='网格数量 (默认: 10)')
@click.option('--grid-range', default=0.10, help='价格区间百分比 (默认: 0.10)')
def grid(strategy_id: str, symbol: str, amount: float, grid_num: int, grid_range: float):
    """创建网格策略
    
    STRATEGY_ID: 策略ID
    SYMBOL: 交易对 (如 BTCUSDT)
    AMOUNT: 分配金额 (USDT)
    """
    pool = CapitalPool(total_assets=100000.0)
    
    strategy = GridStrategy(
        strategy_id=strategy_id,
        symbol=symbol,
        initial_amount=amount,
        grid_num=grid_num,
        grid_range=grid_range
    )
    
    if pool.allocate_funds(strategy, amount):
        click.echo("=" * 50)
        click.echo("网格策略创建成功")
        click.echo("=" * 50)
        click.echo(f"策略ID: {strategy_id}")
        click.echo(f"交易对: {symbol}")
        click.echo(f"分配金额: {amount:.2f} USDT")
        click.echo(f"网格数量: {grid_num}")
        click.echo(f"价格区间: {grid_range * 100:.1f}%")
        click.echo("=" * 50)
    else:
        click.echo("错误: 资金不足，无法分配策略资金", err=True)
        sys.exit(1)


@capital.command()
@click.argument('strategy_id')
@click.argument('symbol')
@click.argument('amount', type=float)
@click.option('--dca-interval', default=3600, help='DCA间隔秒数 (默认: 3600)')
@click.option('--dca-amount-ratio', default=0.1, help='每次DCA金额比例 (默认: 0.1)')
def dca(strategy_id: str, symbol: str, amount: float, dca_interval: int, dca_amount_ratio: float):
    """创建DCA策略
    
    STRATEGY_ID: 策略ID
    SYMBOL: 交易对 (如 BTCUSDT)
    AMOUNT: 分配金额 (USDT)
    """
    pool = CapitalPool(total_assets=100000.0)
    
    strategy = DCAStrategy(
        strategy_id=strategy_id,
        symbol=symbol,
        initial_amount=amount,
        dca_interval=dca_interval,
        dca_amount_ratio=dca_amount_ratio
    )
    
    if pool.allocate_funds(strategy, amount):
        click.echo("=" * 50)
        click.echo("DCA策略创建成功")
        click.echo("=" * 50)
        click.echo(f"策略ID: {strategy_id}")
        click.echo(f"交易对: {symbol}")
        click.echo(f"分配金额: {amount:.2f} USDT")
        click.echo(f"DCA间隔: {dca_interval}秒")
        click.echo(f"DCA金额比例: {dca_amount_ratio * 100:.1f}%")
        click.echo("=" * 50)
    else:
        click.echo("错误: 资金不足，无法分配策略资金", err=True)
        sys.exit(1)


@cli.group()
def risk():
    """风险管理命令"""
    pass


@risk.command()
@click.option('--max-position-ratio', default=0.8, help='最大持仓比例 (默认: 0.8)')
@click.option('--max-single-position-ratio', default=0.3, help='最大单品种持仓比例 (默认: 0.3)')
@click.option('--max-loss-per-strategy', default=0.15, help='单策略最大亏损比例 (默认: 0.15)')
@click.option('--max-drawdown', default=0.20, help='最大回撤比例 (默认: 0.20)')
def config(max_position_ratio: float, max_single_position_ratio: float, 
           max_loss_per_strategy: float, max_drawdown: float):
    """配置风险管理参数"""
    config = RiskConfig(
        max_position_ratio=max_position_ratio,
        max_single_position_ratio=max_single_position_ratio,
        max_loss_per_strategy=max_loss_per_strategy,
        max_drawdown=max_drawdown
    )
    
    click.echo("=" * 50)
    click.echo("风险管理配置")
    click.echo("=" * 50)
    click.echo(f"最大持仓比例: {config.max_position_ratio * 100:.1f}%")
    click.echo(f"最大单品种持仓比例: {config.max_single_position_ratio * 100:.1f}%")
    click.echo(f"单策略最大亏损比例: {config.max_loss_per_strategy * 100:.1f}%")
    click.echo(f"最大回撤比例: {config.max_drawdown * 100:.1f}%")
    click.echo("=" * 50)


@risk.command()
@click.argument('amount', type=float)
@click.argument('total', type=float)
@click.argument('current', type=float)
@click.option('--max-position-ratio', default=0.8, help='最大持仓比例 (默认: 0.8)')
def check(amount: float, total: float, current: float, max_position_ratio: float):
    """检查资金分配是否安全
    
    AMOUNT: 拟分配金额
    TOTAL: 总资金
    CURRENT: 当前已分配金额
    """
    config = RiskConfig(max_position_ratio=max_position_ratio)
    risk_manager = RiskManager(config)
    
    can_allocate = risk_manager.can_allocate(amount, total, current)
    safe_amount = risk_manager.get_safe_allocation(amount, total, current)
    
    click.echo("=" * 50)
    click.echo("风险检查结果")
    click.echo("=" * 50)
    click.echo(f"拟分配金额: {amount:.2f} USDT")
    click.echo(f"总资金: {total:.2f} USDT")
    click.echo(f"当前已分配: {current:.2f} USDT")
    click.echo(f"是否可分配: {'✅ 是' if can_allocate else '❌ 否'}")
    click.echo(f"安全分配金额: {safe_amount:.2f} USDT")
    click.echo("=" * 50)


@cli.group()
def notify():
    """通知管理命令"""
    pass


@notify.command()
@click.argument('title')
@click.argument('content')
@click.option('--priority', type=click.Choice(['low', 'normal', 'high', 'urgent']), 
              default='normal', help='通知优先级 (默认: normal)')
@click.option('--channel', type=click.Choice(['dingtalk', 'telegram', 'email', 'sms', 'voice']),
              help='指定通知渠道')
def send(title: str, content: str, priority: str, channel: Optional[str]):
    """发送测试通知
    
    TITLE: 通知标题
    CONTENT: 通知内容
    """
    priority_map = {
        'low': NotificationPriority.LOW,
        'normal': NotificationPriority.NORMAL,
        'high': NotificationPriority.HIGH,
        'urgent': NotificationPriority.URGENT
    }
    
    message = NotificationMessage(
        title=title,
        content=content,
        priority=priority_map[priority]
    )
    
    manager = NotificationManager()
    
    click.echo("=" * 50)
    click.echo("通知发送")
    click.echo("=" * 50)
    click.echo(f"标题: {title}")
    click.echo(f"内容: {content}")
    click.echo(f"优先级: {priority}")
    click.echo("-" * 50)
    click.echo("提示: 请配置通知渠道后再使用")
    click.echo("=" * 50)


@cli.command()
def info():
    """显示系统信息"""
    click.echo("=" * 50)
    click.echo("OpenSpade - Binance Futures Trading System")
    click.echo("=" * 50)
    click.echo("版本: 1.0.0")
    click.echo("作者: OpenSpade Team")
    click.echo("")
    click.echo("可用模块:")
    click.echo("  - binance: Binance API 接口")
    click.echo("  - capital: 资金池管理")
    click.echo("  - risk: 风险管理")
    click.echo("  - notify: 通知管理")
    click.echo("")
    click.echo("使用 'openspade --help' 查看更多帮助")
    click.echo("=" * 50)


if __name__ == '__main__':
    cli()
