class Solution {
    public List<List<Integer>> fourSum(int[] nums, int target) {
        Arrays.sort(nums);
        List<List<Integer>> list = new ArrayList<>();
        int n = nums.length;
        for(int i=0;i<n-3;i++){
            if(i>0 && i<n-3 && nums[i] == nums[i-1]){
                continue;
            }
            for(int j=i+1;j<n-2;j++){
                if(j>i+1 && j<n-2 && nums[j] == nums[j-1]){
                    continue;
                }
                int k=j+1;
                int l=n-1;
                while(k<l){
                    long sum = (long)nums[i]+nums[j]+nums[k]+nums[l];

                    if(sum == target){
                        list.add(List.of(nums[i],nums[j],nums[k],nums[l]));
                        k++;
                        l--;
                        while (k < l && nums[k] == nums[k - 1]) {
                            k++;
                        }
                        while (k < l && nums[l] == nums[l + 1]) {
                            l--;
                        }
                    }else if(sum > target){
                        l--;
                    }else{
                        k++;
                    }
                }
            }
        }
        return list;
    }
}