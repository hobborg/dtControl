from IPython.display import HTML, display
import webbrowser
import os
from jinja2 import Environment, FileSystemLoader

file_loader = FileSystemLoader('.')
env = Environment(loader=file_loader)

def print_table(benchmark_results, filename='benchmark.html'):
    template = env.get_template('ui/table.html')
    with open(filename, 'w+') as out:
        out.write(template.render(column_names=benchmark_results.column_names, row_names=benchmark_results.row_names,
                                  table=benchmark_results.table))
    display(HTML(f'<html><a href="{filename}" target="_blank">View table</a></html>'))
    url = f'file://{os.path.abspath(filename)}'
    webbrowser.open(url)
