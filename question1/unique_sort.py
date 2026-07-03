def quicksort_unique(nums):
    if len(nums) <= 1:
        return nums
    
    pivot = nums[0]
    smaller = [x for x in nums if x < pivot]
    larger = [x for x in nums if x > pivot]

    return quicksort_unique(smaller) + [pivot] + quicksort_unique(larger)

numbers = [12, 7, 12, 3, 5, 7, 8, 3, 9]
print(quicksort_unique(numbers))