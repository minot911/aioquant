# -*- coding:utf-8 -*-

"""
Market module.

Author: HuangTao
Date:   2019/02/16
Email:  huangtao@ifclover.com
"""

import json

from aioquant import const
from aioquant.utils import logger
from aioquant.tasks import SingleTask
import importlib

class Orderbook:
    """Orderbook object.

    Args:
        platform: Exchange platform name, e.g. `binance` / `bitmex`.
        symbol: Trade pair name, e.g. `ETH/BTC`.
        asks: Asks list, e.g. `[[price, quantity], [...], ...]`
        bids: Bids list, e.g. `[[price, quantity], [...], ...]`
        timestamp: Update time, millisecond.
    """

    def __init__(self, platform=None, symbol=None, asks=None, bids=None, timestamp=None):
        """Initialize."""
        self.platform = platform
        self.symbol = symbol
        self.asks = asks
        self.bids = bids
        self.timestamp = timestamp

    @property
    def data(self):
        d = {
            "platform": self.platform,
            "symbol": self.symbol,
            "asks": self.asks,
            "bids": self.bids,
            "timestamp": self.timestamp
        }
        return d

    @property
    def smart(self):
        d = {
            "p": self.platform,
            "s": self.symbol,
            "a": self.asks,
            "b": self.bids,
            "t": self.timestamp
        }
        return d

    def load_smart(self, d):
        self.platform = d["p"]
        self.symbol = d["s"]
        self.asks = d["a"]
        self.bids = d["b"]
        self.timestamp = d["t"]
        return self

    def __str__(self):
        info = json.dumps(self.data)
        return info

    def __repr__(self):
        return str(self)


class Trade:
    """Trade object.

    Args:
        platform: Exchange platform name, e.g. `binance` / `bitmex`.
        symbol: Trade pair name, e.g. `ETH/BTC`.
        action: Trade action, `BUY` / `SELL`.
        price: Order place price.
        quantity: Order place quantity.
        timestamp: Update time, millisecond.
    """

    def __init__(self, platform=None, symbol=None, action=None, price=None, quantity=None, timestamp=None):
        """Initialize."""
        self.platform = platform
        self.symbol = symbol
        self.action = action
        self.price = price
        self.quantity = quantity
        self.timestamp = timestamp

    @property
    def data(self):
        d = {
            "platform": self.platform,
            "symbol": self.symbol,
            "action": self.action,
            "price": self.price,
            "quantity": self.quantity,
            "timestamp": self.timestamp
        }
        return d

    @property
    def smart(self):
        d = {
            "p": self.platform,
            "s": self.symbol,
            "a": self.action,
            "P": self.price,
            "q": self.quantity,
            "t": self.timestamp
        }
        return d

    def load_smart(self, d):
        self.platform = d["p"]
        self.symbol = d["s"]
        self.action = d["a"]
        self.price = d["P"]
        self.quantity = d["q"]
        self.timestamp = d["t"]
        return self

    def __str__(self):
        info = json.dumps(self.data)
        return info

    def __repr__(self):
        return str(self)


class Kline:
    """Kline object.

    Args:
        platform: Exchange platform name, e.g. `binance` / `bitmex`.
        symbol: Trade pair name, e.g. `ETH/BTC`.
        open: Open price.
        high: Highest price.
        low: Lowest price.
        close: Close price.
        volume: Total trade volume.
        timestamp: Update time, millisecond.
        kline_type: Kline type name, `kline`, `kline_5min`, `kline_15min` ... and so on.
    """

    def __init__(self, platform=None, symbol=None, open=None, high=None, low=None, close=None, volume=None,
                 timestamp=None, kline_type=None):
        """Initialize."""
        self.platform = platform
        self.symbol = symbol
        self.open = open
        self.high = high
        self.low = low
        self.close = close
        self.volume = volume
        self.timestamp = timestamp
        self.kline_type = kline_type

    @property
    def data(self):
        d = {
            "platform": self.platform,
            "symbol": self.symbol,
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume,
            "timestamp": self.timestamp,
            "kline_type": self.kline_type
        }
        return d

    @property
    def smart(self):
        d = {
            "p": self.platform,
            "s": self.symbol,
            "o": self.open,
            "h": self.high,
            "l": self.low,
            "c": self.close,
            "v": self.volume,
            "t": self.timestamp,
            "kt": self.kline_type
        }
        return d

    def load_smart(self, d):
        self.platform = d["p"]
        self.symbol = d["s"]
        self.open = d["o"]
        self.high = d["h"]
        self.low = d["l"]
        self.close = d["c"]
        self.volume = d["v"]
        self.timestamp = d["t"]
        self.kline_type = d["kt"]
        return self

    def __str__(self):
        info = json.dumps(self.data)
        return info

    def __repr__(self):
        return str(self)


