class Solution {
    public List<List<Integer>> threeSum(int[] nums) {
        List<List<Integer>> outlist = new ArrayList<>();
        Arrays.sort(nums);
        int i=0;
        while(i<nums.length-2 && nums[i] <= 0){
            int j=i+1;
            int k=nums.length-1;
            if(i>0 && nums[i] == nums[i-1]){
                i++;
                continue;
            }
            while(j<k){
                if(nums[i]+nums[j]+nums[k] == 0){
                    List<Integer> inlist = new ArrayList<>();
                    inlist.add(nums[i]);
                    inlist.add(nums[j]);
                    inlist.add(nums[k]);
                    outlist.add(inlist);
                    k--;
                    j++;
                    while(j<k && nums[j] == nums[j-1]){
                        j++;
                    }
                    while(j<k && nums[k] == nums[k+1]){
                        k--;
                    }
                }else if(nums[i] + nums[j] + nums[k] > 0){
                    k--;
                }else{
                    j++;
                }
            }
            i++;
        }
        return outlist;
    }
}