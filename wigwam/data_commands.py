from __future__ import annotations

import json
import os
from collections.abc import Iterable

from .search import TestDataset, names_only_search, search_file


def print_search(
    data_file: str | os.PathLike,
    tags: Iterable[Iterable[str]],
    names: Iterable[str],
    fields: Iterable[str] = [],
    all: bool = False,
) -> None:
    """
    Query a file database for items and print the resulting output.

    Parameters
    ----------
    data_file : path-like
        The name of the database file.
    tags : Iterable[Iterable[str]]
        A set of sets of tags - this function will return the union of items that have
        all of any of the sets of tags passed in.
    names : Iterable[str]
        A list of names of data items to return.
    fields : Iterable[str]
        The set of fields to be returned on the data items. This should be a
        strict subset of the fields present on the items. If given, fields not included
        in this parameter will be filtered from the items prior to returning them. If
        empty, all fields will be returned.
    all : bool, optional
        If True, return all of the items in the database. Defaults to False.
    """
    test_datasets: list[TestDataset] = search_file(
        filename=data_file,
        tags=tags,
        names=names,
        all=all,
    )

    json_objects = []
    for file in test_datasets:
        # This should always be true, so we'd like to know if it isn't.
        assert isinstance(file, TestDataset)
        json_object = file.to_dict(fields)
        json_objects.append(json_object)

    print(json.dumps(json_objects, indent=2))


def data_names(
    data_file: str | os.PathLike,
    tags: Iterable[Iterable[str]],
    names: Iterable[str],
    all: bool = False,
) -> list[str]:
    """
    Query a database file and return the names of all data items that match the query.

    Parameters
    ----------
    data_file : path-like
        The path to the database file.
    tags : Iterable[Iterable[str]]
        A set of sets of tags - this function will return the union of items that have
        all of any of the sets of tags passed in.
    names : Iterable[str]
        A list of names of data items to return.
    all : bool, optional
        If true, return all of the items in the database. Defaults to False

    Returns
    -------
    list[str]
        A list of the names of items that were returned by the query.
    """
    if all:
        if (any(True for _ in names)) or (any(True for _ in tags)):
            print("'all' cannot be used in conjunction with 'tags' or 'names'.")
            exit()

    return names_only_search(tags=tags, names=names, filename=data_file, all=all)
