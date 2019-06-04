import numpy as np 
import pandas as pd
import pulp

def storageHeater(heatDemandTotal, houseType, heaterPrevious):

    pD=np.zeros(24)
    pD[0:8]=0.09
    pD[8:25]=0.21
    priceData=pd.DataFrame(pD, columns=['Price'])
    
    if houseType == 'Small':
        heaterCap = 19.3
        heaterRat = 2.76
        heaterNum = 2
    elif houseType == 'Medium':
        heaterCap = 19.3
        heaterRat = 2.76
        heaterNum = 5
    elif houseType == 'Large':
        heaterCap =23.1
        heaterRat =3.3
        heaterNum = 6
        
    deplete = heaterPrevious/heaterCap
    
    heatDemand = pd.DataFrame(heatDemandTotal.iloc[0:]/heaterNum)
    
    flow = heatDemand['Demand']
    price = priceData['Price']
    
    charge = pulp.LpVariable.dicts("charge", 
                               ((Idx,1) for Idx in heatDemand.index), 
                               lowBound=0,
                               upBound=heaterRat)

    discharge = pulp.LpVariable.dicts("discharge", 
                            ((Idx,1) for Idx in heatDemand.index), 
                            lowBound=-heaterRat,
                            upBound=0)

    state = pulp.LpVariable.dicts("state", 
                        ((Idx,1) for Idx in heatDemand.index), 
                        lowBound=heaterCap*0.2,
                        upBound=heaterCap)
    
    overspill = pulp.LpVariable.dicts("overspill",
                                      ((Idx,1) for Idx in heatDemand.index),
                                      lowBound=0,
                                      upBound=heaterRat)
    
    model = pulp.LpProblem("Storage header scheduling problem", pulp.LpMinimize)
    
    # constraint definitions
    hours=heatDemand.index
    for Idx in hours:
        if Idx == 1:
            model += state[(Idx,1)] - (heaterCap*0.2) - (charge[(Idx,1)])  - (discharge[(Idx,1)]) == 0
            model += (charge[(Idx,1)]) + (heaterCap*0.2) <= heaterCap
            model += deplete + discharge[(Idx,1)] >= (heaterCap*0.1) 
        elif Idx > 1:
            model += state[(Idx,1)] - state[((Idx-1),1)] - (charge[(Idx,1)])  - (discharge[(Idx,1)])  == 0
            model += ((charge[(Idx,1)])) + state[((Idx-1),1)] <= heaterCap
            model += state[((Idx-1),1)] + discharge[(Idx,1)]  >= (heaterCap*0.1) 

    for Idx in hours:
        model += charge[Idx,1] >= 0
        model += discharge[Idx,1] <= 0 
        model += overspill[Idx,1] >= 0
    
    for Idx in hours:
        model += flow[Idx] + discharge[Idx,1] + overspill[Idx,1] == 0
    
 
    for Idx in hours:
        model += state[Idx,1] <= heaterCap
        model += state[Idx,1] >= heaterCap*0.2

    for Idx in hours:
        model += (discharge[Idx,1] * -1) + charge[Idx,1] <= heaterRat
    
    # Objective Function
    model +=  pulp.lpSum((price.loc[Idx] * (charge[Idx,1] + overspill[Idx,1])) for Idx in hours)
    
    model.solve()
    
    c = [ charge[Idx,1].varValue for Idx in hours ]
    s = [ state[Idx,1].varValue for Idx in hours ]
    
    
    chg = pd.DataFrame(c, index = heatDemand.index)
    ste = pd.DataFrame(s, index=heatDemand.index)
    
    
    totChg = chg * heaterNum

    gone= ste.iloc[23]/heaterCap
    
    return chg, totChg, gone
