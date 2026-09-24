class Solution {
    public int countSpecialIntegers(int[] nums) {
        Map<Integer,Integer> map = new HashMap<>();
        Set<Integer> set = new HashSet<>();
        map.put(nums[0],1);
        for(int i=1;i<nums.length;i++){
            if(map.containsKey(nums[i]) && nums[i] != nums[i-1]){
                map.remove(nums[i]);
                set.add(nums[i]);
            }else{
                if(!set.contains(nums[i]))
                    map.put(nums[i],1);
            }
        }
        return map.size();
    }
}