def sort_list_of_dicts(dict_list, key):
    """
    Sorts a list of dictionaries by a specified key.

    Args:
        dict_list (list): List of dictionaries to sort.
        key (str): The key in the dictionaries to sort by.

    Returns:
        list: Sorted list of dictionaries.
    """
    return sorted(dict_list, key=lambda x: x.get(key))


# Example usage
if __name__ == "__main__":
    data = [
        {"name": "Alice", "age": 30},
        {"name": "Bob", "age": 25},
        {"name": "Charlie", "age": 35}
    ]

    sorted_data = sort_list_of_dicts(data, "age")
    print("Sorted by age:", sorted_data)

    sorted_data_name = sort_list_of_dicts(data, "name")
    print("Sorted by name:", sorted_data_name)
