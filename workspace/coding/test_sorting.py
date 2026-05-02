import unittest
from sorting_algorithm import merge_sort

class TestMergeSort(unittest.TestCase):

    def test_empty_array(self):
        self.assertEqual(merge_sort([]), [])

    def test_single_element(self):
        self.assertEqual(merge_sort([1]), [1])

    def test_sorted_array(self):
        self.assertEqual(merge_sort([1, 2, 3]), [1, 2, 3])

    def test_reverse_sorted_array(self):
        self.assertEqual(merge_sort([3, 2, 1]), [1, 2, 3])

    def test_unsorted_array_with_duplicates(self):
        self.assertEqual(merge_sort([3, 1, 4, 1, 5, 9, 2, 6, 5]), [1, 1, 2, 3, 4, 5, 5, 6, 9])

    def test_negative_numbers(self):
        self.assertEqual(merge_sort([-1, -3, 2, 0, -2]), [-3, -2, -1, 0, 2])

if __name__ == '__main__':
    unittest.main()