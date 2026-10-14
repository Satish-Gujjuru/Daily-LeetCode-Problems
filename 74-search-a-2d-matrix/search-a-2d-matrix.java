class Solution {
    public boolean searchMatrix(int[][] matrix, int target) {
        int m = matrix.length;
        int n = matrix[0].length;
        
        int l = 0;
        int h = n*m - 1;
        while(l<=h){
            int mid1 = l+(h-l)/2;
            if(matrix[mid1/n][mid1%n] == target){
                return true;
            }else if(matrix[mid1/n][mid1%n] > target){
                h = mid1 -1;
            }else{
                l = mid1 + 1;
            }
        }
        return false;
    }
}