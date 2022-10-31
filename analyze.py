import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.pyplot import legend

def init_df():
    trade_df = pd.read_csv(FILE, index_col = 0)
    trade_df["order time"] = pd.to_datetime(trade_df["order time"], format="%Y-%m-%d %H:%M:%S")
    trade_df["end time"] = pd.to_datetime(trade_df["end time"], format="%Y-%m-%d %H:%M:%S")

    trade_df = trade_df.loc[trade_df["end time"] >= pd.to_datetime(START, format="%Y-%m-%d")]
    trade_df = trade_df.loc[trade_df["end time"] <= pd.to_datetime(END, format="%Y-%m-%d")]
    return trade_df
 
def get_continuous_drawdown(df, by_times=True):
    info = {"start":None, "end":None, "start_index":None, "end_index":None,"max_time":0, "value":1 * float("inf"), "ratio": 1 * float("inf")}
    pos = 0

    while pos < df.shape[0]:
        if df["profit"].iloc[pos] < 0:
            cur = pos
            times = 0
            value = 0
            ratio = 0
            while cur < df.shape[0] and df["profit"].iloc[cur] < 0:
                times += 1
                value += df["profit"].iloc[cur]
                ratio += df["profit rate"].iloc[cur]
                cur += 1
            
            if by_times and times >= info["max_time"]:
                info["max_time"] = times
                info["value"] = value
                info["ratio"] = ratio*100
                info["start"] = df["order time"].iloc[pos]
                info["end"] = df["end time"].iloc[cur-1]
                info["start_index"] = pos
                info["end_index"] = cur-1
            elif not by_times and value < info["value"]:
                info["max_time"] = times
                info["value"] = value
                info["ratio"] = ratio*100
                info["start"] = df["order time"].iloc[pos]
                info["end"] = df["end time"].iloc[cur-1]
                info["start_index"] = pos
                info["end_index"] = cur-1
            pos = cur
            continue
        pos += 1

    return info
  
def get_sharpe_sortino(df, stable=0.0367):
    start = df["order time"].iloc[0]
    daily_df = pd.DataFrame(-1,columns=["balance", "profit rate"], index=pd.date_range(start=START, end=END),dtype="float")
    daily_df["balance"].iloc[0] = 1000000
    daily_df["profit rate"].iloc[0] = 0
    daily_df_pos = 0
    df_pos = 0

    while df_pos < df.shape[0] and daily_df_pos < daily_df.shape[0]:
        if df["end time"].iloc[df_pos] - daily_df.index[daily_df_pos] <= pd.Timedelta(days=1):
            daily_df["balance"].iloc[daily_df_pos] = df["balance"].iloc[df_pos]
        else:
            if daily_df["balance"].iloc[daily_df_pos] == -1:
                daily_df["balance"].iloc[daily_df_pos] = daily_df["balance"].iloc[daily_df_pos-1]
                daily_df["profit rate"].iloc[daily_df_pos] = 0
            daily_df_pos += 1
            continue
        if daily_df_pos > 0:
            daily_df["profit rate"].iloc[daily_df_pos] = (daily_df["balance"].iloc[daily_df_pos] - daily_df["balance"].iloc[daily_df_pos-1])/daily_df["balance"].iloc[daily_df_pos]

        df_pos += 1
    while daily_df["balance"].iloc[-1] == -1:
        daily_df.drop(daily_df.index[-1], inplace=True)
    
    daily_stable = stable/365
    mean_profit_rate = daily_df["profit rate"].mean()
    std_profit_rate = daily_df["profit rate"].std()
    sharpe_rate = (mean_profit_rate-daily_stable)/std_profit_rate
    std_loss_only = daily_df["profit rate"].loc[daily_df["profit rate"]<0].std()
    sortino_rate =  (mean_profit_rate-daily_stable)/std_loss_only
    return sharpe_rate, sortino_rate

def get_max_drawdown(df):
    info = {"start":None, "end":None, "start_index":None, "end_index":None, "top":None, "bottom": None, "max_drawdown": float("inf"), "max_drawdown_percent": None}
    cur_top = [0,None]
    cur_bottom = [float("inf"), None]
    for i in range(df.shape[0]):
        if df["balance"].iloc[i] > cur_top[0]:
            cur_top = [df["balance"].iloc[i], i]
            cur_bottom =  [df["balance"].iloc[i], i]
        else:
            if df["balance"].iloc[i] < cur_bottom[0]:
                cur_bottom =  [df["balance"].iloc[i], i]
                if cur_bottom[0] - cur_top[0] < info["max_drawdown"]:
                    info["start"] = df["order time"].iloc[cur_top[1]]
                    info["end"] = df["end time"].iloc[cur_bottom[1]]
                    info["top"] = cur_top[0]
                    info["bottom"] = cur_bottom[0]
                    info["max_drawdown"] = cur_bottom[0] - cur_top[0]
                    info["start_index"] = cur_top[1]
                    info["end_index"] = cur_bottom[1]
                    info["max_drawdown_percent"] = (cur_bottom[0]-cur_top[0])/cur_top[0] *100
    return info

