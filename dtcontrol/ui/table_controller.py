from os.path import join, exists, abspath, getsize
from urllib.parse import quote

from jinja2 import Environment, FileSystemLoader

import dtcontrol

GRAPHVIZ_URL = 'https://dreampuf.github.io/GraphvizOnline/#'
file_loader = FileSystemLoader([path + "/ui" for path in dtcontrol.__path__])
env = Environment(loader=file_loader)

class TableController:
    def __init__(self, html_file, output_folder, is_artifact=False):
        """
        :param html_file: the html file to save the table to
        :param output_folder: the folder containing the dot and C files
        :param is_artifact: if enabled, always produces a table exactly corresponding to the one in the paper
        """
        self.html_file = html_file
        self.output_folder = output_folder
        self.is_artifact = is_artifact

    @staticmethod
    def load_resource(filename):
        full_paths = [path + "/ui/" + filename for path in dtcontrol.__path__ if exists(path + "/ui/" + filename)]
        with open(full_paths[0]) as infile:
            script = infile.read()
        return script

    def update_and_save(self, results, last_run_datasets, last_run_classifiers):
        template = env.get_template('table.html')
        script_js = self.load_resource('table.js')
        jquery_js = self.load_resource('jquery-3.4.1.min.js')
        bootstrap_css = self.load_resource('bootstrap.min.css')
        bootstrap_js = self.load_resource('bootstrap.min.js')
        bootstrap_toggle_css = self.load_resource('bootstrap4-toggle.min.css')
        bootstrap_toggle_js = self.load_resource('bootstrap4-toggle.min.js')
        style_css = self.load_resource('style.css')

        if self.is_artifact:
            table, row_metadata, column_names = self.get_table_data_artifact(results)
        else:
            table, row_metadata, column_names = self.get_table_data(results)
        with open(self.html_file, 'w+') as out:
            out.write(template.render(
                column_names=column_names,
                row_metadata=row_metadata,
                table=table,
                links_table=self.get_dot_and_c_links(row_metadata, column_names),
                last_run_datasets=last_run_datasets,
                last_run_classifiers=last_run_classifiers,
                script_js=script_js,
                jquery_js=jquery_js,
                bootstrap_css=bootstrap_css,
                bootstrap_js=bootstrap_js,
                bootstrap_toggle_css=bootstrap_toggle_css,
                bootstrap_toggle_js=bootstrap_toggle_js,
                style_css=style_css
            ))

    @staticmethod
    def get_table_data(results):
        row_names = sorted(list(results.keys()))
        column_names = set()
        for dataset in results:
            column_names.update(results[dataset]['classifiers'].keys())
        column_names = sorted(list(column_names))
        table = []
        for dataset in row_names:
            row = []
            for classifier in column_names:
                if classifier in results[dataset]['classifiers']:
                    cell = results[dataset]['classifiers'][classifier]
                else:
                    cell = 'not yet computed'
                row.append(cell)
            table.append(row)
        row_metadata = [{'name': r, 'domain_of_controller': results[r]['metadata']['Y_metadata']['num_rows'],
                         'state_action_pairs': results[r]['metadata']['Y_metadata']['num_flattened']}
                        for r in row_names]
        return table, row_metadata, column_names

    @staticmethod
    def get_table_data_artifact(results):
        row_names = [
            'cartpole',
            'tworooms-noneuler-latest',
            'helicopter',
            'cruise-latest',
            'dcdc',
            '10rooms',
            'truck_trailer',
            'traffic_30m',
            'vehicle',
            'aircraft'
        ]
        column_names = ['CART',
                        'LinearClassifierDT-LinearSVC',
                        'LinearClassifierDT-LogisticRegression',
                        'OC1',
                        'MaxFreqDT',
                        'MaxFreq-LinearClassifierDT-LogisticRegression',
                        'MinNormDT',
                        'MinNorm-LinearClassifierDT',
                        ]
        table = []
        for dataset in row_names:
            row = []
            for classifier in column_names:
                try:
                    cell = results[dataset]['classifiers'][classifier]
                    cell['stats']['paths'] = int((cell['stats']['nodes'] + 1) / 2)
                    if 'bandwidth' in cell['stats']:
                        del cell['stats']['bandwidth']
                    if 'nodes' in cell['stats']:
                        del cell['stats']['nodes']
                    if 'oblique' in cell['stats']:
                        del cell['stats']['oblique']
                    if 'extended' in cell['stats']:
                        del cell['stats']['extended']
                except (KeyError, TypeError):
                    cell = 'not yet computed'
                row.append(cell)
            table.append(row)
        row_metadata = [{'name': r, 'domain_of_controller': results[r]['metadata']['Y_metadata'][
            'num_rows'] if r in results else "unknown",
                         'state_action_pairs': results[r]['metadata']['Y_metadata'][
                             'num_flattened'] if r in results else "unknown"} for r in row_names]
        return table, row_metadata, column_names

    def get_dot_and_c_links(self, row_metadata, column_names):
        links_table = []
        for i in range(len(row_metadata)):
            dataset = row_metadata[i]["name"]
            l = []
            for j in range(len(column_names)):
                classifier = column_names[j]
                d = {}
                path = join(self.output_folder, classifier, dataset, classifier)
                if exists(path + '.dot'):
                    d['dot_link'] = self.get_dot_link(path + '.dot')
                if exists(path + '.c'):
                    d['c_link'] = self.get_file_link(path + '.c')
                l.append(d)
            links_table.append(l)
        return links_table

    def get_dot_link(self, file):
        if getsize(file) > 500e3:
            return self.get_file_link(file)
        with open(file) as infile:
            dot = infile.read()
        return GRAPHVIZ_URL + quote(dot)

    @staticmethod
    def get_file_link(file):
        return f'file://{abspath(file)}'
