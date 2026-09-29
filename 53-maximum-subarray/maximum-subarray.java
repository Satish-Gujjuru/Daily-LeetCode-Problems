class Solution {
    public int maxSubArray(int[] nums) {
        int r=0;
        int sum = 0;
        int max_sum = Integer.MIN_VALUE;
        while(r<nums.length){
            int current_sum = Math.max(sum + nums[r],nums[r]);
            sum = current_sum;
            max_sum = Math.max(current_sum,max_sum);
            r++;
        }
        return max_sum;
    }
}