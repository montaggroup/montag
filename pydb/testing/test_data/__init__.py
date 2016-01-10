# coding=utf-8
import os


def get_book_path(file_name):
    return os.path.abspath(os.path.join(os.path.dirname(__file__), 'books', file_name))
