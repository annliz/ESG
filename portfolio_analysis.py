import pandas as pd
from matplotlib import pyplot as plt

pd.options.display.max_rows = 999
pd.options.display.max_columns = 999

PRICE = 100
MAX_PRICE = 1500
ROUNDS = 5

CONST = 0

TOTAL_CAPACITY = 22050

BIDS = {
    "Big Coal": 160000,
    "Big Gas": 53000,
    "Bay Views": 210000,
    "Beachfront": 60000,
    "East Bay": 100000,
    "Old Timers": 650000,
    "Fossil Light": 832000
}

COLORS = {
    "Big Coal": "red",
    "Big Gas": "orange",
    "Bay Views": "olive",
    "Beachfront": "green",
    "East Bay": "cyan",
    "Old Timers": "blue",
    "Fossil Light": "purple"
}

def format_demands():
    df = pd.read_csv("Demand Forecasts.csv")
    df = df.set_index("Time")
    df = df.T
    # print(df)
    data = df.to_dict()
    return data

demands = format_demands()

def get_demand(day, price):
    m = demands[day]["Slope"]
    b = demands[day]["Intercept"]
    return b + price/m

def format_data():
    
    df = pd.read_csv("ESG clean.csv")
    # print(type(df["Fixed Cost"].iloc[3]))
    df = df.rename(columns={"Unnamed: 0": "Plant"})
    df = df.set_index("Plant")
    df = df.T
    # print(df)
    data = df.to_dict()
    # print(data)

    portfolios = {}
    for plant in data.keys():
        portfolio = data[plant]["Portfolio"]
        try:
            portfolios[portfolio][plant] = data[plant]
        except Exception as e:
            portfolios[portfolio] = {}
            portfolios[portfolio][plant] = data[plant]
    
    return portfolios

portfolios = format_data()
    
def get_full_capacity_profits(price):
    master_capacity = 0
    profits = {}
    marginal_profits = {}
    for portfolio in portfolios.keys():
        total_cost = 0
        total_capacity = 0
        for plant in portfolios[portfolio].keys():
            pl = portfolios[portfolio][plant]
            total_cost += (pl["Capacity"]*pl["Marginal Cost"] + pl["Fixed Cost"])
            total_capacity += pl["Capacity"]
        profit = price*total_capacity - total_cost
        profits[portfolio] = profit
        master_capacity += total_capacity
    
    sorted_profits = dict(sorted(profits.items(), key=lambda item: item[1]))

    print(master_capacity)

    # for p in sorted_profits.keys():
    #     print(p + " \t" + str(sorted_profits[p]))

    return sorted_profits

def plot_full_capacity_profits():
    all_profits = {}
    for p in portfolios.keys():
        all_profits[p] = []
    prices = []    
    for price in range(0,1500,50):
        prices.append(price)
        profits = get_full_capacity_profits(price)
        for p in profits.keys():
            all_profits[p].append(profits[p])
    for p in all_profits.keys():
        plt.plot(prices, all_profits[p], label=p)
    plt.legend()
    plt.show()
        
    return 0

def plot_full_game_projection():
    profits_lines = {}
    for p in portfolios:
        profits_lines[p] = []
    prices = []
    for price in range(0,1500,50):
        prices.append(price)
        for port in portfolios.keys():
            cost = 0
            revenue = 0
            for plant in portfolios[port].keys():
                pl = portfolios[port][plant]
                cost += pl["Fixed Cost"]*4
                for day in range(1,17):
                    cost += pl["Marginal Cost"]*pl["Capacity"]*get_demand(day, price)/TOTAL_CAPACITY
                revenue += pl["Capacity"]*price
            profit = revenue - cost - BIDS[port]
            profits_lines[port].append(profit)

    for p in profits_lines.keys():
        plt.plot(prices, profits_lines[p], label=p)
    plt.legend()
    plt.show()

