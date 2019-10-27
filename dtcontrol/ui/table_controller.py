from os.path import join, exists, abspath, getsize
from urllib.parse import quote

from jinja2 import Environment, FileSystemLoader

GRAPHVIZ_URL = 'https://dreampuf.github.io/GraphvizOnline/#'
file_loader = FileSystemLoader('.')
env = Environment(loader=file_loader)

class TableController:
    def __init__(self, html_file, output_folder, is_artifact):
        self.html_file = html_file
        self.output_folder = output_folder
        self.is_artifact = is_artifact

    def update_and_save(self, results, last_run_datasets, last_run_classifiers):
        template = env.get_template('ui/table.html')
        with open('ui/table.js') as infile:
            script = infile.read()
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
                script=script
            ))

    def get_table_data(self, results):
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

    def get_table_data_artifact(self, results):
        row_names = [
            'cartpole',
            'tworooms-noneuler-latest',
            'cruise-latest',
            'dcdc',
            'truck_trailer',
            '10rooms',
            'helicopter',
            'traffic_1m',
            'traffic_10m',
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
                        'BDD'
                        ]
        table = []
        for dataset in row_names:
            row = []
            for classifier in column_names:
                try:
                    cell = results[dataset]['classifiers'][classifier]
                except KeyError:
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

    def get_file_link(self, file):
        return f'file://{abspath(file)}'
