def recommendations(summary):
    c=summary.get('congestion','LOW'); d=float(summary.get('average_density',0)); flow=float(summary.get('flow_vph',0))
    out=[]
    if c=='HIGH': out += ['Prioritize traffic-signal review for the busiest corridor.','Consider controlled diversion messaging on parallel roads.','Review peak-hour lane allocation and incident management readiness.']
    elif c=='MEDIUM': out += ['Monitor the corridor for rising queue formation.','Prepare adaptive signal timing if density continues increasing.']
    else: out += ['Traffic conditions are relatively light in this analyzed feed.','Maintain monitoring and compare against historical runs.']
    if flow>500: out.append('High vehicle throughput detected; evaluate corridor capacity during peak periods.')
    if d>50: out.append('High spatial density detected; inspect hotspot zones using the heatmap.')
    return out