def main():
    trade_df = init_df()
    gross_profit = trade_df["profit"][trade_df["profit"]>0].sum()
    gross_loss = trade_df["profit"][trade_df["profit"]<0].sum()
    TRX_fee = trade_df["TRX fee"].sum()
    net_profit = gross_profit + gross_loss - TRX_fee
    return_on_account_percent = net_profit/1000000 * 100
    profit_factor = gross_profit/gross_loss
    max_drawdown_one = trade_df["profit"].min()
    max_drawdown_one_percent = trade_df["profit rate"].min() * 100
    continuous_drawdown_times = get_continuous_drawdown(trade_df)
    continuous_drawdown_value = get_continuous_drawdown(trade_df, by_times=False)
    max_drawdown = get_max_drawdown(trade_df)
    numbers_of_profit_TRX = trade_df["profit"][trade_df["profit"]>0].shape[0]
    numbers_of_loss_TRX = trade_df["profit"][trade_df["profit"]<0].shape[0]
    sharpe, sortino = get_sharpe_sortino(trade_df)

    print(f"File Name: {FILE}")
    print(f"Time: {START}-{END}")
    print(f"Amount of Trade: {trade_df.shape[0]}")
    print(f"Amount of win Trade: {numbers_of_profit_TRX}")
    print(f"Amount of loss trade: {numbers_of_loss_TRX}")
    print(f"Gross profit: {gross_profit}")
    print(f"Gross loss: {gross_loss}")
    print(f"TRX Fee: {TRX_fee}")
    print(f"Net Profit: {net_profit}")
    print(f"Net Profit(%): {return_on_account_percent}")
    print(f"Sharpe Ratio: {sharpe}")
    print(f"Sortino Ratio: {sortino}")
    print(f"Max Loss (single Trade): {max_drawdown_one}")
    print(f"Max Loss(single Trade) (%): {max_drawdown_one_percent}")
    print(f"Max Continuous Draw Down(Times):\n"+
          f"\t Start: {continuous_drawdown_times['start']}\n"+
          f"\t End: {continuous_drawdown_times['end']}\n"+
          f"\t Times: {continuous_drawdown_times['max_time']}\n"+
          f"\t Loss: {continuous_drawdown_times['value']}\n"+
          f"\t Loss(%): {continuous_drawdown_times['ratio']}"   
      )
    print(f"Max Continuous Draw Down(Loss):\n"+
          f"\t Start: {continuous_drawdown_value['start']}\n"+
          f"\t End: {continuous_drawdown_value['end']}\n"+
          f"\t Loss: {continuous_drawdown_value['value']}\n"+
          f"\t Loss(%): {continuous_drawdown_value['ratio']}"   
      )
    print(f"Max Draw Down:\n"+
          f"\t Start: {max_drawdown['start']}\n"+
          f"\t End: {max_drawdown['end']}\n"+
          f"\t Top: {max_drawdown['top']}\n"+
          f"\t Bottom: {max_drawdown['bottom']}\n"+
          f"\t Loss: {max_drawdown['max_drawdown']}\n"+
          f"\t Loss(%): {max_drawdown['max_drawdown_percent']}"   
      )
    print("\n\n\n")
    print("RED: Start point of max draw down")
    print("BLUE: End point of max draw down")
    fig,ax = plt.subplots(figsize=[12,7])
    # make a plot
    ax.plot(trade_df["end time"],trade_df["balance"],
            color="green", label="balance")
    # set x-axis label
    ax.set_xlabel("Date", fontsize = 14)
    # set y-axis label
    ax.set_ylabel("USDT",
                  color="green",
                  fontsize=14)
    ax.plot(max_drawdown["start"],max_drawdown["top"], 'ro', label=max_drawdown["top"])
    ax.plot(max_drawdown["end"], max_drawdown["bottom"], 'bo', label=max_drawdown["bottom"]) 
    # twin object for two different y-axis on the sample plot
    ax2=ax.twinx()
    # make a plot with different y-axis using second axis object
    ax2.plot(trade_df["end time"], trade_df["cross price"],color="red", label="BTC price")
    ax2.set_ylabel("BTC price",color="red",fontsize=14)
    fig.legend()
    plt.show()

FILE = input("File Path: ")
START = input("Start: ")
END = input("End: ")
print("\n\n\n")
main()
