
## AIOQuant

`AIOQuant` 是一套使用 `Python` 语言开发的 `异步事件驱动` 的 `量化交易 ` / `做市` 系统，它被设计为适应中高频策略的交易系统，
底层封装了操作系统的 `aio*库` 实现异步事件循环，业务层封装了 `RabbitMQ消息队列` 实现异步事件驱动，再加上 `Python` 语言的简单易用，
它非常适用于数字货币的高频策略和做市策略开发。

`AIOQuant` 同时也被设计为一套完全解耦的量化交易系统，其主要模块包括 `行情系统模块`、`资产系统模块`、`交易系统模块`、`风控系统模块`、`存储系统模块`，
各个模块都可以任意拆卸和组合使用，甚至采用不同的开发语言设计重构，模块之间通过 `RabbitMQ消息队列` 相互驱动，所以不同模块还可以部署在不同的进程，
或不同服务器。

`AIOQuant` 提供了简单而强大的功能：
- 基于 [Python Asyncio](https://docs.python.org/3/library/asyncio.html) 原生异步事件循环，处理更简洁，效率更高；
- 跨平台（Windows、Mac、Linux），可任意私有化部署；
- 任意交易所的交易方式（现货、合约）统一，相同策略只需要区别不同配置，即可无缝切换任意交易所；
- 所有交易所的行情统一，并通过事件订阅的形式，回调触发策略执行不同指令；
- 支持任意多个策略协同运行；
- 支持任意多个策略分布式运行；
- 毫秒级延迟（一般瓶颈在网络延迟）；
- 提供任务、监控、存储、事件发布等一系列高级功能；
- 定制化Docker容器，分布式配置、部署运行；
- 量化交易Web管理系统，通过管理工具，轻松实现对策略、风控、资产、服务器等进程或资源的动态管理；

- `AIOQuant` 交易系统各大模块
![](./docs/images/aioq_framework2.png)

- `AIOQuant` 分布式管理交易系统
![](./docs/images/aioq_framework.jpg)


### 框架依赖

- 运行环境
	- python 3.5.3 或以上版本(建议安装3.6版本)

- 依赖python三方包
	- aiohttp>=3.2.1
	- aioamqp>=0.13.0(可选)
	- motor>=2.0.0 (可选)

- RabbitMQ服务器
    - 事件发布、订阅

- MongoDB数据库(可选)
    - 数据存储


### 安装
使用 `pip` 可以简单方便安装:
```text
pip install aioquant
```


### Demo使用示例

- 推荐创建如下结构的文件及文件夹:
```text
ProjectName
    |----- docs
    |       |----- README.md
    |----- scripts
    |       |----- run.sh
    |----- config.json
    |----- src
    |       |----- main.py
    |       |----- strategy
    |               |----- strategy1.py
    |               |----- strategy2.py
    |               |----- ...
    |----- .gitignore
    |----- README.md
```

- 快速体验 [Demo](example/demo) 示例


- 运行
```text
python src/main.py config.json
```


### 推荐课程
[第1期 高频交易介绍](https://www.bilibili.com/video/BV1EJ41197Fx/)  
[第2期 一分钟上手，开启自己的第一笔程序化交易](https://www.bilibili.com/video/BV1vJ411q799/)  
[第3期 利用REST API拉取行情数据](https://www.bilibili.com/video/BV15J411B7bG/)  
[第4期 使用实时行情动态挂单](https://www.bilibili.com/video/BV1JJ411i7hH/)  
[第5期 API报错 & 订单成交](https://www.bilibili.com/video/BV1nJ411y7zE/)  
[第6期 优雅的处理未完成订单](https://www.bilibili.com/video/BV1nJ411175f/)  
[第7期 配置文件](https://www.bilibili.com/video/BV1ZJ411k71z/)  
[第8期 日志打印](https://www.bilibili.com/video/BV1FJ411C7Ys/)  
[第9期 服务心跳 & 协程任务](https://www.bilibili.com/video/BV1pJ411C7dS/)  
[第10期 Order订单模块](https://www.bilibili.com/video/BV1UJ411C7a6/)  
[第11期 Trade交易模块](https://www.bilibili.com/video/BV1sJ411r73X/)  
[第12期 并发 & 锁](https://www.bilibili.com/video/BV1iJ411677Q/)  
[第13期 Market行情模块 & 行情服务器](https://www.bilibili.com/video/av79695611/)  
[第14期 Position合约持仓模块](https://www.bilibili.com/video/av84079197/)  
[第15期 现货搬砖套利原理](https://www.bilibili.com/video/av86045742/)  
[第16期 分析历史行情数据](https://www.bilibili.com/video/av86060852/)  
[第17期 现货搬砖套利策略编写](https://www.bilibili.com/video/av86493743/)  
[第18期 行情数据存储](https://www.bilibili.com/video/av88433058/)  
[第19期 推送钉钉消息](https://www.bilibili.com/video/av88463345/)  
[第20期 Bollinger Bands 布林带策略](https://www.bilibili.com/video/av91044647/)  
[第21期 一个简单的做市商策略](https://www.bilibili.com/video/av93027310/)  
[第22期 火币永续合约REST API模块](https://www.bilibili.com/video/BV1k5411t7bb/)  
[第23期 火币永续合约Trade模块](https://www.bilibili.com/video/BV1GV411Z766/)  
[第24期 Market行情系统升级](https://www.bilibili.com/video/BV1rk4y1R7gk/)  
[第25期 现货-合约无风险套利](https://www.bilibili.com/video/BV15A411b78b/)  
[第26期 合约的无风险套利](https://www.bilibili.com/video/BV1AK4y1k7un/)  
[第27期 高阶技巧 - 运行时更新](https://www.bilibili.com/video/BV1Xe411p7Pm/)  
[第28期 Triangular Arbitrage 三角套利原理](https://www.bilibili.com/video/BV1WZ4y1W77F/)  
[第29期 Triangular Arbitrage 三角套利策略编写](https://www.bilibili.com/video/BV1zz411i7xW/)  
[第30期 高效的交易方式](https://www.bilibili.com/video/BV1Ai4y1x7Z3/)  
[第31期 高阶技巧 - ClientOrderId的用法](https://www.bilibili.com/video/BV1dA411v72d/)  
[第32期 高阶技巧 - 订单类型的高级用法](https://www.bilibili.com/video/BV12K411n7GC/)  
[第33期 Trade模块的强大功能让你的策略如虎添翼](https://www.bilibili.com/video/BV1WZ4y1u7KF)  
[第34期 AIOQuant到底有何不同？](https://www.bilibili.com/video/BV17t4y1X74P/)  
[第35期 搭建本地量化策略研发环境](https://www.bilibili.com/video/BV1w54y1B7ZH/)  


### 有任何问题，欢迎联系

- 微信二维码
<p>
  <img src ="https://open-space.ifclover.com/wx_qrcode.jpeg" align="middle" width="250" height="250"/>
</p>
