class Solution {
    public int maxArea(int[] height) {
         int i = 0;
         int j = height.length - 1;
         int maxsum = Integer.MIN_VALUE;
         while(i < j){
            int sum = Math.min(height[i],height[j]) * (j-i);
            maxsum = Math.max(sum,maxsum);
            if(height[i] < height[j]){
                i++;
            }else{
                j--;
            }
         }
         return maxsum;
    }
}