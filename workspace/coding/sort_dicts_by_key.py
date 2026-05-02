def sort_list_of_dicts(list_of_dicts, key):
    """
    Sorts a list of dictionaries by a given key.

    Parameters:
        list_of_dicts (list): List of dictionaries to sort.
        key (str): The key to sort the dictionaries by.

    Returns:
        list: A new list of dictionaries sorted by the specified key.
    """
    return sorted(list_of_dicts, key=lambda x: x.get(key))

# Example usage
if __name__ == "__main__":
    people = [
        {"name": "Alice", "age": 30},
        {"name": "Bob", "age": 25},
        {"name": "Charlie", "age": 35},
        {"name": "Diana", "age": 28}
    ]

    sorted_people = sort_list_of_dicts(people, 'age')
    print("Sorted by age:")
    for person in sorted_people:
        print(person)