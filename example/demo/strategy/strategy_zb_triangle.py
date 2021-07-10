# -*- coding:utf-8 -*-

# 策略实现

from aioquant import const
from aioquant.utils import logger
from aioquant.configure import config
from aioquant.market import Market
from aioquant.trade import Trade
from aioquant.const import BINANCE
from aioquant.order import Order
from aioquant.market import Orderbook, Asset
from aioquant.order import ORDER_ACTION_BUY, ORDER_ACTION_SELL, ORDER_STATUS_FAILED, ORDER_STATUS_CANCELED, ORDER_STATUS_FILLED
from aioquant.utils.decorator import async_method_locker
from aioquant.error import Error
from aioquant.platform import zb
from aioquant.tasks import SingleTask, LoopRunTask
import asyncio

negDirection = 1
posDirection = -1

commarket=[
            ('SHIB/QC', 'SHIB/USDT'),
            ('MATIC/QC', 'MATIC/USDT'),
            ('CELR/QC', 'CELR/USDT'),
            ('SOL/QC', 'SOL/USDT'),
            ('RSR/QC', 'RSR/USDT'),     
         ]
comsymbol= 'USDT/QC'
class MyStrategy:

    def __init__(self):
        """ 初始化
        """
        self.strategy = "zb_strategy"
        self.platform = config.accounts[0]["platform"]
        self.account = config.accounts[0]["account"]
        self.access_key = config.accounts[0]["access_key"]
        self.secret_key = config.accounts[0]["secret_key"]
        self.symbol = "EOS/QC"
        self.passphrase = config.accounts[0]["passphrase"]
        self.order_id = None  # 创建订单的id
        self.create_order_price = "0.0"  # 创建订单的价格
        self.rawsymbol = self.symbol.replace("/","").lower()
        self.trader={}
        self.orderbook={}
        self.market = {}
        self.erate = None
        self.asset = {}
        self.MaxposA_B = None
        self.MaxnegA_B = None
        self.orderId = None
        self.act_revok = False
        # 交易模块
        for i in range(0, len(commarket)):
            for j in range(0,2):             
                cc = {
                "strategy": self.strategy,
                "platform": self.platform,
                "symbol": commarket[i][j],
                "account": self.account,
                "access_key": self.access_key,
                "secret_key": self.secret_key,
                "passphrase": self.passphrase,
                "order_update_callback": self.on_event_order_update,
                "init_callback": self.on_init_callback,
                "error_callback": self.on_order_callback,
                "asset_update_callback": self.on_asset_update_callback
                }
                self.trader[commarket[i][j]] = Trade(**cc)
                ma = {
                            "strategy": self.strategy,
                            "platform": self.platform,
                            "symbol": commarket[i][j],
                            "market_type": "orderbook",     
                            "init_callback": self.on_market_init_callback,     
                            "update_callback": self.on_event_orderbook_update            
                        }
                self.market[commarket[i][j]]=Market(**ma)       
        
        self.buyflag = 0
        SingleTask.call_later(self.runfunc,5)        
        #请求行情
        #self.trader._t.request_market_by_websocket("orderbook")    
        # 订阅行情 
       # 市场模块
 

    @async_method_locker("MyStrategy.init_callback.locker")  
    async def on_init_callback(self, success: bool, **kwagrs):
        pass
    
    
    @async_method_locker("MyStrategy.on_event_orderbook_update.locker")  
    async def on_event_orderbook_update(self, orderbook: Orderbook):
        """ 订单薄更新
        """
        self.orderbook[orderbook.symbol]={'asks':orderbook.asks, 'bids':orderbook.bids}
        #logger.error("orderbook:", self.orderbook, caller=self)
        # 判断是否需要撤单
        """if self.order_id:
             if float(self.create_order_price) > float(bid3_price) or float(self.create_order_price) < float(bid4_price):
                 return
             logger.debug("revoke order:", self.order_id, caller=self)
             _, error = await self.trader.revoke_order(self.order_id)
             if error:

                 logger.error("revoke order error! error:", error, caller=self)
                 return
             self.order_id = None             
        else:
            # # 创建新订单
            price = (float(bid3_price) + float(bid4_price)) /2.0
            quantity = "1.5"  # 假设委托数量为0.1
            action = ORDER_ACTION_BUY     
            order_id, error = await self.trader.create_order(action, price, quantity)            
            if error:
                logger.error("create order error! error:", error, caller=self)
                return
            self.order_id = order_id
            self.create_order_price = price
        """           
    async def on_event_order_update(self, order: Order):
        """ 订单状态更新
        """
        #logger.debug("order id:", order, caller=self)
        if order.data["order_id"] == self.orderId and order.data["quantity"] > order.data["remain"]:
            Tradeamount = float(order.data["quantity"] - order.data["remain"])            
            symbolid=self.next_symbol.split("/")
            baseId = symbolid[0]
            quoteId = symbolid[1] 
            bseIdfreeamount=self.asset[baseId]['available']
            sellDepth=self.orderbook[self.next_symbol] 
            sellprice=sellDepth['bids'][2][0]
            jindu=1/float(self.market[self.next_symbol].marketSymbolconfig["minAmount"])
            if bseIdfreeamount < Tradeamount:
                sellamount = math.floor((bseIdfreeamount*jindu))/jindu
            if bseIdfreeamount >= Tradeamount:
                sellamount = Tradeamount
            action = ORDER_ACTION_SELL
            order_id, error = await self.trader[self.next_symbol].create_order(action, sellprice, sellamount)       
        #logger.debug("order id:", self.order_id, caller=self)



    async def on_order_callback(self, error: Error, **kwagrs):
        logger.debug("order error:", error, caller=self)


    async def on_asset_update_callback(self, asset:Asset, **kwagrs):        
        self.asset[asset.data["coins"]] = asset.data
        


    @async_method_locker("MyStrategy.market_init_callback.locker")  
    async def on_market_init_callback(self, success: bool, **kwagrs): 
        logger.debug("inint market:", success, caller=self)  
    @async_method_locker("MyStrategy.calcutpricegap.locker")  
    async def calcutpricegap(self, *args, **kwargs): 
       
        if self.erate == None:
            logger.debug("Erate is none:", self.erate, caller=self)
            return 
        if self.orderId != None:
            _, error = await self.trader[self.oldsymbol].revoke_order(self.orderId)
            logger.debug("only revoke orderid:", self.orderId,"oldsymbol",self.oldsymbol,"error",error,caller=self)                
            self.act_revok = True
            self.orderId = None
            await asyncio.sleep(0.5)
        for i in range(0, len(commarket)):
            Maxpospercent = 0
            Maxnegpercent = 0
            Asymbol=commarket[i][0]
            Bsymbol=commarket[i][1]
            if Asymbol not in self.orderbook or Bsymbol not in self.orderbook:
                continue
            Adepth=self.orderbook[Asymbol]            
            Bdepth=self.orderbook[Bsymbol]            

            A_B=self.get_ABsymbol_dprice(Asymbol, Adepth, Bsymbol, Bdepth, self.erate)

            if A_B['A_B_price']>=0:                
                if A_B['A_B_percent']>=Maxpospercent:
                    Maxpospercent=A_B['A_B_percent']
                    self.MaxposA_B=(Asymbol,Bsymbol,A_B['A_B_price'],A_B['A_B_percent'])
            if A_B['A_B_price']<=0:    
                if A_B['A_B_percent']>=Maxnegpercent: 
                    Maxnegpercent=A_B['A_B_percent']
                    self.MaxnegA_B=(Asymbol,Bsymbol,A_B['A_B_price'],A_B['A_B_percent'])
        
                
        #logger.debug('MaxposA_B', self.MaxposA_B, 'MaxnegA_B', self.MaxnegA_B, caller=self)
        if self.asset["QC"]['available'] == None or self.asset["USDT"]['available'] == None:
            logger.debug("QC or USDT is Noe:", self.asset, caller=self)
            return         
        flag=3
       
        if float(self.asset["QC"]['available']) >= float(self.asset["USDT"]['available'])*self.erate*float(10.0):
            flag=1
        if float(self.asset["QC"]['available'])*float(10.0) <= float(self.asset["USDT"]['available'])*self.erate:
            flag=0
        if Maxpospercent >0.01 or Maxnegpercent >0.01:
            logger.debug('MaxposA_B',self.MaxposA_B,caller=self)
            logger.debug('MaxnegA_B',self.MaxnegA_B,caller=self) 
            logger.debug("QC",self.asset["QC"]['available'],"USDT",self.asset["USDT"]['available'],"flag",flag,'Erate:',self.erate)
        if (Maxnegpercent>=Maxpospercent and Maxnegpercent>=0.01) and flag != 0:
            await self.DirectionTrans(self.MaxnegA_B,negDirection)
            return
        if (Maxnegpercent<Maxpospercent and Maxpospercent>=0.01) and flag != 1:
            await self.DirectionTrans(self.MaxposA_B,posDirection)
            return
       
    def get_ABsymbol_dprice(self, Asymbol, Adepth, Bsymbol, Bdepth, Erate):        
        A_B={}
        if Bdepth['bids']!=None and Adepth['bids']!=None:
            avrAprice=(Adepth['bids'][0][0]+Adepth['bids'][1][0]+Adepth['bids'][2][0]+Adepth['bids'][3][0])/4
            avrBprice=(Bdepth['bids'][0][0]+Bdepth['bids'][1][0]+Bdepth['bids'][2][0]+Bdepth['bids'][3][0])/4
            A_B_price=avrAprice-avrBprice*Erate
            if avrAprice == 0:
                A_B_percent=0
            else:
                A_B_percent=abs(A_B_price)/avrAprice
            A_B['Asymbol']=Asymbol
            A_B['Bsymbol']=Bsymbol
            A_B['A_B_price']=A_B_price
            A_B['A_B_percent']=A_B_percent            
        return A_B
    async def UpdateErate(self, *args, **kwargs):
        self._rest_api = zb.ZbRestAPI(self.access_key, self.secret_key)
        sucess, error = await self._rest_api.get_orderbook(symbol="USDT/QC")
        self.erate = float(sucess['bids'][0][0])
       
    async def hearbeat(self, *args, **kwargs):
        logger.debug('still alive',caller=self)
    async def runfunc(self, *args, **kwargs):
        LoopRunTask.register(self.calcutpricegap, 3)
        LoopRunTask.register(self.UpdateErate, 30)
        #LoopRunTask.register(self.hearbeat, 1800)

    async def DirectionTrans(self,MaxA_B,dirction):
         
        if dirction == negDirection:
            Asymbol = MaxA_B[0]
            Bsymbol = MaxA_B[1]
        if dirction == posDirection:
            Asymbol = MaxA_B[1]
            Bsymbol = MaxA_B[0]
      
        Asymbolid=Asymbol.split("/")
        baseId = Asymbolid[0]
        quoteId = Asymbolid[1] 
    
        AbseIdfreeamount=float(self.asset[baseId]['available'])        
        AquoteIdfreeamount=float(self.asset[quoteId]['available'])       
        newMaxposdepth=self.orderbook[Asymbol]        

        pricelimt = 1/(float(self.market[Asymbol].marketSymbolconfig["priceScale"])**10)
        amountlimt = float(self.market[Asymbol].marketSymbolconfig["minAmount"])
        buyprice=float(newMaxposdepth['bids'][0][0])+ pricelimt
        amount=(AquoteIdfreeamount-1)/buyprice   
          
        if amount>10.0*amountlimt and self.orderId == None:
            self.buyprice = buyprice
            action = ORDER_ACTION_BUY
            order_id, error = await self.trader[Asymbol].create_order(action, buyprice, amount)
            self.orderId = order_id
            logger.debug("creat orderid:", order_id,"Symbol:",Asymbol,"buyprice:",buyprice,"amount:",amount,caller=self)
            self.oldsymbol = Asymbol
            self.next_symbol = Bsymbol
            self.act_revok = False
            return
