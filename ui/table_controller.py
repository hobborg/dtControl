from os.path import join, exists, abspath
from urllib.parse import quote

from jinja2 import Environment, FileSystemLoader

GRAPHVIZ_URL = 'https://dreampuf.github.io/GraphvizOnline/#'
file_loader = FileSystemLoader('.')
env = Environment(loader=file_loader)


class TableController:
    def __init__(self, html_file, output_folder):
        self.html_file = html_file
        self.output_folder = output_folder

    def update_and_save(self, results):
        template = env.get_template('ui/table.html')
        with open(self.html_file, 'w+') as out:
            out.write(template.render(column_names=results.column_names, row_metadata=results.row_metadata,
                                      table=results.table, links_table=self.get_dot_and_c_links(results)))

    def get_dot_and_c_links(self, results):
        links_table = []
        for i in range(len(results.row_metadata)):
            dataset = results.row_metadata[i]["name"]
            l = []
            for j in range(len(results.column_names)):
                classifier = results.column_names[j]
                d = {}
                path = join(self.output_folder, classifier, dataset, classifier)
                if exists(path + '.dot'):
                    d['dot_link'] = self.get_dot_link(path + '.dot')
                if exists(path + '.c'):
                    d['c_link'] = self.get_c_link(path + '.c')
                l.append(d)
            links_table.append(l)
        return links_table

    def get_dot_link(self, file):
        with open(file) as infile:
            dot = infile.read()
        return GRAPHVIZ_URL + quote(dot)

    def get_c_link(self, file):
        return f'file://{abspath(file)}'
