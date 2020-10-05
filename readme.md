# broadband-cli

#### Max Broadband Speed for Address Points, By Submission Period


## Requirements

1. ArcGIS Pro >= 1.4 and python 3.5

## Install

1. `conda create -n environment_name --clone arcgispro-py3`
1. `activate environment_name`
1. `git clone https://github.com/agrc/broadband-cli.git`
1. `cd broadband-cli`
1. `pip install ./`

## Usage

- `boost`

```shell
boost analyze --workspace <workspace>
boost stats --workspace <workspace>
boost postprocess --target <target> --workspace <workspace>
boost -h | --help
boost --version

Options:
--target                          The target folder
--workspace                       A geodatabse
-h --help                         Show this screen.
--version                         Show version.
```

First, edit the values in `config.py` for the existing data. These datasets must live in the `--workspace` geodatabase. The unincorporated areas layer in the SGID may be out-of-date.

The Address Points Layer will affect the accuracy of the counts. A large apartment building with just a single point will lead to an under-representation of coverage for that area. A rural county with less high-speed coverage that sends a huge bunch of address points that we didn't have on previous runs will (correctly) skew the results back down as addresses that weren't properly included now are.

To get the full output, you must run the three commands in order (the `analyze` step may take 1.5-3 hours) :
```shell
boost analyze --workspace c:\temp\workspace.gdb
boost stats --workspace c:\temp\workspace.gdb
boost postprocess --target c:\temp\out_folder --workspace c:\temp\workspace
```

You will then have a few CSVs in the  `--target` folder. To compute the statewide coverage by speed tier, use the data from `MaxDown_County.csv`. Sum the values for each tier across all the counties, then compute their percentages against the total number of address points.

## Development Usage

- `cd broadband-cli`
- `python -m boost`
