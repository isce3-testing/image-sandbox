from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Iterable, List

from .search import filtered_file_search, names_only_search, search_file


def data_search(
    data_file: Path,
    tags: Iterable[Iterable[str]],
    names: Iterable[str],
    fields: Iterable[str],
    all: bool = False,
    print_output: bool = True,
) -> List[Dict[str, str | Dict[str, str]]]:
    """
    Query a file database for items.

    Parameters
    ----------
    data_file : Path
        The name of the database file.
    tags : Iterable[Iterable[str]]
        A set of sets of tags - this function will return the union of items that have
        all of any of the sets of tags passed in.
    names : Iterable[str]
        A list of names of data items to return.
    fields : Iterable[str]
        The set of fields to be returned on the data items. This should be a strict
        subset of the fields present on the items. Fields not included in this parameter
        will be filtered from the items prior to returning them.
    all : bool, optional
        If true, return all of the items in the database. Defaults to False

    Returns
    -------
    List[Dict[str, str | Dict[str, str]]]
        The items returned by the query, in dictionary format.
    """
    if all:
        if (any(True for _ in names)) or (any(True for _ in tags)):
            print("'all' cannot be used in conjunction with 'tags' or 'names'.")
            exit()

    if fields == []:
        return search_file(tags=tags, names=names, filename=data_file, all=all)

    filtered_search = filtered_file_search(
        fields=fields, names=names, tags=tags, filename=data_file, all=all
    )

    if print_output:
        print(json.dumps(filtered_search, indent=2))

    return filtered_search


def data_names(
    data_file: Path,
    tags: Iterable[Iterable[str]],
    names: Iterable[str],
    all: bool = False,
) -> List[str]:
    """
    Query a database file and return the names of all data items that match the query.

    Parameters
    ----------
    data_file : Path
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
    List[str]
        A list of the names of items that were returned by the query.
    """
    if all:
        if (any(True for _ in names)) or (any(True for _ in tags)):
            print("'all' cannot be used in conjunction with 'tags' or 'names'.")
            exit()

    return names_only_search(tags=tags, names=names, filename=data_file, all=all)
