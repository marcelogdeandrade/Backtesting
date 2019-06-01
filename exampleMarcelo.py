from backtesting import evaluateHist, evaluateIntr
from strategy import Strategy
from order import Order
from event import Event
import numpy as np

class RSI(Strategy):

  OVERBOUGHT = 65
  OVERSOLD = 40
  SIZE = 5

  def __init__(self):
    self.prices = []
    self.last_price = 0
    self.rs = []
    self.signal = 0

  def _get_rs(self):
    slice_prices = self.prices
    if len(self.prices) > self.SIZE:
      slice_prices = self.prices[-self.SIZE:]
    highs = []
    lows = []
    for i in range(1, len(slice_prices)):
      ret = slice_prices[i]
      if slice_prices[i] > slice_prices[i - 1]:
        highs.append(ret)
      else:
        lows.append(ret)
    avg_high = sum(highs) / len(slice_prices) if len(slice_prices) else 0
    avg_low = sum(lows) / len(slice_prices) if len(slice_prices) else 1
    return avg_high / avg_low if avg_low else 0

  def _calculate_rsi(self):
    rs = self._get_rs()
    rsi = 100 - 100 /(1 + rs)
    return rsi

  def push(self, event):
    orders = []
    price = event.price[3]
    self.prices.append(price)
    if len(self.prices) > 0:
      rsi = self._calculate_rsi()
      if rsi >= self.OVERBOUGHT:
        if self.signal == 1:
          orders.append(Order(event.instrument, -1, 0))
          orders.append(Order(event.instrument, -1, 0))
        if self.signal == 0:
          orders.append(Order(event.instrument, -1, 0))
        self.signal = -1
      elif rsi <= self.OVERSOLD:
        if self.signal == -1:
          orders.append(Order(event.instrument, 1, 0))
          orders.append(Order(event.instrument, 1, 0))
        if self.signal == 0:
          orders.append(Order(event.instrument, 1, 0))
        self.signal = 1
    return orders

class MarketMaker(Strategy):
  def __init__(self):
    self.cur_petr3 = None
    self.cur_usd = None
    self.buy_order_id = None
    self.sell_order_id = None
    self.spread = 100

  def _calc_pbr(self):
    ti = 1.01815
    tf = -0.32019
    f = 2
    pbr = ((self.cur_petr3 * f) / self.cur_usd) * ti + tf
    return pbr

  def push(self, event):
    orders = []
    if event.instrument == "PETR3":
      self.cur_petr3 = event.price[3]
    if event.instrument == "USDBRL":
      self.cur_usd = event.price[3]
    if self.cur_petr3 and self.cur_usd:
      pbr = self._calc_pbr()
      if self.buy_order_id:
        self.cancel(self.id, self.buy_order_id)
      if self.sell_order_id:
        self.cancel(self.id, self.sell_order_id)
      order_buy = Order("PBR", 1, pbr - self.spread)
      self.buy_order_id = order_buy.id
      order_sell = Order("PBR", -1, pbr + self.spread)
      self.sell_order_id = order_sell.id
      orders.append(order_buy)
      orders.append(order_sell)
      return orders
    return []

  def fill(self, instrument, price, quantity, status):
    super().fill(instrument, price, quantity, status)
    orders = []
    if quantity == 1:
      orders.append(Order("PETR3", -1, 0))
      orders.append(Order("USDBRL", 1, 0))
    elif quantity == -1:
      orders.append(Order("PETR3", 1, 0))
      orders.append(Order("USDBRL", -1, 0))
    return orders

class MarceloStrategy(Strategy):
  def __init__(self):
    self.signal = 0
    self.max_count = 7
    self.count_buy = 0
    self.count_sell = 0
    self.prev = None

  def _update_counts(self, price):
    if price > self.prev:
      self.count_sell += 1
      self.count_buy = 0
    else:
      self.count_buy += 1
      self.count_sell = 0

  def _create_buy_order(self, event):
    orders = []
    self.count_buy = 0
    if self.signal == -1:
      orders.append(Order(event.instrument, 1, 0))
      orders.append(Order(event.instrument, 1, 0))
    self.signal = 1
    return orders

  def _create_sell_order(self, event):
    orders = []
    self.count_sell = 0
    if self.signal == 1:
      orders.append(Order(event.instrument, -1, 0))
      orders.append(Order(event.instrument, -1, 0))
    self.signal = -1
    return orders

  def push(self, event):
    orders = []
    price = event.price[3]
    if self.prev:
      self._update_counts(price)
    if self.count_buy == self.max_count:
      orders = self._create_buy_order(event)
    if self.count_sell == self.max_count:
      orders = self._create_sell_order(event)
    self.prev = price
    return orders

print(evaluateHist(RSI(), {'IBOV':'^BVSP.csv'}))
print(evaluateHist(MarceloStrategy(), {'IBOV':'^BVSP.csv'}))
print(evaluateIntr(MarketMaker(), {'USDBRL':'USDBRL.csv', 'PETR3':'PETR3.csv', 'PBR': None }))
