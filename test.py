import subprocess
from lib.utils import *

test_order = [
    'basic1',
    'basic2',
    'complex1',
    'error1',
    'explicit1',
    'explicit2',
    'implicit_if1',
    'implicit_if2',
    'implicit_while',
    'implicit_throw',
    'implicit_array',
]

def run_tests():
    indent = ' '*4
    border_length = 80
    for index, test in enumerate(test_order):
        start_border_length = border_length-len(str(index+1))
        end_border_length = start_border_length+len(str(index+1))+2
        print(f'\n{blue('--- running test')}', yellow(index+1), blue('-'*start_border_length), '\n')
        with open(f'./tests/{test}.pls') as f:
            src = f.read()
        actual = subprocess.run(['./palisade', 'compile', f'./tests/{test}.pls'], capture_output=True).stdout.decode()
        with open(f'./tests/{test}.out') as f:
            expected = f.read()
        print(cyan(' - test code -'), f'\n{indent}{src.replace('\n', f'\n{indent}')}', '\n')
        print(cyan(' - expected output -'), f'\n{indent}', expected.replace('\n', f'\n{indent}'))
        print(cyan(' - actual output -'), f'\n{indent}', actual.replace('\n', f'\n{indent}'))
        print(blue('---'), green('test passed') if expected in actual else red('test failed'), blue('-'*end_border_length), '\n'*5)



