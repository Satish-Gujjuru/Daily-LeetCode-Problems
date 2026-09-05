class Solution {
    public int firstStableIndex(int[] nums, int k) {
        if(nums.length == 1)
            return 0;

        int[] max_prefix = new int[nums.length];
        int[] min_suffix = new int[nums.length];

        max_prefix[0] = nums[0];
        for(int i=1;i<nums.length;i++){
            max_prefix[i] = Math.max(max_prefix[i-1],nums[i]);
        }

        min_suffix[nums.length - 1] = nums[nums.length - 1];
        for(int i=nums.length - 2;i>=0;i--){
            min_suffix[i] = Math.min(min_suffix[i+1],nums[i]);
        }
        for(int i=0;i<nums.length;i++){
            int check = max_prefix[i] - min_suffix[i];
            if(check <= k){
                return i;
            }
        }
        return -1;
    }
}