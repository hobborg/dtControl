from IPython.display import HTML, display
import webbrowser
import os

def print_table(benchmark_results, inline=True):
    head = '<head><link rel="stylesheet" ' \
           'href="https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/css/bootstrap.min.css" ' \
           'integrity="sha384-ggOyR0iXCbMQv3Xipma34MD+dH/1fQ784/j6cY/iJTQUOhcWr7x9JvoRxT2MZw1T" ' \
           'crossorigin="anonymous"></head>'

    table_class = '' if inline else 'table table-striped table-bordered table-hover'
    body = '<body><table class="{}"><thead><tr><td></td>'.format(table_class)
    for c in benchmark_results.column_names:
        body += '<th scope="col" style="text-align:center">{}</th>'.format(c)
    body += '</tr></thead><tbody>'

    for i in range(len(benchmark_results.row_names)):
        body += '<tr>'
        body += '<th scope="row" style="text-align:center">{}</th>'.format(benchmark_results.row_names[i])
        for column in benchmark_results.table[i]:
            body += '<td style="text-align:center">'
            if isinstance(column, str):
                body += '<span style="color:red">{}</span>'.format(column)
            else:
                for k, v in column.items():
                    body += '{}: {}<br>'.format(k, v)
            body += '</td>'
        body += '</tr>'
    body += '</tbody></table></body>'

    if inline:
        display(HTML(f"<html>{body}</html>"))
    else:
        filename = 'tmp/benchmark.html'
        with open(filename, 'w+') as out:
            out.write(f'<html>{head}{body}</html>')
        display(HTML(f'<html><a href="{filename}" target="_blank">View table</a></html>'))
        url = f'file://{os.path.abspath(filename)}'
        webbrowser.open(url)
