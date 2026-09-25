class Solution {
    public int peakIndexInMountainArray(int[] arr) {
        int l = 0;
        int h = arr.length - 1;
        while(l<h){
            int m = l + (h-l)/2;
            if(arr[m] > arr[m+1]){
                h = m;
            }else if(arr[m] < arr[m+1]){
                l = m+1;
            }
        }
        return l;
    }
}