from prometheus_client import REGISTRY, Gauge
import json
import os


EXPORT_FILE_PATH = "../lgtm/export.json"
if not os.path.exists(EXPORT_FILE_PATH):
    open(EXPORT_FILE_PATH, "a+").close()
    
    
def export_metrics() -> None:
    export_data = {}
    
    for metric in REGISTRY.collect():
        mname = metric.name
        mtype = metric.type
        samples = metric.samples
        
        if mtype == 'info':
            mtype = 'gauge'
        elif mtype == 'stateset':
            mtype = 'gauge'

        if mtype != 'gauge' or not samples:
            continue

        export_data[mname] = []
        for sample in samples:
            export_data[mname].append(
                [sample.labels, sample.value]
            )
        
    with open(EXPORT_FILE_PATH, "w+") as file:
        json.dump(export_data, file, indent=2)


def import_metrics() -> None:
    with open(EXPORT_FILE_PATH, "r") as file:
        raw_data = file.read()
        if not raw_data:
            raw_data = "{}"
        data = json.loads(raw_data)

    for metric_id, samples in data.items():
        metric: Gauge = REGISTRY._names_to_collectors.get(metric_id)
        if not metric or not isinstance(metric, Gauge):
            continue
        
        for (labels, value) in samples:
            if labels:
                metric.labels(**labels).set(value)
            else:
                metric.set(value)
            