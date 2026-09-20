class Solution {
    public int reverseDegree(String s) {
        int sum = 0;
        for(int i=0;i<s.length();i++){
            char c = s.charAt(i);
            int product = (i+1)*('z' - c + 1);
            sum += product;
        }
        return sum;
    }
}