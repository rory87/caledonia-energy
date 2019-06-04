import pandas as pd
from energyStorage.esBalance import esBalance
from energyStorage.esBalance import esBalanceNegative
from energyStorage.esRenewable import esRenewable
from energyStorage.esCapacityBalance import esCapacityBalance
from energyStorage.esCapacityBalance import esCapacityBalanceNegative
from energyStorage.esCapacityRenewable import esCapacityRenewable
import pulp

def runSolutionBalance(esCap, demand):

    idReal=list(range(1,25))
    demand = pd.DataFrame(demand)
    demand = demand.set_index([idReal])
    demand.columns=['Power']
    ap=0.7
    
    check=demand[(demand>0).all(1)]

    if check.empty:
        sign = -1
        model, sol, f, c, d, newDemand = esBalanceNegative(esCap, demand, ap, sign)
    elif len (check) == 24:
        sign = 1
        model, sol, f, c, d, newDemand = esBalance(esCap, demand, ap, sign)
    else:
        model, sol, f, c, d, newDemand = esRenewable(esCap, demand, ap)

              

    while sol == -1:
        if ap < 0.85:
            ap += 0.1
        else: 
            ap += 0.01

        if check.empty:
            sign = -1
            model, sol, f, c, d, newDemand = esBalanceNegative(esCap, demand, ap, sign)
        elif len (check) == 24:
            sign = 1
            model, sol, f, c, d, newDemand = esBalance(esCap, demand, ap, sign)
        else: 
            model, sol, f, c, d, newDemand = esRenewable(esCap, demand, ap)
            

       
    return model, sol, f, c, d, newDemand


def runSolutionCapacity(demand, ap):

    idReal=list(range(1,25))
    demand = pd.DataFrame(demand)
    demand = demand.set_index([idReal])
    demand.columns=['Power']

    check=demand[(demand>0).all(1)]

    if check.empty:
        demandNeg = demand*-1
        model, sol, capacity = esCapacityBalanceNegative(demandNeg, ap)
    elif len (check) == 24:
        model, sol, capacity = esCapacityBalance(demand, ap)
    else:
        model, sol, capacity = esCapacityRenewable(demand, ap)

    while sol == -1:
        if ap < 0.85:
            ap += 0.1
        else: 
            ap += 0.01
                
        if check.empty:
            demand = demand*-1
            model, sol, capacity = esCapacityBalance(demand, ap)
        elif len (check) == 24:
            model, sol, capacity = esCapacityBalance(demand, ap)
        else:
            model, sol, capacity = esCapacityRenewable(demand, ap)

    return model, sol, capacity, ap
