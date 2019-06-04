import pandas as pd
import pulp

def esBalance(esCap, demand, ap, sign):

    disE = 0.8 #example battery efficiencies
    chaE = 0.8
    flow = demand['Power']
    idsA = flow.where(flow > flow.mean(0))
    idsB = flow.where(flow < flow.mean(0))
    above = idsA.dropna()
    below = idsB.dropna()
    aboveIds = above.index
    belowIds = below.index

    
    #esUpper=pulp.LpVariable("esUpper", lowBound=0, upBound=esCap, cat='Continuous')
 
    charge = pulp.LpVariable.dicts("charge", 
                               ((Idx,1) for Idx in demand.index), 
                               lowBound=0,
                               upBound=esCap)

    discharge = pulp.LpVariable.dicts("discharge", 
                            ((Idx,1) for Idx in demand.index), 
                            lowBound=-esCap,
                            upBound=0)

    state = pulp.LpVariable.dicts("state", 
                        ((Idx,1) for Idx in demand.index), 
                        lowBound=esCap*0.2,
                        upBound=esCap*0.9)


                          
    model = pulp.LpProblem("Battery scheduling problem", pulp.LpMinimize) 

    # constraint definitions
    hours=demand.index
    for Idx in hours:
        if Idx == 1:
            model += state[(Idx,1)] - (esCap*0.6) - ((charge[(Idx,1)]) * chaE) - ((discharge[(Idx,1)]) * (1/disE))== 0
            model += (charge[(Idx,1)]) + (esCap*0.6) <= ((esCap*0.9) / chaE)
            model += (esCap*0.6) + discharge[(Idx,1)] >= ((esCap*0.2) * disE)
        elif Idx > 1:
            model += state[(Idx,1)] - state[((Idx-1),1)] - ((charge[(Idx,1)]) * chaE) - ((discharge[(Idx,1)]) * (1/disE)) == 0
            model += ((charge[(Idx,1)])) + state[((Idx-1),1)] <= ((esCap*0.9) / chaE)
            model += state[((Idx-1),1)] + discharge[(Idx,1)]  >= ((esCap*0.2) * disE)  

    for Idx in hours:
        if flow[Idx] < flow.mean(0):
            model += discharge[Idx,1] == 0
        elif flow[Idx] > flow.mean(0):
            model += charge[Idx,1] == 0

    model += state[Idx,1] <= esCap*0.6
    model += state[Idx,1] >= esCap*0.4

    for Idx in hours:
        model += charge[Idx,1] >= 0
        model += discharge[Idx,1] <= 0 

    for Idx in demand.index:
        model += state[Idx,1] <= esCap*0.9
        model += state[Idx,1] >= esCap*0.2

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
    model +=  pulp.lpSum(demand.loc[Idx] + discharge[Idx,1] for Idx in maxFlow) + (pulp.lpSum((charge[Idx,1] + discharge[Idx,1] + demand.loc[Idx]) - flow.mean(0)  for Idx in aboveIds)/len(aboveIds)) 
    
    sol=model.solve()
    
    chg = [ charge[Idx,1].varValue for Idx in hours ]
    dischg = [ discharge[Idx,1].varValue for Idx in hours ]
    ste = [ state[Idx,1].varValue for Idx in hours ]

    f=pd.Series(demand['Power'], demand.index)
    c=pd.Series(chg, demand.index)
    d=pd.Series(dischg, demand.index)

    if sign==1:
        newDemand=pd.Series(f+c+d, demand.index)
    else:
        nD=pd.Series(f+c+d, demand.index)
        newDemand=nD*-1
    
    return model, sol, f, c, d, newDemand




###############


def esBalanceNegative(esCap, demandOld, ap, sign):

    demand=(demandOld*-1)
    disE = 0.8 #example battery efficiencies
    chaE = 0.8
    flow = demand['Power']
    idsA = flow.where(flow > flow.mean(0))
    idsB = flow.where(flow < flow.mean(0))
    above = idsA.dropna()
    below = idsB.dropna()
    aboveIds = above.index
    belowIds = below.index

    
    #esUpper=pulp.LpVariable("esUpper", lowBound=0, upBound=esCap, cat='Continuous')
 
    charge = pulp.LpVariable.dicts("charge", 
                               ((Idx,1) for Idx in demand.index), 
                               lowBound=0,
                               upBound=esCap)

    discharge = pulp.LpVariable.dicts("discharge", 
                            ((Idx,1) for Idx in demand.index), 
                            lowBound=-esCap,
                            upBound=0)

    state = pulp.LpVariable.dicts("state", 
                        ((Idx,1) for Idx in demand.index), 
                        lowBound=esCap*0.2,
                        upBound=esCap*0.9)


                          
    model = pulp.LpProblem("Battery scheduling problem", pulp.LpMinimize) 

    # constraint definitions
    hours=demand.index
    for Idx in hours:
        if Idx == 1:
            model += state[(Idx,1)] - (esCap*0.6) - ((charge[(Idx,1)]) * chaE) - ((discharge[(Idx,1)]) * (1/disE))== 0
            model += (charge[(Idx,1)]) + (esCap*0.6) <= ((esCap*0.9) / chaE)
            model += (esCap*0.6) + discharge[(Idx,1)] >= ((esCap*0.2) * disE)
        elif Idx > 1:
            model += state[(Idx,1)] - state[((Idx-1),1)] - ((charge[(Idx,1)]) * chaE) - ((discharge[(Idx,1)]) * (1/disE)) == 0
            model += ((charge[(Idx,1)])) + state[((Idx-1),1)] <= ((esCap*0.9) / chaE)
            model += state[((Idx-1),1)] + discharge[(Idx,1)]  >= ((esCap*0.2) * disE)  

    for Idx in hours:
        if flow[Idx] < flow.mean(0):
            model += discharge[Idx,1] == 0
        elif flow[Idx] > flow.mean(0):
            model += charge[Idx,1] == 0

    model += state[Idx,1] <= esCap*0.6
    model += state[Idx,1] >= esCap*0.4

    for Idx in hours:
        model += charge[Idx,1] >= 0
        model += discharge[Idx,1] <= 0 

    for Idx in demand.index:
        model += state[Idx,1] <= esCap*0.9
        model += state[Idx,1] >= esCap*0.2

    for Idx in belowIds:
        model += charge[Idx,1] + (demand.loc[Idx]) <= flow.mean(0) 
        model += charge[Idx,1] >=0

    for Idx in aboveIds:
        model += discharge[Idx,1] + (demand.loc[Idx]) >= flow.mean(0)
        model += discharge[Idx,1] <=0
 
    upper = demand.where(demand>flow.mean(0)).dropna()
    
    qUp3 = upper.Power.quantile([0.75]) - (upper.Power.quantile([0.75])*0.1) 
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
    model +=  pulp.lpSum(demand.loc[Idx] + discharge[Idx,1] for Idx in maxFlow) + (pulp.lpSum((charge[Idx,1] + discharge[Idx,1] + demand.loc[Idx]) - flow.mean(0)  for Idx in aboveIds)/len(aboveIds)) 
    
    sol=model.solve()
    
    chg = [ charge[Idx,1].varValue for Idx in hours ]
    dischg = [ discharge[Idx,1].varValue for Idx in hours ]
    ste = [ state[Idx,1].varValue for Idx in hours ]

    f=pd.Series(demand['Power'], demand.index)
    c=pd.Series(chg, demand.index)
    d=pd.Series(dischg, demand.index)

    newDemandInter=pd.Series(f+c+d, demand.index)
    newDemand=newDemandInter*-1
    flow=f*-1
    
    return model, sol, flow, c, d, newDemand

