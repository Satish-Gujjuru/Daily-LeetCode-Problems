class Solution {
    public int[] singleNumber(int[] nums) {
        int diff_ele = 0;
        int arr[] = new int[2];
        for(int i=0;i<nums.length;i++){
            diff_ele ^= nums[i];
        }
        int needed_ele = diff_ele & -diff_ele;
        for(int i=0;i<nums.length;i++){
            if((nums[i] & needed_ele) != 0){
                arr[0] ^= nums[i];
            }else{
                arr[1] ^= nums[i];
            }
        }
        return arr;
    }
}