class Market:
    """Subscribe Market.

    Args:
        market_type: Market data type,
            MARKET_TYPE_TRADE = "trade"
            MARKET_TYPE_ORDERBOOK = "orderbook"
            MARKET_TYPE_KLINE = "kline"
            MARKET_TYPE_KLINE_5M = "kline_5m"
            MARKET_TYPE_KLINE_15M = "kline_15m"
        platform: Exchange platform name, e.g. `binance` / `bitmex`.
        symbol: Trade pair name, e.g. `ETH/BTC`.
        callback: Asynchronous callback function for market data update.
                e.g. async def on_event_kline_update(kline: Kline):
                        pass
    """

    def __init__(self, **kwargs):
        """Initialize."""

        market_type = kwargs["market_type"]
        platform = kwargs["platform"]
        symbol = kwargs["symbol"]
        callback = kwargs["update_callback"]
        if platform == "#" or symbol == "#":
            multi = True
        else:  
            multi = False         
        if market_type == const.MARKET_TYPE_ORDERBOOK:
            from aioquant.event import EventOrderbook            
            EventOrderbook(Orderbook(platform, symbol)).subscribe(callback, multi)
        elif market_type == const.MARKET_TYPE_TRADE:
            from aioquant.event import EventTrade
            EventTrade(Trade(platform, symbol)).subscribe(callback, multi)
        elif market_type in [
            const.MARKET_TYPE_KLINE, const.MARKET_TYPE_KLINE_3M, const.MARKET_TYPE_KLINE_5M,
            const.MARKET_TYPE_KLINE_15M, const.MARKET_TYPE_KLINE_30M, const.MARKET_TYPE_KLINE_1H,
            const.MARKET_TYPE_KLINE_3H, const.MARKET_TYPE_KLINE_6H, const.MARKET_TYPE_KLINE_12H,
            const.MARKET_TYPE_KLINE_1D, const.MARKET_TYPE_KLINE_3D, const.MARKET_TYPE_KLINE_1W,
            const.MARKET_TYPE_KLINE_15D, const.MARKET_TYPE_KLINE_1MON, const.MARKET_TYPE_KLINE_1Y]:
            from aioquant.event import EventKline
            EventKline(Kline(platform, symbol, kline_type=market_type)).subscribe(callback, multi)
        else:
            logger.error("market_type error:", market_type, caller=self)
            return
        SingleTask.run(self.marketreqweb,**kwargs)        
    async def marketreqweb(self,**kwargs):
        """req market data .

        Args:
            typechannel: "trade", "orderbook",  "kline" 

        No Returns:
            success: If execute successfully, return success information, otherwise it's None.
            error: If execute failed, return error information, otherwise it's None.
        """
        # 生产对应交易所的Market对象
        typechannel = kwargs["market_type"]
        platform = kwargs["platform"]
        #导入对应交易所的模块
        ExchangeModel=importlib.import_module("aioquant.platform.{}".format(platform.lower()))
        MarketClassName=platform.capitalize() + 'Market'
        #对象工厂，创建具体的交易市场对象
        MarketClass=getattr(ExchangeModel,MarketClassName)
        ExchangeMarket = MarketClass(**kwargs)
        await self.ExchangeMarket.request_market_by_websocket(typechannel)
        
        
        