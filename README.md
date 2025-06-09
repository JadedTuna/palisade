# Palisade
Palisade is a research programming language with a focus on static information flow analysis.

## Setup
Python library `click` is required to run `palisade`.

```bash
# optionally create a new virtual environment
python3 -m venv venv
source venv/bin/activate
# install requirements
pip install click==8.2.0
```

## Tests
To run built-in tests:

```bash
./palisade test
```

all tests are expected to succeed. For verbose output on all tests use `./palisade test -v`.

## Usage
To analyze a program:

```bash
./palisade compile <program.pls>
```

The analysis tool will make a note of every time a variable's label is changed. At the end
it will print out the list of all output variables and their current lables. Program is
validated to be secure if all initially low output variables remain low at the end.
