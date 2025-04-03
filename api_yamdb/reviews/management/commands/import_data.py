import os
import csv
from django.core.management.base import BaseCommand
from reviews import models

CSV_DIR_PATH = 'static/data/'

FOREIGN_KEY_FIELDS = ('author', 'category')

MODEL_AND_CSV_MATCHING = {
    models.User: 'users.csv',
    models.Genre: 'genre.csv',
    models.Category: 'category.csv',
    models.Title: 'titles.csv',
    models.Review: 'review.csv',
    models.Comment: 'comments.csv',
}


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        error_occurred = False
        for model, csv_file_name in MODEL_AND_CSV_MATCHING.items():
            csv_file_path = os.path.join(CSV_DIR_PATH, csv_file_name)
            try:
                with open(
                    csv_file_path, newline='', encoding='utf-8'
                ) as csv_file:
                    csv_serializer(csv.DictReader(csv_file), model)
            except Exception as e:
                self.stderr.write(
                    f'Error processing file {csv_file_path}: {e}'
                )
                error_occurred = True

        if error_occurred:
            self.stderr.write('Ошибка при загрузке данных.')
        else:
            self.stdout.write('Данные успешно загружены.')


def csv_serializer(csv_data, model):
    objs = []
    for row in csv_data:
        for field in FOREIGN_KEY_FIELDS:
            if field in row:
                row[f'{field}_id'] = row[field]
                del row[field]
        objs.append(model(**row))
    model.objects.bulk_create(objs, ignore_conflicts=True)
