class Solution {
    public int[] smallerNumbersThanCurrent(int[] nums) {
        int[] result = nums.clone();
        Arrays.sort(result);
        HashMap<Integer,Integer> map1 = new HashMap<>();
        for(int i=0;i<nums.length;i++){
            if(!map1.containsKey(result[i]))
                map1.put(result[i],i);
        }
        for(int i=0;i<nums.length;i++){
            result[i] = map1.get(nums[i]);
        }
        return result;
    }
}