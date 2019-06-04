import pandas as pd
import pulp

def esCapacityBalance(demand, ap):

    disE = 0.9 #example battery efficiencies
    chaE = 0.9
    flow = demand['Power']
    idsA = flow.where(flow > flow.mean(0))
    idsB = flow.where(flow < flow.mean(0))
    above = idsA.dropna()
    below = idsB.dropna()
    aboveIds = above.index
    belowIds = below.index

    capacity = pulp.LpVariable("capacity")
    
    charge = pulp.LpVariable.dicts("charge", 
                               ((Idx,1) for Idx in demand.index))

    discharge = pulp.LpVariable.dicts("discharge", 
                            ((Idx,1) for Idx in demand.index))

    state = pulp.LpVariable.dicts("state", 
                        ((Idx,1) for Idx in demand.index))


                          
    model = pulp.LpProblem("Battery scheduling problem", pulp.LpMinimize) 

    # constraint definitions
    hours=demand.index
    for Idx in hours:
        if Idx == 1:
            model += state[(Idx,1)] - (capacity*0.6) - ((charge[(Idx,1)]) * chaE) - ((discharge[(Idx,1)]) * (1/disE))== 0
            model += (charge[(Idx,1)]) + (capacity*0.6) <= ((capacity*0.9) / chaE)
            model += (capacity*0.6) + discharge[(Idx,1)] >= ((capacity*0.2) * disE)
        elif Idx > 1:
            model += state[(Idx,1)] - state[((Idx-1),1)] - ((charge[(Idx,1)]) * chaE) - ((discharge[(Idx,1)]) * (1/disE)) == 0
            model += ((charge[(Idx,1)])) + state[((Idx-1),1)] <= ((capacity*0.9) / chaE)
            model += state[((Idx-1),1)] + discharge[(Idx,1)]  >= ((capacity*0.2) * disE)  

    for Idx in hours:
        if flow[Idx] < flow.mean(0):
            model += discharge[Idx,1] == 0
        elif flow[Idx] > flow.mean(0):
            model += charge[Idx,1] == 0

    model += state[Idx,1] == capacity*0.6

    for Idx in hours:
        model += charge[Idx,1] >= 0
        model += discharge[Idx,1] <= 0 

    for Idx in demand.index:
        model += state[Idx,1] <= capacity*0.9
        model += state[Idx,1] >= capacity*0.2

    for Idx in belowIds:
        model += charge[Idx,1] + (demand.loc[Idx]) <= flow.mean(0) 
        model += charge[Idx,1] >=0

    for Idx in aboveIds:
        model += discharge[Idx,1] + (demand.loc[Idx]) >= flow.mean(0)
        model += discharge[Idx,1] <=0
 
    upper = demand.where(demand>flow.mean(0)).dropna()
    
    qUp3 = upper.Power.quantile([0.75]) 
    qUp1 = upper.Power.quantile([0.25])
    
    posDrop3= upper.where(upper > qUp3.iloc[0]).dropna().index
    
    if qUp3.iloc[0] > qUp1.iloc[0]:
        posDrop1 = upper.where(upper < qUp1.iloc[0]).dropna().index
    else:
        qUp1 = upper.Power.quantile([0.25]) - (upper.Power.quantile([0.25])*0.5)
        posDrop1 = upper.where(upper < qUp1.iloc[0]).dropna().index
            
    
    for Idx in posDrop3:
        model += discharge[Idx,1] + charge[Idx,1] + demand.loc[Idx]  <= demand.loc[Idx]*ap
    
    for Idx in posDrop1:
        model += discharge[Idx,1] == 0

    idsA = flow.where(flow > flow.mean(0))
    above = idsA.dropna()
    ordered=demand.sort_values(by='Power')
    times=ordered.index
    maxFlow=times[(len(flow)-int((len(above)/3))):len(flow)]
        
    # Objective Function
    model += capacity

    sol=model.solve()
    
    capacity = capacity.varValue
    
    return model, sol, capacity


