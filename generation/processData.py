import numpy as np
import pandas as pd

def process_data(data, table, dim):

    vlqs = data.values_list()
    r = np.core.records.fromrecords(vlqs, names=[f.name for f in table._meta.fields])
    l=np.array(r)
    process = pd.DataFrame(index=range(len(l)), columns=range(dim)).as_matrix()             

    for i in range(0,len(process)): # extract the information we need for inputs.
        change = l[i]
        for j in range(1,(dim+1)):
            process[i,(j-1)] = change[j]

    processReal=pd.DataFrame(process)

    return processReal
