# drawbar-pull-experiments
Models drawbar pull on a trisphere cycle model and measures wheel slip versus drawbar pull force.

## Usage
Test parameters must be set in ``config/config.yaml``. 
To run the experiments, source gazebo and ros workspaces and execute:
```
python3 run.py
```
To generate a summary, execute:
```
python3 generate_report.py 
```
This step requires ``pandoc`` to convert the report to html.
