from __future__ import annotations

import fnmatch
import json
import os
import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any, Optional

from .defaults import default_workflowdata_path


def names_only_search(
    tags: Iterable[Optional[Iterable[str]]] = [],
    names: Iterable[Optional[str]] = [],
    filename: str | os.PathLike = default_workflowdata_path(),
    all: bool = False,
) -> list[str]:
    """
    Searches a JSON file for items, returns their names.

    Parameters
    ----------
    tags : Iterable[Iterable[str]], optional
        An iterator of iterators of tags. The inner iterator is used to find the
        items that intersect all tags within the iterator. The outer iterator accepts
        the union of all items accepted by all inner iterators. Defaults to [].
    names : Iterable[str], optional
        The names to be matched. Defaults to [].
    filename : path-like, optional
        The name of the file to search. Defaults to the default workflowdata path.
    all : bool, optional
        If True, ignores other options and returns all items in the file.
        Defaults to False.

    Returns
    -------
    list[str]
        The "name" fields of all accepted items.
    """
    # Search the data file for applicable data.
    items: list[TestDataset] = search_file(
        tags=tags, names=names, filename=filename, all=all
    )
    # Get the set of names associated with that data and return it.
    name_list: list[str] = []
    for item in items:
        assert isinstance(item.name, str)
        name_list.append(item.name)

    return name_list


def search_file(
    tags: Iterable[Optional[Iterable[str]]] = [],
    names: Iterable[Optional[str]] = [],
    filename: str | os.PathLike = default_workflowdata_path(),
    all: bool = False,
) -> list[TestDataset]:
    """
    Return the list of unique objects in a JSON file that have given tags or name.

    This search accepts the union of any item identified by name or containing all of
    any set of tags given.

    Parameters
    ----------
    tags : Iterable[Iterable[str]], optional
        An iterator of iterators of tags. The inner iterator is used to find the
        items that intersect all tags within the iterator. The outer iterator accepts
        the union of all items accepted by all inner iterators. Defaults to [].
    names : Iterable[str], optional
        The names to be matched. Defaults to [].
    filename : path-like, optional
        The name of the file to search. Defaults to the default workflowdata path.
    all : bool, optional
        If True, ignores other options and returns all items in the file.
        Defaults to False.

    Returns
    -------
    list[TestDataset]
        The list of items accepted by the search.
    """
    if all:
        if (any(True for _ in names)) or (any(True for _ in tags)):
            print("'all' cannot be used in conjunction with 'tags' or 'names'.")
            exit()

    # Open the data file and load it into a JSON dictionary object.
    with open(file=os.fspath(filename)) as file:
        data: list[dict[str, Any]] = json.load(file)

    datasets: list[TestDataset] = []
    for data_dict in data:
        datasets.append(TestDataset.from_json_object(data_dict))

    # If every item was requested, return everything.
    if all:
        return datasets

    # Otherwise, filter out only the accepted items using the _accept_item function.
    items: list[TestDataset] = list(
        filter(lambda x: _accept_item(x, tags, names), datasets)
    )
    return items


@dataclass(frozen=True)
class TestFile:
    name: str
    checksum: str


@dataclass(frozen=True)
class TestDataset:
    name: str
    tags: list[str]
    url: str
    files: list[TestFile]

    @classmethod
    def from_json_object(cls, json_object: Mapping[str, Any]) -> TestDataset:
        """
        Generate a TestDataset from a structured JSON object.

        Parameters
        ----------
        json_object : Mapping[str, Any]
            The object.

        Returns
        -------
        TestDataset
            The generated TestDataset object.
        """
        name: str = json_object["name"]
        tags: list[str] = json_object["tags"]
        url: str = json_object["url"]
        files: list[TestFile] = []
        files_json: dict[str, str] = json_object["files"]
        for key in files_json:
            file = TestFile(name=key, checksum=files_json[key])
            files.append(file)

        return cls(name=name, tags=tags, url=url, files=files)

    def to_dict(self, fields: Iterable[str] = []) -> dict[str, Any]:
        """
        Unpackage this object into a dictionary.

        Parameters
        ----------
        fields : Iterable[str], optional
            if given, only include this set of fields from this object onto the
            output dictionary object. Else, include all fields. Defaults to [].

        Returns
        -------
        dict[str, Any]
            The dictionary object.

        Raises
        ------
        ValueError
            If an unknown field is given for filtering.
        """
        fields = list(fields)
        self_dict: dict[str, Any] = self.__dict__
        return_dict: dict[str, Any] = {}
        if len(fields) == 0:
            fields = list(self_dict.keys())
        if "files" in fields:
            return_dict["files"] = {}
        for field in fields:
            if field not in self_dict:
                raise ValueError(f"Unknown field given: {field}")
            value = self_dict[field]
            # Processing the list of TestFiles under the "files" attribute.
            # These need to be processed into a dictionary of filenames to checksums.
            if field == "files":
                return_dict[field] = {}
                for item in value:
                    return_dict[field][item.name] = item.checksum
                continue
            # All other fields can be placed by value into the XML.
            return_dict[field] = value
        return return_dict

    def __str__(self) -> str:
        return str(self.to_dict())


def _accept_item(
    item: TestDataset,
    tags: Iterable[Optional[Iterable[str]]],
    names: Iterable[Optional[str]],
) -> bool:
    """
    Accepts or rejects an item.

    Parameters
    ----------
    item : TestDataset
        The TestDataset item to be accepted or rejected.
    tags : Iterable[Iterable[str]]
        The set of sets of tags to be used as search terms.
    names : Iterable[str]
        The set of names to be used as search terms.

    Returns
    -------
    bool
        True if:
        -   The name of the item matches one of the names given.
        -   The tags on the item are a superset of any of the sets of tags given.
        Else False.
    """
    # Get the name of the item. This name should be a string.
    item_name = item.name
    assert isinstance(item_name, str)
    # For each name in the names list, check if it matches this one. If so, return True.
    for name in names:
        assert isinstance(name, str)
        # Check for the name using a wildcard check.
        match_object = re.match(fnmatch.translate(name), item_name)
        if match_object is not None:
            return True

    # Get the tags of the item.
    item_tags = item.tags
    # For each tag list in the overall set of lists,
    for tag_list in tags:
        assert tag_list is not None  # MyPy complains without this line
        # Match if the item contains each tag in the list.
        if all(tag in item_tags for tag in tag_list):
            return True

    # If neither of the above returned True, reject the item.
    return False
