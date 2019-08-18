from IPython.display import HTML, display

def print_table(benchmark_results):
    output = '<html><body><table><tr><td></td>'
    for c in benchmark_results.column_names:
        output += '<th scope="col">{}</th>'.format(c)
    output += '</tr>'

    for i in range(len(benchmark_results.row_names)):
        output += '<tr>'
        output += '<th scope="row">{}</th>'.format(benchmark_results.row_names[i])
        for column in benchmark_results.table[i]:
            output += '<td>'
            if isinstance(column, str):
                output += '<span style="color:red">{}</span>'.format(column)
            else:
                for k, v in column.items():
                    output += '{}: {}<br>'.format(k, v)
            output += '</td>'
        output += '</tr>'
    output += '</table></body></html>'

    display(HTML(output))
