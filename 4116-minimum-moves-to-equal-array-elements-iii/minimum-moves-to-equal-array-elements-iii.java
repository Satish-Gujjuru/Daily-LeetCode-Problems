class Solution {
    public int minMoves(int[] nums) {
        int n = nums.length;
        int max = Integer.MIN_VALUE;
        for(int i=0;i<n;i++){
            max = Math.max(nums[i],max);
        }
        int moves = 0;
        for(int i=0;i<n;i++){
            moves += Math.abs(max - nums[i]);
        }
        return moves;
    }
}