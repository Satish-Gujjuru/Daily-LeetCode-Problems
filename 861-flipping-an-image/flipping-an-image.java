class Solution {
    public int[][] flipAndInvertImage(int[][] image) {
        int result[][] = new int[image.length][image[0].length];
        for(int i=0;i<image.length;i++){
            int k = image[0].length-1;
            for(int j=0;j<image[0].length;j++){
                result[i][j] = image[i][k-j];
                if(result[i][j] == 0)
                    result[i][j] = 1;
                else
                    result[i][j] = 0;
            }
        }
        return result;
    }
}