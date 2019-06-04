import pandas as pd
import pulp


def esRenewable(esCap, demand, ap):

    disE = 0.8 #example battery efficiencies
    chaE = 0.8
    flow = demand['Power']
    idsA = flow.where(flow > 0)
    idsB = flow.where(flow < 0)
    above = idsA.dropna()
    below = idsB.dropna()
    aboveIds = above.index
    belowIds = below.index

 
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

    for Idx in belowIds:
        model += discharge[Idx,1] == 0
        model += charge[Idx,1]  <= ((demand.loc[Idx])*-1) 
        model += charge[Idx,1] + ((demand.loc[Idx])) >= (demand.loc[Idx])

    
    for Idx in aboveIds:
        model += charge[Idx,1] == 0
        model += discharge[Idx,1] + demand.loc[Idx] >= 0
        model += discharge[Idx,1] + demand.loc[Idx] <= demand.loc[Idx]
        #model += charge[Idx,1] + demand.loc[Idx] <= demand.max()*0.9
        
        
    model += state[Idx,1] <= esCap*0.6
    model += state[Idx,1] >= esCap*0.4

    for Idx in hours:
        model += charge[Idx,1] >= 0
        model += discharge[Idx,1] <= 0 

    for Idx in demand.index:
        model += state[Idx,1] <= esCap*0.9
        model += state[Idx,1] >= esCap*0.2
    
    #######

    neg = demand.where(demand<0).dropna()
    pos = demand.where(demand>0).dropna()
    orderedNeg = neg.sort_values(by='Power')
    orderedPos = pos.sort_values(by='Power')
    
    qNeg3 = orderedNeg.Power.quantile([0.75])
    negDrop3 = orderedNeg.where(orderedNeg < qNeg3.iloc[0]).dropna().index
    
    for Idx in negDrop3:
        model += charge[Idx,1] + demand.loc[Idx] >= demand.loc[Idx]*ap
    
    qPos3 = orderedPos.Power.quantile([0.75]) - (orderedPos.Power.quantile([0.75])*0.1)
    qPos1 = orderedPos.Power.quantile([0.25]) 
    
    posDrop3= orderedPos.where(orderedPos > qPos3.iloc[0]).dropna().index
    
    if qPos3.iloc[0] > qPos1.iloc[0]:
        posDrop1 = orderedPos.where(orderedPos < qPos1.iloc[0]).dropna().index
    else:
        qPos1 = orderedPos.Power.quantile([0.25]) - (orderedPos.Power.quantile([0.25])*0.5)
        posDrop1 = orderedPos.where(orderedPos < qPos1.iloc[0]).dropna().index
    
    for Idx in posDrop3:
        model += discharge[Idx,1] + charge[Idx,1] + demand.loc[Idx]  <= demand.loc[Idx]*ap
    
    for Idx in posDrop1:
        model += discharge[Idx,1] == 0
    
    #######
    
    demandNeg = demand*-1    
    # Objective Function
    model += pulp.lpSum((demandNeg.loc[Idx] - charge[Idx,1]) for Idx in belowIds) 
                        
    sol=model.solve()

    chg = [ charge[Idx,1].varValue for Idx in hours ]
    dischg = [ discharge[Idx,1].varValue for Idx in hours ]
    ste = [ state[Idx,1].varValue for Idx in hours ]

    f=pd.Series(demand['Power'], demand.index)
    c=pd.Series(chg, demand.index)
    d=pd.Series(dischg, demand.index)
    newDemand=pd.Series(f+c+d, demand.index)    
    
    return model, sol, f, c, d, newDemand