def esCapacityBalanceNegative(demand, ap):

    disE = 0.9 #example battery efficiencies
    chaE = 0.9
    flow = demand['Power']
    idsA = flow.where(flow > flow.mean(0))
    idsB = flow.where(flow < flow.mean(0))
    above = idsA.dropna()
    below = idsB.dropna()
    aboveIds = above.index
    belowIds = below.index

    capacity = pulp.LpVariable("capacity")
    
    charge = pulp.LpVariable.dicts("charge", 
                               ((Idx,1) for Idx in demand.index))

    discharge = pulp.LpVariable.dicts("discharge", 
                            ((Idx,1) for Idx in demand.index))

    state = pulp.LpVariable.dicts("state", 
                        ((Idx,1) for Idx in demand.index))


                          
    model = pulp.LpProblem("Battery scheduling problem", pulp.LpMinimize) 

    # constraint definitions
    hours=demand.index
    for Idx in hours:
        if Idx == 1:
            model += state[(Idx,1)] - (capacity*0.6) - ((charge[(Idx,1)]) * chaE) - ((discharge[(Idx,1)]) * (1/disE))== 0
            model += (charge[(Idx,1)]) + (capacity*0.6) <= ((capacity*0.9) / chaE)
            model += (capacity*0.6) + discharge[(Idx,1)] >= ((capacity*0.2) * disE)
        elif Idx > 1:
            model += state[(Idx,1)] - state[((Idx-1),1)] - ((charge[(Idx,1)]) * chaE) - ((discharge[(Idx,1)]) * (1/disE)) == 0
            model += ((charge[(Idx,1)])) + state[((Idx-1),1)] <= ((capacity*0.9) / chaE)
            model += state[((Idx-1),1)] + discharge[(Idx,1)]  >= ((capacity*0.2) * disE)  

    for Idx in hours:
        if flow[Idx] < flow.mean(0):
            model += discharge[Idx,1] == 0
        elif flow[Idx] > flow.mean(0):
            model += charge[Idx,1] == 0

    model += state[Idx,1] == capacity*0.6

    for Idx in hours:
        model += charge[Idx,1] >= 0
        model += discharge[Idx,1] <= 0 

    for Idx in demand.index:
        model += state[Idx,1] <= capacity*0.9
        model += state[Idx,1] >= capacity*0.2

    for Idx in belowIds:
        model += charge[Idx,1] + (demand.loc[Idx]) <= flow.mean(0) 
        model += charge[Idx,1] >=0

    for Idx in aboveIds:
        model += discharge[Idx,1] + (demand.loc[Idx]) >= flow.mean(0)
        model += discharge[Idx,1] <=0
 
    upper = demand.where(demand>flow.mean(0)).dropna()
    
    qUp3 = upper.Power.quantile([0.75]) 
    qUp1 = upper.Power.quantile([0.25])
    
    posDrop3= upper.where(upper > qUp3.iloc[0]).dropna().index
    
    if qUp3.iloc[0] > qUp1.iloc[0]:
        posDrop1 = upper.where(upper < qUp1.iloc[0]).dropna().index
    else:
        qUp1 = upper.Power.quantile([0.25]) - (upper.Power.quantile([0.25])*0.5)
        posDrop1 = upper.where(upper < qUp1.iloc[0]).dropna().index
            
    
    for Idx in posDrop3:
        model += discharge[Idx,1] + charge[Idx,1] + demand.loc[Idx]  <= demand.loc[Idx]*ap
    
    for Idx in posDrop1:
        model += discharge[Idx,1] == 0

    idsA = flow.where(flow > flow.mean(0))
    above = idsA.dropna()
    ordered=demand.sort_values(by='Power')
    times=ordered.index
    maxFlow=times[(len(flow)-int((len(above)/3))):len(flow)]
        
    # Objective Function
    model += capacity

    sol=model.solve()
    
    capacity = capacity.varValue
    
    return model, sol, capacity
