# broadband-cli

#### Max Broadband Speed for Address Points, By Submission Period


## Requirements

1. ArcGIS Pro >= 1.4 and python 3.5

## Install

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

## Development Usage

- `cd broadband-cli`
- `python -m boost`