def plot_supply_and_demand(hour):
    plants = []
    
    for port in portfolios.keys():
        for plant in portfolios[port].keys():
            p = {}
            pl = portfolios[port][plant]
            p["Capacity"] = pl["Capacity"]
            p["Price"] = pl["Marginal Cost"]
            p["Name"] = plant
            p["Portfolio"] = port
            plants.append(p)
    sorted_plants = sorted(plants, key=lambda d: d['Price'])
    print(sorted_plants)

    xstart = 0
    xend = 0
    for plant in sorted_plants:
        xend = xstart + plant["Capacity"]
        plt.plot(list(range(xstart,xend)),[plant["Price"]]*len(range(xstart,xend)), color=COLORS[plant["Portfolio"]])
        xstart = xend
    
    demand_x = []
    demand_y = []
    for price in range(500):
        demand_x.append(get_demand(hour,price))
        demand_y.append(price)
    plt.plot(demand_x,demand_y)

    plt.show()

    return

def get_plant_profits():
    plants = []
    for port in portfolios.keys():
        for plant in portfolios[port].keys():
            p = {}
            pl = portfolios[port][plant]
            p["Capacity"] = pl["Capacity"]
            p["Price"] = pl["Marginal Cost"]
            p["Name"] = plant
            p["Portfolio"] = port
            plants.append(p)
    sorted_plants = sorted(plants, key=lambda d: d['Price'])
    
    total_profits = {}
    for plant in sorted_plants:
        total_profits[plant["Name"]] = 0

    for hour in range(1,9):
        xstart = 0
        xend = 0
        operate = True
        for plant in sorted_plants:
            if operate:
                xend = xstart + plant["Capacity"]
                price = (plant["Price"]+CONST)
                demand = get_demand(hour, price)
                if demand <= xend:
                    prof = (demand - xstart)*(plant["Price"]+CONST-plant["Price"])
                    if prof < 0:
                        prof = 0
                    total_profits[plant["Name"]] += prof
                    operate = False
                else:
                    total_profits[plant["Name"]] += plant["Capacity"]*(plant["Price"]+CONST-plant["Price"])
                xstart = xend
        
    for hour in range(9,17):
        xstart = 0
        xend = 0
        operate = True
        price = 0
        operate_plants = []
        for plant in sorted_plants:
            if operate:
                xend = xstart + plant["Capacity"]
                price = (plant["Price"]+CONST)
                demand = get_demand(hour, price)
                if demand <= xend:
                    prof = (demand - xstart)*(price-plant["Price"])
                    if prof < 0:
                        prof = 0
                    total_profits[plant["Name"]] += prof
                    operate = False
                else:
                    operate_plants.append(plant["Name"])
                xstart = xend
        for p in sorted_plants:
            if p["Name"] in operate_plants:
                total_profits[p["Name"]] += p["Capacity"]*(price-p["Price"])

    # print("\n----Profits by Plant----")
    # for plant in total_profits.keys():
    #     print(plant + " "*(20-len(plant)) + "\t" + str(total_profits[plant]))
    
    return total_profits

def get_portfolio_profits():
    portfolio_profits = {}
    plant_profits = get_plant_profits()
    print("\n----Profits by Portfolio----")
    for port in portfolios.keys():
        portfolio_profits[port] = 0
        for plant in portfolios[port].keys():
            portfolio_profits[port] += plant_profits[plant]
            portfolio_profits[port] -= portfolios[port][plant]["Fixed Cost"]*4
        portfolio_profits[port] -= BIDS[port]
        print(port + " "*(20-len(port)) + "\t" + str(portfolio_profits[port]))

def get_price(hour):
    plants = []
    for port in portfolios.keys():
        for plant in portfolios[port].keys():
            p = {}
            pl = portfolios[port][plant]
            p["Capacity"] = pl["Capacity"]
            p["Price"] = pl["Marginal Cost"]
            p["Name"] = plant
            p["Portfolio"] = port
            plants.append(p)
    sorted_plants = sorted(plants, key=lambda d: d['Price'])

    xstart = 0
    xend = 0
    price = 0
    for plant in sorted_plants:
        xend = xstart + plant["Capacity"]
        price = (plant["Price"]+CONST)
        demand = get_demand(hour, price)
        if demand <= xend:
            return price
        xstart = xend
    return




def do_thing():
    # plot_full_capacity_profits()
    # get_full_capacity_profits(PRICE)
    # plot_full_game_projection()
    # format_demands()
    # print(get_demand(7,200))
    # plot_supply_and_demand(1)
    # print(type(range(3)))
    # get_portfolio_profits()
    # for i in range(1,17):
    #     print(str((i-1)%4+1) + "  " + str(get_price(i)))
    print(TOTAL_CAPACITY - get_demand(7,200))

do_thing()